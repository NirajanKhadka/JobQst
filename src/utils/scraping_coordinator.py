#!/usr/bin/env python3
"""
Optimized Scraping Coordinator
Coordinates and optimizes job scraping across multiple sources with intelligent batching,
caching, and data quality improvements.
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, TaskID

from src.utils.enhanced_error_tolerance import with_retry, robust_ops
from src.core.job_database import get_job_db

console = Console()

@dataclass
class ScrapingMetrics:
    """Metrics for tracking scraping performance."""
    start_time: float
    end_time: Optional[float] = None
    total_jobs_found: int = 0
    unique_jobs_added: int = 0
    duplicates_filtered: int = 0
    errors_encountered: int = 0
    sites_scraped: int = 0
    keywords_processed: int = 0
    average_jobs_per_keyword: float = 0.0
    scraping_rate_per_minute: float = 0.0
    data_quality_score: float = 0.0

class OptimizedScrapingCoordinator:
    """
    Coordinates optimized job scraping with intelligent batching, caching, and quality control.
    """
    
    def __init__(self, profile_name: str):
        """
        Initialize the scraping coordinator.
        
        Args:
            profile_name: Name of the user profile
        """
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.cache_dir = Path("output") / "scraping_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance settings
        self.max_concurrent_scrapers = 3
        self.batch_size = 10
        self.cache_duration_hours = 6
        self.quality_threshold = 0.7
        
        # Tracking
        self.metrics = ScrapingMetrics(start_time=time.time())
        self.processed_urls: Set[str] = set()
        self.keyword_performance: Dict[str, Dict] = {}
        
        # Load cached data
        self._load_cache()
    
    def _load_cache(self):
        """Load cached scraping data to avoid re-scraping recent jobs."""
        cache_file = self.cache_dir / f"{self.profile_name}_cache.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Check if cache is still valid
                cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
                if datetime.now() - cache_time < timedelta(hours=self.cache_duration_hours):
                    self.processed_urls = set(cache_data.get('processed_urls', []))
                    self.keyword_performance = cache_data.get('keyword_performance', {})
                    console.print(f"[cyan]📋 Loaded cache with {len(self.processed_urls)} processed URLs[/cyan]")
                else:
                    console.print("[yellow]⏰ Cache expired, starting fresh[/yellow]")
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Failed to load cache: {e}[/yellow]")
    
    def _save_cache(self):
        """Save current scraping state to cache."""
        cache_file = self.cache_dir / f"{self.profile_name}_cache.json"
        
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'processed_urls': list(self.processed_urls),
                'keyword_performance': self.keyword_performance,
                'metrics': {
                    'total_jobs_found': self.metrics.total_jobs_found,
                    'unique_jobs_added': self.metrics.unique_jobs_added,
                    'duplicates_filtered': self.metrics.duplicates_filtered
                }
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
                
            console.print(f"[green]💾 Cache saved with {len(self.processed_urls)} URLs[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Failed to save cache: {e}[/yellow]")
    
    @with_retry(operation_name="optimized_scraping", max_retries=2)
    def scrape_optimized(self, 
                        keywords: List[str], 
                        sites: List[str] = None,
                        max_jobs_per_keyword: int = 20,
                        enable_deep_scraping: bool = True) -> List[Dict]:
        """
        Perform optimized job scraping with intelligent coordination.
        
        Args:
            keywords: List of keywords to search for
            sites: List of sites to scrape (default: ['eluta'])
            max_jobs_per_keyword: Maximum jobs per keyword
            enable_deep_scraping: Whether to enable deep scraping
            
        Returns:
            List of scraped jobs
        """
        if sites is None:
            sites = ['eluta']
        
        console.print(f"\n[bold blue]🚀 Starting Optimized Scraping Session[/bold blue]")
        console.print(f"[cyan]📊 Keywords: {len(keywords)}, Sites: {len(sites)}, Max per keyword: {max_jobs_per_keyword}[/cyan]")
        
        all_jobs = []
        
        with Progress() as progress:
            # Create progress tasks
            main_task = progress.add_task("[cyan]Overall Progress", total=len(keywords) * len(sites))
            
            # Process keywords in optimized batches
            keyword_batches = self._create_keyword_batches(keywords)
            
            for batch_idx, keyword_batch in enumerate(keyword_batches):
                console.print(f"\n[bold]📦 Processing Batch {batch_idx + 1}/{len(keyword_batches)}[/bold]")
                
                # Scrape batch with concurrent processing
                batch_jobs = self._scrape_keyword_batch(
                    keyword_batch, sites, max_jobs_per_keyword, 
                    enable_deep_scraping, progress, main_task
                )
                
                # Process and filter jobs
                processed_jobs = self._process_job_batch(batch_jobs)
                all_jobs.extend(processed_jobs)
                
                # Update metrics
                self._update_batch_metrics(keyword_batch, batch_jobs, processed_jobs)
                
                # Save intermediate results
                if batch_idx % 2 == 0:  # Save every 2 batches
                    self._save_cache()
        
        # Finalize metrics
        self._finalize_metrics()
        
        # Save final cache
        self._save_cache()
        
        console.print(f"\n[bold green]🎉 Optimized scraping completed![/bold green]")
        self._display_final_metrics()
        
        return all_jobs
    
    def _create_keyword_batches(self, keywords: List[str]) -> List[List[str]]:
        """Create optimized keyword batches based on performance history."""
        # Sort keywords by historical performance
        sorted_keywords = sorted(keywords, key=lambda k: self._get_keyword_priority(k), reverse=True)
        
        # Create batches
        batches = []
        for i in range(0, len(sorted_keywords), self.batch_size):
            batch = sorted_keywords[i:i + self.batch_size]
            batches.append(batch)
        
        return batches
    
    def _get_keyword_priority(self, keyword: str) -> float:
        """Get priority score for a keyword based on historical performance."""
        if keyword not in self.keyword_performance:
            return 0.5  # Default priority for new keywords
        
        perf = self.keyword_performance[keyword]
        
        # Calculate priority based on success rate and job quality
        success_rate = perf.get('success_rate', 0.5)
        avg_quality = perf.get('avg_quality_score', 0.5)
        recent_jobs = perf.get('recent_job_count', 0)
        
        # Boost priority for keywords that recently found jobs
        recency_boost = min(recent_jobs / 10, 0.3)
        
        return (success_rate * 0.4) + (avg_quality * 0.4) + recency_boost
    
    def _scrape_keyword_batch(self, 
                             keywords: List[str], 
                             sites: List[str],
                             max_jobs_per_keyword: int,
                             enable_deep_scraping: bool,
                             progress: Progress,
                             main_task: TaskID) -> List[Dict]:
        """Scrape a batch of keywords with concurrent processing."""
        batch_jobs = []
        
        # Use ThreadPoolExecutor for concurrent scraping
        with ThreadPoolExecutor(max_workers=self.max_concurrent_scrapers) as executor:
            # Submit scraping tasks
            future_to_keyword = {}
            
            for keyword in keywords:
                for site in sites:
                    future = executor.submit(
                        self._scrape_single_keyword,
                        keyword, site, max_jobs_per_keyword, enable_deep_scraping
                    )
                    future_to_keyword[future] = (keyword, site)
            
            # Collect results as they complete
            for future in as_completed(future_to_keyword):
                keyword, site = future_to_keyword[future]
                
                try:
                    jobs = future.result(timeout=300)  # 5 minute timeout
                    batch_jobs.extend(jobs)
                    
                    console.print(f"[green]✅ {keyword} on {site}: {len(jobs)} jobs[/green]")
                    
                except Exception as e:
                    console.print(f"[red]❌ {keyword} on {site} failed: {e}[/red]")
                    self.metrics.errors_encountered += 1
                
                finally:
                    progress.update(main_task, advance=1)
        
        return batch_jobs
    
    def _scrape_single_keyword(self, 
                              keyword: str, 
                              site: str, 
                              max_jobs: int,
                              enable_deep_scraping: bool) -> List[Dict]:
        """Scrape jobs for a single keyword from a specific site."""
        try:
            # Import the appropriate scraper
            if site == 'eluta':
                from scrapers.eluta_enhanced import ElutaEnhancedScraper
                
                # Create a minimal profile for the scraper
                profile = {
                    'keywords': [keyword],
                    'location': '',
                    'ollama_model': 'mistral:7b'
                }
                
                scraper = ElutaEnhancedScraper(profile)
                jobs = list(scraper.scrape_jobs())
                
                # Limit to max_jobs
                return jobs[:max_jobs]
            
            else:
                console.print(f"[yellow]⚠️ Site {site} not supported yet[/yellow]")
                return []
                
        except Exception as e:
            console.print(f"[red]❌ Error scraping {keyword} from {site}: {e}[/red]")
            return []

    def _process_job_batch(self, jobs: List[Dict]) -> List[Dict]:
        """Process and filter a batch of jobs for quality and duplicates."""
        processed_jobs = []

        for job in jobs:
            # Skip if already processed
            job_url = job.get('url', '')
            if job_url in self.processed_urls:
                self.metrics.duplicates_filtered += 1
                continue

            # Quality check
            quality_score = self._calculate_job_quality(job)
            if quality_score < self.quality_threshold:
                console.print(f"[yellow]⚠️ Low quality job filtered: {job.get('title', 'Unknown')} (score: {quality_score:.2f})[/yellow]")
                continue

            # Enhance job data
            enhanced_job = self._enhance_job_data(job, quality_score)

            # Add to database
            if self.db.add_job(enhanced_job):
                processed_jobs.append(enhanced_job)
                self.processed_urls.add(job_url)
                self.metrics.unique_jobs_added += 1
            else:
                self.metrics.duplicates_filtered += 1

        return processed_jobs

    def _calculate_job_quality(self, job: Dict) -> float:
        """Calculate quality score for a job (0.0 to 1.0)."""
        score = 0.0

        # Required fields check (40% of score)
        required_fields = ['title', 'company', 'location', 'url']
        field_score = sum(1 for field in required_fields if job.get(field, '').strip()) / len(required_fields)
        score += field_score * 0.4

        # Content quality check (30% of score)
        title = job.get('title', '').strip()
        company = job.get('company', '').strip()
        summary = job.get('summary', '').strip()

        content_score = 0.0
        if len(title) >= 10 and not title.lower().startswith('unknown'):
            content_score += 0.4
        if len(company) >= 3 and company.lower() not in ['unknown', 'eluta', 'indeed']:
            content_score += 0.3
        if len(summary) >= 50:
            content_score += 0.3

        score += content_score * 0.3

        # Freshness check (20% of score)
        posted_date = job.get('posted_date', '')
        if posted_date:
            # Simple freshness check - prefer recent jobs
            if 'today' in posted_date.lower() or 'hour' in posted_date.lower():
                score += 0.2
            elif 'day' in posted_date.lower() and not 'week' in posted_date.lower():
                score += 0.15
            elif 'week' in posted_date.lower():
                score += 0.1

        # URL quality check (10% of score)
        url = job.get('url', '')
        if url and len(url) > 20 and 'http' in url:
            score += 0.1

        return min(score, 1.0)

    def _enhance_job_data(self, job: Dict, quality_score: float) -> Dict:
        """Enhance job data with additional metadata."""
        enhanced_job = job.copy()

        # Add quality metadata
        enhanced_job['quality_score'] = quality_score
        enhanced_job['processed_at'] = datetime.now().isoformat()
        enhanced_job['scraping_session'] = f"{self.profile_name}_{int(self.metrics.start_time)}"

        # Normalize and clean data
        enhanced_job['title'] = self._clean_text(job.get('title', ''))
        enhanced_job['company'] = self._clean_text(job.get('company', ''))
        enhanced_job['location'] = self._clean_text(job.get('location', ''))
        enhanced_job['summary'] = self._clean_text(job.get('summary', ''))

        # Add search metadata
        enhanced_job['search_keyword'] = job.get('search_keyword', '')
        enhanced_job['site'] = job.get('site', 'unknown')

        return enhanced_job

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text data."""
        if not text:
            return ''

        # Basic cleaning
        cleaned = text.strip()

        # Remove excessive whitespace
        cleaned = ' '.join(cleaned.split())

        # Remove common artifacts
        artifacts = ['...', '…', '\n', '\r', '\t']
        for artifact in artifacts:
            cleaned = cleaned.replace(artifact, ' ')

        # Final cleanup
        cleaned = ' '.join(cleaned.split())

        return cleaned

    def _update_batch_metrics(self, keywords: List[str], raw_jobs: List[Dict], processed_jobs: List[Dict]):
        """Update metrics after processing a batch."""
        self.metrics.total_jobs_found += len(raw_jobs)
        self.metrics.keywords_processed += len(keywords)

        # Update keyword performance
        for keyword in keywords:
            keyword_jobs = [j for j in raw_jobs if j.get('search_keyword') == keyword]
            keyword_processed = [j for j in processed_jobs if j.get('search_keyword') == keyword]

            if keyword not in self.keyword_performance:
                self.keyword_performance[keyword] = {
                    'total_attempts': 0,
                    'total_jobs_found': 0,
                    'total_jobs_processed': 0,
                    'success_rate': 0.0,
                    'avg_quality_score': 0.0,
                    'recent_job_count': 0
                }

            perf = self.keyword_performance[keyword]
            perf['total_attempts'] += 1
            perf['total_jobs_found'] += len(keyword_jobs)
            perf['total_jobs_processed'] += len(keyword_processed)
            perf['recent_job_count'] = len(keyword_processed)

            # Calculate success rate
            if perf['total_attempts'] > 0:
                perf['success_rate'] = perf['total_jobs_processed'] / max(perf['total_jobs_found'], 1)

            # Calculate average quality score
            if keyword_processed:
                quality_scores = [j.get('quality_score', 0.0) for j in keyword_processed]
                perf['avg_quality_score'] = sum(quality_scores) / len(quality_scores)

    def _finalize_metrics(self):
        """Finalize scraping metrics."""
        self.metrics.end_time = time.time()
        duration_minutes = (self.metrics.end_time - self.metrics.start_time) / 60

        if self.metrics.keywords_processed > 0:
            self.metrics.average_jobs_per_keyword = self.metrics.unique_jobs_added / self.metrics.keywords_processed

        if duration_minutes > 0:
            self.metrics.scraping_rate_per_minute = self.metrics.unique_jobs_added / duration_minutes

        # Calculate overall data quality score
        if self.metrics.unique_jobs_added > 0:
            total_quality = sum(
                perf.get('avg_quality_score', 0.0) * perf.get('total_jobs_processed', 0)
                for perf in self.keyword_performance.values()
            )
            self.metrics.data_quality_score = total_quality / self.metrics.unique_jobs_added

    def _display_final_metrics(self):
        """Display final scraping metrics."""
        duration = (self.metrics.end_time - self.metrics.start_time) / 60

        console.print(f"\n[bold blue]📊 Scraping Session Summary[/bold blue]")
        console.print(f"[cyan]⏱️  Duration: {duration:.1f} minutes[/cyan]")
        console.print(f"[green]✅ Jobs found: {self.metrics.total_jobs_found}[/green]")
        console.print(f"[green]📝 Unique jobs added: {self.metrics.unique_jobs_added}[/green]")
        console.print(f"[yellow]🔄 Duplicates filtered: {self.metrics.duplicates_filtered}[/yellow]")
        console.print(f"[red]❌ Errors: {self.metrics.errors_encountered}[/red]")
        console.print(f"[blue]📈 Scraping rate: {self.metrics.scraping_rate_per_minute:.1f} jobs/minute[/blue]")
        console.print(f"[purple]⭐ Data quality score: {self.metrics.data_quality_score:.2f}/1.0[/purple]")

        # Top performing keywords
        if self.keyword_performance:
            console.print(f"\n[bold]🏆 Top Performing Keywords:[/bold]")
            sorted_keywords = sorted(
                self.keyword_performance.items(),
                key=lambda x: x[1].get('total_jobs_processed', 0),
                reverse=True
            )

            for keyword, perf in sorted_keywords[:5]:
                console.print(f"  [cyan]{keyword}[/cyan]: {perf.get('total_jobs_processed', 0)} jobs (quality: {perf.get('avg_quality_score', 0):.2f})")

# Convenience function for easy access
def run_optimized_scraping(profile_name: str,
                          keywords: List[str],
                          sites: List[str] = None,
                          max_jobs_per_keyword: int = 20) -> List[Dict]:
    """
    Run optimized scraping with the coordinator.

    Args:
        profile_name: Name of the user profile
        keywords: List of keywords to search for
        sites: List of sites to scrape
        max_jobs_per_keyword: Maximum jobs per keyword

    Returns:
        List of scraped jobs
    """
    coordinator = OptimizedScrapingCoordinator(profile_name)
    return coordinator.scrape_optimized(keywords, sites, max_jobs_per_keyword)

def get_scraping_coordinator() -> OptimizedScrapingCoordinator:
    """Get a scraping coordinator instance."""
    return OptimizedScrapingCoordinator()

# Backward compatibility alias
ScrapingCoordinator = OptimizedScrapingCoordinator
