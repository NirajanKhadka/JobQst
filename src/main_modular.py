#!/usr/bin/env python3
"""
Main Modular Entry Point for AutoJobAgent
This is the new modular entry point that replaces the old monolithic app.py
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix SSL certificate path before any other imports that might use SSL
import ssl_fix  # This must be imported first to fix SSL issues

# Import the new modular app runner
from src.core.app_runner import main

if __name__ == "__main__":
    sys.exit(main()) 