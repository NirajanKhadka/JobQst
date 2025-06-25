# Ensure project root is in sys.path for robust imports
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import ssl_fix  # This must be imported first to fix SSL issues
except ImportError as e:
    print('FATAL: Could not import ssl_fix. Make sure ssl_fix.py is in the project root.')
    raise e

import argparse
import signal
import time
import multiprocessing
from rich.console import Console

try:
    from src.core.process_manager import ProcessManager, DashboardManager
except ImportError as e:
    print('FATAL: Import error. Make sure you are running from the project root and all dependencies are installed.')
    raise e

console = Console()

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(_signum, _frame):
    """Handle keyboard interrupt gracefully."""
    global shutdown_requested
    shutdown_requested = True
    console.print("\n[yellow]Shutdown requested. Finishing current operation...[/yellow]")
    console.print("[yellow]Press Ctrl+C again to force quit[/yellow]")

    # Set up a second handler for force quit
    signal.signal(signal.SIGINT, force_quit_handler)

def force_quit_handler(_signum, _frame):
    """Force quit on second Ctrl+C."""
    console.print("\n[red]Force quit requested. Exiting immediately...[/red]")
    sys.exit(1)

# Set up signal handler
signal.signal(signal.SIGINT, signal_handler)

def parse_args():
    parser = argparse.ArgumentParser(
        description="AutoJobAgent - Automated job application tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/app.py Nirajan
        """
    )
    parser.add_argument("profile", help="Profile name to use (folder name in /profiles)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()

# Example subsystem runner stubs (to be replaced with real logic)
def run_scraping_subsystem(profile_name, queue, shutdown_event):
    console.print(f"[{os.getpid()}] Scraping subsystem started for {profile_name}")
    while not shutdown_event.is_set():
        # Simulate scraping work by sleeping
        time.sleep(10)
    console.print(f"[{os.getpid()}] Scraping subsystem stopped.")


def run_ats_subsystem(profile_name, queue, shutdown_event):
    console.print(f"[{os.getpid()}] ATS subsystem started for {profile_name}")
    while not shutdown_event.is_set():
        # Simulate ATS work by sleeping
        time.sleep(10)
    console.print(f"[{os.getpid()}] ATS subsystem stopped.")


def run_docgen_subsystem(profile_name, queue, shutdown_event):
    console.print(f"[{os.getpid()}] Docgen subsystem started for {profile_name}")
    while not shutdown_event.is_set():
        # Simulate document generation by sleeping
        time.sleep(10)
    console.print(f"[{os.getpid()}] Docgen subsystem stopped.")


def main():
    """Main entry point for the application."""
    args = parse_args()
    profile = {"profile_name": args.profile}

    # The ProcessManager now handles initialization of single-run components
    pm = ProcessManager(profile)

    try:
        # The DashboardManager ensures the dashboard is started only once by the main process.
        if multiprocessing.current_process().name == 'MainProcess':
            DashboardManager.start(verbose=args.verbose)

        # Start background processes
        pm.start_process('scraping', run_scraping_subsystem)
        pm.start_process('ats', run_ats_subsystem)
        pm.start_process('docgen', run_docgen_subsystem)

        # The main process can now focus on its primary role (e.g., monitoring)
        console.print("[bold cyan]Main process is running. Subsystems are in the background.[/bold cyan]")
        console.print("[yellow]Press Ctrl+C to shut down all processes.[/yellow]")
        
        # Keep the main process alive to monitor subprocesses
        while not shutdown_requested:
            pm.monitor_processes()
            # Check for messages from subprocesses if needed
            for name, queue in list(pm.queues.items()):
                while not queue.empty():
                    message = queue.get_nowait()
                    console.print(f"[dim]Message from {name}: {message}[/dim]")
            time.sleep(5)

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutdown requested by user.[/yellow]")
    finally:
        pm.shutdown_all()
        console.print("[bold red]Application shut down.[/bold red]")
    return 0


if __name__ == "__main__":
    # This check is crucial for multiprocessing on Windows
    if 'win' in sys.platform and multiprocessing.get_start_method() != 'spawn':
        multiprocessing.set_start_method('spawn', force=True)
        
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Application interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
