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
        """Show the improved main interactive menu with robust options."""
        console.clear()
        console.print(Panel("🤖 AutoJobAgent - Main Menu", style="bold blue"))

        # Show profile info
        self._show_profile_info()

        console.print("\n[bold]Available Actions:[/bold]")
        options = {
            "1": "🔍 Job Scraping (choose site and bot detection method)",
            "2": "📝 Apply to Jobs from Queue",
            "3": "🎯 Apply to Specific Job URL",
            "4": "📂 Apply Jobs from External Source (CSV or Link)",
            "5": "📄 AI Document Generation (Resumes & Cover Letters)",
            "6": "📊 Status & Dashboard",
            "7": "⚙️ System Status & Settings",
            "8": "📋 Process Jobs from Queue (Scrape Details from Links)",
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
