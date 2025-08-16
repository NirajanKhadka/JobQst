#!/usr/bin/env python3
"""
Unified Dashboard Manager for AutoJobAgent
Consolidates all dashboard functionality with improved performance and features.
"""

import subprocess
import sys
import time
import os
import threading
import requests
from pathlib import Path
from typing import Dict, List, Optional, Literal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class DashboardManager:
    """Unified dashboard manager with consolidated functionality and singleton pattern."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DashboardManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.processes = {}
            self.dashboard_configs = {
                "modern": {
                    "name": "Modern Dashboard",
                    "description": "Clean, utility-focused design with improved performance",
                    "port": 8501,
                    "script": "src/dashboard/unified_dashboard.py",
                    "features": [
                        "Real-time metrics",
                        "Improved filtering", 
                        "Clean charts",
                        "Document generation",
                        "60s refresh",
                    ],
                },
                "streamlit": {
                    "name": "Streamlit Dashboard",
                    "description": "Feature-rich dashboard with comprehensive analytics",
                    "port": 8502,
                    "script": "src/dashboard/unified_dashboard.py",
                    "features": ["Comprehensive analytics", "Multiple chart types", "Document generation", "30s refresh"],
                },
                "simple": {
                    "name": "Simple HTTP Dashboard",
                    "description": "Lightweight, reliable fallback dashboard",
                    "port": 8503,
                    "script": "src/dashboard/simple_dashboard.py",
                    "features": ["Lightweight", "Fast loading", "Basic metrics"],
                },
            }
            self._initialized = True

    def get_dashboard_info(self, dashboard_type: str) -> Optional[Dict]:
        """Get information about a specific dashboard type."""
        return self.dashboard_configs.get(dashboard_type)

    def list_dashboards(self) -> None:
        """List all available dashboards with their features."""
        table = Table(title="Available Dashboards")
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Name", style="green")
        table.add_column("Port", style="yellow")
        table.add_column("Features", style="blue")
        table.add_column("Status", style="red")

        for dash_type, config in self.dashboard_configs.items():
            status = "Running" if self.is_dashboard_running(config["port"]) else "Stopped"
            features = (
                ", ".join(config["features"][:2]) + "..."
                if len(config["features"]) > 2
                else ", ".join(config["features"])
            )

            table.add_row(dash_type, config["name"], str(config["port"]), features, status)

        console.print(table)

    def is_dashboard_running(self, port: int) -> bool:
        """Check if a dashboard is running on the specified port."""
        try:
            response = requests.get(f"http://localhost:{port}/api/health", timeout=1)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def start_dashboard(self, dashboard_type: str = "modern", verbose: bool = False, profile_name: str = "Nirajan") -> bool:
        """Start a specific dashboard type."""
        config = self.get_dashboard_info(dashboard_type)
        if not config:
            console.print(f"[red]Unknown dashboard type: {dashboard_type}[/red]")
            return False

        if self.is_dashboard_running(config["port"]):
            console.print(
                f"[yellow]{config['name']} already running on port {config['port']}[/yellow]"
            )
            return True

        script_path = Path(config["script"])
        if not script_path.exists():
            console.print(f"[red]Dashboard script not found: {script_path}[/red]")
            return False

        console.print(f"[green]Starting {config['name']}...[/green]")
        console.print(f"[cyan]URL: http://localhost:{config['port']}[/cyan]")
        console.print(f"[cyan]Features: {', '.join(config['features'])}[/cyan]")

        try:
            # Start the dashboard process
            if dashboard_type == "modern":
                cmd = [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(script_path),
                    "--server.port",
                    str(config["port"]),
                    "--server.headless",
                    "true",
                    "--",
                    "--profile",
                    profile_name,
                ]
            else:
                cmd = [sys.executable, str(script_path)]

            stdout = None if verbose else subprocess.DEVNULL
            stderr = None if verbose else subprocess.DEVNULL

            process = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
            self.processes[dashboard_type] = process

            # Wait for the dashboard to start
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Starting dashboard...", total=None)

                for _ in range(15):  # 15 second timeout
                    if self.is_dashboard_running(config["port"]):
                        progress.update(task, description="Dashboard started successfully!")
                        console.print(
                            f"[green]{config['name']} is now running at http://localhost:{config['port']}[/green]"
                        )
                        return True
                    time.sleep(1)

            console.print(f"[red]Failed to start {config['name']} within timeout[/red]")
            self.stop_dashboard(dashboard_type)
            return False

        except Exception as e:
            console.print(f"[red]Error starting {config['name']}: {e}[/red]")
            return False

    def stop_dashboard(self, dashboard_type: str) -> bool:
        """Stop a specific dashboard."""
        if dashboard_type in self.processes:
            process = self.processes[dashboard_type]
            try:
                process.terminate()
                process.wait(timeout=5)
                console.print(f"[yellow]Stopped {dashboard_type} dashboard[/yellow]")
            except subprocess.TimeoutExpired:
                process.kill()
                console.print(f"[red]Force killed {dashboard_type} dashboard[/red]")
            finally:
                del self.processes[dashboard_type]
            return True
        else:
            console.print(f"[yellow]{dashboard_type} dashboard not running[/yellow]")
            return False

    def stop_all_dashboards(self) -> None:
        """Stop all running dashboards."""
        console.print("[yellow]Stopping all dashboards...[/yellow]")
        for dashboard_type in list(self.processes.keys()):
            self.stop_dashboard(dashboard_type)
        console.print("[green]All dashboards stopped[/green]")

    def restart_dashboard(self, dashboard_type: str) -> bool:
        """Restart a specific dashboard."""
        console.print(f"[yellow]Restarting {dashboard_type} dashboard...[/yellow]")
        self.stop_dashboard(dashboard_type)
        time.sleep(2)
        return self.start_dashboard(dashboard_type)

    def get_dashboard_status(self) -> Dict:
        """Get status of all dashboards."""
        status = {}
        for dash_type, config in self.dashboard_configs.items():
            status[dash_type] = {
                "running": self.is_dashboard_running(config["port"]),
                "port": config["port"],
                "name": config["name"],
            }
        return status

    def show_dashboard_status(self) -> None:
        """Display status of all dashboards."""
        status = self.get_dashboard_status()

        table = Table(title="Dashboard Status")
        table.add_column("Dashboard", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Port", style="yellow")
        table.add_column("URL", style="blue")

        for dash_type, info in status.items():
            status_text = "Running" if info["running"] else "Stopped"
            url = f"http://localhost:{info['port']}" if info["running"] else "N/A"

            table.add_row(info["name"], status_text, str(info["port"]), url)

        console.print(table)

    def start_recommended_dashboard(self) -> bool:
        """Start the recommended dashboard (modern)."""
        console.print(
            Panel(
                "[bold green]Starting Recommended Dashboard[/bold green]\n"
                "[cyan]The Modern Dashboard is recommended for best performance and features.[/cyan]",
                title="Dashboard Selection",
            )
        )
        return self.start_dashboard("modern")

    def interactive_dashboard_selector(self) -> None:
        """Interactive dashboard selection menu."""
        console.print(
            Panel(
                "[bold blue]Dashboard Selection Menu[/bold blue]\n"
                "Choose which dashboard to start:",
                title="AutoJobAgent Dashboard Manager",
            )
        )

        options = []
        for dash_type, config in self.dashboard_configs.items():
            status = "Running" if self.is_dashboard_running(config["port"]) else "Stopped"
            options.append(f"{dash_type}: {config['name']} ({status})")

        for i, option in enumerate(options, 1):
            console.print(f"[cyan]{i}.[/cyan] {option}")

        console.print(f"[cyan]{len(options) + 1}.[/cyan] Show all dashboards")
        console.print(f"[cyan]{len(options) + 2}.[/cyan] Stop all dashboards")
        console.print(f"[cyan]{len(options) + 3}.[/cyan] Exit")

        try:
            choice = input("\nEnter your choice (1-{}): ".format(len(options) + 3))
            choice = int(choice)

            if 1 <= choice <= len(options):
                dash_type = list(self.dashboard_configs.keys())[choice - 1]
                self.start_dashboard(dash_type)
            elif choice == len(options) + 1:
                self.show_dashboard_status()
            elif choice == len(options) + 2:
                self.stop_all_dashboards()
            elif choice == len(options) + 3:
                console.print("[green]Goodbye![/green]")
            else:
                console.print("[red]Invalid choice[/red]")

        except (ValueError, KeyboardInterrupt):
            console.print("[yellow]Exiting...[/yellow]")


def main():
    """Main function for dashboard management."""
    manager = DashboardManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "start":
            dashboard_type = sys.argv[2] if len(sys.argv) > 2 else "modern"
            manager.start_dashboard(dashboard_type)
        elif command == "stop":
            dashboard_type = sys.argv[2] if len(sys.argv) > 2 else None
            if dashboard_type:
                manager.stop_dashboard(dashboard_type)
            else:
                manager.stop_all_dashboards()
        elif command == "status":
            manager.show_dashboard_status()
        elif command == "list":
            manager.list_dashboards()
        elif command == "restart":
            dashboard_type = sys.argv[2] if len(sys.argv) > 2 else "modern"
            manager.restart_dashboard(dashboard_type)
        else:
            console.print("[red]Unknown command. Use: start, stop, status, list, restart[/red]")
    else:
        # Interactive mode
        manager.interactive_dashboard_selector()


if __name__ == "__main__":
    main()
