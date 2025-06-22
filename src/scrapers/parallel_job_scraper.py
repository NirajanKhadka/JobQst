#!/usr/bin/env python3
"""
Parallel Job Scraper System
Modular, multi-process job scraping with parallel browser sessions
and intelligent task distribution for maximum efficiency.
"""

import asyncio
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import queue
import traceback

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel
from playwright.async_api import async_playwright

from job_database import get_job_db
import utils

console = Console()

@dataclass
class ScrapingTask:
    """Individual scraping task."""
    task_id: str
    task_type: str  # 'basic_scrape', 'detail_scrape', 'url_extract'
    keyword: str
    page_number: int
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class JobData:
    """Enhanced job data structure."""
    basic_info: Dict
    detailed_info: Optional[Dict] = None
    real_url: Optional[str] = None
    experience_level: str = "Unknown"
    confidence_score: float = 0.0
    needs_detail_scraping: bool = False

class ParallelJobScraper:
    """
    Parallel job scraping system with multiple workers and intelligent task distribution.
    """
    
    def __init__(self, profile_name: str = "Nirajan", num_workers: int = 3):
        """Initialize parallel scraper."""
        self.profile_name = profile_name
        self.profile = utils.load_profile(profile_name)
        self.db = get_job_db(profile_name)
        
        # Worker configuration
        self.num_workers = min(num_workers, mp.cpu_count())
        self.num_browser_sessions = 2  # Multiple browser sessions
        
        # Get keywords from profile
        self.keywords = self.profile.get("keywords", [])
        self.skills = self.profile.get("skills", [])
        self.search_terms = list(set(self.keywords + self.skills))
        
        # Enhanced experience filtering (more robust)
        self.experience_filters = {
            'definitely_entry_level': [
                'junior', 'entry', 'entry level', 'entry-level', 'associate', 
                'graduate', 'new grad', 'recent graduate', 'trainee', 'coordinator',
                '0-2 years', '1-2 years', '0-1 years', 'level i', 'level 1',
                'intern', 'internship', 'co-op', 'coop', 'student'
            ],
            'definitely_too_senior': [
                'senior', 'sr.', 'sr ', 'lead', 'principal', 'manager', 'director',
                'supervisor', 'head of', 'chief', 'vp', 'vice president',
                '5+ years', '7+ years', '10+ years', 'experienced',
                'expert', 'architect', 'staff engineer'
            ],
            'ambiguous_terms': [
                'analyst', 'developer', 'engineer', 'specialist', 'consultant'
            ]
        }
        
        # Task queues for different types of work
        self.basic_scrape_queue = asyncio.Queue()
        self.detail_scrape_queue = asyncio.Queue()
        self.url_extract_queue = asyncio.Queue()
        
        # Results storage
        self.scraped_jobs = []
        self.failed_tasks = []
        
        # Statistics
        self.stats = {
            'tasks_created': 0,
            'tasks_completed': 0,
            'jobs_scraped': 0,
            'jobs_saved': 0,
            'parallel_sessions': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def start_parallel_scraping(self, max_jobs_per_keyword: int = 50) -> List[Dict]:
        """
        Start parallel scraping with multiple workers and browser sessions.
        
        Args:
            max_jobs_per_keyword: Maximum jobs to scrape per keyword
            
        Returns:
            List of scraped job data
        """
        console.print(Panel.fit("🚀 PARALLEL JOB SCRAPING SYSTEM", style="bold blue"))
        console.print(f"[cyan]🔧 Workers: {self.num_workers}[/cyan]")
        console.print(f"[cyan]🌐 Browser Sessions: {self.num_browser_sessions}[/cyan]")
        console.print(f"[cyan]🔍 Keywords: {len(self.search_terms)}[/cyan]")
        console.print(f"[cyan]📊 Expected Jobs: {len(self.search_terms) * max_jobs_per_keyword}[/cyan]")
        
        self.stats['start_time'] = time.time()
        
        # Create scraping tasks
        await self._create_scraping_tasks(max_jobs_per_keyword)
        
        # Start parallel workers
        workers = []
        
        # Basic scraping workers (multiple browser sessions)
        for i in range(self.num_browser_sessions):
            worker = asyncio.create_task(
                self._basic_scraping_worker(f"BasicWorker-{i+1}")
            )
            workers.append(worker)
        
        # Detail scraping worker
        detail_worker = asyncio.create_task(
            self._detail_scraping_worker("DetailWorker")
        )
        workers.append(detail_worker)
        
        # URL extraction worker
        url_worker = asyncio.create_task(
            self._url_extraction_worker("URLWorker")
        )
        workers.append(url_worker)
        
        # Progress monitoring
        monitor_task = asyncio.create_task(self._monitor_progress())
        workers.append(monitor_task)
        
        try:
            # Wait for all workers to complete
            await asyncio.gather(*workers)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ Stopping parallel scraping...[/yellow]")
            for worker in workers:
                worker.cancel()
        
        self.stats['end_time'] = time.time()
        
        # Process and save results
        await self._process_final_results()
        
        return self.scraped_jobs
    
    async def _create_scraping_tasks(self, max_jobs_per_keyword: int) -> None:
        """Create scraping tasks for all keywords and pages."""
        console.print("[cyan]📋 Creating scraping tasks...[/cyan]")
        
        pages_per_keyword = 5
        task_id = 0
        
        for keyword in self.search_terms:
            for page_num in range(1, pages_per_keyword + 1):
                task = ScrapingTask(
                    task_id=f"task_{task_id}",
                    task_type="basic_scrape",
                    keyword=keyword,
                    page_number=page_num,
                    priority=1 if page_num <= 2 else 2  # Higher priority for first 2 pages
                )
                
                await self.basic_scrape_queue.put(task)
                task_id += 1
                self.stats['tasks_created'] += 1
        
        console.print(f"[green]✅ Created {self.stats['tasks_created']} scraping tasks[/green]")
    
    async def _basic_scraping_worker(self, worker_name: str) -> None:
        """Basic scraping worker - handles main scraping loop."""
        console.print(f"[cyan]🚀 Starting {worker_name}...[/cyan]")
        max_restarts = 3
        restart_count = 0
        while restart_count < max_restarts:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=False,
                        args=["--start-maximized", f"--user-data-dir=./browser_data_{worker_name}"]
                    )
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080}
                    )
                    page = await context.new_page()
                    try:
                        while True:
                            try:
                                # Get next task (with timeout to allow graceful shutdown)
                                task = await asyncio.wait_for(
                                    self.basic_scrape_queue.get(), 
                                    timeout=30.0
                                )
                                console.print(f"[cyan]{worker_name}: Processing {task.keyword} page {task.page_number}[/cyan]")
                                # Scrape basic job info
                                jobs = await self._scrape_basic_job_info(page, task)
                                # Process each job
                                for job_data in jobs:
                                    # Apply robust experience filtering
                                    filtered_job = self._apply_robust_filtering(job_data)
                                    if filtered_job:
                                        self.scraped_jobs.append(filtered_job)
                                        # Queue for detailed scraping if needed
                                        if filtered_job.needs_detail_scraping:
                                            detail_task = ScrapingTask(
                                                task_id=f"detail_{len(self.scraped_jobs)}",
                                                task_type="detail_scrape",
                                                keyword=task.keyword,
                                                page_number=0
                                            )
                                            await self.detail_scrape_queue.put((detail_task, filtered_job))
                                self.stats['tasks_completed'] += 1
                                self.stats['jobs_scraped'] += len(jobs)
                                # Resource monitoring
                                open_pages = len(context.pages)
                                console.print(f"[dim]{worker_name}: Open pages: {open_pages}[/dim]")
                                # Small delay between tasks
                                await asyncio.sleep(1)
                            except asyncio.TimeoutError:
                                # No more tasks, worker can exit
                                break
                            except Exception as e:
                                console.print(f"[red]{worker_name} error: {e}[/red]")
                                traceback.print_exc()
                                if task.retry_count < task.max_retries:
                                    task.retry_count += 1
                                    await self.basic_scrape_queue.put(task)
                                else:
                                    self.failed_tasks.append(task)
                    finally:
                        await context.close()
                        await browser.close()
                        console.print(f"[yellow]{worker_name} finished[/yellow]")
                break  # Exit loop if successful
            except Exception as e:
                restart_count += 1
                console.print(f"[red]{worker_name} browser crash detected (restart {restart_count}/{max_restarts}): {e}[/red]")
                traceback.print_exc()
                await asyncio.sleep(2)  # Short delay before restart
        if restart_count >= max_restarts:
            console.print(f"[red]{worker_name} exceeded max restarts. Worker exiting.[/red]")
    
    async def _detail_scraping_worker(self, worker_name: str) -> None:
        """Detail scraping worker - handles detailed job information extraction."""
        console.print(f"[cyan]🔍 Starting {worker_name}...[/cyan]")
        max_restarts = 3
        restart_count = 0
        while restart_count < max_restarts:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(
                        headless=False,
                        args=["--start-maximized", f"--user-data-dir=./browser_data_{worker_name}"]
                    )
                    context = await browser.new_context()
                    page = await context.new_page()
                    try:
                        while True:
                            try:
                                # Get next detail task
                                task_data = await asyncio.wait_for(
                                    self.detail_scrape_queue.get(),
                                    timeout=60.0
                                )
                                task, job_data = task_data
                                console.print(f"[cyan]{worker_name}: Extracting details for {job_data.basic_info.get('title', 'Unknown')}[/cyan]")
                                # Extract detailed information
                                detailed_info = await self._extract_detailed_job_info(page, job_data)
                                job_data.detailed_info = detailed_info
                                # Re-evaluate experience level with detailed info
                                job_data.experience_level = self._determine_experience_level_detailed(job_data)
                                await asyncio.sleep(2)
                            except asyncio.TimeoutError:
                                break
                            except Exception as e:
                                console.print(f"[red]{worker_name} error: {e}[/red]")
                                traceback.print_exc()
                    finally:
                        await context.close()
                        await browser.close()
                        console.print(f"[yellow]{worker_name} finished[/yellow]")
                break  # Exit loop if successful
            except Exception as e:
                restart_count += 1
                console.print(f"[red]{worker_name} browser crash detected (restart {restart_count}/{max_restarts}): {e}[/red]")
                traceback.print_exc()
                await asyncio.sleep(2)
        if restart_count >= max_restarts:
            console.print(f"[red]{worker_name} exceeded max restarts. Worker exiting.[/red]")
    
    async def _url_extraction_worker(self, worker_name: str) -> None:
        """URL extraction worker - handles real URL extraction."""
        console.print(f"[cyan]🔗 Starting {worker_name}...[/cyan]")
        
        # This worker processes jobs that need real URL extraction
        # Implementation would be similar to detail worker but focused on URL extraction
        await asyncio.sleep(1)  # Placeholder
        console.print(f"[yellow]{worker_name} finished[/yellow]")
    
    async def _scrape_basic_job_info(self, page, task: ScrapingTask) -> List[JobData]:
        """Scrape basic job information from a search results page."""
        jobs = []
        
        try:
            # Build search URL
            search_url = f"https://www.eluta.ca/search?q={task.keyword}&l=&posted=14&pg={task.page_number}"
            
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            
            # Get job elements
            job_elements = await page.query_selector_all('.organic-job')
            
            for i, job_element in enumerate(job_elements):
                try:
                    job_text = await job_element.inner_text()
                    lines = [line.strip() for line in job_text.split('\n') if line.strip()]
                    
                    if len(lines) >= 2:
                        basic_info = {
                            "title": lines[0],
                            "company": lines[1].replace("TOP EMPLOYER", "").strip(),
                            "location": lines[2] if len(lines) > 2 else "",
                            "description": " ".join(lines[3:])[:300] if len(lines) > 3 else "",
                            "source": "eluta.ca",
                            "scraped_date": datetime.now().isoformat(),
                            "search_keyword": task.keyword,
                            "page_number": task.page_number
                        }
                        
                        # Try to get URL
                        try:
                            link = await job_element.query_selector('a')
                            if link:
                                href = await link.get_attribute('href')
                                basic_info["eluta_url"] = href
                        except:
                            pass
                        
                        job_data = JobData(basic_info=basic_info)
                        jobs.append(job_data)
                
                except Exception as e:
                    continue
        
        except Exception as e:
            console.print(f"[red]Error scraping {task.keyword} page {task.page_number}: {e}[/red]")
        
        return jobs
    
    def _apply_robust_filtering(self, job_data: JobData) -> Optional[JobData]:
        """
        Apply robust experience filtering - save jobs when experience can't be determined.
        """
        title = job_data.basic_info.get('title', '').lower()
        description = job_data.basic_info.get('description', '').lower()
        job_text = f"{title} {description}"
        
        # Check for definitely too senior positions
        for senior_term in self.experience_filters['definitely_too_senior']:
            if senior_term in job_text:
                console.print(f"[red]❌ Too senior: {job_data.basic_info.get('title', 'Unknown')}[/red]")
                return None  # Definitely exclude
        
        # Check for definitely entry level
        for entry_term in self.experience_filters['definitely_entry_level']:
            if entry_term in job_text:
                job_data.experience_level = "Entry Level"
                job_data.confidence_score = 0.9
                console.print(f"[green]✅ Entry level: {job_data.basic_info.get('title', 'Unknown')}[/green]")
                return job_data
        
        # Check for ambiguous terms - these need detailed analysis
        has_ambiguous = any(term in job_text for term in self.experience_filters['ambiguous_terms'])
        
        if has_ambiguous:
            job_data.experience_level = "Needs Analysis"
            job_data.confidence_score = 0.5
            job_data.needs_detail_scraping = True
            console.print(f"[yellow]📋 Needs analysis: {job_data.basic_info.get('title', 'Unknown')}[/yellow]")
            return job_data
        
        # If we can't determine experience level, save it anyway (robust approach)
        job_data.experience_level = "Unknown - Saved"
        job_data.confidence_score = 0.3
        console.print(f"[cyan]💾 Unknown experience - saved: {job_data.basic_info.get('title', 'Unknown')}[/cyan]")
        return job_data
    
    async def _extract_detailed_job_info(self, page, job_data: JobData) -> Dict:
        """Extract detailed job information from job page."""
        # Placeholder for detailed extraction
        return {"detailed_requirements": "To be implemented"}
    
    def _determine_experience_level_detailed(self, job_data: JobData) -> str:
        """Determine experience level using detailed information."""
        # Placeholder for detailed analysis
        return job_data.experience_level
    
    async def _monitor_progress(self) -> None:
        """Monitor and display progress of parallel scraping."""
        while True:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                # Display current statistics
                console.print(f"[dim]📊 Progress: {self.stats['tasks_completed']}/{self.stats['tasks_created']} tasks, {self.stats['jobs_scraped']} jobs scraped[/dim]")
                
                # Check if all tasks are complete
                if (self.stats['tasks_completed'] >= self.stats['tasks_created'] and 
                    self.basic_scrape_queue.empty() and 
                    self.detail_scrape_queue.empty()):
                    break
                    
            except asyncio.CancelledError:
                break
    
    async def _process_final_results(self) -> None:
        """Process and save final results."""
        console.print("\n[bold]📊 PROCESSING FINAL RESULTS[/bold]")
        
        # Remove duplicates
        unique_jobs = self._remove_duplicates()
        
        # Save to database
        saved_count = 0
        for job_data in unique_jobs:
            try:
                # Convert JobData to dict for database
                job_dict = job_data.basic_info.copy()
                job_dict.update({
                    'experience_level': job_data.experience_level,
                    'confidence_score': job_data.confidence_score,
                    'url': job_data.real_url or job_data.basic_info.get('eluta_url', ''),
                    'apply_url': job_data.real_url or job_data.basic_info.get('eluta_url', ''),
                    'ats_system': 'Eluta Redirect' if not job_data.real_url else 'Unknown'
                })
                
                self.db.add_job(job_dict)
                saved_count += 1
                
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not save job: {e}[/yellow]")
        
        self.stats['jobs_saved'] = saved_count
        
        # Display final statistics
        self._display_final_statistics()
    
    def _remove_duplicates(self) -> List[JobData]:
        """Remove duplicate jobs."""
        seen = set()
        unique_jobs = []
        
        for job_data in self.scraped_jobs:
            # Create unique identifier
            title = job_data.basic_info.get('title', '').lower()
            company = job_data.basic_info.get('company', '').lower()
            identifier = f"{title}_{company}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique_jobs.append(job_data)
        
        console.print(f"[cyan]🔄 Removed {len(self.scraped_jobs) - len(unique_jobs)} duplicates[/cyan]")
        return unique_jobs
    
    def _display_final_statistics(self) -> None:
        """Display final scraping statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        console.print("\n" + "="*80)
        console.print(Panel.fit("🚀 PARALLEL SCRAPING RESULTS", style="bold green"))
        
        stats_table = Table(title="Performance Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Duration", f"{duration:.1f} seconds")
        stats_table.add_row("Tasks Created", str(self.stats['tasks_created']))
        stats_table.add_row("Tasks Completed", str(self.stats['tasks_completed']))
        stats_table.add_row("Jobs Scraped", str(self.stats['jobs_scraped']))
        stats_table.add_row("Jobs Saved", str(self.stats['jobs_saved']))
        stats_table.add_row("Failed Tasks", str(len(self.failed_tasks)))
        stats_table.add_row("Workers Used", str(self.num_workers))
        stats_table.add_row("Browser Sessions", str(self.num_browser_sessions))
        
        if duration > 0:
            stats_table.add_row("Jobs per Second", f"{self.stats['jobs_scraped'] / duration:.2f}")
        
        console.print(stats_table)


# Convenience function
async def run_parallel_scraping(profile_name: str = "Nirajan", 
                               num_workers: int = 3,
                               max_jobs_per_keyword: int = 50) -> List[Dict]:
    """Run parallel job scraping."""
    scraper = ParallelJobScraper(profile_name, num_workers)
    return await scraper.start_parallel_scraping(max_jobs_per_keyword)


if __name__ == "__main__":
    asyncio.run(run_parallel_scraping())
