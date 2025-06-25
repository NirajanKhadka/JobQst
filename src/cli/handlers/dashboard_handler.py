"""
Dashboard Handler for AutoJobAgent CLI.

Handles all dashboard operations including:
- Starting the dashboard
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

from src.utils import utils
import psutil

logger = logging.getLogger(__name__)
console = Console()


class DashboardHandler:
    """Handles dashboard and status operations."""
    
    def __init__(self, profile: Dict):
        self.profile = profile
        self.session = {}
        self.pid_file = Path("dashboard.pid")
        self.port = 8002
    
    def _get_process_by_port(self) -> Optional[psutil.Process]:
        """Find and return a process using the dashboard port."""
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port == self.port and conn.status == 'LISTEN':
                try:
                    return psutil.Process(conn.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        return None
    
    def show_status_and_dashboard(self) -> None:
        """Show system status and launch dashboard."""
        console.print(Panel("📊 Status & Dashboard", style="bold blue"))
        
        # Show current status
        self.show_status()
        
        # Ask if user wants to launch dashboard
        if Prompt.ask("\nLaunch dashboard?", choices=["y", "n"], default="y") == "y":
            self.auto_start_dashboard()
    
    def show_status(self) -> None:
        """Show current system status."""
        console.print("[bold]📊 Current Status:[/bold]")
        
        # Load session data
        scraped_jobs = self.session.get("scraped_jobs", [])
        done_jobs = self.session.get("done", [])
        pending_jobs = [job for job in scraped_jobs if generate_job_hash(job) not in done_jobs]
        
        # Create status table
        table = Table(title="System Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Jobs Scraped", str(len(scraped_jobs)))
        table.add_row("Jobs Applied", str(len(done_jobs)))
        table.add_row("Pending Jobs", str(len(pending_jobs)))
        table.add_row("Success Rate", f"{len(done_jobs)/len(scraped_jobs)*100:.1f}%" if scraped_jobs else "0%")
        
        console.print(table)
        
        # Show recent jobs
        if scraped_jobs:
            console.print("\n[bold]Recent Jobs:[/bold]")
            recent_table = Table()
            recent_table.add_column("Title", style="cyan")
            recent_table.add_column("Company", style="magenta")
            recent_table.add_column("Status", style="green")
            
            for job in scraped_jobs[-5:]:  # Show last 5 jobs
                job_hash = generate_job_hash(job)
                status = "✅ Applied" if job_hash in done_jobs else "⏳ Pending"
                recent_table.add_row(
                    job.get('title', 'Unknown')[:30],
                    job.get('company', 'Unknown')[:20],
                    status
                )
            
            console.print(recent_table)
    
    def auto_start_dashboard(self) -> bool:
        """Automatically start the dashboard, killing any existing process on the port."""
        console.print(f"[cyan]🚀 Starting dashboard on port {self.port}...[/cyan]")

        existing_process = self._get_process_by_port()
        if existing_process:
            console.print(f"[yellow]⚠️ Port {self.port} is already in use by PID {existing_process.pid}. Terminating it...[/yellow]")
            try:
                existing_process.terminate()
                existing_process.wait(timeout=3)
                console.print(f"[green]✅ Process {existing_process.pid} terminated.[/green]")
            except psutil.TimeoutExpired:
                console.print(f"[red]❌ Failed to terminate process {existing_process.pid}. Killing it...[/red]")
                existing_process.kill()
                console.print(f"[green]✅ Process {existing_process.pid} killed.[/green]")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                console.print(f"[yellow]⚠️ Could not terminate process {existing_process.pid}: {e}[/yellow]")

        try:
            dashboard_process = subprocess.Popen(
                ["python", "-m", "uvicorn", "src.dashboard.api:app", "--host", "0.0.0.0", "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.pid_file.write_text(str(dashboard_process.pid))
            
            console.print("[cyan]⏳ Waiting for dashboard to start...[/cyan]")
            for _ in range(15):
                time.sleep(1)
                if self._check_dashboard_running():
                    console.print("[green]✅ Dashboard started successfully![/green]")
                    console.print(f"[cyan]🌐 Dashboard URL: http://localhost:{self.port}[/cyan]")
                    console.print("[yellow]💡 Use 'shutdown' action to stop the dashboard.[/yellow]")
                    return True
            
            console.print("[red]❌ Dashboard failed to start in time.[/red]")
            self.stop_dashboard()
            return False
            
        except Exception as e:
            console.print(f"[red]❌ Error starting dashboard: {e}[/red]")
            return False

    def stop_dashboard(self) -> bool:
        """Stop the running dashboard process."""
        if not self.pid_file.exists():
            proc = self._get_process_by_port()
            if proc:
                console.print(f"[yellow]⚠️ No PID file, but found process {proc.pid} on port {self.port}. Terminating it...[/yellow]")
                try:
                    proc.terminate()
                    return True
                except Exception as e:
                    console.print(f"[red]❌ Error stopping process {proc.pid}: {e}[/red]")
                    return False
            console.print("[yellow]⚠️ Dashboard is not running (no PID file).[/yellow]")
            return False
        
        try:
            pid = int(self.pid_file.read_text())
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=3)
            console.print(f"[green]✅ Dashboard process {pid} terminated.[/green]")
        except psutil.TimeoutExpired:
            console.print(f"[red]❌ Process {pid} did not terminate gracefully. Killing it...[/red]")
            psutil.Process(pid).kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            console.print(f"[yellow]⚠️ Could not terminate process {pid}. It may have already been stopped.[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Error stopping dashboard: {e}[/red]")
            return False
        finally:
            if self.pid_file.exists():
                self.pid_file.unlink(missing_ok=True)
            
        return True

    def _check_dashboard_running(self) -> bool:
        """Check if dashboard is running."""
        try:
            response = requests.get(f"http://localhost:{self.port}/health", timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def debug_dashboard(self) -> None:
        """Debug dashboard issues."""
        console.print(Panel("🔧 Dashboard Debug", style="bold blue"))
        
        # Check if dashboard files exist
        dashboard_path = Path("src/dashboard/api.py")
        if not dashboard_path.exists():
            console.print("[red]❌ Dashboard file not found: src/dashboard/api.py[/red]")
            return
        
        # Check if required dependencies are installed
        try:
            import fastapi
            import uvicorn
            console.print("[green]✅ FastAPI and Uvicorn are installed[/green]")
        except ImportError as e:
            console.print(f"[red]❌ Missing dependency: {e}[/red]")
            console.print("[yellow]💡 Install with: pip install fastapi uvicorn[/yellow]")
            return
        
        # Check if dashboard can be imported
        try:
            from src.dashboard import api
            console.print("[green]✅ Dashboard module can be imported[/green]")
        except ImportError as e:
            console.print(f"[red]❌ Dashboard import error: {e}[/red]")
            return
        
        # Try to start dashboard
        console.print("[cyan]🔄 Attempting to start dashboard...[/cyan]")
        if self.auto_start_dashboard():
            console.print("[green]✅ Dashboard debug successful![/green]")
        else:
            console.print("[red]❌ Dashboard debug failed[/red]")
    
    def get_system_performance_info(self) -> Dict:
        """Get system performance information."""
        import psutil
        
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # Disk information
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free / (1024**3)  # GB
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'memory_percent': memory_percent,
                'memory_available_gb': memory_available,
                'disk_percent': disk_percent,
                'disk_free_gb': disk_free
            }
        except ImportError:
            console.print("[yellow]⚠️ psutil not available for system monitoring[/yellow]")
            return {}
        except Exception as e:
            console.print(f"[yellow]⚠️ Error getting system info: {e}[/yellow]")
            return {}
    
    def display_system_info(self) -> None:
        """Display system information."""
        console.print(Panel("💻 System Information", style="bold blue"))
        
        # Get performance info
        perf_info = self.get_system_performance_info()
        
        if perf_info:
            table = Table(title="System Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("CPU Usage", f"{perf_info.get('cpu_percent', 0):.1f}%")
            table.add_row("CPU Cores", str(perf_info.get('cpu_count', 0)))
            table.add_row("Memory Usage", f"{perf_info.get('memory_percent', 0):.1f}%")
            table.add_row("Available Memory", f"{perf_info.get('memory_available_gb', 0):.1f} GB")
            table.add_row("Disk Usage", f"{perf_info.get('disk_percent', 0):.1f}%")
            table.add_row("Free Disk Space", f"{perf_info.get('disk_free_gb', 0):.1f} GB")
            
            console.print(table)
        else:
            console.print("[yellow]System information not available[/yellow]")
        
        # Show profile information
        console.print(f"\n[bold]👤 Profile:[/bold] {self.profile.get('profile_name', 'Unknown')}")
        console.print(f"[bold]📧 Email:[/bold] {self.profile.get('email', 'Not set')}")
        console.print(f"[bold]📱 Phone:[/bold] {self.profile.get('phone', 'Not set')}")
        console.print(f"[bold]📍 Location:[/bold] {self.profile.get('location', 'Not set')}")
        
        # Show keywords
        keywords = self.profile.get('keywords', [])
        if keywords:
            console.print(f"\n[bold]🔍 Keywords:[/bold] {', '.join(keywords[:5])}")
            if len(keywords) > 5:
                console.print(f"[dim]... and {len(keywords) - 5} more[/dim]") 