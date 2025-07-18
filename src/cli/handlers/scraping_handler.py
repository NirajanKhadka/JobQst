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
        if keywords is None:
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
        """Run simple sequential scraping - saves directly to database."""
        
        # Use enhanced scraper if custom parameters are provided
        if days != 14 or pages != 3 or jobs != 20:
            console.print("[cyan]🚀 Using enhanced scraper with custom parameters[/cyan]")
            return self._run_enhanced_scraping(days, pages, jobs)
        
        # Use comprehensive scraper for default parameters
        from src.scrapers.comprehensive_eluta_scraper import run_comprehensive_scraping
        import asyncio

        console.print("[cyan]🔄 Using simple sequential scraping for reliability[/cyan]")
        console.print("[yellow]📝 Note: This will scrape jobs and save directly to database.[/yellow]")

        try:
            profile_name = self.profile.get("profile_name", "default")
            
            # Run scraping - this automatically saves to database
            success = asyncio.run(run_comprehensive_scraping(profile_name, max_jobs_per_keyword=15))

            if success:
                # Check database to confirm jobs were saved
                from src.core.job_database import ModernJobDatabase
                db = ModernJobDatabase(f'profiles/{profile_name}/{profile_name}.db')
                job_count = len(db.get_jobs())
                
                console.print(
                    f"[bold green]✅ Simple scraping completed! {job_count} jobs in database![/bold green]"
                )
                console.print(
                    f"[cyan]🔄 Jobs saved to database. Use 'python main.py {profile_name} --action process-jobs' to process them.[/cyan]"
                )
                return True
            else:
                console.print("[yellow]⚠️ Simple scraping found no jobs[/yellow]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Error in simple scraping: {e}[/red]")
            return False

    def _run_multi_worker_scraping(self, sites: List[str], keywords: List[str], days: int = 14, pages: int = 3, jobs: int = 20) -> bool:
        """Run multi-worker scraping - saves directly to database."""
        
        # Use enhanced scraper if custom parameters are provided
        if days != 14 or pages != 3 or jobs != 20:
            console.print("[cyan]⚡ Using enhanced scraper with custom parameters (multi-worker mode)[/cyan]")
            return self._run_enhanced_scraping(days, pages, jobs)
        
        # Use comprehensive scraper for default parameters
        from src.scrapers.comprehensive_eluta_scraper import run_comprehensive_scraping
        import asyncio

        console.print("[cyan]⚡ Using multi-worker scraping (parallel keyword processing)[/cyan]")
        console.print("[yellow]📝 Note: This will scrape jobs and save directly to database.[/yellow]")

        try:
            profile_name = self.profile.get("profile_name", "default")

            # Run scraping - this automatically saves to database
            success = asyncio.run(
                run_comprehensive_scraping(profile_name, max_jobs_per_keyword=30)
            )

            if success:
                # Check database to confirm jobs were saved
                from src.core.job_database import ModernJobDatabase
                db = ModernJobDatabase(f'profiles/{profile_name}/{profile_name}.db')
                job_count = len(db.get_jobs())

                console.print(
                    f"[bold green]✅ Multi-worker scraping completed! {job_count} jobs in database![/bold green]"
                )
                console.print(
                    f"[cyan]🔄 Jobs saved to database. Use 'python main.py {profile_name} --action process-jobs' to process them.[/cyan]"
                )
                
                return True
            else:
                console.print(
                    "[yellow]⚠️ No jobs found during scraping[/yellow]"
                )
                return False

        except Exception as e:
            console.print(f"[red]❌ Error in multi-worker scraping: {e}[/red]")
            return False

    def _run_enhanced_scraping(self, days: int, pages: int, jobs: int) -> bool:
        """Run enhanced scraping with custom parameters and AI content extraction."""
        try:
            profile_name = self.profile.get("profile_name", "default")
            
            console.print(f"[cyan]🚀 Running enhanced Eluta scraper with AI content extraction[/cyan]")
            console.print(f"[yellow]📅 {days} days back, {pages} pages per keyword, {jobs} jobs per keyword[/yellow]")
            
            # Import and run the enhanced scraper directly
            from src.scrapers.enhanced_eluta_scraper import EnhancedElutaScraper
            import asyncio
            
            # Create enhanced scraper instance
            scraper = EnhancedElutaScraper(
                profile_name=profile_name,
                ai_model="llama3.2:1b"
            )
            
            # Run scraping with custom parameters (async)
            async def run_scraping():
                return await scraper.scrape_with_options(
                    days=days,
                    pages_per_keyword=pages,
                    max_jobs_per_keyword=jobs,
                    enable_ai_extraction=True
                )
            
            # Execute async scraping
            jobs_data = asyncio.run(run_scraping())
            
            console.print("[bold green]✅ Enhanced scraping completed successfully![/bold green]")
            console.print(f"[cyan]📊 Total jobs scraped: {len(jobs_data) if jobs_data else 0}[/cyan]")
            
            return True
                
        except Exception as e:
            console.print(f"[red]❌ Error running enhanced scraping: {e}[/red]")
            import traceback
            console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")
            return False

    def eluta_enhanced_click_popup_scrape(self) -> bool:
        """Run Eluta enhanced click-popup scraping - saves directly to database."""
        from src.scrapers.comprehensive_eluta_scraper import run_comprehensive_scraping
        import asyncio

        console.print("[cyan]🖱️ Running Eluta enhanced click-popup scraping...[/cyan]")

        try:
            profile_name = self.profile.get("profile_name", "default")
            success = asyncio.run(run_comprehensive_scraping(profile_name, max_jobs_per_keyword=10))

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
