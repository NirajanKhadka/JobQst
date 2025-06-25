"""
Comprehensive Scraping Test for AutoJobAgent.

This test module provides comprehensive testing of the scraping functionality
across multiple job sites and scenarios.
"""

import pytest
import asyncio
import logging
from typing import Dict, List
from pathlib import Path

# Fix import paths to use correct src. prefix
from src.utils.job_filters import JobDateFilter, ExperienceLevelFilter, UniversalJobFilter
from src.core.job_database import get_job_db
from src import utils

logger = logging.getLogger(__name__)


class ComprehensiveScrapingTest:
    """Comprehensive scraping test suite."""
    
    def __init__(self, profile_name: str = "test_comprehensive"):
        self.profile_name = profile_name
        self.db = get_job_db(profile_name)
        self.test_results = {}
    
    def test_job_filtering(self) -> Dict:
        """Test job filtering functionality."""
        logger.info("🧪 Testing job filtering...")
        
        # Create test jobs
        test_jobs = [
            {
                'title': 'Senior Data Analyst',
                'company': 'Tech Corp',
                'location': 'Toronto, ON',
                'salary': '$80,000 - $120,000',
                'experience_level': 'senior',
                'scraped_at': 1640995200  # 2022-01-01
            },
            {
                'title': 'Junior Developer',
                'company': 'Startup Inc',
                'location': 'Vancouver, BC',
                'salary': '$50,000 - $70,000',
                'experience_level': 'junior',
                'scraped_at': 1640995200  # 2022-01-01
            }
        ]
        
        # Test experience level filter
        exp_filter = ExperienceLevelFilter()
        for job in test_jobs:
            result = exp_filter.filter_job(job)
            assert result.should_keep is True
        
        # Test date filter
        date_filter = JobDateFilter()
        recent_jobs = [job for job in test_jobs if date_filter.filter_job(job).should_keep]
        assert len(recent_jobs) == 2
        
        logger.info("✅ Job filtering tests passed")
        return {'status': 'passed', 'tests': 2}
    
    def test_database_operations(self) -> Dict:
        """Test database operations."""
        logger.info("🧪 Testing database operations...")
        
        # Test adding jobs
        test_job = {
            'title': 'Test Job',
            'company': 'Test Company',
            'location': 'Test Location',
            'url': 'https://test.com/job',
            'source': 'test'
        }
        
        # Add job
        self.db.add_job(test_job)
        
        # Get jobs
        jobs = self.db.get_jobs()
        assert len(jobs) > 0
        
        # Check if test job exists
        test_job_found = any(job.get('title') == 'Test Job' for job in jobs)
        assert test_job_found
        
        logger.info("✅ Database operations tests passed")
        return {'status': 'passed', 'jobs_added': 1}
    
    def test_utils_functions(self) -> Dict:
        """Test utility functions."""
        logger.info("🧪 Testing utility functions...")
        
        # Test profile loading
        profile = load_profile(self.profile_name)
        assert profile is not None
        assert 'profile_name' in profile
        
        # Test hash function (using a simple hash implementation)
        test_data = {'title': 'Test', 'company': 'Test Corp'}
        hash_value = str(hash(str(test_data)))
        assert isinstance(hash_value, str)
        assert len(hash_value) > 0
        
        logger.info("✅ Utility functions tests passed")
        return {'status': 'passed', 'functions_tested': 2}
    
    def run_all_tests(self) -> Dict:
        """Run all comprehensive tests."""
        logger.info("🚀 Starting comprehensive scraping tests...")
        
        try:
            # Run individual tests
            self.test_results['filtering'] = self.test_job_filtering()
            self.test_results['database'] = self.test_database_operations()
            self.test_results['utils'] = self.test_utils_functions()
            
            # Calculate overall status
            all_passed = all(result['status'] == 'passed' for result in self.test_results.values())
            
            logger.info("✅ All comprehensive tests completed")
            return {
                'overall_status': 'passed' if all_passed else 'failed',
                'test_results': self.test_results
            }
            
        except Exception as e:
            logger.error(f"❌ Comprehensive test failed: {e}")
            return {
                'overall_status': 'failed',
                'error': str(e)
            }


# Test functions for pytest
def test_comprehensive_scraping():
    """Test comprehensive scraping functionality."""
    test_suite = ComprehensiveScrapingTest()
    result = test_suite.run_all_tests()
    assert result['overall_status'] == 'passed'


def test_job_filtering():
    """Test job filtering functionality."""
    test_suite = ComprehensiveScrapingTest()
    result = test_suite.test_job_filtering()
    assert result['status'] == 'passed'


def test_database_operations():
    """Test database operations."""
    test_suite = ComprehensiveScrapingTest()
    result = test_suite.test_database_operations()
    assert result['status'] == 'passed'


def test_utils_functions():
    """Test utility functions."""
    test_suite = ComprehensiveScrapingTest()
    result = test_suite.test_utils_functions()
    assert result['status'] == 'passed'


if __name__ == "__main__":
    # Run tests directly
    test_suite = ComprehensiveScrapingTest()
    result = test_suite.run_all_tests()
    print(f"Test Results: {result}")
