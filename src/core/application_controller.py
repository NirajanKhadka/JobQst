"""
Application Controller - Core Business Logic

Extracted from main.py following DEVELOPMENT_STANDARDS.md guidelines.
Contains the main application logic and workflow coordination.
Each function <30 lines, proper error handling, type hints.
"""

import os
import sys
import time
import asyncio
from typing import Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Create console instance
console = Console()

# Performance: Lazy import flag for heavy modules
_HEAVY_IMPORTS_LOADED = False


def ensure_auto_job_env() -> bool:
    """Ensure we are running inside the 'auto_job' conda environment."""
    try:
        if os.environ.get("AUTO_JOB_ENV_ENSURED") == "1":
            return True

        current_env = (os.environ.get("CONDA_DEFAULT_ENV") or "").lower()
        if current_env == "auto_job":
            return True

        console.print(
            "[yellow]⚠️ Not in 'auto_job' environment. " f"Current: {current_env}[/yellow]"
        )
        return False

    except Exception as e:
        console.print(f"[red]❌ Environment check failed: {e}[/red]")
        return False


def _ensure_imports() -> None:
    """Lazy import heavy modules only when needed."""
    global _HEAVY_IMPORTS_LOADED
    if not _HEAVY_IMPORTS_LOADED:
        global ScrapingActions, DashboardActions, load_profile
        from src.cli.actions.scraping_actions import ScrapingActions
        from src.cli.actions.dashboard_actions import DashboardActions
        from src.utils.profile_helpers import load_profile

        _HEAVY_IMPORTS_LOADED = True


async def run_optimized_scraping(profile: Dict[str, Any], args: Any) -> bool:
    """Run optimized scraping using Core Eluta scraper."""
    try:
        console.print("[yellow]⚠️  Optimized Eluta scraper temporarily unavailable[/yellow]")
        console.print("[cyan]💡 Use 'jobspy-pipeline' action for job scraping[/cyan]")
        return False

    except Exception as e:
        console.print(f"[red]❌ Scraping failed: {e}[/red]")
        return False


async def run_two_stage_processing(profile: Dict[str, Any], args: Any) -> bool:
    """Run two-stage job processing (CPU + GPU)."""
    try:
        _ensure_imports()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Starting two-stage processing...", total=100)

            from src.analysis.two_stage_processor import TwoStageJobProcessor

            processor = TwoStageJobProcessor(
                user_profile=profile,
                cpu_workers=getattr(args, "workers", 10),
                max_concurrent_stage2=getattr(args, "gpu_workers", 2),
            )

            progress.update(task, advance=25, description="Loading jobs...")

            # Get jobs from database
            from src.core.job_database import get_job_db

            db = get_job_db(args.profile)
            jobs = db.get_jobs()

            progress.update(task, advance=50, description="Two-stage processing...")

            # Run two-stage processing
            final_results = await processor.process_jobs(jobs)

            # Save results back to database
            progress.update(task, advance=75, description="Saving results...")

            for result in final_results:
                db.update_job_analysis(
                    result.job_id,
                    {
                        "stage1_score": result.stage1.basic_compatibility,
                        "stage2_score": (
                            result.stage2.semantic_compatibility if result.stage2 else None
                        ),
                        "final_score": result.final_compatibility,
                        "processing_time": result.total_processing_time,
                    },
                )

            progress.update(task, completed=100)

        console.print(f"[green]✅ Processed {len(final_results)} jobs[/green]")
        return True

    except Exception as e:
        console.print(f"[red]❌ Processing failed: {e}[/red]")
        return False


def run_health_check(profile: Dict[str, Any]) -> bool:
    """Run comprehensive health check."""
    try:
        console.print("[bold blue]🔍 Running Health Check...[/bold blue]")
        
        # Import the actual health checker
        from src.health_checks.system_health_checker import SystemHealthChecker
        
        # Run comprehensive health check
        health_checker = SystemHealthChecker(profile)
        results = health_checker.run_comprehensive_check()
        
        # Check critical systems only (database, disk, memory, services)
        critical_checks = ["database", "disk", "memory", "services"]
        critical_passed = all(results.get(key, False) for key in critical_checks)
        
        console.print("\n[bold blue]📊 Final Status[/bold blue]")
        if critical_passed:
            console.print("[bold green]✅ System ready for job search operations![/bold green]")
        else:
            console.print("[bold red]❌ Critical issues detected - please review above[/bold red]")
        
        return critical_passed

    except Exception as e:
        console.print(f"[red]❌ Health check failed: {e}[/red]")
        return False


async def run_interactive_mode(profile: Dict[str, Any]) -> bool:
    """Run interactive mode with menu."""
    try:
        from src.orchestration.command_dispatcher import dispatch_command
        import argparse
        
        while True:
            console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
            console.print("[bold green]🎯 JobLens Interactive Mode[/bold green]")
            console.print(f"[dim]Profile: {profile.get('profile_name', 'Unknown')}[/dim]")
            console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
            
            console.print("\n[bold blue]📋 Main Menu:[/bold blue]")
            console.print("  [bold]1.[/bold] 🔍 Job Search Pipeline [cyan](Comprehensive Options)[/cyan]")
            console.print("  [bold]2.[/bold] ⚙️  Process Existing Jobs")
            console.print("  [bold]3.[/bold] 📊 Launch Dashboard")
            console.print("  [bold]4.[/bold] 🏥 System Health Check")
            console.print("  [bold]5.[/bold] 🚪 Exit")
            
            choice = input("\n[bold yellow]→[/bold yellow] Enter your choice (1-5): ").strip()
            
            if choice == "5":
                console.print("[yellow]👋 Exiting interactive mode...[/yellow]")
                return True
            
            if choice == "1":
                # Comprehensive JobSpy Pipeline sub-menu
                await _run_jobspy_submenu(profile, dispatch_command)
            elif choice in ["2", "3", "4"]:
                # Create minimal args object for other commands
                args = argparse.Namespace(
                    profile=profile.get("profile_name", "Nirajan"),
                    sites="indeed,linkedin,glassdoor",
                    days=14,
                    jobs=200,
                    headless=True,
                    jobspy_preset="quality",
                    workers=4
                )
                
                action_map = {
                    "2": "process-jobs",
                    "3": "dashboard",
                    "4": "health-check"
                }
                
                await dispatch_command(action_map[choice], profile, args)
            else:
                console.print("[red]❌ Invalid choice. Please enter 1-5.[/red]")

    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Exiting interactive mode...[/yellow]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Interactive mode failed: {e}[/red]")
        return False


async def _run_jobspy_submenu(profile: Dict[str, Any], dispatch_command) -> None:
    """Show comprehensive JobSpy pipeline options with step-by-step configuration."""
    import argparse
    
    console.print("\n[bold magenta]" + "=" * 60 + "[/bold magenta]")
    console.print("[bold green]🔍 Job Search Pipeline - Configuration[/bold green]")
    console.print("[bold magenta]" + "=" * 60 + "[/bold magenta]")
    
    console.print("\n[bold blue]Choose your search strategy:[/bold blue]")
    console.print("\n  [bold]1.[/bold] ⚡ [green]Quick Search[/green] [dim](~5-10 min)[/dim]")
    console.print("     • Best for: Testing, immediate results")
    console.print("     • Sites: Indeed, LinkedIn")
    console.print("     • Jobs: ~100 total")
    console.print("     • Days back: 7")
    console.print("     • Processing: Fast mode")
    
    console.print("\n  [bold]2.[/bold] 🏙️  [blue]Major Cities Only[/blue] [dim](~10-15 min)[/dim]")
    console.print("     • Best for: Targeting Toronto, Vancouver, Montreal")
    console.print("     • Sites: Indeed, LinkedIn, Glassdoor")
    console.print("     • Jobs: ~250 total")
    console.print("     • Days back: 14")
    console.print("     • Processing: Quality mode, top 3 cities")
    
    console.print("\n  [bold]3.[/bold] 📅 [magenta]Last 7 Days Only[/magenta] [dim](~12-18 min)[/dim]")
    console.print("     • Best for: Fresh opportunities only, recent postings")
    console.print("     • Sites: Indeed, LinkedIn, Glassdoor")
    console.print("     • Jobs: ~200 total")
    console.print("     • Days back: 7 (recent jobs only)")
    console.print("     • Processing: Quality mode, all locations")
    
    console.print("\n  [bold]4.[/bold] 🌲 [green]RNIP Cities[/green] [dim](~8-12 min)[/dim]")
    console.print("     • Best for: Rural & Northern Immigration Program cities")
    console.print("     • Sites: Indeed, LinkedIn, Glassdoor")
    console.print("     • Jobs: ~200 total")
    console.print("     • Days back: 14")
    console.print("     • Processing: Quality mode, RNIP communities")
    
    console.print("\n  [bold]5.[/bold] ⚖️  [yellow]Balanced Search[/yellow] [dim](~15-25 min)[/dim]")
    console.print("     • Best for: Regular job hunting, quality results")
    console.print("     • Sites: Indeed, LinkedIn, Glassdoor")
    console.print("     • Jobs: ~300 total")
    console.print("     • Days back: 14")
    console.print("     • Processing: Quality mode with full analysis")
    
    console.print("\n  [bold]6.[/bold] 🎯 [cyan]Deep Search[/cyan] [dim](~30-45 min)[/dim]")
    console.print("     • Best for: Comprehensive search, finding hidden gems")
    console.print("     • Sites: Indeed, LinkedIn, Glassdoor, ZipRecruiter")
    console.print("     • Jobs: ~500 total")
    console.print("     • Days back: 30")
    console.print("     • Processing: Comprehensive with AI analysis")
    
    console.print("\n  [bold]7.[/bold] ⬅️  Back to Main Menu")
    
    search_choice = input("\n[bold yellow]→[/bold yellow] Choose search type (1-7): ").strip()
    
    if search_choice == "7":
        return
    
    # Configuration presets based on choice
    config_presets = {
        "1": {
            "name": "Quick Search",
            "sites": "indeed,linkedin",
            "days": 7,
            "jobs": 100,
            "preset": "fast",
            "workers": 2,
            "location_set": "tech_hubs_canada",
            "description": "Fast turnaround, essential sites only"
        },
        "2": {
            "name": "Major Cities Only",
            "sites": "indeed,linkedin,glassdoor",
            "days": 14,
            "jobs": 250,
            "preset": "quality",
            "workers": 3,
            "location_set": "top_3_cities",
            "description": "Focused search in Toronto, Vancouver, Montreal"
        },
        "3": {
            "name": "Last 7 Days Only",
            "sites": "indeed,linkedin,glassdoor",
            "days": 7,
            "jobs": 200,
            "preset": "quality",
            "workers": 3,
            "location_set": "canada_comprehensive",
            "description": "Fresh opportunities across all locations, last week only"
        },
        "4": {
            "name": "RNIP Cities",
            "sites": "indeed,linkedin,glassdoor",
            "days": 14,
            "jobs": 200,
            "preset": "quality",
            "workers": 3,
            "location_set": "rnip_cities",
            "description": "Rural and Northern Immigration Program communities"
        },
        "5": {
            "name": "Balanced Search",
            "sites": "indeed,linkedin,glassdoor",
            "days": 14,
            "jobs": 300,
            "preset": "quality",
            "workers": 3,
            "location_set": "canada_comprehensive",
            "description": "Optimal balance of speed and coverage"
        },
        "6": {
            "name": "Deep Search",
            "sites": "indeed,linkedin,glassdoor,ziprecruiter",
            "days": 30,
            "jobs": 500,
            "preset": "comprehensive",
            "workers": 4,
            "location_set": "canada_comprehensive",
            "description": "Maximum coverage and depth"
        }
    }
    
    if search_choice not in config_presets:
        console.print("[red]❌ Invalid choice. Returning to main menu.[/red]")
        return
    
    config = config_presets[search_choice]
    
    # Display confirmation
    console.print(f"\n[bold green]✓ Selected: {config['name']}[/bold green]")
    console.print(f"[dim]{config['description']}[/dim]")
    console.print("\n[bold blue]Configuration Summary:[/bold blue]")
    console.print(f"  • Sites: {config['sites'].replace(',', ', ')}")
    console.print(f"  • Max Jobs: {config['jobs']}")
    console.print(f"  • Days Back: {config['days']}")
    console.print(f"  • Preset: {config['preset']}")
    console.print(f"  • Location Set: {config['location_set']}")
    console.print(f"  • Workers: {config['workers']}")
    
    confirm = input("\n[bold yellow]→[/bold yellow] Start search? (yes/no): ").strip().lower()
    
    if confirm not in ["yes", "y"]:
        console.print("[yellow]⚠️  Search cancelled.[/yellow]")
        return
    
    # Create args object with selected configuration
    args = argparse.Namespace(
        profile=profile.get("profile_name", "Nirajan"),
        sites=config["sites"],
        days=config["days"],
        jobs=config["jobs"],
        headless=True,
        jobspy_preset=config["preset"],
        workers=config["workers"],
        max_jobs_total=config["jobs"],
        location_set=config["location_set"]
    )
    
    console.print(f"\n[bold green]🚀 Starting {config['name']}...[/bold green]")
    await dispatch_command("jobspy-pipeline", profile, args)
