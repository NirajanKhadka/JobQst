#!/usr/bin/env python3
"""
External Job Description Scraper
Parallel scraping of job descriptions from external sites (non-Eluta).
Respects Eluta anti-bot by only scraping external job sites in parallel.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from playwright.async_api import async_playwright, Page
from rich.console import Console
from rich.progress import Progress, TaskID

from .enhanced_job_description_scraper import ImprovedJobDescriptionScraper

console = Console()


class ExternalJobDescriptionScraper(ImprovedJobDescriptionScraper):
    """
    Parallel scraper for external job sites (Workday, Greenhouse, company pages).
    Does NOT scrape Eluta directly - only external sites that Eluta URLs point to.
    """

    def __init__(self, num_workers: int = 6):
        super().__init__()
        self.num_workers = num_workers
        self.stats = {
            "total_jobs": 0,
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "workers_used": num_workers,
            "start_time": None,
            "end_time": None,
            "processing_time": 0.0,
            "jobs_per_second": 0.0
        }

    async def scrape_external_jobs_parallel(self, job_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape job descriptions from external sites in parallel.
        
        Args:
            job_urls: List of job URLs from Eluta (pointing to external sites)
            
        Returns:
            List of job dictionaries with scraped descriptions
        """
        if not job_urls:
            console.print("[yellow]⚠️ No job URLs provided for external scraping[/yellow]")
            return []

        self.stats["total_jobs"] = len(job_urls)
        self.stats["start_time"] = time.time()
        
        console.print(f"[cyan]🚀 Starting parallel external job scraping[/cyan]")
        console.print(f"[cyan]📋 {len(job_urls)} jobs to scrape with {self.num_workers} workers[/cyan]")

        # Filter out any Eluta URLs (safety check)
        external_urls = [url for url in job_urls if "eluta.ca" not in url.lower()]
        if len(external_urls) != len(job_urls):
            console.print(f"[yellow]⚠️ Filtered out {len(job_urls) - len(external_urls)} Eluta URLs[/yellow]")

        results = []
        
        async with async_playwright() as p:
            # Create persistent browsers for workers
            browsers = []
            try:
                for i in range(self.num_workers):
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                    browsers.append(browser)

                # Create job queue
                job_queue = asyncio.Queue()
                for url in external_urls:
                    await job_queue.put(url)

                # Start worker tasks
                with Progress() as progress:
                    task = progress.add_task(
                        "[green]Scraping external job descriptions...", 
                        total=len(external_urls)
                    )

                    worker_tasks = [
                        self._external_worker_loop(browser, worker_id, job_queue, progress, task)
                        for worker_id, browser in enumerate(browsers)
                    ]

                    # Wait for all workers to complete
                    worker_results = await asyncio.gather(*worker_tasks, return_exceptions=True)

                    # Collect results from all workers
                    for worker_result in worker_results:
                        if isinstance(worker_result, list):
                            results.extend(worker_result)
                        elif isinstance(worker_result, Exception):
                            console.print(f"[red]❌ Worker error: {worker_result}[/red]")

            finally:
                # Clean up browsers
                for browser in browsers:
                    try:
                        await browser.close()
                    except:
                        pass

        # Update statistics
        self.stats["end_time"] = time.time()
        self.stats["processing_time"] = self.stats["end_time"] - self.stats["start_time"]
        self.stats["successful_scrapes"] = len(results)
        self.stats["failed_scrapes"] = len(external_urls) - len(results)
        self.stats["jobs_per_second"] = len(results) / self.stats["processing_time"] if self.stats["processing_time"] > 0 else 0

        console.print(f"[green]✅ External scraping complete: {len(results)} jobs scraped[/green]")
        console.print(f"[green]📊 Speed: {self.stats['jobs_per_second']:.2f} jobs/sec[/green]")

        return results

    async def _external_worker_loop(
        self, 
        browser, 
        worker_id: int, 
        job_queue: asyncio.Queue, 
        progress: Progress, 
        task: TaskID
    ) -> List[Dict[str, Any]]:
        """
        Worker loop for processing external job URLs.
        
        Args:
            browser: Playwright browser instance
            worker_id: Unique worker identifier
            job_queue: Queue of job URLs to process
            progress: Rich progress bar
            task: Progress task ID
            
        Returns:
            List of scraped job data
        """
        worker_results = []
        context = None
        
        try:
            # Create browser context for this worker
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
            )
            page = await context.new_page()
            page.set_default_timeout(30000)  # 30 second timeout

            console.print(f"[dim]🔧 Worker {worker_id} started[/dim]")

            while True:
                try:
                    # Get next job URL with timeout
                    job_url = await asyncio.wait_for(job_queue.get(), timeout=1.0)
                    
                    console.print(f"[dim]Worker {worker_id}: Processing {job_url[:50]}...[/dim]")
                    
                    # Scrape job description using parent class method
                    job_data = await self.scrape_job_description(job_url, page)
                    
                    if job_data and job_data.get("description"):
                        # Add worker metadata
                        job_data["worker_id"] = worker_id
                        job_data["scraping_method"] = "external_parallel"
                        job_data["scraped_at"] = datetime.now().isoformat()
                        
                        worker_results.append(job_data)
                        console.print(f"[green]✅ Worker {worker_id}: Scraped {job_data.get('title', 'Unknown')[:30]}...[/green]")
                    else:
                        console.print(f"[yellow]⚠️ Worker {worker_id}: Failed to scrape {job_url[:50]}...[/yellow]")
                    
                    # Mark job as done and update progress
                    job_queue.task_done()
                    progress.update(task, advance=1)
                    
                    # Small delay to be respectful
                    await asyncio.sleep(0.5)
                    
                except asyncio.TimeoutError:
                    # No more jobs in queue
                    break
                except Exception as e:
                    console.print(f"[red]❌ Worker {worker_id} error: {e}[/red]")
                    # Continue processing other jobs
                    continue

        except Exception as e:
            console.print(f"[red]❌ Worker {worker_id} setup error: {e}[/red]")
        finally:
            if context:
                try:
                    await context.close()
                except:
                    pass

        console.print(f"[dim]🏁 Worker {worker_id} finished: {len(worker_results)} jobs scraped[/dim]")
        return worker_results

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return self.stats.copy()

    async def test_single_job(self, job_url: str) -> Dict[str, Any]:
        """Test scraping a single job URL (for debugging)."""
        console.print(f"[cyan]🧪 Testing single job scrape: {job_url}[/cyan]")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Non-headless for debugging
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                result = await self.scrape_job_description(job_url, page)
                console.print(f"[green]✅ Test result: {result.get('title', 'No title')}[/green]")
                return result
            finally:
                await context.close()
                await browser.close()


# Convenience function
def get_external_job_scraper(num_workers: int = 6) -> ExternalJobDescriptionScraper:
    """Get configured external job scraper instance."""
    return ExternalJobDescriptionScraper(num_workers=num_workers)


# CLI test function
async def test_external_scraper():
    """Test the external scraper with sample URLs."""
    test_urls = [
        "https://example-company.workday.com/job/123",
        "https://boards.greenhouse.io/company/jobs/456"
    ]
    
    scraper = ExternalJobDescriptionScraper(num_workers=2)
    results = await scraper.scrape_external_jobs_parallel(test_urls)
    
    console.print(f"[cyan]Test Results: {len(results)} jobs scraped[/cyan]")
    for result in results:
        console.print(f"[green]- {result.get('title', 'Unknown')} at {result.get('company', 'Unknown')}[/green]")


# For testing this scraper, use: python -m pytest tests/scrapers/
# Example usage available in tests/ directory