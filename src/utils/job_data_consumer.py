#!/usr/bin/env python3
"""
Multi-Process Job Data Consumer - Processes raw job data from FastElutaProducer.
Optimized for high-speed scraping with multiple worker processes.
Now includes real-time cache integration and job filtering for instant dashboard updates.
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

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.job_database import ModernJobDatabase

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

class JobDataConsumer:
    """
    Multi-process consumer that processes raw job data and saves it to the specified database.
    Optimized for high-speed scraping with multiple worker processes.
    Now includes real-time cache integration and job filtering for instant dashboard updates.
    """
    
    def __init__(self, input_dir: str, processed_dir: str, db_path: str, num_workers: int = 4):
        self.input_dir = Path(input_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.num_workers = num_workers
        
        # Process management
        self.workers = []
        self.running = False
        self.file_watcher_thread = None
        
        # Performance tracking
        self.stats = {
            'batches_processed': 0,
            'jobs_processed': 0,
            'jobs_saved': 0,
            'jobs_cached': 0,  # New stat for cache operations
            'jobs_filtered': 0,  # New stat for filtering operations
            'start_time': None,
            'end_time': None,
            'worker_stats': {},
            'filter_stats': {}  # New stat for filtering statistics
        }
        
        # File processing queue
        self.file_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        
        console.print(Panel.fit("🔄 MULTI-PROCESS JOB DATA CONSUMER", style="bold green"))
        console.print(f"[cyan]📁 Input: {self.input_dir}[/cyan]")
        console.print(f"[cyan]📁 Processed: {self.processed_dir}[/cyan]")
        console.print(f"[cyan]👥 Workers: {self.num_workers}[/cyan]")
        console.print(f"[cyan]⚡ DDR5-6400 optimized[/cyan]")
        console.print(f"[cyan]🚀 Real-time cache: {'✅ Enabled' if CACHE_AVAILABLE else '❌ Disabled'}[/cyan]")
        console.print(f"[cyan]🔍 Job filtering: {'✅ Enabled' if FILTER_AVAILABLE else '❌ Disabled'}[/cyan]")
        
        if FILTER_AVAILABLE:
            filter_config = get_filter_stats()
            console.print(f"[blue]🔍 Filter config: {filter_config['french_patterns_count']} French patterns, {filter_config['montreal_patterns_count']} Montreal patterns[/blue]")
    
    def start_processing(self) -> None:
        """Start the multi-process consumer processing loop."""
        self.stats['start_time'] = datetime.now()
        self.running = True
        
        console.print(f"\n[bold green]🚀 Starting multi-process consumer with {self.num_workers} workers[/bold green]")
        if CACHE_AVAILABLE:
            console.print(f"[green]✅ Real-time cache integration enabled - dashboard will show jobs instantly![/green]")
        else:
            console.print(f"[yellow]⚠️ Real-time cache not available - dashboard will use database only[/yellow]")
            
        if FILTER_AVAILABLE:
            console.print(f"[green]✅ Job filtering enabled - French and Montreal jobs will be filtered out![/green]")
        else:
            console.print(f"[yellow]⚠️ Job filtering not available - all jobs will be processed[/yellow]")
        
        # Start worker processes
        self._start_workers()
        
        # Start file watcher thread
        self.file_watcher_thread = threading.Thread(target=self._file_watcher_loop)
        self.file_watcher_thread.daemon = True
        self.file_watcher_thread.start()
        
        # Start result processor thread
        result_thread = threading.Thread(target=self._result_processor_loop)
        result_thread.daemon = True
        result_thread.start()
        
        # Keep main thread alive to show stats
        try:
            while self.running:
                # Check if file watcher is still alive
                if not self.file_watcher_thread.is_alive():
                    console.print("[yellow]⚠️ File watcher stopped, ending processing[/yellow]")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 Interrupted by user[/yellow]")
        finally:
            self.stop_processing()

    def stop_processing(self) -> None:
        """Stop the consumer processing."""
        if not self.running:
            return
            
        console.print("\n[yellow]🛑 Stopping multi-process consumer...[/yellow]")
        self.running = False
        
        # Stop workers
        self._stop_workers()
        
        # Wait for threads to finish
        if self.file_watcher_thread:
            self.file_watcher_thread.join(timeout=5)
        
        self.stats['end_time'] = datetime.now()
        self._print_final_stats()
    
    def _start_workers(self) -> None:
        """Start worker processes."""
        for i in range(self.num_workers):
            worker = multiprocessing.Process(
                target=JobDataConsumer._worker_process,
                args=(i, self.file_queue, self.result_queue, self.db_path)
            )
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            console.print(f"[green]✅ Started worker {i+1}/{self.num_workers}[/green]")
    
    def _stop_workers(self) -> None:
        """Stop all worker processes."""
        console.print(f"[yellow]🛑 Stopping {len(self.workers)} workers...[/yellow]")
        
        # Send stop signal to all workers
        for _ in self.workers:
            self.file_queue.put(None)  # Stop signal
        
        # Wait for workers to finish
        for i, worker in enumerate(self.workers):
            worker.join(timeout=10)
            if worker.is_alive():
                console.print(f"[red]❌ Force killing worker {i+1}[/red]")
                worker.terminate()
                worker.join(timeout=5)
            else:
                console.print(f"[green]✅ Worker {i+1} stopped cleanly[/green]")
        
        self.workers.clear()
    
    def _file_watcher_loop(self) -> None:
        """Watch for new batch files and add them to the processing queue."""
        processed_files = set()
        
        while self.running:
            try:
                batch_files = list(self.input_dir.glob("jobs_batch_*.json"))
                
                new_files_found = False
                for filepath in batch_files:
                    if filepath.name not in processed_files:
                        console.print(f"[cyan]📦 Adding {filepath.name} to processing queue[/cyan]")
                        self.file_queue.put(str(filepath))
                        processed_files.add(filepath.name)
                        new_files_found = True
                
                # If no new files, wait a bit
                if not new_files_found:
                    time.sleep(2)
                    
            except Exception as e:
                console.print(f"[red]❌ File watcher error: {e}[/red]")
                time.sleep(5)
        
        console.print("[cyan]✅ File watcher stopped.[/cyan]")
    
    def _result_processor_loop(self) -> None:
        """Process results from worker processes."""
        while self.running:
            try:
                # Non-blocking get with timeout
                result = self.result_queue.get(timeout=1)
                if result:
                    self._handle_worker_result(result)
            except Empty:
                continue
            except Exception as e:
                console.print(f"[red]❌ Result processor error: {e}[/red]")
                time.sleep(1)
    
    def _handle_worker_result(self, result: Dict) -> None:
        """Handle a result from a worker process."""
        try:
            worker_id = result.get('worker_id', 'unknown')
            batch_id = result.get('batch_id', 'unknown')
            jobs_processed = result.get('jobs_processed', 0)
            jobs_saved = result.get('jobs_saved', 0)
            jobs_cached = result.get('jobs_cached', 0)  # New stat
            jobs_filtered = result.get('jobs_filtered', 0)  # New stat
            filter_stats = result.get('filter_stats', {})  # New stat
            error = result.get('error')
            
            # Update stats
            self.stats['batches_processed'] += 1
            self.stats['jobs_processed'] += jobs_processed
            self.stats['jobs_saved'] += jobs_saved
            self.stats['jobs_cached'] += jobs_cached  # New stat
            self.stats['jobs_filtered'] += jobs_filtered  # New stat
            
            # Update filter stats
            for key, value in filter_stats.items():
                if key not in self.stats['filter_stats']:
                    self.stats['filter_stats'][key] = 0
                self.stats['filter_stats'][key] += value
            
            # Update worker stats
            if worker_id not in self.stats['worker_stats']:
                self.stats['worker_stats'][worker_id] = {
                    'jobs_processed': 0,
                    'jobs_saved': 0,
                    'jobs_cached': 0,
                    'jobs_filtered': 0
                }
            
            self.stats['worker_stats'][worker_id]['jobs_processed'] += jobs_processed
            self.stats['worker_stats'][worker_id]['jobs_saved'] += jobs_saved
            self.stats['worker_stats'][worker_id]['jobs_cached'] += jobs_cached
            self.stats['worker_stats'][worker_id]['jobs_filtered'] += jobs_filtered
            
            if error:
                console.print(f"[red]❌ Worker {worker_id} error: {error}[/red]")
            else:
                console.print(f"[green]✅ Worker {worker_id} completed batch {batch_id}: {jobs_processed} processed, {jobs_saved} saved, {jobs_cached} cached, {jobs_filtered} filtered[/green]")
                
            # After all jobs processed, check if any jobs were saved (only in worker 0)
            if worker_id == 0:
                try:
                    if db:
                        stats = db.get_stats()
                        if stats.get('total_jobs', 0) == 0:
                            console.print("[yellow]⚠️ WARNING: No jobs saved to the database! Check for errors above.[/yellow]")
                except Exception as e:
                    console.print(f"[red]❌ Error checking final DB stats: {e}[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ Error handling worker result: {e}[/red]")
    
    def _print_final_stats(self) -> None:
        """Print final system statistics."""
        if not self.stats['start_time']:
            return
        
        duration = self.stats['end_time'] - self.stats['start_time']
        
        console.print(Panel.fit("📊 MULTI-PROCESS CONSUMER COMPLETE", style="bold green"))
        console.print(f"[cyan]⏱️ Total runtime: {duration}[/cyan]")
        console.print(f"[cyan]📦 Batches processed: {self.stats['batches_processed']}[/cyan]")
        console.print(f"[cyan]🔄 Jobs processed: {self.stats['jobs_processed']}[/cyan]")
        console.print(f"[cyan]💾 Jobs saved: {self.stats['jobs_saved']}[/cyan]")
        console.print(f"[cyan]🚀 Jobs cached: {self.stats['jobs_cached']}[/cyan]")
        console.print(f"[cyan]🔍 Jobs filtered: {self.stats['jobs_filtered']}[/cyan]")
        
        # Print filter statistics
        if self.stats['filter_stats']:
            console.print(f"\n[bold yellow]🔍 Filter Statistics:[/bold yellow]")
            for key, value in self.stats['filter_stats'].items():
                console.print(f"  {key}: {value}")
        
        if duration.total_seconds() > 0:
            overall_speed = (self.stats['jobs_saved'] / duration.total_seconds()) * 60
            console.print(f"[bold green]⚡ Overall performance: {overall_speed:.1f} jobs/minute[/bold green]")
        
        console.print(f"\n[bold yellow]👥 Worker Performance:[/bold yellow]")
        for worker_id, stats in self.stats['worker_stats'].items():
            console.print(f"  Worker {worker_id}: {stats['jobs_saved']} jobs saved, {stats['jobs_cached']} cached, {stats['jobs_filtered']} filtered")

    @staticmethod
    def _worker_process(worker_id: int, file_queue: multiprocessing.Queue, result_queue: multiprocessing.Queue, db_path: str):
        """Worker process function."""
        console = Console()
        console.print(f"[cyan]🔄 Worker {worker_id} started[/cyan]")
        
        # Initialize database connection for this worker
        db = None
        try:
            db = ModernJobDatabase(db_path=db_path)
            console.print(f"[green]✅ Worker {worker_id} database connection established[/green]")
        except Exception as e:
            console.print(f"[red]❌ Worker {worker_id} failed to connect to database: {e}[/red]")
            return
        
        while True:
            try:
                # Get file from queue
                filepath_str = file_queue.get(timeout=30)  # 30 second timeout
                
                # Check for stop signal
                if filepath_str is None:
                    console.print(f"[cyan]🛑 Worker {worker_id} received stop signal[/cyan]")
                    break
                
                filepath = Path(filepath_str)
                if not filepath.exists():
                    console.print(f"[yellow]⚠️ Worker {worker_id}: File {filepath} no longer exists[/yellow]")
                    continue
                
                # Process the batch file
                result = JobDataConsumer._process_batch_file_worker(worker_id, filepath, db)
                result_queue.put(result)
                
            except Empty:
                console.print(f"[yellow]⚠️ Worker {worker_id} timeout waiting for files[/yellow]")
                continue
            except Exception as e:
                console.print(f"[red]❌ Worker {worker_id} error: {e}[/red]")
                result_queue.put({
                    'worker_id': worker_id,
                    'batch_id': 'unknown',
                    'jobs_processed': 0,
                    'jobs_saved': 0,
                    'jobs_cached': 0,
                    'jobs_filtered': 0,
                    'filter_stats': {},
                    'error': str(e)
                })
        
        console.print(f"[cyan]✅ Worker {worker_id} finished[/cyan]")

    @staticmethod
    def _process_batch_file_worker(worker_id: int, filepath: Path, db: ModernJobDatabase) -> Dict:
        """Process a batch file in a worker process."""
        console = Console()
        
        try:
            console.print(f"[cyan]🔄 Worker {worker_id} processing {filepath.name}[/cyan]")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
            
            jobs = batch_data.get('jobs', [])
            batch_id = batch_data.get('batch_id', 'unknown')
            
            jobs_processed = 0
            jobs_saved = 0
            jobs_cached = 0  # New counter
            jobs_filtered = 0  # New counter
            filter_stats = {}  # New counter
            
            # Apply job filtering if available
            if FILTER_AVAILABLE:
                try:
                    kept_jobs, filtered_jobs, batch_filter_stats = filter_jobs_batch(jobs)
                    jobs = kept_jobs  # Only process kept jobs
                    jobs_filtered = len(filtered_jobs)
                    filter_stats = batch_filter_stats
                    
                    console.print(f"[blue]🔍 Worker {worker_id} filtered {jobs_filtered} jobs (French/Montreal), keeping {len(jobs)}[/blue]")
                    
                    # Log some filtered jobs for debugging
                    if filtered_jobs:
                        for i, filtered_job in enumerate(filtered_jobs[:3]):  # Show first 3
                            score = filtered_job.get('filter_score', 0)
                            title = filtered_job.get('title', 'Unknown')[:40]
                            console.print(f"[yellow]🔍 Filtered job {i+1}: {title}... (score: {score})[/yellow]")
                            
                except Exception as filter_error:
                    console.print(f"[yellow]⚠️ Worker {worker_id} filtering error: {filter_error}[/yellow]")
                    # Continue with original jobs if filtering fails
            
            for raw_job in jobs:
                try:
                    processed_job = JobDataConsumer._process_single_job_worker(raw_job)
                    if processed_job:
                        # Save to database with better error handling
                        try:
                            success = db.add_job(processed_job)
                            if success:
                                jobs_saved += 1
                                console.print(f"[green]✅ Worker {worker_id} saved job: {processed_job.get('title', 'Unknown')[:30]}...[/green]")
                                
                                # Add to real-time cache for instant dashboard updates
                                try:
                                    if CACHE_AVAILABLE:
                                        add_job_to_cache(processed_job)
                                        jobs_cached += 1
                                        console.print(f"[blue]🚀 Worker {worker_id} cached job for real-time dashboard[/blue]")
                                except Exception as cache_error:
                                    console.print(f"[yellow]⚠️ Worker {worker_id} cache error: {cache_error}[/yellow]")
                            else:
                                console.print(f"[yellow]⚠️ Worker {worker_id} job not saved (duplicate?): {processed_job.get('title', 'Unknown')[:30]}...[/yellow]")
                        except Exception as db_error:
                            console.print(f"[red]❌ Worker {worker_id} database save error: {db_error}[/red]")
                            console.print(f"[red]❌ Job data: {processed_job.get('title', 'Unknown')}[/red]")
                    jobs_processed += 1
                    
                except Exception as e:
                    console.print(f"[yellow]⚠️ Worker {worker_id} job processing error: {e}[/yellow]")
                    continue
            
            console.print(f"[green]✅ Worker {worker_id} completed {filepath.name}: {jobs_processed} processed, {jobs_saved} saved, {jobs_cached} cached, {jobs_filtered} filtered[/green]")
            
            return {
                'worker_id': worker_id,
                'batch_id': batch_id,
                'jobs_processed': jobs_processed,
                'jobs_saved': jobs_saved,
                'jobs_cached': jobs_cached,
                'jobs_filtered': jobs_filtered,
                'filter_stats': filter_stats,
                'error': None
            }
            
            # NOTE: For full DB check after all batches, this should be done in the orchestrator or after all workers finish.
            
        except json.JSONDecodeError:
            error_msg = f"Invalid JSON in {filepath.name}"
            console.print(f"[red]❌ Worker {worker_id}: {error_msg}[/red]")
            return {
                'worker_id': worker_id,
                'batch_id': filepath.name,
                'jobs_processed': 0,
                'jobs_saved': 0,
                'jobs_cached': 0,
                'jobs_filtered': 0,
                'filter_stats': {},
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Error processing {filepath.name}: {e}"
            console.print(f"[red]❌ Worker {worker_id}: {error_msg}[/red]")
            return {
                'worker_id': worker_id,
                'batch_id': filepath.name,
                'jobs_processed': 0,
                'jobs_saved': 0,
                'jobs_cached': 0,
                'jobs_filtered': 0,
                'filter_stats': {},
                'error': error_msg
            }

    @staticmethod
    def _process_single_job_worker(raw_job: Dict) -> Optional[Dict]:
        """Transform a raw job into the database schema format in worker process."""
        try:
            # Only require title and URL
            if not raw_job.get("title"):
                return None
            
            # Only save jobs with valid URLs
            url = raw_job.get("url", "")
            if not url or url.strip() == "":
                return None  # Skip jobs without URLs
            
            processed_job = {
                "title": raw_job.get("title", ""),
                "company": raw_job.get("company", ""),
                "location": raw_job.get("location", ""),
                "summary": raw_job.get("summary", ""),
                "url": url,  # Use the extracted URL
                "job_id": raw_job.get("job_id", ""),
                "site": "eluta",
                "keyword": raw_job.get("search_keyword", ""),
                "page_num": raw_job.get("page_number", 0),
                "job_num": raw_job.get("job_number", 0),
                "timestamp": raw_job.get("scraped_at", ""),
                "session_id": raw_job.get("session_id", "")
            }
            
            # Add filter information if available
            if 'filter_score' in raw_job:
                processed_job['filter_score'] = raw_job['filter_score']
                processed_job['filter_reasons'] = raw_job.get('filter_reasons', [])
                processed_job['filter_penalties'] = raw_job.get('filter_penalties', [])
                processed_job['filter_warnings'] = raw_job.get('filter_warnings', [])
            
            return processed_job
            
        except Exception as e:
            console = Console()
            console.print(f"[red]❌ Error processing job: {e}[/red]")
            return None

def main():
    """Main function for testing the multi-process consumer independently."""
    console.print(Panel("Running Multi-Process JobDataConsumer Standalone Test", style="bold yellow"))
    
    # Configuration
    temp_dir = Path("temp_consumer_test")
    input_dir = temp_dir / "raw_jobs"
    processed_dir = temp_dir / "processed"
    db_path = temp_dir / "test_jobs.db"
    
    # Cleanup previous run
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
        
    input_dir.mkdir(parents=True)
    
    # Create dummy batch files for testing
    for i in range(3):
        dummy_job = {
            "title": f"Software Engineer {i}",
            "company": f"TestCorp {i}",
            "location": "Testville",
            "summary": f"This is test job {i}.",
            "url": f"http://example.com/job/{i}",
            "job_id": f"test{i}",
            "scraped_at": datetime.now().isoformat(),
            "search_keyword": "testing",
            "session_id": "test-session",
        }
        dummy_batch = {"batch_id": i+1, "jobs": [dummy_job]}
        with open(input_dir / f"jobs_batch_{i+1}.json", "w") as f:
            json.dump(dummy_batch, f)
        
    console.print(f"Created {3} dummy batch files in {input_dir}")
    
    # Initialize and run consumer with 2 workers
    consumer = JobDataConsumer(str(input_dir), str(processed_dir), str(db_path), num_workers=2)
    
    try:
        # Run for a short period to process the files
        processing_thread = threading.Thread(target=consumer.start_processing)
        processing_thread.daemon = True
        processing_thread.start()
        
        time.sleep(10)  # Let it run for 10 seconds
        
    finally:
        consumer.stop_processing()
        console.print("\nStandalone test finished.")

if __name__ == "__main__":
    main() 