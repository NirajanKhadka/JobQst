"""
Main Menu for AutoJobAgent CLI.

Handles the main interactive menu system.
"""

from typing import Dict
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import logging
import time

from ..actions.scraping_actions import ScrapingActions
from ..actions.dashboard_actions import DashboardActions
from ..actions.system_actions import SystemActions

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
        self.dashboard_actions = DashboardActions(profile)
        self.system_actions = SystemActions(profile)

    def show_interactive_menu(self) -> str:
        """Show the simplified main interactive menu."""
        console.clear()
        console.print(Panel("🤖 AutoJobAgent - Main Menu", style="bold blue"))
        
        # Show profile info
        self._show_profile_info()

        console.print("\n[bold]Available Actions:[/bold]")
        options = {
            "1": "🚀 Ultra-Fast Job Scraping (2+ jobs/sec, 29x faster!)",
            "2": "📊 Dashboard", 
            "3": "⚙️ System Status",
            "4": "⚡ Ultra-Fast Process Jobs (GPU optimized)",
            "5": "👤 Profile Settings",
            "q": "🚪 Exit",
        }

        for key, value in options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

        console.print()
        choice = Prompt.ask("Select option", choices=list(options.keys()), default="1")
        return choice

    def handle_menu_choice(self, choice: str, args) -> bool:
        """Handle menu choice and execute corresponding action.

        Args:
            choice: Menu choice (1-5, q)
            args: Command line arguments

        Returns:
            bool: True to continue menu loop, False to exit
        """
        if choice == "1":  # Ultra-Fast Job Scraping (32x faster)
            self.scraping_actions.show_scraping_menu(args)
        elif choice == "2":  # Status & Dashboard
            self.dashboard_actions.show_status_and_dashboard_action()
        elif choice == "3":  # System status & settings
            self.system_actions.system_status_and_settings_action()
        elif choice == "4":  # Auto-Process Jobs with Smart Detection
            import asyncio
            asyncio.run(self._auto_process_jobs_action(args))
        elif choice == "5":  # Profile Management with Auto-Watch
            self._profile_management_action(args)
        elif choice == "q":  # Exit
            console.print("[green]Goodbye![/green]")
            return False

        # Don't pause after exit
        if choice != "q":
            input("\nPress Enter to continue...")

        return True

    def _show_profile_info(self) -> None:
        """Show current profile information in a condensed format."""
        profile_name = self.profile.get("profile_name", "Unknown")
        name = self.profile.get("name", "Not set")
        email = self.profile.get("email", "Not set")

        console.print(f"[bold]👤 Profile:[/bold] {profile_name}")
        console.print(f"[bold]📧 Name:[/bold] {name}")
        console.print(f"[bold]📧 Email:[/bold] {email}")

        # Show keywords (condensed)
        keywords = self.profile.get("keywords", [])
        if keywords:
            kw_display = ', '.join(keywords[:3])
            console.print(f"[bold]🔍 Keywords:[/bold] {kw_display}")
            if len(keywords) > 3:
                console.print(f"[dim]... and {len(keywords) - 3} more[/dim]")
        
        # Show database info (condensed)
        try:
            from src.core.job_database import get_job_db
            db = get_job_db(profile_name)
            job_count = db.get_job_count()
            console.print(f"[bold]💾 Database:[/bold] {job_count} jobs stored")
            
            # Check for unprocessed jobs
            if job_count > 0:
                unprocessed_count = db.get_unprocessed_job_count()
                
                if unprocessed_count > 0:
                    console.print(
                        f"[yellow]⚠️ {unprocessed_count} unprocessed jobs "
                        f"detected[/yellow]"
                    )
                    console.print("[cyan]💡 Use option 4 to process them[/cyan]")
                else:
                    console.print("[green]✅ All jobs processed[/green]")
                
                # Show recent activity (condensed)
                recent_jobs = db.get_jobs(limit=3)
                if recent_jobs:
                    titles = [
                        job.get('title', 'Unknown')[:20] + '...'
                        for job in recent_jobs
                    ]
                    console.print(
                        f"[dim]� Recent: {', '.join(titles)}[/dim]"
                    )
        except Exception:
            console.print("[bold]� Database:[/bold] Not accessible")

    async def _auto_process_jobs_action(self, args) -> None:
        """Auto-detect and process unprocessed jobs using Ultra-Fast Pipeline (DEFAULT)."""
        console.print(Panel("🚀 Ultra-Fast Job Processing (2+ jobs/sec)", style="bold blue"))
        
        try:
            profile_name = self.profile.get("profile_name", "default")
            
            # Check database for existing jobs
            from src.core.job_database import get_job_db
            db = get_job_db(profile_name)
            
            # Get jobs that need processing using proper database query
            jobs_to_process = db.get_jobs_for_processing(limit=5000)  # Get all unprocessed jobs
            
            if not jobs_to_process:
                console.print("[green]✅ No unprocessed jobs found[/green]")
                console.print("[cyan]💡 All jobs in database are fully processed[/cyan]")
                console.print("[cyan]💡 Use option 1 to scrape new jobs[/cyan]")
                return
            
            console.print(f"[cyan]📋 Found {len(jobs_to_process)} jobs that need processing[/cyan]")
            console.print(f"[cyan]🚀 Using Ultra-Fast Pipeline (2+ jobs/sec, 29x faster!)[/cyan]")
            
            # Use OptimizedTwoStageProcessor for ultra-fast processing
            from src.optimization.integrated_processor import create_optimized_processor
            
            console.print(f"[cyan]🔄 Processing {len(jobs_to_process)} existing jobs with ultra-fast method...[/cyan]")
            
            # Initialize optimized processor
            processor = create_optimized_processor(
                user_profile=self.profile,
                cpu_workers=4,  # Optimized for performance
                max_concurrent_stage2=2
            )
            
            # Process jobs using optimized processor
            processed_jobs = await processor.process_jobs(jobs_to_process)
            
            if processed_jobs:
                # Save updated jobs to database
                saved_count = 0
                for result in processed_jobs:
                    try:
                        # Convert TwoStageResult to job dict for database
                        job_dict = {
                            'id': result.job_id,
                            'url': result.url,
                            'title': result.stage1.title if result.stage1 else 'Unknown',
                            'company': result.stage1.company if result.stage1 else 'Unknown',
                            'location': result.stage1.location if result.stage1 else 'Unknown',
                            'salary_range': result.stage1.salary_range if result.stage1 else None,
                            'compatibility_score': result.final_compatibility,
                            'required_skills': result.final_skills,
                            'requirements': result.final_requirements,
                            'status': 'processed',
                            'processing_method': processing_method,
                            'processed_at': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'recommendation': result.recommendation
                        }
                        
                        # Update original job data with processed results
                        if result.job_data:
                            job_dict.update(result.job_data)
                        
                        # Get the job ID for the update operation
                        job_id = result.job_data.get('id') if result.job_data else None
                        if job_id:
                            db.update_job(job_id, job_dict)
                            saved_count += 1
                        else:
                            # Try to find job by job_id string
                            if hasattr(result, 'job_id') and result.job_id:
                                # Fallback: update by job_id (string identifier)
                                try:
                                    existing_jobs = db.get_jobs(limit=1000)
                                    for job in existing_jobs:
                                        if str(job.get('id', '')) == str(result.job_id):
                                            db.update_job(job['id'], job_dict)
                                            saved_count += 1
                                            break
                                except Exception:
                                    pass
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Failed to save job {result.job_id}: {e}[/yellow]")
                
                console.print(f"[bold green]✅ Processing completed successfully![/bold green]")
                console.print(f"[cyan]📊 Jobs processed: {len(processed_jobs)}[/cyan]")
                console.print(f"[cyan]🧠 Processing method: {processing_method}[/cyan]")
                console.print(f"[cyan]💾 Jobs updated in database: {saved_count}[/cyan]")
                
                # Show sample of processed jobs
                if processed_jobs:
                    console.print("\n[bold]📋 Sample Processed Jobs:[/bold]")
                    for i, result in enumerate(processed_jobs[:3], 1):
                        # Safely extract title and company with None checks
                        title = 'Unknown'
                        company = 'Unknown'
                        
                        try:
                            if result.stage1 and hasattr(result.stage1, 'title') and result.stage1.title:
                                title = str(result.stage1.title)[:40]
                            elif result.job_data and result.job_data.get('title'):
                                title = str(result.job_data['title'])[:40]
                            
                            if result.stage1 and hasattr(result.stage1, 'company') and result.stage1.company:
                                company = str(result.stage1.company)[:20]
                            elif result.job_data and result.job_data.get('company'):
                                company = str(result.job_data['company'])[:20]
                            
                            score = getattr(result, 'final_compatibility', 0.0)
                            skills_count = len(getattr(result, 'final_skills', []))
                            console.print(
                                f"  {i}. {title}... at {company} "
                                f"(Score: {score:.2f}, Skills: {skills_count})"
                            )
                        except Exception as e:
                            console.print(f"  {i}. Error displaying job: {e}")
                            continue
                    
                    if len(processed_jobs) > 3:
                        console.print(
                            f"  ... and {len(processed_jobs) - 3} more jobs"
                        )
            else:
                console.print("[yellow]⚠️ No jobs were successfully processed[/yellow]")
                console.print("[cyan]💡 Try a different processing method or check job data quality[/cyan]")
                
        except Exception as e:
            console.print("[red]❌ Error in job processing[/red]")
            console.print(f"[red]Error details: {str(e)}[/red]")
            import traceback
            console.print(f"[dim]Traceback: {traceback.format_exc()}[/dim]")

    def _profile_management_action(self, args):
        """Unified profile management with auto-watch resume functionality."""
        from src.cli.actions.profile_actions import ProfileActions
        from rich.prompt import Prompt, Confirm
        from pathlib import Path
        
        console.print(Panel("👤 Profile Management (Auto-Watch Resume)", style="bold green"))
        
        # Get profile name
        profile_name = Prompt.ask("Enter profile name")
        profile_path = Path("profiles") / profile_name
        
        # Check if profile exists
        if profile_path.exists():
            console.print(f"[cyan]📁 Profile '{profile_name}' already exists[/cyan]")
            
            # Check for existing resume files
            resume_files = []
            for ext in ['*.pdf', '*.doc', '*.docx', '*.txt']:
                resume_files.extend(profile_path.glob(ext))
            
            if resume_files:
                console.print(f"[green]📄 Found {len(resume_files)} resume file(s)[/green]")
                if Confirm.ask("Scan existing resume files now?", default=True):
                    # Scan existing resumes
                    from types import SimpleNamespace
                    profile_args = SimpleNamespace(profile=profile_name)
                    profile_actions = ProfileActions(self.profile)
                    success = profile_actions.scan_resume_action(profile_args)
                    
                    if success:
                        console.print("[green]✅ Profile updated from existing resume![/green]")
                        return
            
            # Ask if they want to watch for new resume files
            if Confirm.ask("Watch folder for new resume files?", default=True):
                self._start_resume_watch(profile_path, profile_name)
            
        else:
            # Create new profile
            console.print(f"[cyan]📁 Creating new profile '{profile_name}'[/cyan]")
            
            # Create profile directory and template
            profile_path.mkdir(parents=True, exist_ok=True)
            
            # Copy template
            template_path = Path("profiles/profile_template.json")
            profile_file = profile_path / "profile.json"
            
            if template_path.exists():
                import json
                import time
                with open(template_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                profile_data["profile_name"] = profile_name
                profile_data["name"] = profile_name
                profile_data["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=2)
            
            console.print(f"[green]✅ Profile '{profile_name}' created successfully![/green]")
            console.print(f"[cyan]📁 Location: {profile_path}[/cyan]")
            
            # Start watching for resume files
            self._start_resume_watch(profile_path, profile_name)
    
    def _start_resume_watch(self, profile_path: Path, profile_name: str):
        """Start watching for resume files with auto-processing."""
        from src.cli.actions.profile_actions import ProfileActions
        
        console.print("\n" + "="*60)
        console.print(Panel(
            f"👀 [bold green]WATCHING FOR RESUME FILES[/bold green]\n\n"
            f"📁 Profile folder: [cyan]{profile_path}[/cyan]\n"
            f"📄 [yellow]Drop your resume file here (PDF, DOC, DOCX, TXT)[/yellow]\n"
            f"🤖 [green]It will be automatically processed![/green]\n\n"
            f"[dim]Press Enter after copying your resume file to process it immediately[/dim]\n"
            f"[dim]Or press Ctrl+C to stop watching[/dim]",
            title=f"Profile: {profile_name}",
            border_style="green"
        ))
        
        try:
            # Check if resume already exists
            resume_files = []
            for ext in ['*.pdf', '*.doc', '*.docx', '*.txt']:
                resume_files.extend(profile_path.glob(ext))
            
            if resume_files:
                console.print(f"[green]📄 Resume file detected: {resume_files[0].name}[/green]")
                input("Press Enter to process it...")
                
                # Process the resume
                from types import SimpleNamespace
                profile_args = SimpleNamespace(profile=profile_name)
                profile_actions = ProfileActions(self.profile)
                success = profile_actions.scan_resume_action(profile_args)
                
                if success:
                    console.print("[green]✅ Resume processed successfully![/green]")
                    console.print("[cyan]💡 Keywords and skills extracted automatically[/cyan]")
                else:
                    console.print("[red]❌ Resume processing failed![/red]")
                return
            
            # Set up file watcher for new files
            from src.cli.actions.profile_actions import ResumeWatcher
            from watchdog.observers import Observer
            import time
            
            event_handler = ResumeWatcher(str(profile_path), profile_name)
            observer = Observer()
            observer.schedule(event_handler, str(profile_path), recursive=False)
            observer.start()
            
            try:
                while True:
                    user_input = input("Press Enter after copying resume (or 'q' to quit): ")
                    if user_input.lower() == 'q':
                        break
                    
                    # Check for new resume files
                    new_resume_files = []
                    for ext in ['*.pdf', '*.doc', '*.docx', '*.txt']:
                        new_resume_files.extend(profile_path.glob(ext))
                    
                    if new_resume_files:
                        console.print(f"[green]📄 Processing resume: {new_resume_files[0].name}[/green]")
                        
                        # Process the resume
                        from types import SimpleNamespace
                        profile_args = SimpleNamespace(profile=profile_name)
                        profile_actions = ProfileActions(self.profile)
                        success = profile_actions.scan_resume_action(profile_args)
                        
                        if success:
                            console.print("[green]✅ Resume processed successfully![/green]")
                            console.print("[cyan]💡 Keywords and skills extracted automatically[/cyan]")
                            break
                        else:
                            console.print("[red]❌ Resume processing failed![/red]")
                    else:
                        console.print("[yellow]⚠️ No resume files found. Please copy your resume to the folder.[/yellow]")
                        
            except KeyboardInterrupt:
                console.print("\n🛑 [yellow]Stopped watching for files.[/yellow]")
            finally:
                observer.stop()
                observer.join()
                
        except Exception as e:
            console.print(f"[red]❌ Error in profile management: {e}[/red]")

    def run_interactive_mode(self, args) -> int:
        """Run the interactive menu mode."""
        while True:
            choice = self.show_interactive_menu()
            if not self.handle_menu_choice(choice, args):
                break

        return 0

