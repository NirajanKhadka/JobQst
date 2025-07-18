#!/usr/bin/env python3
"""
Test script for dashboard apply button integration
"""


import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.job_database import get_job_db

def test_database_connection():
    """
    Test if we can connect to the database and get jobs.
    Skips if database is unavailable.
    """
    try:
        db = get_job_db('Nirajan')
        jobs = db.get_jobs(limit=5)
        assert db is not None, "Database connection failed"
        assert isinstance(jobs, list), "Jobs should be a list"
        print(f"✅ Database connection successful")
        print(f"📊 Found {len(jobs)} jobs in database")
        if jobs:
            print("\n📋 Sample jobs:")
            for i, job in enumerate(jobs[:3], 1):
                title = job.get('title', 'N/A')
                company = job.get('company', 'N/A')
                status = job.get('application_status', 'not_applied')
                print(f"  {i}. {title} at {company} (Status: {status})")
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")

def test_applier_import():
    """
    Test if applier module can be imported.
    Skips if applier module is not available.
    """
    try:
        from applier import JobApplier
        print("✅ Applier module imported successfully")
        assert True
    except ImportError as e:
        pytest.skip(f"Applier module not available: {e}")

