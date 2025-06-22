#!/usr/bin/env python3
"""
Modern Job Pipeline - Big Data inspired architecture with modern Python patterns.
Consolidates the best methods into a single, high-performance system.
"""

import asyncio
import json
import time
import threading
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import wraps
import weakref

# Modern Python imports
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.layout import Layout
from rich.text import Text
from pydantic import BaseModel, Field, validator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.async_api import async_playwright, Page
from src.core.job_database import get_job_db
from src.utils.job_analyzer import JobAnalyzer

console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """Job processing status enum."""
    PENDING = "pending"
    SCRAPING = "scraping"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    SAVED = "saved"
    FAILED = "failed"
    DUPLICATE = "duplicate"

class PipelineStage(Enum):
    """Pipeline processing stages."""
    SCRAPER = "scraper"
    PROCESSOR = "processor"
    ANALYZER = "analyzer"
    STORAGE = "storage"

@dataclass
class JobData:
    """Modern job data structure using dataclass."""
    title: str
    company: str
    location: str = ""
    summary: str = ""
    url: str = ""
    search_keyword: str = ""
    site: str = "eluta"
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
    job_id: str = ""
    status: JobStatus = JobStatus.PENDING
    raw_data: Dict = field(default_factory=dict)
    analysis_data: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "summary": self.summary,
            "url": self.url,
            "search_keyword": self.search_keyword,
            "site": self.site,
            "scraped_at": self.scraped_at,
            "job_id": self.job_id,
            "status": self.status.value,
            "raw_data": self.raw_data,
            "analysis_data": self.analysis_data,
            "metadata": self.metadata
        }

class JobPipelineConfig(BaseModel):
    """Configuration using Pydantic for validation."""
    batch_size: int = Field(default=50, ge=1, le=1000)
    max_workers: int = Field(default=4, ge=1, le=16)
    buffer_size: int = Field(default=1000, ge=100, le=10000)
    timeout_seconds: int = Field(default=30, ge=10, le=300)
    enable_ai_analysis: bool = True
    enable_duplicate_detection: bool = True
    enable_streaming: bool = True
    ddr5_optimized: bool = True
    
    @validator('max_workers')
    def validate_workers(cls, v):
        """Ensure workers don't exceed CPU cores."""
        cpu_count = mp.cpu_count()
        if v > cpu_count:
            console.print(f"[yellow]⚠️ Reducing workers from {v} to {cpu_count} (CPU cores)[/yellow]")
            return cpu_count
        return v

class PipelineMetrics:
    """Real-time pipeline metrics tracking."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            'jobs_scraped': 0,
            'jobs_processed': 0,
            'jobs_analyzed': 0,
            'jobs_saved': 0,
            'jobs_failed': 0,
            'jobs_duplicates': 0,
            'batches_processed': 0,
            'errors': 0
        }
        self.stage_times = {}
        self._lock = threading.Lock()
    
    def increment(self, stat: str, value: int = 1):
        """Thread-safe increment."""
        with self._lock:
            self.stats[stat] += value
    
    def get_performance_stats(self) -> Dict:
        """Get current performance statistics."""
        with self._lock:
            duration = datetime.now() - self.start_time
            total_jobs = self.stats['jobs_scraped']
            
            return {
                'duration': duration,
                'total_jobs': total_jobs,
                'jobs_per_minute': (total_jobs / duration.total_seconds()) * 60 if duration.total_seconds() > 0 else 0,
                'success_rate': (self.stats['jobs_saved'] / total_jobs * 100) if total_jobs > 0 else 0,
                'stats': self.stats.copy()
            }

class ModernJobPipeline:
    """
    Modern job pipeline using big data patterns and modern Python features.
    Consolidates the best methods into a single, high-performance system.
    """
    
    def __init__(self, profile: Dict, config: JobPipelineConfig = None):
        self.profile = profile
        self.config = config or JobPipelineConfig()
        self.metrics = PipelineMetrics()
        
        # Modern async queues
        self.scraping_queue = asyncio.Queue(maxsize=self.config.buffer_size)
        self.processing_queue = asyncio.Queue(maxsize=self.config.buffer_size)
        self.analysis_queue = asyncio.Queue(maxsize=self.config.buffer_size)
        self.storage_queue = asyncio.Queue(maxsize=self.config.buffer_size)
        
        # Thread pools for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=min(2, self.config.max_workers))
        
        # Components
        self.db = get_job_db()
        self.analyzer = JobAnalyzer(use_ai=self.config.enable_ai_analysis) if self.config.enable_ai_analysis else None
        
        # Control flags
        self.running = False
        self.tasks = []
        
        # DDR5-6400 optimizations
        if self.config.ddr5_optimized:
            self._optimize_for_ddr5()
        
        console.print(Panel.fit("🚀 MODERN JOB PIPELINE", style="bold blue"))
        console.print(f"[cyan]⚡ DDR5-6400 Optimized: {self.config.ddr5_optimized}[/cyan]")
        console.print(f"[cyan]🔧 Workers: {self.config.max_workers}[/cyan]")
        console.print(f"[cyan]💾 Batch Size: {self.config.batch_size}[/cyan]")
        console.print(f"[cyan]🔄 Streaming: {self.config.enable_streaming}[/cyan]")
    
    def _optimize_for_ddr5(self):
        """Apply DDR5-6400 specific optimizations."""
        # Larger batch sizes for fast memory
        self.config.batch_size = min(100, self.config.batch_size * 2)
        # More workers for fast context switching
        self.config.max_workers = min(8, self.config.max_workers + 2)
        # Larger buffers for fast I/O
        self.config.buffer_size = min(5000, self.config.buffer_size * 2)
        
        console.print("[green]✅ DDR5-6400 optimizations applied[/green]")
    
    async def start(self):
        """Start the modern pipeline."""
        self.running = True
        self.metrics.start_time = datetime.now()
        
        console.print(f"\n[bold green]🚀 Starting Modern Job Pipeline[/bold green]")
        console.print(f"[cyan]⏰ Started at: {self.metrics.start_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
        
        # Start all pipeline stages
        self.tasks = [
            asyncio.create_task(self._scraping_stage()),
            asyncio.create_task(self._processing_stage()),
            asyncio.create_task(self._analysis_stage()),
            asyncio.create_task(self._storage_stage()),
            asyncio.create_task(self._monitoring_stage())
        ]
        
        # Start scraping
        await self._start_scraping()
        
        # Wait for completion
        await asyncio.gather(*self.tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the pipeline gracefully."""
        console.print(f"\n[yellow]🛑 Stopping Modern Job Pipeline...[/yellow]")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close thread pools
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        
        self._print_final_stats()
    
    async def _start_scraping(self):
        """Start the scraping process."""
        keywords = self.profile.get("keywords", [])
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-automation",
                    "--disable-extensions",
                    "--no-first-run",
                    "--disable-default-apps",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding"
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            # Scrape each keyword
            for keyword in keywords:
                if not self.running:
                    break
                
                console.print(f"\n[bold blue]🔍 Scraping keyword: {keyword}[/bold blue]")
                await self._scrape_keyword(page, keyword)
                
                # Small delay between keywords
                await asyncio.sleep(2)
            
            await browser.close()
    
    async def _scrape_keyword(self, page: Page, keyword: str):
        """Scrape a single keyword using modern async patterns."""
        jobs_processed = 0
        max_pages = 5
        max_jobs = 100
        
        for page_num in range(1, max_pages + 1):
            if jobs_processed >= max_jobs or not self.running:
                break
            
            console.print(f"[cyan]📄 Page {page_num}/{max_pages} for '{keyword}'[/cyan]")
            
            # Build search URL (no location for Canada-wide)
            search_url = f"https://www.eluta.ca/search?q={keyword}"
            if page_num > 1:
                search_url += f"&pg={page_num}"
            
            try:
                # Navigate to search page
                await page.goto(search_url, timeout=30000)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                
                # Find job elements
                job_elements = await page.query_selector_all(".organic-job")
                
                if not job_elements:
                    console.print(f"[yellow]⚠️ No jobs found on page {page_num}[/yellow]")
                    break
                
                console.print(f"[green]✅ Found {len(job_elements)} jobs on page {page_num}[/green]")
                
                # Extract and queue jobs
                for i, job_elem in enumerate(job_elements):
                    if jobs_processed >= max_jobs:
                        break
                    
                    job_data = await self._extract_job_data(job_elem, keyword, page_num, i+1)
                    if job_data:
                        await self.scraping_queue.put(job_data)
                        jobs_processed += 1
                        self.metrics.increment('jobs_scraped')
                
                await asyncio.sleep(1)
                
            except Exception as e:
                console.print(f"[red]❌ Page {page_num} error: {e}[/red]")
                continue
    
    async def _extract_job_data(self, job_elem, keyword: str, page_num: int, job_num: int) -> Optional[JobData]:
        """Extract job data using modern patterns."""
        try:
            # Get basic text content
            text = await job_elem.inner_text()
            text = text.strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                return None
            
            # Create job data object
            job_data = JobData(
                title=lines[0] if lines else "",
                company=lines[1] if len(lines) > 1 else "",
                location=lines[2] if len(lines) > 2 else "",
                summary=" ".join(lines[3:]) if len(lines) > 3 else "",
                search_keyword=keyword,
                job_id=f"{keyword}_{page_num}_{job_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                raw_data={"text": text, "lines": lines}
            )
            
            # Try to get job URL
            try:
                links = await job_elem.query_selector_all("a")
                for link in links:
                    href = await link.get_attribute("href")
                    if href and '/job/' in href and 'eluta.ca' in href:
                        job_data.url = href
                        break
            except:
                pass
            
            return job_data
            
        except Exception as e:
            console.print(f"[red]❌ Job extraction error: {e}[/red]")
            return None
    
    async def _scraping_stage(self):
        """Scraping stage - moves jobs to processing queue."""
        while self.running:
            try:
                job_data = await asyncio.wait_for(self.scraping_queue.get(), timeout=1.0)
                job_data.status = JobStatus.SCRAPING
                await self.processing_queue.put(job_data)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                console.print(f"[red]❌ Scraping stage error: {e}[/red]")
                self.metrics.increment('errors')
    
    async def _processing_stage(self):
        """Processing stage - validates and filters jobs."""
        while self.running:
            try:
                job_data = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                job_data.status = JobStatus.PROCESSING
                
                # Basic validation
                if not job_data.title or not job_data.company:
                    job_data.status = JobStatus.FAILED
                    self.metrics.increment('jobs_failed')
                    continue
                
                # Apply filters
                if not await self._is_suitable_job(job_data):
                    job_data.status = JobStatus.FAILED
                    self.metrics.increment('jobs_failed')
                    continue
                
                # Move to analysis queue
                await self.analysis_queue.put(job_data)
                self.metrics.increment('jobs_processed')
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                console.print(f"[red]❌ Processing stage error: {e}[/red]")
                self.metrics.increment('errors')
    
    async def _analysis_stage(self):
        """Analysis stage - AI analysis and enhancement."""
        while self.running:
            try:
                job_data = await asyncio.wait_for(self.analysis_queue.get(), timeout=1.0)
                job_data.status = JobStatus.ANALYZED
                
                if self.analyzer:
                    try:
                        # Run analysis in thread pool (CPU intensive)
                        loop = asyncio.get_event_loop()
                        analysis_result = await loop.run_in_executor(
                            self.thread_pool,
                            self.analyzer.analyze_job_deep,
                            job_data.to_dict(),
                            None
                        )
                        job_data.analysis_data = analysis_result
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Analysis error: {e}[/yellow]")
                
                # Move to storage queue
                await self.storage_queue.put(job_data)
                self.metrics.increment('jobs_analyzed')
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                console.print(f"[red]❌ Analysis stage error: {e}[/red]")
                self.metrics.increment('errors')
    
    async def _storage_stage(self):
        """Storage stage - saves jobs to database."""
        while self.running:
            try:
                job_data = await asyncio.wait_for(self.storage_queue.get(), timeout=1.0)
                job_data.status = JobStatus.SAVED
                
                try:
                    # Save to database
                    loop = asyncio.get_event_loop()
                    success = await loop.run_in_executor(
                        self.thread_pool,
                        self.db.add_job,
                        job_data.to_dict()
                    )
                    
                    if success:
                        self.metrics.increment('jobs_saved')
                    else:
                        self.metrics.increment('jobs_duplicates')
                        job_data.status = JobStatus.DUPLICATE
                        
                except Exception as e:
                    console.print(f"[yellow]⚠️ Database save error: {e}[/yellow]")
                    self.metrics.increment('jobs_failed')
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                console.print(f"[red]❌ Storage stage error: {e}[/red]")
                self.metrics.increment('errors')
    
    async def _monitoring_stage(self):
        """Real-time monitoring and statistics."""
        while self.running:
            try:
                stats = self.metrics.get_performance_stats()
                
                # Clear screen and show status
                console.clear()
                
                # Create status table
                table = Table(title="🚀 Modern Job Pipeline Status")
                table.add_column("Stage", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Jobs", style="yellow")
                table.add_column("Speed", style="blue")
                
                table.add_row(
                    "Scraping",
                    "🟢 Active" if self.running else "🔴 Stopped",
                    f"{stats['stats']['jobs_scraped']}",
                    f"{stats['jobs_per_minute']:.1f}/min"
                )
                
                table.add_row(
                    "Processing",
                    "🟢 Active",
                    f"{stats['stats']['jobs_processed']}",
                    "DDR5-6400"
                )
                
                table.add_row(
                    "Analysis",
                    "🟢 Active",
                    f"{stats['stats']['jobs_analyzed']}",
                    "AI Powered"
                )
                
                table.add_row(
                    "Storage",
                    "🟢 Active",
                    f"{stats['stats']['jobs_saved']}",
                    "SQLite"
                )
                
                console.print(table)
                
                # Show performance metrics
                console.print(f"[cyan]⏱️ Runtime: {stats['duration']}[/cyan]")
                console.print(f"[cyan]📊 Success Rate: {stats['success_rate']:.1f}%[/cyan]")
                console.print(f"[cyan]❌ Errors: {stats['stats']['errors']}[/cyan]")
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                console.print(f"[red]❌ Monitoring error: {e}[/red]")
    
    async def _is_suitable_job(self, job_data: JobData) -> bool:
        """Check if job is suitable using modern patterns."""
        title = job_data.title.lower()
        summary = job_data.summary.lower()
        
        # Skip senior positions
        senior_keywords = [
            "senior", "sr.", "lead", "principal", "director", "manager",
            "head of", "chief", "vp", "vice president", "supervisor",
            "5+ years", "6+ years", "7+ years", "8+ years", "9+ years", "10+ years"
        ]
        
        for keyword in senior_keywords:
            if keyword in title or keyword in summary:
                return False
        
        # Look for entry-level indicators
        entry_keywords = [
            "junior", "jr.", "entry", "entry-level", "graduate", "new grad",
            "associate", "trainee", "intern", "co-op", "0-2 years", "0-3 years"
        ]
        
        for keyword in entry_keywords:
            if keyword in title or keyword in summary:
                return True
        
        # Default to include if no clear senior indicators
        return True
    
    def _print_final_stats(self):
        """Print final pipeline statistics."""
        stats = self.metrics.get_performance_stats()
        
        console.print(Panel.fit("📊 PIPELINE COMPLETE", style="bold green"))
        console.print(f"[cyan]⏱️ Total runtime: {stats['duration']}[/cyan]")
        console.print(f"[cyan]📋 Jobs scraped: {stats['stats']['jobs_scraped']}[/cyan]")
        console.print(f"[cyan]🔄 Jobs processed: {stats['stats']['jobs_processed']}[/cyan]")
        console.print(f"[cyan]🧠 Jobs analyzed: {stats['stats']['jobs_analyzed']}[/cyan]")
        console.print(f"[cyan]💾 Jobs saved: {stats['stats']['jobs_saved']}[/cyan]")
        console.print(f"[cyan]🚫 Jobs failed: {stats['stats']['jobs_failed']}[/cyan]")
        console.print(f"[cyan]🔄 Jobs duplicates: {stats['stats']['jobs_duplicates']}[/cyan]")
        
        if stats['jobs_per_minute'] > 0:
            console.print(f"[bold green]⚡ Performance: {stats['jobs_per_minute']:.1f} jobs/minute[/bold green]")
        
        console.print(f"[bold green]✅ Success Rate: {stats['success_rate']:.1f}%[/bold green]")

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    console.print(f"\n[yellow]🛑 Received signal {signum}, stopping...[/yellow]")
    sys.exit(0)

async def main():
    """Main function for testing."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load profile
    try:
        with open("profiles/Nirajan/Nirajan.json", "r") as f:
            profile = json.load(f)
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return
    
    # Create modern pipeline
    config = JobPipelineConfig(
        batch_size=100,  # DDR5 optimized
        max_workers=6,   # DDR5 optimized
        buffer_size=2000, # DDR5 optimized
        enable_ai_analysis=True,
        enable_duplicate_detection=True,
        enable_streaming=True,
        ddr5_optimized=True
    )
    
    pipeline = ModernJobPipeline(profile, config)
    
    try:
        await pipeline.start()
    except KeyboardInterrupt:
        console.print(f"\n[yellow]🛑 Interrupted by user[/yellow]")
    finally:
        await pipeline.stop()

if __name__ == "__main__":
    asyncio.run(main())
