#!/usr/bin/env python3
"""
Job Processor Queue System
Producer-consumer architecture with caching and real-time dashboard updates.
"""

import asyncio
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from queue import Queue, Empty
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel
from playwright.async_api import async_playwright

from .job_database import get_job_db
from ..scrapers.enhanced_job_description_scraper import EnhancedJobDescriptionScraper
from ..utils.language_detector import JobLanguageDetector
from ..analysis.hybrid_processor import HybridProcessingEngine, get_hybrid_processing_engine

console = Console()


@dataclass
class JobTask:
    """Job task for processing queue."""

    job_url: str
    job_id: str
    title: str
    company: str
    location: str
    search_keyword: str
    priority: int = 1
    created_at: str = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class ProcessingResult:
    """Result of job processing."""

    job_id: str
    success: bool
    data: Dict[str, Any]
    error: str = None
    processing_time: float = 0.0
    cached: bool = False
    processed_at: str = None

    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now().isoformat()


class JobCache:
    """Cache for job descriptions to avoid re-scraping."""

    def __init__(self, cache_dir: str = "cache/job_descriptions"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)  # Cache for 24 hours

    def _get_cache_key(self, job_url: str) -> str:
        """Generate cache key from job URL."""
        import hashlib
        return hashlib.md5(job_url.encode()).hexdigest()

    def get(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Get cached job description."""
        cache_key = self._get_cache_key(job_url)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)

            # Check if cache is still valid
            cached_time = datetime.fromisoformat(
                cached_data.get("cached_at", "1970-01-01T00:00:00")
            )
            if datetime.now() - cached_time > self.cache_ttl:
                cache_file.unlink()  # Remove expired cache
                return None

            return cached_data

        except Exception as e:
            console.print(f"[yellow]⚠️ Error reading cache: {e}[/yellow]")
            return None

    def set(self, job_url: str, data: Dict[str, Any]) -> bool:
        """Cache job description."""
        cache_key = self._get_cache_key(job_url)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            data["cached_at"] = datetime.now().isoformat()
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            console.print(f"[yellow]⚠️ Error writing cache: {e}[/yellow]")
            return False


class JobProcessor:
    """Individual job processor worker with enhanced analysis."""

    def __init__(
        self, worker_id: int, cache: JobCache, db, dashboard_callback: Optional[Callable] = None, user_profile: Optional[Dict] = None
    ):
        self.worker_id = worker_id
        self.cache = cache
        self.db = db
        self.dashboard_callback = dashboard_callback
        self.scraper = EnhancedJobDescriptionScraper()
        self.hybrid_processor = get_hybrid_processing_engine(user_profile)
        self.is_running = False

    async def process_job(self, job_task: JobTask) -> ProcessingResult:
        """Process a single job task."""
        start_time = time.time()

        try:
            console.print(f"[cyan]🔍 Worker {self.worker_id}: Processing {job_task.job_url}[/cyan]")

            # Check cache first
            cached_data = self.cache.get(job_task.job_url)
            if cached_data:
                console.print(f"[green]✅ Worker {self.worker_id}: Using cached data[/green]")
                result = ProcessingResult(
                    job_id=job_task.job_id,
                    success=True,
                    data=cached_data,
                    processing_time=time.time() - start_time,
                    cached=True,
                )
            else:
                # Scrape job description
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context()
                    page = await context.new_page()

                    try:
                        job_data = await self.scraper.scrape_job_description(job_task.job_url, page)

                        # ENHANCED: Process with hybrid processor for 95%+ reliability
                        console.print(f"[cyan]🧠 Worker {self.worker_id}: Running enhanced analysis...[/cyan]")
                        hybrid_result = self.hybrid_processor.process_job(job_data)
                        
                        # Merge scraped data with enhanced analysis
                        enhanced_job_data = {
                            **job_data,  # Original scraped data
                            # Enhanced analysis results
                            "enhanced_title": hybrid_result.title,
                            "enhanced_company": hybrid_result.company,
                            "enhanced_location": hybrid_result.location,
                            "enhanced_salary_range": hybrid_result.salary_range,
                            "enhanced_experience_level": hybrid_result.experience_level,
                            "enhanced_employment_type": hybrid_result.employment_type,
                            "enhanced_skills": hybrid_result.required_skills,
                            "enhanced_requirements": hybrid_result.job_requirements,
                            "enhanced_benefits": hybrid_result.extracted_benefits,
                            "compatibility_score": hybrid_result.compatibility_score,
                            "analysis_confidence": hybrid_result.analysis_confidence,
                            "custom_logic_confidence": hybrid_result.custom_logic_confidence,
                            "processing_method": hybrid_result.processing_method,
                            "reasoning": hybrid_result.reasoning,
                            "enhanced_processing_time": hybrid_result.total_processing_time
                        }

                        # Cache the enhanced result
                        self.cache.set(job_task.job_url, enhanced_job_data)

                        console.print(f"[green]✅ Worker {self.worker_id}: Enhanced analysis complete (confidence: {hybrid_result.analysis_confidence:.2f})[/green]")

                        result = ProcessingResult(
                            job_id=job_task.job_id,
                            success=True,
                            data=enhanced_job_data,
                            processing_time=time.time() - start_time,
                            cached=False,
                        )

                    finally:
                        await context.close()
                        await browser.close()

            # Update database
            self._update_database(job_task, result)

            # Notify dashboard
            if self.dashboard_callback:
                self.dashboard_callback(result)

            return result

        except Exception as e:
            console.print(f"[red]❌ Worker {self.worker_id}: Error processing job: {e}[/red]")
            return ProcessingResult(
                job_id=job_task.job_id,
                success=False,
                data={},
                error=str(e),
                processing_time=time.time() - start_time,
                cached=False,
            )

    def _update_database(self, job_task: JobTask, result: ProcessingResult):
        """Update database with enhanced processing result."""
        try:
            if result.success:
                # Update job with detailed information including enhanced analysis
                job_data = result.data
                
                # Prepare enhanced data for database storage
                enhanced_data = {
                    "description": job_data.get("description", ""),
                    "experience_requirements": json.dumps(job_data.get("experience_requirements", {})),
                    "skills_requirements": json.dumps(job_data.get("skills_requirements", {})),
                    "summary": job_data.get("summary", ""),
                    "ats_system": job_data.get("ats_system", "unknown"),
                    "processing_status": "enhanced_completed",
                    
                    # Enhanced analysis results
                    "enhanced_title": job_data.get("enhanced_title"),
                    "enhanced_company": job_data.get("enhanced_company"),
                    "enhanced_location": job_data.get("enhanced_location"),
                    "enhanced_salary_range": job_data.get("enhanced_salary_range"),
                    "enhanced_experience_level": job_data.get("enhanced_experience_level"),
                    "enhanced_employment_type": job_data.get("enhanced_employment_type"),
                    "enhanced_skills": json.dumps(job_data.get("enhanced_skills", [])),
                    "enhanced_requirements": json.dumps(job_data.get("enhanced_requirements", [])),
                    "enhanced_benefits": json.dumps(job_data.get("enhanced_benefits", [])),
                    "compatibility_score": job_data.get("compatibility_score", 0.0),
                    "analysis_confidence": job_data.get("analysis_confidence", 0.0),
                    "custom_logic_confidence": job_data.get("custom_logic_confidence", 0.0),
                    "processing_method": job_data.get("processing_method", "hybrid"),
                    "reasoning": job_data.get("reasoning", ""),
                    "enhanced_processing_time": job_data.get("enhanced_processing_time", 0.0)
                }
                
                self.db.update_job_details(job_task.job_id, **enhanced_data)
                
                console.print(f"[green]✅ Enhanced job data saved to database (confidence: {job_data.get('analysis_confidence', 0.0):.2f})[/green]")
                
            else:
                # Mark as failed
                self.db.update_job_details(
                    job_task.job_id, processing_status="failed", error_message=result.error
                )
        except Exception as e:
            console.print(f"[yellow]⚠️ Error updating database with enhanced data: {e}[/yellow]")
            # Fallback to basic update
            try:
                if result.success:
                    job_data = result.data
                    self.db.update_job_details(
                        job_task.job_id,
                        description=job_data.get("description", ""),
                        processing_status="completed",
                    )
            except Exception as fallback_error:
                console.print(f"[red]❌ Fallback database update also failed: {fallback_error}[/red]")


class JobProcessorQueue:
    """Main job processor queue with producer-consumer architecture."""

    def __init__(
        self, profile_name: str, num_workers: int = 2, dashboard_callback: Optional[Callable] = None
    ):
        self.profile_name = profile_name
        # Force single worker for sequential processing
        self.num_workers = 1  # Override to ensure sequential processing
        self.dashboard_callback = dashboard_callback

        # Initialize components
        self.db = get_job_db(profile_name)
        self.cache = JobCache()
        self.language_detector = JobLanguageDetector(french_threshold=0.4)  # 40% French threshold
        
        # Load user profile for enhanced processing
        self.user_profile = self._load_user_profile(profile_name)

        # Queue and workers
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.workers = []
        self.is_running = False

        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "cached": 0,
            "skipped_language": 0,
            "start_time": None,
            "last_update": None,
        }

        # Dashboard update timer
        self.dashboard_update_interval = 60  # 1 minute
        self.last_dashboard_update = time.time()

    def _load_user_profile(self, profile_name: str) -> Optional[Dict]:
        """Load user profile for enhanced processing."""
        try:
            from ..utils.profile_helpers import load_profile
            profile = load_profile(profile_name)
            if profile:
                console.print(f"[green]✅ Loaded user profile for enhanced processing: {profile_name}[/green]")
                return profile
            else:
                console.print(f"[yellow]⚠️ Profile '{profile_name}' not found, using default profile[/yellow]")
                return {}
        except Exception as e:
            console.print(f"[yellow]⚠️ Error loading profile: {e}[/yellow]")
            return {}

    def start(self):
        """Start the job processor queue."""
        console.print(
            Panel(
                f"[bold blue]🚀 Starting Job Processor Queue[/bold blue]\n"
                f"[cyan]Profile: {self.profile_name}[/cyan]\n"
                f"[cyan]Workers: {self.num_workers}[/cyan]\n"
                f"[cyan]Cache: Enabled[/cyan]",
                style="bold blue",
            )
        )

        self.is_running = True
        self.stats["start_time"] = datetime.now().isoformat()

        # Start workers with user profile for enhanced processing
        for i in range(self.num_workers):
            worker = JobProcessor(i + 1, self.cache, self.db, self.dashboard_callback, self.user_profile)
            self.workers.append(worker)

        # Start worker threads
        self.worker_threads = []
        for worker in self.workers:
            thread = threading.Thread(target=self._worker_loop, args=(worker,), daemon=True)
            thread.start()
            self.worker_threads.append(thread)

        # Start result processor
        self.result_thread = threading.Thread(target=self._result_processor_loop, daemon=True)
        self.result_thread.start()

        console.print(
            f"[green]✅ Job processor queue started with {self.num_workers} workers[/green]"
        )
        
        # Auto-load pending jobs from database
        self._load_pending_jobs()

    def _load_pending_jobs(self):
        """Load jobs with status 'scraped' from database, filter by language, and add to processing queue."""
        try:
            # Get jobs that need processing
            all_jobs = self.db.get_jobs()
            pending_jobs = [job for job in all_jobs if job.get('status') == 'scraped']

            if pending_jobs:
                console.print(f"[cyan]📥 Found {len(pending_jobs)} pending jobs in database[/cyan]")

                # Filter jobs by language
                processable_jobs, filtered_jobs = self.language_detector.filter_jobs_by_language(pending_jobs)

                # Convert to JobTask format and add to queue
                for job in processable_jobs:
                    task = JobTask(
                        job_url=job.get('url', ''),
                        job_id=str(job.get('id', '')),
                        title=job.get('title', 'Unknown'),
                        company=job.get('company', 'Unknown'),
                        location=job.get('location', 'Unknown'),
                        search_keyword=job.get('found_by_keyword', 'unknown')
                    )
                    self.task_queue.put(task)

                # Log and count filtered jobs
                if filtered_jobs:
                    self.stats["skipped_language"] += len(filtered_jobs)
                    for job in filtered_jobs:
                        reason = job.get('language_detection', {}).get('reason', 'Unknown reason')
                        console.print(f"[yellow]⏭️ Skipped job {job.get('url', '')} due to language filter: {reason}[/yellow]")

                console.print(f"[green]✅ Added {len(processable_jobs)} jobs to processing queue, skipped {len(filtered_jobs)} due to language filter[/green]")
            else:
                console.print("[yellow]📭 No pending jobs found in database[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ Error loading pending jobs: {e}[/red]")

    def stop(self):
        """Stop the job processor queue."""
        console.print("[yellow]🛑 Stopping job processor queue...[/yellow]")
        self.is_running = False

        # Wait for workers to finish
        for thread in self.worker_threads:
            thread.join(timeout=5)

        self.result_thread.join(timeout=5)

        console.print("[green]✅ Job processor queue stopped[/green]")

    def add_job(self, job_task: JobTask):
        """Add a job task to the processing queue."""
        self.task_queue.put(job_task)
        console.print(f"[cyan]📥 Added job to queue: {job_task.job_url}[/cyan]")

    def add_jobs_from_scraping(self, scraped_jobs: List[Dict[str, Any]]):
        """Add multiple jobs from scraping results."""
        for job_data in scraped_jobs:
            job_task = JobTask(
                job_url=job_data.get("url", ""),
                job_id=job_data.get("job_id", ""),
                title=job_data.get("title", ""),
                company=job_data.get("company", ""),
                location=job_data.get("location", ""),
                search_keyword=job_data.get("search_keyword", ""),
            )
            self.add_job(job_task)

    def _worker_loop(self, worker: JobProcessor):
        """Worker loop for processing jobs - SEQUENTIAL PROCESSING ONLY."""
        while self.is_running:
            try:
                # Get job from queue with timeout
                job_task = self.task_queue.get(timeout=1)

                # Process job SEQUENTIALLY (one at a time)
                console.print(f"[cyan]🔄 Sequential processing: {job_task.job_url[:60]}...[/cyan]")
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(worker.process_job(job_task))
                loop.close()

                # Put result in result queue
                self.result_queue.put(result)

                # Mark task as done
                self.task_queue.task_done()
                
                # Add delay between jobs to avoid overwhelming the server
                time.sleep(2)

            except Empty:
                continue
            except Exception as e:
                console.print(f"[red]❌ Worker error: {e}[/red]")

    def _result_processor_loop(self):
        """Process results and update statistics."""
        while self.is_running:
            try:
                # Get result from queue with timeout
                result = self.result_queue.get(timeout=1)

                # Update statistics
                self.stats["total_processed"] += 1
                if result.success:
                    self.stats["successful"] += 1
                else:
                    self.stats["failed"] += 1

                if result.cached:
                    self.stats["cached"] += 1

                self.stats["last_update"] = datetime.now().isoformat()

                # Periodic dashboard update
                current_time = time.time()
                if current_time - self.last_dashboard_update >= self.dashboard_update_interval:
                    self._update_dashboard()
                    self.last_dashboard_update = current_time

                # Mark result as done
                self.result_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                console.print(f"[red]❌ Result processor error: {e}[/red]")

    def _update_dashboard(self):
        """Update dashboard with current statistics."""
        if self.dashboard_callback:
            try:
                dashboard_data = {
                    "type": "job_processing_stats",
                    "profile": self.profile_name,
                    "stats": self.stats,
                    "queue_size": self.task_queue.qsize(),
                    "timestamp": datetime.now().isoformat(),
                }
                self.dashboard_callback(dashboard_data)
            except Exception as e:
                console.print(f"[yellow]⚠️ Dashboard update error: {e}[/yellow]")

    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return {
            **self.stats,
            "queue_size": self.task_queue.qsize(),
            "workers_active": len([w for w in self.workers if w.is_running]),
            "uptime": time.time()
            - (
                datetime.fromisoformat(self.stats["start_time"]).timestamp()
                if self.stats["start_time"]
                else 0
            ),
        }

    def wait_for_completion(self, timeout: Optional[float] = None):
        """Wait for all jobs in queue to be processed."""
        self.task_queue.join()
        self.result_queue.join()


def create_job_processor_queue(
    profile_name: str, num_workers: int = 2, dashboard_callback: Optional[Callable] = None
) -> JobProcessorQueue:
    """
    Factory function to create a job processor queue.

    Args:
        profile_name: Name of the user profile
        num_workers: Number of worker threads
        dashboard_callback: Callback function for dashboard updates

    Returns:
        JobProcessorQueue instance
    """
    return JobProcessorQueue(profile_name, num_workers, dashboard_callback)


if __name__ == "__main__":
    # Test the job processor queue
    def dashboard_callback(data):
        console.print(f"[cyan]Dashboard Update: {data}[/cyan]")

    queue = create_job_processor_queue("test", num_workers=2, dashboard_callback=dashboard_callback)
    queue.start()

    # Add test jobs
    test_jobs = [
        JobTask(
            job_url="https://example.com/job1",
            job_id="test1",
            title="Test Job 1",
            company="Test Company",
            location="Test Location",
            search_keyword="test",
        ),
        JobTask(
            job_url="https://example.com/job2",
            job_id="test2",
            title="Test Job 2",
            company="Test Company 2",
            location="Test Location 2",
            search_keyword="test",
        ),
    ]

    for job in test_jobs:
        queue.add_job(job)

    # Wait for completion
    queue.wait_for_completion()

    # Show final stats
    stats = queue.get_stats()
    console.print(f"[cyan]Final Stats: {stats}[/cyan]")

    queue.stop()
