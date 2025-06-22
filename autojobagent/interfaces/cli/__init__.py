"""
Command-line interface for AutoJobAgent.
"""
import logging
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt, IntPrompt

from ....shared.config import settings
from ....core.models import UserProfile, JobPosting, JobStatus
from ....core.job_application.service import JobApplicationService
from ....shared.browser.manager import BrowserManager

logger = logging.getLogger(__name__)
console = Console()

def display_welcome():
    """Display welcome message."""
    console.print(Panel.fit(
        "[bold blue]AutoJobAgent[/bold blue] - Automated Job Application System\n"
        "[dim]Version 1.0.0[/dim]",
        border_style="blue"
    ))

def display_main_menu() -> str:
    """
    Display the main menu and get user selection.
    
    Returns:
        str: Selected menu option
    """
    console.print("\n[bold]Main Menu[/bold]")
    console.print("1. Apply to new jobs")
    console.print("2. View applications")
    console.print("3. Scrape job listings")
    console.print("4. Manage profile")
    console.print("5. Settings")
    console.print("0. Exit")
    
    return Prompt.ask(
        "\nSelect an option",
        choices=["0", "1", "2", "3", "4", "5"],
        default="0"
    )

def run_cli(profile_name: str):
    """
    Run the command-line interface.
    
    Args:
        profile_name: Name of the profile to use
    """
    display_welcome()
    
    try:
        # Load profile
        profile = UserProfile(
            name=profile_name,
            email=f"{profile_name}@example.com",  # TODO: Load from profile
            location=""
        )
        
        # Initialize services
        app_service = JobApplicationService(profile)
        
        # Main loop
        while True:
            choice = display_main_menu()
            
            if choice == "0":
                console.print("\n[green]Goodbye![/green]")
                break
                
            elif choice == "1":
                handle_apply(app_service)
                
            elif choice == "2":
                handle_view_applications(app_service)
                
            elif choice == "3":
                handle_scrape_jobs(profile)
                
            elif choice == "4":
                handle_manage_profile(profile)
                
            elif choice == "5":
                handle_settings()
                
    except KeyboardInterrupt:
        console.print("\n[red]Operation cancelled by user[/red]")
    except Exception as e:
        logger.exception("An error occurred in the CLI")
        console.print(f"\n[red]Error: {e}[/red]")

def handle_apply(service: JobApplicationService):
    """Handle job application flow."""
    console.print("\n[bold]Apply to Jobs[/bold]")
    console.print("1. Apply to a specific job URL")
    console.print("2. Apply to jobs from CSV")
    console.print("3. Apply to scraped jobs")
    console.print("0. Back to main menu")
    
    choice = Prompt.ask(
        "\nSelect an option",
        choices=["0", "1", "2", "3"],
        default="0"
    )
    
    if choice == "1":
        job_url = Prompt.ask("Enter job URL")
        apply_to_job(service, job_url)
    elif choice == "2":
        csv_path = Prompt.ask("Enter path to CSV file")
        apply_from_csv(service, csv_path)
    elif choice == "3":
        apply_to_scraped_jobs(service)

def apply_to_job(service: JobApplicationService, job_url: str):
    """Apply to a specific job URL."""
    console.print(f"\nApplying to job: {job_url}")
    
    # TODO: Implement job application logic
    with BrowserManager(profile_name=service.profile.name) as browser_manager:
        context = browser_manager.create_context()
        page = context.new_page()
        
        try:
            page.goto(job_url)
            console.print(f"Opened job page: {page.title()}")
            
            # TODO: Extract job details and apply
            console.print("[yellow]Job application flow not yet implemented[/yellow]")
            
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            console.print(f"[red]Error: {e}[/red]")

def apply_from_csv(service: JobApplicationService, csv_path: str):
    """Apply to jobs from a CSV file."""
    console.print(f"\nApplying to jobs from CSV: {csv_path}")
    # TODO: Implement CSV application logic
    console.print("[yellow]CSV application not yet implemented[/yellow]")

def apply_to_scraped_jobs(service: JobApplicationService):
    """Apply to previously scraped jobs."""
    console.print("\nApplying to scraped jobs")
    # TODO: Implement application to scraped jobs
    console.print("[yellow]Scraped jobs application not yet implemented[/yellow]")

def handle_view_applications(service: JobApplicationService):
    """Display application status and history."""
    console.print("\n[bold]Your Applications[/bold]")
    
    # TODO: Load and display applications
    console.print("[yellow]Application history not yet implemented[/yellow]")

def handle_scrape_jobs(profile: UserProfile):
    """Handle job scraping flow."""
    console.print("\n[bold]Scrape Job Listings[/bold]")
    
    query = Prompt.ask("Search query")
    site = Prompt.ask(
        "Site to search",
        choices=["indeed", "linkedin", "workday", "all"],
        default="all"
    )
    limit = IntPrompt.ask("Maximum results", default=10)
    
    console.print(f"\nSearching for '{query}' on {site} (max {limit} results)")
    
    # TODO: Implement job scraping
    console.print("[yellow]Job scraping not yet implemented[/yellow]")

def handle_manage_profile(profile: UserProfile):
    """Manage user profile."""
    console.print("\n[bold]Manage Profile[/bold]")
    console.print(f"Name: {profile.name}")
    console.print(f"Email: {profile.email}")
    console.print(f"Location: {profile.location}")
    
    # TODO: Implement profile management
    console.print("\n[yellow]Profile management not yet implemented[/yellow]")

def handle_settings():
    """Display and modify application settings."""
    console.print("\n[bold]Settings[/bold]")
    
    # TODO: Implement settings management
    console.print("[yellow]Settings management not yet implemented[/yellow]")
