"""
Application Menu for AutoJobAgent CLI.

Handles the application-specific menu system.
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel

from ..actions.application_actions import ApplicationActions

console = Console()


class ApplicationMenu:
    """Handles the application menu."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.application_actions = ApplicationActions(profile)

    def show_menu(self, args) -> None:
        """Show the application menu."""
        console.print(Panel("📝 Application Menu", style="bold blue"))
        # Implementation for application menu
        pass
