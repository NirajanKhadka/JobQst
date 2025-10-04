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


async def dispatch_command(action: str, profile: Dict[str, Any], args: Any) -> bool:
    """Unified command dispatcher - Phase 1 consolidation."""
    try:
        # UNIFIED PIPELINE: All scraping goes through jobspy_streaming_orchestrator
        if action in ["scrape", "jobspy-pipeline"]:
            return await _run_unified_jobspy_pipeline(profile, args)
        elif action in ["process", "process-jobs"]:
            return await run_two_stage_processing(profile, args)
        elif action == "health-check":
            return run_health_check(profile)
        elif action == "interactive":
            return await run_interactive_mode(profile)
        elif action == "dashboard":
            return await _run_dashboard(profile, args)
        elif action == "benchmark":
            return await _run_benchmark(profile, args)
        else:
            console.print(f"[red]❌ Unknown action: {action}[/red]")
            console.print(
                "[cyan]💡 Available actions: jobspy-pipeline, process-jobs, dashboard, health-check, interactive, benchmark[/cyan]"
            )
            return False

    except Exception as e:
        console.print(f"[red]❌ Command dispatch failed: {e}[/red]")
        return False


async def _run_dashboard(profile: Dict[str, Any], args: Any) -> bool:
    """Run dashboard interface."""
    try:
        console.print("[bold blue]🌐 Starting Dashboard...[/bold blue]")
        console.print("[cyan]📊 Dashboard will be available at: http://localhost:8050[/cyan]")
        console.print("[cyan]💡 Press Ctrl+C to stop the dashboard[/cyan]")

        # Import dashboard launcher
        from src.dashboard.unified_dashboard import launch_dashboard

        # Launch the actual dashboard
        profile_name = profile.get("profile_name", "Nirajan")
        port = getattr(args, "port", 8050)
        
        # This is a blocking call
        launch_dashboard(profile_name, port)
        return True

    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Dashboard stopped by user[/yellow]")
        return True
    except Exception as e:
        console.print(f"[red]❌ Dashboard launch failed: {e}[/red]")
        console.print("[cyan]💡 Make sure you have installed: pip install -r src/dashboard/requirements_dash.txt[/cyan]")
        return False


# Fast pipeline removed - use jobspy-pipeline instead


async def _run_unified_jobspy_pipeline(profile: Dict[str, Any], args: Any) -> bool:
    """UNIFIED PIPELINE: Single JobSpy streaming orchestrator for all scraping."""
    try:
        console.print("[bold blue]🚀 Starting Unified JobSpy Pipeline (Phase 1)...[/bold blue]")

        from src.pipeline.jobspy_streaming_orchestrator import run_jobspy_to_two_stage

        # Parse sites
        sites = getattr(args, "sites", None)
        if sites:
            sites = [s.strip() for s in sites.split(",")]
        else:
            sites = ["indeed", "linkedin", "glassdoor"]  # Default unified sites

        # Get configuration
        max_jobs = getattr(args, "max_jobs_total", None) or getattr(args, "jobs", 200)
        preset = getattr(args, "jobspy_preset", "quality")

        # Use profile locations or defaults
        locations = profile.get("locations", ["Toronto, ON", "Vancouver, BC", "Montreal, QC"])

        console.print(
            f"[cyan]📍 Targeting {len(locations)} locations with {len(sites)} sites[/cyan]"
        )
        console.print(f"[cyan]🎯 Max jobs: {max_jobs} | Preset: {preset}[/cyan]")

        # Run unified pipeline
        results = await run_jobspy_to_two_stage(
            profile_name=profile["profile_name"],
            location_set="canada_comprehensive",  # Use predefined location set
            query_preset="comprehensive",
            sites=sites,
            max_jobs_per_site_location=max_jobs // len(sites) if sites else 50,
            per_site_concurrency=4,
            max_total_jobs=max_jobs,
            batch_size=min(250, max_jobs // 4),
            cpu_workers=12,
            max_concurrent_stage2=2,
            fetch_descriptions=True,
            description_fetch_concurrency=24,
        )

        jobs_found = len(results) if results else 0
        console.print(
            f"[green]✅ Unified pipeline completed! Found and processed {jobs_found} jobs[/green]"
        )

        if jobs_found > 0:
            # Show sample results
            console.print(f"\n[bold green]📋 Sample Results:[/bold green]")
            for i, result in enumerate(results[:3], 1):
                # Try multiple sources for title and company
                title = "Unknown Title"
                company = "Unknown Company"

                # First try: stage1 results (processed)
                if hasattr(result, "stage1") and result.stage1:
                    stage1_title = getattr(result.stage1, "title", None)
                    stage1_company = getattr(result.stage1, "company", None)

                    # Clean and validate stage1 title
                    if (
                        stage1_title
                        and len(stage1_title.strip()) > 0
                        and len(stage1_title.strip()) <= 80
                    ):
                        # Check if title looks reasonable (not a fragment of description)
                        clean_title = stage1_title.strip()
                        if not ("\n" in clean_title or len(clean_title.split()) > 10):
                            title = clean_title

                    # Clean and validate stage1 company
                    if (
                        stage1_company
                        and len(stage1_company.strip()) > 0
                        and len(stage1_company.strip()) <= 60
                    ):
                        clean_company = stage1_company.strip()
                        if not ("\n" in clean_company or len(clean_company.split()) > 6):
                            company = clean_company

                # Second try: original job_data as fallback
                if (
                    (title == "Unknown Title" or company == "Unknown Company")
                    and hasattr(result, "job_data")
                    and result.job_data
                ):
                    if title == "Unknown Title" and result.job_data.get("title"):
                        fallback_title = result.job_data["title"].strip()
                        if len(fallback_title) <= 80 and not "\n" in fallback_title:
                            title = fallback_title

                    if company == "Unknown Company" and result.job_data.get("company"):
                        fallback_company = result.job_data["company"].strip()
                        if len(fallback_company) <= 60 and not "\n" in fallback_company:
                            company = fallback_company

                # Display with truncation for safety
                title_display = title[:75] + "..." if len(title) > 75 else title
                company_display = company[:50] + "..." if len(company) > 50 else company
                console.print(f"  {i}. {title_display} at {company_display}")

        return jobs_found > 0

    except Exception as e:
        console.print(f"[red]❌ Unified JobSpy pipeline failed: {e}[/red]")
        return False


def validate_command_args(action: str, args: Any) -> bool:
    """Validate command arguments for the given action."""
    try:
        if action == "scrape":
            if not hasattr(args, "profile") or not args.profile:
                console.print("[red]❌ Profile required for scraping[/red]")
                return False

        elif action in ["process", "process-jobs"]:
            if getattr(args, "batch", 0) <= 0:
                console.print("[red]❌ Invalid batch size[/red]")
                return False

        return True

    except Exception as e:
        console.print(f"[red]❌ Argument validation failed: {e}[/red]")
        return False


def get_available_actions() -> list[str]:
    """Get list of available actions - Phase 1 consolidated."""
    return [
        "jobspy-pipeline",  # UNIFIED: Primary scraping method
        "process-jobs",  # Two-stage processing
        "dashboard",  # Web interface
        "health-check",  # System diagnostics
        "interactive",  # Menu mode
        "benchmark",  # Performance testing
    ]


# Enhanced JobSpy variants removed - use jobspy-pipeline instead


# Benchmark handler moved to main.py


# Application handler moved to main.py


async def _run_benchmark(profile: Dict[str, Any], args: Any) -> bool:
    """Run performance benchmark."""
    try:
        console.print("[bold blue]🏃 Running performance benchmark...[/bold blue]")

        # Simple benchmark - test unified pipeline performance
        import time

        start_time = time.time()

        # Run a small test with unified pipeline
        test_args = type(
            "Args",
            (),
            {"sites": "indeed", "jobs": 10, "jobspy_preset": "fast", "max_jobs_total": 10},
        )()

        success = await _run_unified_jobspy_pipeline(profile, test_args)

        end_time = time.time()
        duration = end_time - start_time

        console.print(f"[green]✅ Benchmark completed in {duration:.2f} seconds[/green]")
        console.print(f"[cyan]📊 Performance: {'GOOD' if duration < 30 else 'SLOW'}[/cyan]")

        return success

    except Exception as e:
        console.print(f"[red]❌ Benchmark failed: {e}[/red]")
        return False
