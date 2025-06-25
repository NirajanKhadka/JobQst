"""
Main module - Entry point for the application.
This file provides the main CLI interface for the job automation system.
"""

import sys
import os
from rich.console import Console

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Create console instance for testing
console = Console()

# Dummy sync_playwright for test patching compatibility
sync_playwright = None

# Import the main application
try:
    from cli.actions.scraping_actions import ScrapingActions
    from app import main
except ImportError as e:
    print(f"ImportError: {e}")
    # Fallback: try direct import
    sys.path.insert(0, 'src')
    from cli.actions.scraping_actions import ScrapingActions
    from app import main


if __name__ == "__main__":
    # Call the main function from src.app
    # main()
    # For now, let's test the scraping menu action directly
    # This will be integrated into the main app flow later
    profile = {"keywords": ["software engineer"], "profile_name": "default"}
    actions = ScrapingActions(profile)
    actions.show_scraping_menu(None)