#!/usr/bin/env python3
"""
Dashboard Manager
Handles automatic dashboard startup, process management, and port monitoring.
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

console = Console()

class DashboardManager:
    """Manages dashboard lifecycle and auto-start functionality."""
    
    def __init__(self, port: int = 8002):
        self.port = port
        self.dashboard_url = f"http://localhost:{port}"
        self.pid_file = Path("dashboard.pid")
        self.dashboard_process: Optional[subprocess.Popen] = None
        
    def kill_existing_dashboard(self) -> bool:
        """Kill any existing dashboard process on the specified port."""
        console.print(f"[yellow]🔍 Checking for existing dashboard on port {self.port}...[/yellow]")
        
        try:
            # Check if port is in use
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    connections = proc.info['connections']
                    for conn in connections:
                        if conn.laddr.port == self.port:
                            console.print(f"[red]⚠️ Found process {proc.info['name']} (PID: {proc.info['pid']}) using port {self.port}[/red]")
                            proc.terminate()
                            proc.wait(timeout=5)
                            console.print(f"[green]✅ Killed existing process on port {self.port}[/green]")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    continue
                    
            # Check PID file
            if self.pid_file.exists():
                try:
                    pid = int(self.pid_file.read_text().strip())
                    if psutil.pid_exists(pid):
                        console.print(f"[red]⚠️ Found dashboard PID file with running process {pid}[/red]")
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(2)
                        console.print(f"[green]✅ Killed dashboard process from PID file[/green]")
                        return True
                except (ValueError, ProcessLookupError):
                    pass
                    
            console.print(f"[green]✅ No existing dashboard found on port {self.port}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error killing existing dashboard: {e}[/red]")
            return False
    
    def start_dashboard(self) -> bool:
        """Start the dashboard server."""
        console.print(f"[blue]🚀 Starting dashboard on port {self.port}...[/blue]")
        
        try:
            # Kill any existing dashboard first
            if not self.kill_existing_dashboard():
                return False
            
            # Start dashboard process
            dashboard_script = Path("src/dashboard/api.py")
            if not dashboard_script.exists():
                console.print(f"[red]❌ Dashboard script not found: {dashboard_script}[/red]")
                return False
                
            self.dashboard_process = subprocess.Popen([
                sys.executable, str(dashboard_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Save PID
            self.pid_file.write_text(str(self.dashboard_process.pid))
            
            # Wait for dashboard to start
            console.print("[yellow]⏳ Waiting for dashboard to start...[/yellow]")
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"{self.dashboard_url}/api/health", timeout=2)
                    if response.status_code == 200:
                        console.print(f"[green]✅ Dashboard started successfully on {self.dashboard_url}[/green]")
                        return True
                except requests.RequestException:
                    pass
                time.sleep(1)
                
            console.print(f"[red]❌ Dashboard failed to start on port {self.port}[/red]")
            return False
            
        except Exception as e:
            console.print(f"[red]❌ Error starting dashboard: {e}[/red]")
            return False
    
    def check_dashboard_status(self) -> Dict[str, Any]:
        """Check dashboard status and return health information."""
        status = {
            "running": False,
            "port": self.port,
            "url": self.dashboard_url,
            "pid": None,
            "health": "unknown"
        }
        
        try:
            # Check if process is running
            if self.dashboard_process and self.dashboard_process.poll() is None:
                status["running"] = True
                status["pid"] = self.dashboard_process.pid
                
            # Check if port is responding
            response = requests.get(f"{self.dashboard_url}/api/health", timeout=5)
            if response.status_code == 200:
                status["health"] = "healthy"
            else:
                status["health"] = "unhealthy"
                
        except requests.RequestException:
            status["health"] = "unreachable"
        except Exception as e:
            status["health"] = f"error: {e}"
            
        return status
    
    def stop_dashboard(self) -> bool:
        """Stop the dashboard server."""
        console.print(f"[yellow]🛑 Stopping dashboard on port {self.port}...[/yellow]")
        
        try:
            if self.dashboard_process:
                self.dashboard_process.terminate()
                self.dashboard_process.wait(timeout=5)
                console.print(f"[green]✅ Dashboard stopped successfully[/green]")
                
            if self.pid_file.exists():
                self.pid_file.unlink()
                
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error stopping dashboard: {e}[/red]")
            return False
    
    def restart_dashboard(self) -> bool:
        """Restart the dashboard server."""
        console.print("[blue]🔄 Restarting dashboard...[/blue]")
        
        self.stop_dashboard()
        time.sleep(2)
        return self.start_dashboard()


def auto_start_dashboard(port: int = 8002) -> DashboardManager:
    """
    Auto-start dashboard with process management.
    
    Args:
        port: Dashboard port (default: 8002)
        
    Returns:
        DashboardManager instance
    """
    manager = DashboardManager(port)
    
    console.print(Panel(
        f"[bold blue]🤖 AutoJobAgent Dashboard Manager[/bold blue]\n"
        f"[cyan]Port: {port}[/cyan]\n"
        f"[cyan]URL: http://localhost:{port}[/cyan]",
        style="bold blue"
    ))
    
    if manager.start_dashboard():
        console.print("[green]✅ Dashboard auto-start completed successfully[/green]")
    else:
        console.print("[red]❌ Dashboard auto-start failed[/red]")
        
    return manager


if __name__ == "__main__":
    # Test dashboard manager
    manager = auto_start_dashboard()
    
    # Show status
    status = manager.check_dashboard_status()
    console.print(f"[cyan]Dashboard Status: {status}[/cyan]")
    
    input("Press Enter to stop dashboard...")
    manager.stop_dashboard() 