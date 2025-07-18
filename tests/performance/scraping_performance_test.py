#!/usr/bin/env python3
"""
Scraping Performance Test
Runs scraping for 1 minute and tracks producer, consumer, and data processing metrics.
"""

import time
import sys
import threading
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from datetime import datetime
import queue

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

console = Console()


class ScrapingMetrics:
    """Track scraping performance metrics."""

    def __init__(self):
        self.start_time = time.time()
        self.producer_jobs_scraped = 0
        self.consumer_jobs_processed = 0
        self.jobs_saved_to_db = 0
        self.jobs_updated = 0
        self.errors = 0
        self.duplicates_found = 0
        self.session_creations = 0
        self.database_queries = 0
        self.hash_generations = 0
        self.lock = threading.Lock()

    def increment_producer(self):
        with self.lock:
            self.producer_jobs_scraped += 1

    def increment_consumer(self):
        with self.lock:
            self.consumer_jobs_processed += 1

    def increment_saved(self):
        with self.lock:
            self.jobs_saved_to_db += 1

    def increment_updated(self):
        with self.lock:
            self.jobs_updated += 1

    def increment_error(self):
        with self.lock:
            self.errors += 1

    def increment_duplicate(self):
        with self.lock:
            self.duplicates_found += 1

    def increment_session(self):
        with self.lock:
            self.session_creations += 1

    def increment_query(self):
        with self.lock:
            self.database_queries += 1

    def increment_hash(self):
        with self.lock:
            self.hash_generations += 1

    def get_elapsed_time(self):
        return time.time() - self.start_time

    def get_jobs_per_second(self):
        elapsed = self.get_elapsed_time()
        if elapsed > 0:
            return self.producer_jobs_scraped / elapsed
        return 0

    def get_processing_rate(self):
        elapsed = self.get_elapsed_time()
        if elapsed > 0:
            return self.consumer_jobs_processed / elapsed
        return 0


def simulate_producer(metrics, stop_event):
    """Simulate job producer/scraper."""
    try:
        from src.scrapers.session_manager import SessionManager
        from src.utils.job_helpers import generate_job_hash

        session_manager = SessionManager("performance_test")
        metrics.increment_session()

        job_id = 0
        while not stop_event.is_set():
            # Simulate scraping a job
            job = {
                "title": f"Software Engineer {job_id}",
                "company": f"Tech Corp {job_id % 10}",
                "location": f"City {job_id % 5}",
                "url": f"https://example.com/job/{job_id}",
                "description": f"Job description for position {job_id}",
                "salary": f"${50000 + (job_id * 1000)}",
                "requirements": ["Python", "JavaScript", "SQL"],
                "scraped_at": datetime.now().isoformat(),
            }

            # Generate hash for job
            job_hash = generate_job_hash(job)
            metrics.increment_hash()

            # Simulate processing time
            time.sleep(0.1)  # 100ms per job

            metrics.increment_producer()
            job_id += 1

    except Exception as e:
        console.print(f"[red]Producer error: {e}[/red]")
        metrics.increment_error()


def simulate_consumer(metrics, stop_event):
    """Simulate job consumer/processor."""
    try:
        from src.core.job_database import get_job_db
        from src.utils.job_helpers import is_duplicate_job

        db = get_job_db("Nirajan")

        while not stop_event.is_set():
            # Simulate processing a job
            time.sleep(0.05)  # 50ms per job

            # Simulate database operations
            existing_jobs = db.get_all_jobs()
            metrics.increment_query()

            # Simulate duplicate checking
            if len(existing_jobs) > 0:
                # Check against first existing job
                test_job = {
                    "title": "Test Job",
                    "company": "Test Company",
                    "url": "https://test.com",
                }
                if is_duplicate_job(test_job, existing_jobs[0]):
                    metrics.increment_duplicate()

            # Simulate saving job (not actually saving to avoid polluting DB)
            metrics.increment_saved()

            # Simulate updating job status
            metrics.increment_updated()

            metrics.increment_consumer()

    except Exception as e:
        console.print(f"[red]Consumer error: {e}[/red]")
        metrics.increment_error()


def create_metrics_display(metrics):
    """Create real-time metrics display."""
    elapsed = metrics.get_elapsed_time()
    jobs_per_sec = metrics.get_jobs_per_second()
    processing_rate = metrics.get_processing_rate()

    # Create layout
    layout = Layout()

    # Header
    header = Panel(
        f"[bold blue]🕷️ AutoJobAgent Scraping Performance Test[/bold blue]\n"
        f"[cyan]Elapsed Time: {elapsed:.1f}s[/cyan] | "
        f"[green]Jobs/Second: {jobs_per_sec:.1f}[/green] | "
        f"[yellow]Processing Rate: {processing_rate:.1f}[/yellow]",
        style="bold",
    )

    # Metrics table
    metrics_table = Table(show_header=True, header_style="bold magenta")
    metrics_table.add_column("Metric", style="cyan", width=25)
    metrics_table.add_column("Count", style="yellow", width=15)
    metrics_table.add_column("Rate", style="green", width=15)

    metrics_table.add_row(
        "Producer Jobs Scraped", str(metrics.producer_jobs_scraped), f"{jobs_per_sec:.1f}/s"
    )
    metrics_table.add_row(
        "Consumer Jobs Processed", str(metrics.consumer_jobs_processed), f"{processing_rate:.1f}/s"
    )
    metrics_table.add_row(
        "Jobs Saved to DB",
        str(metrics.jobs_saved_to_db),
        f"{metrics.jobs_saved_to_db/elapsed:.1f}/s" if elapsed > 0 else "0/s",
    )
    metrics_table.add_row(
        "Jobs Updated",
        str(metrics.jobs_updated),
        f"{metrics.jobs_updated/elapsed:.1f}/s" if elapsed > 0 else "0/s",
    )
    metrics_table.add_row(
        "Hash Generations",
        str(metrics.hash_generations),
        f"{metrics.hash_generations/elapsed:.1f}/s" if elapsed > 0 else "0/s",
    )
    metrics_table.add_row(
        "Database Queries",
        str(metrics.database_queries),
        f"{metrics.database_queries/elapsed:.1f}/s" if elapsed > 0 else "0/s",
    )
    metrics_table.add_row("Session Creations", str(metrics.session_creations), "N/A")
    metrics_table.add_row(
        "Duplicates Found",
        str(metrics.duplicates_found),
        f"{metrics.duplicates_found/elapsed:.1f}/s" if elapsed > 0 else "0/s",
    )
    metrics_table.add_row(
        "Errors", str(metrics.errors), f"{metrics.errors/elapsed:.1f}/s" if elapsed > 0 else "0/s"
    )

    # Performance indicators
    performance_panel = Panel(
        (
            f"[bold]Performance Indicators:[/bold]\n"
            f"• [green]Producer Efficiency:[/green] {jobs_per_sec:.1f} jobs/second\n"
            f"• [blue]Consumer Efficiency:[/blue] {processing_rate:.1f} jobs/second\n"
            f"• [yellow]Database Operations:[/yellow] {metrics.database_queries/elapsed:.1f} queries/second\n"
            f"• [cyan]Hash Generation:[/cyan] {metrics.hash_generations/elapsed:.1f} hashes/second\n"
            f"• [red]Error Rate:[/red] {metrics.errors/elapsed:.2f} errors/second"
            if elapsed > 0
            else "0 errors/second"
        ),
        title="Performance Analysis",
        style="bold",
    )

    return Panel(
        f"{header}\n\n{metrics_table}\n\n{performance_panel}",
        title="Live Scraping Metrics",
        style="bold",
    )


def run_scraping_performance_test(duration_seconds=60):
    """Run scraping performance test for specified duration."""
    console.print(Panel("[bold blue]🚀 Starting Scraping Performance Test[/bold blue]"))
    console.print(f"[cyan]Test Duration: {duration_seconds} seconds[/cyan]")

    # Initialize metrics
    metrics = ScrapingMetrics()
    stop_event = threading.Event()

    # Start producer and consumer threads
    producer_thread = threading.Thread(target=simulate_producer, args=(metrics, stop_event))
    consumer_thread = threading.Thread(target=simulate_consumer, args=(metrics, stop_event))

    producer_thread.start()
    consumer_thread.start()

    # Run with live display
    with Live(create_metrics_display(metrics), refresh_per_second=4) as live:
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            live.update(create_metrics_display(metrics))
            time.sleep(0.25)  # Update every 250ms

        # Stop threads
        stop_event.set()
        producer_thread.join()
        consumer_thread.join()

        # Final update
        live.update(create_metrics_display(metrics))

    # Display final results
    console.print("\n[bold green]📊 Final Performance Results[/bold green]")

    final_table = Table(show_header=True, header_style="bold magenta")
    final_table.add_column("Metric", style="cyan", width=30)
    final_table.add_column("Total", style="yellow", width=15)
    final_table.add_column("Rate", style="green", width=20)
    final_table.add_column("Performance", style="blue", width=20)

    elapsed = metrics.get_elapsed_time()

    # Calculate rates
    producer_rate = metrics.producer_jobs_scraped / elapsed if elapsed > 0 else 0
    consumer_rate = metrics.consumer_jobs_processed / elapsed if elapsed > 0 else 0
    db_rate = metrics.database_queries / elapsed if elapsed > 0 else 0
    hash_rate = metrics.hash_generations / elapsed if elapsed > 0 else 0

    final_table.add_row(
        "Producer Jobs Scraped",
        str(metrics.producer_jobs_scraped),
        f"{producer_rate:.1f}/s",
        "✅ Good" if producer_rate > 5 else "⚠️ Slow",
    )
    final_table.add_row(
        "Consumer Jobs Processed",
        str(metrics.consumer_jobs_processed),
        f"{consumer_rate:.1f}/s",
        "✅ Good" if consumer_rate > 5 else "⚠️ Slow",
    )
    final_table.add_row(
        "Jobs Saved to Database",
        str(metrics.jobs_saved_to_db),
        f"{metrics.jobs_saved_to_db/elapsed:.1f}/s" if elapsed > 0 else "0/s",
        "✅ Good",
    )
    final_table.add_row(
        "Jobs Updated",
        str(metrics.jobs_updated),
        f"{metrics.jobs_updated/elapsed:.1f}/s" if elapsed > 0 else "0/s",
        "✅ Good",
    )
    final_table.add_row(
        "Hash Generations",
        str(metrics.hash_generations),
        f"{hash_rate:.1f}/s",
        "✅ Good" if hash_rate > 5 else "⚠️ Slow",
    )
    final_table.add_row(
        "Database Queries",
        str(metrics.database_queries),
        f"{db_rate:.1f}/s",
        "✅ Good" if db_rate > 5 else "⚠️ Slow",
    )
    final_table.add_row("Session Creations", str(metrics.session_creations), "N/A", "✅ Good")
    final_table.add_row(
        "Duplicates Found",
        str(metrics.duplicates_found),
        f"{metrics.duplicates_found/elapsed:.1f}/s" if elapsed > 0 else "0/s",
        "✅ Good",
    )
    final_table.add_row(
        "Errors",
        str(metrics.errors),
        f"{metrics.errors/elapsed:.2f}/s" if elapsed > 0 else "0/s",
        "✅ Good" if metrics.errors == 0 else "⚠️ Issues",
    )

    console.print(final_table)

    # Performance summary
    console.print(f"\n[bold blue]🎯 Performance Summary[/bold blue]")
    console.print(f"⏱️ Total Test Duration: {elapsed:.1f} seconds")
    console.print(f"🚀 Producer Performance: {producer_rate:.1f} jobs/second")
    console.print(f"⚡ Consumer Performance: {consumer_rate:.1f} jobs/second")
    console.print(f"💾 Database Performance: {db_rate:.1f} queries/second")
    console.print(f"🔐 Hash Performance: {hash_rate:.1f} hashes/second")

    # Performance grade
    if producer_rate > 10 and consumer_rate > 10 and metrics.errors == 0:
        console.print("[green]🏆 Performance Grade: A+ (Excellent)[/green]")
        console.print("[green]🎉 System is performing at peak efficiency![/green]")
    elif producer_rate > 5 and consumer_rate > 5 and metrics.errors <= 1:
        console.print("[yellow]📊 Performance Grade: A (Very Good)[/yellow]")
        console.print("[yellow]✅ System is performing very well[/yellow]")
    elif producer_rate > 2 and consumer_rate > 2:
        console.print("[blue]📊 Performance Grade: B (Good)[/blue]")
        console.print("[blue]✅ System is performing well[/blue]")
    else:
        console.print("[red]📊 Performance Grade: C (Needs Improvement)[/red]")
        console.print("[red]⚠️ System performance needs optimization[/red]")

    return metrics


if __name__ == "__main__":
    # Run test for 60 seconds (1 minute)
    run_scraping_performance_test(60)
