#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Site JobSpy Workers - Optimal Performance Architecture
Separate workers for Indeed, LinkedIn, and Glassdoor with parallel processing
"""

import asyncio
import concurrent.futures
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime

from src.core.job_database import ModernJobDatabase
from src.config.jobspy_integration_config import JOBSPY_LOCATION_SETS, JOBSPY_QUERY_PRESETS

# New imports for async description fetching
try:
    import aiohttp
except Exception:  # pragma: no cover
    aiohttp = None

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@dataclass
class WorkerResult:
    """Result from a single site worker"""
    site: str
    jobs_found: int
    processing_time: float
    success: bool
    error: Optional[str] = None
    jobs_data: Optional[pd.DataFrame] = None

@dataclass
class MultiSiteResult:
    """Aggregated result from all site workers"""
    total_jobs: int
    total_time: float
    worker_results: List[WorkerResult]
    combined_data: pd.DataFrame
    success_rate: float

class SiteWorker:
    """Base class for site-specific workers"""
    
    def __init__(self, site: str, max_jobs_per_location: int = 20, per_site_concurrency: int = 3, rate_limit_delay: float = 0.1):
        self.site = site
        self.max_jobs_per_location = max_jobs_per_location
        self.per_site_concurrency = max(1, int(per_site_concurrency))
        self.rate_limit_delay = max(0.0, float(rate_limit_delay))
        self.logger = logging.getLogger(f"SiteWorker.{site}")
    
    async def search_jobs(self, locations: List[str], search_terms: List[str], per_site_concurrency: Optional[int] = None, max_total_jobs: Optional[int] = None) -> WorkerResult:
        """Search jobs for this specific site using bounded per-site concurrency and early-stop.
        
        Args:
            locations: List of locations to search
            search_terms: List of search terms/queries
            per_site_concurrency: Max concurrent scrape calls for this site
            max_total_jobs: Early stop after reaching this many unique jobs for this site
        """
        start_time = time.time()
        all_jobs: List[pd.DataFrame] = []
        seen_urls: set = set()
        max_unique = max_total_jobs if (isinstance(max_total_jobs, int) and max_total_jobs > 0) else None
        concurrency = max(1, int(per_site_concurrency or self.per_site_concurrency))
        
        try:
            self.logger.info(f"🔍 {self.site.upper()} Worker starting search")
            self.logger.info(f"📍 Locations: {len(locations)} | 🎯 Search terms: {len(search_terms)} | ⚙️ Concurrency: {concurrency}")
            
            combos: List[Tuple[str, str]] = [(term, location) for location in locations for term in search_terms]
            total_combos = len(combos)
            if total_combos == 0:
                return WorkerResult(site=self.site, jobs_found=0, processing_time=time.time()-start_time, success=False, error="No search combos")
            
            loop = asyncio.get_event_loop()
            
            async def _schedule_next(it, executor, pending, meta_map):
                try:
                    term, location = next(it)
                except StopIteration:
                    return False
                # Respect gentle pacing between submissions
                if self.rate_limit_delay:
                    await asyncio.sleep(self.rate_limit_delay)
                future = executor.submit(self._scrape_jobs_sync, term, location)
                t = asyncio.wrap_future(future)
                pending.add(t)
                meta_map[t] = (term, location)
                return True
            
            # Single shared executor per worker
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                it = iter(combos)
                pending: set = set()
                meta_map: Dict[asyncio.Task, Tuple[str, str]] = {}
                # Prime the pool
                for _ in range(concurrency):
                    scheduled = await _schedule_next(it, executor, pending, meta_map)
                    if not scheduled:
                        break
                
                # Process as they complete
                processed = 0
                while pending:
                    done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                    for d in done:
                        processed += 1
                        term, location = meta_map.pop(d, ("", ""))
                        try:
                            jobs_df = d.result()
                        except Exception as e:  # scrape failure for this combo
                            self.logger.debug(f"❌ {self.site} combo failed for '{term}' in {location}: {e}")
                            jobs_df = None
                        
                        if jobs_df is not None and not jobs_df.empty:
                            # Early de-duplication by URL
                            if 'job_url' in jobs_df.columns:
                                new_df = jobs_df[~jobs_df['job_url'].isin(seen_urls)].copy()
                            else:
                                new_df = jobs_df.copy()
                            if not new_df.empty:
                                # annotate
                                new_df['search_term'] = term
                                new_df['search_location'] = location
                                new_df['source_site'] = self.site
                                new_df['scraped_at'] = datetime.now()
                                all_jobs.append(new_df)
                                if 'job_url' in new_df.columns:
                                    seen_urls.update(new_df['job_url'].astype(str).tolist())
                                self.logger.debug(f"✅ {self.site}: +{len(new_df)} new (uniq) for '{term}' in {location} | total={len(seen_urls)}")
                            
                            # Early stop if reached target
                            if max_unique is not None and len(seen_urls) >= max_unique:
                                self.logger.info(f"⏹️ Early stop reached for {self.site}: {len(seen_urls)} >= {max_unique}")
                                # Cancel remaining tasks
                                for p in pending:
                                    p.cancel()
                                pending.clear()
                                break
                        
                    # Top-up pending to maintain concurrency, unless early-stopped
                    while len(pending) < concurrency:
                        scheduled = await _schedule_next(it, executor, pending, meta_map)
                        if not scheduled:
                            break
            
            # Combine all results
            if all_jobs:
                combined_df = pd.concat(all_jobs, ignore_index=True)
                # Deduplicate by URL
                initial_count = len(combined_df)
                if 'job_url' in combined_df.columns:
                    combined_df = combined_df.drop_duplicates(subset=['job_url'], keep='first')
                final_count = len(combined_df)
                
                processing_time = time.time() - start_time
                
                self.logger.info(f"✅ {self.site.upper()} Worker completed:")
                self.logger.info(f"   📊 Raw jobs: {initial_count}")
                self.logger.info(f"   🎯 Unique jobs: {final_count}")
                self.logger.info(f"   ⚡ Time: {processing_time:.1f}s")
                self.logger.info(f"   🚀 Speed: {final_count/max(processing_time, 1e-6):.1f} jobs/sec")
                
                return WorkerResult(
                    site=self.site,
                    jobs_found=final_count,
                    processing_time=processing_time,
                    success=True,
                    jobs_data=combined_df
                )
            else:
                processing_time = time.time() - start_time
                self.logger.warning(f"❌ {self.site.upper()} Worker found no jobs")
                
                return WorkerResult(
                    site=self.site,
                    jobs_found=0,
                    processing_time=processing_time,
                    success=False,
                    error="No jobs found"
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ {self.site.upper()} Worker failed: {e}")
            
            return WorkerResult(
                site=self.site,
                jobs_found=0,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    def _scrape_jobs_sync(self, search_term: str, location: str) -> Optional[pd.DataFrame]:
        """Synchronous wrapper for jobspy scrape_jobs"""
        try:
            return scrape_jobs(
                search_term=search_term,
                location=location,
                site_name=[self.site],  # Only this site
                results_wanted=self.max_jobs_per_location,
                hours_old=336,  # 14 days
                country_indeed='Canada',
                hyperlinks=True,
                description_format='markdown'  # Changed from 'text' to 'markdown'
            )
        except Exception as e:
            self.logger.warning(f"Scrape failed for {self.site}: {e}")
            return None

class MultiSiteJobSpyWorkers:
    """Orchestrates multiple site workers for optimal performance"""
    
    def __init__(self, profile_name: str = "default", max_jobs_per_site_location: int = 20, per_site_concurrency: int = 3):
        self.profile_name = profile_name
        self.max_jobs_per_site_location = max_jobs_per_site_location
        self.per_site_concurrency = max(1, int(per_site_concurrency))
        self.db = ModernJobDatabase(profile_name)
        self.logger = logging.getLogger("MultiSiteJobSpyWorkers")
        
        # Create site-specific workers
        self.workers = {
            'indeed': SiteWorker('indeed', max_jobs_per_site_location, per_site_concurrency=self.per_site_concurrency),
            'linkedin': SiteWorker('linkedin', max_jobs_per_site_location, per_site_concurrency=self.per_site_concurrency),
            'glassdoor': SiteWorker('glassdoor', max_jobs_per_site_location, per_site_concurrency=self.per_site_concurrency)
        }
    
    async def run_comprehensive_search(
        self,
        location_set: str = "canada_comprehensive",
        query_preset: str = "comprehensive",
        sites: Optional[List[str]] = None,
        per_site_concurrency: Optional[int] = None,
        max_total_jobs: Optional[int] = None
    ) -> MultiSiteResult:
        """Run comprehensive search across all sites in parallel.
        
        per_site_concurrency: limit concurrent scrape calls per site
        max_total_jobs: early-stop threshold per site (after cross-combo de-dup)
        """
        
        start_time = time.time()
        
        # Get locations and search terms
        locations = JOBSPY_LOCATION_SETS.get(location_set, JOBSPY_LOCATION_SETS['canadian_cities'])
        search_terms = JOBSPY_QUERY_PRESETS.get(query_preset, JOBSPY_QUERY_PRESETS['comprehensive'])
        
        # Default to all sites if none specified
        if sites is None:
            sites = ['indeed', 'linkedin', 'glassdoor']
        
        self.logger.info("🚀 Starting Multi-Site JobSpy Workers")
        self.logger.info(f"📍 Locations: {len(locations)} ({location_set})")
        self.logger.info(f"🎯 Search terms: {len(search_terms)} ({query_preset})")
        self.logger.info(f"🌐 Sites: {sites}")
        self.logger.info(f"📊 Max jobs per site/location: {self.max_jobs_per_site_location}")
        self.logger.info(f"⚙️ Per-site concurrency: {per_site_concurrency or self.per_site_concurrency} | ⏹️ Max per-site jobs: {max_total_jobs or '∞'}")
        
        # Run all workers in parallel
        tasks = []
        for site in sites:
            if site in self.workers:
                worker = self.workers[site]
                task = asyncio.create_task(
                    worker.search_jobs(locations, search_terms, per_site_concurrency=per_site_concurrency, max_total_jobs=max_total_jobs),
                    name=f"worker_{site}"
                )
                tasks.append(task)
            else:
                self.logger.warning(f"Unknown site: {site}")
        
        # Wait for all workers to complete
        self.logger.info(f"⚡ Running {len(tasks)} workers in parallel...")
        worker_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        total_jobs = 0
        all_jobs_data = []
        
        for i, result in enumerate(worker_results):
            if isinstance(result, Exception):
                self.logger.error(f"❌ Worker {sites[i]} failed with exception: {result}")
                continue
            
            if isinstance(result, WorkerResult):
                successful_results.append(result)
                total_jobs += result.jobs_found
                
                if result.success and result.jobs_data is not None:
                    all_jobs_data.append(result.jobs_data)
        
        # Combine all job data
        combined_df = pd.DataFrame()
        if all_jobs_data:
            combined_df = pd.concat(all_jobs_data, ignore_index=True)
            # Improved deduplication across all sites
            initial_count = len(combined_df)
            
            # Step 1: Remove duplicates by URL (if available)
            if 'job_url' in combined_df.columns:
                # Remove rows with non-null URLs that are duplicates
                url_mask = combined_df['job_url'].notna() & (combined_df['job_url'] != '')
                url_dupes_removed = combined_df[url_mask].drop_duplicates(subset=['job_url'], keep='first')
                no_url_jobs = combined_df[~url_mask]
                combined_df = pd.concat([url_dupes_removed, no_url_jobs], ignore_index=True)
            
            # Step 2: Remove duplicates by title + company combination
            if 'title' in combined_df.columns and 'company' in combined_df.columns:
                # Create a normalized title+company key for deduplication
                combined_df['_dedup_key'] = (
                    combined_df['title'].astype(str).str.lower().str.strip() + 
                    '|' + 
                    combined_df['company'].astype(str).str.lower().str.strip()
                )
                combined_df = combined_df.drop_duplicates(subset=['_dedup_key'], keep='first')
                combined_df = combined_df.drop(columns=['_dedup_key'])  # Remove helper column
            
            final_count = len(combined_df)
            
            self.logger.info(f"🔄 Improved deduplication: {initial_count} → {final_count} jobs")
            if initial_count > final_count:
                removed = initial_count - final_count
                self.logger.info(f"   Removed {removed} duplicates ({removed/initial_count:.1%})")
        
        total_time = time.time() - start_time
        success_rate = len(successful_results) / len(sites) if sites else 0
        
        # Log comprehensive results
        self.logger.info("🎉 Multi-Site Search Complete!")
        self.logger.info(f"📊 Total unique jobs: {len(combined_df)}")
        self.logger.info(f"⚡ Total time: {total_time:.1f}s")
        self.logger.info(f"🚀 Overall speed: {len(combined_df)/max(total_time, 1e-6):.1f} jobs/sec")
        self.logger.info(f"✅ Success rate: {success_rate:.1%}")
        
        # Site-by-site breakdown
        for result in successful_results:
            self.logger.info(f"   {result.site.upper()}: {result.jobs_found} jobs in {result.processing_time:.1f}s")
        
        return MultiSiteResult(
            total_jobs=len(combined_df),
            total_time=total_time,
            worker_results=successful_results,
            combined_data=combined_df,
            success_rate=success_rate
        )
    
    async def run_optimized_description_fetching(self, jobs_df: pd.DataFrame, max_concurrency: int = 20, timeout_seconds: int = 12) -> pd.DataFrame:
        """Fetch job descriptions asynchronously for massive speed improvement.
        Only fetch where description is missing/empty.
        """
        
        if jobs_df.empty:
            return jobs_df
        
        if aiohttp is None:
            self.logger.warning("aiohttp not installed; skipping async description fetching")
            return jobs_df
        
        self.logger.info(f"🔄 Starting optimized description fetching for {len(jobs_df)} jobs")
        start_time = time.time()
        
        # Determine which rows need fetching
        def _is_missing(val) -> bool:
            try:
                if val is None:
                    return True
                if isinstance(val, float) and pd.isna(val):
                    return True
                if isinstance(val, str) and val.strip() == "":
                    return True
                return False
            except Exception:
                return True
        
        jobs_df = jobs_df.copy()
        need_mask = jobs_df['description'].apply(_is_missing) if 'description' in jobs_df.columns else pd.Series([True] * len(jobs_df))
        to_fetch = jobs_df[need_mask].reset_index()
        if to_fetch.empty:
            self.logger.info("All descriptions present; skipping fetching")
            return jobs_df
        
        semaphore = asyncio.Semaphore(max(1, int(max_concurrency)))
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AutoJobAgent/1.0)"}
        
        async def fetch_and_parse(session, url: str) -> Optional[str]:
            if not url:
                return None
            try:
                async with semaphore:
                    async with session.get(url, timeout=timeout_seconds, headers=headers, allow_redirects=True) as resp:
                        if resp.status != 200:
                            return None
                        html = await resp.text(errors='ignore')
                        soup = BeautifulSoup(html, 'html.parser')
                        # Remove scripts/styles
                        for tag in soup(['script', 'style', 'noscript']):
                            tag.decompose()
                        text = soup.get_text(" ")
                        # Basic cleanup
                        text = ' '.join(text.split())
                        return text if text else None
            except Exception:
                return None
        
        connector = aiohttp.TCPConnector(limit=max(32, max_concurrency))
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [asyncio.create_task(fetch_and_parse(session, str(row.get('job_url', '')))) for _, row in to_fetch.iterrows()]
            fetched_texts = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Apply fetched descriptions
        filled = 0
        # to_fetch contains an 'index' column with original indices
        for (_, row), fetched in zip(to_fetch[['index']].iterrows(), fetched_texts):
            if isinstance(fetched, Exception):
                continue
            orig_idx = row['index']
            if fetched and str(fetched).strip():
                # Prefer existing description if present; otherwise fill
                if 'description' not in jobs_df.columns or _is_missing(jobs_df.at[orig_idx, 'description']):
                    jobs_df.at[orig_idx, 'description'] = fetched
                    filled += 1
                else:
                    # Store as a separate column for reference
                    jobs_df.at[orig_idx, 'description_fetched'] = fetched
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ Description fetching completed in {processing_time:.1f}s | filled={filled}")
        
        return jobs_df
    
    def save_jobs_to_database(self, jobs_df: pd.DataFrame) -> int:
        """Save jobs to database with proper error handling"""
        
        if jobs_df.empty:
            self.logger.warning("No jobs to save to database")
            return 0
        
        try:
            saved_count = 0
            
            for _, job in jobs_df.iterrows():
                try:
                    # Convert job data to the format expected by the database
                    job_data = {
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', ''),
                        'url': job.get('job_url', ''),
                        'description': job.get('description', job.get('description_fetched', '')),
                        'site': job.get('source_site', 'jobspy'),
                        'date_posted': job.get('date_posted', ''),
                        'salary': job.get('compensation', ''),
                    }
                    
                    # Check if job already exists
                    existing_job = self.db.get_job_by_url(job_data['url'])
                    if existing_job:
                        # Update metadata
                        self.db.update_job_metadata(existing_job[0], {
                            'last_seen': datetime.now().isoformat(),
                            'source_site': job_data['site'],
                            'search_term': job.get('search_term', ''),
                            'search_location': job.get('search_location', '')
                        })
                    else:
                        # Save new job
                        self.db.save_job(job_data)
                        saved_count += 1
                        
                except Exception as e:
                    self.logger.warning(f"Failed to save job {job.get('title', 'Unknown')}: {e}")
                    continue
            
            self.logger.info(f"💾 Saved {saved_count} new jobs to database")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"❌ Database save failed: {e}")
            return 0

# Convenience function for easy usage
async def run_multi_site_search(
    profile_name: str = "default",
    location_set: str = "canada_comprehensive", 
    query_preset: str = "comprehensive",
    sites: Optional[List[str]] = None,
    max_jobs_per_site_location: int = 20,
    per_site_concurrency: int = 3,
    max_total_jobs: Optional[int] = None
) -> MultiSiteResult:
    """
    Run comprehensive multi-site job search
    
    Args:
        profile_name: User profile name
        location_set: Location set from config (e.g., 'canada_comprehensive')
        query_preset: Query preset from config (e.g., 'comprehensive')
        sites: List of sites to search (default: all)
        max_jobs_per_site_location: Max jobs per site per location
        per_site_concurrency: Concurrent scrape calls per site
        max_total_jobs: Early-stop threshold per site
    
    Returns:
        MultiSiteResult with comprehensive job data
    """
    
    workers = MultiSiteJobSpyWorkers(profile_name, max_jobs_per_site_location, per_site_concurrency)
    return await workers.run_comprehensive_search(location_set, query_preset, sites, per_site_concurrency=per_site_concurrency, max_total_jobs=max_total_jobs)

class JobSpyController:
    """Controller for managing JobSpy worker operations and testing"""
    
    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.logger = logging.getLogger("JobSpyController")
    
    async def test_configuration(
        self,
        target_jobs: int = 50,
        keywords: List[str] = None,
        sites: List[str] = None,
        location_set: str = "toronto_extended",
        per_site_concurrency: int = 3,
        jobs_per_keyword: int = 10
    ):
        """
        Test JobSpy with specific configuration
        
        Args:
            target_jobs: Target number of jobs to find
            keywords: List of search keywords 
            sites: List of sites to search
            location_set: Location set from config
            per_site_concurrency: Concurrent requests per site
            jobs_per_keyword: Jobs to find per keyword
        """
        
        # Set defaults
        if keywords is None:
            keywords = ["Python Developer", "Data Analyst", "Machine Learning Engineer", "SQL Developer", "Business Analyst"]
        if sites is None:
            # Use 5 different sites by default
            sites = ["indeed", "linkedin", "glassdoor", "zip_recruiter", "google"]
        
        # Add test keywords to config temporarily
        from src.config.jobspy_integration_config import JOBSPY_QUERY_PRESETS
        test_preset_name = f"test_{len(keywords)}_keywords"
        JOBSPY_QUERY_PRESETS[test_preset_name] = keywords
        
        # Calculate limits - with 5 sites, target fewer jobs per site
        max_total_per_site = max(10, target_jobs // len(sites))
        
        print("🧪 JobSpy Test Configuration")
        print("=" * 50)
        print(f"📊 Target jobs: {target_jobs}")
        print(f"🎯 Keywords ({len(keywords)}): {', '.join(keywords)}")
        print(f"🌐 Sites ({len(sites)}): {', '.join(sites)}")
        print(f"📍 Location set: {location_set}")
        print(f"⚙️ Per-site concurrency: {per_site_concurrency}")
        print(f"📈 Jobs per keyword: {jobs_per_keyword}")
        print(f"🔢 Max per site: {max_total_per_site}")
        
        start_time = time.time()
        
        try:
            result = await run_multi_site_search(
                profile_name=self.profile_name,
                location_set=location_set,
                query_preset=test_preset_name,
                sites=sites,
                max_jobs_per_site_location=jobs_per_keyword,
                per_site_concurrency=per_site_concurrency,
                max_total_jobs=max_total_per_site
            )
            
            total_time = time.time() - start_time
            
            # Display results
            self._display_test_results(result, target_jobs, keywords, sites, total_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Clean up test preset
            if test_preset_name in JOBSPY_QUERY_PRESETS:
                del JOBSPY_QUERY_PRESETS[test_preset_name]
    
    def _display_test_results(self, result, target_jobs: int, keywords: List[str], sites: List[str], total_time: float):
        """Display comprehensive test results"""
        
        print("\n" + "=" * 70)
        print("🎉 TEST RESULTS")
        print("=" * 70)
        
        print(f"📊 Total unique jobs found: {result.total_jobs}")
        print(f"🎯 Target vs Actual: {target_jobs} → {result.total_jobs}")
        print(f"⏱️  Total time: {total_time:.1f}s")
        print(f"🚀 Speed: {result.total_jobs/total_time:.1f} jobs/sec")
        print(f"✅ Success rate: {result.success_rate:.1%}")
        
        # Site breakdown
        print(f"\n🌐 Site breakdown:")
        for worker_result in result.worker_results:
            efficiency = worker_result.jobs_found / worker_result.processing_time if worker_result.processing_time > 0 else 0
            print(f"   {worker_result.site.upper()}: {worker_result.jobs_found} jobs in {worker_result.processing_time:.1f}s ({efficiency:.1f} jobs/sec)")
        
        # Sample jobs
        if not result.combined_data.empty:
            print(f"\n📋 Sample jobs found:")
            sample_size = min(5, len(result.combined_data))
            for i, (_, job) in enumerate(result.combined_data.head(sample_size).iterrows()):
                print(f"   {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')} ({job.get('source_site', 'N/A')})")
        
        # Keyword distribution
        if 'search_term' in result.combined_data.columns:
            print(f"\n🎯 Jobs per keyword:")
            keyword_counts = result.combined_data['search_term'].value_counts()
            for keyword, count in keyword_counts.items():
                print(f"   {keyword}: {count} jobs")
        
        # Site distribution  
        if 'source_site' in result.combined_data.columns:
            print(f"\n🌐 Jobs per site:")
            site_counts = result.combined_data['source_site'].value_counts()
            for site, count in site_counts.items():
                print(f"   {site.upper()}: {count} jobs")
        
        # Performance assessment
        print(f"\n📈 Performance Assessment:")
        if result.total_jobs >= target_jobs * 0.8:
            print("🟢 EXCELLENT: Met or exceeded target")
        elif result.total_jobs >= target_jobs * 0.6:
            print("🟡 GOOD: Close to target")
        elif result.total_jobs >= target_jobs * 0.4:
            print("🟠 FAIR: Below target but reasonable")
        else:
            print("🔴 POOR: Well below target")


def get_jobspy_controller(profile_name: str = "Nirajan") -> JobSpyController:
    """Get a JobSpy controller instance"""
    return JobSpyController(profile_name)


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments for testing
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            # Test mode with parameters
            async def test_mode():
                controller = JobSpyController("Nirajan")
                
                # Parse test parameters
                target_jobs = int(sys.argv[2]) if len(sys.argv) > 2 else 50
                keywords = sys.argv[3].split(",") if len(sys.argv) > 3 else None
                sites = sys.argv[4].split(",") if len(sys.argv) > 4 else None
                
                await controller.test_configuration(
                    target_jobs=target_jobs,
                    keywords=keywords,
                    sites=sites
                )
            
            asyncio.run(test_mode())
        
        elif sys.argv[1] == "demo":
            # Demo with different configurations
            async def demo_mode():
                controller = JobSpyController("Nirajan")
                
                print("🎯 Demo 1: 50 jobs, 5 keywords, 2 sites")
                await controller.test_configuration(
                    target_jobs=50,
                    keywords=["Python Developer", "Data Analyst", "Machine Learning Engineer", "SQL Developer", "Business Analyst"],
                    sites=["indeed", "linkedin"]
                )
                
                print("\n" + "="*50 + "\n")
                
                print("🎯 Demo 2: 30 jobs, 3 keywords, 1 site")
                await controller.test_configuration(
                    target_jobs=30,
                    keywords=["Python Developer", "Data Scientist", "Software Engineer"],
                    sites=["linkedin"]
                )
            
            asyncio.run(demo_mode())
    
    else:
        # Default example
        async def main():
            result = await run_multi_site_search(
                profile_name="Nirajan",
                location_set="canada_comprehensive",
                query_preset="comprehensive", 
                max_jobs_per_site_location=30,
                per_site_concurrency=4,
                max_total_jobs=800
            )
            
            print(f"🎉 Found {result.total_jobs} jobs in {result.total_time:.1f}s")
            print(f"🚀 Speed: {result.total_jobs/max(result.total_time, 1e-6):.1f} jobs/sec")
            print(f"✅ Success rate: {result.success_rate:.1%}")
        
        asyncio.run(main())
