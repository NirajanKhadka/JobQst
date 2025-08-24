"""
CLI Interface - Main Command Line Interface

Extracted from main.py following DEVELOPMENT_STANDARDS.md guidelines.
Handles argument parsing, validation, and command routing.
Max 30 lines per function, proper error handling, type hints.
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


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments with improved validation."""
    parser = argparse.ArgumentParser(
        description="AutoJobAgent - Job Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_get_examples_text(),
    )

    _add_basic_arguments(parser)
    _add_scraping_arguments(parser)
    _add_pipeline_arguments(parser)
    _add_jobspy_arguments(parser)
    _add_profile_arguments(parser)

    return parser.parse_args()


def _get_examples_text() -> str:
    """Get examples text for CLI help."""
    return """
Performance Optimized Examples:
  python main.py Nirajan                    # Interactive mode
  python main.py Nirajan --action scrape    # Parallel scraping
  python main.py Nirajan --action dashboard # Fast dashboard
  python main.py Nirajan --action scrape --sites eluta
  python main.py Nirajan --action scrape --days 7 --jobs 10
  python main.py Nirajan --action benchmark # Performance test
  python main.py Nirajan --action pipeline  # Direct pipeline
    """


def _add_basic_arguments(parser: argparse.ArgumentParser) -> None:
    """Add basic CLI arguments."""
    parser.add_argument(
        "profile", 
        nargs="?", 
        default="Nirajan", 
        help="Profile name to use (default: Nirajan)"
    )
    parser.add_argument(
        "--action",
        choices=[
            "scrape", "dashboard", "interactive", "benchmark", "process",
            "process-jobs", "fetch-descriptions", "analyze-jobs", "shutdown",
            "pipeline", "health-check", "fast-pipeline", "jobspy-pipeline",
            "auto-jobspy", "legacy-process-jobs", "create-profile",
            "scan-resume"
        ],
        default="interactive",
        help="Action to perform (default: interactive)",
    )


def _add_scraping_arguments(parser: argparse.ArgumentParser) -> None:
    """Add scraping-related CLI arguments."""
    parser.add_argument(
        "--sites", 
        help="Comma-separated list of sites (eluta, indeed, linkedin)"
    )
    parser.add_argument(
        "--keywords", 
        help="Comma-separated list of keywords"
    )
    parser.add_argument(
        "--batch", 
        type=int, 
        default=10, 
        help="Number of jobs per batch"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=14, 
        choices=[7, 14, 30], 
        help="Days to look back (7, 14, or 30)"
    )
    parser.add_argument(
        "--pages", 
        type=int, 
        default=3, 
        choices=range(1, 11), 
        metavar="1-10", 
        help="Max pages per keyword (1-10)"
    )
    parser.add_argument(
        "--jobs", 
        type=int, 
        default=20, 
        choices=range(5, 101), 
        metavar="5-100", 
        help="Max jobs per keyword (5-100)"
    )


def _add_pipeline_arguments(parser: argparse.ArgumentParser) -> None:
    """Add pipeline-related CLI arguments."""
    parser.add_argument(
        "--headless", 
        action="store_true", 
        help="Run browser in headless mode (faster)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=4, 
        help="Number of worker processes (default: 4)"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=30, 
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--retry-attempts", 
        type=int, 
        default=3, 
        help="Number of retry attempts (default: 3)"
    )
    parser.add_argument(
        "--processing-method", 
        choices=["auto", "gpu", "hybrid", "rule_based"], 
        default="auto", 
        help="Job processing method for fast pipeline"
    )
    parser.add_argument(
        "--external-workers", 
        type=int, 
        default=6, 
        help="External scraping workers for fast pipeline"
    )


def _add_jobspy_arguments(parser: argparse.ArgumentParser) -> None:
    """Add JobSpy integration CLI arguments."""
    parser.add_argument(
        "--jobspy-preset", 
        choices=[
            "fast", "comprehensive", "quality", "mississauga", 
            "toronto", "remote", "canadian_cities", "canada_comprehensive", 
            "tech_hubs"
        ],
        default="quality", 
        help="JobSpy configuration preset"
    )
    parser.add_argument(
        "--enable-eluta", 
        action="store_true", 
        default=True, 
        help="Enable Eluta scraper alongside JobSpy"
    )
    parser.add_argument(
        "--jobspy-only", 
        action="store_true", 
        help="Use JobSpy only (fastest option)"
    )
    parser.add_argument(
        "--multi-site-workers", 
        action="store_true", 
        help="Use multi-site worker architecture"
    )
    parser.add_argument(
        "--hours-old", 
        type=int, 
        default=336, 
        help="Maximum age of jobs in hours (default: 336 = 14 days)"
    )
    parser.add_argument(
        "--max-jobs-total", 
        type=int, 
        help="Override maximum total jobs for comprehensive searches"
    )


def _add_profile_arguments(parser: argparse.ArgumentParser) -> None:
    """Add profile creation CLI arguments."""
    parser.add_argument(
        "--name", 
        help="Name for new profile creation"
    )
    parser.add_argument(
        "--watch", 
        action="store_true", 
        help="Watch folder for resume files after profile creation"
    )
    parser.add_argument(
        "--resume-path", 
        help="Path to resume file for profile creation"
    )


def validate_environment() -> bool:
    """Validate that we're running in the correct environment."""
    try:
        current_env = (os.environ.get("CONDA_DEFAULT_ENV") or "").lower()
        if current_env != "auto_job":
            console.print(
                f"[yellow]⚠️ Warning: Not running in 'auto_job' environment. "
                f"Current environment: {current_env}[/yellow]"
            )
            return False
        return True
    except Exception as e:
        console.print(f"[red]❌ Error checking environment: {e}[/red]")
        return False


def display_welcome_banner() -> None:
    """Display the application welcome banner."""
    banner = """
🎯 JobLens - Automated Job Discovery & Analysis
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
