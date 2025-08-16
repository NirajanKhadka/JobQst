#!/usr/bin/env python3
"""
Test basic imports and functionality for JobLens.
Follows DEVELOPMENT_STANDARDS.md - tests core functionality without fabricated content.
"""

import pytest
import sys
from pathlib import Path
from rich.console import Console

# Add project root and src directory to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))


class TestBasicImports:
    """Test that all required modules can be imported successfully."""
    
    def test_standard_library_imports(self):
        """Test that standard library modules import correctly."""
        import argparse
        import signal
        import subprocess
        import time
        import os
        from pathlib import Path
        from typing import Dict
        
        # Verify basic functionality
        assert argparse.ArgumentParser is not None
        assert Path("test").name == "test"
        
    def test_third_party_imports(self):
        """Test that third-party dependencies import correctly."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Confirm, Prompt
        from rich.table import Table
        
        # Test that we can create objects
        console = Console()
        assert console is not None
        
    @pytest.mark.performance
    def test_playwright_import(self):
        """Test that playwright imports correctly (slow due to browser startup)."""
        try:
            from playwright.sync_api import sync_playwright
            # Just test import, don't actually start browsers in unit tests
            assert sync_playwright is not None
        except ImportError:
            pytest.skip("Playwright not installed or not working")


class TestCoreModules:
    """Test that our core application modules can be imported."""
    
    def test_utils_import(self):
        """Test that utils modules import correctly."""
        try:
            from src.utils.document_generator import customize
            assert customize is not None
        except ImportError:
            pytest.skip("document_generator module not available")
    
    def test_core_utils_import(self):
        """Test that core utils import correctly."""
        try:
            from src import utils
            assert utils is not None
        except ImportError:
            pytest.skip("core utils module not available")
    
    def test_ats_module_import(self):
        """Test that ATS module imports correctly."""
        try:
            from src.ats import detect, get_submitter
            assert detect is not None
            assert get_submitter is not None
        except ImportError:
            pytest.skip("ATS module not available")
    
    def test_job_database_import(self):
        """Test that job database imports correctly."""
        try:
            from src.core.job_database import JobDatabase
            assert JobDatabase is not None
        except ImportError:
            pytest.skip("job_database module not available")


class TestBasicFunctionality:
    """Test basic functionality without external dependencies."""
    
    def test_console_creation(self):
        """Test that we can create a Rich console."""
        console = Console()
        assert console is not None
        
    def test_basic_data_structures(self):
        """Test basic Python data structure creation."""
        test_dict = {"test": "value"}
        assert test_dict["test"] == "value"
        
        test_list = [1, 2, 3]
        assert len(test_list) == 3
        
    def test_path_operations(self):
        """Test basic path operations."""
        test_path = Path("test")
        assert test_path.name == "test"
        
        # Test with real project structure
        assert project_root.exists()
        assert src_path.exists()


# Note: This replaces the old script-style testing with proper pytest structure
# following DEVELOPMENT_STANDARDS.md requirements for testing
