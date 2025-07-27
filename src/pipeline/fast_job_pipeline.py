#!/usr/bin/env python3
"""
Fast Job Pipeline - 3-Phase Job Processing System
Phase 1: Eluta URL Collection (single context, respects anti-bot)
Phase 2: Parallel External Job Description Scraping (6+ workers)
Phase 3: GPU-Accelerated Job Processing (pattern matching + analysis)

This is the new default job processor orchestrator.
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
from ..scrapers.unified_eluta_scraper import UnifiedElutaScraper
from ..scrapers.external_job_scraper import ExternalJobDescriptionScraper
from ..core.job_database import get_job_db
from ..utils.profile_helpers import load_profile

# Import processors (with fallbacks)
try:
    from ..ai.gpu_job_processor import GPUJobProcessor
    GPU_PROCESSOR_AVAILABLE = True
except ImportError:
    GPU_PROCESSOR_AVAILABLE = False

try:
    from ..analysis.hybrid_processor import HybridProcessingEngine
    HYBRID_PROCESSOR_AVAILABLE = True
except ImportError:
    HYBRID_PROCESSOR_AVAILABLE = False

try:
    from ..ai.enhanced_rule_based_analyzer import EnhancedRuleBasedAnalyzer
    RULE_BASED_AVAILABLE = True
except ImportError:
    RULE_BASED_AVAILABLE = False

console = Console()


class FastJobPipeline:
    """
    Fast 3-Phase Job Processing Pipeline
    
    This is the new default job processor orchestrator that replaces
    all the redundant job processors with a single, fast, integrated system.
    """

    def __init__(self, profile_name: str = "Nirajan", config: Optional[Dict] = None):
        self.profile_name = profile_name
        self.profile = load_profile(profile_name) or {}
        self.db = get_job_db(profile_name)
        
        # Configuration with defaults
        default_config = {
            "eluta_pages": 5,
            "eluta_jobs": 50,
            "external_workers": 6,
            "processing_method": "rule_based",  # rule_based is fastest, no Ollama needed
            "save_to_database": True,
            "enable_duplicate_check": True,
            "timeout_seconds": 1800,  # 30 minutes total timeout
        }
        self.config = {**default_config, **(config or {})}
        
        # Initialize components
        self.eluta_scraper = None
        self.external_scraper = None
        self.job_processor = None
        
        # Statistics
        self.stats = {
            "pipeline_start_time": None,
            "pipeline_end_time": None,
            "total_processing_time": 0.0,
            "phase1_time": 0.0,
            "phase2_time": 0.0,
            "phase3_time": 0.0,
            "urls_collected": 0,
            "descriptions_scraped": 0,
            "jobs_processed": 0,
            "jobs_saved": 0,
            "duplicates_skipped": 0,
            "errors_encountered": 0,
            "jobs_per_second": 0.0,
            "processing_method_used": "unknown"
        }

    async def run_complete_pipeline(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Run the complete 3-phase job processing pipeline.
        
        Args:
            limit: Maximum number of jobs to process (None for config default)
            
        Returns:
            List of fully processed job dictionaries
        """
        self.stats["pipeline_start_time"] = time.time()
        
        console.print(Panel.fit(
            "[bold blue]🚀 Fast Job Pipeline - 3-Phase Processing[/bold blue]\n"
            f"[cyan]Profile: {self.profile_name}[/cyan]\n"
            f"[cyan]Target Jobs: {limit or self.config['eluta_jobs']}[/cyan]\n"
            f"[cyan]External Workers: {self.config['external_workers']}[/cyan]",
            title="Pipeline Starting"
        ))

        try:
            # Phase 1: Eluta URL Collection
            job_urls = await self._phase1_collect_urls(limit)
            if not job_urls:
                console.print("[red]❌ No job URLs collected, pipeline stopped[/red]")
                return []

            # Phase 2: Parallel External Description Scraping
            jobs_with_descriptions = await self._phase2_scrape_descriptions(job_urls)
            if not jobs_with_descriptions:
                console.print("[red]❌ No job descriptions scraped, pipeline stopped[/red]")
                return []

            # Phase 3: Job Processing and Analysis
            processed_jobs = await self._phase3_process_jobs(jobs_with_descriptions)

            # Save to database if enabled
            if self.config["save_to_database"]:
                await self._save_jobs_to_database(processed_jobs)

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

    async def _phase1_collect_urls(self, limit: Optional[int]) -> List[str]:
        """Phase 1: Collect job URLs from Eluta (single browser context)."""
        console.print("\n[bold cyan]📋 Phase 1: Collecting Job URLs from Eluta[/bold cyan]")
        
        phase1_start = time.time()
        
        try:
            # Initialize Eluta scraper
            eluta_config = {
                "pages": self.config["eluta_pages"],
                "jobs": limit or self.config["eluta_jobs"],
                "headless": False,  # Disabled to handle popups
                "enable_ai": False,  # Just collect URLs, no processing yet
            }
            
            self.eluta_scraper = UnifiedElutaScraper(self.profile_name, eluta_config)
            
            # Scrape URLs (this respects Eluta anti-bot with single context)
            console.print("[cyan]🕷️ Scraping job URLs from Eluta...[/cyan]")
            scraped_jobs = await self.eluta_scraper.scrape_all_keywords()
            
            # Extract URLs
            job_urls = []
            for job in scraped_jobs:
                url = job.get("url") or job.get("apply_url")
                if url and "eluta.ca" not in url.lower():  # Only external URLs
                    job_urls.append(url)
            
            self.stats["urls_collected"] = len(job_urls)
            self.stats["phase1_time"] = time.time() - phase1_start
            
            console.print(f"[green]✅ Phase 1 Complete: {len(job_urls)} external URLs collected[/green]")
            console.print(f"[green]⏱️ Phase 1 Time: {self.stats['phase1_time']:.1f}s[/green]")
            
            return job_urls
            
        except Exception as e:
            console.print(f"[red]❌ Phase 1 Error: {e}[/red]")
            self.stats["errors_encountered"] += 1
            return []

    async def _phase2_scrape_descriptions(self, job_urls: List[str]) -> List[Dict[str, Any]]:
        """Phase 2: Scrape job descriptions from external sites in parallel."""
        console.print("\n[bold cyan]🌐 Phase 2: Scraping Job Descriptions (Parallel)[/bold cyan]")
        
        phase2_start = time.time()
        
        try:
            # Initialize external scraper
            self.external_scraper = ExternalJobDescriptionScraper(
                num_workers=self.config["external_workers"]
            )
            
            # Scrape descriptions in parallel
            console.print(f"[cyan]🚀 Scraping {len(job_urls)} job descriptions with {self.config['external_workers']} workers...[/cyan]")
            jobs_with_descriptions = await self.external_scraper.scrape_external_jobs_parallel(job_urls)
            
            self.stats["descriptions_scraped"] = len(jobs_with_descriptions)
            self.stats["phase2_time"] = time.time() - phase2_start
            
            console.print(f"[green]✅ Phase 2 Complete: {len(jobs_with_descriptions)} descriptions scraped[/green]")
            console.print(f"[green]⏱️ Phase 2 Time: {self.stats['phase2_time']:.1f}s[/green]")
            
            return jobs_with_descriptions
            
        except Exception as e:
            console.print(f"[red]❌ Phase 2 Error: {e}[/red]")
            self.stats["errors_encountered"] += 1
            return []

    async def _phase3_process_jobs(self, jobs_with_descriptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Phase 3: Process jobs with GPU/AI analysis."""
        console.print("\n[bold cyan]🧠 Phase 3: Processing Jobs with AI Analysis[/bold cyan]")
        
        phase3_start = time.time()
        
        try:
            # Determine best processing method
            processing_method = self._select_processing_method()
            console.print(f"[cyan]🔧 Using processing method: {processing_method}[/cyan]")
            
            # Process jobs based on selected method
            if processing_method == "gpu" and GPU_PROCESSOR_AVAILABLE:
                processed_jobs = await self._process_with_gpu(jobs_with_descriptions)
            elif processing_method == "hybrid" and HYBRID_PROCESSOR_AVAILABLE:
                processed_jobs = await self._process_with_hybrid(jobs_with_descriptions)
            elif processing_method == "rule_based" and RULE_BASED_AVAILABLE:
                processed_jobs = await self._process_with_rule_based(jobs_with_descriptions)
            else:
                # Fallback to basic processing
                processed_jobs = await self._process_with_basic(jobs_with_descriptions)
            
            self.stats["jobs_processed"] = len(processed_jobs)
            self.stats["phase3_time"] = time.time() - phase3_start
            self.stats["processing_method_used"] = processing_method
            
            console.print(f"[green]✅ Phase 3 Complete: {len(processed_jobs)} jobs processed[/green]")
            console.print(f"[green]⏱️ Phase 3 Time: {self.stats['phase3_time']:.1f}s[/green]")
            
            return processed_jobs
            
        except Exception as e:
            console.print(f"[red]❌ Phase 3 Error: {e}[/red]")
            self.stats["errors_encountered"] += 1
            return jobs_with_descriptions  # Return unprocessed jobs as fallback

    def _select_processing_method(self) -> str:
        """Select the best available processing method."""
        if self.config["processing_method"] != "auto":
            return self.config["processing_method"]
        
        # Auto-select based on availability
        if GPU_PROCESSOR_AVAILABLE:
            return "gpu"
        elif HYBRID_PROCESSOR_AVAILABLE:
            return "hybrid"
        elif RULE_BASED_AVAILABLE:
            return "rule_based"
        else:
            return "basic"

    async def _process_with_gpu(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process jobs with GPU acceleration."""
        console.print("[cyan]⚡ Using GPU-accelerated processing...[/cyan]")
        
        try:
            gpu_processor = GPUJobProcessor()
            result = await gpu_processor.process_jobs_gpu_async(jobs)
            return result.job_results
        except Exception as e:
            console.print(f"[yellow]⚠️ GPU processing failed: {e}, falling back...[/yellow]")
            return await self._process_with_hybrid(jobs)

    async def _process_with_hybrid(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process jobs with hybrid processing engine."""
        console.print("[cyan]🔄 Using hybrid processing (rule-based + AI)...[/cyan]")
        
        try:
            hybrid_processor = HybridProcessingEngine(user_profile=self.profile)
            processed_jobs = []
            
            for job in jobs:
                result = hybrid_processor.process_job(job)
                # Convert HybridProcessingResult to dict
                processed_job = job.copy()
                processed_job.update({
                    "required_skills": result.required_skills,
                    "job_requirements": result.job_requirements,
                    "compatibility_score": result.compatibility_score,
                    "analysis_confidence": result.analysis_confidence,
                    "extracted_benefits": result.extracted_benefits,
                    "analysis_reasoning": result.reasoning,
                    "processing_method": result.processing_method,
                    "processed_at": time.time()
                })
                processed_jobs.append(processed_job)
            
            return processed_jobs
        except Exception as e:
            console.print(f"[yellow]⚠️ Hybrid processing failed: {e}, falling back...[/yellow]")
            return await self._process_with_rule_based(jobs)

    async def _process_with_rule_based(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process jobs with rule-based analyzer."""
        console.print("[cyan]📋 Using rule-based processing...[/cyan]")
        
        try:
            rule_analyzer = EnhancedRuleBasedAnalyzer(self.profile)
            processed_jobs = []
            
            for job in jobs:
                analysis = rule_analyzer.analyze_job(job)
                processed_job = job.copy()
                processed_job.update(analysis)
                processed_job["processing_method"] = "rule_based"
                processed_job["processed_at"] = time.time()
                processed_jobs.append(processed_job)
            
            return processed_jobs
        except Exception as e:
            console.print(f"[yellow]⚠️ Rule-based processing failed: {e}, using basic...[/yellow]")
            return await self._process_with_basic(jobs)

    async def _process_with_basic(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Basic processing fallback."""
        console.print("[cyan]⚙️ Using basic processing (fallback)...[/cyan]")
        
        processed_jobs = []
        for job in jobs:
            processed_job = job.copy()
            processed_job.update({
                "required_skills": [],
                "job_requirements": [],
                "compatibility_score": 0.5,
                "analysis_confidence": 0.3,
                "extracted_benefits": [],
                "analysis_reasoning": "Basic processing - no advanced analysis available",
                "processing_method": "basic",
                "processed_at": time.time()
            })
            processed_jobs.append(processed_job)
        
        return processed_jobs

    async def _save_jobs_to_database(self, processed_jobs: List[Dict[str, Any]]) -> None:
        """Save processed jobs to database."""
        console.print("\n[cyan]💾 Saving jobs to database...[/cyan]")
        
        saved_count = 0
        duplicate_count = 0
        
        for job in processed_jobs:
            try:
                # Check for duplicates if enabled
                if self.config["enable_duplicate_check"]:
                    if self.db.is_duplicate_job(job):
                        duplicate_count += 1
                        continue
                
                # Save job to database
                success = self.db.add_job(job)
                if success:
                    saved_count += 1
                    
            except Exception as e:
                console.print(f"[yellow]⚠️ Error saving job: {e}[/yellow]")
                self.stats["errors_encountered"] += 1
        
        self.stats["jobs_saved"] = saved_count
        self.stats["duplicates_skipped"] = duplicate_count
        
        console.print(f"[green]✅ Database save complete: {saved_count} jobs saved, {duplicate_count} duplicates skipped[/green]")

    def _display_pipeline_results(self, processed_jobs: List[Dict[str, Any]]) -> None:
        """Display comprehensive pipeline results."""
        console.print("\n" + "=" * 80)
        console.print(Panel.fit("🎉 FAST JOB PIPELINE RESULTS", style="bold green"))

        # Calculate final statistics
        if self.stats["total_processing_time"] > 0:
            self.stats["jobs_per_second"] = self.stats["jobs_processed"] / self.stats["total_processing_time"]

        # Results table
        results_table = Table(title="📊 Pipeline Performance")
        results_table.add_column("Phase", style="cyan")
        results_table.add_column("Results", style="yellow")
        results_table.add_column("Time", style="green")
        results_table.add_column("Speed", style="magenta")

        results_table.add_row(
            "Phase 1: URL Collection",
            f"{self.stats['urls_collected']} URLs",
            f"{self.stats['phase1_time']:.1f}s",
            f"{self.stats['urls_collected']/self.stats['phase1_time']:.1f} URLs/sec" if self.stats['phase1_time'] > 0 else "N/A"
        )
        
        results_table.add_row(
            "Phase 2: Description Scraping",
            f"{self.stats['descriptions_scraped']} descriptions",
            f"{self.stats['phase2_time']:.1f}s",
            f"{self.stats['descriptions_scraped']/self.stats['phase2_time']:.1f} jobs/sec" if self.stats['phase2_time'] > 0 else "N/A"
        )
        
        results_table.add_row(
            "Phase 3: Job Processing",
            f"{self.stats['jobs_processed']} jobs",
            f"{self.stats['phase3_time']:.1f}s",
            f"{self.stats['jobs_processed']/self.stats['phase3_time']:.1f} jobs/sec" if self.stats['phase3_time'] > 0 else "N/A"
        )
        
        results_table.add_row(
            "[bold]Total Pipeline[/bold]",
            f"[bold]{len(processed_jobs)} jobs[/bold]",
            f"[bold]{self.stats['total_processing_time']:.1f}s[/bold]",
            f"[bold]{self.stats['jobs_per_second']:.1f} jobs/sec[/bold]"
        )

        console.print(results_table)

        # Summary information
        console.print(f"\n[bold blue]📋 Pipeline Summary:[/bold blue]")
        console.print(f"[green]✅ Processing Method: {self.stats['processing_method_used']}[/green]")
        console.print(f"[green]✅ Jobs Saved to Database: {self.stats['jobs_saved']}[/green]")
        console.print(f"[green]✅ Duplicates Skipped: {self.stats['duplicates_skipped']}[/green]")
        if self.stats["errors_encountered"] > 0:
            console.print(f"[yellow]⚠️ Errors Encountered: {self.stats['errors_encountered']}[/yellow]")

        # Performance comparison
        estimated_old_time = len(processed_jobs) * 0.6  # ~36 seconds per job with old system
        speedup = estimated_old_time / self.stats['total_processing_time'] if self.stats['total_processing_time'] > 0 else 1
        
        console.print(f"\n[bold green]🚀 Performance Improvement:[/bold green]")
        console.print(f"[green]📈 Estimated speedup: {speedup:.1f}x faster than old system[/green]")
        console.print(f"[green]⚡ New pipeline: {self.stats['total_processing_time']:.1f}s vs Old system: ~{estimated_old_time:.0f}s[/green]")

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return self.stats.copy()


# Convenience functions
def get_fast_job_pipeline(profile_name: str = "Nirajan", **config) -> FastJobPipeline:
    """Get configured fast job pipeline instance."""
    return FastJobPipeline(profile_name, config)


async def run_fast_pipeline(profile_name: str = "Nirajan", limit: int = 50, **config) -> List[Dict[str, Any]]:
    """Run fast job pipeline with simple interface."""
    pipeline = FastJobPipeline(profile_name, config)
    return await pipeline.run_complete_pipeline(limit)


# CLI test function
async def test_fast_pipeline():
    """Test the fast pipeline with a small job set."""
    console.print("[bold blue]🧪 Testing Fast Job Pipeline[/bold blue]")
    
    pipeline = FastJobPipeline("test_profile", {
        "eluta_jobs": 10,
        "external_workers": 3,
        "processing_method": "rule_based"
    })
    
    results = await pipeline.run_complete_pipeline(10)
    console.print(f"[green]✅ Test complete: {len(results)} jobs processed[/green]")


if __name__ == "__main__":
    asyncio.run(test_fast_pipeline())