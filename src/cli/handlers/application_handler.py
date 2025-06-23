"""
Application Handler for AutoJobAgent CLI.

Handles all job application operations including:
- Applying to jobs from queue
- Applying to specific URLs
- CSV batch applications
- ATS system integration
"""

import time
import csv
from typing import Dict, List, Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.core import utils
from src.ats.csv_applicator import CSVJobApplicator
from ats import detect, get_submitter

console = Console()


class ApplicationHandler:
    """Handles all job application operations."""
    
    def __init__(self, profile: Dict):
        self.profile = profile
        self.session = self._load_session(profile.get('profile_name', 'default'))
    
    def _load_session(self, profile_name: str) -> Dict:
        """Load session data for a profile."""
        try:
            import json
            from pathlib import Path
            session_file = Path(f"profiles/{profile_name}/session.json")
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                return session_data
            else:
                return {}
        except Exception:
            return {}
    
    def _save_session(self, profile_name: str, session_data: Dict) -> bool:
        """Save session data for a profile."""
        try:
            import json
            from pathlib import Path
            session_file = Path(f"profiles/{profile_name}/session.json")
            session_file.parent.mkdir(parents=True, exist_ok=True)
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def run_application(self, jobs: Optional[List[Dict]] = None, ats: str = "auto") -> bool:
        """Run job application process.

        Args:
            jobs: List of jobs to apply to (default: from queue)
            ats: ATS system to use (default: auto-detect)

        Returns:
            bool: True if applications were successful, False otherwise
        """
        console.print("[bold blue]📝 Running job application process...[/bold blue]")

        try:
            if jobs is None:
                # Load jobs from session queue
                scraped_jobs = self.session.get("scraped_jobs", [])
                done_jobs = self.session.get("done", [])

                # Filter out already processed jobs
                pending_jobs = [job for job in scraped_jobs if utils.hash_job(job) not in done_jobs]

                if not pending_jobs:
                    console.print("[yellow]No jobs in queue to apply to[/yellow]")
                    return False

                jobs = pending_jobs[:5]  # Default batch size

            console.print(f"[green]Found {len(jobs)} jobs to apply to[/green]")

            # Create mock args object for compatibility with existing apply_from_queue function
            class MockArgs:
                def __init__(self):
                    self.ats = ats
                    self.batch = len(jobs)
                    self.verbose = False
                    self.headless = False
                    self.allow_senior = False

            mock_args = MockArgs()

            # Use existing apply_from_queue function
            result = self.apply_from_queue(mock_args)

            return result == 0

        except Exception as e:
            console.print(f"[red]❌ Error during application process: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    def apply_from_queue(self, args) -> int:
        """Apply to jobs from the queue."""
        console.print("[bold blue]📝 Applying to jobs from queue...[/bold blue]")
        
        # Load jobs from session
        scraped_jobs = self.session.get("scraped_jobs", [])
        done_jobs = self.session.get("done", [])
        
        if not scraped_jobs:
            console.print("[yellow]No jobs in queue to apply to[/yellow]")
            return 1
        
        # Filter out already processed jobs
        pending_jobs = [job for job in scraped_jobs if utils.hash_job(job) not in done_jobs]
        
        if not pending_jobs:
            console.print("[yellow]All jobs in queue have been processed[/yellow]")
            return 0
        
        # Limit batch size
        batch_size = getattr(args, 'batch', 5)
        jobs_to_apply = pending_jobs[:batch_size]
        
        console.print(f"[cyan]Applying to {len(jobs_to_apply)} jobs...[/cyan]")
        
        # Create browser context for applications
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=getattr(args, 'headless', False))
            context = browser.new_context()
            
            success_count = 0
            for i, job in enumerate(jobs_to_apply, 1):
                console.print(f"\n[bold]Job {i}/{len(jobs_to_apply)}:[/bold] {job.get('title', 'Unknown')}")
                console.print(f"[cyan]Company:[/cyan] {job.get('company', 'Unknown')}")
                console.print(f"[cyan]URL:[/cyan] {job.get('url', 'No URL')}")
                
                if not job.get('url'):
                    console.print("[yellow]⚠️ Skipping job without URL[/yellow]")
                    continue
                
                try:
                    # Detect ATS system
                    ats_system = args.ats if args.ats != "auto" else detect(job['url'])
                    console.print(f"[cyan]ATS System:[/cyan] {ats_system}")
                    
                    # Get submitter with browser context
                    submitter = get_submitter(ats_system, context)
                    if not submitter:
                        console.print(f"[red]❌ No submitter available for {ats_system}[/red]")
                        continue
                    
                    # Generate documents
                    resume_path, cover_letter_path = self._generate_documents(job)
                    
                    # Apply to job
                    result = submitter.submit(job, self.profile, resume_path, cover_letter_path)
                    
                    if result == "Applied":
                        console.print("[bold green]✅ Application successful![/bold green]")
                        success_count += 1
                        
                        # Mark as done
                        job_hash = utils.hash_job(job)
                        done_jobs.append(job_hash)
                        self.session["done"] = done_jobs
                        self._save_session(self.profile.get('profile_name', 'default'), self.session)
                    else:
                        console.print(f"[red]❌ Application failed: {result}[/red]")
                    
                    # Delay between applications
                    if i < len(jobs_to_apply):
                        delay = getattr(args, 'delay', 30)
                        console.print(f"[cyan]Waiting {delay} seconds before next application...[/cyan]")
                        time.sleep(delay)
                    
                except Exception as e:
                    console.print(f"[red]❌ Error applying to job: {e}[/red]")
                    continue
            
            browser.close()
        
        console.print(f"\n[bold green]✅ Applications completed! {success_count}/{len(jobs_to_apply)} successful[/bold green]")
        return 0
    
    def apply_to_specific_job(self, job_url: str, args) -> str:
        """Apply to a specific job URL."""
        console.print(f"[bold blue]📝 Applying to specific job: {job_url}[/bold blue]")
        
        try:
            # Detect ATS system
            ats_system = args.ats if args.ats != "auto" else detect(job_url)
            console.print(f"[cyan]ATS System:[/cyan] {ats_system}")
            
            # Create browser context
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=getattr(args, 'headless', False))
                context = browser.new_context()
                
                # Get submitter with browser context
                submitter = get_submitter(ats_system, context)
                if not submitter:
                    browser.close()
                    return f"❌ No submitter available for {ats_system}"
                
                # Create job object
                job = {
                    'url': job_url,
                    'title': 'Unknown',
                    'company': 'Unknown'
                }
                
                # Generate documents
                resume_path, cover_letter_path = self._generate_documents(job)
                
                # Apply to job
                result = submitter.submit(job, self.profile, resume_path, cover_letter_path)
                
                browser.close()
                
                if result == "Applied":
                    return "✅ Application successful!"
                else:
                    return f"❌ Application failed: {result}"
                    
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _generate_documents(self, job: Dict) -> tuple:
        """Generate resume and cover letter for a job."""
        from src.utils.document_generator import customize
        
        try:
            # Generate customized documents
            resume_path, cover_letter_path = customize(job, self.profile)
            
            return resume_path, cover_letter_path
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error generating documents: {e}[/yellow]")
            # Return default paths if generation fails
            return "resume.pdf", "cover_letter.pdf"
    
    def apply_from_csv(self, csv_path: str, args) -> int:
        """Apply to jobs from CSV file."""
        console.print(f"[bold blue]📝 Applying to jobs from CSV: {csv_path}[/bold blue]")
        
        try:
            # Load jobs from CSV
            jobs = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    jobs.append(row)
            
            if not jobs:
                console.print("[yellow]No jobs found in CSV file[/yellow]")
                return 1
            
            console.print(f"[cyan]Found {len(jobs)} jobs in CSV[/cyan]")
            
            # Use CSV applicator
            profile_name = self.profile.get('profile_name', 'default')
            applicator = CSVJobApplicator(profile_name)
            success_count = applicator.apply_to_jobs(jobs, args)
            
            console.print(f"[bold green]✅ CSV applications completed! {success_count}/{len(jobs)} successful[/bold green]")
            return 0
            
        except Exception as e:
            console.print(f"[red]❌ Error processing CSV: {e}[/red]")
            return 1
    
    def select_ats(self) -> str:
        """Let user select ATS system."""
        console.print("\n[bold]Available ATS Systems:[/bold]")
        ats_options = {
            "1": "workday",
            "2": "icims", 
            "3": "greenhouse",
            "4": "lever",
            "5": "bamboohr",
            "6": "auto"
        }
        
        for key, value in ats_options.items():
            display_name = "Auto-detect" if value == "auto" else value.title()
            console.print(f"  [bold cyan]{key}[/bold cyan]: {display_name}")
        
        choice = Prompt.ask("Select ATS system", choices=list(ats_options.keys()), default="6")
        return ats_options[choice]
    
    def prompt_continue(self) -> bool:
        """Prompt user to continue."""
        return Prompt.ask("Continue?", choices=["y", "n"], default="y") == "y"
    
    def is_senior_job(self, job_title: str) -> bool:
        """Check if job title indicates senior position."""
        senior_keywords = [
            'senior', 'sr.', 'sr ', 'lead', 'principal', 'manager', 'director',
            'supervisor', 'head of', 'chief', 'vp', 'vice president',
            'experienced', 'expert', 'architect', 'staff engineer'
        ]
        
        job_title_lower = job_title.lower()
        return any(keyword in job_title_lower for keyword in senior_keywords) 