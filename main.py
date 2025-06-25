"""
Main module - Entry point for the application.
This file provides the main CLI interface for the job automation system.
"""

import sys
import os
from rich.console import Console

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Create console instance for testing
console = Console()

# Dummy sync_playwright for test patching compatibility
sync_playwright = None

# Import the main application
try:
    from src.cli.actions.scraping_actions import ScrapingActions
    from src.cli.actions.dashboard_actions import DashboardActions
    from src.utils.profile_helpers import load_profile
    from src.app import main
except ImportError as e:
    print(f"ImportError: {e}")
    # Fallback: try direct import
    sys.path.insert(0, 'src')
    from src.cli.actions.scraping_actions import ScrapingActions
    from src.cli.actions.dashboard_actions import DashboardActions
    from src.utils.profile_helpers import load_profile
    from src.app import main


if __name__ == "__main__":
    # Check for help argument
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        console.print("[bold blue]AutoJobAgent - Job Automation System[/bold blue]")
        console.print("\n[cyan]Usage:[/cyan]")
        console.print("  python main.py [profile_name]")
        console.print("\n[cyan]Available Profiles:[/cyan]")
        console.print("  - Nirajan (default)")
        console.print("  - default")
        console.print("  - test_profile")
        console.print("\n[cyan]Examples:[/cyan]")
        console.print("  python main.py Nirajan")
        console.print("  python main.py default")
        console.print("  python main.py --help")
        sys.exit(0)
    
    # Get profile name from command line argument
    profile_name = sys.argv[1] if len(sys.argv) > 1 else "Nirajan"
    
    # Load the actual profile
    profile = load_profile(profile_name)
    if not profile:
        console.print(f"[red]❌ Profile '{profile_name}' not found![/red]")
        console.print(f"[yellow]Available profiles: {', '.join(['Nirajan', 'default', 'test_profile'])}[/yellow]")
        console.print("[cyan]Use 'python main.py --help' for usage information[/cyan]")
        sys.exit(1)
    
    # Add profile_name to the profile dict
    profile['profile_name'] = profile_name
    
    console.print(f"[green]✅ Loaded profile: {profile.get('name', profile_name)}[/green]")
    console.print(f"[cyan]Keywords: {profile.get('keywords', [])}[/cyan]")
    
    # Start dashboard automatically after profile load
    dashboard_actions = DashboardActions(profile)
    dashboard_started = dashboard_actions.auto_start_dashboard_action()
    if dashboard_started:
        import webbrowser
        webbrowser.open(f"http://localhost:8002/")
    
    # Create actions with the loaded profile
    actions = ScrapingActions(profile)
    actions.show_scraping_menu(None)