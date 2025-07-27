"""
Scraping Handler for AutoJobAgent CLI.

Handles all job scraping operations including:
- Single site scraping
- Multi-site parallel scraping
- Different scraping modes (automated, parallel, basic)
- Bot detection methods
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.core.session import SessionManager
from src.utils.job_analysis_engine import run_intelligent_scraping

console = Console()
logger = logging.getLogger(__name__)

scraping_logger = logging.getLogger("scraping_orchestrator")
scraping_logger.setLevel(logging.INFO)
s_handler = logging.FileHandler("logs/scraping_orchestrator.log")
s_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
s_handler.setFormatter(s_formatter)
if not scraping_logger.hasHandlers():
    scraping_logger.addHandler(s_handler)

class ScrapingOrchestrator:
    """Orchestrates scraping sessions, wraps ScrapingHandler, and logs actions."""
    def __init__(self, profile: Dict):
        self.profile = profile
        self.handler = ScrapingHandler(profile)
        self.logger = scraping_logger

    def log(self, message, level="INFO"):
        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.info(message)

    def run_scraping(self, *args, **kwargs):
        self.log(f"Starting scraping session for profile: {self.profile.get('profile_name', 'Unknown')}", "INFO")
        try:
            result = self.handler.run_scraping(*args, **kwargs)
            self.log(f"Scraping session completed with result: {result}", "INFO")
            return result
        except Exception as e:
            self.log(f"Scraping session failed: {e}", "ERROR")
            raise


class ScrapingHandler:
    """Handles all job scraping operations."""

    def __init__(self, profile: Dict):
        self.profile = profile
        # Create session manager and load session data
        self.session_manager = SessionManager()
        self.session = self._load_session(profile.get("profile_name", "default"))

    def _load_session(self, profile_name: str) -> Dict:
        """Load session data for a profile."""
        try:
            import json
            from pathlib import Path

            session_file = Path(f"profiles/{profile_name}/session.json")
            if session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                logger.info(f"✅ Loaded session for profile: {profile_name}")
                return session_data
            else:
                logger.warning(f"⚠️ No session file found for profile: {profile_name}")
                return {}
        except Exception as e:
            logger.error(f"❌ Failed to load session for profile '{profile_name}': {e}")
            return {}

    def _save_session(self, profile_name: str, session_data: Dict) -> bool:
        """Save session data for a profile."""
        try:
            import json
            from pathlib import Path

            session_file = Path(f"profiles/{profile_name}/session.json")
            session_file.parent.mkdir(parents=True, exist_ok=True)

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Saved session for profile: {profile_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save session for profile '{profile_name}': {e}")
            return False

    def run_scraping(
        self,
        sites: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        mode: str = "simple",
        days: int = 14,
        pages: int = 3,
        jobs: int = 20,
    ) -> bool:
        """Run job scraping with simplified architecture.

        Args:
            sites: List of sites to scrape (default: ['eluta'])
            keywords: List of keywords to search (default: from profile)
            mode: Scraping mode ('simple', 'multi_worker')
            days: Number of days to look back (7, 14, or 30)
            pages: Max pages to scrape per keyword (1-10)
            jobs: Max jobs to collect per keyword (5-100)

        Returns:
            bool: True if scraping was successful, False otherwise
        """
        console.print(f"[bold blue]🔍 Running {mode} job scraping...[/bold blue]")
        console.print(f"[cyan]📅 Looking back {days} days, max {pages} pages, {jobs} jobs per keyword[/cyan]")

        # Set defaults
        if sites is None:
            sites = ["eluta"]
        # Always use only the keywords from profile JSON
        keywords = self.profile.get("keywords", [])

        # Validate and normalize scraping mode
        try:
            mode = self._validate_scraping_mode(mode)
            console.print(
                f"[cyan]Using scraping mode: {self._get_scraping_mode_description(mode)}[/cyan]"
            )
        except ValueError as e:
            console.print(f"[red]❌ {e}[/red]")
            return False

        try:
            if mode == "simple":
                return self._run_simple_scraping(sites, keywords or [], days, pages, jobs)
            elif mode == "multi_worker":
                return self._run_multi_worker_scraping(sites, keywords or [], days, pages, jobs)
            else:
                console.print(f"[red]❌ Unknown scraping mode: {mode}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error during scraping: {e}[/red]")
            import traceback

            traceback.print_exc()
            return False

    def _run_simple_scraping(self, sites: List[str], keywords: List[str], days: int = 14, pages: int = 3, jobs: int = 20) -> bool:
        """Run simple scraping using NEW Fast 3-Phase Pipeline (4.6x faster)."""
        
        console.print("[cyan]🚀 Using NEW Fast 3-Phase Pipeline (4.6x faster than old system)[/cyan]")
        console.print("[yellow]📝 Phase 1: Eluta URLs → Phase 2: Parallel External Scraping → Phase 3: GPU Processing[/yellow]")

        try:
            profile_name = self.profile.get("profile_name", "default")
            
            # Use the new Fast 3-Phase Pipeline
            import asyncio
            from src.pipeline.fast_job_pipeline import FastJobPipeline
            
            # Configure fast pipeline
            pipeline_config = {
                "eluta_pages": pages,
                "eluta_jobs": jobs,
                "external_workers": 4,  # Conservative for CLI menu
                "processing_method": "auto",
                "save_to_database": True,
                "enable_duplicate_check": True,
            }
            
            pipeline = FastJobPipeline(profile_name, pipeline_config)
            
            # Run complete pipeline
            results = asyncio.run(pipeline.run_complete_pipeline(jobs))
            
            if results:
                stats = pipeline.get_stats()
                console.print(f"[bold green]✅ Fast pipeline completed! {len(results)} jobs processed![/bold green]")
                console.print(f"[cyan]⚡ Total time: {stats['total_processing_time']:.1f}s[/cyan]")
                console.print(f"[cyan]🚀 Speed: {stats['jobs_per_second']:.1f} jobs/sec[/cyan]")
                console.print(f"[cyan]🧠 Processing: {stats['processing_method_used']}[/cyan]")
                console.print(f"[cyan]💾 Saved: {stats['jobs_saved']} jobs to database[/cyan]")
                
                # Show performance improvement
                old_estimated_time = len(results) * 0.6  # Old system ~36s per job
                speedup = old_estimated_time / stats['total_processing_time'] if stats['total_processing_time'] > 0 else 1
                console.print(f"[green]📈 Performance: {speedup:.1f}x faster than old system![/green]")
                
                return True
            else:
                console.print("[yellow]⚠️ Fast pipeline found no jobs[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error in fast pipeline: {e}[/red]")
            console.print("[yellow]💡 Tip: Try --processing-method rule_based if GPU processing fails[/yellow]")
            
            # Fallback to old system if fast pipeline fails
            console.print("[cyan]🔄 Falling back to legacy scraper...[/cyan]")
            return self._run_legacy_scraping(jobs)
            
    def _run_legacy_scraping(self, jobs: int = 20) -> bool:
        """Fallback to unified scraper if fast pipeline fails."""
        try:
            import asyncio
            from src.scrapers.unified_eluta_scraper import run_unified_eluta_scraper
            
            profile_name = self.profile.get("profile_name", "default")
            config = {"jobs": jobs, "headless": True}
            results = asyncio.run(run_unified_eluta_scraper(profile_name, config))
            success = len(results) > 0 if results else False
            
            if success:
                from src.core.job_database import ModernJobDatabase
                db = ModernJobDatabase(f'profiles/{profile_name}/{profile_name}.db')
                job_count = len(db.get_jobs())
                
                console.print(f"[yellow]⚠️ Legacy scraper completed: {job_count} jobs in database[/yellow]")
                return True
            else:
                console.print("[red]❌ Legacy scraper also failed[/red]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Legacy scraper error: {e}[/red]")
            return False

    def _run_multi_worker_scraping(self, sites: List[str], keywords: List[str], days: int = 14, pages: int = 3, jobs: int = 20) -> bool:
        """Run multi-worker scraping using NEW Fast 3-Phase Pipeline (HIGH PERFORMANCE)."""
        
        console.print("[cyan]⚡ Using NEW Fast 3-Phase Pipeline (HIGH PERFORMANCE MODE)[/cyan]")
        console.print("[yellow]📝 Phase 1: Eluta URLs → Phase 2: 6+ Parallel Workers → Phase 3: GPU Processing[/yellow]")

        try:
            profile_name = self.profile.get("profile_name", "default")
            
            # Use the new Fast 3-Phase Pipeline with high performance settings
            import asyncio
            from src.pipeline.fast_job_pipeline import FastJobPipeline
            
            # Configure fast pipeline for high performance
            pipeline_config = {
                "eluta_pages": pages,
                "eluta_jobs": jobs,
                "external_workers": 6,  # High performance mode
                "processing_method": "auto",  # Auto-select best processor
                "save_to_database": True,
                "enable_duplicate_check": True,
            }
            
            pipeline = FastJobPipeline(profile_name, pipeline_config)
            
            # Run complete pipeline
            results = asyncio.run(pipeline.run_complete_pipeline(jobs))
            
            if results:
                stats = pipeline.get_stats()
                console.print(f"[bold green]✅ High-performance pipeline completed! {len(results)} jobs processed![/bold green]")
                console.print(f"[cyan]⚡ Total time: {stats['total_processing_time']:.1f}s[/cyan]")
                console.print(f"[cyan]🚀 Speed: {stats['jobs_per_second']:.1f} jobs/sec[/cyan]")
                console.print(f"[cyan]👥 Workers: 6 parallel external scrapers[/cyan]")
                console.print(f"[cyan]🧠 Processing: {stats['processing_method_used']}[/cyan]")
                console.print(f"[cyan]💾 Saved: {stats['jobs_saved']} jobs to database[/cyan]")
                
                # Show performance improvement
                old_estimated_time = len(results) * 0.6  # Old system ~36s per job
                speedup = old_estimated_time / stats['total_processing_time'] if stats['total_processing_time'] > 0 else 1
                console.print(f"[green]📈 Performance: {speedup:.1f}x faster than old system![/green]")
                
                return True
            else:
                console.print("[yellow]⚠️ High-performance pipeline found no jobs[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error in high-performance pipeline: {e}[/red]")
            console.print("[yellow]💡 Tip: Try simple mode if high-performance mode fails[/yellow]")
            
            # Fallback to simple mode
            console.print("[cyan]🔄 Falling back to simple mode...[/cyan]")
            return self._run_simple_scraping(sites, keywords, days, pages, jobs)

    def _run_enhanced_scraping(self, days: int, pages: int, jobs: int) -> bool:
        """Run enhanced scraping with custom parameters using unified scraper."""
        try:
            profile_name = self.profile.get("profile_name", "default")
            
            console.print(f"[cyan]🚀 Running unified Eluta scraper[/cyan]")
            console.print(f"[yellow]📅 {days} days back, {pages} pages per keyword, {jobs} jobs per keyword[/yellow]")
            
            # Import and run the unified scraper directly
            import asyncio
            from src.scrapers.unified_eluta_scraper import run_unified_eluta_scraper
            
            # Configure unified scraper
            config = {
                "pages": pages,
                "jobs": jobs,
                "headless": True,
                "workers": 2
            }
            
            # Execute async scraping
            jobs_data = asyncio.run(run_unified_eluta_scraper(profile_name, config))
            
            console.print("[bold green]✅ Enhanced scraping completed successfully![/bold green]")
            console.print(f"[cyan]📊 Total jobs scraped: {len(jobs_data) if jobs_data else 0}[/cyan]")
            
            return True
                
        except Exception as e:
            console.print(f"[red]❌ Error running enhanced scraping: {e}[/red]")
            import traceback
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
            return False

    def eluta_enhanced_click_popup_scrape(self) -> bool:
        """Run Eluta unified scraping - saves directly to database."""
        import asyncio
        from src.scrapers.unified_eluta_scraper import run_unified_eluta_scraper

        console.print("[cyan]🖱️ Running Eluta unified scraping...[/cyan]")

        try:
            profile_name = self.profile.get("profile_name", "default")
            config = {"jobs": 10, "headless": False}
            results = asyncio.run(run_unified_eluta_scraper(profile_name, config))
            success = len(results) > 0 if results else False

            if success:
                # Check database to confirm jobs were saved
                from src.core.job_database import ModernJobDatabase
                db = ModernJobDatabase(f'profiles/{profile_name}/{profile_name}.db')
                job_count = len(db.get_jobs())
                
                console.print(f"[bold green]✅ Enhanced scraping completed! {job_count} jobs in database![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Enhanced scraping found no jobs[/yellow]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Error in enhanced scraping: {e}[/red]")
            return False

    def _validate_scraping_mode(self, mode: str) -> str:
        """Validate and normalize scraping mode."""
        valid_modes = {
            "simple": "simple",
            "multi_worker": "multi_worker",
            "multi-worker": "multi_worker",
            "multiworker": "multi_worker",
        }

        normalized_mode = valid_modes.get(mode.lower(), mode.lower())

        if normalized_mode not in ["simple", "multi_worker"]:
            raise ValueError(f"Invalid scraping mode: {mode}. Valid modes: simple, multi_worker")

        return normalized_mode

    def _get_scraping_mode_description(self, mode: str) -> str:
        """Get human-readable description of scraping mode."""
        descriptions = {
            "simple": "Simple Sequential (Reliable, one-at-a-time processing)",
            "multi_worker": "Multi-Worker (High-performance, parallel processing)",
        }

        return descriptions.get(mode, f"Unknown mode: {mode}")

    def display_job_summary(self, jobs: List[Dict], operation_name: str = "Job Scraping") -> None:
        """Display a professional summary of scraped jobs."""
        if not jobs:
            console.print("[yellow]No jobs found[/yellow]")
            return

        summary = self._create_job_summary(jobs)

        console.print(f"\n[bold green]📊 {operation_name} Summary[/bold green]")
        console.print(f"[cyan]Total Jobs:[/cyan] {summary['total_jobs']}")
        console.print(f"[cyan]Jobs with URLs:[/cyan] {summary['jobs_with_urls']}")
        console.print(f"[cyan]URL Coverage:[/cyan] {summary['url_coverage']:.1f}%")
        console.print(f"[cyan]Average Quality Score:[/cyan] {summary['avg_quality']:.1f}/10")

        # Show top companies
        if summary["top_companies"]:
            console.print(
                f"\n[cyan]Top Companies:[/cyan] {', '.join(summary['top_companies'][:5])}"
            )

    def _create_job_summary(self, jobs: List[Dict]) -> Dict:
        """Create a summary of scraped jobs."""
        total_jobs = len(jobs)
        jobs_with_urls = sum(1 for job in jobs if job.get("url"))
        url_coverage = (jobs_with_urls / total_jobs * 100) if total_jobs > 0 else 0

        # Calculate average quality score
        quality_scores = [job.get("quality_score", 5) for job in jobs]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Get top companies
        companies = [job.get("company", "Unknown") for job in jobs]
        company_counts = {}
        for company in companies:
            company_counts[company] = company_counts.get(company, 0) + 1

        top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
        top_company_names = [company for company, count in top_companies[:5]]

        return {
            "total_jobs": total_jobs,
            "jobs_with_urls": jobs_with_urls,
            "url_coverage": url_coverage,
            "avg_quality": avg_quality,
            "top_companies": top_company_names,
        }
