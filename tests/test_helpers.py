#!/usr/bin/env python3
"""
Test data helpers for loading fixtures and test data.
Provides utilities for consistent test data access.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class _TestDataLoader:
    """Helper class for loading test data from fixtures."""
    
    def __init__(self):
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self._test_data = None
    
    @property
    def test_data(self) -> Dict[str, Any]:
        """Load test data from JSON fixture file."""
        if self._test_data is None:
            test_data_file = self.fixtures_dir / "test_data.json"
            with open(test_data_file, 'r', encoding='utf-8') as f:
                self._test_data = json.load(f)
        return self._test_data
    
    def get_sample_jobs(self) -> List[Dict[str, Any]]:
        """Get sample job listings for testing."""
        return self.test_data["sample_jobs"]
    
    def get_test_profiles(self) -> List[Dict[str, Any]]:
        """Get test user profiles."""
        return self.test_data["test_profiles"]
    
    def get_mock_scraping_responses(self) -> List[Dict[str, Any]]:
        """Get mock scraping responses for testing scrapers."""
        return self.test_data["mock_scraping_responses"]
    
    def get_performance_benchmarks(self) -> Dict[str, Any]:
        """Get performance benchmark thresholds."""
        return self.test_data["performance_benchmarks"]
    
    def get_sample_job_by_title(self, title: str) -> Dict[str, Any]:
        """Get a specific sample job by title."""
        for job in self.get_sample_jobs():
            if job["title"] == title:
                return job.copy()
        raise ValueError(f"No sample job found with title: {title}")
    
    def get_test_profile_by_name(self, name: str) -> Dict[str, Any]:
        """Get a specific test profile by name."""
        for profile in self.get_test_profiles():
            if profile["name"] == name:
                return profile.copy()
        raise ValueError(f"No test profile found with name: {name}")
    
    def create_job_with_skills(self, skills: List[str]) -> Dict[str, Any]:
        """Create a test job with specific skills."""
        base_job = self.get_sample_jobs()[0].copy()
        base_job["skills"] = skills
        base_job["description"] = f"Job requiring {', '.join(skills)} skills"
        base_job["job_url"] = f"https://test.com/job/{hash(tuple(skills))}"
        return base_job
    
    def create_profile_with_skills(self, skills: List[str], experience_years: int = 3) -> Dict[str, Any]:
        """Create a test profile with specific skills and experience."""
        base_profile = self.get_test_profiles()[0].copy()
        base_profile["skills"] = skills
        base_profile["experience_years"] = experience_years
        base_profile["name"] = f"Test User ({', '.join(skills[:2])})"
        return base_profile


# Global instance for easy access
test_data_loader = _TestDataLoader()


def load_sample_jobs() -> List[Dict[str, Any]]:
    """Convenience function to load sample jobs."""
    return test_data_loader.get_sample_jobs()


def load_test_profiles() -> List[Dict[str, Any]]:
    """Convenience function to load test profiles."""
    return test_data_loader.get_test_profiles()


def load_performance_benchmarks() -> Dict[str, Any]:
    """Convenience function to load performance benchmarks."""
    return test_data_loader.get_performance_benchmarks()


def create_test_job_batch(count: int = 10) -> List[Dict[str, Any]]:
    """Create a batch of test jobs for performance testing."""
    sample_jobs = load_sample_jobs()
    batch = []
    
    for i in range(count):
        job = sample_jobs[i % len(sample_jobs)].copy()
        job["title"] = f"{job['title']} {i+1}"
        job["job_url"] = f"https://test.com/job/{i+1}"
        job["company"] = f"{job['company']} Batch {i+1}"
        batch.append(job)
    
    return batch


def create_skill_matched_jobs(profile_skills: List[str]) -> List[Dict[str, Any]]:
    """Create jobs with varying skill matches to a profile."""
    jobs = []
    
    # Perfect match job
    perfect_job = test_data_loader.create_job_with_skills(profile_skills)
    perfect_job["title"] = "Perfect Match Job"
    jobs.append(perfect_job)
    
    # Partial match job (50% skills)
    partial_skills = profile_skills[:len(profile_skills)//2] + ["Extra Skill"]
    partial_job = test_data_loader.create_job_with_skills(partial_skills)
    partial_job["title"] = "Partial Match Job"
    jobs.append(partial_job)
    
    # No match job
    no_match_skills = ["Unrelated Skill 1", "Unrelated Skill 2"]
    no_match_job = test_data_loader.create_job_with_skills(no_match_skills)
    no_match_job["title"] = "No Match Job"
    jobs.append(no_match_job)
    
    return jobs
