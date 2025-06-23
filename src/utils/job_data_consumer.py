#!/usr/bin/env python3
"""
Multi-Process Job Data Consumer - Processes individual job data concurrently.
Optimized for high-speed processing with a modern ProcessPoolExecutor.
"""

import json
import time
import os
import sys
import threading
import multiprocessing
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from queue import Queue, Empty
import signal
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.job_database import ModernJobDatabase
from src.utils.job_filters import filter_job, filter_jobs_batch, get_filter_stats

# Import the real-time cache
try:
    from src.dashboard.job_cache import add_job_to_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

# Import the job filtering system
try:
    from src.utils.job_filters import filter_job, filter_jobs_batch, get_filter_stats
    FILTER_AVAILABLE = True
except ImportError:
    FILTER_AVAILABLE = False

console = Console()

def worker_process(job_data: Dict, db_path: str) -> Optional[Dict]:
    """
    Worker function to process a single job.
    This function runs in a separate process.
    """
    try:
        db = ModernJobDatabase(db_path=db_path)
        
        # 1. Filter the job
        if filter_job(job_data):
            # console.print(f"[yellow]Filtered out job: {job_data.get('job_title')}[/yellow]")
            return {"status": "filtered"}

        # 2. Enhance job data (placeholder for future AI analysis)
        job_data['enhanced'] = True
        job_data['analyzed_at'] = datetime.now().isoformat()

        # 3. Save to database
        was_saved = db.add_job(job_data)
        
        if was_saved:
            # console.print(f"[green]Saved job: {job_data.get('job_title')}[/green]")
            return {"status": "saved", "job_hash": job_data.get('job_id')}
        else:
            # console.print(f"[blue]Job already exists: {job_data.get('job_title')}[/blue]")
            return {"status": "duplicate"}
            
    except Exception as e:
        # console.print(f"[red]Error processing job: {e}[/red]")
        return {"status": "error", "error": str(e)}


class JobDataConsumer:
    """
    Legacy JobDataConsumer class for backward compatibility with tests.
    This wraps the modern JobProcessor functionality.
    """
    
    def __init__(self, raw_dir: str, processed_dir: str, db_path: Optional[str] = None, num_workers: int = 4):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.db_path = db_path if db_path is not None else "data/jobs.db"
        self.num_workers = num_workers
        self.processor = JobProcessor(self.db_path, num_workers)
        self.processing = False
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[green]✅ JobDataConsumer initialized[/green]")
        console.print(f"Raw directory: {self.raw_dir}")
        console.print(f"Processed directory: {self.processed_dir}")
        console.print(f"Database: {self.db_path}")
        console.print(f"Workers: {self.num_workers}")

    def start_processing(self):
        """Start processing jobs from the raw directory."""
        self.processing = True
        console.print("[cyan]🚀 Starting job processing...[/cyan]")
        
        # Process any existing files in raw directory
        for file_path in self.raw_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    job_data = json.load(f)
                self.processor.submit_job(job_data)
                
                # Move to processed directory
                processed_file = self.processed_dir / file_path.name
                file_path.rename(processed_file)
                
            except Exception as e:
                console.print(f"[red]Error processing file {file_path}: {e}[/red]")

    def stop_processing(self):
        """Stop processing and wait for completion."""
        self.processing = False
        console.print("[yellow]🛑 Stopping job processing...[/yellow]")
        self.processor.wait_for_completion()

    def process_batch_file(self, file_path: str):
        """Process a specific batch file."""
        try:
            with open(file_path, 'r') as f:
                jobs = json.load(f)
            
            if isinstance(jobs, list):
                for job in jobs:
                    self.processor.submit_job(job)
            else:
                self.processor.submit_job(jobs)
                
        except Exception as e:
            console.print(f"[red]Error processing batch file {file_path}: {e}[/red]")

    def get_queue_size(self) -> int:
        """Get the current queue size."""
        return len(self.processor.futures)

    def get_memory_usage(self) -> Dict:
        """Get memory usage statistics."""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'percent': process.memory_percent()
        }


class JobProcessor:
    """
    Manages a pool of worker processes to consume and process job data concurrently.
    """
    
    def __init__(self, db_path: str, num_workers: int = 4):
        self.db_path = db_path
        self.num_workers = num_workers
        self.executor = ProcessPoolExecutor(max_workers=self.num_workers)
        self.futures = []
        
        self.stats = {
            'total_processed': 0,
            'saved': 0,
            'filtered': 0,
            'duplicates': 0,
            'errors': 0,
            'start_time': time.time(),
        }

        console.print(Panel.fit("🚀 JOB PROCESSOR INITIALIZED", style="bold green"))
        console.print(f"Database: {self.db_path}")
        console.print(f"Workers: {self.num_workers}")

    def submit_job(self, job_data: Dict):
        """Submits a single job to the processing pool."""
        future = self.executor.submit(worker_process, job_data, self.db_path)
        self.futures.append(future)

    def wait_for_completion(self):
        """Waits for all submitted jobs to finish and processes the results."""
        console.print(f"\n[cyan]Waiting for {len(self.futures)} jobs to complete...[/cyan]")

        for future in as_completed(self.futures):
            try:
                result = future.result()
                if result:
                    self.stats['total_processed'] += 1
                    status = result.get("status")
                    if status == "saved":
                        self.stats['saved'] += 1
                    elif status == "filtered":
                        self.stats['filtered'] += 1
                    elif status == "duplicate":
                        self.stats['duplicates'] += 1
                    elif status == "error":
                        self.stats['errors'] += 1
                        # console.print(f"[red]ERROR: {result.get('error')}[/red]")

            except Exception as e:
                self.stats['errors'] += 1
                console.print(f"[bold red]Future result retrieval failed: {e}[/bold red]")
        
        self.shutdown()

    def shutdown(self):
        """Shuts down the executor and prints final stats."""
        self.executor.shutdown(wait=True)
        self.stats['end_time'] = time.time()
        self.print_final_stats()

    def print_final_stats(self):
        """Prints the final processing statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']
        jobs_per_sec = self.stats['total_processed'] / duration if duration > 0 else 0

        console.print(Panel.fit("📊 JOB PROCESSING COMPLETE", style="bold green"))
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        
        table.add_row("Total Jobs Processed", f"{self.stats['total_processed']:,}")
        table.add_row("✅ Jobs Saved", f"[green]{self.stats['saved']:,}[/green]")
        table.add_row("🔵 Duplicates Found", f"[blue]{self.stats['duplicates']:,}[/blue]")
        table.add_row("🟡 Jobs Filtered", f"[yellow]{self.stats['filtered']:,}[/yellow]")
        table.add_row("❌ Errors", f"[red]{self.stats['errors']:,}[/red]")
        table.add_row("⏱️ Duration", f"{duration:.2f} seconds")
        table.add_row("⚡ Speed", f"{jobs_per_sec:.2f} jobs/sec")
        
        console.print(table)


# Example Usage
if __name__ == '__main__':
    # This is a demonstration of how the new JobProcessor works.
    
    # 1. Setup
    console.print("\n--- DEMO: Job Processor ---")
    demo_db_path = "temp/demo_jobs.db"
    if os.path.exists(demo_db_path):
        os.remove(demo_db_path)
    
    # 2. Create a JobProcessor instance
    processor = JobProcessor(db_path=demo_db_path, num_workers=4)
    
    # 3. Simulate submitting jobs from a scraper
    console.print("\n[cyan]Simulating job submission...[/cyan]")
    for i in range(100):
        job = {
            'job_id': f'demo_{i}',
            'job_title': f'Software Engineer {i}',
            'company_name': 'Tech Corp',
            'location': 'Toronto, ON',
            'job_url': f'http://example.com/job/{i}',
            'scraped_at': datetime.now().isoformat()
        }
        # Simulate some jobs that should be filtered
        if i % 10 == 0:
            job['job_title'] = 'Ingénieur Logiciel' # French title
        
        processor.submit_job(job)
        
    # Add a duplicate job
    processor.submit_job({
        'job_id': 'demo_5', 'job_title': 'Software Engineer 5', 'company_name': 'Tech Corp', 
        'location': 'Toronto, ON', 'job_url': 'http://example.com/job/5', 
        'scraped_at': datetime.now().isoformat()
    })

    # 4. Wait for all jobs to be processed
    processor.wait_for_completion()
    
    # 5. Verify database content
    console.print("\n[cyan]Verifying database content...[/cyan]")
    db = ModernJobDatabase(demo_db_path)
    stats = db.get_stats()
    console.print(f"Jobs in database: {stats.get('total_jobs')}")
    console.print("--- DEMO COMPLETE ---") 