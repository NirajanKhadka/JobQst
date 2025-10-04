"""
CLI Interface - Main Command Line Interface

Extracted from main.py following DEVELOPMENT_STANDARDS.md guidelines.
Handles argument parsing, validation, and command routing.
"""

import argparse
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.traceback import install

# Install rich traceback for better error display
install(show_locals=True)

# Create console instance
console = Console()


def parse_arguments():
    """Parse command line arguments with improved validation."""
    parser = argparse.ArgumentParser(
        description="AutoJobAgent - Job Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Performance Optimized Examples:
  python main.py Nirajan                           # Interactive mode (lazy loading)
  python main.py Nirajan --action scrape           # Optimized parallel scraping
  python main.py Nirajan --action dashboard        # Fast dashboard startup
  python main.py Nirajan --action scrape --sites eluta  # Site-specific optimization
  python main.py Nirajan --action scrape --sites eluta,indeed  # Multi-site with worker pools
  python main.py Nirajan --action scrape --days 7 --pages 2 --jobs 10 --headless  # Fast scrape
  python main.py Nirajan --action scrape --days 14 --pages 3 --jobs 20  # Balanced scrape  
  python main.py Nirajan --action scrape --days 30 --pages 5 --jobs 50  # Deep scrape
  python main.py Nirajan --action benchmark        # Performance diagnostics
  python main.py Nirajan --action pipeline         # Direct pipeline access
        """,
    )

    parser.add_argument(
        "profile", nargs="?", default="Nirajan", help="Profile name to use (default: Nirajan)"
    )
    parser.add_argument(
        "--action",
        choices=[
            "scrape",
            "dashboard",
            "interactive",
            "benchmark",
            "process",
            "process-jobs",
            "fetch-descriptions",
            "analyze-jobs",
            "shutdown",
            "pipeline",
            "health-check",
            "fast-pipeline",
            "jobspy-pipeline",
            "auto-jobspy",
            "legacy-process-jobs",
            "create-profile",
            "scan-resume",
        ],
        default="interactive",
        help="Action to perform: interactive (DEFAULT: show menu), "
        "process/process-jobs (two-stage CPU+GPU processing), "
        "scrape (get jobs), "
        "jobspy-pipeline (Improved pipeline with JobSpy integration), "
        "dashboard (launch UI), "
        "create-profile (auto-create profile from resume), "
        "scan-resume (scan resume in existing profile)",
    )
    parser.add_argument(
        "--sites",
        help="Comma-separated list of sites (eluta, indeed, linkedin, monster, towardsai)",
    )
    parser.add_argument("--keywords", help="Comma-separated list of keywords")
    parser.add_argument("--batch", type=int, default=10, help="Number of jobs per batch")
    parser.add_argument(
        "--days", type=int, default=14, choices=[7, 14, 30], help="Days to look back (7, 14, or 30)"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        choices=range(1, 11),
        metavar="1-10",
        help="Max pages per keyword (1-10)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=20,
        choices=range(5, 101),
        metavar="5-100",
        help="Max jobs per keyword (5-100)",
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run browser in headless mode (faster)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of worker processes (default: 4)"
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--retry-attempts", type=int, default=3, help="Number of retry attempts (default: 3)"
    )

    # Fast pipeline specific options
    parser.add_argument(
        "--processing-method",
        choices=["auto", "gpu", "hybrid", "rule_based"],
        default="auto",
        help="Job processing method for fast pipeline",
    )
    parser.add_argument(
        "--external-workers",
        type=int,
        default=6,
        help="External scraping workers for fast pipeline",
    )

    # JobSpy integration options
    parser.add_argument(
        "--jobspy-preset",
        choices=[
            "fast",
            "comprehensive",
            "quality",
            "mississauga",
            "toronto",
            "remote",
            "canadian_cities",
            "canada_comprehensive",
            "tech_hubs",
        ],
        default="quality",
        help="JobSpy configuration preset",
    )
    parser.add_argument(
        "--enable-eluta",
        action="store_true",
        default=True,
        help="Enable Eluta scraper alongside JobSpy",
    )
    parser.add_argument(
        "--jobspy-only", action="store_true", help="Use JobSpy only (fastest option)"
    )
    parser.add_argument(
        "--multi-site-workers",
        action="store_true",
        help="Use multi-site worker architecture for optimal performance",
    )
    parser.add_argument(
        "--hours-old",
        type=int,
        default=336,
        help="Maximum age of jobs in hours (default: 336 = 14 days)",
    )
    parser.add_argument(
        "--max-jobs-total", type=int, help="Override maximum total jobs for comprehensive searches"
    )

    # Profile creation options
    parser.add_argument("--name", help="Name for new profile creation")
    parser.add_argument(
        "--watch", action="store_true", help="Watch folder for resume files after profile creation"
    )
    parser.add_argument("--resume-path", help="Path to resume file for profile creation")

    return parser.parse_args()


def validate_environment():
    """Validate that we're running in the correct environment."""
    try:
        current_env = (os.environ.get("CONDA_DEFAULT_ENV") or "").lower()
        if current_env != "auto_job":
            console.print(
                "[yellow]⚠️ Warning: Not running in 'auto_job' environment. "
                f"Current environment: {current_env}[/yellow]"
            )
            return False
        return True
    except Exception as e:
        console.print(f"[red]❌ Error checking environment: {e}[/red]")
        return False


def display_welcome_banner():
    """Display the application welcome banner."""
    banner = """
🎯 JobQst - Automated Job Discovery & Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Performance Optimized CLI Interface
📊 Following DEVELOPMENT_STANDARDS.md guidelines
🚀 Clean Architecture with Separation of Concerns
    """
    console.print(Panel(banner, title="Welcome", style="bold green"))


def handle_cli_error(error: Exception, context: str = "CLI") -> None:
    """Handle CLI errors with proper logging and user feedback."""
    console.print(f"[red]❌ {context} Error: {str(error)}[/red]")
    if "--verbose" in sys.argv:
        console.print_exception()
