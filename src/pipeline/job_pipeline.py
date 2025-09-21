#!/usr/bin/env python3
"""
Improved Fast Job Pipeline with JobSpy Integration
Combines JobSpy's proven scraping capabilities with AutoJobAgent's processing pipeline.

Features:
- JobSpy integration for 104-106 job discovery with 83-87% success rate
- Existing Eluta scraper compatibility
- External job description fetching
- GPU-accelerated processing with OpenHermes 2.5
- Automated fallback and error recovery
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
from ..scrapers.jobspy_scraper_v2 import JobSpyImprovedScraper, JOBSPY_AVAILABLE
from ..scrapers.external_job_scraper import ExternalJobDescriptionScraper
from ..optimization.integrated_processor import create_optimized_processor
from ..core.job_database import get_job_db
from ..utils.profile_helpers import load_profile
from ..config.jobspy_integration_config import (
    JobSpyIntegrationConfig, 
    get_profile_optimized_config,
    JOBSPY_CONFIG_PRESETS
)

console = Console()


class JobPipeline:
    """
    Improved Fast Job Pipeline with JobSpy Integration
    
    Combines the best of both worlds:
    - JobSpy's proven job discovery (104-106 jobs, 83-87% success rate)
    - AutoJobAgent's Improved processing (OpenHermes 2.5, GPU acceleration)
    - Automated fallback and error recovery
    """

    def __init__(self, profile_name: str = "Nirajan", config: Optional[Dict] = None):
        """Initialize the Enhanced Fast Job Pipeline.
        
        Args:
            profile_name: Name of the user profile to use
            config: Optional configuration overrides
        """
        self.profile_name = profile_name
        self.profile = load_profile(profile_name) or {}
        self.db = get_job_db(profile_name)
        
        # Configuration with defaults - following development standards
        default_config = {
            # JobSpy settings
            "enable_jobspy": True,
            "jobspy_priority": "high",  # high, medium, low
            # fast, comprehensive, quality, mississauga, toronto, remote
            "jobspy_preset": "quality",
            "jobspy_max_jobs": 100,
            # Job age filter (hours): 24=daily, 168=weekly, 336=biweekly
            "hours_old": 168,  # Changed to weekly for better performance
            
            # Existing scraper settings
            "enable_eluta": False,  # Disabled - JobSpy is 40x faster
            "eluta_pages": 3,
            "eluta_jobs": 50,
            
            # External scraping settings - DISABLED: JobSpy already gets full descriptions
            "enable_external_scraping": False,  # JobSpy provides descriptions
            "external_workers": 6,
            
            # Processing settings
            "enable_processing": True,
            "processing_method": "auto",  # auto, gpu, hybrid, rule_based
            "cpu_workers": 10,
            
            # General settings
            "save_to_database": True,
            "enable_duplicate_check": True,
            "timeout_seconds": 1800,  # 30 minutes total timeout
            "fallback_enabled": True
        }
        self.config = {**default_config, **(config or {})}
        
        # Initialize JobSpy integration config
        self._setup_jobspy_config()
        
        # Initialize components
        self.jobspy_scraper = None
        self.eluta_scraper = None
        self.external_scraper = None
        self.processor = None
        
        # Statistics
        self.stats = {
            "pipeline_start_time": None,
            "pipeline_end_time": None,
            "total_processing_time": 0.0,
            
            # JobSpy stats
            "jobspy_jobs_found": 0,
            "jobspy_success_rate": 0.0,
            "jobspy_processing_time": 0.0,
            
            # Eluta stats
            "eluta_jobs_found": 0,
            "eluta_processing_time": 0.0,
            
            # External scraping stats
            "descriptions_fetched": 0,
            "external_scraping_time": 0.0,
            
            # Processing stats
            "jobs_processed": 0,
            "jobs_ready_to_apply": 0,
            "processing_time": 0.0,
            "processing_method_used": "unknown",
            
            # Overall stats
            "total_jobs_found": 0,
            "jobs_saved": 0,
            "duplicates_skipped": 0,
            "errors_encountered": 0,
            "jobs_per_second": 0.0,
            "phases_completed": []
        }

    def _setup_jobspy_config(self):
        """Setup JobSpy integration configuration."""
        if not self.config["enable_jobspy"]:
            self.jobspy_config = None
            return
        
        # Use preset if specified
        preset_name = self.config.get("jobspy_preset", "quality")
        if preset_name in JOBSPY_CONFIG_PRESETS:
            self.jobspy_config = JOBSPY_CONFIG_PRESETS[preset_name]()
        else:
            # Generate profile-optimized config
            self.jobspy_config = get_profile_optimized_config(self.profile)
        
        # Override with any explicit config
        if "jobspy_max_jobs" in self.config:
            self.jobspy_config.jobspy_max_jobs = self.config["jobspy_max_jobs"]
            
        # Override sites if specified in config
        if "jobspy_sites" in self.config and self.config["jobspy_sites"]:
            self.jobspy_config.jobspy_sites = self.config["jobspy_sites"]

    def _get_filter_description(self) -> str:
        """Get human-readable description of current time filter."""
        hours = self.config.get("hours_old", 336)
        if hours <= 24:
            return "last 24 hours (daily)"
        elif hours <= 168:
            return f"last {hours // 24} days"
        else:
            return f"last {hours // 24} days"

    def set_daily_filter(self) -> None:
        """Set the pipeline to only scrape jobs from the last 24 hours."""
        self.config["hours_old"] = 24
        console.print(
            "[yellow]📅 Daily filter enabled: "
            "jobs from last 24 hours only[/yellow]"
        )

    def set_weekly_filter(self) -> None:
        """Set the pipeline to only scrape jobs from the last week."""
        self.config["hours_old"] = 168
        console.print(
            "[yellow]📅 Weekly filter enabled: "
            "jobs from last 7 days only[/yellow]"
        )

    async def run_complete_pipeline(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Run the enhanced job pipeline with JobSpy integration.
        
        Phases:
        1. Job Discovery (JobSpy + Eluta)
        2. External Description Fetching
        3. AI Processing with OpenHermes 2.5
        
        Args:
            limit: Maximum number of jobs to process (None for config default)
            
        Returns:
            List of processed job dictionaries
        """
        self.stats["pipeline_start_time"] = time.time()
        
        console.print(Panel.fit(
            "[bold blue]🚀 Enhanced Fast Job Pipeline"
            " with JobSpy Integration[/bold blue]\n"
            f"[cyan]Profile: {self.profile_name}[/cyan]\n"
            f"[cyan]JobSpy: "
            f"{'✅ Enabled' if self.config['enable_jobspy'] else '❌ Disabled'}"
            f"[/cyan]\n"
            f"[cyan]Eluta: "
            f"{'✅ Enabled' if self.config['enable_eluta'] else '❌ Disabled'}"
            f"[/cyan]\n"
            f"[cyan]External Scraping: "
            f"{'✅ Enabled' if self.config['enable_external_scraping'] else '❌ Disabled'}"
            f"[/cyan]\n"
            f"[cyan]AI Processing: "
            f"{'✅ Enabled' if self.config['enable_processing'] else '❌ Disabled'}"
            f"[/cyan]\n"
            f"[cyan]Job Age Filter: {self._get_filter_description()}[/cyan]\n"
            f"[cyan]Target Jobs: {limit or 'Config Default'}[/cyan]",
            title="Enhanced Pipeline Starting"
        ))

        try:
            # Phase 1: Job Discovery
            discovered_jobs = await self._phase1_job_discovery(limit)
            if not discovered_jobs:
                console.print("[red]❌ No jobs discovered in Phase 1[/red]")
                return []

            # Phase 2: External Description Fetching (if enabled)
            Improved_jobs = discovered_jobs
            if self.config["enable_external_scraping"]:
                Improved_jobs = await self._phase2_fetch_descriptions(discovered_jobs)

            # Phase 3: AI Processing (if enabled)
            processed_jobs = Improved_jobs
            if self.config["enable_processing"]:
                processed_jobs = await self._phase3_process_jobs(Improved_jobs)

            # Display final results
            self._display_pipeline_results(processed_jobs)

            return processed_jobs

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

    async def _phase1_job_discovery(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Phase 1: Job Discovery using JobSpy and/or Eluta."""
        console.print("\n[bold cyan]📋 Phase 1: Job Discovery[/bold cyan]")
        
        all_jobs = []
        
        # JobSpy Discovery (if enabled and available)
        if self.config["enable_jobspy"] and JOBSPY_AVAILABLE:
            jobspy_jobs = await self._run_jobspy_discovery(limit)
            if jobspy_jobs:
                all_jobs.extend(jobspy_jobs)
                self.stats["phases_completed"].append("jobspy_discovery")
        
        # Eluta Discovery (if enabled and needed)
        # Only run Eluta if:
        # 1. Eluta is explicitly enabled AND
        # 2. Either no JobSpy jobs found OR combine_with_existing_scrapers is True AND JobSpy didn't find enough jobs
        should_run_eluta = (
            self.config["enable_eluta"] and 
            (
                (not all_jobs) or  # No JobSpy jobs found, fallback to Eluta
                (self.config.get("enable_jobspy", False) and 
                 self.jobspy_config and 
                 self.jobspy_config.combine_with_existing_scrapers and 
                 len(all_jobs) < (limit or self.config.get("jobspy_max_jobs", 100)) // 2)  # JobSpy found few jobs, supplement with Eluta
            )
        )
        
        if should_run_eluta:
            eluta_jobs = await self._run_eluta_discovery(limit)
            if eluta_jobs:
                all_jobs.extend(eluta_jobs)
                self.stats["phases_completed"].append("eluta_discovery")
        
        # Deduplicate if we have jobs from multiple sources
        if len(all_jobs) > 0 and self.config["enable_duplicate_check"]:
            all_jobs = self._deduplicate_jobs(all_jobs)
        
        self.stats["total_jobs_found"] = len(all_jobs)
        console.print(f"[green]✅ Phase 1 Complete: {len(all_jobs)} unique jobs discovered[/green]")
        
        return all_jobs

    async def _run_jobspy_discovery(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Run JobSpy job discovery."""
        console.print("[cyan]🕷️ Running JobSpy Improved Discovery...[/cyan]")
        
        try:
            start_time = time.time()
            
            # Initialize JobSpy scraper with config
            jobspy_config_dict = {
                "locations": self.jobspy_config.jobspy_locations,
                "search_terms": self.jobspy_config.jobspy_search_terms,
                "sites": self.jobspy_config.jobspy_sites,
                "max_total_jobs": limit or self.jobspy_config.jobspy_max_jobs
            }
            
            from ..scrapers.jobspy_scraper_v2 import JobSpyConfig
            jobspy_scraper_config = JobSpyConfig(
                locations=jobspy_config_dict["locations"],
                search_terms=jobspy_config_dict["search_terms"],
                sites=jobspy_config_dict["sites"],
                max_total_jobs=jobspy_config_dict["max_total_jobs"],
                hours_old=int(self.config.get("hours_old", 336))
            )
            
            self.jobspy_scraper = JobSpyImprovedScraper(self.profile_name, jobspy_scraper_config)
            
            # Run JobSpy scraping
            jobs = await self.jobspy_scraper.scrape_jobs_Improved(limit or self.jobspy_config.jobspy_max_jobs)
            
            # Update stats
            self.stats["jobspy_processing_time"] = time.time() - start_time
            self.stats["jobspy_jobs_found"] = len(jobs)
            
            if hasattr(self.jobspy_scraper, 'get_stats'):
                jobspy_stats = self.jobspy_scraper.get_stats()
                self.stats["jobspy_success_rate"] = jobspy_stats.get("success_rate", 0.0)
            
            console.print(f"[green]✅ JobSpy Discovery: {len(jobs)} jobs found[/green]")
            return jobs
            
        except Exception as e:
            console.print(f"[red]❌ JobSpy Discovery Failed: {e}[/red]")
            self.stats["errors_encountered"] += 1
            
            if self.config["fallback_enabled"]:
                console.print("[yellow]🔄 Falling back to Eluta scraper...[/yellow]")
                return []
            else:
                raise

    async def _run_eluta_discovery(self, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Run Eluta job discovery."""
        console.print("[cyan]🕷️ Running Eluta Discovery...[/cyan]")
        
        try:
            start_time = time.time()
            
            # Initialize Eluta scraper
            eluta_config = {
                "pages": self.config["eluta_pages"],
                "jobs": limit or self.config["eluta_jobs"],
                "headless": False,
            }
            
            self.eluta_scraper = ElutaScraper(self.profile_name, eluta_config)
            
            # Run Eluta scraping
            jobs = await self.eluta_scraper.scrape_all_keywords(limit=limit or self.config["eluta_jobs"])
            
            # Update stats
            self.stats["eluta_processing_time"] = time.time() - start_time
            self.stats["eluta_jobs_found"] = len(jobs)
            
            console.print(f"[green]✅ Eluta Discovery: {len(jobs)} jobs found[/green]")
            return jobs
            
        except Exception as e:
            console.print(f"[red]❌ Eluta Discovery Failed: {e}[/red]")
            self.stats["errors_encountered"] += 1
            return []

    async def _phase2_fetch_descriptions(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Phase 2: Fetch detailed job descriptions."""
        console.print("\n[bold cyan]🌐 Phase 2: Fetching Job Descriptions[/bold cyan]")
        
        if not jobs:
            return jobs
        
        # Smart check: Skip if JobSpy already provided descriptions
        jobs_with_descriptions = sum(
            1 for job in jobs
            if job.get('description') and len(job.get('description', '')) > 100
        )
        description_coverage = (
            jobs_with_descriptions / len(jobs) if jobs else 0
        )
        
        if description_coverage > 0.8:  # If 80%+ already have descriptions
            console.print(
                f"[green]✅ Skipping external scraping: "
                f"{jobs_with_descriptions}/{len(jobs)} jobs already have "
                f"descriptions ({description_coverage:.1%})[/green]"
            )
            # Mark all as description_fetched since they came from JobSpy
            for job in jobs:
                job['description_fetched'] = bool(job.get('description'))
            
            self.stats["external_scraping_time"] = 0.0
            self.stats["descriptions_fetched"] = jobs_with_descriptions
            self.stats["phases_completed"].append("external_scraping_skipped")
            return jobs
        
        if not self.config.get("enable_external_scraping", True):
            console.print(
                "[yellow]⚠️ External scraping disabled in config[/yellow]"
            )
            for job in jobs:
                job['description_fetched'] = bool(job.get('description'))
            return jobs
        
        try:
            start_time = time.time()
            
            # Initialize external scraper
            self.external_scraper = ExternalJobDescriptionScraper(
                num_workers=self.config["external_workers"]
            )
            
            # Extract URLs from jobs that don't have descriptions
            jobs_needing_descriptions = [
                job for job in jobs
                if not job.get('description') or
                len(job.get('description', '')) < 100
            ]
            job_urls = [
                job.get('url', '') for job in jobs_needing_descriptions
                if job.get('url')
            ]
            
            if not job_urls:
                console.print(
                    "[yellow]⚠️ No job URLs found for description "
                    "fetching[/yellow]"
                )
                return jobs
            
            console.print(
                f"[cyan]📋 Fetching descriptions for {len(job_urls)} jobs "
                f"with {self.config['external_workers']} workers...[/cyan]"
            )
            
            # Fetch descriptions
            scraped_jobs = await self.external_scraper.\
                scrape_external_jobs_parallel(job_urls)
            
            # Merge descriptions back into jobs
            Improved_jobs = []
            for i, job in enumerate(jobs):
                if i < len(scraped_jobs) and scraped_jobs[i].get('description'):
                    job['description'] = scraped_jobs[i]['description']
                    job['description_fetched'] = True
                else:
                    job['description_fetched'] = bool(job.get('description'))
                Improved_jobs.append(job)
            
            # Update stats
            self.stats["external_scraping_time"] = time.time() - start_time
            self.stats["descriptions_fetched"] = len([j for j in Improved_jobs if j.get('description_fetched')])
            self.stats["phases_completed"].append("external_scraping")
            
            console.print(f"[green]✅ Phase 2 Complete: {self.stats['descriptions_fetched']}/{len(jobs)} descriptions fetched[/green]")
            
            return Improved_jobs
            
        except Exception as e:
            console.print(f"[red]❌ Phase 2 Failed: {e}[/red]")
            self.stats["errors_encountered"] += 1
            return jobs  # Return original jobs without descriptions

    async def _phase3_process_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Phase 3: Process jobs with AI analysis."""
        console.print("\n[bold cyan]🧠 Phase 3: AI Processing with OpenHermes 2.5[/bold cyan]")
        
        if not jobs:
            return jobs
        
        try:
            start_time = time.time()
            
            # Initialize optimized two-stage processor with batch processing
            self.processor = create_optimized_processor(
                self.profile, 
                cpu_workers=self.config["cpu_workers"]
            )
            
            console.print(f"[cyan]🔬 Processing {len(jobs)} jobs with {self.config['processing_method']} method...[/cyan]")
            
            # Process jobs
            results = await self.processor.process_jobs(jobs)
            
            # Convert results to job dictionaries and save to database
            processed_jobs = []
            ready_to_apply_count = 0
            
            for result in results:
                # Update job data with analysis results
                job_data = result.job_data.copy()
                job_data.update({
                    'compatibility_score': result.final_compatibility,
                    'skills_found': result.final_skills,
                    'recommendation': result.recommendation,
                    'processing_method': self.config['processing_method'],
                    'stages_completed': result.stages_completed,
                    'analysis_status': 'completed',
                    'processed_at': datetime.now()
                })
                
                # Update status based on recommendation
                if result.recommendation == "apply":
                    job_data['status'] = "ready_to_apply"
                    ready_to_apply_count += 1
                elif result.recommendation == "review":
                    job_data['status'] = "needs_review"
                else:
                    job_data['status'] = "filtered_out"
                
                processed_jobs.append(job_data)
                
                # Save to database
                if self.config["save_to_database"]:
                    try:
                        if 'id' in job_data:
                            # Update existing job
                            self.db.update_job_analysis(job_data['id'], {
                                'compatibility_score': result.final_compatibility,
                                'skills_found': result.final_skills,
                                'recommendation': result.recommendation,
                                'processing_method': self.config['processing_method'],
                                'analysis_status': 'completed'
                            })
                            self.db.update_job_status(job_data['id'], job_data['status'])
                        else:
                            # Add new job
                            job_id = self.db.add_job(job_data)
                            if job_id:
                                job_data['id'] = job_id
                                self.stats["jobs_saved"] += 1
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Failed to save job to database: {e}[/yellow]")
            
            # Update stats
            self.stats["processing_time"] = time.time() - start_time
            self.stats["jobs_processed"] = len(processed_jobs)
            self.stats["jobs_ready_to_apply"] = ready_to_apply_count
            self.stats["processing_method_used"] = self.config.get("processing_method", "auto")
            self.stats["phases_completed"].append("ai_processing")
            
            console.print(f"[green]✅ Phase 3 Complete: {len(processed_jobs)} jobs processed, {ready_to_apply_count} ready to apply[/green]")
            
            return processed_jobs
            
        except Exception as e:
            console.print(f"[red]❌ Phase 3 Failed: {e}[/red]")
            self.stats["errors_encountered"] += 1
            return jobs  # Return original jobs without processing

    def _deduplicate_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate jobs based on URL or title+company."""
        if not jobs:
            return jobs
        
        seen_urls = set()
        seen_combinations = set()
        unique_jobs = []
        duplicates_count = 0
        
        for job in jobs:
            # Check URL first
            url = job.get('url', '')
            if url and url in seen_urls:
                duplicates_count += 1
                continue
            
            # Check title+company combination
            title = job.get('title', '').lower().strip()
            company = job.get('company', '').lower().strip()
            combination = f"{title}|{company}"
            
            if combination in seen_combinations:
                duplicates_count += 1
                continue
            
            # Add to seen sets and unique jobs
            if url:
                seen_urls.add(url)
            seen_combinations.add(combination)
            unique_jobs.append(job)
        
        self.stats["duplicates_skipped"] = duplicates_count
        
        if duplicates_count > 0:
            console.print(f"[yellow]🔄 Removed {duplicates_count} duplicate jobs[/yellow]")
        
        return unique_jobs

    def _display_pipeline_results(self, processed_jobs: List[Dict[str, Any]]) -> None:
        """Display comprehensive pipeline results."""
        console.print("\n" + "=" * 80)
        console.print(Panel.fit("🎉 Improved PIPELINE RESULTS", style="bold green"))

        # Calculate final statistics
        if self.stats["total_processing_time"] > 0:
            self.stats["jobs_per_second"] = self.stats["total_jobs_found"] / self.stats["total_processing_time"]

        # Results table
        results_table = Table(title="📊 Pipeline Performance")
        results_table.add_column("Phase", style="cyan")
        results_table.add_column("Jobs", style="yellow")
        results_table.add_column("Time", style="green")
        results_table.add_column("Status", style="blue")

        # Phase results
        if "jobspy_discovery" in self.stats["phases_completed"]:
            results_table.add_row("JobSpy Discovery", str(self.stats["jobspy_jobs_found"]), 
                                f"{self.stats['jobspy_processing_time']:.1f}s", "✅ Complete")
        
        if "eluta_discovery" in self.stats["phases_completed"]:
            results_table.add_row("Eluta Discovery", str(self.stats["eluta_jobs_found"]), 
                                f"{self.stats['eluta_processing_time']:.1f}s", "✅ Complete")
        
        if "external_scraping" in self.stats["phases_completed"]:
            results_table.add_row("Description Fetching", str(self.stats["descriptions_fetched"]), 
                                f"{self.stats['external_scraping_time']:.1f}s", "✅ Complete")
        
        if "ai_processing" in self.stats["phases_completed"]:
            results_table.add_row("AI Processing", str(self.stats["jobs_processed"]), 
                                f"{self.stats['processing_time']:.1f}s", "✅ Complete")

        results_table.add_row("TOTAL", str(self.stats["total_jobs_found"]), 
                            f"{self.stats['total_processing_time']:.1f}s", "🎯 Pipeline")

        console.print(results_table)

        # Summary information
        console.print(f"\n[bold blue]📋 Improved Pipeline Summary:[/bold blue]")
        
        if self.stats["jobspy_jobs_found"] > 0:
            console.print(f"[green]🚀 JobSpy: {self.stats['jobspy_jobs_found']} jobs ({self.stats['jobspy_success_rate']:.1f}% success rate)[/green]")
        
        if self.stats["eluta_jobs_found"] > 0:
            console.print(f"[green]🕷️ Eluta: {self.stats['eluta_jobs_found']} jobs[/green]")
        
        if self.stats["descriptions_fetched"] > 0:
            console.print(f"[green]📄 Descriptions: {self.stats['descriptions_fetched']} fetched[/green]")
        
        if self.stats["jobs_processed"] > 0:
            console.print(f"[green]🧠 AI Processing: {self.stats['jobs_processed']} jobs analyzed[/green]")
            console.print(f"[green]🎯 Ready to Apply: {self.stats['jobs_ready_to_apply']} jobs[/green]")
        
        if self.stats["duplicates_skipped"] > 0:
            console.print(f"[yellow]🔄 Duplicates Skipped: {self.stats['duplicates_skipped']}[/yellow]")
        
        if self.stats["errors_encountered"] > 0:
            console.print(f"[yellow]⚠️ Errors Encountered: {self.stats['errors_encountered']}[/yellow]")

        console.print(f"\n[bold green]🎯 Performance Metrics:[/bold green]")
        console.print(f"[green]⚡ Speed: {self.stats['jobs_per_second']:.1f} jobs/second[/green]")
        console.print(f"[green]🕰️ Total Time: {self.stats['total_processing_time']:.1f} seconds[/green]")
        
        if self.stats["jobs_processed"] > 0:
            console.print(f"[green]🎯 Processing Method: {self.stats['processing_method_used']}[/green]")

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics."""
        return self.stats.copy()

    def get_jobspy_report(self) -> str:
        """Get detailed JobSpy integration report."""
        if not self.jobspy_scraper:
            return "JobSpy not used in this pipeline run."
        
        if hasattr(self.jobspy_scraper, 'generate_report'):
            return self.jobspy_scraper.generate_report()
        else:
            return f"JobSpy found {self.stats['jobspy_jobs_found']} jobs in {self.stats['jobspy_processing_time']:.1f}s"


# Convenience functions for easy access
def get_Improved_fast_pipeline(profile_name: str = "Nirajan", **config) -> JobPipeline:
    """Get configured Improved fast job pipeline instance."""
    return JobPipeline(profile_name, config)


async def run_Improved_pipeline(profile_name: str = "Nirajan", limit: int = 100, **config) -> List[Dict[str, Any]]:
    """Run enhanced job pipeline with JobSpy integration."""
    pipeline = JobPipeline(profile_name, config)
    return await pipeline.run_complete_pipeline(limit)


async def run_jobspy_only_pipeline(profile_name: str = "Nirajan", limit: int = 100, preset: str = "quality") -> List[Dict[str, Any]]:
    """Run pipeline with JobSpy only (fastest option)."""
    config = {
        "enable_jobspy": True,
        "enable_eluta": False,
        "enable_external_scraping": True,
        "enable_processing": True,
        "jobspy_preset": preset,
        "external_workers": 6
    }
    pipeline = JobPipeline(profile_name, config)
    return await pipeline.run_complete_pipeline(limit)


async def run_comprehensive_pipeline(profile_name: str = "Nirajan", limit: int = 200) -> List[Dict[str, Any]]:
    """Run comprehensive pipeline with all features enabled."""
    config = {
        "enable_jobspy": True,
        "enable_eluta": True,
        "enable_external_scraping": True,
        "enable_processing": True,
        "jobspy_preset": "comprehensive",
        "external_workers": 8,
        "processing_method": "auto"
    }
    pipeline = JobPipeline(profile_name, config)
    return await pipeline.run_complete_pipeline(limit)


# CLI test function
async def test_Improved_pipeline():
    """Test the Improved pipeline with JobSpy integration."""
    console.print("[bold blue]🧪 Testing Improved Pipeline with JobSpy Integration[/bold blue]")
    
    # Test JobSpy-only pipeline
    console.print("\n[cyan]Testing JobSpy-only pipeline...[/cyan]")
    pipeline = JobPipeline("test_profile", {
        "enable_jobspy": True,
        "enable_eluta": False,
        "jobspy_preset": "fast",
        "enable_external_scraping": False,
        "enable_processing": False
    })
    
    results = await pipeline.run_complete_pipeline(20)
    console.print(f"[green]✅ JobSpy test complete: {len(results)} jobs found[/green]")
    
    # Print JobSpy report
    if pipeline.jobspy_scraper:
        print("\n" + "="*50)
        print("JOBSPY INTEGRATION REPORT")
        print("="*50)
        print(pipeline.get_jobspy_report())


# Pipeline testing moved to tests/pipeline/
# Use pipeline classes directly in your code
