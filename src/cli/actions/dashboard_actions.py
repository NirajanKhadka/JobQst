"""
Dashboard Actions for AutoJobAgent CLI.

Contains action processors for different dashboard operations:
- Status display
- Dashboard launching
- System monitoring
"""

from typing import Dict
from rich.console import Console
from rich.panel import Panel

from ..handlers.dashboard_handler import DashboardHandler

console = Console()


class DashboardActions:
    """Handles all dashboard action processing."""
    
    def __init__(self, profile: Dict):
        self.profile = profile
        self.dashboard_handler = DashboardHandler(profile)
    
    def show_status_and_dashboard_action(self) -> None:
        """Handle show status and dashboard action."""
        self.dashboard_handler.show_status_and_dashboard()
    
    def shutdown_dashboard_action(self) -> None:
        """Handle shutting down the dashboard."""
        self.dashboard_handler.stop_dashboard()
    
    def show_status_action(self) -> None:
        """Handle show status action."""
        self.dashboard_handler.show_status()
    
    def auto_start_dashboard_action(self) -> bool:
        """Handle auto start dashboard action."""
        return self.dashboard_handler.auto_start_dashboard()
    
    def debug_dashboard_action(self) -> None:
        """Handle debug dashboard action."""
        self.dashboard_handler.debug_dashboard()
    
    def display_system_info_action(self) -> None:
        """Handle display system info action."""
        self.dashboard_handler.display_system_info() 