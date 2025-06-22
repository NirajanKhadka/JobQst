"""
Test suite for the Universal Job Filtering system.
Tests date filtering (124 days vs 14 days for Eluta) and experience level detection (0-2 years).
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.job_filters import JobDateFilter, ExperienceLevelFilter, UniversalJobFilter


class TestJobDateFilter:
    """Test the job date filtering functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.eluta_filter = JobDateFilter("eluta")
        self.indeed_filter = JobDateFilter("indeed")
        self.generic_filter = JobDateFilter("unknown_site")
        
    def test_site_specific_date_limits(self):
        """Test that different sites have correct date limits."""
        # Eluta should have 14-day limit
        assert self.eluta_filter.current_config["max_age_days"] == 14
        
        # Indeed should have 124-day limit
        assert self.indeed_filter.current_config["max_age_days"] == 124
        
        # Unknown sites should default to 124 days
        assert self.generic_filter.current_config["max_age_days"] == 124
        
    def test_recent_jobs_hours(self):
        """Test that jobs posted hours ago are always considered recent."""
        job_hours = {"posted_date": "2 hours ago"}
        
        assert self.eluta_filter.is_job_recent_enough(job_hours) == True
        assert self.indeed_filter.is_job_recent_enough(job_hours) == True
        
    def test_recent_jobs_days(self):
        """Test day-based filtering with site-specific limits."""
        # Job posted 10 days ago
        job_10_days = {"posted_date": "10 days ago"}
        
        # Should be rejected by Eluta (14-day limit) but accepted by Indeed (124-day limit)
        assert self.eluta_filter.is_job_recent_enough(job_10_days) == True  # 10 < 14
        assert self.indeed_filter.is_job_recent_enough(job_10_days) == True  # 10 < 124
        
        # Job posted 20 days ago
        job_20_days = {"posted_date": "20 days ago"}
        
        # Should be rejected by Eluta but accepted by Indeed
        assert self.eluta_filter.is_job_recent_enough(job_20_days) == False  # 20 > 14
        assert self.indeed_filter.is_job_recent_enough(job_20_days) == True   # 20 < 124
        
    def test_old_jobs_weeks(self):
        """Test week-based filtering."""
        job_3_weeks = {"posted_date": "3 weeks ago"}
        
        # 3 weeks = 21 days
        assert self.eluta_filter.is_job_recent_enough(job_3_weeks) == False  # 21 > 14
        assert self.indeed_filter.is_job_recent_enough(job_3_weeks) == True   # 21 < 124
        
    def test_very_old_jobs_months(self):
        """Test month-based filtering."""
        job_2_months = {"posted_date": "2 months ago"}
        
        # 2 months = ~60 days
        assert self.eluta_filter.is_job_recent_enough(job_2_months) == False  # 60 > 14
        assert self.indeed_filter.is_job_recent_enough(job_2_months) == True   # 60 < 124
        
        job_5_months = {"posted_date": "5 months ago"}
        
        # 5 months = ~150 days
        assert self.eluta_filter.is_job_recent_enough(job_5_months) == False  # 150 > 14
        assert self.indeed_filter.is_job_recent_enough(job_5_months) == False  # 150 > 124
        
    def test_no_date_info(self):
        """Test that jobs without date info are considered recent."""
        job_no_date = {"title": "Software Developer"}
        
        assert self.eluta_filter.is_job_recent_enough(job_no_date) == True
        assert self.indeed_filter.is_job_recent_enough(job_no_date) == True


class TestExperienceLevelFilter:
    """Test the experience level filtering functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.filter = ExperienceLevelFilter()
        
    def test_definitely_entry_level_jobs(self):
        """Test jobs that are definitely entry level (0-2 years)."""
        entry_jobs = [
            {"title": "Junior Software Developer", "summary": "Entry level position"},
            {"title": "Data Analyst - Entry Level", "summary": "0-2 years experience required"},
            {"title": "Associate Developer", "summary": "Recent graduate welcome"},
            {"title": "Trainee Programmer", "summary": "No experience necessary"},
            {"title": "Software Developer Intern", "summary": "1-2 years experience preferred"}
        ]
        
        for job in entry_jobs:
            is_suitable, level, confidence = self.filter.is_suitable_experience_level(job)
            assert is_suitable == True
            assert level == "Entry"
            assert confidence >= 0.6
            
    def test_definitely_senior_jobs(self):
        """Test jobs that are definitely too senior (3+ years)."""
        senior_jobs = [
            {"title": "Senior Software Developer", "summary": "5+ years experience required"},
            {"title": "Lead Data Analyst", "summary": "Minimum 7 years experience"},
            {"title": "Principal Engineer", "summary": "10+ years in software development"},
            {"title": "Software Development Manager", "summary": "Team leadership experience"},
            {"title": "Director of Engineering", "summary": "Executive level position"}
        ]
        
        for job in senior_jobs:
            is_suitable, level, confidence = self.filter.is_suitable_experience_level(job)
            assert is_suitable == False
            assert level == "Senior"
            assert confidence >= 0.8
            
    def test_ambiguous_jobs(self):
        """Test jobs with ambiguous experience requirements."""
        ambiguous_jobs = [
            {"title": "Software Developer", "summary": "Join our development team"},
            {"title": "Data Analyst", "summary": "Analyze business data"},
            {"title": "Systems Engineer", "summary": "Work with our infrastructure"}
        ]
        
        for job in ambiguous_jobs:
            is_suitable, level, confidence = self.filter.is_suitable_experience_level(job)
            assert is_suitable == True  # Include by default as per memories
            assert level == "Unknown"
            assert confidence <= 0.6
            
    def test_positive_entry_indicators(self):
        """Test jobs with positive entry-level indicators."""
        positive_jobs = [
            {"title": "Software Developer", "summary": "Training provided, mentorship available"},
            {"title": "Data Analyst", "summary": "Growth opportunity, will train"},
            {"title": "Engineer", "summary": "Entry into technology, career development"}
        ]
        
        for job in positive_jobs:
            is_suitable, level, confidence = self.filter.is_suitable_experience_level(job)
            assert is_suitable == True
            assert confidence >= 0.6


class TestUniversalJobFilter:
    """Test the complete universal job filtering system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.eluta_filter = UniversalJobFilter("eluta")
        self.indeed_filter = UniversalJobFilter("indeed")
        
    def test_complete_filtering_entry_level_recent(self):
        """Test filtering of entry-level, recent jobs (should pass)."""
        good_job = {
            "title": "Junior Software Developer",
            "summary": "Entry level position for recent graduates",
            "posted_date": "2 days ago",
            "company": "Tech Corp"
        }
        
        # Should pass both Eluta and Indeed filters
        eluta_result, eluta_enhanced = self.eluta_filter.filter_job(good_job)
        indeed_result, indeed_enhanced = self.indeed_filter.filter_job(good_job)
        
        assert eluta_result == True
        assert indeed_result == True
        assert eluta_enhanced["experience_level"] == "Entry"
        assert eluta_enhanced["filter_passed"] == True
        
    def test_complete_filtering_senior_recent(self):
        """Test filtering of senior-level, recent jobs (should fail experience filter)."""
        senior_job = {
            "title": "Senior Software Developer",
            "summary": "5+ years experience required",
            "posted_date": "1 day ago",
            "company": "Tech Corp"
        }
        
        # Should fail both filters due to experience level
        eluta_result, eluta_enhanced = self.eluta_filter.filter_job(senior_job)
        indeed_result, indeed_enhanced = self.indeed_filter.filter_job(senior_job)
        
        assert eluta_result == False
        assert indeed_result == False
        assert eluta_enhanced["experience_level"] == "Senior"
        assert eluta_enhanced["filter_passed"] == False
        
    def test_complete_filtering_entry_level_old(self):
        """Test filtering of entry-level, old jobs (site-specific date filtering)."""
        old_job = {
            "title": "Junior Developer",
            "summary": "Entry level position",
            "posted_date": "20 days ago",
            "company": "Tech Corp"
        }
        
        # Should fail Eluta (14-day limit) but pass Indeed (124-day limit)
        eluta_result, _ = self.eluta_filter.filter_job(old_job)
        indeed_result, indeed_enhanced = self.indeed_filter.filter_job(old_job)
        
        assert eluta_result == False  # Too old for Eluta
        assert indeed_result == True   # Recent enough for Indeed
        assert indeed_enhanced["experience_level"] == "Entry"
        
    def test_batch_filtering(self):
        """Test batch filtering of multiple jobs."""
        jobs = [
            {"title": "Junior Developer", "posted_date": "1 day ago", "summary": "Entry level"},
            {"title": "Senior Developer", "posted_date": "1 day ago", "summary": "5+ years exp"},
            {"title": "Developer", "posted_date": "30 days ago", "summary": "Join our team"},
            {"title": "Entry Level Analyst", "posted_date": "2 days ago", "summary": "No experience required"}
        ]
        
        # Filter with Eluta (14-day limit)
        eluta_results = self.eluta_filter.filter_jobs_batch(jobs)
        
        # Should include: Junior Developer (entry + recent), Entry Level Analyst (entry + recent)
        # Should exclude: Senior Developer (too senior), Developer (too old for Eluta)
        assert len(eluta_results) == 2
        
        # Filter with Indeed (124-day limit)
        indeed_results = self.indeed_filter.filter_jobs_batch(jobs)
        
        # Should include: Junior Developer, Developer (now recent enough), Entry Level Analyst
        # Should exclude: Senior Developer (too senior)
        assert len(indeed_results) == 3


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
