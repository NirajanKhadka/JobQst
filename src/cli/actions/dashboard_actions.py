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
        console.print("[cyan]📊 Modern Dashboard Status[/cyan]")
        self.dashboard_handler.show_status_and_dashboard()

    def shutdown_dashboard_action(self) -> None:
        """Handle shutting down the dashboard."""
        console.print("[yellow]🛑 Shutting down Modern Dashboard...[/yellow]")
        self.dashboard_handler.stop_dashboard()

    def show_status_action(self) -> None:
        """Handle show status action."""
        console.print("[cyan]📊 Modern Dashboard Status[/cyan]")
        self.dashboard_handler.show_status()

    def auto_start_dashboard_action(self) -> bool:
        """Handle auto start dashboard action."""
        success = self.dashboard_handler.auto_start_dashboard()
        if success:
            pass
        else:
            pass
        return success

    def debug_dashboard_action(self) -> None:
        """Handle debug dashboard action."""
        console.print("[cyan]🔍 Debugging Modern Dashboard...[/cyan]")
        self.dashboard_handler.debug_dashboard()

    def display_system_info_action(self) -> None:
        """Handle display system info action."""
        console.print("[cyan]💻 System Information[/cyan]")
        # Show basic system info
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            console.print(f"[cyan]CPU Usage: {cpu_percent:.1f}%[/cyan]")
            console.print(f"[cyan]Memory Usage: {memory.percent:.1f}%[/cyan]")
            console.print(f"[cyan]Profile: {self.profile.get('profile_name', 'Unknown')}[/cyan]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not get system info: {e}[/yellow]")
