"""
Main Menu for AutoJobAgent CLI.

Handles the main interactive menu system.
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import logging

from ..actions.scraping_actions import ScrapingActions
from ..actions.application_actions import ApplicationActions
from ..actions.dashboard_actions import DashboardActions
from ..actions.system_actions import SystemActions
from ..actions.document_actions import DocumentActions

console = Console()

# Set up CLI logger (can be configured to write to a file for dashboard pickup)
cli_logger = logging.getLogger("cli_orchestrator")
cli_logger.setLevel(logging.INFO)
handler = logging.FileHandler("logs/cli_orchestrator.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
if not cli_logger.hasHandlers():
    cli_logger.addHandler(handler)

class CLIOrchestrator:
    """Orchestrates the CLI session, wraps MainMenu, and logs all actions."""
    def __init__(self, profile: Dict):
        self.profile = profile
        self.menu = MainMenu(profile)
        self.logger = cli_logger

    def run(self, args) -> int:
        self.logger.info(f"Starting CLI session for profile: {self.profile.get('profile_name', 'Unknown')}")
        while True:
            choice = self.menu.show_interactive_menu()
            self.logger.info(f"Menu choice selected: {choice}")
            continue_session = self.menu.handle_menu_choice(choice, args)
            self.logger.info(f"Action executed for choice {choice}, continue: {continue_session}")
            if not continue_session:
                self.logger.info("CLI session ended by user.")
                break
        return 0


class MainMenu:
    """Handles the main interactive menu."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.scraping_actions = ScrapingActions(profile)
        self.application_actions = ApplicationActions(profile)
        self.dashboard_actions = DashboardActions(profile)
        self.system_actions = SystemActions(profile)
        self.document_actions = DocumentActions(profile)

    def show_interactive_menu(self) -> str:
        """Show the improved main interactive menu with NEW Fast 3-Phase Pipeline."""
        console.clear()
        console.print(Panel("🤖 AutoJobAgent - Main Menu", style="bold blue"))
        
        # Show new features banner
        console.print("[green]🆕 NEW: Fast 3-Phase Pipeline - 4.6x Performance Improvement![/green]")
        console.print("[cyan]⚡ Phase 1: Eluta URLs → Phase 2: Parallel External Scraping → Phase 3: GPU Processing[/cyan]")
        console.print("[dim]💡 All scraping now uses the new fast pipeline automatically[/dim]")

        # Show profile info
        self._show_profile_info()

        console.print("\n[bold]Available Actions:[/bold]")
        options = {
            "1": "🚀 Job Scraping (NEW Fast 3-Phase Pipeline - 4.6x faster)",
            "2": "📝 Apply to Jobs from Queue",
            "3": "🎯 Apply to Specific Job URL",
            "4": "📂 Apply Jobs from External Source (CSV or Link)",
            "5": "📄 AI Document Generation (Resumes & Cover Letters)",
            "6": "📊 Status & Dashboard",
            "7": "⚙️ System Status & Settings",
            "8": "🔄 Process Existing Jobs (Improved with Fast Pipeline)",
            "9": "🚪 Exit",
        }

        for key, value in options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        console.print()
        choice = Prompt.ask("Select option", choices=list(options.keys()), default="1")
        return choice

    def handle_menu_choice(self, choice: str, args) -> bool:
        """Handle menu choice and execute corresponding action.

        Args:
            choice: Menu choice (1-9)
            args: Command line arguments

        Returns:
            bool: True to continue menu loop, False to exit
        """
        if choice == "1":  # Job Scraping with site selection
            self.scraping_actions.show_scraping_menu(args)
        elif choice == "2":  # Apply from queue
            self.application_actions.apply_from_queue_action(args)
        elif choice == "3":  # Apply to specific URL
            self.application_actions.apply_to_specific_url_action(args)
        elif choice == "4":  # Apply jobs from external (CSV or link)
            self.application_actions.apply_jobs_from_external_action(args)
        elif choice == "5":  # AI Document Generation
            self.document_actions.run_document_menu()
        elif choice == "6":  # Status & Dashboard
            self.dashboard_actions.show_status_and_dashboard_action()
        elif choice == "7":  # System status & settings
            self.system_actions.system_status_and_settings_action()
        elif choice == "8":  # Process existing jobs with Fast Pipeline
            import asyncio
            asyncio.run(self._process_existing_jobs_action(args))
        elif choice == "9":  # Exit
            console.print("[green]Goodbye![green]")
            return False

        # Don't pause after exit
        if choice != "9":
            input("\nPress Enter to continue...")

        return True

    def _show_profile_info(self) -> None:
        """Show current profile information with Improved details."""
        profile_name = self.profile.get("profile_name", "Unknown")
        name = self.profile.get("name", "Not set")
        email = self.profile.get("email", "Not set")

        console.print(f"[bold]👤 Profile:[/bold] {profile_name}")
        console.print(f"[bold]📧 Name:[/bold] {name}")
        console.print(f"[bold]📧 Email:[/bold] {email}")

        # Show keywords
        keywords = self.profile.get("keywords", [])
        if keywords:
            console.print(f"[bold]🔍 Keywords:[/bold] {', '.join(keywords[:3])}")
            if len(keywords) > 3:
                console.print(f"[dim]... and {len(keywords) - 3} more[/dim]")
        
        # Show database info
        try:
            from src.core.job_database import get_job_db
            db = get_job_db(profile_name)
            job_count = db.get_job_count()
            console.print(f"[bold]💾 Database:[/bold] {job_count} jobs stored")
            
            # Show recent activity
            if job_count > 0:
                recent_jobs = db.get_jobs()[-3:] if len(db.get_jobs()) >= 3 else db.get_jobs()
                if recent_jobs:
                    console.print(f"[dim]📋 Recent: {', '.join([job.get('title', 'Unknown')[:20] + '...' for job in recent_jobs])}[/dim]")
        except Exception:
            console.print(f"[bold]💾 Database:[/bold] Not accessible")
        
        # Show fast pipeline status
        console.print(f"[green]🚀 Fast Pipeline:[/green] Ready (4.6x performance boost)")
        console.print(f"[dim]💡 Use option 1 for the new Fast 3-Phase Pipeline[/dim]")

    async def _process_existing_jobs_action(self, args) -> None:
        """Process existing jobs in database using Fast Pipeline orchestrator."""
        console.print(Panel("🔄 Process Existing Jobs with Fast Pipeline", style="bold blue"))
        
        try:
            profile_name = self.profile.get("profile_name", "default")
            
            # Check database for existing jobs
            from src.core.job_database import get_job_db
            db = get_job_db(profile_name)
            
            # Get jobs that need processing (status = 'scraped' or incomplete processing)
            all_jobs = db.get_all_jobs()
            
            # Filter jobs that need processing
            jobs_to_process = []
            for job in all_jobs:
                status = job.get('status', '')
                # Process jobs that are scraped but not fully processed
                if (status == 'scraped' or 
                    not job.get('required_skills') or 
                    not job.get('compatibility_score') or
                    job.get('compatibility_score', 0) == 0):
                    jobs_to_process.append(job)
            
            if not jobs_to_process:
                console.print("[yellow]⚠️ No jobs found that need processing[/yellow]")
                console.print("[cyan]💡 All jobs in database appear to be fully processed[/cyan]")
                console.print("[cyan]💡 Use option 1 to scrape new jobs[/cyan]")
                return
            
            console.print(f"[cyan]📋 Found {len(jobs_to_process)} jobs that need processing[/cyan]")
            console.print(f"[cyan]🚀 Using Fast Pipeline orchestrator for Improved processing[/cyan]")
            
            # Show processing options
            console.print(f"\n[bold]Processing Options:[/bold]")
            process_options = {
                "1": "🚀 Fast Processing (GPU/Hybrid analysis)",
                "2": "🔧 Rule-based Processing (No AI dependencies)",
                "3": "🧠 AI-only Processing (Maximum accuracy)",
                "4": "⚡ Auto-select Best Method",
            }
            
            for key, value in process_options.items():
                console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
            
            console.print()
            process_choice = Prompt.ask("Select processing method", choices=list(process_options.keys()), default="4")
            
            # Map choice to processing method
            method_map = {
                "1": "gpu",
                "2": "rule_based", 
                "3": "hybrid",
                "4": "auto"
            }
            processing_method = method_map.get(process_choice, "rule_based")  # Default to fast rule-based
            
            # Use Fast Pipeline to process existing jobs
            import asyncio
            from src.pipeline.fast_job_pipeline import FastJobPipeline
            
            # Configure pipeline for processing existing jobs
            pipeline_config = {
                "eluta_pages": 1,  # Not scraping new jobs
                "eluta_jobs": 0,   # Not scraping new jobs
                "external_workers": 0,  # Not scraping descriptions
                "processing_method": processing_method,
                "save_to_database": True,
                "enable_duplicate_check": False,  # These are existing jobs
            }
            
            pipeline = FastJobPipeline(profile_name, pipeline_config)
            
            console.print(f"[cyan]🔄 Processing {len(jobs_to_process)} existing jobs with {processing_method} method...[/cyan]")
            
            # Process jobs directly (skip scraping phases)
            processed_jobs = await pipeline._phase3_process_jobs(jobs_to_process)
            
            if processed_jobs:
                # Save updated jobs to database
                await pipeline._save_jobs_to_database(processed_jobs)
                
                stats = pipeline.get_stats()
                console.print(f"[bold green]✅ Processing completed successfully![/bold green]")
                console.print(f"[cyan]📊 Jobs processed: {len(processed_jobs)}[/cyan]")
                console.print(f"[cyan]🧠 Processing method: {stats.get('processing_method_used', processing_method)}[/cyan]")
                console.print(f"[cyan]💾 Jobs updated in database: {stats.get('jobs_saved', len(processed_jobs))}[/cyan]")
                
                # Show sample of processed jobs
                if processed_jobs:
                    console.print(f"\n[bold]📋 Sample Processed Jobs:[/bold]")
                    for i, job in enumerate(processed_jobs[:3], 1):
                        title = job.get('title', 'Unknown')[:40]
                        company = job.get('company', 'Unknown')[:20]
                        score = job.get('compatibility_score', 0)
                        skills_count = len(job.get('required_skills', []))
                        console.print(f"  {i}. {title}... at {company} (Score: {score:.2f}, Skills: {skills_count})")
                    
                    if len(processed_jobs) > 3:
                        console.print(f"  ... and {len(processed_jobs) - 3} more jobs")
            else:
                console.print("[yellow]⚠️ No jobs were successfully processed[/yellow]")
                console.print("[cyan]💡 Try a different processing method or check job data quality[/cyan]")
                
        except Exception as e:
            console.print(f"[red]❌ Error processing existing jobs: {e}[/red]")
            console.print("[yellow]💡 Try using option 1 to scrape fresh jobs instead[/yellow]")
            import traceback
            console.print(f"[dim]Debug info: {traceback.format_exc()}[/dim]")

    def run_interactive_mode(self, args) -> int:
        """Run the interactive menu mode."""
        while True:
            choice = self.show_interactive_menu()
            if not self.handle_menu_choice(choice, args):
                break

        return 0
