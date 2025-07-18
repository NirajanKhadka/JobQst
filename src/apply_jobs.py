#!/usr/bin/env python3
"""
Job Application CLI
Simple command-line interface for automated job applications.
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ats.enhanced_universal_applier import EnhancedUniversalApplier, apply_to_jobs_from_database
from src.core.job_database import get_job_db
from src.utils.profile_helpers import load_profile

console = Console()


def display_welcome():
    """Display welcome message."""
    console.print(Panel.fit("🚀 AutoJobAgent - Job Application System", style="bold blue"))
    console.print(
        "[cyan]Automatically apply to jobs with smart form filling and ATS detection[/cyan]"
    )
    console.print(
        "[yellow]Supports: Workday, Greenhouse, iCIMS, Lever, BambooHR, and generic sites[/yellow]"
    )


def get_available_jobs(profile_name: str) -> list:
    """Get available jobs from database."""
    db = get_job_db(profile_name)
    all_jobs = db.get_all_jobs()

    # Filter for jobs that haven't been applied to
    unprocessed_jobs = [job for job in all_jobs if not job.get("application_status")]
    return unprocessed_jobs


def display_job_preview(jobs: list, max_display: int = 10):
    """Display preview of jobs to apply to."""
    if not jobs:
        console.print("[yellow]⚠️ No jobs available for application[/yellow]")
        return

    console.print(f"\n[bold]📋 Available Jobs ({len(jobs)} total)[/bold]")

    table = Table()
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Title", style="green", max_width=30)
    table.add_column("Company", style="yellow", max_width=25)
    table.add_column("Location", style="blue", max_width=20)
    table.add_column("ATS", style="magenta", width=12)

    for i, job in enumerate(jobs[:max_display], 1):
        from src.ats.ats_utils import detect_ats_system

        ats = detect_ats_system(job.get("url", ""))

        table.add_row(
            str(i),
            (
                job.get("title", "Unknown")[:27] + "..."
                if len(job.get("title", "")) > 30
                else job.get("title", "Unknown")
            ),
            (
                job.get("company", "Unknown")[:22] + "..."
                if len(job.get("company", "")) > 25
                else job.get("company", "Unknown")
            ),
            (
                job.get("location", "Unknown")[:17] + "..."
                if len(job.get("location", "")) > 20
                else job.get("location", "Unknown")
            ),
            ats if ats != "unknown" else "Generic",
        )

    console.print(table)

    if len(jobs) > max_display:
        console.print(f"[dim]... and {len(jobs) - max_display} more jobs[/dim]")


def check_profile_setup(profile_name: str) -> bool:
    """Check if profile is properly set up for applications."""
    profile = load_profile(profile_name)
    if not profile:
        console.print(f"[red]❌ Profile '{profile_name}' not found![/red]")
        return False

    # Check required fields
    required_fields = ["name", "email"]
    missing_fields = [field for field in required_fields if not profile.get(field)]

    if missing_fields:
        console.print(f"[red]❌ Missing required profile fields: {', '.join(missing_fields)}[/red]")
        console.print(
            "[yellow]💡 Please update your profile in profiles/{profile_name}/profile.json[/yellow]"
        )
        return False

    # Check for resume
    applier = EnhancedUniversalApplier(profile_name)
    if not applier.resume_path:
        console.print(
            "[yellow]⚠️ No resume found. Please add resume.pdf to your profile folder[/yellow]"
        )
        console.print(f"[cyan]📁 Expected location: profiles/{profile_name}/resume.pdf[/cyan]")
        return Confirm.ask("Continue without resume?")

    console.print(f"[green]✅ Profile setup looks good![/green]")
    console.print(f"[cyan]📄 Resume: {applier.resume_path}[/cyan]")
    if applier.cover_letter_path:
        console.print(f"[cyan]📄 Cover Letter: {applier.cover_letter_path}[/cyan]")

    return True


async def run_application_session():
    """Run interactive application session."""
    display_welcome()

    # Get profile name
    profile_name = Prompt.ask("[cyan]Enter profile name", default="Nirajan")

    # Check profile setup
    if not check_profile_setup(profile_name):
        return

    # Get available jobs
    console.print("[cyan]🔍 Loading available jobs...[/cyan]")
    jobs = get_available_jobs(profile_name)

    if not jobs:
        console.print("[yellow]⚠️ No unprocessed jobs found in database[/yellow]")
        console.print(
            "[cyan]💡 Run the scraper first to find jobs: python main.py Nirajan --action scrape[/cyan]"
        )
        return

    # Display job preview
    display_job_preview(jobs)

    # Get application preferences
    max_applications = int(
        Prompt.ask(
            "[cyan]How many jobs to apply to?", default="5", choices=[str(i) for i in range(1, 21)]
        )
    )

    headless = Confirm.ask("[cyan]Run browser in headless mode? (recommended)", default=True)

    # Confirm before starting
    console.print(f"\n[bold]📋 Application Summary:[/bold]")
    console.print(f"[cyan]Profile: {profile_name}[/cyan]")
    console.print(f"[cyan]Jobs to apply: {min(max_applications, len(jobs))}[/cyan]")
    console.print(f"[cyan]Browser mode: {'Headless' if headless else 'Visible'}[/cyan]")

    if not Confirm.ask("\n[bold]Start applying to jobs?[/bold]"):
        console.print("[yellow]Application cancelled[/yellow]")
        return

    # Run applications
    console.print("\n[bold blue]🚀 Starting application process...[/bold blue]")

    try:
        applier = EnhancedUniversalApplier(profile_name)
        applier.headless = headless

        summary = await applier.apply_to_multiple_jobs(jobs, max_applications)

        # Final summary
        console.print("\n[bold green]🎉 Application session completed![/bold green]")

        if summary["manual_required"] > 0:
            console.print(
                f"\n[yellow]📝 {summary['manual_required']} applications need manual completion[/yellow]"
            )
            console.print("[cyan]💡 Check the browser windows that opened for manual steps[/cyan]")

        if summary["successful"] > 0:
            console.print(
                f"\n[green]✅ Successfully applied to {summary['successful']} jobs![/green]"
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Application process interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error during application process: {e}[/red]")


async def quick_apply_mode():
    """Quick apply mode - apply to top 5 jobs immediately."""
    console.print("[bold blue]⚡ Quick Apply Mode[/bold blue]")

    profile_name = "Nirajan"  # Default profile

    if not check_profile_setup(profile_name):
        return

    jobs = get_available_jobs(profile_name)
    if not jobs:
        console.print("[yellow]⚠️ No jobs available for quick apply[/yellow]")
        return

    console.print(f"[cyan]🚀 Applying to top 5 jobs for {profile_name}...[/cyan]")

    try:
        summary = await apply_to_jobs_from_database(profile_name, max_applications=5)
        console.print(
            f"[green]✅ Quick apply completed! Applied to {summary['successful']} jobs[/green]"
        )
    except Exception as e:
        console.print(f"[red]❌ Quick apply failed: {e}[/red]")


def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--quick":
            asyncio.run(quick_apply_mode())
        elif sys.argv[1] == "--help":
            console.print("[bold]AutoJobAgent Application CLI[/bold]")
            console.print("[cyan]Usage:[/cyan]")
            console.print("  python apply_jobs.py           # Interactive mode")
            console.print("  python apply_jobs.py --quick   # Quick apply to 5 jobs")
            console.print("  python apply_jobs.py --help    # Show this help")
        else:
            console.print(f"[red]Unknown argument: {sys.argv[1]}[/red]")
            console.print("Use --help for usage information")
    else:
        asyncio.run(run_application_session())


if __name__ == "__main__":
    main()
