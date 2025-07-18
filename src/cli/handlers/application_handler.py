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

from src.utils.job_helpers import generate_job_hash
from src.ats.csv_applicator import CSVJobApplicator
from src.ats import detect, get_submitter
from src.job_applier.job_applier import JobApplier

console = Console()


class ApplicationHandler:
    """Handles all job application operations."""

    def __init__(self, profile: Dict):
        self.profile = profile
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
            with open(session_file, "w", encoding="utf-8") as f:
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
                scraped_jobs = self.session.get("scraped_jobs", [])
                done_jobs = self.session.get("done", [])
                pending_jobs = [
                    job for job in scraped_jobs if generate_job_hash(job) not in done_jobs
                ]
                if not pending_jobs:
                    console.print("[yellow]No jobs in queue to apply to[/yellow]")
                    return False
                jobs = pending_jobs[:5]
            console.print(f"[green]Found {len(jobs)} jobs to apply to[/green]")
            applier = JobApplier(self.profile)
            results = [applier.apply(job, ats=ats) for job in jobs]
            return all(r == "Applied" for r in results)
        except Exception as e:
            console.print(f"[red]❌ Error during application process: {e}[/red]")
            import traceback

            traceback.print_exc()
            return False

    def apply_from_queue(self, args) -> int:
        """Apply to jobs from the queue."""
        console.print("[bold blue]📝 Applying to jobs from queue...[/bold blue]")
        scraped_jobs = self.session.get("scraped_jobs", [])
        done_jobs = self.session.get("done", [])
        if not scraped_jobs:
            console.print("[yellow]No jobs in queue to apply to[/yellow]")
            return 1
        pending_jobs = [job for job in scraped_jobs if generate_job_hash(job) not in done_jobs]
        if not pending_jobs:
            console.print("[yellow]All jobs in queue have been processed[/yellow]")
            return 0
        batch_size = getattr(args, "batch", 5)
        jobs_to_apply = pending_jobs[:batch_size]
        console.print(f"[cyan]Applying to {len(jobs_to_apply)} jobs...[/cyan]")
        applier = JobApplier(self.profile)
        success_count = 0
        for job in jobs_to_apply:
            result = applier.apply(
                job,
                ats=getattr(args, "ats", "auto"),
                headless=getattr(args, "headless", False),
                delay=getattr(args, "delay", 30),
            )
            if result == "Applied":
                success_count += 1
                job_hash = generate_job_hash(job)
                done_jobs.append(job_hash)
                self.session["done"] = done_jobs
                self._save_session(self.profile.get("profile_name", "default"), self.session)
        console.print(
            f"\n[bold green]✅ Applications completed! {success_count}/{len(jobs_to_apply)} successful[/bold green]"
        )
        return 0

    def apply_to_specific_job(self, job_url: str, args) -> str:
        """Apply to a specific job URL."""
        console.print(f"[bold blue]📝 Applying to specific job: {job_url}[/bold blue]")
        try:
            job = {"url": job_url, "title": "Unknown", "company": "Unknown"}
            applier = JobApplier(self.profile)
            result = applier.apply(
                job,
                ats=getattr(args, "ats", "auto"),
                headless=getattr(args, "headless", False),
                delay=getattr(args, "delay", 30),
            )
            if result == "Applied":
                return "✅ Application successful!"
            else:
                return f"❌ Application failed: {result}"
        except Exception as e:
            return f"❌ Error: {e}"

    def _generate_documents(self, job: Dict) -> tuple:
        """Generate resume and cover letter for a job."""
        from src.document_modifier.document_modifier import customize
        # from src.utils.document_generator import customize  # If needed, import with alias or clarify usage

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
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    jobs.append(row)

            if not jobs:
                console.print("[yellow]No jobs found in CSV file[/yellow]")
                return 1

            console.print(f"[cyan]Found {len(jobs)} jobs in CSV[/cyan]")

            # Use CSV applicator
            profile_name = self.profile.get("profile_name", "default")
            applicator = CSVJobApplicator(profile_name)
            success_count = applicator.apply_to_jobs(jobs, args)

            console.print(
                f"[bold green]✅ CSV applications completed! {success_count}/{len(jobs)} successful[/bold green]"
            )
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
            "6": "auto",
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
            "senior",
            "sr.",
            "sr ",
            "lead",
            "principal",
            "manager",
            "director",
            "supervisor",
            "head of",
            "chief",
            "vp",
            "vice president",
            "experienced",
            "expert",
            "architect",
            "staff engineer",
        ]

        job_title_lower = job_title.lower()
        return any(keyword in job_title_lower for keyword in senior_keywords)
