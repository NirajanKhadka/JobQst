# Fix SSL certificate path before any other imports that might use SSL
import ssl_fix  # This must be imported first to fix SSL issues

import argparse
import signal
import subprocess
import sys
import time
import os
import requests
from pathlib import Path
from typing import Dict, List
import asyncio

from playwright.sync_api import sync_playwright
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

# Core modules
from src.utils.document_generator import customize
from src.core import utils
from ats import detect, get_submitter
from src.ats.csv_applicator import CSVJobApplicator
from src.core.job_database import ModernJobDatabase, get_job_db

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
  python main.py Nirajan                           # Interactive mode
  python main.py Nirajan --action scrape           # Scrape jobs only
  python main.py Nirajan --action apply            # Apply to scraped jobs
  python main.py Nirajan --action dashboard        # Launch dashboard
  python main.py Nirajan --action status           # Show status
        """
    )

    # Profile is required
    parser.add_argument("profile", help="Profile name to use (folder name in /profiles)")

    # Action commands
    parser.add_argument("--action",
                       choices=["interactive", "scrape", "apply", "apply-url", "apply-csv", "dashboard", "status", "setup"],
                       default="interactive",
                       help="Action to perform")

    # Scraping options
    parser.add_argument("--sites",
                       help="Comma-separated list of sites to scrape (eluta, indeed, workday)")
    parser.add_argument("--keywords",
                       help="Comma-separated list of keywords to search")
    parser.add_argument("--batch", type=int,
                       help="Number of jobs to process in each batch")

    # Application options
    parser.add_argument("--url", help="Specific job URL to apply to (use with --action apply-url)")
    parser.add_argument("--csv", help="CSV file path for batch applications (use with --action apply-csv)")
    parser.add_argument("--ats", choices=["workday", "icims", "greenhouse", "lever", "bamboohr", "auto", "manual"],
                       help="ATS system to target (or 'auto' to detect)")

    # General options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--allow-senior", action="store_true", help="Don't skip senior job postings")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--delay", type=int, default=30, help="Delay between applications in seconds")
    parser.add_argument("--preview", action="store_true", help="Preview jobs without applying")

    return parser.parse_args()

def check_ollama_installation() -> bool:
    """Check if Ollama is installed on the system."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=True if os.name == 'nt' else False
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def install_ollama_guide():
    """Display Ollama installation guide."""
    console.print("\n[bold red]❌ Ollama is not installed[/bold red]")
    console.print("\n[bold cyan]📥 Ollama Installation Guide:[/bold cyan]")

    if os.name == 'nt':  # Windows
        console.print("1. Visit: [link]https://ollama.ai[/link]")
        console.print("2. Download the Windows installer")
        console.print("3. Run the installer as Administrator")
        console.print("4. Restart your terminal/command prompt")
        console.print("5. Run: [bold]ollama --version[/bold] to verify")
    else:  # Linux/macOS
        console.print("1. Run: [bold]curl -fsSL https://ollama.ai/install.sh | sh[/bold]")
        console.print("2. Or visit: [link]https://ollama.ai[/link] for manual installation")

    console.print("\n[yellow]💡 After installation, run this command again[/yellow]")


def check_ollama_service() -> bool:
    """Check if Ollama service is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def start_ollama_service() -> bool:
    """Start Ollama service."""
    console.print("[cyan]🚀 Starting Ollama service...[/cyan]")

    try:
        if os.name == 'nt':  # Windows
            # On Windows, try to start ollama serve
            subprocess.Popen(
                ["ollama", "serve"],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
            )
        else:  # Linux/macOS
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        # Wait for service to start
        console.print("[cyan]⏳ Waiting for Ollama service to start...[/cyan]")
        for _ in range(10):  # Wait up to 10 seconds
            time.sleep(1)
            if check_ollama_service():
                console.print("[green]✅ Ollama service started successfully[/green]")
                return True

        console.print("[red]❌ Ollama service failed to start[/red]")
        return False

    except Exception as e:
        console.print(f"[red]❌ Error starting Ollama service: {e}[/red]")
        return False


def check_mistral_model() -> bool:
    """Check if Mistral model is available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any("mistral" in model.get("name", "") for model in models)
    except requests.exceptions.RequestException:
        pass
    return False


def download_mistral_model() -> bool:
    """Download Mistral model."""
    console.print("[cyan]📥 Downloading Mistral model (this may take a few minutes)...[/cyan]")

    try:
        result = subprocess.run(
            ["ollama", "pull", "mistral"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout for model download
            shell=True if os.name == 'nt' else False
        )

        if result.returncode == 0:
            console.print("[green]✅ Mistral model downloaded successfully[/green]")
            return True
        else:
            console.print(f"[red]❌ Failed to download Mistral model: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Timeout downloading Mistral model[/red]")
        console.print("[yellow]💡 Try manually: ollama pull mistral[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Error downloading Mistral model: {e}[/red]")
        return False


def check_ollama_status() -> bool:
    """Check if Ollama is properly set up and running."""
    console.print("[cyan]🔍 Checking Ollama status...[/cyan]")

    # Step 1: Check if Ollama is installed
    if not check_ollama_installation():
        install_ollama_guide()
        return False

    console.print("[green]✅ Ollama is installed[/green]")

    # Step 2: Check if Ollama service is running
    if not check_ollama_service():
        console.print("[yellow]⚠️ Ollama service not running, attempting to start...[/yellow]")
        if not start_ollama_service():
            console.print("[red]❌ Failed to start Ollama service[/red]")
            console.print("[yellow]💡 Try manually: ollama serve[/yellow]")
            return False
    else:
        console.print("[green]✅ Ollama service is running[/green]")

    # Step 3: Check if Mistral model is available
    if not check_mistral_model():
        console.print("[yellow]⚠️ Mistral model not found, downloading...[/yellow]")
        if not download_mistral_model():
            console.print("[red]❌ Failed to download Mistral model[/red]")
            console.print("[yellow]💡 Try manually: ollama pull mistral[/yellow]")
            return False
    else:
        console.print("[green]✅ Mistral model is available[/green]")

    console.print("[bold green]🎉 Ollama is fully configured and ready![/bold green]")
    return True

def show_profile_info(profile: Dict):
    """Display profile information."""
    console.print(Panel(f"Profile: {profile['name']}", style="bold green"))

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("📧 Email", profile.get("email", "Not set"))
    table.add_row("📍 Location", profile.get("location", "Not set"))
    table.add_row("📞 Phone", profile.get("phone", "Not set"))
    table.add_row("🔑 Keywords", ", ".join(profile.get("keywords", [])[:3]) + "..." if len(profile.get("keywords", [])) > 3 else ", ".join(profile.get("keywords", [])))
    table.add_row("🎯 Batch Size", str(profile.get("batch_default", 10)))

    console.print(table)

def show_menu(profile: Dict):
    """Show the main menu (alias for show_interactive_menu for compatibility)."""
    return show_interactive_menu(profile)

def run_scraping(profile: Dict, sites: list = None, keywords: list = None, mode: str = "automated") -> bool:
    """Run job scraping with specified parameters.

    Args:
        profile: User profile dictionary
        sites: List of sites to scrape (default: ['eluta'])
        keywords: List of keywords to search (default: from profile)
        mode: Scraping mode ('automated', 'parallel', 'basic')

    Returns:
        bool: True if scraping was successful, False otherwise
    """
    console.print(f"[bold blue]🔍 Running {mode} job scraping...[/bold blue]")

    # Set defaults
    if sites is None:
        sites = ['eluta']
    if keywords is None:
        keywords = profile.get('keywords', [])

    # Validate and normalize scraping mode
    try:
        mode = validate_scraping_mode(mode)
        console.print(f"[cyan]Using scraping mode: {get_scraping_mode_description(mode)}[/cyan]")
    except ValueError as e:
        console.print(f"[red]❌ {e}[/red]")
        return False

    try:
        if mode == "automated":
            # Use intelligent scraper
            from job_analysis_engine import run_intelligent_scraping

            console.print("[cyan]🧠 Using automated scraping with AI filtering[/cyan]")
            success = run_intelligent_scraping(profile['profile_name'], max_jobs=15)

            if success:
                console.print("[bold green]✅ Automated scraping completed successfully![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Automated scraping completed with limited results[/yellow]")
                return False

        elif mode == "parallel":
            # Use parallel scraper
            from scrapers.parallel_job_scraper import ParallelJobScraper

            console.print("[cyan]⚡ Using parallel scraping for speed[/cyan]")
            scraper = ParallelJobScraper(profile, max_workers=2)
            jobs = scraper.scrape_jobs_parallel(sites=sites, detailed_scraping=True)

            if jobs:
                # Save jobs to session
                session = utils.load_session(profile)
                session["scraped_jobs"] = jobs
                utils.save_session(profile, session)

                console.print(f"[bold green]✅ Parallel scraping found {len(jobs)} jobs![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Parallel scraping found no jobs[/yellow]")
                return False

        else:  # basic mode
            # Use working scraper
            from scrapers.eluta_working import ElutaWorkingScraper
            from playwright.sync_api import sync_playwright

            console.print("[cyan]🔍 Using working Eluta scraper[/cyan]")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                scraper = ElutaWorkingScraper(profile, browser_context=context)
                jobs = list(scraper.scrape_jobs())
                browser.close()

            if jobs:
                # Save jobs to session
                session = utils.load_session(profile)
                session["scraped_jobs"] = jobs
                utils.save_session(profile, session)

                console.print(f"[bold green]✅ Basic scraping found {len(jobs)} jobs![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Basic scraping found no jobs[/yellow]")
                return False

    except Exception as e:
        console.print(f"[red]❌ Error during scraping: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def run_application(profile: Dict, jobs: list = None, ats: str = "auto") -> bool:
    """Run job application process.

    Args:
        profile: User profile dictionary
        jobs: List of jobs to apply to (default: from queue)
        ats: ATS system to use (default: auto-detect)

    Returns:
        bool: True if applications were successful, False otherwise
    """
    console.print("[bold blue]📝 Running job application process...[/bold blue]")

    try:
        if jobs is None:
            # Load jobs from session queue
            session = utils.load_session(profile)
            scraped_jobs = session.get("scraped_jobs", [])
            done_jobs = session.get("done", [])

            # Filter out already processed jobs
            pending_jobs = [job for job in scraped_jobs if utils.hash_job(job) not in done_jobs]

            if not pending_jobs:
                console.print("[yellow]No jobs in queue to apply to[/yellow]")
                return False

            jobs = pending_jobs[:5]  # Default batch size

        console.print(f"[green]Found {len(jobs)} jobs to apply to[/green]")

        # Create mock args object for compatibility with existing apply_from_queue function
        class MockArgs:
            def __init__(self):
                self.ats = ats
                self.batch = len(jobs)
                self.verbose = False
                self.headless = False
                self.allow_senior = False

        mock_args = MockArgs()

        # Use existing apply_from_queue function
        result = apply_from_queue(profile, mock_args)

        return result == 0

    except Exception as e:
        console.print(f"[red]❌ Error during application process: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def show_interactive_menu(profile: Dict):
    """Show the simplified main interactive menu."""
    console.clear()
    console.print(Panel("🤖 AutoJobAgent - Simplified Menu", style="bold blue"))

    # Show profile info
    show_profile_info(profile)

    console.print("\n[bold]Available Actions:[/bold]")
    options = {
        "1": "🔍 Job Scraping (choose site and bot detection method)",
        "2": "📝 Apply to jobs from queue",
        "3": "🎯 Apply to specific job URL",
        "4": "📊 Status & Dashboard",
        "5": "⚙️ System status & settings",
        "6": "🚪 Exit"
    }

    for key, value in options.items():
        console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

    console.print()
    choice = Prompt.ask("Select option", choices=list(options.keys()), default="1")
    return choice

def handle_menu_choice(choice: str, profile: Dict, args) -> bool:
    """Handle menu choice and execute corresponding action.

    Args:
        choice: Menu choice (1-6)
        profile: User profile dictionary
        args: Command line arguments

    Returns:
        bool: True to continue menu loop, False to exit
    """
    if choice == "1":  # Job Scraping with site selection
        scraping_menu_action(profile, args)
    elif choice == "2":  # Apply from queue
        apply_from_queue(profile, args)
    elif choice == "3":  # Apply to specific URL
        url = Prompt.ask("Enter job URL")
        if url:
            status = apply_to_specific_job(url, profile, args)
            console.print(f"[bold]Application Status:[/bold] {status}")
    elif choice == "4":  # Status & Dashboard
        show_status_and_dashboard(profile)
    elif choice == "5":  # System status & settings
        system_status_and_settings_action(profile)
    elif choice == "6":  # Exit
        console.print("[green]Goodbye![/green]")
        return False

    # Don't pause after exit
    if choice != "6":
        input("\nPress Enter to continue...")

    return True

def scraping_menu_action(profile: Dict, args) -> None:
    """Show enhanced scraping menu with all available options."""
    console.print(Panel("🔍 Enhanced Scraping Menu", style="bold blue"))
    
    # Show system capabilities
    console.print(f"[cyan]🖥️  System: DDR5-6400, 32GB RAM, 16-core CPU[/cyan]")
    console.print(f"[cyan]🔍 Keywords: {len(profile.get('keywords', []))}[/cyan]")
    console.print(f"[cyan]⚡ Optimized for high performance[/cyan]")
    
    # Site selection first
    console.print(f"\n[bold]Available Job Sites:[/bold]")
    site_options = {
        "1": "🇨🇦 Eluta.ca (Canadian jobs - DDR5 optimized)",
        "2": "🌍 Indeed.ca (Global jobs with anti-detection)",
        "3": "💼 LinkedIn Jobs (Professional network)",
        "4": "🏛️ JobBank.gc.ca (Government jobs)",
        "5": "👹 Monster.ca (Canadian Monster)",
        "6": "🏢 Workday (Corporate ATS)",
        "7": "⚡ Multi-site parallel (all sites simultaneously)"
    }
    
    for key, value in site_options.items():
        console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
    
    console.print()
    site_choice = Prompt.ask("Select job site", choices=list(site_options.keys()), default="1")
    
    if site_choice == "1":
        # Eluta with enhanced options including producer-consumer
        console.print(f"\n[bold]Eluta.ca Scraping Methods:[/bold]")
        eluta_options = {
            "1": "🚀 Producer-Consumer (DDR5 Optimized) - RECOMMENDED",
            "2": "⚡ Enhanced Click-Popup (Best results)",
            "3": "🌐 Multi-Browser (Multiple contexts)",
            "4": "🔄 Parallel Processing (Ultra-fast)",
            "5": "📊 Detailed Analysis (Comprehensive)",
            "6": "🛡️ Anti-Bot (Advanced detection avoidance)",
            "7": "📋 Basic Scrape (Simple method)"
        }
        
        for key, value in eluta_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        eluta_choice = Prompt.ask("Select Eluta scraping method", choices=list(eluta_options.keys()), default="1")
        
        if eluta_choice == "1":
            # Producer-Consumer (DDR5 Optimized)
            console.print(Panel("🚀 Producer-Consumer System (DDR5-6400 Optimized)", style="bold green"))
            console.print("[cyan]This system separates scraping and processing for maximum performance:[/cyan]")
            console.print("  • Producer: Fast scraping only (single browser context)")
            console.print("  • Consumer: Multi-core processing (4 workers)")
            console.print("  • DDR5-6400 optimized for fast I/O")
            console.print("  • NVMe SSD for ultra-fast storage")
            
            if Confirm.ask("Start producer-consumer system?"):
                try:
                    from src.scrapers.producer_consumer_orchestrator import ProducerConsumerOrchestrator
                    orchestrator = ProducerConsumerOrchestrator(profile)
                    orchestrator.start()
                except Exception as e:
                    console.print(f"[red]❌ Error: {e}[/red]")
        else:
            # Map other choices to existing methods
            method_mapping = {
                "2": "1",  # Enhanced Click-Popup
                "3": "2",  # Multi-Browser
                "4": "3",  # Parallel Processing
                "5": "4",  # Detailed Analysis
                "6": "5",  # Anti-Bot
                "7": "6"   # Basic Scrape
            }
            single_site_scrape_action(profile, args, "eluta", method_mapping.get(eluta_choice, "1"))
    
    elif site_choice == "2":
        # Indeed
        console.print(f"\n[bold]Indeed.ca Scraping Methods:[/bold]")
        indeed_options = {
            "1": "🎯 Working Method (proven site analysis - RECOMMENDED)",
            "2": "⚡ Standard Detection (balanced speed/stealth)",
            "3": "🚀 Fast Mode (fastest, minimal detection)",
            "4": "🔧 Custom Settings"
        }
        
        for key, value in indeed_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        indeed_choice = Prompt.ask("Select Indeed scraping method", choices=list(indeed_options.keys()), default="1")
        single_site_scrape_action(profile, args, "indeed", indeed_choice)
    
    elif site_choice == "3":
        # LinkedIn
        console.print(f"\n[bold]LinkedIn Jobs Scraping Methods:[/bold]")
        linkedin_options = {
            "1": "🎯 Professional Network (requires login)",
            "2": "⚡ Fast Mode (minimal detection)",
            "3": "🔧 Custom Settings"
        }
        
        for key, value in linkedin_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        linkedin_choice = Prompt.ask("Select LinkedIn scraping method", choices=list(linkedin_options.keys()), default="1")
        single_site_scrape_action(profile, args, "linkedin", linkedin_choice)
    
    elif site_choice == "4":
        # JobBank
        console.print(f"\n[bold]JobBank.gc.ca Scraping Methods:[/bold]")
        jobbank_options = {
            "1": "🏛️ Government Jobs (official site)",
            "2": "⚡ Fast Mode (minimal detection)",
            "3": "🔧 Custom Settings"
        }
        
        for key, value in jobbank_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        jobbank_choice = Prompt.ask("Select JobBank scraping method", choices=list(jobbank_options.keys()), default="1")
        single_site_scrape_action(profile, args, "jobbank", jobbank_choice)
    
    elif site_choice == "5":
        # Monster
        console.print(f"\n[bold]Monster.ca Scraping Methods:[/bold]")
        monster_options = {
            "1": "👹 Canadian Monster (proven method)",
            "2": "⚡ Fast Mode (minimal detection)",
            "3": "🔧 Custom Settings"
        }
        
        for key, value in monster_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        monster_choice = Prompt.ask("Select Monster scraping method", choices=list(monster_options.keys()), default="1")
        single_site_scrape_action(profile, args, "monster", monster_choice)
    
    elif site_choice == "6":
        # Workday
        console.print(f"\n[bold]Workday ATS Scraping Methods:[/bold]")
        workday_options = {
            "1": "🏢 Corporate ATS (advanced detection)",
            "2": "⚡ Fast Mode (minimal detection)",
            "3": "🔧 Custom Settings"
        }
        
        for key, value in workday_options.items():
            console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")
        
        console.print()
        workday_choice = Prompt.ask("Select Workday scraping method", choices=list(workday_options.keys()), default="1")
        single_site_scrape_action(profile, args, "workday", workday_choice)
    
    elif site_choice == "7":
        # Multi-site parallel
        console.print(Panel("⚡ Multi-Site Parallel Scraping", style="bold green"))
        console.print("[cyan]This will scrape all major Canadian job sites simultaneously:[/cyan]")
        console.print("  • Eluta.ca (Producer-Consumer optimized)")
        console.print("  • Indeed.ca (Anti-detection)")
        console.print("  • LinkedIn Jobs (Professional)")
        console.print("  • JobBank.gc.ca (Government)")
        console.print("  • Monster.ca (Canadian)")
        
        if Confirm.ask("Start multi-site parallel scraping?"):
            multi_site_scrape_action(profile, args)

def single_site_scrape_action(profile: Dict, args, site: str, bot_method: str = "1") -> None:
    """Execute single site scraping with specified bot detection method."""
    console.print(f"[bold blue]🔍 Starting {site.upper()} scraping with bot detection method {bot_method}[/bold blue]")

    # Configure bot detection based on method
    bot_config = {
        "1": {"delay_range": (5, 10), "human_like": True, "stealth_mode": "deep"},
        "2": {"delay_range": (3, 6), "human_like": True, "stealth_mode": "standard"},
        "3": {"delay_range": (1, 3), "human_like": False, "stealth_mode": "minimal"},
        "4": {"delay_range": (3, 8), "human_like": True, "stealth_mode": "custom"}
    }

    config = bot_config.get(bot_method, bot_config["2"])

    try:
        # Start dashboard
        console.print("[green]Starting dashboard for monitoring...[/green]")
        dashboard_proc = subprocess.Popen(
            ["uvicorn", "dashboard_api:app", "--port", "8002"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)

        # Health check to ensure dashboard is running
        try:
            import requests
            response = requests.get("http://localhost:8002/api/health", timeout=5)
            if response.status_code == 200:
                console.print("[green]✅ Dashboard started successfully at: http://localhost:8002[/green]")
            else:
                console.print("[yellow]⚠️ Dashboard starting, may take a moment to be available at: http://localhost:8002[/yellow]")
        except:
            console.print("[yellow]⚠️ Dashboard starting, may take a moment to be available at: http://localhost:8002[/yellow]")

        # Execute scraping based on site and method
        if site == "eluta":
            if bot_method == "1":
                # Enhanced click-and-popup with human behavior
                console.print(f"[cyan]🎯 Using enhanced click-and-popup scraper with 3-second waits and human behavior[/cyan]")
                console.print(f"[cyan]📅 14-day filter + 0-2 years experience filtering[/cyan]")
                jobs = eluta_enhanced_click_popup_scrape(profile)

            elif bot_method == "2":
                # Multi-browser click-and-popup with universal framework
                console.print(f"[cyan]⚡ Using multi-browser click-and-popup scraper with universal framework[/cyan]")
                console.print(f"[cyan]🌐 2-3 browser contexts + enhanced experience filtering[/cyan]")
                jobs = eluta_multi_browser_scrape(profile)

            elif bot_method == "3":
                # Automated scraping with 14-day filter + job analysis + parallel processing
                console.print(f"[cyan]🧠 Using automated Eluta scraper with 14-day filter and job analysis[/cyan]")
                jobs = eluta_optimized_parallel_scrape(profile)

            elif bot_method == "4":
                # Basic click-and-popup scraping
                console.print(f"[cyan]🔍 Using basic click-and-popup scraper with enhanced human behavior[/cyan]")
                jobs = eluta_basic_scrape(profile)

            else:
                # Fallback to enhanced click-and-popup method
                console.print(f"[cyan]🎯 Using enhanced click-and-popup scraper (fallback)[/cyan]")
                jobs = eluta_enhanced_click_popup_scrape(profile)
        else:
            # Use standard enhanced scrapers
            from scrapers import get_scraper
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                scraper = get_scraper(site, profile, browser_context=context, **config)
                jobs = list(scraper.scrape_jobs())
                browser.close()

        if jobs:
            # Save to database
            from job_database import get_job_db
            job_db = get_job_db(profile['profile_name'])
            added, duplicates = job_db.add_jobs_batch(jobs)

            console.print(f"[bold green]✅ Scraping completed![/bold green]")
            console.print(f"[green]Found {len(jobs)} jobs, added {added} new jobs, {duplicates} duplicates[/green]")
        else:
            console.print("[yellow]⚠️ No jobs found[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Scraping error: {e}[/red]")
    finally:
        try:
            dashboard_proc.terminate()
        except:
            pass

def eluta_parallel_scrape(profile: Dict) -> List[Dict]:
    """Parallel Eluta scraping using our working method."""
    from scrapers.eluta_working import ElutaWorkingScraper
    from playwright.sync_api import sync_playwright
    import threading
    from queue import Queue

    console.print("[cyan]⚡ Starting parallel Eluta scraping with working method[/cyan]")

    # Get all keywords for parallel processing
    keywords = profile.get("keywords", [])
    all_jobs = []
    job_queue = Queue()

    def scrape_keyword(keyword, job_queue):
        """Scrape a single keyword in a separate thread."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)  # Headless for parallel
                context = browser.new_context()

                # Create profile copy with single keyword
                keyword_profile = profile.copy()
                keyword_profile["keywords"] = [keyword]

                scraper = ElutaWorkingScraper(keyword_profile, browser_context=context)
                scraper.max_jobs_per_keyword = 20  # Increased limit for parallel
                scraper.max_pages_per_keyword = 2  # 2 pages per keyword in parallel
                keyword_jobs = list(scraper.scrape_jobs())

                browser.close()

                for job in keyword_jobs:
                    job_queue.put(job)

                console.print(f"[green]✅ Keyword '{keyword}' completed: {len(keyword_jobs)} jobs[/green]")

        except Exception as e:
            console.print(f"[red]❌ Error scraping keyword '{keyword}': {e}[/red]")

    # Start threads for each keyword
    threads = []
    for keyword in keywords:
        thread = threading.Thread(target=scrape_keyword, args=(keyword, job_queue))
        thread.start()
        threads.append(thread)
        console.print(f"[cyan]🚀 Started thread for keyword: '{keyword}'[/cyan]")

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Collect all jobs from queue
    while not job_queue.empty():
        all_jobs.append(job_queue.get())

    console.print(f"[bold green]⚡ Parallel scraping completed: {len(all_jobs)} total jobs[/bold green]")
    return all_jobs

def eluta_parallel_scrape(profile: Dict) -> List[Dict]:
    """Parallel Eluta scraping using our working method with concurrent processing."""
    from scrapers.parallel_job_scraper import ParallelJobScraper

    console.print("[cyan]🚀 Starting parallel Eluta scraping[/cyan]")

    try:
        # Use our parallel scraper with concurrent workers
        scraper = ParallelJobScraper(profile, max_workers=2)
        jobs = scraper.scrape_jobs_parallel(sites=["eluta"], detailed_scraping=True)

        console.print(f"[bold green]🚀 Parallel scraping completed: {len(jobs)} jobs[/bold green]")
        return jobs

    except Exception as e:
        console.print(f"[red]❌ Parallel scraping error: {e}[/red]")
        return []

def eluta_detailed_scrape(profile: Dict) -> List[Dict]:
    """Detailed Eluta scraping using our working method."""
    from scrapers.eluta_working import ElutaWorkingScraper
    from playwright.sync_api import sync_playwright

    console.print("[cyan]🔍 Starting detailed Eluta scraping with working method[/cyan]")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Visible for detailed scraping
            context = browser.new_context()

            # Use working scraper with higher limits for detailed scraping
            scraper = ElutaWorkingScraper(profile, browser_context=context)
            scraper.max_jobs_per_keyword = 30  # Higher limit for detailed scraping
            scraper.max_pages_per_keyword = 5  # 5 pages for detailed scraping
            jobs = list(scraper.scrape_jobs())

            browser.close()

        console.print(f"[bold green]🔍 Detailed scraping completed: {len(jobs)} jobs[/bold green]")
        return jobs

    except Exception as e:
        console.print(f"[red]❌ Detailed scraping error: {e}[/red]")
        return []

def eluta_optimized_parallel_scrape(profile: Dict) -> List[Dict]:
    """Optimized parallel Eluta scraping with job analysis and 14-day filtering."""
    from scrapers.eluta_optimized_parallel import ElutaOptimizedParallelScraper

    console.print("[cyan]🧠 Starting optimized parallel Eluta scraping with job analysis[/cyan]")
    console.print("[cyan]📅 Using 14-day job filtering for fresh opportunities[/cyan]")
    console.print("[cyan]🎯 Enhanced with smart job matching and analysis[/cyan]")

    # Clear old jobs without enhanced fields
    console.print("[yellow]🗑️ Clearing old jobs to ensure fresh data with enhanced fields[/yellow]")
    try:
        from job_database import JobDatabase
        db = JobDatabase(profile['profile_name'])
        db.clear_all_jobs()
        console.print("[green]✅ Old jobs cleared successfully[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error clearing old jobs: {e}[/red]")

    try:
        # Use optimized parallel scraper with ultra-conservative settings to avoid bot detection
        scraper = ElutaOptimizedParallelScraper(
            profile,
            max_workers=2,  # 2 workers for maximum stability
            max_jobs_per_keyword=50,  # Higher limit per keyword
            max_pages_per_keyword=5,  # 5 pages per keyword (up to 14 days)
            enable_deep_analysis=True  # Enable job analysis
        )

        jobs = list(scraper.scrape_jobs())

        # Display analysis summary
        if jobs:
            high_match_jobs = [job for job in jobs if job.get("match_score", 0) >= 0.7]
            medium_match_jobs = [job for job in jobs if 0.5 <= job.get("match_score", 0) < 0.7]

            console.print(f"[bold green]🧠 Optimized scraping completed: {len(jobs)} jobs with analysis[/bold green]")
            console.print(f"[green]🎯 High match jobs (70%+): {len(high_match_jobs)}[/green]")
            console.print(f"[yellow]⚠️ Medium match jobs (50-69%): {len(medium_match_jobs)}[/yellow]")
            console.print(f"[cyan]📊 Average match score: {sum(job.get('match_score', 0) for job in jobs) / len(jobs):.2f}[/cyan]")

        return jobs

    except Exception as e:
        console.print(f"[red]❌ Optimized parallel scraping error: {e}[/red]")
        return []

def eluta_multi_browser_scrape(profile: Dict) -> List[Dict]:
    """Multi-browser Eluta scraping with enhanced click-and-popup and universal framework."""
    from scrapers.eluta_multi_browser import ElutaMultiBrowserScraper

    console.print("[cyan]⚡ Starting multi-browser click-and-popup Eluta scraping[/cyan]")
    console.print("[cyan]🖱️ Universal click-popup framework with site-specific optimizations[/cyan]")
    console.print("[cyan]🌐 2-3 browser contexts with human-like behavior[/cyan]")
    console.print("[cyan]🛡️ Enhanced stealth mode with 3-second popup waits[/cyan]")
    console.print("[cyan]📍 Using Eluta's default location (no location parameter)[/cyan]")
    console.print("[cyan]📅 Using 14-day job filtering and 0-2 years experience filter[/cyan]")

    try:
        # Use enhanced multi-browser scraper with click-and-popup framework
        scraper = ElutaMultiBrowserScraper(
            profile,
            max_workers=2,  # 2-3 browser contexts as per memories for better performance
            max_jobs_per_keyword=50,  # Higher limit per keyword
            max_pages_per_keyword=5,  # 5 pages minimum as per memories
            enable_deep_analysis=True  # Enable job analysis
        )

        jobs = list(scraper.scrape_jobs())

        # Display analysis summary
        if jobs:
            high_match_jobs = [job for job in jobs if job.get("match_score", 0) >= 0.7]
            medium_match_jobs = [job for job in jobs if 0.5 <= job.get("match_score", 0) < 0.7]

            console.print(f"[bold green]⚡ Multi-browser scraping completed: {len(jobs)} jobs[/bold green]")
            console.print(f"[green]🎯 High match jobs (70%+): {len(high_match_jobs)}[/green]")
            console.print(f"[yellow]⚠️ Medium match jobs (50-69%): {len(medium_match_jobs)}[/yellow]")
            if jobs:
                console.print(f"[cyan]📊 Average match score: {sum(job.get('match_score', 0) for job in jobs) / len(jobs):.2f}[/cyan]")

        return jobs

    except Exception as e:
        console.print(f"[red]❌ Multi-browser scraping error: {e}[/red]")
        return []

def eluta_enhanced_click_popup_scrape(profile: Dict) -> List[Dict]:
    """Enhanced click-and-popup Eluta scraping with human behavior and universal filtering."""
    from scrapers.eluta_working import ElutaWorkingScraper
    from playwright.sync_api import sync_playwright

    console.print("[cyan]🎯 Starting enhanced click-and-popup Eluta scraping[/cyan]")
    console.print("[cyan]🖱️ Using 3-second popup waits and human-like behavior[/cyan]")
    console.print("[cyan]📅 14-day filter + 0-2 years experience filtering[/cyan]")
    console.print("[cyan]🎯 Universal click-popup framework with site-specific optimizations[/cyan]")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()

            # Use enhanced working scraper with all new features
            scraper = ElutaWorkingScraper(profile, browser_context=context)
            scraper.max_age_days = 14  # 14-day filter as per memories
            scraper.max_jobs_per_keyword = 30  # Higher limit for enhanced scraping
            scraper.max_pages_per_keyword = 5  # 5 pages minimum as per memories
            jobs = list(scraper.scrape_jobs())

            browser.close()

        # Display enhanced filtering results
        if jobs:
            entry_level_jobs = [job for job in jobs if job.get("experience_level") == "Entry"]
            filtered_jobs = [job for job in jobs if job.get("filter_passed", True)]

            console.print(f"[bold green]🎯 Enhanced click-and-popup scraping completed: {len(jobs)} jobs[/bold green]")
            console.print(f"[green]✅ Entry level jobs: {len(entry_level_jobs)}[/green]")
            console.print(f"[green]🔍 Jobs passed filtering: {len(filtered_jobs)}[/green]")
            console.print(f"[cyan]🖱️ All jobs extracted using enhanced click-and-popup with 3-second waits[/cyan]")

        return jobs

    except Exception as e:
        console.print(f"[red]❌ Enhanced click-and-popup scraping error: {e}[/red]")
        return []

def eluta_basic_scrape(profile: Dict) -> List[Dict]:
    """Basic single-threaded Eluta scraping with enhanced click-and-popup behavior."""
    from scrapers.eluta_working import ElutaWorkingScraper
    from playwright.sync_api import sync_playwright

    console.print("[cyan]🔍 Starting basic click-and-popup Eluta scraping[/cyan]")
    console.print("[cyan]🖱️ Enhanced human-like behavior with click-and-popup method[/cyan]")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()

            # Use working scraper with enhanced features
            scraper = ElutaWorkingScraper(profile, browser_context=context)
            scraper.max_age_days = 14  # Set 14-day filter
            scraper.max_jobs_per_keyword = 20  # Reasonable limit for basic scraping
            scraper.max_pages_per_keyword = 5  # 5 pages for basic scraping
            jobs = list(scraper.scrape_jobs())

            browser.close()

        console.print(f"[bold green]🔍 Basic click-and-popup scraping completed: {len(jobs)} jobs[/bold green]")
        return jobs

    except Exception as e:
        console.print(f"[red]❌ Basic scraping error: {e}[/red]")
        return []

def multi_site_scrape_action(profile: Dict, args, bot_method: str = "2") -> None:
    """Execute multi-site parallel scraping."""
    console.print("[bold blue]🌐 Starting Multi-Site Parallel Scraping[/bold blue]")

    try:
        from scrapers.multi_site_scraper import MultiSiteScraper
        from scrapers import create_multi_site_scraper

        # Start dashboard
        console.print("[green]Starting dashboard for monitoring...[/green]")
        dashboard_proc = subprocess.Popen(
            ["uvicorn", "dashboard_api:app", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)
        console.print("[cyan]Dashboard available at: http://localhost:8000[/cyan]")

        # Create multi-site scraper
        sites = ["eluta", "indeed", "jobbank", "monster"]  # Working scrapers
        multi_scraper = create_multi_site_scraper(profile, sites)

        # Execute scraping
        jobs = multi_scraper.scrape_all_sites(max_jobs_per_site=20)

        if jobs:
            # Save to database
            from job_database import get_job_db
            job_db = get_job_db(profile['profile_name'])
            added, duplicates = job_db.add_jobs_batch(jobs)

            console.print(f"[bold green]✅ Multi-site scraping completed![/bold green]")
            console.print(f"[green]Found {len(jobs)} total jobs, added {added} new jobs, {duplicates} duplicates[/green]")
        else:
            console.print("[yellow]⚠️ No jobs found across all sites[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Multi-site scraping error: {e}[/red]")
    finally:
        try:
            dashboard_proc.terminate()
        except:
            pass

def show_status_and_dashboard(profile: Dict) -> None:
    """Show status and launch dashboard."""
    show_status(profile)

    console.print("\n[bold]Dashboard Options:[/bold]")
    dashboard_options = {
        "1": "🚀 Launch dashboard (auto-opens browser)",
        "2": "📊 Show detailed statistics only",
        "3": "🔄 Refresh status",
        "4": "🗑️ Clear recent applications data"
    }

    for key, value in dashboard_options.items():
        console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

    choice = Prompt.ask("Select option", choices=list(dashboard_options.keys()), default="1")

    if choice == "1":
        # Launch dashboard and open browser
        console.print("[green]Starting dashboard...[/green]")
        dashboard_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "src.dashboard.api:app", "--port", "8000", "--host", "0.0.0.0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)

        # Health check to ensure dashboard is running
        try:
            import requests
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                console.print("[green]✅ Dashboard started successfully at: http://localhost:8000[/green]")
            else:
                console.print("[yellow]⚠️ Dashboard starting, may take a moment to be available at: http://localhost:8000[/yellow]")
        except:
            console.print("[yellow]⚠️ Dashboard starting, may take a moment to be available at: http://localhost:8000[/yellow]")

        # Try to open browser
        try:
            import webbrowser
            webbrowser.open("http://localhost:8000")
            console.print("[green]Dashboard opened in browser[/green]")
        except:
            console.print("[yellow]Please manually open http://localhost:8000[/yellow]")

        input("Press Enter to stop dashboard...")
        dashboard_proc.terminate()
    elif choice == "3":
        show_status_and_dashboard(profile)  # Recursive call for refresh
    elif choice == "4":
        # Clear recent applications data
        console.print("[yellow]🗑️ Clearing recent applications data...[/yellow]")
        from utils import clear_recent_applications_data
        success = clear_recent_applications_data(profile['profile_name'], days_to_keep=7)
        if success:
            console.print("[green]✅ Recent applications data cleared successfully![/green]")
        else:
            console.print("[red]❌ Failed to clear recent applications data[/red]")
        input("Press Enter to continue...")
        show_status_and_dashboard(profile)  # Return to menu

def system_status_and_settings_action(profile: Dict) -> None:
    """Show system status and settings options."""
    console.print(Panel("⚙️ System Status & Settings", style="bold blue"))

    settings_options = {
        "1": "🔧 Check system status",
        "2": "📝 Manage profile settings",
        "3": "🧪 Run system tests",
        "4": "🔍 Debug dashboard issues",
        "5": "📊 Performance test",
        "6": "🔙 Back to main menu"
    }

    for key, value in settings_options.items():
        console.print(f"  [bold cyan]{key}[/bold cyan]: {value}")

    choice = Prompt.ask("Select option", choices=list(settings_options.keys()), default="1")

    if choice == "1":
        system_status_action(profile)
    elif choice == "2":
        console.print(f"[green]Profile location:[/green] profiles/{profile['profile_name']}")
        console.print("[yellow]Edit the JSON file to modify your profile[/yellow]")
    elif choice == "3":
        console.print("[cyan]🧪 Running system integration tests...[/cyan]")
        try:
            from test_system_integration import SystemIntegrationTest
            test_runner = SystemIntegrationTest()
            test_runner.run_all_tests()
        except ImportError:
            console.print("[yellow]Test module not found[/yellow]")
    elif choice == "4":
        debug_dashboard_action(profile)
    elif choice == "5":
        console.print("[cyan]🧪 Running performance test...[/cyan]")
        try:
            from test_parallel_performance import run_performance_comparison
            run_performance_comparison(profile['profile_name'])
        except ImportError:
            console.print("[yellow]Performance test module not found[/yellow]")

def run_scraping_legacy(profile: Dict, sites: list = None, keywords: list = None, mode: str = "automated") -> bool:
    """Legacy run job scraping with specified parameters (duplicate function - should be removed).

    Args:
        profile: User profile dictionary
        sites: List of sites to scrape (default: ['eluta'])
        keywords: List of keywords to search (default: from profile)
        mode: Scraping mode ('automated', 'parallel', 'basic')

    Returns:
        bool: True if scraping was successful, False otherwise
    """
    console.print(f"[bold blue]🔍 Running {mode} job scraping...[/bold blue]")

    # Set defaults
    if sites is None:
        sites = ['eluta']
    if keywords is None:
        keywords = profile.get('keywords', [])

    try:
        if mode == "automated":
            # Use intelligent scraper
            from job_analysis_engine import run_intelligent_scraping

            console.print("[cyan]🧠 Using automated scraping with AI filtering[/cyan]")
            success = run_intelligent_scraping(profile['profile_name'], max_jobs=15)

            if success:
                console.print("[bold green]✅ Automated scraping completed successfully![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Automated scraping completed with limited results[/yellow]")
                return False

        elif mode == "parallel":
            # Use parallel scraper
            from scrapers.parallel_job_scraper import ParallelJobScraper

            console.print("[cyan]⚡ Using parallel scraping for speed[/cyan]")
            scraper = ParallelJobScraper(profile, max_workers=2)
            jobs = scraper.scrape_jobs_parallel(sites=sites, detailed_scraping=True)

            if jobs:
                # Save jobs to session
                session = utils.load_session(profile)
                session["scraped_jobs"] = jobs
                utils.save_session(profile, session)

                console.print(f"[bold green]✅ Parallel scraping found {len(jobs)} jobs![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Parallel scraping found no jobs[/yellow]")
                return False

        else:  # basic mode
            # Use working scraper
            from scrapers.eluta_working import ElutaWorkingScraper
            from playwright.sync_api import sync_playwright

            console.print("[cyan]🔍 Using working Eluta scraper[/cyan]")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                scraper = ElutaWorkingScraper(profile, browser_context=context)
                jobs = list(scraper.scrape_jobs())
                browser.close()

            if jobs:
                # Save jobs to session
                session = utils.load_session(profile)
                session["scraped_jobs"] = jobs
                utils.save_session(profile, session)

                console.print(f"[bold green]✅ Basic scraping found {len(jobs)} jobs![/bold green]")
                return True
            else:
                console.print("[yellow]⚠️ Basic scraping found no jobs[/yellow]")
                return False

    except Exception as e:
        console.print(f"[red]❌ Error during scraping: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

def select_ats():
    console.print(Panel("Select ATS System", style="bold blue"))
    options = {
        "1": "Workday",
        "2": "iCIMS",
        "3": "Greenhouse",
        "4": "BambooHR",
        "5": "Auto-detect",
        "6": "Resume last session",
        "7": "Manual mode (prepare documents only)"
    }

    for key, value in options.items():
        console.print(f"[bold]{key}[/bold]: {value}")

    choice = Prompt.ask("Select option", choices=list(options.keys()))

    if choice == "1":
        return "workday"
    elif choice == "2":
        return "icims"
    elif choice == "3":
        return "greenhouse"
    elif choice == "4":
        return "bamboohr"
    elif choice == "5":
        return "auto"
    elif choice == "6":
        return "resume"
    else:
        return "manual"

def prompt_continue():
    """Prompt user to continue to next batch of jobs."""
    return Confirm.ask("Continue to next batch?")

def is_senior_job(job_title: str) -> bool:
    """
    Check if a job title indicates a senior-level position.

    Args:
        job_title: The job title to analyze

    Returns:
        True if the job appears to be senior-level, False otherwise
    """
    senior_keywords = ["senior", "lead", "principal", "director", "manager", "head"]
    lower_title = job_title.lower()
    return any(keyword in lower_title for keyword in senior_keywords)

def validate_scraping_mode(mode: str) -> str:
    """
    Validate and normalize scraping mode parameter.

    Args:
        mode: The scraping mode to validate

    Returns:
        Normalized mode string

    Raises:
        ValueError: If mode is not supported
    """
    valid_modes = ["automated", "parallel", "basic"]
    normalized_mode = mode.lower().strip()

    # Handle legacy mode names for backward compatibility
    legacy_mappings = {
        "smart": "automated",
        "intelligent": "automated",
        "ultra": "parallel",
        "fast": "parallel",
        "deep": "basic",
        "detailed": "basic"
    }

    if normalized_mode in legacy_mappings:
        console.print(f"[yellow]⚠️ Legacy mode '{mode}' mapped to '{legacy_mappings[normalized_mode]}'[/yellow]")
        return legacy_mappings[normalized_mode]

    if normalized_mode not in valid_modes:
        raise ValueError(f"Invalid scraping mode: {mode}. Valid modes: {', '.join(valid_modes)}")

    return normalized_mode

def get_scraping_mode_description(mode: str) -> str:
    """
    Get a human-readable description of a scraping mode.

    Args:
        mode: The scraping mode

    Returns:
        Description of the scraping mode
    """
    descriptions = {
        "automated": "AI-powered automated scraping with intelligent filtering",
        "parallel": "High-performance parallel scraping using multiple workers",
        "basic": "Single-threaded basic scraping with standard settings"
    }
    return descriptions.get(mode, f"Unknown mode: {mode}")

def get_professional_scraper_name(legacy_name: str) -> str:
    """
    Convert legacy scraper names to professional equivalents.

    Args:
        legacy_name: The legacy scraper name

    Returns:
        Professional scraper name
    """
    name_mappings = {
        "ultra_parallel": "parallel_processing",
        "smart_scraper": "automated_scraper",
        "enhanced_scraper": "advanced_scraper",
        "deep_scraper": "detailed_scraper",
        "fast_scraper": "optimized_scraper"
    }
    return name_mappings.get(legacy_name, legacy_name)

def create_professional_job_summary(jobs: List[Dict]) -> Dict:
    """
    Create a professional summary of scraped jobs.

    Args:
        jobs: List of job dictionaries

    Returns:
        Professional job summary statistics
    """
    if not jobs:
        return {
            "total_jobs": 0,
            "unique_companies": 0,
            "job_sites": [],
            "keywords_found": [],
            "summary_message": "No jobs found"
        }

    unique_companies = set()
    job_sites = set()
    keywords_found = set()

    for job in jobs:
        if job.get('company'):
            unique_companies.add(job['company'])
        if job.get('site'):
            job_sites.add(job['site'])
        if job.get('keywords'):
            keywords_found.update(job['keywords'])

    return {
        "total_jobs": len(jobs),
        "unique_companies": len(unique_companies),
        "job_sites": list(job_sites),
        "keywords_found": list(keywords_found)[:10],  # Top 10 keywords
        "summary_message": f"Successfully scraped {len(jobs)} jobs from {len(unique_companies)} companies"
    }

def display_professional_job_summary(jobs: List[Dict], operation_name: str = "Job Scraping") -> None:
    """
    Display a professional summary of job scraping results.

    Args:
        jobs: List of scraped jobs
        operation_name: Name of the operation performed
    """
    summary = create_professional_job_summary(jobs)

    console.print(f"\n[bold green]🎉 {operation_name} Complete[/bold green]")
    console.print(f"[cyan]📊 Total Jobs: {summary['total_jobs']}[/cyan]")
    console.print(f"[cyan]🏢 Unique Companies: {summary['unique_companies']}[/cyan]")

    if summary['job_sites']:
        console.print(f"[cyan]🌐 Job Sites: {', '.join(summary['job_sites'])}[/cyan]")

    if summary['keywords_found']:
        console.print(f"[cyan]🔍 Top Keywords: {', '.join(summary['keywords_found'][:5])}[/cyan]")

    console.print(f"[green]✅ {summary['summary_message']}[/green]")

def validate_profile_completeness(profile: Dict) -> Dict:
    """
    Validate that a user profile has all required fields for professional operation.

    Args:
        profile: User profile dictionary

    Returns:
        Validation result with status and missing fields
    """
    required_fields = ['profile_name', 'name', 'email', 'keywords']
    recommended_fields = ['skills', 'experience_level', 'location', 'phone']

    missing_required = [field for field in required_fields if not profile.get(field)]
    missing_recommended = [field for field in recommended_fields if not profile.get(field)]

    is_valid = len(missing_required) == 0
    completeness_score = (len(required_fields + recommended_fields) - len(missing_required + missing_recommended)) / len(required_fields + recommended_fields)

    return {
        "is_valid": is_valid,
        "completeness_score": completeness_score,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "status_message": "Profile complete" if is_valid else f"Missing required fields: {', '.join(missing_required)}"
    }

def get_system_performance_info() -> Dict:
    """
    Get system performance information for optimizing scraping parameters.

    Returns:
        System performance information
    """
    import os

    try:
        # Try to import psutil for detailed system info
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            memory_gb = 8.0  # Default assumption

        cpu_count = os.cpu_count() or 4

        # Recommend optimal worker count based on system specs
        if cpu_count >= 16 and memory_gb >= 16:
            recommended_workers = min(12, cpu_count - 2)
            performance_tier = "high"
        elif cpu_count >= 8 and memory_gb >= 8:
            recommended_workers = min(6, cpu_count - 1)
            performance_tier = "medium"
        else:
            recommended_workers = min(3, cpu_count)
            performance_tier = "basic"

        return {
            "cpu_count": cpu_count,
            "memory_gb": round(memory_gb, 1),
            "recommended_workers": recommended_workers,
            "performance_tier": performance_tier,
            "optimization_message": f"System optimized for {performance_tier} performance with {recommended_workers} workers"
        }
    except Exception:
        return {
            "cpu_count": 4,
            "memory_gb": 8.0,
            "recommended_workers": 3,
            "performance_tier": "basic",
            "optimization_message": "Using conservative settings due to system detection error"
        }

def apply_to_specific_job(job_url: str, profile: Dict, args) -> str:
    """Apply to a specific job by URL with interactive step-by-step process."""
    console.print(f"[bold]Applying to specific job:[/bold] {job_url}")

    # Create a job object from the URL
    job = {
        "title": "Manual Job Application",
        "company": "Unknown Company",
        "location": "Unknown Location",
        "url": job_url,
        "summary": "Manual job application from provided URL",
        "site": "Manual",
        "keywords": []
    }

    # Always start dashboard for monitoring
    console.print("[green]Starting dashboard for monitoring...[/green]")
    dashboard_proc = subprocess.Popen(
        ["uvicorn", "dashboard_api:app", "--port", "8002"],
        stdout=subprocess.DEVNULL if not args.verbose else None,
        stderr=subprocess.DEVNULL if not args.verbose else None
    )
    time.sleep(3)  # Give dashboard time to start

    # Health check to ensure dashboard is running
    try:
        import requests
        response = requests.get("http://localhost:8002/api/health", timeout=5)
        if response.status_code == 200:
            console.print("[green]✅ Dashboard started successfully at: http://localhost:8002[/green]")
        else:
            console.print("[yellow]⚠️ Dashboard starting, may take a moment to be available at: http://localhost:8002[/yellow]")
    except:
        console.print("[yellow]⚠️ Dashboard starting, may take a moment to be available at: http://localhost:8002[/yellow]")

    try:
        # Launch Playwright in non-headless mode for interaction
        console.print("[green]Launching browser (interactive mode)...[/green]")
        with sync_playwright() as p:
            # Create persistent context using Opera browser with saved passwords
            ctx = utils.create_browser_context(p, profile, headless=False)  # Interactive mode always non-headless

            try:
                # Generate/customize documents
                console.print("[green]Customizing documents...[/green]")
                pdf_cv, pdf_cl = customize(job, profile)

                # Select ATS if not provided
                ats_choice = args.ats if args.ats else select_ats()

                if ats_choice == "manual":
                    console.print(f"[green]Documents prepared:[/green] {pdf_cv}, {pdf_cl}")
                    console.print(f"[yellow]Manual mode: Please apply manually using the prepared documents[/yellow]")
                    utils.append_log_row(job, profile, "Manual", pdf_cv, pdf_cl, "Manual")
                    return "Manual"

                # Detect ATS if auto mode
                detected_ats = detect(job["url"]) if ats_choice == "auto" else ats_choice
                console.print(f"[green]Detected ATS:[/green] {detected_ats}")

                # Get submitter for the ATS
                submitter = get_submitter(detected_ats, ctx)

                # Submit application with interactive step-by-step process
                console.print("[green]Starting interactive application process...[/green]")
                console.print("[yellow]You can monitor progress at http://localhost:8000[/yellow]")
                console.print("[yellow]Use dashboard to pause/resume if needed[/yellow]")

                status = submitter.submit(job, profile, pdf_cv, pdf_cl)
                console.print(f"[bold]Final Status:[/bold] {status}")

                # Log result
                utils.append_log_row(job, profile, status, pdf_cv, pdf_cl, detected_ats)

                return status

            except Exception as e:
                console.print(f"[bold red]Error applying to job:[/bold red] {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                return "Failed"

            finally:
                console.print("[yellow]Keeping browser open for final review...[/yellow]")
                input("Press Enter to close browser and continue...")
                ctx.close()

    finally:
        dashboard_proc.terminate()
        console.print("[green]Dashboard stopped[/green]")



def save_jobs_to_csv(jobs, csv_file):
    """Save jobs to CSV file with comprehensive information."""
    import csv

    if not jobs:
        return

    # Define CSV headers
    headers = [
        "title", "company", "location", "url", "apply_url", "summary",
        "site", "search_keyword", "scraped_at", "salary", "job_type",
        "posted_date", "company_rating", "keywords"
    ]

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for job in jobs:
            # Ensure all fields exist
            row = {}
            for header in headers:
                if header == "keywords":
                    # Convert keywords list to string
                    row[header] = ", ".join(job.get("keywords", []))
                else:
                    row[header] = job.get(header, "")
            writer.writerow(row)

    console.print(f"[green]Saved {len(jobs)} jobs to {csv_file}[/green]")

def show_status(profile: Dict) -> None:
    """Show current application status."""
    console.print(Panel("Application Status", style="bold blue"))

    try:
        # Use database instead of session file for accurate data
        from job_database import get_job_db

        job_db = get_job_db(profile['profile_name'])
        stats = job_db.get_stats()

        # Get recent jobs from database
        recent_jobs = job_db.get_jobs(limit=5)

        console.print(f"[green]Jobs in database:[/green] {stats.get('total_jobs', 0)}")
        console.print(f"[blue]Applied jobs:[/blue] {stats.get('applied_jobs', 0)}")
        console.print(f"[yellow]Available to apply:[/yellow] {stats.get('unapplied_jobs', 0)}")
        console.print(f"[cyan]Unique companies:[/cyan] {stats.get('unique_companies', 0)}")

        if recent_jobs:
            console.print("\n[bold]Recent jobs in database:[/bold]")
            for i, job in enumerate(recent_jobs, 1):
                title = job.get("title", "Unknown Title")
                company = job.get("company", "Unknown Company")
                location = job.get("location", "Unknown Location")
                posted = job.get("posted_date", "Unknown")
                console.print(f"  {i}. {title} at {company}")
                console.print(f"     📍 {location} | 📅 {posted}")

            if stats.get('total_jobs', 0) > 5:
                console.print(f"  ... and {stats.get('total_jobs', 0) - 5} more in database")
        else:
            console.print("\n[yellow]No jobs found in database. Try running job scraping first.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error accessing database: {e}[/red]")
        # Fallback to session file if database fails
        session = utils.load_session(profile)
        scraped_jobs = session.get("scraped_jobs", [])
        done_jobs = session.get("done", [])
        console.print(f"[yellow]Fallback - Session data:[/yellow]")
        console.print(f"[green]Jobs in session:[/green] {len(scraped_jobs)}")
        console.print(f"[blue]Applications completed:[/blue] {len(done_jobs)}")

    # Check for log file
    log_file = Path("output/logs/applications.xlsx")
    if log_file.exists():
        console.print(f"\n[green]Application log:[/green] {log_file}")
    else:
        console.print(f"\n[yellow]No application log found yet[/yellow]")

def apply_from_queue(profile: Dict, args) -> int:
    """Apply to jobs from the scraped queue."""
    console.print("[bold]Applying to jobs from queue...[/bold]")

    # Load session
    session = utils.load_session(profile)
    scraped_jobs = session.get("scraped_jobs", [])
    done_jobs = session.get("done", [])

    if not scraped_jobs:
        console.print("[yellow]No jobs in queue. Run scraping first.[/yellow]")
        return 1

    # Filter out already processed jobs
    pending_jobs = [job for job in scraped_jobs if utils.hash_job(job) not in done_jobs]

    if not pending_jobs:
        console.print("[yellow]All jobs in queue have been processed.[/yellow]")
        return 0

    console.print(f"[green]Found {len(pending_jobs)} jobs to process[/green]")

    # Set batch size
    batch_size = args.batch if args.batch else profile.get("batch_default", 5)
    jobs_to_process = pending_jobs[:batch_size]

    # Check if dashboard is already running
    dashboard_proc = None
    try:
        import requests
        requests.get("http://localhost:8002", timeout=2)
        console.print("[green]Dashboard already running at http://localhost:8002[/green]")
    except:
        # Start dashboard subprocess
        console.print("[green]Starting dashboard...[/green]")
        dashboard_proc = subprocess.Popen(
            ["uvicorn", "dashboard_api:app", "--port", "8002"],
            stdout=subprocess.DEVNULL if not args.verbose else None,
            stderr=subprocess.DEVNULL if not args.verbose else None
        )
        time.sleep(2)

    try:
        # Launch Playwright
        with sync_playwright() as p:
            # Use Opera browser with persistent sessions
            ctx = utils.create_browser_context(p, profile, headless=getattr(args, 'headless', False))

            try:
                # Select ATS if not provided
                ats_choice = args.ats if args.ats else select_ats()

                # Process each job
                for i, job in enumerate(jobs_to_process, 1):
                    console.print(f"\n[bold]Job {i}/{len(jobs_to_process)}:[/bold] {job['title']} at {job['company']}")

                    # Skip senior jobs unless allowed
                    if not args.allow_senior and is_senior_job(job["title"]):
                        console.print(f"[yellow]Skipping senior job:[/yellow] {job['title']}")
                        utils.append_log_row(job, profile, "Skipped (Senior)", "", "", "")
                        session.setdefault("done", []).append(utils.hash_job(job))
                        continue

                    try:
                        # Generate/customize documents
                        console.print("[green]Customizing documents...[/green]")
                        pdf_cv, pdf_cl = customize(job, profile)

                        if ats_choice == "manual":
                            console.print(f"[green]Documents prepared:[/green] {pdf_cv}, {pdf_cl}")
                            utils.append_log_row(job, profile, "Manual", pdf_cv, pdf_cl, "")
                            session.setdefault("done", []).append(utils.hash_job(job))
                            continue

                        # Detect ATS if auto mode
                        detected_ats = detect(job["url"]) if ats_choice == "auto" else ats_choice
                        console.print(f"[green]Detected ATS:[/green] {detected_ats}")

                        # Get submitter for the ATS
                        submitter = get_submitter(detected_ats, ctx)

                        # Submit application
                        console.print("[green]Submitting application...[/green]")
                        status = submitter.submit(job, profile, pdf_cv, pdf_cl)
                        console.print(f"[bold]Status:[/bold] {status}")

                        # Log result
                        utils.append_log_row(job, profile, status, pdf_cv, pdf_cl, detected_ats)

                        # Mark job as done
                        session.setdefault("done", []).append(utils.hash_job(job))

                    except Exception as e:
                        console.print(f"[bold red]Error processing job:[/bold red] {e}")
                        if args.verbose:
                            import traceback
                            traceback.print_exc()
                        utils.append_log_row(job, profile, "Failed", "", "", "")
                        session.setdefault("done", []).append(utils.hash_job(job))

                    # Save progress after each job
                    utils.save_session(profile, session)

                    # Check for pause signal or shutdown request
                    if utils.check_pause_signal():
                        console.print("[yellow]Pause signal detected[/yellow]")
                        break

                    if shutdown_requested:
                        console.print("[yellow]Shutdown requested, stopping job processing[/yellow]")
                        break

                    # Ask to continue after each job
                    if i < len(jobs_to_process):
                        if not Confirm.ask("Continue to next job?"):
                            break

                console.print(Panel("[bold green]Job processing complete![/bold green]", style="green"))

            finally:
                ctx.close()

    finally:
        if dashboard_proc:
            dashboard_proc.terminate()
            console.print("[green]Dashboard stopped[/green]")
        else:
            console.print("[cyan]Dashboard remains running[/cyan]")

    return 0

def apply_from_csv(csv_path: str, profile: Dict, args) -> int:
    """Apply to jobs from a CSV file."""
    console.print(f"[bold]Applying to jobs from CSV file:[/bold] {csv_path}")

    # Initialize CSV applicator
    applicator = CSVJobApplicator(profile['profile_name'])

    # Load profile (already loaded but applicator needs its own copy)
    if not applicator.load_profile():
        return 1

    # Load session
    applicator.load_session()

    # Read jobs from CSV
    jobs = applicator.read_csv_jobs(csv_path)
    if not jobs:
        return 1

    # Apply limit if specified
    if args.batch:
        jobs = jobs[:args.batch]
        console.print(f"[yellow]Limited to first {args.batch} jobs[/yellow]")

    # Display preview
    applicator.display_jobs_preview(jobs)

    if args.preview:
        console.print("[yellow]Preview mode - not applying to jobs[/yellow]")
        return 0

    # Filter already applied jobs
    jobs = applicator.filter_applied_jobs(jobs)

    if not jobs:
        console.print("[green]All jobs have already been applied to![/green]")
        return 0

    # Confirm before proceeding
    console.print(f"\n[bold yellow]Ready to apply to {len(jobs)} jobs[/bold yellow]")
    if not Confirm.ask("Continue?"):
        console.print("[yellow]Cancelled by user[/yellow]")
        return 0

    # Apply to jobs
    ats_choice = args.ats if args.ats else "auto"
    stats = applicator.apply_to_jobs(jobs, ats_choice, args.delay)

    # Print results
    applicator.print_statistics(stats)

    return 0

def system_status_action(profile: Dict) -> None:
    """Check system status and offer setup options."""
    console.print(Panel("🔧 System Status & Setup", style="bold blue"))

    # Check Ollama
    console.print("[cyan]Checking Ollama...[/cyan]")
    ollama_running = check_ollama_status()

    # If Ollama is not working, offer to run setup
    if not ollama_running:
        console.print("\n[yellow]⚠️ Ollama is not properly configured[/yellow]")
        if Confirm.ask("Would you like to run the Ollama setup wizard?"):
            console.print("[cyan]Running Ollama setup...[/cyan]")
            try:
                result = subprocess.run([
                    sys.executable, "scripts/setup_ollama.py"
                ], check=False)
                if result.returncode == 0:
                    console.print("[green]✅ Ollama setup completed successfully![/green]")
                    # Re-check Ollama status
                    ollama_running = check_ollama_status()
                else:
                    console.print("[red]❌ Ollama setup failed[/red]")
            except Exception as e:
                console.print(f"[red]❌ Error running Ollama setup: {e}[/red]")

    # Check browser availability
    console.print("\n[cyan]Checking browsers...[/cyan]")
    browsers = ["opera", "msedge", "chrome", "chromium"]
    available_browsers = []

    for browser in browsers:
        try:
            with sync_playwright() as p:
                if hasattr(p, browser):
                    available_browsers.append(browser)
                    console.print(f"[green]✅ {browser.title()}[/green]")
                else:
                    console.print(f"[red]❌ {browser.title()}[/red]")
        except:
            console.print(f"[red]❌ {browser.title()}[/red]")

    # Check profile files
    console.print("\n[cyan]Checking profile files...[/cyan]")
    profile_dir = Path("profiles") / profile["profile_name"]
    required_files = [f"{profile['profile_name']}.json"]

    for file in required_files:
        file_path = profile_dir / file
        if file_path.exists():
            console.print(f"[green]✅ {file}[/green]")
        else:
            console.print(f"[yellow]⚠️ {file} (will be created)[/yellow]")

    # Check document files
    doc_files = [
        f"{profile['profile_name']}_Resume.docx",
        f"{profile['profile_name']}_CoverLetter.docx"
    ]

    for file in doc_files:
        file_path = profile_dir / file
        if file_path.exists():
            console.print(f"[green]✅ {file}[/green]")
        else:
            console.print(f"[yellow]⚠️ {file} (template needed)[/yellow]")

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"Ollama: {'✅ Running' if ollama_running else '❌ Not running'}")
    console.print(f"Browsers: {len(available_browsers)} available")
    console.print(f"Profile: {profile['name']}")

    if ollama_running and available_browsers:
        console.print("\n[bold green]🎉 System is ready for job automation![/bold green]")
    else:
        console.print("\n[yellow]⚠️ Some components need attention[/yellow]")
        console.print("[yellow]💡 Use the setup options above to fix issues[/yellow]")

def automated_scrape_action(profile: Dict, args=None) -> None:
    """Automated scraping with resume analysis and experience filtering."""
    console.print(Panel("🤖 Automated Job Scraping", style="bold blue"))

    console.print("[cyan]🧠 Starting intelligent job scraping automatically:[/cyan]")
    console.print("[cyan]   • Extract keywords from your resume automatically[/cyan]")
    console.print("[cyan]   • Filter for entry-level/1-2 years experience jobs[/cyan]")
    console.print("[cyan]   • Only save jobs relevant to your skills[/cyan]")

    try:
        # Use the intelligent scraper
        from job_analysis_engine import run_intelligent_scraping

        # Use default settings - no prompts
        max_jobs = 15  # Default target
        console.print(f"[cyan]🎯 Target: {max_jobs} suitable jobs[/cyan]")

        # Run intelligent scraping with auto mode
        success = run_intelligent_scraping(profile['profile_name'], max_jobs, auto_mode=True)

        if success:
            console.print(f"\n[bold green]🎉 Intelligent scraping completed successfully![/bold green]")

            # Show updated database stats
            job_db = get_job_db(profile['profile_name'])
            stats = job_db.get_stats()
            console.print(f"[green]📊 Database now contains: {stats.get('total_jobs', 0)} total jobs[/green]")
            console.print(f"[green]🎯 Unapplied jobs: {stats.get('unapplied_jobs', 0)}[/green]")
            console.print(f"[green]🏢 Unique companies: {stats.get('unique_companies', 0)}[/green]")
        else:
            console.print("[yellow]⚠️ Intelligent scraping completed with limited results[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error during intelligent scraping: {e}[/red]")
        import traceback
        traceback.print_exc()



def fix_ssl_cert_issue():
    """Fix common SSL certificate issue that prevents Ollama import."""
    import os

    ssl_cert_file = os.environ.get('SSL_CERT_FILE', '')

    if ssl_cert_file and not ssl_cert_file.endswith('.pem'):
        # If it points to a directory, try to find the cert file
        potential_cert_path = os.path.join(ssl_cert_file, 'cacert.pem')
        if os.path.exists(potential_cert_path):
            os.environ['SSL_CERT_FILE'] = potential_cert_path
            console.print(f"[cyan]🔧 Fixed SSL_CERT_FILE path automatically[/cyan]")
            return True

    return False

def main():
    args = parse_args()

    # Set up console and display banner
    console.print(Panel.fit(
        "[bold blue]AutoJobAgent[/bold blue] - Automated Job Application Tool",
        border_style="blue"
    ))

    # Fix SSL certificate issue early
    fix_ssl_cert_issue()

    # Load profile
    try:
        profile_path = Path(f"profiles/{args.profile}")
        if not profile_path.exists():
            console.print(f"[bold red]Error:[/bold red] Profile '{args.profile}' not found")
            return 1

        profile = utils.load_profile(args.profile)
        console.print(f"[green]Loaded profile:[/green] {profile['name']}")
    except Exception as e:
        console.print(f"[bold red]Error loading profile:[/bold red] {e}")
        return 1

    # Check Ollama on startup (except for dashboard mode)
    if args.action not in ["dashboard", "status"]:
        check_ollama_status()

    # Ensure profile files exist (may generate PDFs if needed)
    try:
        utils.ensure_profile_files(profile)
    except Exception as e:
        console.print(f"[bold red]Error ensuring profile files:[/bold red] {e}")
        return 1

    # ALWAYS start dashboard first - it's the primary interface
    console.print(Panel("📊 Starting Dashboard Interface", style="bold green"))
    dashboard_started = auto_start_dashboard()
    
    if dashboard_started:
        console.print("[green]✅ Dashboard is ready![/green]")
        console.print("[cyan]🌐 Your dashboard is available at: http://localhost:8000[/cyan]")
        console.print("[cyan]💡 The dashboard shows your job data, applications, and system status[/cyan]")
        console.print()
    else:
        console.print("[yellow]⚠️ Dashboard could not be started automatically[/yellow]")
        console.print("[cyan]💡 You can still use the CLI interface below[/cyan]")
        console.print()

    # Handle different actions
    if args.action == "interactive":
        return interactive_mode(profile, args)
    elif args.action == "scrape":
        automated_scrape_action(profile, args)
        return 0
    elif args.action == "apply-url":
        if not args.url:
            console.print("[bold red]Error:[/bold red] --url is required with --action apply-url")
            return 1
        status = apply_to_specific_job(args.url, profile, args)
        console.print(f"[bold]Final Status:[/bold] {status}")
        return 0
    elif args.action == "apply-csv":
        if not args.csv:
            console.print("[bold red]Error:[/bold red] --csv is required with --action apply-csv")
            return 1
        return apply_from_csv(args.csv, profile, args)
    elif args.action == "dashboard":
        console.print("[green]Dashboard is already running![/green]")
        console.print("[cyan]Visit http://localhost:8000 to view your job data[/cyan]")
        console.print("[cyan]Press Ctrl+C to stop the dashboard[/cyan]")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[yellow]Dashboard stopped[/yellow]")
        return 0
    elif args.action == "status":
        show_status(profile)
        return 0
    elif args.action == "setup":
        system_status_action(profile)
        return 0
    elif args.action == "apply":
        return apply_from_queue(profile, args)
    else:
        console.print(f"[bold red]Unknown action:[/bold red] {args.action}")
        return 1

def parallel_scrape_action(profile: Dict, args) -> None:
    """Run parallel job scraping."""
    from scrapers.parallel_job_scraper import ParallelJobScraper

    console.print(Panel("⚡ Parallel Job Scraping", style="bold green"))

    # Show system capabilities
    console.print(f"[cyan]🖥️  System: Conservative settings for stability[/cyan]")
    console.print(f"[cyan]🔍 Keywords: {len(profile.get('keywords', []))}[/cyan]")
    console.print(f"[cyan]⚡ Max parallel workers: 2[/cyan]")

    # Choose parallel mode
    mode = Prompt.ask(
        "Choose parallel mode",
        choices=["standard", "fast", "test"],
        default="standard"
    )

    if mode == "test":
        # Run performance test
        console.print("[cyan]🧪 Running parallel performance test...[/cyan]")
        from test_parallel_performance import run_performance_comparison
        run_performance_comparison(profile['profile_name'])
        return

    # Get scraping parameters
    max_pages = int(Prompt.ask("Max pages per keyword", default="5"))
    sites = ["eluta"]  # Can be expanded later

    try:
        # Use parallel scraper for all modes
        scraper = ParallelJobScraper(profile, max_workers=2)
        jobs = scraper.scrape_jobs_parallel(sites=sites, detailed_scraping=True)

        if jobs:
            # Save jobs to database
            console.print(f"[cyan]💾 Saving {len(jobs)} jobs to database...[/cyan]")
            db = get_job_db(profile['profile_name'])
            saved_count = 0
            duplicate_count = 0

            for job in jobs:
                if db.add_job(job):
                    saved_count += 1
                else:
                    duplicate_count += 1

            # Also save jobs to session for backward compatibility
            session = utils.load_session(profile)
            session["scraped_jobs"] = jobs
            utils.save_session(profile, session)

            console.print(f"[bold green]🎉 Parallel scraping completed![/bold green]")
            console.print(f"[green]💾 Saved {saved_count} new jobs to database ({duplicate_count} duplicates skipped)[/green]")

            # Show sample jobs
            console.print(f"\n[bold]📋 Sample Jobs Found:[/bold]")
            for i, job in enumerate(jobs[:5], 1):
                console.print(f"   {i}. [green]{job['title']}[/green] at {job['company']}")
        else:
            console.print("[yellow]⚠️ No jobs found with parallel scraping[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Parallel scraping error: {e}[/red]")
        if args.verbose:
            import traceback
            traceback.print_exc()

def parallel_scrape_action(profile: Dict, args=None) -> None:
    """Parallel scraping optimized for multi-core systems."""
    console.print(Panel("⚡ Parallel Job Scraping", style="bold green"))
    console.print("[cyan]💪 Optimized for multi-core CPU and high RAM systems![/cyan]")

    # Get user preferences
    max_workers = Prompt.ask("Number of parallel workers", default="2")
    detailed_scraping = Confirm.ask("Enable detailed scraping for company URLs?", default=True)

    try:
        max_workers = int(max_workers)
    except ValueError:
        max_workers = 2

    console.print(f"[cyan]🚀 Starting parallel scraping with {max_workers} workers...[/cyan]")
    console.print(f"[cyan]🔍 Detailed scraping: {'Enabled' if detailed_scraping else 'Disabled'}[/cyan]")

    try:
        from scrapers.parallel_job_scraper import ParallelJobScraper
        scraper = ParallelJobScraper(profile, max_workers=max_workers)
        jobs = scraper.scrape_jobs_parallel(detailed_scraping=detailed_scraping)

        if jobs:
            # Save jobs to database
            console.print(f"[cyan]💾 Saving {len(jobs)} jobs to database...[/cyan]")
            db = get_job_db(profile['profile_name'])
            saved_count = 0
            duplicate_count = 0

            for job in jobs:
                if db.add_job(job):
                    saved_count += 1
                else:
                    duplicate_count += 1

            console.print(f"[bold green]✅ Ultra-fast scraping found {len(jobs)} jobs![/bold green]")
            console.print(f"[green]💾 Saved {saved_count} new jobs to database ({duplicate_count} duplicates skipped)[/green]")
            console.print("[cyan]💡 Check the dashboard to see your scraped jobs[/cyan]")
        else:
            console.print("[yellow]⚠️ Ultra-fast scraping found no jobs[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error during ultra-fast scraping: {e}[/red]")
        import traceback
        traceback.print_exc()

def detailed_scrape_action(profile: Dict, args=None) -> None:
    """Detailed scraping that clicks into individual jobs for company URLs."""
    console.print(Panel("🔍 Detailed Job Scraping", style="bold cyan"))
    console.print("[cyan]Clicks into each job to extract company application URLs[/cyan]")

    # Get user preferences
    max_pages = Prompt.ask("Maximum pages per keyword", default="5")
    try:
        max_pages = int(max_pages)
    except ValueError:
        max_pages = 5

    console.print(f"[cyan]🔍 Starting deep scraping (up to {max_pages} pages per keyword)...[/cyan]")

    try:
        from scrapers.eluta_working import ElutaWorkingScraper
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Show browser for deep scraping
            context = browser.new_context()

            # Use working scraper
            scraper = ElutaWorkingScraper(profile, browser_context=context)

            jobs = list(scraper.scrape_jobs())
            browser.close()

        if jobs:
            # Save jobs to database
            console.print(f"[cyan]💾 Saving {len(jobs)} jobs to database...[/cyan]")
            db = get_job_db(profile['profile_name'])
            saved_count = 0
            duplicate_count = 0

            for job in jobs:
                if db.add_job(job):
                    saved_count += 1
                else:
                    duplicate_count += 1

            console.print(f"[bold green]✅ Deep scraping found {len(jobs)} jobs with company URLs![/bold green]")
            console.print(f"[green]💾 Saved {saved_count} new jobs to database ({duplicate_count} duplicates skipped)[/green]")
            console.print("[cyan]💡 Check the dashboard to see your scraped jobs[/cyan]")
        else:
            console.print("[yellow]⚠️ Deep scraping found no jobs[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error during deep scraping: {e}[/red]")
        import traceback
        traceback.print_exc()

def anti_bot_scrape_action(profile: Dict, args) -> None:
    """Anti-bot scraping that handles verification challenges gracefully."""
    console.print(Panel("🛡️ Anti-Bot Job Scraping", style="bold cyan"))
    console.print("[cyan]Handles CAPTCHA and verification challenges automatically[/cyan]")
    console.print("[yellow]⚠️ Will open browser window if verification is needed[/yellow]")

    # Get user preferences
    max_keywords = Prompt.ask("Maximum keywords to process", default="5")
    try:
        max_keywords = int(max_keywords)
        # Limit keywords for anti-bot mode to avoid triggering too much detection
        limited_keywords = profile.get("keywords", [])[:max_keywords]
        profile_copy = profile.copy()
        profile_copy["keywords"] = limited_keywords
    except ValueError:
        profile_copy = profile

    console.print(f"[cyan]🛡️ Starting anti-bot scraping for {len(profile_copy['keywords'])} keywords...[/cyan]")
    console.print("[yellow]💡 This mode uses slower, human-like delays to avoid detection[/yellow]")

    try:
        from scrapers.eluta_working import ElutaWorkingScraper
        from playwright.sync_api import sync_playwright

        console.print("[cyan]🎯 Using proven working Eluta scraper for anti-bot mode[/cyan]")

        with sync_playwright() as p:
            # Use visible browser for better success rate
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            scraper = ElutaWorkingScraper(profile_copy, browser_context=context)
            jobs = list(scraper.scrape_jobs())
            browser.close()

        if jobs:
            # Save jobs to database
            console.print(f"[cyan]💾 Saving {len(jobs)} jobs to database...[/cyan]")
            db = get_job_db(profile['profile_name'])
            saved_count = 0
            duplicate_count = 0

            for job in jobs:
                if db.add_job(job):
                    saved_count += 1
                else:
                    duplicate_count += 1

            console.print(f"[bold green]✅ Anti-bot scraping found {len(jobs)} jobs![/bold green]")
            console.print(f"[green]💾 Saved {saved_count} new jobs to database ({duplicate_count} duplicates skipped)[/green]")
            console.print("[cyan]💡 Check the dashboard to see your scraped jobs[/cyan]")
        else:
            console.print("[yellow]⚠️ Anti-bot scraping found no jobs[/yellow]")
            console.print("[yellow]💡 This might be due to verification challenges or rate limiting[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Error during anti-bot scraping: {e}[/red]")
        import traceback
        traceback.print_exc()

def debug_dashboard_action(profile: Dict) -> None:
    """Debug dashboard issues and database problems."""
    console.print(Panel("🔍 Dashboard Issue Debugger", style="bold yellow"))

    try:
        console.print("[cyan]Running dashboard diagnostics...[/cyan]")
        import subprocess
        result = subprocess.run([sys.executable, "debug_dashboard_issue.py"],
                              capture_output=True, text=True, timeout=30)

        if result.stdout:
            console.print(result.stdout)
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]")

    except Exception as e:
        console.print(f"[red]❌ Error running dashboard debugger: {e}[/red]")

def auto_start_dashboard() -> bool:
    """Automatically start the dashboard in the background if not already running."""
    try:
        import requests
        # Check if dashboard is already running on port 8000
        response = requests.get("http://localhost:8000", timeout=2)
        console.print("[green]📊 Dashboard already running at http://localhost:8000[/green]")
        return True
    except:
        # Dashboard not running, start it
        try:
            console.print("[cyan]🚀 Starting dashboard in background...[/cyan]")

            # Start dashboard as background process
            import subprocess
            dashboard_proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "src.dashboard.api:app", "--port", "8000", "--host", "0.0.0.0"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0
            )

            # Wait a moment for dashboard to start
            time.sleep(3)

            # Verify it started with health check
            try:
                response = requests.get("http://localhost:8000/api/health", timeout=5)
                if response.status_code == 200:
                    console.print("[green]✅ Dashboard started successfully at http://localhost:8000[/green]")
                    console.print("[cyan]💡 You can view your job data and metrics in the browser[/cyan]")
                    
                    # Try to open browser automatically
                    try:
                        import webbrowser
                        webbrowser.open("http://localhost:8000")
                        console.print("[green]🌐 Dashboard opened in your browser[/green]")
                    except:
                        console.print("[cyan]💡 Please manually open http://localhost:8000 in your browser[/cyan]")
                    
                    return True
                else:
                    console.print("[yellow]⚠️ Dashboard starting, may take a moment to be available at http://localhost:8000[/yellow]")
                    return True
            except:
                console.print("[yellow]⚠️ Dashboard starting, may take a moment to be available at http://localhost:8000[/yellow]")
                return True

        except Exception as e:
            console.print(f"[yellow]⚠️ Could not start dashboard: {e}[/yellow]")
            console.print("[cyan]💡 You can start it manually later if needed[/cyan]")
            return False

def interactive_mode(profile: Dict, args) -> int:
    """Run in interactive mode with menu."""

    # Dashboard is already started in main(), no need to start again

    while True:
        choice = show_interactive_menu(profile)

        # Use the handle_menu_choice function for consistency
        continue_loop = handle_menu_choice(choice, profile, args)

        if not continue_loop:
            break

    return 0

def scrape_jobs():
    """Scrape jobs from various sources."""
    print("\n" + "="*60)
    print("🔍 JOB SCRAPING MENU")
    print("="*60)
    
    # Load user profile
    profile = load_user_profile()
    if not profile:
        return
    
    print(f"\n👤 Profile: {profile.get('name', 'Unknown')}")
    print(f"🎯 Keywords: {', '.join(profile.get('keywords', []))}")
    print(f"📍 Location: {profile.get('location', 'Canada-wide')}")
    
    print("\n📋 Available Scraping Options:")
    print("1. 🚀 Modern Pipeline (Recommended) - DDR5-6400 Optimized")
    print("2. 🔄 Producer-Consumer System - High Performance")
    print("3. 🎯 Eluta.ca - Fast & Reliable")
    print("4. 💼 Indeed.ca - Comprehensive")
    print("5. 🔗 LinkedIn - Professional Network")
    print("6. 🏦 JobBank - Government Jobs")
    print("7. 👹 Monster - Large Database")
    print("8. 🏢 Workday - Enterprise Jobs")
    print("9. 🔄 Multi-Site Scraper - All Sources")
    print("0. ⬅️ Back to Main Menu")
    
    choice = input("\n🎯 Select scraping method (0-9): ").strip()
    
    if choice == "0":
        return
    elif choice == "1":
        print("\n🚀 Starting Modern Job Pipeline...")
        print("⚡ DDR5-6400 Optimized | 🔄 Streaming | 🧠 AI Analysis")
        asyncio.run(run_modern_pipeline(profile))
    elif choice == "2":
        print("\n🔄 Starting Producer-Consumer System...")
        print("⚡ High Performance | 🔄 Parallel Processing | 🧠 AI Analysis")
        asyncio.run(run_producer_consumer_system(profile))
    elif choice == "3":
        print("\n🎯 Starting Eluta.ca Scraper...")
        print("⚡ Fast & Reliable | 🎯 Canada-wide | 🔄 Real-time")
        asyncio.run(run_eluta_scraper(profile))
    elif choice == "4":
        print("\n💼 Starting Indeed.ca Scraper...")
        print("📊 Comprehensive | 🎯 Large Database | 🔄 Real-time")
        asyncio.run(run_indeed_scraper(profile))
    elif choice == "5":
        print("\n🔗 Starting LinkedIn Scraper...")
        print("👥 Professional Network | 🎯 Quality Jobs | 🔄 Real-time")
        asyncio.run(run_linkedin_scraper(profile))
    elif choice == "6":
        print("\n🏦 Starting JobBank Scraper...")
        print("🏛️ Government Jobs | 🎯 Reliable | 🔄 Real-time")
        asyncio.run(run_jobbank_scraper(profile))
    elif choice == "7":
        print("\n👹 Starting Monster Scraper...")
        print("📈 Large Database | 🎯 Diverse Jobs | 🔄 Real-time")
        asyncio.run(run_monster_scraper(profile))
    elif choice == "8":
        print("\n🏢 Starting Workday Scraper...")
        print("🏢 Enterprise Jobs | 🎯 Quality | 🔄 Real-time")
        asyncio.run(run_workday_scraper(profile))
    elif choice == "9":
        print("\n🔄 Starting Multi-Site Scraper...")
        print("🌐 All Sources | 🎯 Maximum Coverage | 🔄 Real-time")
        asyncio.run(run_multi_site_scraper(profile))
    else:
        print("❌ Invalid choice. Please try again.")

async def run_modern_pipeline(profile):
    """Run the modern job pipeline with big data patterns."""
    try:
        from src.scrapers.modern_job_pipeline import ModernJobPipeline, JobPipelineConfig
        
        # Create optimized configuration for DDR5-6400
        config = JobPipelineConfig(
            batch_size=100,      # DDR5 optimized batch size
            max_workers=6,       # DDR5 optimized workers
            buffer_size=2000,    # DDR5 optimized buffer
            timeout_seconds=30,
            enable_ai_analysis=True,
            enable_duplicate_detection=True,
            enable_streaming=True,
            ddr5_optimized=True
        )
        
        # Create and run pipeline
        pipeline = ModernJobPipeline(profile, config)
        await pipeline.start()
        
    except Exception as e:
        print(f"❌ Modern pipeline error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Application interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)
