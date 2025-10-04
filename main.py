#!/usr/bin/env python3
"""
JobLens Main CLI Entry Point - Consolidated Architecture
Phase 1 Implementation: Single Pipeline, Unified Commands

🎯 CLI Mode: For automation, scripting, and command-line users
🌐 Dashboard: For visual interface, launch: streamlit run src/dashboard/unified_dashboard.py
🔄 Hybrid: Use both - monitor in dashboard while running CLI operations

Architecture Changes:
- Single pipeline: jobspy_streaming_orchestrator.py
- Unified command handling via command_dispatcher.py
- Eliminated 4 redundant pipeline implementations
- Consolidated deduplication to single system
- Streamlined to <100 lines (vs 1050+ original)
"""

import sys
import os  # Keep for environment variables only
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.traceback import install

# Load environment and setup
load_dotenv()
install(show_locals=True)
sys.path.insert(0, str(Path(__file__).parent / "src"))

console = Console()


def parse_arguments():
    """Parse command line arguments - streamlined version."""
    parser = argparse.ArgumentParser(
        description="JobLens - Consolidated Job Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Consolidated Examples (Phase 1):
  python main.py Nirajan                                    # Interactive mode
  python main.py Nirajan --action jobspy-pipeline          # Unified pipeline (DEFAULT)
  python main.py Nirajan --action process-jobs             # Two-stage processing
  python main.py Nirajan --action dashboard                # Web interface
  python main.py Nirajan --action health-check             # System diagnostics
        """,
    )

    # Core arguments
    parser.add_argument(
        "profile", nargs="?", default=None, 
        help="Profile name (Nirajan for real profile, None/other for Demo)"
    )
    parser.add_argument(
        "--action",
        choices=[
            "jobspy-pipeline",
            "process-jobs",
            "dashboard",
            "interactive",
            "health-check",
            "benchmark",
        ],
        default="interactive",
        help="Action to perform (jobspy-pipeline is the unified scraping method)",
    )

    # JobSpy unified pipeline options
    parser.add_argument("--sites", help="Comma-separated sites (indeed,linkedin,glassdoor)")
    parser.add_argument("--keywords", help="Comma-separated keywords")
    parser.add_argument(
        "--days", type=int, default=14, choices=[7, 14, 30], help="Days to look back"
    )
    parser.add_argument("--jobs", type=int, default=200, help="Max jobs to process")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--port", type=int, default=8050, help="Port for dashboard (default: 8050)")

    # Advanced options
    parser.add_argument(
        "--jobspy-preset",
        choices=["fast", "comprehensive", "quality", "canada_comprehensive", "tech_hubs"],
        default="quality",
        help="JobSpy configuration preset",
    )
    parser.add_argument("--max-jobs-total", type=int, help="Override maximum total jobs")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker processes")

    return parser.parse_args()


async def main():
    """Consolidated main function - delegates to unified command dispatcher."""
    args = parse_arguments()

    # Profile resolution with demo fallback
    from src.dashboard.utils.profile_utils import require_profile
    from src.utils.profile_helpers import load_profile
    
    try:
        # Resolve profile: Nirajan if specified, else Demo
        resolved_profile_name = require_profile(args.profile)
        console.print(f"[cyan]📋 Using profile: {resolved_profile_name}[/cyan]")
        
        # Load profile data
        profile = load_profile(resolved_profile_name)
        if not profile:
            console.print(f"[red]❌ Failed to load profile '{resolved_profile_name}'[/red]")
            return False
        
        profile["profile_name"] = resolved_profile_name
        
    except ValueError as e:
        console.print(f"[red]❌ Profile error: {e}[/red]")
        return False

    # Dispatch to unified command handler
    from src.orchestration.command_dispatcher import dispatch_command

    try:
        success = await dispatch_command(args.action, profile, args)
        if success:
            console.print(f"[green]✅ Action '{args.action}' completed successfully![/green]")
        else:
            console.print(f"[yellow]⚠️ Action '{args.action}' completed with warnings[/yellow]")
        return success
    except Exception as e:
        console.print(f"[red]❌ Action '{args.action}' failed: {e}[/red]")
        return False


if __name__ == "__main__":
    # Run consolidated main
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
