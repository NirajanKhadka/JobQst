#!/usr/bin/env python3
"""
Producer-Consumer Orchestrator - Manages FastElutaProducer and JobDataConsumer.
Optimized for DDR5-6400 and high-performance job automation.
"""

import json
import time
import threading
import signal
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

# Import our producer and consumer
try:
    from src.scrapers.fast_eluta_producer import FastElutaProducer
    from src.utils.job_data_consumer import JobDataConsumer
    from src.core.job_database import ModernJobDatabase
except ImportError:
    # Fallback for direct script execution
    from fast_eluta_producer import FastElutaProducer
    from src.utils.job_data_consumer import JobDataConsumer
    from src.core.job_database import ModernJobDatabase

console = Console()

class ProducerConsumerOrchestrator:
    """
    Orchestrator that manages producer and consumer processes.
    Optimized for DDR5-6400 performance.
    """
    
    def __init__(self, profile: Dict, output_dir: str = "temp", database_path: Optional[str] = None):
        self.profile = profile
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw_jobs"
        self.processed_dir = self.output_dir / "processed"
        
        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Database
        self.database_path = database_path
        if not self.database_path:
            profile_name = self.profile.get("profile_name", "default")
            self.database_path = f"profiles/{profile_name}/jobs.db"
            console.print(f"[yellow]⚠️ No database path provided, defaulting to: {self.database_path}[/yellow]")
        
        # Initialize components
        self.producer = FastElutaProducer(profile, str(self.raw_dir))
        self.consumer = JobDataConsumer(str(self.raw_dir), str(self.processed_dir), db_path=self.database_path, num_workers=4)
        
        # Control flags
        self.running = False
        self.producer_thread = None
        self.consumer_thread = None
        
        # Performance monitoring
        self.start_time = None
        self.stats = {
            'total_jobs_scraped': 0,
            'total_jobs_processed': 0,
            'total_jobs_saved': 0,
            'scraping_speed': 0,
            'processing_speed': 0
        }
        
        console.print(Panel.fit("🎯 PRODUCER-CONSUMER ORCHESTRATOR", style="bold blue"))
        console.print(f"[cyan]📁 Raw data: {self.raw_dir}[/cyan]")
        console.print(f"[cyan]📁 Processed: {self.processed_dir}[/cyan]")
        console.print(f"[cyan]⚡ DDR5-6400 optimized[/cyan]")
        console.print(f"[cyan]🔍 Keywords: {len(profile.get('keywords', []))}[/cyan]")
        console.print(f"[cyan]👥 Consumer workers: 4[/cyan]")
    
    def start(self) -> None:
        """Start both producer and consumer."""
        self.start_time = datetime.now()
        self.running = True
        
        console.print(f"\n[bold green]🚀 Starting producer-consumer system[/bold green]")
        console.print(f"[cyan]⏰ Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
        
        # Start consumer first (it will wait for data)
        console.print(f"\n[cyan]🔄 Starting consumer...[/cyan]")
        self.consumer_thread = threading.Thread(target=self._run_consumer)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
        
        # Give consumer time to start
        time.sleep(2)
        
        # Start producer
        console.print(f"\n[cyan]🚀 Starting producer...[/cyan]")
        self.producer_thread = threading.Thread(target=self._run_producer)
        self.producer_thread.daemon = True
        self.producer_thread.start()
        
        # Start monitoring
        self._monitor_system()
    
    def stop(self) -> None:
        """Stop both producer and consumer."""
        console.print(f"\n[yellow]🛑 Stopping producer-consumer system...[/yellow]")
        self.running = False
        
        # Stop consumer
        if self.consumer:
            self.consumer.stop_processing()
        
        # Wait for threads to finish
        if self.producer_thread:
            self.producer_thread.join(timeout=10)
        if self.consumer_thread:
            self.consumer_thread.join(timeout=10)
        
        self._print_final_stats()
    
    def _run_producer(self) -> None:
        """Run the producer in a separate thread."""
        try:
            self.producer.scrape_all_keywords()
        except Exception as e:
            console.print(f"[red]❌ Producer error: {e}[/red]")
        finally:
            console.print(f"[cyan]✅ Producer completed[/cyan]")
    
    def _run_consumer(self) -> None:
        """Run the consumer in a separate thread."""
        try:
            self.consumer.start_processing()
        except Exception as e:
            console.print(f"[red]❌ Consumer error: {e}[/red]")
        finally:
            console.print(f"[cyan]✅ Consumer completed[/cyan]")
    
    def _monitor_system(self) -> None:
        """Monitor system performance and status."""
        try:
            while self.running:
                # Update stats
                self._update_stats()
                
                # Display status
                self._display_status()
                
                # Check if producer is done
                if self.producer_thread and not self.producer_thread.is_alive():
                    console.print(f"[green]✅ Producer finished, waiting for consumer...[/green]")
                    # Wait a bit more for consumer to finish processing
                    time.sleep(30)
                    break
                
                time.sleep(5)  # Update every 5 seconds
                
        except KeyboardInterrupt:
            console.print(f"\n[yellow]🛑 Interrupted by user[/yellow]")
        finally:
            self.stop()
    
    def _update_stats(self) -> None:
        """Update performance statistics."""
        try:
            # Get producer stats
            if hasattr(self.producer, 'stats'):
                self.stats['total_jobs_scraped'] = self.producer.stats.get('jobs_scraped', 0)
                if self.producer.stats.get('start_time'):
                    duration = datetime.now() - self.producer.stats['start_time']
                    if duration.total_seconds() > 0:
                        self.stats['scraping_speed'] = (self.stats['total_jobs_scraped'] / duration.total_seconds()) * 60
            
            # Get consumer stats
            if hasattr(self.consumer, 'stats'):
                self.stats['total_jobs_processed'] = self.consumer.stats.get('jobs_processed', 0)
                self.stats['total_jobs_saved'] = self.consumer.stats.get('jobs_saved', 0)
                if self.consumer.stats.get('start_time'):
                    duration = datetime.now() - self.consumer.stats['start_time']
                    if duration.total_seconds() > 0:
                        self.stats['processing_speed'] = (self.stats['total_jobs_processed'] / duration.total_seconds()) * 60
                        
        except Exception as e:
            console.print(f"[yellow]⚠️ Stats update error: {e}[/yellow]")
    
    def _display_status(self) -> None:
        """Display current system status."""
        # Clear screen and show status
        console.clear()
        
        # Create status table
        table = Table(title="🎯 Producer-Consumer System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Jobs", style="yellow")
        table.add_column("Speed", style="blue")
        
        # Producer status
        producer_status = "🟢 Running" if self.producer_thread and self.producer_thread.is_alive() else "🔴 Stopped"
        table.add_row(
            "Producer",
            producer_status,
            f"{self.stats['total_jobs_scraped']}",
            f"{self.stats['scraping_speed']:.1f}/min"
        )
        
        # Consumer status
        consumer_status = "🟢 Running" if self.consumer_thread and self.consumer_thread.is_alive() else "🔴 Stopped"
        table.add_row(
            "Consumer",
            consumer_status,
            f"{self.stats['total_jobs_processed']}",
            f"{self.stats['processing_speed']:.1f}/min"
        )
        
        # System status
        total_saved = self.stats['total_jobs_saved']
        table.add_row(
            "System",
            "🟢 Active" if self.running else "🔴 Stopped",
            f"{total_saved} saved",
            "DDR5-6400"
        )
        
        console.print(table)
        
        # Show directories
        console.print(f"\n[cyan]📁 Raw data: {self.raw_dir}[/cyan]")
        console.print(f"[cyan]📁 Processed: {self.processed_dir}[/cyan]")
        
        # Show runtime
        if self.start_time:
            runtime = datetime.now() - self.start_time
            console.print(f"[cyan]⏱️ Runtime: {runtime}[/cyan]")
    
    def _print_final_stats(self) -> None:
        """Print final system statistics."""
        if not self.start_time:
            return
        
        duration = datetime.now() - self.start_time
        
        console.print(Panel.fit("📊 SYSTEM COMPLETE", style="bold green"))
        console.print(f"[cyan]⏱️ Total runtime: {duration}[/cyan]")
        console.print(f"[cyan]📋 Jobs scraped: {self.stats['total_jobs_scraped']}[/cyan]")
        console.print(f"[cyan]🔄 Jobs processed: {self.stats['total_jobs_processed']}[/cyan]")
        console.print(f"[cyan]💾 Jobs saved: {self.stats['total_jobs_saved']}[/cyan]")
        
        if duration.total_seconds() > 0:
            overall_speed = (self.stats['total_jobs_saved'] / duration.total_seconds()) * 60
            console.print(f"[bold green]⚡ Overall performance: {overall_speed:.1f} jobs/minute[/bold green]")
        
        console.print(f"[cyan]📁 Raw data: {self.raw_dir}[/cyan]")
        console.print(f"[cyan]📁 Processed data: {self.processed_dir}[/cyan]")

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    console.print(f"\n[yellow]🛑 Received signal {signum}, stopping...[/yellow]")
    sys.exit(0)

def main():
    """Main function for testing."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load profile
    try:
        with open("profiles/Nirajan/Nirajan.json", "r") as f:
            profile = json.load(f)
            console.print(f"[green]✅ Loaded profile with {len(profile.get('keywords', []))} keywords[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error loading profile: {e}[/red]")
        return
    
    # Define database path based on profile
    profile_name = profile.get("profile_name", "Nirajan")
    db_path = f"profiles/{profile_name}/{profile_name}.db"
    
    # Create and run orchestrator
    orchestrator = ProducerConsumerOrchestrator(profile, database_path=db_path)
    
    try:
        orchestrator.start()
    except KeyboardInterrupt:
        console.print(f"\n[yellow]🛑 Interrupted by user[/yellow]")
    finally:
        orchestrator.stop()

if __name__ == "__main__":
    main() 