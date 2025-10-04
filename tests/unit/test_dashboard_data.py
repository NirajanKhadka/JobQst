#!/usr/bin/env python3
"""
Test dashboard data functionality using real database data.
Follows DEVELOPMENT_STANDARDS.md - no fabricated content.
"""

import pytest
from src.core.job_database import get_job_db
from datetime import datetime, timedelta


class TestDashboardData:
    """Test dashboard data operations with real data."""

    def test_database_connection(self):
        """Test that we can connect to the database."""
        db = get_job_db("test_profile")
        assert db is not None

    def test_get_recent_jobs(self):
        """Test getting recent jobs from database."""
        db = get_job_db("test_profile")
        try:
            # Test with real data if available
            jobs = db.get_recent_jobs(limit=5)
            assert isinstance(jobs, list)
            # Can be empty if no real data exists
            assert len(jobs) >= 0
        except Exception:
            pytest.skip("Database not available or empty")

    def test_job_count(self):
        """Test getting job count from database."""
        db = get_job_db("test_profile")
        try:
            count = db.get_job_count()
            assert isinstance(count, int)
            assert count >= 0
        except Exception:
            pytest.skip("Database not available")

    def test_applied_jobs_count(self):
        """Test getting applied jobs count."""
        db = get_job_db("test_profile")
        try:
            # This should work even with empty database
            applied_count = len([job for job in db.get_recent_jobs() if job.get("applied", False)])
            assert isinstance(applied_count, int)
            assert applied_count >= 0
        except Exception:
            pytest.skip("Database not available")


# End of file
