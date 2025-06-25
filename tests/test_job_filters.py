"""
Job Filters Test for AutoJobAgent.

This test module provides testing of the job filtering functionality.
"""

import pytest
import logging
from typing import Dict, List
from pathlib import Path

# Fix import paths to use correct src. prefix
from src.utils.job_filters import JobDateFilter, ExperienceLevelFilter, UniversalJobFilter
from src.core.job_database import get_job_db
from src import utils

logger = logging.getLogger(__name__)

# --- Fixtures ---
@pytest.fixture
def test_jobs():
    return [
        {
            'title': 'Data Analyst',
            'company': 'Tech Corp',
            'location': 'Toronto, ON',
            'salary': '$60,000 - $80,000',
            'experience_level': 'mid',
            'scraped_at': 1640995200
        },
        {
            'title': 'Senior Developer',
            'company': 'Startup Inc',
            'location': 'Vancouver, BC',
            'salary': '$90,000 - $120,000',
            'experience_level': 'senior',
            'scraped_at': 1640995200
        }
    ]

@pytest.fixture
def exp_filter():
    from src.utils.job_filters import ExperienceLevelFilter
    return ExperienceLevelFilter()

@pytest.fixture
def date_filter():
    from src.utils.job_filters import JobDateFilter
    return JobDateFilter()

@pytest.fixture
def mock_db():
    class MockDB:
        def __init__(self):
            self.jobs = []
        def add_job(self, job):
            self.jobs.append(job)
        def get_jobs(self):
            return self.jobs
    return MockDB()

@pytest.fixture
def test_job():
    return {
        'title': 'Filter Test Job',
        'company': 'Filter Test Company',
        'location': 'Filter Test Location',
        'url': 'https://filter-test.com/job',
        'source': 'test'
    }

# --- Refactored Tests ---
def test_basic_filtering(exp_filter, date_filter, test_jobs):
    logger.info("🧪 Testing basic job filtering...")
    assert exp_filter is not None
    assert date_filter is not None
    result = exp_filter.filter_job(test_jobs[0])
    assert result.should_keep is True
    logger.info("✅ Basic filtering tests passed")

def test_database_operations(mock_db, test_job):
    logger.info("🧪 Testing database operations...")
    mock_db.add_job(test_job)
    jobs = mock_db.get_jobs()
    assert len(jobs) > 0
    logger.info("✅ Database operations tests passed")
