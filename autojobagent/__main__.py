"""
AutoJobAgent - Automated job application system.

This module serves as the main entry point for the AutoJobAgent application.
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

from .shared.config import settings
from .shared.logging_config import configure_logging

# Configure logging
configure_logging()

console = Console()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AutoJobAgent - Automated job application system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start in interactive mode
  python -m autojobagent --profile myprofile
  
  # Apply to a specific job
  python -m autojobagent --profile myprofile apply --url JOB_URL
  
  # Scrape jobs
  python -m autojobagent --profile myprofile scrape --query "python developer"
  
  # Show dashboard
  python -m autojobagent --profile myprofile dashboard
  """
    )
    
    # Global options
    parser.add_argument(
        "--profile",
        required=True,
        help="Profile name to use"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Apply command
    apply_parser = subparsers.add_parser("apply", help="Apply to jobs")
    apply_parser.add_argument("--url", help="Job URL to apply to")
    apply_parser.add_argument("--resume", help="Path to resume file")
    apply_parser.add_argument("--cover-letter", help="Path to cover letter file")
    
    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape job listings")
    scrape_parser.add_argument("query", nargs="?", help="Search query")
    scrape_parser.add_argument("--site", help="Site to scrape (e.g., indeed, workday)")
    scrape_parser.add_argument("--limit", type=int, default=10, help="Maximum number of jobs to scrape")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start the web dashboard")
    dashboard_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    dashboard_parser.add_argument("--port", type=int, default=8002, help="Port to listen on")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Run initial setup")
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    try:
        args = parse_args()
        
        # Set debug mode if specified
        if args.debug:
            settings.DEBUG = True
            configure_logging(log_level=logging.DEBUG)
        
        # Import here to avoid circular imports
        from .interfaces.cli import run_cli
        from .interfaces.web.dashboard import run_dashboard
        
        # Execute the appropriate command
        if args.command == "apply":
            # Handle apply command
            pass
        elif args.command == "scrape":
            # Handle scrape command
            pass
        elif args.command == "dashboard":
            run_dashboard(host=args.host, port=args.port)
        elif args.command == "setup":
            # Handle setup command
            pass
        else:
            # No command specified, run interactive mode
            run_cli(profile_name=args.profile)
            
    except KeyboardInterrupt:
        console.print("\n[red]Operation cancelled by user[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if settings.DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
