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

# DashboardManager removed - using direct streamlit commands
import psutil

logger = logging.getLogger(__name__)
console = Console()

dash_logger = logging.getLogger("dashboard_orchestrator")
dash_logger.setLevel(logging.INFO)
d_handler = logging.FileHandler("logs/dashboard_orchestrator.log")
d_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
d_handler.setFormatter(d_formatter)
if not dash_logger.hasHandlers():
    dash_logger.addHandler(d_handler)


class DashboardOrchestrator:
    """Orchestrates dashboard sessions, wraps DashboardHandler, and logs actions."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.handler = DashboardHandler(profile)
        self.logger = dash_logger

    def log(self, message, level="INFO"):
        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.info(message)

    def show_status_and_dashboard(self):
        self.log(
            f"Showing status and dashboard for profile: {self.profile.get('profile_name', 'Unknown')}",
            "INFO",
        )
        try:
            self.handler.show_status_and_dashboard()
            self.log("Status and dashboard displayed.", "INFO")
        except Exception as e:
            self.log(f"Dashboard display failed: {e}", "ERROR")
            raise


class DashboardHandler:
    """Handles Modern Dashboard and status operations."""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.session = {}
        self.port = 8501  # Modern Dashboard port
        # Dashboard manager removed - using direct streamlit commands

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
        dashboard_running = self._is_dashboard_running()

        if dashboard_running:
            console.print(
                f"[green]✅ Clean Dashboard: Running on http://localhost:{self.port}[/green]"
            )
        else:
            console.print(f"[red]❌ Clean Dashboard: Not running[/red]")

        # System metrics
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            console.print(f"[cyan]CPU Usage: {cpu_percent:.1f}%[/cyan]")
            console.print(f"[cyan]Memory Usage: {memory.percent:.1f}%[/cyan]")

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not get system metrics: {e}[/yellow]")

    def _is_dashboard_running(self) -> bool:
        """Check if dashboard is running on the port."""
        try:
            import requests

            response = requests.get(f"http://localhost:{self.port}", timeout=2)
            return response.status_code == 200
        except (requests.RequestException, OSError, TimeoutError):
            return False

    def auto_start_dashboard(self) -> bool:
        """Automatically start the available dashboard."""
        console.print("[cyan]🚀 Starting Dashboard...[/cyan]")

        try:
            # Check if already running
            if self._is_dashboard_running():
                console.print("[yellow]⚠️ Dashboard already running![/yellow]")
                console.print(f"[cyan]🌐 Dashboard URL: http://localhost:{self.port}[/cyan]")
                webbrowser.open(f"http://localhost:{self.port}")
                return True

            # Check for available dashboard types
            dash_app_path = Path("src/dashboard/dash_app/app.py")

            if dash_app_path.exists():
                # Use Dash dashboard (port 8050 default for Dash)
                self.port = 8050  # Update port for Dash
                python_path = r"C:\Users\Niraj\miniconda3\envs\auto_job\python.exe"
                cmd = [python_path, str(dash_app_path)]
                console.print("[cyan]🚀 Starting Dash Dashboard on port 8050...[/cyan]")
            else:
                console.print("[red]❌ No dashboard found at:[/red]")
                console.print(f"  - {dash_app_path}")
                return False

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd()
            )

            # Wait a moment for startup
            time.sleep(3)

            # Check if it started successfully
            if self._is_dashboard_running():
                console.print("[green]✅ Clean Dashboard started successfully![/green]")
                console.print(f"[cyan]🌐 Dashboard URL: http://localhost:{self.port}[/cyan]")
                console.print("[yellow]💡 Use 'shutdown' action to stop the dashboard.[/yellow]")

                # Auto-open in browser
                webbrowser.open(f"http://localhost:{self.port}")
                return True
            else:
                console.print("[red]❌ Clean Dashboard failed to start.[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Error starting Clean Dashboard: {e}[/red]")
            return False

    def stop_dashboard(self) -> bool:
        """Stop the running Clean Dashboard process."""
        try:
            # Find and kill streamlit processes on our port
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if "streamlit" in proc.info["name"].lower():
                        cmdline = " ".join(proc.info["cmdline"])
                        if str(self.port) in cmdline:
                            proc.kill()
                            console.print("[green]✅ Clean Dashboard stopped successfully[/green]")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            console.print("[yellow]⚠️ No dashboard process found to stop[/yellow]")
            return False
        except Exception as e:
            console.print(f"[red]❌ Error stopping Clean Dashboard: {e}[/red]")
            return False

    def debug_dashboard(self) -> None:
        """Debug Clean Dashboard issues."""
        console.print(Panel("🔧 Clean Dashboard Debug", style="bold blue"))

        # Check if dashboard file exists
        dashboard_path = Path("src/dashboard/unified_dashboard.py")
        if not dashboard_path.exists():
            console.print(
                "[red]❌ Clean dashboard file not found: src/dashboard/unified_dashboard.py[/red]"
            )
            return

        # Check if dashboard components exist
        components_path = Path("src/dashboard/components")
        if not components_path.exists():
            console.print(f"[red]❌ Dashboard components not found: {components_path}[/red]")
            return

        console.print("[green]✅ Clean dashboard files found[/green]")

        # Try to start dashboard
        console.print("[cyan]🔄 Attempting to start Clean Dashboard...[/cyan]")
        if self.auto_start_dashboard():
            console.print("[green]✅ Clean Dashboard debug successful![/green]")
        else:
            console.print("[red]❌ Clean Dashboard debug failed[/red]")

    def show_dashboard_info(self) -> None:
        """Show detailed dashboard information."""
        console.print(Panel("📊 Clean Dashboard Information", style="bold blue"))

        dashboard_running = self._is_dashboard_running()

        table = Table(title="Dashboard Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Running", "✅ Yes" if dashboard_running else "❌ No")
        table.add_row("Port", str(self.port))
        table.add_row("URL", f"http://localhost:{self.port}")
        table.add_row("Type", "Modern Dashboard (Streamlit)")
        table.add_row("Features", "Clean UI, Improved Filtering, Real-time Metrics")

        console.print(table)

        if dashboard_running:
            console.print(f"[green]🌐 Open dashboard: http://localhost:{self.port}[/green]")
        else:
            console.print("[yellow]💡 Dashboard is not currently running[/yellow]")


# Note: DashboardActions class is defined in src/cli/actions/dashboard_actions.py
# This prevents duplicate class definitions and initialization issues
