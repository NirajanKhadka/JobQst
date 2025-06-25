import multiprocessing
import subprocess
import sys
import time
import requests
from rich.console import Console

console = Console()

class DashboardManager:
    """Manages the lifecycle of the dashboard server."""
    _process = None
    _port = 8002

    @classmethod
    def start(cls, verbose: bool = False) -> bool:
        """Starts the dashboard if it's not already running."""
        if cls.is_running():
            # console.print(f"[cyan]Dashboard already running at http://localhost:{cls._port}[/cyan]")
            return True

        console.print(f"[green]Starting dashboard on port {cls._port}...[/green]")
        try:
            stdout = None if verbose else subprocess.DEVNULL
            stderr = None if verbose else subprocess.DEVNULL
            
            cls._process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "src.dashboard.api:app", "--port", str(cls._port), "--host", "0.0.0.0"],
                stdout=stdout,
                stderr=stderr
            )
            
            # Wait for the server to start
            for _ in range(10):  # 10 seconds timeout
                if cls.is_running():
                    console.print(f"[green]✅ Dashboard started successfully at: http://localhost:{cls._port}[/green]")
                    return True
                time.sleep(1)

            console.print("[red]❌ Dashboard failed to start.[/red]")
            cls.stop()
            return False
        except Exception as e:
            console.print(f"[red]❌ Error starting dashboard: {e}[/red]")
            return False

    @classmethod
    def stop(cls):
        """Stops the dashboard process if it's running."""
        if cls._process:
            try:
                cls._process.terminate()
                cls._process.wait(timeout=5)
                console.print("[yellow]Dashboard stopped.[/yellow]")
            except subprocess.TimeoutExpired:
                cls._process.kill()
                console.print("[red]Dashboard forcefully killed.[/red]")
            except Exception as e:
                console.print(f"[red]Error stopping dashboard: {e}[/red]")
            finally:
                cls._process = None

    @classmethod
    def is_running(cls) -> bool:
        """Checks if the dashboard server is responsive."""
        if cls._process and cls._process.poll() is not None:
            # Process has terminated
            cls._process = None
            return False
            
        try:
            response = requests.get(f"http://localhost:{cls._port}/api/health", timeout=1)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

class ProcessManager:
    """Manages subprocesses for scraping, ATS, document generation."""
    def __init__(self, profile):
        self.processes = {}
        self.queues = {}
        self.shutdown_event = multiprocessing.Event()
        self.profile = profile
        self.is_main_process = multiprocessing.current_process().name == 'MainProcess'

        if self.is_main_process:
            self._initialize_main_process_components()

    def _initialize_main_process_components(self):
        """Initializes components that should only run in the main process."""
        console.print("[blue]Initializing main process components...[/blue]")
        # Centralize health checks and profile loading here to avoid repetition.
        # This addresses the repetitive logging issue.
        from src.core.user_profile_manager import UserProfileManager
        from src.agents.system_health_monitor import SystemHealthMonitor

        # Load profile context once
        UserProfileManager.get_profile(self.profile["profile_name"])
        console.print("[green]✅ Default profile context set.[/green]")

        # Register health checks once
        monitor = SystemHealthMonitor()
        monitor.run_comprehensive_health_check()
        console.print("[green]✅ System health checks performed.[/green]")


    def start_process(self, name, target, args=()):
        if name in self.processes and self.processes[name].is_alive():
            console.print(f"[yellow]Process '{name}' already running.[/yellow]")
            return
        
        queue = multiprocessing.Queue()
        # Pass profile name instead of the whole object if it's not picklable
        all_args = (self.profile["profile_name"], queue, self.shutdown_event) + args
        
        proc = multiprocessing.Process(target=target, args=all_args, name=name)
        proc.start()
        self.processes[name] = proc
        self.queues[name] = queue
        console.print(f"[green]Started process: {name} (PID {proc.pid})[/green]")

    def stop_process(self, name):
        if name in self.processes:
            proc = self.processes.pop(name)
            if proc.is_alive():
                self.shutdown_event.set()
                proc.join(timeout=5)
                if proc.is_alive():
                    proc.terminate()
                    proc.join(timeout=2) # wait for termination
                    if proc.is_alive():
                        proc.kill()
            console.print(f"[red]Stopped process: {name}[/red]")
            if name in self.queues:
                del self.queues[name]

    def monitor_processes(self):
        for name, proc in list(self.processes.items()):
            if not proc.is_alive():
                console.print(f"[red]Process '{name}' exited unexpectedly with code {proc.exitcode}.[/red]")
                del self.processes[name]
                if name in self.queues:
                    del self.queues[name]

    def shutdown_all(self):
        console.print("[yellow]Shutting down all subprocesses...[/yellow]")
        self.shutdown_event.set()
        for name, proc in list(self.processes.items()):
            self.stop_process(name)
        
        if self.is_main_process:
            DashboardManager.stop()
        
        self.processes.clear()
        self.queues.clear()
        console.print("[yellow]All subprocesses shut down.[/yellow]")

# Helper function to access job_db, needed for health check
def get_job_db(profile_name):
    from src.core.job_database import get_job_db as get_db
    return get_db(profile_name)