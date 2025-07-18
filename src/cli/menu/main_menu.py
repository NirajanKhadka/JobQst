"""
Main Menu for AutoJobAgent CLI.

Handles the main interactive menu system.
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ..actions.scraping_actions import ScrapingActions
from ..actions.application_actions import ApplicationActions
from ..actions.dashboard_actions import DashboardActions
from ..actions.system_actions import SystemActions
from ..actions.document_actions import DocumentActions

console = Console()


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
        """Show the simplified main interactive menu."""
        console.clear()
        console.print(Panel("🤖 AutoJobAgent - Simplified Menu", style="bold blue"))

        # Show profile info
        self._show_profile_info()

        console.print("\n[bold]Available Actions:[/bold]")
        options = {
            "1": "🔍 Job Scraping (choose site and bot detection method)",
            "2": "📝 Apply to jobs from queue",
            "3": "🎯 Apply to specific job URL",
            "4": "🌐 Apply jobs from external (CSV or link)",
            "5": "� AI Document Generation (Resumes & Cover Letters)",
            "6": "�📊 Status & Dashboard",
            "7": "⚙️ System status & settings",
            "8": "📋 Process jobs from queue (scrape details from links)",
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
        elif choice == "8":  # Process jobs from queue
            self.scraping_actions.process_queue_action(args)
        elif choice == "9":  # Exit
            console.print("[green]Goodbye![green]")
            return False

        # Don't pause after exit
        if choice != "9":
            input("\nPress Enter to continue...")

        return True

    def _show_profile_info(self) -> None:
        """Show current profile information."""
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

    def run_interactive_mode(self, args) -> int:
        """Run the interactive menu mode."""
        while True:
            choice = self.show_interactive_menu()
            if not self.handle_menu_choice(choice, args):
                break

        return 0
