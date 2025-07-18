"""
System Menu for AutoJobAgent CLI.

Handles the system-specific menu system.
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel

from ..actions.system_actions import SystemActions

console = Console()


class SystemMenu:
    """Handles the system menu."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.system_actions = SystemActions(profile)

    def show_menu(self, args) -> None:
        """Show the system menu."""
        console.print(Panel("⚙️ System Menu", style="bold blue"))
        # Implementation for system menu
        pass
