#!/usr/bin/env python3
"""
Application Runner for AutoJobAgent
Handles the main application logic and orchestration.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.panel import Panel

# Import from modular structure
from src.cli.arg_parser import parse_args, validate_args
from src.core.ollama_manager import setup_ollama_if_needed
from src.core.system_utils import setup_signal_handlers, fix_ssl_cert_issue
from src.core import utils
from src.cli.actions.scraping_actions import ScrapingActions
from src.cli.actions.application_actions import ApplicationActions
from src.cli.actions.dashboard_actions import DashboardActions
from src.cli.actions.system_actions import SystemActions

console = Console()


def load_profile(profile_name: str) -> Dict[str, Any]:
    """Load user profile."""
    try:
        profile = utils.load_profile(profile_name)
        console.print(f"[green]✅ Profile loaded: {profile_name}[/green]")
        return profile
    except Exception as e:
        console.print(f"[red]❌ Failed to load profile '{profile_name}': {e}[/red]")
        sys.exit(1)


def show_profile_info(profile: Dict[str, Any]) -> None:
    """Display profile information."""
    console.print(Panel(
        f"[bold cyan]Profile: {profile.get('name', 'Unknown')}[/bold cyan]\n"
        f"Email: {profile.get('email', 'Not set')}\n"
        f"Location: {profile.get('location', 'Not set')}\n"
        f"Resume: {profile.get('resume_path', 'Not set')}",
        title="📋 Profile Information",
        style="bold blue"
    ))


def run_interactive_mode(profile: Dict[str, Any], args) -> int:
    """Run interactive mode."""
    from src.cli.menu.main_menu import MainMenu
    
    console.print(Panel(
        "[bold green]🤖 AutoJobAgent v2.0[/bold green]\n"
        "[cyan]Intelligent Job Application Automation[/cyan]\n"
        "[yellow]Modular Architecture • AI-Powered • Production Ready[/yellow]",
        style="bold blue"
    ))
    
    show_profile_info(profile)
    
    # Setup Ollama if needed
    if not setup_ollama_if_needed():
        console.print("[yellow]⚠️ Ollama setup incomplete, some features may be limited[/yellow]")
    
    # Create menu and run
    menu = MainMenu(profile)
    return menu.run_interactive_mode(args)


def run_scraping_mode(profile: Dict[str, Any], args) -> int:
    """Run scraping mode."""
    console.print("[bold blue]🔍 Running scraping mode...[/bold blue]")
    
    scraping_actions = ScrapingActions(profile)
    
    if args.sites:
        # Multi-site scraping
        sites = args.sites if isinstance(args.sites, list) else [args.sites]
        keywords = args.keywords if isinstance(args.keywords, list) else [args.keywords] if args.keywords else None
        
        for site in sites:
            console.print(f"[cyan]Scraping from {site}...[/cyan]")
            scraping_actions.multi_site_scrape_action(args, "2")
    else:
        # Default scraping
        scraping_actions.automated_scrape_action(args)
    
    return 0


def run_application_mode(profile: Dict[str, Any], args) -> int:
    """Run application mode."""
    console.print("[bold blue]📝 Running application mode...[/bold blue]")
    
    application_actions = ApplicationActions(profile)
    
    if args.url:
        # Apply to specific URL
        application_actions.apply_to_specific_url_action(args)
        return 0
    elif args.csv:
        # Apply from CSV
        application_actions.apply_from_csv_action(args)
        return 0
    else:
        # Apply from queue
        application_actions.apply_from_queue_action(args)
        return 0


def run_dashboard_mode(profile: Dict[str, Any], args) -> int:
    """Run dashboard mode."""
    console.print("[bold blue]📊 Running dashboard mode...[/bold blue]")
    
    dashboard_actions = DashboardActions(profile)
    dashboard_actions.show_status_and_dashboard_action()
    return 0


def run_status_mode(profile: Dict[str, Any], args) -> int:
    """Run status mode."""
    console.print("[bold blue]📈 Running status mode...[/bold blue]")
    
    system_actions = SystemActions(profile)
    system_actions.system_status_and_settings_action()
    return 0


def run_setup_mode(profile: Dict[str, Any], args) -> int:
    """Run setup mode."""
    console.print("[bold blue]⚙️ Running setup mode...[/bold blue]")
    
    system_actions = SystemActions(profile)
    system_actions.system_status_and_settings_action()
    return 0


def run_process_queue_mode(profile: Dict[str, Any], args) -> int:
    """Run process queue mode."""
    console.print("[bold blue]📋 Processing jobs from queue...[/bold blue]")
    
    scraping_actions = ScrapingActions(profile)
    scraping_actions.process_queue_action(args)
    return 0


def main() -> int:
    """Main application entry point."""
    try:
        # Fix SSL issues first
        fix_ssl_cert_issue()
        
        # Setup signal handlers
        setup_signal_handlers()
        
        # Parse arguments
        args = parse_args()
        
        # Load profile
        profile = load_profile(args.profile)
        
        # Run appropriate mode based on action
        if args.action == "interactive":
            return run_interactive_mode(profile, args)
        elif args.action == "scrape":
            return run_scraping_mode(profile, args)
        elif args.action == "apply":
            return run_application_mode(profile, args)
        elif args.action == "apply-url":
            return run_application_mode(profile, args)
        elif args.action == "apply-csv":
            return run_application_mode(profile, args)
        elif args.action == "dashboard":
            return run_dashboard_mode(profile, args)
        elif args.action == "status":
            return run_status_mode(profile, args)
        elif args.action == "setup":
            return run_setup_mode(profile, args)
        elif args.action == "process-queue":
            return run_process_queue_mode(profile, args)
        else:
            console.print(f"[red]❌ Unknown action: {args.action}[/red]")
            return 1
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Operation cancelled by user[/yellow]")
        return 0
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 