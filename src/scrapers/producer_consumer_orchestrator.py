#!/usr/bin/env python3
"""
Producer-Consumer Orchestrator - Manages the scraper (Producer) and the processor (Consumer).
"""

import time
import threading
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

# Import our producer and the new processor
from src.scrapers.fast_eluta_producer import FastElutaProducer
from src.utils.job_data_consumer import JobProcessor

console = Console()

class ProducerConsumerOrchestrator:
    """
    Orchestrator that manages producer and consumer processes.
    """
    
    def __init__(self, profile: Dict, database_path: Optional[str] = None):
        self.profile = profile
        
        # Database
        self.database_path = database_path
        if not self.database_path:
            profile_name = self.profile.get("profile_name", "default")
            self.database_path = f"profiles/{profile_name}/jobs.db"
            console.print(f"[yellow]⚠️ No database path provided, defaulting to: {self.database_path}[/yellow]")
        
        # Initialize components
        self.processor = JobProcessor(db_path=self.database_path, num_workers=4)
        self.producer = FastElutaProducer(profile, self.processor) # Pass processor to producer
        
        # Control flags
        self.running = False
        self.producer_thread = None
        
        # Performance monitoring
        self.start_time = None
        
        console.print(Panel.fit("🎯 PRODUCER-PROCESSOR ORCHESTRATOR", style="bold blue"))
        console.print(f"📊 Database: {self.database_path}")
        console.print(f"⚡ Processor Workers: 4")
        console.print(f"🔍 Keywords: {len(profile.get('keywords', []))}")
    
    def start(self) -> None:
        """Start both producer and processor."""
        self.start_time = datetime.now()
        self.running = True
        
        console.print(f"\n[bold green]🚀 Starting scraper and processor system[/bold green]")
        
        # Start producer in a background thread
        console.print(f"\n[cyan]🚀 Starting scraper (producer)...[/cyan]")
        self.producer_thread = threading.Thread(target=self._run_producer)
        self.producer_thread.daemon = True
        self.producer_thread.start()
        
        # Wait for the producer to finish
        self.producer_thread.join()
        
        # Once the producer is done, all jobs have been submitted.
        # Now, wait for the processor to finish handling all submitted jobs.
        console.print(f"\n[green]✅ Scraping complete. Waiting for all jobs to be processed...[/green]")
        self.processor.wait_for_completion()
        
        self.stop()
    
    def stop(self) -> None:
        """Stop the system and print stats."""
        if not self.running:
            return
            
        console.print(f"\n[yellow]🛑 System finished.[/yellow]")
        self.running = False
        self._print_final_stats()
    
    def _run_producer(self) -> None:
        """Run the producer in a separate thread."""
        try:
            self.producer.scrape_all_keywords()
        except Exception as e:
            console.print(f"[red]❌ Producer error: {e}[/red]")
        finally:
            console.print(f"[cyan]✅ Producer has finished scraping.[/cyan]")
    
    def _print_final_stats(self) -> None:
        """Print final system statistics."""
        if not self.start_time:
            return
            
        end_time = datetime.now()
        duration = end_time - self.start_time
        console.print(f"\n--- Orchestrator Final Stats ---")
        console.print(f"Total Runtime: {duration}")
        console.print(f"---------------------------------")

def main():
    """Main function for testing the orchestrator."""
    console.print("--- ORCHESTRATOR MAIN SCRIPT STARTED ---")
    console.print(Panel("Running Producer-Consumer Orchestrator Standalone Test", style="bold yellow"))
    
    # Dummy profile for testing
    test_profile = {
        "profile_name": "test_profile",
        "keywords": ["software engineer", "data analyst"],
        "pages_to_scrape": 1 # Keep it small for a quick test
    }
    
    orchestrator = ProducerConsumerOrchestrator(profile=test_profile, database_path="temp/orchestrator_test.db")
    
    try:
        console.print("--- CLEANING UP OLD DATABASE ---")
        # Cleanup old test db
        if os.path.exists("temp/orchestrator_test.db"):
            os.remove("temp/orchestrator_test.db")
        
        console.print("--- STARTING ORCHESTRATOR ---")
        orchestrator.start()
    except KeyboardInterrupt:
        orchestrator.stop()
    finally:
        console.print("\nStandalone test finished.")

if __name__ == "__main__":
    main() 