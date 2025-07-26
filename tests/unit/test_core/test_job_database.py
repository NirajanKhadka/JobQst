#!/usr/bin/env python3
"""
Unit tests for job database operations.
Tests core database functionality following TESTING_STANDARDS.md
"""

import pytest
import tempfile
import sqlite3
import os
from pathlib import Path
from unittest.mock import patch

from src.core.job_database import ModernJobDatabase


@pytest.mark.unit
class TestJobDatabaseCore:
    """Test core job database functionality."""
    
    def test_database_initialization_creates_schema(self, temp_dir):
        """Test that database initializes with correct schema."""
        db_path = temp_dir / "test.db"
        db = ModernJobDatabase(str(db_path))
        
        # Verify database file exists
        assert db_path.exists()
        
        # Verify tables are created
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert "jobs" in tables
        db.close()
    
    def test_add_job_saves_correctly(self, temp_dir, real_job):
        """Test that jobs are saved with all required fields."""
        db_path = temp_dir / "test.db"
        db = ModernJobDatabase(str(db_path))
        
        # Skip if no real job data available
        if not real_job or not real_job.get('title'):
            pytest.skip("No real job data available for testing")
        
        result = db.add_job(real_job)
        
        assert result is True
        
        # Verify job was saved
        saved_jobs = db.get_all_jobs()
        assert len(saved_jobs) == 1
        
        saved_job = saved_jobs[0]
        assert saved_job["title"] == real_job["title"]
        db.close()
        
        db.close()
    
    def test_duplicate_job_url_prevents_duplicate_storage(self, temp_dir, sample_job):
        """Test that duplicate job URLs are not stored twice."""
        db_path = temp_dir / "test.db"
        db = ModernJobDatabase(str(db_path))
        
        # Ensure the job has a URL for duplicate detection
        test_job = sample_job.copy()
        test_job["url"] = "https://example.com/job/123"
        
        # Add job first time
        result1 = db.add_job(test_job)
        assert result1 is True
        
        # Try to add same job again
        result2 = db.add_job(test_job)
        assert result2 is False  # Should fail due to duplicate URL
        
        # Verify only one job exists
        jobs = db.get_all_jobs()
        assert len(jobs) == 1
        
        db.close()
    
    def test_search_jobs_by_keyword_returns_matching_jobs(self, temp_dir, sample_jobs):
        """Test keyword search functionality."""
        db_path = temp_dir / "test.db"
        db = ModernJobDatabase(str(db_path))
        
        # Create test jobs if sample_jobs is empty
        test_jobs = sample_jobs if sample_jobs else [
            {
                "title": "Python Developer",
                "company": "Tech Corp",
                "location": "Toronto, ON",
                "url": "https://test.com/python-developer",
                "description": "Python development role with Django",
                "job_type": "Full-time"
            },
            {
                "title": "Java Developer", 
                "company": "Software Inc",
                "location": "Vancouver, BC",
                "url": "https://test.com/java-developer",
                "description": "Java development with Spring framework",
                "job_type": "Full-time"
            }
        ]
        
        # Add multiple jobs
        for job in test_jobs:
            db.add_job(job)
        
        # Search for Python jobs
        python_jobs = db.search_jobs("Python")
        assert len(python_jobs) >= 1
        
        # Verify search results contain keyword
        for job in python_jobs:
            assert "Python" in job["title"] or "Python" in str(job.get("skills", []))
        
        db.close()
    
    def test_get_job_count_returns_correct_count(self, test_db, sample_jobs):
        """Test job count functionality."""
        db = test_db
        
        initial_count = db.get_job_count()
        assert initial_count == 0
        
        # Add jobs
        for i, job in enumerate(sample_jobs):
            job["job_url"] = f"https://test.com/job/{i}"
            db.add_job(job)
        
        final_count = db.get_job_count()
        assert final_count == len(sample_jobs)
        
        db.close()
    
    def test_delete_job_removes_from_database(self, test_db, sample_job):
        """Test job deletion functionality."""
        db = test_db
        
        # Add job
        sample_job["job_url"] = "https://test.com/unique-job"
        db.add_job(sample_job)
        
        # Verify job exists
        jobs = db.get_all_jobs()
        assert len(jobs) == 1
        job_id = jobs[0]["id"]
        
        # Delete job
        result = db.delete_job(job_id)
        assert result is True
        
        # Verify job is gone
        jobs = db.get_all_jobs()
        assert len(jobs) == 0
        
        db.close()


@pytest.mark.unit  
class TestJobDatabasePerformance:
    """Test database performance characteristics."""
    
    def test_batch_insert_performance(self, test_db, performance_timer):
        """Test that batch inserts complete within time limits."""
        db = test_db
        
        # Generate test jobs
        test_jobs = []
        for i in range(100):
            job = {
                "title": f"Test Job {i}",
                "company": f"Company {i}",
                "location": "Test Location",
                "job_url": f"https://test.com/job/{i}",
                "skills": "Python,Django"
            }
            test_jobs.append(job)
        
        # Time batch insert
        with performance_timer:
            for job in test_jobs:
                db.add_job(job)
        
        # Assert performance within acceptable limits (< 5 seconds for 100 jobs)
        assert performance_timer.elapsed < 5.0, f"Batch insert took {performance_timer.elapsed:.2f}s"
        
        # Verify all jobs were inserted
        assert db.get_job_count() == 100
        
        db.close()


@pytest.mark.unit
class TestJobDatabaseErrorHandling:
    """Test database error handling and edge cases."""
    
    def test_invalid_database_path_raises_error(self):
        """Test that invalid database path raises appropriate error."""
        # Use a path that cannot be created (invalid characters on Windows)
        invalid_path = "C:\\invalid<>path\\database.db" if os.name == 'nt' else "/dev/null/invalid/database.db"
        
        with pytest.raises(Exception):
            db = ModernJobDatabase(invalid_path)
            db.get_job_count()  # Try to use the database
    
    def test_add_job_with_missing_required_fields_handles_gracefully(self, test_db):
        """Test handling of jobs with missing required fields."""
        db = test_db
        
        incomplete_job = {
            "title": "Test Job"
            # Missing required company field
        }
        
        # Should raise TypeError for missing required fields
        with pytest.raises(TypeError):
            db.add_job(incomplete_job)
    
    def test_search_empty_database_returns_empty_list(self, test_db):
        """Test search on empty database returns empty results."""
        db = test_db
        
        results = db.search_jobs("any keyword")
        assert results == []
    
    def test_database_connection_recovery_after_error(self, test_db):
        """Test that database can recover from connection errors."""
        db = test_db
        
        # Force close connection
        if hasattr(db, 'conn'):
            db.conn.close()
        
        # Try to use database - should recover
        count = db.get_job_count()
        assert isinstance(count, int)
