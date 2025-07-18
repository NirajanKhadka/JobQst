"""
Dashboard Handler for AutoJobAgent CLI.

Handles all dashboard operations including:
- Starting the Modern Dashboard
- Showing status
- System monitoring
"""

import subprocess
import time
import requests
from typing import Dict, Optional
from pathlib import Path
import logging
import json
import os
import webbrowser
import sys
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.utils.job_helpers import generate_job_hash
from src.dashboard.dashboard_manager import DashboardManager
import psutil

logger = logging.getLogger(__name__)
console = Console()


class DashboardHandler:
    """Handles Modern Dashboard and status operations."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.session = {}
        self.port = 8501  # Modern Dashboard port
        self.dashboard_manager = DashboardManager()

    def show_status_and_dashboard(self) -> None:
        """Show system status and launch Modern Dashboard."""
        console.print(Panel("📊 Status & Modern Dashboard", style="bold blue"))

        # Show current status
        self.show_status()

        # Ask if user wants to launch dashboard
        if Prompt.ask("\nLaunch Modern Dashboard?", choices=["y", "n"], default="y") == "y":
            self.auto_start_dashboard()

    def show_status(self) -> None:
        """Show current system status."""
        console.print("[bold cyan]🔍 System Status[/bold cyan]")

        # Profile info
        profile_name = self.profile.get("profile_name", "Unknown")
        keywords = self.profile.get("keywords", [])

        console.print(f"[green]✅ Profile: {profile_name}[/green]")
        console.print(f"[cyan]Keywords: {', '.join(keywords)}[/cyan]")

        # Dashboard status
        dashboard_running = self.dashboard_manager.is_dashboard_running(self.port)

        if dashboard_running:
            console.print(
                f"[green]✅ Modern Dashboard: Running on http://localhost:{self.port}[/green]"
            )
        else:
            console.print(f"[red]❌ Modern Dashboard: Not running[/red]")

        # System metrics
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            console.print(f"[cyan]CPU Usage: {cpu_percent:.1f}%[/cyan]")
            console.print(f"[cyan]Memory Usage: {memory.percent:.1f}%[/cyan]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not get system metrics: {e}[/yellow]")

    def auto_start_dashboard(self) -> bool:
        """Automatically start the Modern Dashboard."""
        console.print(f"[cyan]🚀 Starting Modern Dashboard on port {self.port}...[/cyan]")
        console.print("[cyan]✨ Features: Clean UI • Utility-Focused • High Performance[/cyan]")

        try:
            # Use the Modern Dashboard manager
            success = self.dashboard_manager.start_dashboard("modern")

            if success:
                console.print("[green]✅ Modern Dashboard started successfully![/green]")
                console.print(f"[cyan]🌐 Dashboard URL: http://localhost:{self.port}[/cyan]")
                console.print("[yellow]💡 Use 'shutdown' action to stop the dashboard.[/yellow]")

                # Auto-open in browser
                webbrowser.open(f"http://localhost:{self.port}")
                return True
            else:
                console.print("[red]❌ Modern Dashboard failed to start.[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error starting Modern Dashboard: {e}[/red]")
            return False

    def stop_dashboard(self) -> bool:
        """Stop the running Modern Dashboard process."""
        try:
            self.dashboard_manager.stop_dashboard("modern")
            console.print("[green]✅ Modern Dashboard stopped successfully[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Error stopping Modern Dashboard: {e}[/red]")
            return False

    def debug_dashboard(self) -> None:
        """Debug Modern Dashboard issues."""
        console.print(Panel("🔧 Modern Dashboard Debug", style="bold blue"))

        # Check if dashboard file exists
        dashboard_path = Path("src/dashboard/modern_dashboard.py")
        if not dashboard_path.exists():
            console.print(
                "[red]❌ Modern dashboard file not found: src/dashboard/modern_dashboard.py[/red]"
            )
            return

        # Check if dashboard can be imported
        try:
            from src.dashboard import modern_dashboard

            console.print("[green]✅ Modern dashboard module can be imported[/green]")
        except ImportError as e:
            console.print(f"[red]❌ Dashboard import error: {e}[/red]")
            return

        # Try to start dashboard
        console.print("[cyan]🔄 Attempting to start Modern Dashboard...[/cyan]")
        if self.auto_start_dashboard():
            console.print("[green]✅ Modern Dashboard debug successful![/green]")
        else:
            console.print("[red]❌ Modern Dashboard debug failed[/red]")

    def show_dashboard_info(self) -> None:
        """Show detailed dashboard information."""
        console.print(Panel("📊 Modern Dashboard Information", style="bold blue"))

        dashboard_running = self.dashboard_manager.is_dashboard_running(self.port)

        table = Table(title="Dashboard Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Running", "✅ Yes" if dashboard_running else "❌ No")
        table.add_row("Port", str(self.port))
        table.add_row("URL", f"http://localhost:{self.port}")
        table.add_row("Type", "Modern Dashboard (Streamlit)")
        table.add_row("Features", "Clean UI, Advanced Filtering, Real-time Metrics")

        console.print(table)

        if dashboard_running:
            console.print(f"[green]🌐 Open dashboard: http://localhost:{self.port}[/green]")
        else:
            console.print("[yellow]💡 Dashboard is not currently running[/yellow]")


# Note: DashboardActions class is defined in src/cli/actions/dashboard_actions.py
# This prevents duplicate class definitions and initialization issues
