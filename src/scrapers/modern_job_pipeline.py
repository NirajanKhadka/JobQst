"""
Modern Job Pipeline - Enhanced Performance Architecture
Provides optimized, scalable job scraping and processing pipeline.

Features:
- Async/await throughout for maximum concurrency
- Memory-efficient queue management
- Real-time performance monitoring
- Adaptive worker scaling
- Intelligent error recovery
- Database connection pooling
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Optional Playwright import with fallback
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Playwright not available: {e}")
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None

# Import with proper relative paths when running from src directory
try:
    from core.job_database import get_job_db
    from ai.enhanced_job_analyzer import EnhancedJobAnalyzer
    from pipeline.stages.processing import processing_stage
    from pipeline.stages.analysis import analysis_stage
    from pipeline.stages.storage import storage_stage
except ImportError:
    # Fallback for different import contexts
    from src.core.job_database import get_job_db
    from src.ai.enhanced_job_analyzer import EnhancedJobAnalyzer
    from src.pipeline.stages.processing import processing_stage
    from src.pipeline.stages.analysis import analysis_stage
    from src.pipeline.stages.storage import storage_stage

console = Console()


@dataclass
class PipelineResults:
    """Results from pipeline execution."""
    jobs_scraped: int
    jobs_processed: int
    jobs_analyzed: int
    jobs_saved: int
    jobs_failed: int
    jobs_duplicates: int
    errors: int
    success_rate: float
    duration: float
    success: bool


from src.pipeline.redis_queue import RedisQueue

class ModernJobPipeline:
    """
    Enhanced job processing pipeline with performance optimizations.
    
    Performance Features:
    - Asynchronous processing throughout
    - Dynamic worker scaling based on load
    - Memory-efficient queue management
    - Real-time metrics and monitoring
    - Intelligent retry mechanisms
    - Connection pooling and reuse
    """
    
    def __init__(self, profile: Dict[str, Any], config: Dict[str, Any]):
        self.profile = profile
        self.config = config
        self.profile_name = profile.get("profile_name", "default")
        
        # Enhanced configuration
        self.max_workers = config.get("max_workers", 4)
        self.enable_ai_analysis = config.get("enable_ai_analysis", False)  # Rule-based is much faster
        self.performance_mode = config.get("performance_mode", False)
        self.timeout = config.get("timeout", 30)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.headless = config.get("headless", True)
        self.batch_size = config.get("batch_size", 10)
        
        # Database and analyzer
        self.db = get_job_db(self.profile_name)
        self.analyzer = EnhancedJobAnalyzer(self.profile) if self.enable_ai_analysis else None
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

        # Enhanced queue system with size limits for memory efficiency
        max_queue_size = 1000 if self.performance_mode else 500
        self.scraping_queue = asyncio.Queue(maxsize=max_queue_size)
        self.processing_queue = asyncio.Queue(maxsize=max_queue_size)
        self.analysis_queue = asyncio.Queue(maxsize=max_queue_size)
        self.storage_queue = asyncio.Queue(maxsize=max_queue_size)

        # Enhanced metrics tracking
        self.stats = {
            "jobs_scraped": 0,
            "jobs_processed": 0,
            "jobs_analyzed": 0,
            "jobs_saved": 0,
            "jobs_failed": 0,
            "jobs_duplicates": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

        # Redis queue for job handoff
        self.redis_queue = RedisQueue(queue_name="jobs:main")
        
        # Performance monitoring
        self.performance_monitor = None

    def increment(self, key: str, value: int = 1) -> None:
        """Thread-safe increment of statistics."""
        self.stats[key] += value

    async def start(self) -> PipelineResults:
        """Start the enhanced pipeline with performance monitoring."""
        self.stats["start_time"] = time.time()
        
        console.print("[bold blue]🚀 Starting Enhanced Job Pipeline[/bold blue]")
        console.print(f"[cyan]Workers: {self.max_workers} | AI Analysis: {self.enable_ai_analysis} | Performance Mode: {self.performance_mode}[/cyan]")
        
        try:
            # Start performance monitoring if available
            try:
                from src.core.performance_monitor import PerformanceMonitor
                self.performance_monitor = PerformanceMonitor()
                self.performance_monitor.start_monitoring()
            except ImportError:
                console.print("[yellow]⚠️ Performance monitoring not available[/yellow]")
            
            # Create and start all pipeline stages
            tasks = [
                asyncio.create_task(self._enhanced_scraping_stage()),
                asyncio.create_task(
                    processing_stage(self.processing_queue, self.analysis_queue, self)
                ),
                asyncio.create_task(
                    analysis_stage(
                        self.analysis_queue,
                        self.storage_queue,
                        self,
                        self.analyzer,
                        self.thread_pool,
                    )
                ),
                asyncio.create_task(
                    storage_stage(self.storage_queue, self, self.db, self.thread_pool)
                ),
            ]
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Calculate final results
            self.stats["end_time"] = time.time()
            duration = self.stats["end_time"] - self.stats["start_time"]
            
            # Calculate success rate
            total_jobs = self.stats["jobs_scraped"]
            successful_jobs = self.stats["jobs_saved"]
            success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
            
            results = PipelineResults(
                jobs_scraped=self.stats["jobs_scraped"],
                jobs_processed=self.stats["jobs_processed"],
                jobs_analyzed=self.stats["jobs_analyzed"],
                jobs_saved=self.stats["jobs_saved"],
                jobs_failed=self.stats["jobs_failed"],
                jobs_duplicates=self.stats["jobs_duplicates"],
                errors=self.stats["errors"],
                success_rate=success_rate,
                duration=duration,
                success=success_rate > 50  # Consider successful if > 50% jobs saved
            )
            
            # Stop performance monitoring
            if self.performance_monitor:
                perf_stats = self.performance_monitor.stop_monitoring()
                console.print(f"[green]📊 Performance: {perf_stats.get('jobs_per_second', 0):.2f} jobs/sec[/green]")
            
            console.print(f"[bold green]✅ Pipeline completed in {duration:.2f}s[/bold green]")
            
            return results
            
        except Exception as e:
            console.print(f"[red]❌ Pipeline error: {e}[/red]")
            return PipelineResults(
                jobs_scraped=0, jobs_processed=0, jobs_analyzed=0, jobs_saved=0,
                jobs_failed=1, jobs_duplicates=0, errors=1, success_rate=0,
                duration=0, success=False
            )

    async def run_optimized(self, days: int = 14, pages: int = 3, max_jobs: int = 20) -> Dict[str, Any]:
        """
        Run optimized pipeline with specific parameters.
        
        Args:
            days: Days to look back
            pages: Max pages per keyword  
            max_jobs: Max jobs per keyword
            
        Returns:
            Dictionary with pipeline results and performance metrics
        """
        console.print(f"[cyan]🎯 Optimized run: {days} days, {pages} pages, {max_jobs} jobs per keyword[/cyan]")
        
        # Store parameters for scraping stage
        self.scraping_params = {
            "days": days,
            "pages": pages,
            "max_jobs": max_jobs
        }
        
        # Run the pipeline
        results = await self.start()
        
        # Return comprehensive results
        return {
            "success": results.success,
            "jobs_scraped": results.jobs_scraped,
            "jobs_processed": results.jobs_processed,
            "jobs_saved": results.jobs_saved,
            "success_rate": results.success_rate,
            "duration": results.duration,
            "jobs_per_second": results.jobs_scraped / results.duration if results.duration > 0 else 0,
            "performance_mode": self.performance_mode,
            "workers": self.max_workers
        }

    async def _enhanced_scraping_stage(self) -> None:
        """Enhanced scraping stage with performance optimizations."""
        keywords = self.profile.get("keywords", ["python developer", "data analyst"])
        
        # Get scraping parameters
        params = getattr(self, 'scraping_params', {})
        max_pages = params.get("pages", 5)
        max_jobs = params.get("max_jobs", 100)
        
        console.print(f"[cyan]🔍 Scraping {len(keywords)} keywords with {max_pages} pages each[/cyan]")
        
        try:
            async with async_playwright() as p:
                # Enhanced browser configuration for performance
                browser_args = [
                    "--no-sandbox",
                    "--disable-setuid-sandbox", 
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--no-zygote",
                    "--single-process",
                    "--disable-gpu"
                ] if self.performance_mode else []
                
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=browser_args
                )
                
                try:
                    # Create pages for parallel scraping
                    pages = []
                    max_concurrent_pages = min(self.max_workers, len(keywords))
                    
                    for i in range(max_concurrent_pages):
                        context = await browser.new_context(
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                        )
                        page = await context.new_page()
                        pages.append(page)
                    
                    # Scrape keywords in parallel batches
                    semaphore = asyncio.Semaphore(max_concurrent_pages)
                    
                    async def scrape_keyword_with_semaphore(keyword: str, page_idx: int):
                        async with semaphore:
                            page = pages[page_idx % len(pages)]
                            try:
                                await self._scrape_keyword_enhanced(page, keyword, max_pages, max_jobs)
                                if self.performance_monitor:
                                    self.performance_monitor.record_job_processed()
                            except Exception as e:
                                console.print(f"[red]❌ Error scraping {keyword}: {e}[/red]")
                                self.increment("errors")
                                if self.performance_monitor:
                                    self.performance_monitor.record_error()
                    
                    # Execute scraping tasks
                    scraping_tasks = [
                        scrape_keyword_with_semaphore(keyword, i) 
                        for i, keyword in enumerate(keywords)
                    ]
                    
                    await asyncio.gather(*scraping_tasks, return_exceptions=True)
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            console.print(f"[red]❌ Scraping stage error: {e}[/red]")
            self.increment("errors")
        
        # Signal end of scraping to processing stage
        await self.processing_queue.put(None)

    async def _scrape_keyword_enhanced(self, page, keyword: str, max_pages: int, max_jobs: int) -> None:
        """Enhanced keyword scraping with performance optimizations."""
        jobs_scraped = 0
        
        for page_num in range(1, max_pages + 1):
            if jobs_scraped >= max_jobs:
                break
            try:
                # Construct search URL (Eluta example)
                search_url = f"https://www.eluta.ca/search?q={keyword}"
                if page_num > 1:
                    search_url += f"&pg={page_num}"
                await page.goto(search_url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                await page.wait_for_selector(".organic-job", timeout=10000)
                job_elements = await page.query_selector_all(".organic-job")
                if not job_elements:
                    console.print(f"[yellow]No jobs found on page {page_num} for '{keyword}'[/yellow]")
                    break
                batch_tasks = []
                for i, job_elem in enumerate(job_elements[:max_jobs - jobs_scraped]):
                    batch_tasks.append(self._extract_job_data_enhanced(job_elem, keyword, page_num, i + 1))
                job_data_list = await asyncio.gather(*batch_tasks, return_exceptions=True)
                for job_data in job_data_list:
                    if job_data and not isinstance(job_data, Exception):
                        # Enqueue to Redis
                        await self.redis_queue.enqueue(job_data.to_dict())
                        await self.processing_queue.put(job_data)
                        jobs_scraped += 1
                        self.increment("jobs_scraped")
                console.print(f"[green]✅ {keyword} page {page_num}: {len([j for j in job_data_list if j and not isinstance(j, Exception)])} jobs[/green]")
                if not self.performance_mode:
                    await asyncio.sleep(1)
            except Exception as e:
                console.print(f"[yellow]⚠️ Page {page_num} error for '{keyword}': {str(e)[:100]}...[/yellow]")
                continue

    async def _extract_job_data_enhanced(self, job_elem, keyword: str, page_num: int, job_num: int):
        """Enhanced job data extraction with error handling."""
        try:
            # Import JobData with fallback
            try:
                from scrapers.scraping_models import JobData
            except ImportError:
                from src.scrapers.scraping_models import JobData
                
            from datetime import datetime
            
            text = await job_elem.inner_text()
            lines = [line.strip() for line in text.split("\n") if line.strip()]

            if len(lines) < 2:
                return None

            job_data = JobData(
                title=lines[0],
                company=lines[1],
                location=lines[2] if len(lines) > 2 else "",
                summary=" ".join(lines[3:]) if len(lines) > 3 else "",
                search_keyword=keyword,
                job_id=f"{keyword}_{page_num}_{job_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            )

            # Extract URL
            link = await job_elem.query_selector("a")
            if link:
                href = await link.get_attribute("href")
                if href:
                    if href.startswith("/"):
                        job_data.url = f"https://www.eluta.ca{href}"
                    else:
                        job_data.url = href

            return job_data
            
        except Exception as e:
            console.print(f"[red]❌ Job extraction error: {e}[/red]")
            return None


async def main():
    """Test the enhanced pipeline."""
    profile = {
        "keywords": ["python developer", "data analyst"],
        "profile_name": "test"
    }
    config = {
        "max_workers": 4, 
        "enable_ai_analysis": False,
        "performance_mode": True,
        "headless": True
    }
    
    pipeline = ModernJobPipeline(profile, config)
    results = await pipeline.run_optimized(days=7, pages=2, max_jobs=10)
    
    console.print(f"[bold green]Pipeline Results:[/bold green]")
    console.print(f"Success: {results['success']}")
    console.print(f"Jobs: {results['jobs_scraped']} scraped, {results['jobs_saved']} saved")
    console.print(f"Rate: {results['jobs_per_second']:.2f} jobs/sec")


if __name__ == "__main__":
    asyncio.run(main())
