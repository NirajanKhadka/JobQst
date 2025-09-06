#!/usr/bin/env python3
"""
CLI Argument Parser for AutoJobAgent
"""

import argparse
from typing import Dict, Any
from src.cli.handlers.system_handler import summarize_docs_command


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="AutoJobAgent - Automated job application tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py Nirajan                           # Interactive mode
  python main.py Nirajan --action scrape           # Scrape jobs only
  python main.py Nirajan --action apply            # Apply to scraped jobs
  python main.py Nirajan --action dashboard        # Launch dashboard
  python main.py Nirajan --action shutdown         # Stop the dashboard
  python main.py Nirajan --action status           # Show status
  python main.py --action create-profile --name "John" --watch  # Create profile and wait for resume
  python main.py --action scan-resume John         # Scan resume in existing profile
        """,
    )

    # Profile is required
    parser.add_argument("profile", help="Profile name to use (folder name in /profiles)")

    # Action commands
    parser.add_argument(
        "--action",
        choices=[
            "interactive",
            "scrape",
            "apply",
            "apply-url",
            "apply-csv",
            "dashboard",
            "status",
            "setup",
            "process-queue",
            "shutdown",
            "create-profile",
            "scan-resume",
        ],
        default="interactive",
        help="Action to perform",
    )

    # Scraping options
    parser.add_argument(
        "--sites", help="Comma-separated list of sites to scrape (eluta, indeed, workday)"
    )
    parser.add_argument("--keywords", help="Comma-separated list of keywords to search")
    parser.add_argument("--batch", type=int, help="Number of jobs to process in each batch")

    # Application options
    parser.add_argument("--url", help="Specific job URL to apply to (use with --action apply-url)")
    parser.add_argument(
        "--csv", help="CSV file path for batch applications (use with --action apply-csv)"
    )
    parser.add_argument(
        "--ats",
        choices=["workday", "icims", "greenhouse", "lever", "bamboohr", "auto", "manual"],
        help="ATS system to target (or 'auto' to detect)",
    )

    # Profile creation options
    parser.add_argument("--name", help="Name for new profile creation")
    parser.add_argument("--watch", action="store_true", help="Watch folder for resume files after profile creation")
    parser.add_argument("--resume-path", help="Path to resume file for profile creation")

    # General options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--allow-senior", action="store_true", help="Don't skip senior job postings"
    )
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument(
        "--delay", type=int, default=30, help="Delay between applications in seconds"
    )
    parser.add_argument("--preview", action="store_true", help="Preview jobs without applying")

    subparsers = parser.add_subparsers(dest="subcommand")
    parser_summarize_docs = subparsers.add_parser(
        "summarize-docs",
        help="Summarize and update all core documentation files (README, ISSUE_TRACKER, STATUS).",
    )
    parser_summarize_docs.set_defaults(func=summarize_docs_command)

    return parser


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_parser()
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> Dict[str, Any]:
    """Validate and process arguments."""
    validated = vars(args)

    # Process sites list
    if args.sites:
        validated["sites"] = [site.strip() for site in args.sites.split(",")]

    # Process keywords list
    if args.keywords:
        validated["keywords"] = [keyword.strip() for keyword in args.keywords.split(",")]

    return validated

