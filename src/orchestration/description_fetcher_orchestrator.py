#!/usr/bin/env python3
"""
Description Fetcher Orchestrator - 10-Worker System
Pulls scraped jobs from database and fetches descriptions with maximum concurrency.

Features:
- 10 concurrent workers with connection pooling
- Rate limiting and anti-bot detection
- Automatic retry with exponential backoff
- Real-time progress tracking
- Memory-efficient job batching
- Integration with high-performance job processing queue
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from ..core.job_database import get_job_db
from ..scrapers.external_job_scraper import ExternalJobDescriptionScraper
from ..pipeline.optimized_job_queue import OptimizedJobQueue
from ..utils.profile_helpers import load_profile
from .optimized_connection_pool import OptimizedConnectionPool, ConnectionConfig, RateLimitConfig
from .optimized_job_batcher import OptimizedJobBatcher, BatchConfig

console = Console()
logger = logging.getLogger(__name__)


@dataclass
class OrchestratorMetrics:
    """Metrics for the description fetcher orchestrator."""
    total_jobs_processed: int = 0
    total_descriptions_fetched: int = 0
    total_failures: int = 0
    total_retries: int = 0
    avg_fetch_time: float = 0.0
    workers_active: int = 0
    queue_depth: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    success_rate: float = 0.0


class DescriptionFetcherOrchestrator:
    """
    Description fetcher orchestrator with 10 concurrent workers.
    
    Features:
    - 10 concurrent workers for maximum throughput
    - Connection pooling and rate limiting
    - Automatic retry with exponential backoff
    - Real-time progress tracking
    - Memory-efficient job batching
    - Integration with high-performance job processing queue
    """
    
    def __init__(self, profile_name: str, num_workers: int = 10, 
                 batch_size: int = 20, rate_limit: int = 100):
        self.profile_name = profile_name
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.rate_limit = rate_limit
        
        # Initialize components
        self.db = get_job_db(profile_name)
        self.profile = load_profile(profile_name) or {}
        self.processing_queue = OptimizedJobQueue("job_processing")
        
        # Initialize optimized components for Phase 2
        self.connection_pool = OptimizedConnectionPool(
            config=ConnectionConfig(
                pool_size=num_workers,
                max_connections=num_workers * 5,
                retry_attempts=3
            ),
            rate_limit_config=RateLimitConfig(
                requests_per_second=rate_limit,
                burst_limit=rate_limit // 2
            )
        )
        
        self.job_batcher = OptimizedJobBatcher(
            config=BatchConfig(
                initial_batch_size=batch_size,
                min_batch_size=5,
                max_batch_size=100,
                memory_threshold_mb=1024.0,
                enable_auto_optimization=True
            )
        )
        
        # Initialize external scraper for each worker
        self.scrapers = []
        for i in range(num_workers):
            scraper = ExternalJobDescriptionScraper(num_workers=1)  # Each worker gets its own scraper
            self.scrapers.append(scraper)
        
        # Metrics tracking
        self.metrics = OrchestratorMetrics()
        self.metrics.start_time = datetime.now()
        
        # Worker management
        self.worker_tasks = []
        self.is_running = False
        
        # Progress tracking
        self.progress = None
        self.progress_task = None
        
        logger.info(f"DescriptionFetcherOrchestrator initialized: {num_workers} workers, batch_size={batch_size}")
    
    async def start(self):
        """Start the orchestrator and all workers."""
        if self.is_running:
            logger.warning("Orchestrator is already running")
            return
            
        # Start optimized components
        await self.connection_pool.start()
        await self.job_batcher.start()
        
        console.print(f"[bold blue]🚀 Starting Description Fetcher Orchestrator with {self.num_workers} workers[/bold blue]")
        
        # Start the processing queue
        await self.processing_queue.start()
        
        # Start progress tracking
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        )
        self.progress.start()
        
        # Start workers
        self.is_running = True
        self.worker_tasks = [
            asyncio.create_task(self._worker_loop(worker_id))
            for worker_id in range(self.num_workers)
        ]
        
        # Start metrics update task
        self.metrics_task = asyncio.create_task(self._update_metrics())
        
        logger.info(f"Started {self.num_workers} description fetcher workers")
    
    async def stop(self):
        """Stop the orchestrator and all workers."""
        if not self.is_running:
            return
        
        console.print("[yellow]🛑 Stopping Description Fetcher Orchestrator...[/yellow]")
        
        # Stop optimized components
        await self.connection_pool.stop()
        await self.job_batcher.stop()
        
        # Stop workers
        self.is_running = False
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Stop metrics task
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
        
        # Stop progress tracking
        if self.progress:
            self.progress.stop()
        
        # Stop processing queue
        await self.processing_queue.stop()
        
        # Update final metrics
        self.metrics.end_time = datetime.now()
        if self.metrics.total_jobs_processed > 0:
            self.metrics.success_rate = (self.metrics.total_descriptions_fetched / self.metrics.total_jobs_processed) * 100
        
        logger.info("Description Fetcher Orchestrator stopped")
    
    async def process_scraped_jobs(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Process scraped jobs and fetch descriptions.
        
        Args:
            limit: Maximum number of jobs to process (None for all)
            
        Returns:
            Processing statistics
        """
        try:
            # Get scraped jobs from database
            scraped_jobs = self._get_scraped_jobs(limit)
            if not scraped_jobs:
                console.print("[yellow]⚠️ No scraped jobs found in database[/yellow]")
                return asdict(self.metrics)
            
            console.print(f"[cyan]📋 Found {len(scraped_jobs)} scraped jobs to process[/cyan]")
            
            # Start orchestrator
            await self.start()
            
            # Create progress task
            progress_task = self.progress.add_task(
                f"[cyan]Fetching descriptions with {self.num_workers} workers...",
                total=len(scraped_jobs)
            )
            
            # Distribute jobs to workers
            await self._distribute_jobs_to_workers(scraped_jobs, progress_task)
            
            # Wait for all workers to complete
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            
            # Stop orchestrator
            await self.stop()
            
            # Display results
            self._display_results()
            
            return asdict(self.metrics)
            
        except Exception as e:
            logger.error(f"Error in process_scraped_jobs: {e}")
            await self.stop()
            raise
    
    def _get_scraped_jobs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get scraped jobs from database."""
        try:
            # Get jobs with status 'scraped' that don't have descriptions
            jobs = self.db.get_jobs_by_status('scraped', limit=limit)
            
            # Filter jobs that don't have descriptions
            jobs_without_descriptions = [
                job for job in jobs 
                if not job.get('description') or len(job.get('description', '').strip()) < 50
            ]
            
            return jobs_without_descriptions
            
        except Exception as e:
            logger.error(f"Error getting scraped jobs: {e}")
            return []
    
    async def _distribute_jobs_to_workers(self, jobs: List[Dict[str, Any]], progress_task):
        """Distribute jobs to workers in batches."""
        # Create a shared job queue for workers
        job_queue = asyncio.Queue()
        
        # Add jobs to queue
        for job in jobs:
            await job_queue.put(job)
        
        # Update worker tasks to use the shared queue
        self.worker_tasks = [
            asyncio.create_task(self._worker_loop_with_queue(worker_id, job_queue, progress_task))
            for worker_id in range(self.num_workers)
        ]
    
    async def _worker_loop(self, worker_id: int):
        """Individual worker loop for fetching descriptions."""
        logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get job from database (this would be replaced with queue-based approach)
                job = await self._get_next_job_for_worker(worker_id)
                if not job:
                    await asyncio.sleep(1)
                    continue
                
                # Process job
                await self._process_job(worker_id, job)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _worker_loop_with_queue(self, worker_id: int, job_queue: asyncio.Queue, progress_task):
        """Worker loop using shared job queue."""
        logger.info(f"Worker {worker_id} started with queue")
        
        while self.is_running:
            try:
                # Get job from queue
                try:
                    job = await asyncio.wait_for(job_queue.get(), timeout=5)
                except asyncio.TimeoutError:
                    continue
                
                # Process job
                success = await self._process_job(worker_id, job)
                
                # Update progress
                if self.progress:
                    self.progress.advance(progress_task)
                
                # Mark job as done
                job_queue.task_done()
                
                # Rate limiting
                await self.rate_limiter.wait()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _get_next_job_for_worker(self, worker_id: int) -> Optional[Dict[str, Any]]:
        """Get next job for worker from database."""
        try:
            # This would implement job distribution logic
            # For now, return None to indicate no jobs
            return None
        except Exception as e:
            logger.error(f"Error getting job for worker {worker_id}: {e}")
            return None
    
    async def _process_job(self, worker_id: int, job: Dict[str, Any]) -> bool:
        """
        Process a single job and fetch its description.
        
        Args:
            worker_id: Worker identifier
            job: Job data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        job_id = job.get('id', 'unknown')
        
        try:
            logger.debug(f"Worker {worker_id} processing job {job_id}")
            
            # Get the scraper for this worker
            scraper = self.scrapers[worker_id]
            
            # Fetch description with retry logic
            description = await self._fetch_job_description_with_retry(scraper, job)
            
            if description:
                # Update job with description
                job['description'] = description
                job['status'] = 'description_saved'
                job['description_fetched_at'] = datetime.now().isoformat()
                job['description_worker_id'] = worker_id
                
                # Save to database
                success = self.db.update_job(job_id, job)
                if success:
                    # Enqueue to processing queue
                    await self.processing_queue.enqueue_job(job)
                    
                    # Update metrics
                    self.metrics.total_descriptions_fetched += 1
                    self.metrics.total_jobs_processed += 1
                    
                    # Track performance
                    fetch_time = time.time() - start_time
                    self._update_avg_fetch_time(fetch_time)
                    
                    logger.debug(f"Worker {worker_id} successfully processed job {job_id}")
                    return True
                else:
                    logger.error(f"Worker {worker_id} failed to save job {job_id} to database")
                    self.metrics.total_failures += 1
                    return False
            else:
                logger.warning(f"Worker {worker_id} failed to fetch description for job {job_id}")
                self.metrics.total_failures += 1
                return False
                
        except Exception as e:
            logger.error(f"Worker {worker_id} error processing job {job_id}: {e}")
            self.metrics.total_failures += 1
            return False
    
    async def _fetch_job_description_with_retry(self, scraper: ExternalJobDescriptionScraper, 
                                              job: Dict[str, Any], max_retries: int = 3) -> Optional[str]:
        """
        Fetch job description with retry logic.
        
        Args:
            scraper: External job scraper instance
            job: Job data dictionary
            max_retries: Maximum number of retry attempts
            
        Returns:
            Job description or None if failed
        """
        job_url = job.get('url')
        if not job_url:
            return None
        
        for attempt in range(max_retries):
            try:
                # Fetch description
                description = await scraper.fetch_job_description(job_url)
                
                if description and len(description.strip()) > 50:
                    return description.strip()
                else:
                    logger.warning(f"Empty or too short description for job {job.get('id')}")
                    return None
                    
            except Exception as e:
                self.metrics.total_retries += 1
                logger.warning(f"Attempt {attempt + 1} failed for job {job.get('id')}: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All retry attempts failed for job {job.get('id')}")
                    return None
        
        return None
    
    def _update_avg_fetch_time(self, fetch_time: float):
        """Update average fetch time metric."""
        # Simple moving average
        if self.metrics.avg_fetch_time == 0:
            self.metrics.avg_fetch_time = fetch_time
        else:
            self.metrics.avg_fetch_time = (self.metrics.avg_fetch_time + fetch_time) / 2
    
    async def _update_metrics(self):
        """Background task to update metrics."""
        while self.is_running:
            try:
                # Update worker count
                active_workers = sum(1 for task in self.worker_tasks if not task.done())
                self.metrics.workers_active = active_workers
                
                # Update queue depth
                queue_stats = await self.processing_queue.get_queue_stats()
                self.metrics.queue_depth = queue_stats.get('total_queue_size', 0)
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
                await asyncio.sleep(5)
    
    def _display_results(self):
        """Display processing results."""
        duration = (self.metrics.end_time - self.metrics.start_time).total_seconds()
        
        table = Table(title="Description Fetcher Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Jobs Processed", str(self.metrics.total_jobs_processed))
        table.add_row("Descriptions Fetched", str(self.metrics.total_descriptions_fetched))
        table.add_row("Failures", str(self.metrics.total_failures))
        table.add_row("Retries", str(self.metrics.total_retries))
        table.add_row("Success Rate", f"{self.metrics.success_rate:.1f}%")
        table.add_row("Average Fetch Time", f"{self.metrics.avg_fetch_time:.2f}s")
        table.add_row("Total Duration", f"{duration:.1f}s")
        table.add_row("Jobs per Second", f"{self.metrics.total_jobs_processed / max(duration, 1):.1f}")
        
        console.print(table)
    
    async def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "orchestrator_name": "DescriptionFetcherOrchestrator",
            "profile_name": self.profile_name,
            "num_workers": self.num_workers,
            "is_running": self.is_running,
            "metrics": asdict(self.metrics),
            "queue_stats": await self.processing_queue.get_queue_stats(),
            "connection_pool_metrics": self.connection_pool.get_metrics(),
            "job_batcher_metrics": self.job_batcher.get_metrics(),
            "connection_pool_health": self.connection_pool.get_health_status(),
            "job_batcher_health": self.job_batcher.get_health_status()
        }


class RateLimiter:
    """Simple rate limiter for controlling request frequency."""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def wait(self):
        """Wait if rate limit is exceeded."""
        now = time.time()
        
        # Remove old requests
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        # Check if we're at the limit
        if len(self.requests) >= self.max_requests:
            # Wait until we can make another request
            wait_time = self.time_window - (now - self.requests[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # Add current request
        self.requests.append(now)


# Convenience functions
async def create_description_fetcher_orchestrator(profile_name: str, num_workers: int = 10) -> DescriptionFetcherOrchestrator:
    """Create a description fetcher orchestrator."""
    return DescriptionFetcherOrchestrator(profile_name, num_workers)


async def process_scraped_jobs_with_orchestrator(profile_name: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """Process scraped jobs using the description fetcher orchestrator."""
    orchestrator = DescriptionFetcherOrchestrator(profile_name)
    return await orchestrator.process_scraped_jobs(limit) 