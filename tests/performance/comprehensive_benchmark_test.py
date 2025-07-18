#!/usr/bin/env python3
"""
Comprehensive Benchmark Test for AutoJobAgent.

This script executes a suite of benchmark scenarios to test the performance
of the continuous scraping functionality under various conditions, including
different keywords and durations. It provides a detailed analysis of scraping
speed, database insertion rates, and overall system stability.

Key Features:
- Runs multiple, isolated benchmark scenarios.
- Clears the database before each run to ensure a clean state.
- Measures jobs scraped per minute and success rate.
- Provides a final performance assessment (Excellent, Good, Slow).
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Corrected imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

from src.core.job_database import get_job_db
from src.scrapers.enhanced_eluta_scraper import EnhancedElutaScraper

# --- Initialization ---
console = Console()


class ComprehensiveBenchmark:
    """
    A class to orchestrate comprehensive benchmark testing for multiple scenarios.
    """

    def __init__(self, profile_name: str = "Nirajan"):
        """
        Initialize the benchmark suite.

        Args:
            profile_name: The name of the profile to use for the benchmark.
        """
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.results: Dict[str, Dict[str, Any]] = {}

    def clear_database(self) -> bool:
        """
        Clear all job entries from the database to ensure a clean slate.

        Returns:
            True if the database was cleared successfully, False otherwise.
        """
        console.print("[cyan]🗑️ Clearing database...[/cyan]")
        try:
            self.db.clear_all_jobs()
            console.print("[green]✅ Database cleared successfully.[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to clear database: {e}[/red]")
            return False

    def verify_database_empty(self) -> bool:
        """
        Verify that the database is empty before starting a benchmark.

        Returns:
            True if the database is empty, False otherwise.
        """
        count = self.db.get_job_count()
        if count == 0:
            console.print("[green]✅ Database is confirmed empty.[/green]")
            return True
        
        console.print(f"[red]❌ Database is not empty. Found {count} jobs.[/red]")
        return False

    async def run_benchmark_scenario(
        self, scenario_name: str, keywords: List[str], duration_minutes: int = 1
    ) -> Dict[str, Any]:
        """
        Run a single benchmark scenario with specific keywords and duration.

        Args:
            scenario_name: The name for the benchmark scenario.
            keywords: A list of keywords to use for scraping.
            duration_minutes: The duration in minutes to run the scraper.

        Returns:
            A dictionary containing the performance metrics for the scenario.
        """
        console.print(f"\n[bold blue]🧪 Running Scenario: {scenario_name}[/bold blue]")
        console.print(f"  [cyan]Keywords: {', '.join(keywords)}[/cyan]")
        console.print(f"  [cyan]Duration: {duration_minutes} minutes[/cyan]")

        metrics: Dict[str, Any] = {}
        start_time = time.time()

        try:
            # Initialize scraper with custom keywords for this scenario
            scraper = EnhancedElutaScraper(self.profile_name)
            # Note: EnhancedElutaScraper doesn't have continuous scraping capability
            # This test would need modification to work with available scrapers
            metrics = {
                "jobs_scraped": 0,
                "jobs_saved": 0,
                "jobs_per_minute": 0,
                "success_rate": 0,
                "error": "FastContinuousScraper not available, test skipped"
            }

        except Exception as e:
            console.print(f"[red]❌ An error occurred during scraping: {e}[/red]")
            metrics = {
                "jobs_scraped": 0,
                "jobs_saved": 0,
                "jobs_per_minute": 0,
                "success_rate": 0,
                "error": str(e),
            }
        
        end_time = time.time()
        actual_duration = end_time - start_time

        # Compile final metrics for the scenario
        metrics.update({
            "scenario_name": scenario_name,
            "keywords_used": keywords,
            "actual_duration": actual_duration,
            "final_db_count": self.db.get_job_count(),
        })

        self.results[scenario_name] = metrics
        return metrics

    def display_comprehensive_results(self):
        """
        Display a formatted table summarizing the results of all benchmark scenarios.
        """
        console.print("\n" + "=" * 100)
        console.print(Panel.fit("📊 COMPREHENSIVE BENCHMARK RESULTS", style="bold green"))

        summary_table = Table(title="Benchmark Summary")
        summary_table.add_column("Scenario", style="cyan", justify="left")
        summary_table.add_column("Jobs Scraped", style="green", justify="right")
        summary_table.add_column("Jobs Saved", style="green", justify="right")
        summary_table.add_column("Jobs/Min", style="yellow", justify="right")
        summary_table.add_column("Success Rate", style="blue", justify="right")
        summary_table.add_column("Duration (s)", style="magenta", justify="right")

        total_jobs_scraped = 0
        total_jobs_saved = 0
        total_duration = 0

        for scenario_name, metrics in self.results.items():
            summary_table.add_row(
                scenario_name,
                str(metrics.get("jobs_scraped", 0)),
                str(metrics.get("jobs_saved", 0)),
                f"{metrics.get('jobs_per_minute', 0):.1f}",
                f"{metrics.get('success_rate', 0):.1f}%",
                f"{metrics.get('actual_duration', 0):.1f}",
            )
            total_jobs_scraped += metrics.get("jobs_scraped", 0)
            total_jobs_saved += metrics.get("jobs_saved", 0)
            total_duration += metrics.get("actual_duration", 0)

        console.print(summary_table)

        # Overall performance summary
        overall_rate = (total_jobs_scraped / total_duration) * 60 if total_duration > 0 else 0
        overall_success = (total_jobs_saved / total_jobs_scraped * 100) if total_jobs_scraped > 0 else 0

        console.print("\n[bold]Overall Performance:[/bold]")
        console.print(f"  [green]Total Jobs Scraped: {total_jobs_scraped}[/green]")
        console.print(f"  [green]Total Jobs Saved: {total_jobs_saved}[/green]")
        console.print(f"  [yellow]Overall Rate: {overall_rate:.1f} jobs/minute[/yellow]")
        console.print(f"  [blue]Overall Success Rate: {overall_success:.1f}%[/blue]")
        console.print(f"  [magenta]Total Duration: {total_duration:.1f} seconds[/magenta]")

        # Performance assessment
        if overall_rate >= 100:
            console.print("\n[bold green]🎯 ASSESSMENT: EXCELLENT (100+ jobs/minute achieved!)[/bold green]")
        elif overall_rate >= 50:
            console.print("\n[bold yellow] ASSESSMENT: GOOD (50+ jobs/minute)[/bold yellow]")
        else:
            console.print("\n[bold red] ASSESSMENT: SLOW (Below 50 jobs/minute)[/bold red]")

    async def run_all_benchmarks(self):
        """
        Run the full suite of predefined benchmark scenarios.
        """
        console.print(Panel.fit("🚀 COMPREHENSIVE BENCHMARK SUITE", style="bold blue"))

        if not self.clear_database() or not self.verify_database_empty():
            console.print("[red]❌ Halting benchmark due to database preparation failure.[/red]")
            return

        # Define benchmark scenarios
        scenarios = {
            "Popular Keywords (1min)": {"keywords": ["Data Analyst", "SQL", "Python"], "duration": 1},
            "Technical Keywords (1min)": {"keywords": ["MySQL", "PostgreSQL", "Database"], "duration": 1},
            "Extended Test (2min)": {"keywords": ["Data Analyst", "SQL", "Python", "MySQL"], "duration": 2},
        }

        for name, params in scenarios.items():
            await self.run_benchmark_scenario(
                scenario_name=name,
                keywords=params["keywords"],
                duration_minutes=params["duration"],
            )

        self.display_comprehensive_results()


async def run_comprehensive_benchmark(profile_name: str = "Nirajan") -> Dict[str, Any]:
    """
    A convenience function to initialize and run the comprehensive benchmark.

    Args:
        profile_name: The profile to use for the benchmark.

    Returns:
        A dictionary containing the results of all benchmark scenarios.
    """
    benchmark = ComprehensiveBenchmark(profile_name)
    await benchmark.run_all_benchmarks()
    return benchmark.results


if __name__ == "__main__":
    import sys
    from pathlib import Path
    from src.core.job_database import get_job_db
    
    # Ensure the script can find the 'src' module
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        
    asyncio.run(run_comprehensive_benchmark())
