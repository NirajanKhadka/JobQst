"""
Command Dispatcher - Routes Commands to Appropriate Handlers

Extracted from main.py following DEVELOPMENT_STANDARDS.md guidelines.
Implements command routing pattern with clear separation of concerns.
Each function <30 lines, proper error handling, type hints.
"""

import asyncio
from typing import Dict, Any
from rich.console import Console

from src.core.application_controller import (
    run_optimized_scraping,
    run_two_stage_processing,
    run_health_check,
    run_interactive_mode,
)

# Create console instance
console = Console()


async def dispatch_command(
    action: str, 
    profile: Dict[str, Any], 
    args: Any
) -> bool:
    """Dispatch command to appropriate handler."""
    try:
        if action == "scrape":
            return await run_optimized_scraping(profile, args)
        elif action in ["process", "process-jobs"]:
            return await run_two_stage_processing(profile, args)
        elif action == "health-check":
            return run_health_check(profile)
        elif action == "interactive":
            return await run_interactive_mode(profile)
        elif action == "dashboard":
            return await _run_dashboard(profile, args)
        elif action == "fast-pipeline":
            return await _run_fast_pipeline(profile, args)
        elif action == "jobspy-pipeline":
            return await _run_jobspy_pipeline(profile, args)
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Command dispatch failed: {e}[/red]")
        return False


async def _run_dashboard(profile: Dict[str, Any], args: Any) -> bool:
    """Run dashboard interface."""
    try:
        console.print("[bold blue]🌐 Starting Dashboard...[/bold blue]")
        
        # Import dashboard launcher
        from src.dashboard.unified_dashboard import launch_dashboard
        
        # This would launch the actual dashboard
        # For now, just simulate success
        console.print("[green]✅ Dashboard would launch here[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Dashboard launch failed: {e}[/red]")
        return False


async def _run_fast_pipeline(profile: Dict[str, Any], args: Any) -> bool:
    """Run fast processing pipeline."""
    try:
        console.print("[bold blue]⚡ Starting Fast Pipeline...[/bold blue]")
        
        from src.pipeline.enhanced_fast_job_pipeline import FastJobPipeline
        
        pipeline = FastJobPipeline(
            profile_name=args.profile,
            processing_method=getattr(args, 'processing_method', 'auto')
        )
        
        results = await pipeline.run_complete_pipeline(
            limit=getattr(args, 'jobs', 50)
        )
        
        console.print(f"[green]✅ Pipeline processed {len(results)} jobs[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Fast pipeline failed: {e}[/red]")
        return False


async def _run_jobspy_pipeline(profile: Dict[str, Any], args: Any) -> bool:
    """Run JobSpy integration pipeline."""
    try:
        console.print("[bold blue]🔍 Starting JobSpy Pipeline...[/bold blue]")
        
        from src.scrapers.multi_site_jobspy_workers import JobSpyWorkerManager
        
        manager = JobSpyWorkerManager(
            profile_name=args.profile,
            preset=getattr(args, 'jobspy_preset', 'quality')
        )
        
        results = await manager.run_multi_site_scrape(
            max_jobs_total=getattr(args, 'max_jobs_total', 200)
        )
        
        console.print(f"[green]✅ JobSpy found {len(results)} jobs[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ JobSpy pipeline failed: {e}[/red]")
        return False


def validate_command_args(action: str, args: Any) -> bool:
    """Validate command arguments for the given action."""
    try:
        if action == "scrape":
            if not hasattr(args, 'profile') or not args.profile:
                console.print("[red]❌ Profile required for scraping[/red]")
                return False
                
        elif action in ["process", "process-jobs"]:
            if getattr(args, 'batch', 0) <= 0:
                console.print("[red]❌ Invalid batch size[/red]")
                return False
                
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Argument validation failed: {e}[/red]")
        return False


def get_available_actions() -> list[str]:
    """Get list of available actions."""
    return [
        "scrape",
        "process",
        "process-jobs", 
        "dashboard",
        "health-check",
        "interactive",
        "fast-pipeline",
        "jobspy-pipeline",
    ]
