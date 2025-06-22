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
    from app import main, scraping_menu_action
except ImportError:
    # Fallback: try direct import
    sys.path.insert(0, 'src')
    from app import main, scraping_menu_action

if __name__ == "__main__":
    # Call the main function from src.app
    main() 