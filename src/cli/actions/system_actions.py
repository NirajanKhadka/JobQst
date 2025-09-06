"""
System Actions for AutoJobAgent CLI.

Contains action processors for different system operations:
- Ollama management
- System status
- Profile management
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel

from ..handlers.system_handler import SystemHandler

console = Console()


class SystemActions:
    """Handles all system action processing."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.system_handler = SystemHandler(profile)

    def system_status_and_settings_action(self) -> None:
        """Handle system status and settings action."""
        self.system_handler.system_status_and_settings()

    def check_ollama_status_action(self) -> bool:
        """Handle check Ollama status action."""
        return self.system_handler.check_ollama_status()

    def show_profile_info_action(self) -> None:
        """Handle show profile info action."""
        self.system_handler.show_profile_info()

    def show_available_profiles_action(self) -> None:
        """Handle show available profiles action."""
        self.system_handler.show_available_profiles()

    def display_system_info_action(self) -> None:
        """Handle display system info action."""
        self.system_handler.display_system_info()

    def show_profile_completeness_action(self) -> None:
        """Handle show profile completeness action."""
        self.system_handler.show_profile_completeness()

