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


class JobFiltersTest:
    """Job filters test suite."""
    
    def __init__(self, profile_name: str = "test_filters"):
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.test_results = {}
    
    def test_basic_filtering(self) -> Dict:
        """Test basic job filtering functionality."""
        logger.info("🧪 Testing basic job filtering...")
        
        # Create test jobs
        test_jobs = [
            {
                'title': 'Data Analyst',
                'company': 'Tech Corp',
                'location': 'Toronto, ON',
                'salary': '$60,000 - $80,000',
                'experience_level': 'mid',
                'scraped_at': 1640995200  # 2022-01-01
            },
            {
                'title': 'Senior Developer',
                'company': 'Startup Inc',
                'location': 'Vancouver, BC',
                'salary': '$90,000 - $120,000',
                'experience_level': 'senior',
                'scraped_at': 1640995200  # 2022-01-01
            }
        ]
        
        # Test that we can create filter objects
        exp_filter = ExperienceLevelFilter()
        date_filter = JobDateFilter()
        
        # Basic assertions
        assert exp_filter is not None
        assert date_filter is not None
        
        # Replace: exp_filter = ExperienceLevelFilter(['mid'])
        result = exp_filter.filter_job(test_jobs[0])
        assert result.should_keep is True  # or appropriate assertion based on test logic
        
        logger.info("✅ Basic filtering tests passed")
        return {'status': 'passed', 'tests': 1}
    
    def test_database_operations(self) -> Dict:
        """Test database operations."""
        logger.info("🧪 Testing database operations...")
        
        # Test adding jobs
        test_job = {
            'title': 'Filter Test Job',
            'company': 'Filter Test Company',
            'location': 'Filter Test Location',
            'url': 'https://filter-test.com/job',
            'source': 'test'
        }
        
        # Add job
        self.db.add_job(test_job)
        
        # Get jobs
        jobs = self.db.get_jobs()
        assert len(jobs) > 0
        
        logger.info("✅ Database operations tests passed")
        return {'status': 'passed', 'jobs_added': 1}
    
    def run_all_tests(self) -> Dict:
        """Run all job filter tests."""
        logger.info("🚀 Starting job filter tests...")
        
        try:
            # Run individual tests
            self.test_results['basic'] = self.test_basic_filtering()
            self.test_results['database'] = self.test_database_operations()
            
            # Calculate overall status
            all_passed = all(result['status'] == 'passed' for result in self.test_results.values())
            
            logger.info("✅ All job filter tests completed")
            return {
                'overall_status': 'passed' if all_passed else 'failed',
                'test_results': self.test_results
            }
            
        except Exception as e:
            logger.error(f"❌ Job filter test failed: {e}")
            return {
                'overall_status': 'failed',
                'error': str(e)
            }


# Test functions for pytest
def test_job_filters():
    """Test job filtering functionality."""
    test_suite = JobFiltersTest()
    result = test_suite.run_all_tests()
    assert result['overall_status'] == 'passed'


def test_basic_filtering():
    """Test basic filtering functionality."""
    test_suite = JobFiltersTest()
    result = test_suite.test_basic_filtering()
    assert result['status'] == 'passed'


def test_database_operations():
    """Test database operations."""
    test_suite = JobFiltersTest()
    result = test_suite.test_database_operations()
    assert result['status'] == 'passed'


if __name__ == "__main__":
    # Run tests directly
    test_suite = JobFiltersTest()
    result = test_suite.run_all_tests()
    print(f"Test Results: {result}")
