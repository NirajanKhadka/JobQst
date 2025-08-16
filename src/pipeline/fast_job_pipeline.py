#!/usr/bin/env python3
"""
Simplified Job URL Collection Pipeline
Collects job URLs from Eluta.ca and saves them directly to the database.
Filters out French language jobs and Senior/Lead positions.

This pipeline only handles URL collection - no external scraping or AI processing.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Import pipeline components
from ..scrapers.unified_eluta_scraper import ElutaScraper
from ..core.job_database import get_job_db
from ..utils.profile_helpers import load_profile

console = Console()


class FastJobPipeline:
    """
    Simplified Job URL Collection Pipeline
    
    This pipeline only collects job URLs from Eluta and saves them to the database.
    No external scraping or AI processing - just clean URL collection with filtering.
    """

    def __init__(self, profile_name: str = "Nirajan", config: Optional[Dict] = None):
        self.profile_name = profile_name
        self.profile = load_profile(profile_name) or {}
        self.db = get_job_db(profile_name)
        
        # Configuration with defaults
        default_config = {
            "eluta_pages": 5,
            "eluta_jobs": 50,
            "save_to_database": True,
            "enable_duplicate_check": True,
            "timeout_seconds": 1800,  # 30 minutes total timeout
        }
        self.config = {**default_config, **(config or {})}
        
        # Initialize components
        self.eluta_scraper = None
        
        # Statistics
        self.stats = {
            "pipeline_start_time": None,
            "pipeline_end_time": None,
            "total_processing_time": 0.0,
            "urls_collected": 0,
            "jobs_saved": 0,
            "duplicates_skipped": 0,
            "french_jobs_skipped": 0,
            "senior_jobs_skipped": 0,
            "errors_encountered": 0,
            "jobs_per_second": 0.0
        }

    async def run_complete_pipeline(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Run the simplified job URL collection pipeline.
        
        Args:
            limit: Maximum number of jobs to collect (None for config default)
            
        Returns:
            List of collected job dictionaries with URLs
        """
        self.stats["pipeline_start_time"] = time.time()
        
        console.print(Panel.fit(
            "[bold blue]🚀 Simplified Job URL Collection Pipeline[/bold blue]\n"
            f"[cyan]Profile: {self.profile_name}[/cyan]\n"
            f"[cyan]Target Jobs: {limit or self.config['eluta_jobs']}[/cyan]\n"
            f"[cyan]Filtering: French & Senior/Lead positions[/cyan]",
            title="Pipeline Starting"
        ))

        try:
            # Single Phase: Eluta URL Collection with filtering
            collected_jobs = await self._collect_and_save_jobs(limit)
            
            if not collected_jobs:
                console.print("[red]❌ No job URLs collected[/red]")
                return []

            # Display final results
            self._display_pipeline_results(collected_jobs)

            return collected_jobs

        except Exception as e:
            console.print(f"[red]❌ Pipeline error: {e}[/red]")
            self.stats["errors_encountered"] += 1
            raise
        finally:
            self.stats["pipeline_end_time"] = time.time()
            if self.stats["pipeline_start_time"]:
                self.stats["total_processing_time"] = (
                    self.stats["pipeline_end_time"] - self.stats["pipeline_start_time"]
                )

    async def _collect_and_save_jobs(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Collect job URLs from Eluta and save directly to database."""
        console.print("\n[bold cyan]📋 Collecting Job URLs from Eluta[/bold cyan]")
        
        try:
            # Initialize Eluta scraper
            eluta_config = {
                "pages": self.config["eluta_pages"],
                "jobs": limit or self.config["eluta_jobs"],
                "headless": False,  # Disabled to handle popups
            }
            
            self.eluta_scraper = ElutaScraper(self.profile_name, eluta_config)
            
            # Scrape jobs (this already saves to database and filters French/Senior)
            console.print("[cyan]🕷️ Scraping and saving job URLs from Eluta...[/cyan]")
            scraped_jobs = await self.eluta_scraper.scrape_all_keywords(limit=limit or self.config["eluta_jobs"])
            
            # Update stats from scraper
            self.stats["urls_collected"] = len(scraped_jobs)
            self.stats["jobs_saved"] = self.eluta_scraper.stats.get("jobs_saved", 0)
            self.stats["duplicates_skipped"] = self.eluta_scraper.stats.get("duplicates_skipped", 0)
            self.stats["french_jobs_skipped"] = self.eluta_scraper.stats.get("french_jobs_skipped", 0)
            self.stats["senior_jobs_skipped"] = self.eluta_scraper.stats.get("senior_jobs_skipped", 0)
            
            console.print(f"[green]✅ Collection Complete: {len(scraped_jobs)} jobs collected and saved[/green]")
            
            return scraped_jobs
            
        except Exception as e:
            console.print(f"[red]❌ Collection Error: {e}[/red]")
            self.stats["errors_encountered"] += 1
            return []



    def _display_pipeline_results(self, collected_jobs: List[Dict[str, Any]]) -> None:
        """Display pipeline results."""
        console.print("\n" + "=" * 80)
        console.print(Panel.fit("🎉 JOB URL COLLECTION RESULTS", style="bold green"))

        # Calculate final statistics
        if self.stats["total_processing_time"] > 0:
            self.stats["jobs_per_second"] = self.stats["urls_collected"] / self.stats["total_processing_time"]

        # Results table
        results_table = Table(title="📊 Collection Performance")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Count", style="yellow")

        results_table.add_row("URLs Collected", str(self.stats["urls_collected"]))
        results_table.add_row("Jobs Saved to Database", str(self.stats["jobs_saved"]))
        results_table.add_row("Duplicates Skipped", str(self.stats["duplicates_skipped"]))
        results_table.add_row("French Jobs Skipped", str(self.stats["french_jobs_skipped"]))
        results_table.add_row("Senior/Lead Jobs Skipped", str(self.stats["senior_jobs_skipped"]))
        results_table.add_row("Processing Time", f"{self.stats['total_processing_time']:.1f}s")
        results_table.add_row("Jobs per Second", f"{self.stats['jobs_per_second']:.1f}")

        console.print(results_table)

        # Summary information
        console.print(f"\n[bold blue]📋 Collection Summary:[/bold blue]")
        console.print(f"[green]✅ Jobs Saved to Database: {self.stats['jobs_saved']}[/green]")
        console.print(f"[green]✅ Duplicates Skipped: {self.stats['duplicates_skipped']}[/green]")
        console.print(f"[green]✅ French Jobs Filtered: {self.stats['french_jobs_skipped']}[/green]")
        console.print(f"[green]✅ Senior/Lead Jobs Filtered: {self.stats['senior_jobs_skipped']}[/green]")
        if self.stats["errors_encountered"] > 0:
            console.print(f"[yellow]⚠️ Errors Encountered: {self.stats['errors_encountered']}[/yellow]")

        console.print(f"\n[bold green]🎯 Ready for Processing:[/bold green]")
        console.print(f"[green]📋 {self.stats['jobs_saved']} job URLs saved and ready for external processing[/green]")

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return self.stats.copy()


# Convenience functions
def get_fast_job_pipeline(profile_name: str = "Nirajan", **config) -> FastJobPipeline:
    """Get configured fast job pipeline instance."""
    return FastJobPipeline(profile_name, config)


async def run_fast_pipeline(profile_name: str = "Nirajan", limit: int = 50, **config) -> List[Dict[str, Any]]:
    """Run simplified job URL collection pipeline."""
    pipeline = FastJobPipeline(profile_name, config)
    return await pipeline.run_complete_pipeline(limit)


# CLI test function
async def test_fast_pipeline():
    """Test the simplified pipeline with a small job set."""
    console.print("[bold blue]🧪 Testing Simplified Job Collection Pipeline[/bold blue]")
    
    pipeline = FastJobPipeline("test_profile", {
        "eluta_jobs": 10
    })
    
    results = await pipeline.run_complete_pipeline(10)
    console.print(f"[green]✅ Test complete: {len(results)} job URLs collected[/green]")


if __name__ == "__main__":
    asyncio.run(test_fast_pipeline())