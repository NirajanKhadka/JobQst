#!/usr/bin/env python3
"""
Global pytest configuration and fixtures for AutoJobAgent test suite.
Provides shared test infrastructure following TESTING_STANDARDS.md

This module provides:
- Test configuration and markers
- Real data fixtures (no fabricated content)
- Performance monitoring utilities
- Test isolation and cleanup
- Shared test infrastructure
"""

import pytest
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import time
import tempfile
import shutil
from unittest.mock import Mock, patch
from rich.console import Console

# Add src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

console = Console()

# Test configuration constants following TESTING_STANDARDS.md
TEST_CONFIG = {
    "DEFAULT_JOB_LIMIT": 10,
    "DEFAULT_TIMEOUT": 30,
    "FAST_TEST_LIMIT": 5,
    "PERFORMANCE_TEST_DURATION": 60,
    "SCRAPING_DELAY": 0.5,
    "BATCH_SIZE": 5,
    "MAX_UNIT_TEST_TIME": 1.0,  # Unit tests must complete within 1 second
    "MAX_INTEGRATION_TEST_TIME": 10.0,  # Integration tests within 10 seconds
    "MAX_PERFORMANCE_TEST_TIME": 60.0,  # Performance tests within 60 seconds
    "COVERAGE_THRESHOLD": 80,  # Overall project coverage target
}


# Test markers for categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (medium speed)")
    config.addinivalue_line("markers", "performance: Performance/benchmark tests (slow)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (very slow)")
    config.addinivalue_line("markers", "scraping: Web scraping tests")
    config.addinivalue_line("markers", "database: Database-related tests")
    config.addinivalue_line("markers", "ai: AI/ML model tests")
    config.addinivalue_line("markers", "real_world: Tests using real external services")
    config.addinivalue_line("markers", "limited: Tests with limited data processing")


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Global test configuration."""
    return TEST_CONFIG.copy()


@pytest.fixture(scope="session")
def console_output():
    """Rich console for test output."""
    return Console()


@pytest.fixture
def job_limit(request) -> int:
    """
    Dynamic job limit fixture.
    Uses marker value if specified, otherwise defaults to TEST_CONFIG.

    Usage:
        @pytest.mark.parametrize("job_limit", [5], indirect=True)
        def test_scraping(job_limit):
            # Will use 5 jobs instead of default 10
    """
    # Check if test has a custom limit marker
    if hasattr(request, "param"):
        return request.param

    # Check for limited marker
    if request.node.get_closest_marker("limited"):
        return TEST_CONFIG["FAST_TEST_LIMIT"]

    return TEST_CONFIG["DEFAULT_JOB_LIMIT"]


@pytest.fixture
def batch_size(request) -> int:
    """Dynamic batch size for processing tests."""
    if hasattr(request, "param"):
        return request.param
    return TEST_CONFIG["BATCH_SIZE"]


@pytest.fixture
def test_timeout(request) -> int:
    """Dynamic timeout for tests."""
    if hasattr(request, "param"):
        return request.param
    return TEST_CONFIG["DEFAULT_TIMEOUT"]


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def real_job_data(test_db) -> Dict[str, Any]:
    """Real job data from database for testing (follows DEVELOPMENT_STANDARDS.md - no fabricated content)."""
    if test_db is None:
        pytest.skip("Database not available for real job data")

    try:
        # Get a real job from the database
        jobs = test_db.get_recent_jobs(limit=1)
        if jobs:
            return jobs[0]
        else:
            # If no jobs in database, return minimal structure based on actual schema
            return {
                "title": "",
                "company": "",
                "location": "",
                "url": "",
                "description": "",
                "salary": "",
                "job_type": "",
                "experience_level": "",
                "scraped_at": "",
            }
    except Exception:
        # Fallback to minimal real structure
        return {
            "title": "",
            "company": "",
            "location": "",
            "url": "",
            "description": "",
        }


@pytest.fixture
def real_job_list(test_db) -> List[Dict[str, Any]]:
    """Real job list from database for batch testing (follows DEVELOPMENT_STANDARDS.md - no fabricated content)."""
    if test_db is None:
        pytest.skip("Database not available for real job list")

    try:
        # Get real jobs from the database (limited for testing)
        jobs = test_db.get_recent_jobs(limit=10)
        if jobs:
            return jobs
        else:
            # If no jobs, return empty list rather than fabricated data
            return []
    except Exception:
        return []


@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, *args):
            self.stop()

    return Timer()


@pytest.fixture
def mock_scraping_results(job_limit):
    """Mock scraping results for testing without actual web requests.

    Note: This is for testing scraping infrastructure, not job content.
    Follows DEVELOPMENT_STANDARDS.md by avoiding fabricated job content.
    """

    def _generate_results(count: int = None) -> List[Dict[str, Any]]:
        if count is None:
            count = job_limit

        # Return empty structure for testing scraping infrastructure
        # without fabricated job content
        results = []
        for i in range(count):
            results.append(
                {
                    "title": "",  # Empty to avoid fabricated content
                    "company": "",
                    "location": "",
                    "url": "",
                    "description": "",
                    "salary": "",
                    "scraped_at": time.time(),
                    "test_index": i + 1,  # Only metadata for testing
                }
            )
        return results

    return _generate_results


@pytest.fixture
def test_database_config():
    """Test database configuration using real profile structure."""
    try:
        from src.utils.profile_helpers import get_available_profiles

        profiles = get_available_profiles()
        profile_name = profiles[0] if profiles else "Nirajan"  # Use real profile or fallback
    except ImportError:
        profile_name = "Nirajan"  # Fallback to known profile

    return {
        "database": f"{profile_name}_test_jobs_duckdb.db",
        "profile": profile_name,
        "cleanup_after": True,
    }


# Performance thresholds for automated testing
PERFORMANCE_THRESHOLDS = {
    "scraping_rate_min": 2.0,  # jobs per second
    "processing_rate_min": 5.0,  # jobs per second
    "db_query_rate_min": 10.0,  # queries per second
    "max_memory_mb": 500,  # maximum memory usage
    "max_test_duration": 300,  # maximum test duration in seconds
}


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return PERFORMANCE_THRESHOLDS.copy()


def pytest_runtest_setup(item):
    """Setup before each test."""
    # Print test start info for debugging
    if item.config.getoption("verbose") > 0:
        console.print(f"[cyan]🧪 Starting: {item.name}[/cyan]")


def pytest_runtest_teardown(item):
    """Cleanup after each test."""
    # Add any cleanup logic here
    pass


@pytest.fixture(autouse=True)
def test_isolation():
    """Ensure test isolation by cleaning up between tests."""
    yield
    # Add cleanup logic here if needed
    pass


# Command line options for test customization
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--job-limit",
        action="store",
        default=10,
        type=int,
        help="Default number of jobs for scraping tests",
    )
    parser.addoption(
        "--skip-slow", action="store_true", default=False, help="Skip slow performance tests"
    )
    parser.addoption(
        "--real-scraping",
        action="store_true",
        default=False,
        help="Enable real web scraping tests (slow)",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options."""
    if config.getoption("--skip-slow"):
        skip_slow = pytest.mark.skip(reason="--skip-slow option provided")
        for item in items:
            if "performance" in item.keywords or "slow" in item.keywords:
                item.add_marker(skip_slow)

    if not config.getoption("--real-scraping"):
        skip_real = pytest.mark.skip(reason="--real-scraping not provided")
        for item in items:
            if "real_world" in item.keywords:
                item.add_marker(skip_real)


# Helper functions for tests
class TestHelpers:
    """Helper functions for tests."""

    @staticmethod
    def validate_job_data(job_data: Dict[str, Any]) -> bool:
        """Validate job data structure."""
        required_fields = ["title", "company", "url"]
        return all(field in job_data for field in required_fields)

    @staticmethod
    def calculate_success_rate(successful: int, total: int) -> float:
        """Calculate success rate percentage."""
        if total == 0:
            return 0.0
        return (successful / total) * 100

    @staticmethod
    def format_performance_result(metric_name: str, value: float, threshold: float) -> str:
        """Format performance test results."""
        status = "✅ PASS" if value >= threshold else "❌ FAIL"
        return f"{status} {metric_name}: {value:.2f} (threshold: {threshold:.2f})"


@pytest.fixture
def test_helpers():
    """Test helper functions."""
    return TestHelpers


@pytest.fixture
def test_db():
    """Test database fixture for integration tests with proper cleanup."""
    db = None
    try:
        from src.core.job_database import get_job_db
        import shutil

        # Use a test-specific database
        test_profile = "test_profile"
        
        # Clean up any existing test profile directory before starting
        test_profile_dir = Path(f"profiles/{test_profile}")
        if test_profile_dir.exists():
            shutil.rmtree(test_profile_dir, ignore_errors=True)
        
        # Create fresh database
        db = get_job_db(test_profile)
        
        # Ensure database is clean before test
        if hasattr(db, 'clear_all_jobs'):
            db.clear_all_jobs()

        yield db

        # Cleanup after test
        if db is not None:
            try:
                if hasattr(db, 'clear_all_jobs'):
                    db.clear_all_jobs()
                if hasattr(db, 'close'):
                    db.close()
            except Exception as e:
                console.print(f"[yellow]Warning: Cleanup failed: {e}[/yellow]")
            
            # Remove test profile directory after test
            try:
                if test_profile_dir.exists():
                    shutil.rmtree(test_profile_dir, ignore_errors=True)
            except Exception:
                pass
                
    except ImportError:
        # If database module not available, return None
        yield None


@pytest.fixture
def real_job(real_job_data):
    """Single real job fixture (follows DEVELOPMENT_STANDARDS.md - no fabricated content)."""
    return real_job_data


@pytest.fixture
def real_jobs(real_job_list):
    """Multiple real jobs fixture (follows DEVELOPMENT_STANDARDS.md - no fabricated content)."""
    return real_job_list


@pytest.fixture
def real_profile():
    """Real profile fixture from actual profile files (follows DEVELOPMENT_STANDARDS.md - no fabricated content)."""
    try:
        from src.utils.profile_helpers import load_profile, get_available_profiles

        # Get available real profiles
        profiles = get_available_profiles()
        if profiles:
            # Use the first available real profile
            profile = load_profile(profiles[0])
            if profile:
                return profile

        # If no profiles available, return minimal structure
        return {
            "profile_name": "test_profile",
            "keywords": [],
            "skills": [],
        }
    except ImportError:
        # Fallback minimal structure
        return {
            "profile_name": "test_profile",
            "keywords": [],
            "skills": [],
        }


# Legacy compatibility aliases (for backward compatibility during transition)
@pytest.fixture
def sample_job(real_job):
    """Legacy alias for real_job fixture (DEPRECATED - use real_job instead)."""
    return real_job


@pytest.fixture
def sample_jobs(real_jobs):
    """Legacy alias for real_jobs fixture (DEPRECATED - use real_jobs instead)."""
    return real_jobs


@pytest.fixture
def sample_job_data(real_job_data):
    """Legacy alias for real_job_data fixture (DEPRECATED - use real_job_data instead)."""
    return real_job_data


@pytest.fixture
def sample_job_list(real_job_list):
    """Legacy alias for real_job_list fixture (DEPRECATED - use real_job_list instead)."""
    return real_job_list


@pytest.fixture
def test_profile(real_profile):
    """Legacy alias for real_profile fixture (DEPRECATED - use real_profile instead)."""
    return real_profile


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory fixture."""
    return tmp_path


@pytest.fixture
def scraper():
    """Mock scraper fixture for testing scraper functionality."""

    class MockScraper:
        def __init__(self):
            self.name = "MockScraper"

        def scrape_jobs(self, keywords=None, limit=None):
            """Mock scrape_jobs method that returns empty results."""
            if limit is None:
                limit = 5
            # Return empty job structures to avoid fabricated content
            return [
                {
                    "title": "",
                    "company": "",
                    "location": "",
                    "url": "",
                    "description": "",
                    "scraped_at": time.time(),
                    "test_index": i + 1,
                }
                for i in range(min(limit, 5))  # Limit to 5 for testing
            ]

    return MockScraper()
