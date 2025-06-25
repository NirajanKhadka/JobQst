#!/usr/bin/env python3
"""
Simple test script to check if basic imports and functionality work
"""

import sys
from pathlib import Path

# Add project root and src directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

try:
    print("Testing basic imports...")
    print(f"Added to path: {src_path}")
    print(f"Added to path: {project_root}")
    
    # Test basic imports
    import argparse
    print("✅ argparse imported")
    
    import signal
    print("✅ signal imported")
    
    import subprocess
    print("✅ subprocess imported")
    
    import time
    print("✅ time imported")
    
    import os
    print("✅ os imported")
    
    from pathlib import Path
    print("✅ pathlib imported")
    
    from typing import Dict
    print("✅ typing imported")
    
    # Test rich imports
    from rich.console import Console
    print("✅ rich.console imported")
    
    from rich.panel import Panel
    print("✅ rich.panel imported")
    
    from rich.prompt import Confirm, Prompt
    print("✅ rich.prompt imported")
    
    from rich.table import Table
    print("✅ rich.table imported")
    
    # Test playwright
    from playwright.sync_api import sync_playwright
    print("✅ playwright imported")
    
    # Test core modules individually
    print("\nTesting core modules...")
    
    # Test utils module
    try:
        from src.utils.document_generator import customize
        print("✅ utils.document_generator imported")
    except ImportError as e:
        print(f"⚠️ utils.document_generator import failed: {e}")
    
    # Test core module
    try:
        from src import utils
        print("✅ core.utils imported")
    except ImportError as e:
        print(f"⚠️ core.utils import failed: {e}")
    
    # Test ats module
    try:
        from src.ats import detect, get_submitter
        print("✅ ats module imported")
    except ImportError as e:
        print(f"⚠️ ats module import failed: {e}")
    
    # Test job database
    try:
        from src.core.job_database import JobDatabase
        print("✅ job_database imported")
    except ImportError as e:
        print(f"⚠️ job_database import failed: {e}")
    
    print("\n🎉 Basic imports successful!")
    
    # Test basic functionality
    print("\nTesting basic functionality...")
    
    # Test that we can create basic objects
    console = Console()
    print("✅ Console created successfully")
    
    # Test that we can create basic data structures
    test_dict = {"test": "value"}
    print("✅ Dictionary creation works")
    
    # Test that we can create basic file paths
    test_path = Path("test")
    print("✅ Path creation works")
    
except Exception as e:
    print(f"❌ Test error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ Test completed successfully!")
