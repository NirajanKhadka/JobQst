import pytest
import os
import shutil
import sqlite3
from pathlib import Path
from test_real_database_benchmarks import RealDatabaseJobFetcher, RealJobData

TEST_DB_PATH = "data/test_jobs.db"
REAL_DB_PATH = "data/jobs.db"

@pytest.fixture(scope="module")
def setup_test_db():
    # Copy the real database to a test location to avoid modifying production data
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    shutil.copy(REAL_DB_PATH, TEST_DB_PATH)
    yield TEST_DB_PATH
    os.remove(TEST_DB_PATH)

@pytest.fixture
def job_fetcher(setup_test_db):
    return RealDatabaseJobFetcher(db_path=setup_test_db)

def test_fetch_real_jobs(job_fetcher):
    jobs = pytest.run(job_fetcher.fetch_real_jobs(limit=10))
    assert isinstance(jobs, list)
    assert all(isinstance(job, RealJobData) for job in jobs)
    assert len(jobs) > 0
    # Check for required fields
    for job in jobs:
        assert job.id
        assert job.title
        assert job.company
        assert job.description

def test_fetch_real_jobs_edge_cases(job_fetcher):
    # Test with limit=0
    jobs = pytest.run(job_fetcher.fetch_real_jobs(limit=0))
    assert jobs == []
    # Test with very high limit
    jobs = pytest.run(job_fetcher.fetch_real_jobs(limit=10000))
    assert isinstance(jobs, list)
    # Test with missing/invalid db path
    bad_fetcher = RealDatabaseJobFetcher(db_path="data/nonexistent.db")
    jobs = pytest.run(bad_fetcher.fetch_real_jobs(limit=5))
    assert jobs == []

def test_job_text_conversion(job_fetcher):
    jobs = pytest.run(job_fetcher.fetch_real_jobs(limit=5))
    for job in jobs:
        text = job.to_text()
        assert isinstance(text, str)
        assert job.title in text
        assert job.company in text
        assert job.description in text
