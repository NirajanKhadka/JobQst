"""
High-Performance Parallel Job Scraper
Optimized for multi-core systems with concurrent processing
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Generator
from playwright.async_api import async_playwright
from rich.console import Console
from rich.progress import Progress, TaskID
import threading
from queue import Queue
import random

from .eluta_working import ElutaWorkingScraper
from .base_scraper import BaseJobScraper

console = Console()

class ParallelJobScraper:
    """
    High-performance parallel job scraper designed for multi-core systems.

    Features:
    - Concurrent processing (up to 12 workers for multi-core CPU)
    - Dynamic pagination with early termination
    - Detailed scraping for company application URLs
    - Memory-efficient job processing
    - Real-time progress tracking
    """
    
    def __init__(self, profile: Dict, max_workers: int = None):
        self.profile = profile
        self.keywords = profile.get("keywords", [])
        
        # Conservative settings for stability
        if max_workers is None:
            # Use conservative worker count for stability
            self.max_workers = 2  # Conservative default
        else:
            self.max_workers = max_workers

        # Performance settings optimized for stability
        self.batch_size = 2  # Process 2 keywords per batch
        self.max_pages_per_keyword = 5  # 5 pages per keyword
        self.concurrent_browsers = min(self.max_workers, 2)  # Conservative browser instances
        
        # Results storage
        self.all_jobs = []
        self.job_queue = Queue()
        self.stats = {
            'keywords_processed': 0,
            'pages_scraped': 0,
            'jobs_found': 0,
            'duplicates_skipped': 0,
            'start_time': None,
            'end_time': None
        }
        
        console.print(f"[bold green]🚀 Parallel Job Scraper initialized[/bold green]")
        console.print(f"[cyan]💪 Using {self.max_workers} workers for {len(self.keywords)} keywords[/cyan]")
        console.print(f"[cyan]🌐 {self.concurrent_browsers} concurrent browser instances[/cyan]")

    def scrape_jobs_parallel(self, sites: List[str] = None, detailed_scraping: bool = True) -> List[Dict]:
        """
        Parallel job scraping using concurrent processing.

        Args:
            sites: List of sites to scrape (default: ['eluta'])
            detailed_scraping: Whether to perform detailed scraping for company URLs

        Returns:
            List of scraped jobs
        """
        if sites is None:
            sites = ['eluta']
            
        self.stats['start_time'] = time.time()
        console.print(f"\n[bold blue]🚀 Starting parallel scraping session[/bold blue]")
        console.print(f"[cyan]🎯 Target: {len(self.keywords)} keywords with detailed scraping: {detailed_scraping}[/cyan]")

        # Create keyword batches for parallel processing
        keyword_batches = self._create_keyword_batches()

        with Progress() as progress:
            # Create progress tasks
            main_task = progress.add_task("[green]Overall Progress", total=len(self.keywords))
            batch_task = progress.add_task("[blue]Current Batch", total=len(keyword_batches))

            # Process batches in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all batch jobs
                future_to_batch = {
                    executor.submit(
                        self._process_keyword_batch,
                        batch,
                        batch_idx,
                        detailed_scraping,
                        progress,
                        main_task
                    ): batch_idx
                    for batch_idx, batch in enumerate(keyword_batches)
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_batch):
                    batch_idx = future_to_batch[future]
                    try:
                        batch_jobs = future.result()
                        self.all_jobs.extend(batch_jobs)
                        progress.update(batch_task, advance=1)
                        
                        console.print(f"[green]✅ Batch {batch_idx + 1} complete: {len(batch_jobs)} jobs[/green]")
                        
                    except Exception as e:
                        console.print(f"[red]❌ Batch {batch_idx + 1} failed: {e}[/red]")
        
        self.stats['end_time'] = time.time()
        self._print_performance_stats()

        return self.all_jobs
    
    def _create_keyword_batches(self) -> List[List[str]]:
        """Create batches of keywords for parallel processing."""
        batches = []
        for i in range(0, len(self.keywords), self.batch_size):
            batch = self.keywords[i:i + self.batch_size]
            batches.append(batch)
        return batches
    
    def _process_keyword_batch(self, keywords: List[str], batch_idx: int, detailed_scraping: bool,
                              progress: Progress, main_task: TaskID) -> List[Dict]:
        """Process a batch of keywords in parallel."""
        batch_jobs = []

        try:
            # Create a separate browser context for this batch
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                batch_jobs = loop.run_until_complete(
                    self._async_process_batch(keywords, batch_idx, detailed_scraping, progress, main_task)
                )
            finally:
                loop.close()

        except Exception as e:
            console.print(f"[red]❌ Error processing batch {batch_idx}: {e}[/red]")

        return batch_jobs
    
    async def _async_process_batch(self, keywords: List[str], batch_idx: int, detailed_scraping: bool,
                                  progress: Progress, main_task: TaskID) -> List[Dict]:
        """Async processing of keyword batch."""
        batch_jobs = []

        async with async_playwright() as p:
            # Launch browser for this batch
            browser = await p.chromium.launch(
                headless=True,  # Headless for performance
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )

            try:
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )

                # Process each keyword in this batch
                for keyword in keywords:
                    try:
                        keyword_jobs = await self._async_scrape_keyword(
                            context, keyword, detailed_scraping
                        )
                        batch_jobs.extend(keyword_jobs)

                        # Update progress
                        progress.update(main_task, advance=1)
                        self.stats['keywords_processed'] += 1

                        console.print(f"[green]✅ Keyword '{keyword}' complete: {len(keyword_jobs)} jobs[/green]")

                        # Small delay between keywords to avoid rate limiting
                        await asyncio.sleep(random.uniform(0.5, 1.5))

                    except Exception as e:
                        console.print(f"[red]❌ Error scraping keyword '{keyword}': {e}[/red]")
                        progress.update(main_task, advance=1)

            finally:
                await browser.close()

        return batch_jobs
    
    async def _async_scrape_keyword(self, context, keyword: str, detailed_scraping: bool) -> List[Dict]:
        """Async scraping of a single keyword with dynamic pagination."""
        keyword_jobs = []
        page = await context.new_page()

        try:
            page_num = 1
            consecutive_old_pages = 0
            max_consecutive_old = 2  # Stop after 2 pages of old jobs

            while page_num <= self.max_pages_per_keyword:
                console.print(f"[cyan]📄 Scraping '{keyword}' - Page {page_num}[/cyan]")

                # Scrape this page
                page_jobs, has_old_jobs = await self._async_scrape_page(
                    page, keyword, page_num, detailed_scraping
                )

                if not page_jobs:
                    console.print(f"[yellow]⚠️ No jobs found on page {page_num} for '{keyword}'[/yellow]")
                    break

                keyword_jobs.extend(page_jobs)
                self.stats['pages_scraped'] += 1
                self.stats['jobs_found'] += len(page_jobs)

                # Dynamic termination logic
                if has_old_jobs:
                    consecutive_old_pages += 1
                    console.print(f"[yellow]⚠️ Old jobs detected on page {page_num} (consecutive: {consecutive_old_pages})[/yellow]")

                    if consecutive_old_pages >= max_consecutive_old:
                        console.print(f"[yellow]🛑 Stopping '{keyword}' - too many old jobs[/yellow]")
                        break
                else:
                    consecutive_old_pages = 0  # Reset counter

                page_num += 1

                # Optimized pagination delay for multi-core systems
                await asyncio.sleep(random.uniform(0.3, 0.8))

        finally:
            await page.close()

        return keyword_jobs
    
    async def _async_scrape_page(self, page, keyword: str, page_num: int, detailed_scraping: bool) -> tuple:
        """Async scraping using our proven working method."""
        try:
            # Build search URL
            location = self.profile.get("location", "Toronto")
            search_url = f"https://www.eluta.ca/search?q={keyword}&l={location}"
            if page_num > 1:
                search_url += f"&pg={page_num}"

            # Navigate to page
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # Wait for JS to load

            # Find job containers using proven selector
            job_elements = await page.query_selector_all(".organic-job")

            if not job_elements:
                return [], False

            page_jobs = []
            has_old_jobs = False

            # Process each job using our proven method
            for i, job_elem in enumerate(job_elements[:10]):  # Limit for performance
                try:
                    job_data = await self._async_extract_job_data(job_elem, page, i+1)
                    if job_data:
                        page_jobs.append(job_data)

                        # Check if job is old (simplified check)
                        if "days ago" in job_data.get("description", ""):
                            has_old_jobs = True

                    # Small delay between jobs
                    await asyncio.sleep(0.5)

                except Exception as e:
                    console.print(f"[yellow]⚠️ Error processing job {i+1}: {e}[/yellow]")
                    continue

            return page_jobs, has_old_jobs

        except Exception as e:
            console.print(f"[red]❌ Error scraping page {page_num} for '{keyword}': {e}[/red]")
            return [], False

    async def _async_extract_job_data(self, job_elem, page, job_number: int) -> dict:
        """Async job data extraction using proven working method."""
        try:
            # Extract basic data from text
            text = await job_elem.inner_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            if len(lines) < 2:
                return None

            job_data = {
                "title": "",
                "company": "",
                "location": "",
                "salary": "",
                "description": "",
                "url": "",
                "apply_url": "",
                "source": "eluta.ca",
                "ats_system": "",
                "scraped_at": time.time(),
                "deep_scraped": False
            }

            # Parse title and salary
            title_line = lines[0]
            import re
            salary_match = re.search(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?', title_line)
            if salary_match:
                job_data["salary"] = salary_match.group(0)
                job_data["title"] = title_line.replace(salary_match.group(0), "").strip()
            else:
                job_data["title"] = title_line

            # Parse company
            if len(lines) > 1:
                job_data["company"] = lines[1].replace("TOP EMPLOYER", "").strip()

            # Parse location
            if len(lines) > 2:
                job_data["location"] = lines[2]

            # Parse description
            if len(lines) > 3:
                job_data["description"] = " ".join(lines[3:])[:200] + "..."

            # Try to get real URL using proven expect_popup method (async version)
            real_url = await self._async_get_real_job_url(job_elem, page, job_number)
            if real_url:
                job_data["apply_url"] = real_url
                job_data["url"] = real_url
                job_data["ats_system"] = self._detect_ats_system(real_url)
                job_data["deep_scraped"] = True
            else:
                job_data["url"] = page.url
                job_data["apply_url"] = page.url

            return job_data

        except Exception as e:
            console.print(f"[yellow]⚠️ Error extracting job {job_number}: {e}[/yellow]")
            return None

    async def _async_get_real_job_url(self, job_elem, page, job_number: int) -> str:
        """Async version of proven URL extraction method."""
        try:
            # Find job title link
            links = await job_elem.query_selector_all("a")
            title_link = None

            for link in links:
                link_text = await link.inner_text()
                if link_text and len(link_text.strip()) > 10:
                    title_link = link
                    break

            if not title_link:
                return None

            # Use async version of expect_popup
            async with page.expect_popup(timeout=5000) as popup_info:
                await title_link.click()

            popup = await popup_info.value
            popup_url = popup.url

            # Close popup immediately
            await popup.close()

            return popup_url

        except Exception as e:
            return None

    def _detect_ats_system(self, url: str) -> str:
        """Detect ATS system from URL."""
        if not url:
            return "Unknown"

        ats_systems = {
            "workday": "Workday",
            "myworkday": "Workday",
            "ultipro": "UltiPro",
            "greenhouse": "Greenhouse",
            "lever.co": "Lever",
            "icims": "iCIMS",
            "bamboohr": "BambooHR",
            "smartrecruiters": "SmartRecruiters",
            "jobvite": "Jobvite",
            "taleo": "Taleo",
            "successfactors": "SuccessFactors"
        }

        url_lower = url.lower()
        for keyword, system in ats_systems.items():
            if keyword in url_lower:
                return system

        return "Company Website"

    def _print_performance_stats(self):
        """Print comprehensive performance statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']

        console.print(f"\n[bold green]🎉 PARALLEL SCRAPING COMPLETE[/bold green]")
        console.print(f"[cyan]⏱️  Total time: {duration:.1f} seconds[/cyan]")
        console.print(f"[cyan]🔍 Keywords processed: {self.stats['keywords_processed']}/{len(self.keywords)}[/cyan]")
        console.print(f"[cyan]📄 Pages scraped: {self.stats['pages_scraped']}[/cyan]")
        console.print(f"[cyan]💼 Jobs found: {self.stats['jobs_found']}[/cyan]")

        if duration > 0:
            jobs_per_minute = (self.stats['jobs_found'] / duration) * 60
            pages_per_minute = (self.stats['pages_scraped'] / duration) * 60
            console.print(f"[bold cyan]⚡ Performance: {jobs_per_minute:.1f} jobs/min, {pages_per_minute:.1f} pages/min[/bold cyan]")

        console.print(f"[bold yellow]💪 Used {self.max_workers} parallel workers[/bold yellow]")


# Note: UltraParallelScraper has been renamed to ParallelJobScraper for professional naming standards
