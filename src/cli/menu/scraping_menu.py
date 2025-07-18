"""
Scraping Menu for AutoJobAgent CLI.

Handles the scraping-specific menu system.
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel

from ..actions.scraping_actions import ScrapingActions

console = Console()


class ScrapingMenu:
    """Handles the scraping menu."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.scraping_actions = ScrapingActions(profile)

    def show_menu(self, args) -> None:
        """Show the scraping menu."""
        self.scraping_actions.show_scraping_menu(args)
