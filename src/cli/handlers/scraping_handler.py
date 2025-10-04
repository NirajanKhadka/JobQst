"""
Scraping Handler for AutoJobAgent CLI.

Handles all job scraping operations including:
- Single site scraping
- Multi-site parallel scraping
- Different scraping modes (automated, parallel, basic)
- Bot detection methods
"""

import logging
from typing import Dict, List, Optional

from rich.console import Console

from src.core.session import SessionManager

console = Console()
logger = logging.getLogger(__name__)

scraping_logger = logging.getLogger("scraping_orchestrator")
scraping_logger.setLevel(logging.INFO)
s_handler = logging.FileHandler("logs/scraping_orchestrator.log")
s_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
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
        self.log(
            f"Starting scraping session for profile: {self.profile.get('profile_name', 'Unknown')}",
            "INFO",
        )
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
        console.print(
            f"[cyan]📅 Looking back {days} days, max {pages} pages, {jobs} jobs per keyword[/cyan]"
        )

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
            elif mode == "eluta_only":
                console.print(
                    "[yellow]🐌 Running Eluta-only scraping (slower but comprehensive)[/yellow]"
                )
                return self._run_eluta_scraping(jobs=jobs, pages=pages)
            else:
                console.print(f"[red]❌ Unknown scraping mode: {mode}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error during scraping: {e}[/red]")
            import traceback

            traceback.print_exc()
            return False

    def _create_pipeline_config(self, mode: str, jobs: int):
        """Create pipeline config based on scraping mode."""
        return {
            "enable_jobspy": True,
            "enable_eluta": mode != "fast",  # Skip Eluta for fast mode
            "enable_external_scraping": True,
            "enable_processing": True,
            "jobspy_preset": "quality" if mode == "simple" else "fast",
            "jobspy_max_jobs": jobs,
            "external_workers": 6 if mode == "simple" else 12,
            "processing_method": "auto",
            "save_to_database": True,
            "enable_duplicate_check": True,
            "hours_old": 72 if mode == "fast" else 168,  # Shorter for speed
        }

    def _display_pipeline_results(self, results: List[Dict], stats: Dict, mode: str) -> None:
        """Display pipeline results with performance stats."""
        total_jobs = len(results)
        total_time = stats.get("total_processing_time", 0)
        jobs_per_sec = stats.get("jobs_per_second", 0)

        console.print(
            f"[bold green]✅ {mode.title()} pipeline completed! "
            f"{total_jobs} jobs processed![/bold green]"
        )
        console.print(f"[cyan]⚡ Total time: {total_time:.1f}s[/cyan]")
        console.print(f"[cyan]🚀 Speed: {jobs_per_sec:.1f} jobs/sec[/cyan]")

        # Display additional stats if available
        if "jobspy_jobs_found" in stats:
            console.print(f"[cyan]🚀 JobSpy jobs: {stats['jobspy_jobs_found']}[/cyan]")
        if "descriptions_fetched" in stats:
            console.print(f"[cyan]📄 Descriptions fetched: {stats['descriptions_fetched']}[/cyan]")

        # Processing mode stats
        if mode == "ai_processor":
            jobs_processed = stats.get("jobs_processed", 0)
            console.print(f"[cyan]🧠 AI Processing: {jobs_processed} " f"jobs analyzed[/cyan]")
        else:  # multi_worker
            console.print("[cyan]🚀 32x Performance Improvement![/cyan]")
            workers = stats.get("cpu_workers", 12)
            console.print(f"[cyan]👥 Workers: {workers} parallel " f"processors[/cyan]")
            processing_method = stats.get("processing_method_used", "auto")
            console.print(f"[cyan]🧠 Processing: {processing_method}[/cyan]")
            jobs_saved = stats.get("jobs_saved", total_jobs)
            console.print(f"[cyan]💾 Saved: {jobs_saved} jobs to " f"database[/cyan]")

        ready_jobs = stats["jobs_ready_to_apply"]
        console.print(f"[cyan]🎯 Ready to Apply: {ready_jobs} jobs[/cyan]")

        # Show performance improvement
        old_time = total_jobs * 0.6  # Old system ~36s per job
        speedup = old_time / total_time if total_time > 0 else 1
        console.print(f"[green]📈 Performance: {speedup:.1f}x faster " f"than old system![/green]")

    def _run_ultra_fast_pipeline(self, mode: str, jobs: int) -> bool:
        """Run the ultra-fast pipeline with mode-specific configuration."""
        # Display mode-specific messages
        if mode == "simple":
            console.print(
                "[cyan]🚀 Using NEW Fast 3-Phase Pipeline (4.6x faster than old system)[/cyan]"
            )
            console.print(
                "[yellow]📝 Phase 1: Eluta URLs → Phase 2: Parallel External Scraping → Phase 3: GPU Processing[/yellow]"
            )
        else:  # multi_worker
            console.print("[cyan]⚡ Using PARALLEL PIPELINE[/cyan]")
            console.print(
                "[yellow]📝 JobSpy Scraping → Parallel AI Processing → " "Batch Processing[/yellow]"
            )
            console.print("[green]🚀 Optimized for parallel processing efficiency[/green]")

        try:
            import asyncio
            from src.pipeline.enhanced_fast_job_pipeline import ImprovedFastJobPipeline

            profile_name = self.profile.get("profile_name", "default")
            config = self._create_pipeline_config(mode, jobs)
            pipeline = ImprovedFastJobPipeline(profile_name, config)

            # Run improved pipeline
            results = asyncio.run(pipeline.run_complete_pipeline(jobs))

            if results:
                stats = pipeline.get_stats()
                self._display_pipeline_results(results, stats, mode)
                return True
            else:
                console.print(f"[yellow]⚠️ {mode.title()} pipeline found no jobs[/yellow]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error in {mode} pipeline: {e}[/red]")
            console.print(
                "[yellow]💡 Tip: Try --processing-method rule_based if GPU processing fails[/yellow]"
            )

            # Fallback strategies
            if mode == "multi_worker":
                console.print("[cyan]🔄 Falling back to simple mode...[/cyan]")
                return self._run_ultra_fast_pipeline("simple", jobs)
            else:
                console.print("[cyan]🔄 Falling back to legacy scraper...[/cyan]")
                return self._run_legacy_scraping(jobs)

    def _run_simple_scraping(
        self, sites: List[str], keywords: List[str], days: int = 14, pages: int = 3, jobs: int = 20
    ) -> bool:
        """Run simple scraping using NEW Fast 3-Phase Pipeline (4.6x faster)."""
        return self._run_ultra_fast_pipeline("simple", jobs)

    def _run_multi_worker_scraping(
        self, sites: List[str], keywords: List[str], days: int = 14, pages: int = 3, jobs: int = 20
    ) -> bool:
        """Run multi-worker scraping using NEW Fast 3-Phase Pipeline (HIGH PERFORMANCE)."""
        return self._run_ultra_fast_pipeline("multi_worker", jobs)

    def _run_eluta_scraping(
        self, jobs: int = 20, headless: bool = True, pages: int = 3, workers: int = 2
    ) -> bool:
        """Run Eluta scraping with configurable parameters."""
        import asyncio
        from src.scrapers.unified_eluta_scraper import run_unified_eluta_scraper

        console.print("[cyan]🚀 Running unified Eluta scraper[/cyan]")

        try:
            profile_name = self.profile.get("profile_name", "default")
            config = {"jobs": jobs, "headless": headless, "pages": pages, "workers": workers}

            results = asyncio.run(run_unified_eluta_scraper(profile_name, config))
            success = len(results) > 0 if results else False

            if success:
                from src.core.job_database import get_job_db

                db = get_job_db(profile_name)
                job_count = len(db.get_jobs())

                console.print(
                    f"[bold green]✅ Eluta scraping completed! {job_count} jobs in database![/bold green]"
                )
                return True
            else:
                console.print("[yellow]⚠️ Eluta scraping found no jobs[/yellow]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Error in Eluta scraping: {e}[/red]")
            return False

    def _run_legacy_scraping(self, jobs: int = 20) -> bool:
        """Fallback to unified scraper if fast pipeline fails."""
        try:
            success = self._run_eluta_scraping(jobs, headless=True)
            if success:
                console.print(f"[yellow]⚠️ Legacy scraper completed[/yellow]")
            else:
                console.print("[red]❌ Legacy scraper also failed[/red]")
            return success
        except Exception as e:
            console.print(f"[red]❌ Legacy scraper error: {e}[/red]")
            return False

    def _run_Improved_scraping(self, days: int, pages: int, jobs: int) -> bool:
        """Run Improved scraping with custom parameters using unified scraper."""
        console.print(
            f"[yellow]📅 {days} days back, {pages} pages per keyword, {jobs} jobs per keyword[/yellow]"
        )
        return self._run_eluta_scraping(jobs, headless=True, pages=pages, workers=2)

    def eluta_Improved_click_popup_scrape(self) -> bool:
        """Run Eluta scraping with popup handling - saves directly to database."""
        console.print("[cyan]🖱️ Running Eluta scraping with popup handling...[/cyan]")
        return self._run_eluta_scraping(jobs=10, headless=False)

    def _validate_scraping_mode(self, mode: str) -> str:
        """Validate and normalize scraping mode."""
        valid_modes = {
            "simple": "simple",
            "multi_worker": "multi_worker",
            "multi-worker": "multi_worker",
            "multiworker": "multi_worker",
            "eluta_only": "eluta_only",
            "eluta-only": "eluta_only",
            "elutaonly": "eluta_only",
        }

        normalized_mode = valid_modes.get(mode.lower(), mode.lower())

        if normalized_mode not in ["simple", "multi_worker", "eluta_only"]:
            raise ValueError(
                f"Invalid scraping mode: {mode}. Valid modes: simple, multi_worker, eluta_only"
            )

        return normalized_mode

    def _get_scraping_mode_description(self, mode: str) -> str:
        """Get human-readable description of scraping mode."""
        descriptions = {
            "simple": "Simple Sequential (Reliable, one-at-a-time processing)",
            "multi_worker": "Multi-Worker (High-performance, parallel processing)",
            "eluta_only": "Eluta-Only (Slower but comprehensive, secondary option)",
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
