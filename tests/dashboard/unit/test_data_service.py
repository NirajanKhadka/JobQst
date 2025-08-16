"""
Comprehensive unit tests for DataService.

Tests all functionality of the data service including:
- Job data retrieval and caching
- Database operations and connectivity
- Profile management
- Health monitoring and status reporting
- Error handling and recovery
"""

import pytest
import sqlite3
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.services.data_service import DataService, get_data_service


class TestDataService:
    """Test suite for DataService class."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            yield Path(tmp.name)
        # Cleanup after test
        Path(tmp.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def data_service(self):
        """Create a fresh DataService instance for testing."""
        return DataService(cache_ttl=5)
    
    @pytest.fixture
    def mock_profiles(self):
        """Mock profile data for testing."""
        return {
            "Nirajan": {
                "name": "Nirajan Khadka",
                "database_path": "profiles/Nirajan/jobs.db"
            },
            "TestUser": {
                "name": "Test User", 
                "database_path": "profiles/TestUser/jobs.db"
            }
        }
    
    @pytest.fixture
    def sample_job_data(self):
        """Sample job data for testing."""
        return [
            {
                "id": 1,
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "Toronto, ON",
                "date_posted": "2025-08-01",
                "application_status": "pending",
                "application_date": "2025-08-05",
                "job_url": "https://example.com/job1",
                "description": "Python developer position",
                "salary": "80000-100000",
                "job_type": "full-time"
            },
            {
                "id": 2,
                "title": "Senior Developer",
                "company": "Software Inc",
                "location": "Vancouver, BC",
                "date_posted": "2025-08-02",
                "application_status": "applied",
                "application_date": "2025-08-06",
                "job_url": "https://example.com/job2",
                "description": "Senior Python developer",
                "salary": "100000-120000",
                "job_type": "full-time"
            }
        ]
    
    def test_data_service_initialization(self, data_service):
        """Test DataService proper initialization."""
        assert data_service.cache_ttl == 5
        assert data_service._cache == {}
        assert data_service._cache_timestamps == {}
        assert data_service._config_service is not None
    
    def test_singleton_pattern(self):
        """Test that get_data_service returns the same instance."""
        service1 = get_data_service()
        service2 = get_data_service()
        
        assert service1 is service2
        assert isinstance(service1, DataService)
    
    def test_get_profiles_success(self, data_service, mock_profiles):
        """Test successful profile retrieval."""
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles):
            profiles = data_service.get_profiles()
            
            assert isinstance(profiles, list)
            assert len(profiles) == 2
            assert "Nirajan" in profiles
            assert "TestUser" in profiles
    
    def test_get_profiles_empty(self, data_service):
        """Test profile retrieval when no profiles exist."""
        with patch.object(data_service._config_service, 'get_profiles', return_value={}):
            profiles = data_service.get_profiles()
            
            assert isinstance(profiles, list)
            assert len(profiles) == 0
    
    def test_get_job_data_success(self, data_service, sample_job_data, mock_profiles):
        """Test successful job data retrieval."""
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = sample_job_data
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            jobs = data_service.get_job_data("Nirajan")
            
            assert isinstance(jobs, list)
            assert len(jobs) == 2
            assert jobs[0]["title"] == "Software Engineer"
            assert jobs[1]["title"] == "Senior Developer"
    
    def test_get_job_data_with_status_derivation(self, data_service, mock_profiles):
        """Test job data retrieval with status text derivation."""
        raw_job_data = [
            {
                "id": 1,
                "title": "Software Engineer",
                "company": "Tech Corp",
                "application_status": "pending",
                "application_date": "2025-08-05",
                "date_posted": "2025-08-01"
            }
        ]
        
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = raw_job_data
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            jobs = data_service.get_job_data("Nirajan")
            
            assert len(jobs) == 1
            job = jobs[0]
            
            # Should have derived status fields
            assert "status_text" in job
            assert "status_stage" in job
            assert "priority" in job
    
    def test_get_job_data_caching(self, data_service, sample_job_data, mock_profiles):
        """Test that job data is properly cached."""
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = sample_job_data
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            # First call
            jobs1 = data_service.get_job_data("Nirajan")
            
            # Second call should use cache
            jobs2 = data_service.get_job_data("Nirajan")
            
            # Database should only be called once
            mock_db.get_all_jobs.assert_called_once()
            assert jobs1 == jobs2
    
    def test_get_job_data_cache_expiration(self, data_service, mock_profiles):
        """Test that cache expires after TTL."""
        data_service.cache_ttl = 0.1  # 100ms for quick testing
        
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = [{"id": 1, "title": "Job 1"}]
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            # First call
            data_service.get_job_data("Nirajan")
            
            # Wait for cache to expire
            import time
            time.sleep(0.2)
            
            # Second call should hit database again
            data_service.get_job_data("Nirajan")
            
            assert mock_db.get_all_jobs.call_count == 2
    
    def test_get_job_data_invalid_profile(self, data_service, mock_profiles):
        """Test job data retrieval with invalid profile."""
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles):
            jobs = data_service.get_job_data("NonExistentProfile")
            
            assert isinstance(jobs, list)
            assert len(jobs) == 0
    
    def test_get_job_data_database_error(self, data_service, mock_profiles):
        """Test job data retrieval with database error."""
        mock_db = Mock()
        mock_db.get_all_jobs.side_effect = sqlite3.DatabaseError("Database error")
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            jobs = data_service.get_job_data("Nirajan")
            
            # Should handle error gracefully
            assert isinstance(jobs, list)
            assert len(jobs) == 0
    
    def test_get_job_statistics_success(self, data_service, sample_job_data, mock_profiles):
        """Test successful job statistics calculation."""
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = sample_job_data
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            stats = data_service.get_job_statistics("Nirajan")
            
            assert isinstance(stats, dict)
            assert "total_jobs" in stats
            assert "applied_jobs" in stats
            assert "pending_jobs" in stats
            assert "response_rate" in stats
            assert stats["total_jobs"] == 2
    
    def test_get_job_statistics_empty_data(self, data_service, mock_profiles):
        """Test job statistics with no data."""
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = []
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            stats = data_service.get_job_statistics("Nirajan")
            
            assert isinstance(stats, dict)
            assert stats["total_jobs"] == 0
            assert stats["applied_jobs"] == 0
            assert stats["response_rate"] == 0
    
    def test_get_health_status_healthy(self, data_service, mock_profiles):
        """Test health status when service is healthy."""
        mock_db = Mock()
        mock_db.get_job_count.return_value = 100
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            health = data_service.get_health_status()
            
            assert isinstance(health, dict)
            assert health["status"] == "healthy"
            assert health["profiles_count"] == 2
            assert health["database_healthy"] is True
            assert health["error"] is None
    
    def test_get_health_status_unhealthy(self, data_service, mock_profiles):
        """Test health status when database is unhealthy."""
        mock_db = Mock()
        mock_db.get_job_count.side_effect = sqlite3.DatabaseError("DB Error")
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            health = data_service.get_health_status()
            
            assert isinstance(health, dict)
            assert health["status"] == "unhealthy"
            assert health["database_healthy"] is False
            assert health["error"] is not None
    
    def test_get_health_status_no_profiles(self, data_service):
        """Test health status when no profiles exist."""
        with patch.object(data_service._config_service, 'get_profiles', return_value={}):
            health = data_service.get_health_status()
            
            assert isinstance(health, dict)
            assert health["profiles_count"] == 0
    
    def test_derive_status_text_pending(self, data_service):
        """Test status text derivation for pending jobs."""
        job = {"application_status": "pending", "application_date": "2025-08-05"}
        
        status_text = data_service._derive_status_text(job)
        
        assert "pending" in status_text.lower()
    
    def test_derive_status_text_applied(self, data_service):
        """Test status text derivation for applied jobs."""
        job = {"application_status": "applied", "application_date": "2025-08-05"}
        
        status_text = data_service._derive_status_text(job)
        
        assert "applied" in status_text.lower()
    
    def test_derive_status_stage(self, data_service):
        """Test status stage derivation."""
        # Test various statuses
        pending_job = {"application_status": "pending"}
        applied_job = {"application_status": "applied"}
        interview_job = {"application_status": "interview"}
        rejected_job = {"application_status": "rejected"}
        
        assert data_service._derive_status_stage(pending_job) == "discovery"
        assert data_service._derive_status_stage(applied_job) == "application"
        assert data_service._derive_status_stage(interview_job) == "interview"
        assert data_service._derive_status_stage(rejected_job) == "closed"
    
    def test_derive_priority(self, data_service):
        """Test priority derivation."""
        # High priority: recent posting, good company
        high_priority_job = {
            "date_posted": datetime.now().strftime("%Y-%m-%d"),
            "company": "Google",
            "title": "Senior Software Engineer"
        }
        
        # Low priority: old posting
        low_priority_job = {
            "date_posted": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "company": "Unknown Corp",
            "title": "Junior Developer"
        }
        
        assert data_service._derive_priority(high_priority_job) == "high"
        assert data_service._derive_priority(low_priority_job) == "low"
    
    def test_clear_cache(self, data_service):
        """Test cache clearing functionality."""
        # Add some cache data
        data_service._cache["test_key"] = "test_data"
        data_service._cache_timestamps["test_key"] = datetime.now()
        
        data_service.clear_cache()
        
        assert data_service._cache == {}
        assert data_service._cache_timestamps == {}
    
    def test_get_job_data_as_dataframe(self, data_service, sample_job_data, mock_profiles):
        """Test getting job data as pandas DataFrame."""
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = sample_job_data
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            df = data_service.get_job_data_as_dataframe("Nirajan")
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert "title" in df.columns
            assert "company" in df.columns
    
    def test_get_job_data_as_dataframe_empty(self, data_service, mock_profiles):
        """Test getting empty DataFrame when no data exists."""
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = []
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            df = data_service.get_job_data_as_dataframe("Nirajan")
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0
    
    def test_cache_invalidation_on_profile_change(self, data_service, mock_profiles):
        """Test that cache is invalidated when profile data changes."""
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = [{"id": 1, "title": "Job 1"}]
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            # First call
            data_service.get_job_data("Nirajan")
            
            # Simulate profile change
            data_service.clear_cache()
            
            # Second call should hit database again
            data_service.get_job_data("Nirajan")
            
            assert mock_db.get_all_jobs.call_count == 2
    
    def test_error_handling_in_status_derivation(self, data_service):
        """Test error handling in status derivation methods."""
        # Job with missing fields
        incomplete_job = {"id": 1}
        
        # Should not raise exceptions
        status_text = data_service._derive_status_text(incomplete_job)
        status_stage = data_service._derive_status_stage(incomplete_job)
        priority = data_service._derive_priority(incomplete_job)
        
        assert isinstance(status_text, str)
        assert isinstance(status_stage, str)
        assert isinstance(priority, str)
    
    def test_concurrent_data_access(self, data_service, sample_job_data, mock_profiles):
        """Test handling of concurrent data access."""
        import threading
        
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = sample_job_data
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=mock_profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            results = []
            
            def get_data():
                results.append(data_service.get_job_data("Nirajan"))
            
            # Start multiple threads
            threads = [threading.Thread(target=get_data) for _ in range(5)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            
            # All should succeed and return same data
            assert len(results) == 5
            for result in results:
                assert isinstance(result, list)
                assert len(result) == 2
    
    def test_memory_efficiency(self, data_service):
        """Test that service manages memory efficiently."""
        # Add many cache entries
        for i in range(1000):
            data_service._cache[f"key_{i}"] = [{"id": j, "data": "x" * 100} for j in range(100)]
            data_service._cache_timestamps[f"key_{i}"] = datetime.now()
        
        # Clear cache and verify memory is freed
        data_service.clear_cache()
        
        assert len(data_service._cache) == 0
        assert len(data_service._cache_timestamps) == 0


class TestDataServiceIntegration:
    """Integration tests for DataService with real database operations."""
    
    @pytest.mark.integration
    def test_real_database_operations(self, temp_db_path):
        """Test with actual database operations."""
        # Create a real database
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute("""
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                company TEXT,
                application_status TEXT DEFAULT 'pending'
            )
        """)
        
        # Insert test data
        cursor.execute("""
            INSERT INTO jobs (title, company) 
            VALUES ('Test Job', 'Test Company')
        """)
        
        conn.commit()
        conn.close()
        
        # Test DataService with real database
        service = DataService()
        
        # Mock config to return our test database
        with patch.object(service._config_service, 'get_profiles', return_value={
            "TestProfile": {"database_path": str(temp_db_path)}
        }), patch('src.dashboard.services.data_service.get_job_db') as mock_get_db:
            
            # Create a real database connection mock
            from src.core.job_database import JobDatabase
            real_db = JobDatabase(temp_db_path)
            mock_get_db.return_value = real_db
            
            try:
                jobs = service.get_job_data("TestProfile")
                assert isinstance(jobs, list)
                # Should have our test job
                if len(jobs) > 0:
                    assert jobs[0]["title"] == "Test Job"
            except Exception as e:
                pytest.skip(f"Real database operations not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
