"""
Job Filters Module for AutoJobAgent.

This module provides filtering functionality for job data based on various criteria
such as experience level, salary, location, and other job attributes.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FilterCriteria:
    """Criteria for filtering jobs."""
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    locations: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    exclude_companies: Optional[List[str]] = None
    date_range_days: Optional[int] = None
    job_types: Optional[List[str]] = None
    remote_allowed: Optional[bool] = None


class JobDateFilter:
    """Filter jobs based on date criteria."""
    
    def __init__(self, date_range_days: Optional[int] = None):
        self.date_range_days = date_range_days
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs based on date criteria."""
        if not self.date_range_days:
            return jobs
        
        cutoff_date = datetime.now() - timedelta(days=self.date_range_days)
        filtered_jobs = []
        
        for job in jobs:
            try:
                # Extract date from job data
                job_date = self._extract_job_date(job)
                if job_date and job_date >= cutoff_date:
                    filtered_jobs.append(job)
            except Exception as e:
                logger.warning(f"⚠️ Error filtering job by date: {e}")
                continue
        
        return filtered_jobs
    
    def _extract_job_date(self, job: Dict) -> Optional[datetime]:
        """Extract date from job data."""
        # Try different date fields
        date_fields = ['posted_date', 'scraped_at', 'created_at', 'date']
        
        for field in date_fields:
            if field in job:
                try:
                    date_value = job[field]
                    if isinstance(date_value, (int, float)):
                        return datetime.fromtimestamp(date_value)
                    elif isinstance(date_value, str):
                        # Try common date formats
                        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y']:
                            try:
                                return datetime.strptime(date_value, fmt)
                            except ValueError:
                                continue
                except Exception:
                    continue
        
        return None


class ExperienceLevelFilter:
    """Filter jobs based on experience level."""
    
    def __init__(self, experience_levels: Optional[List[str]] = None):
        self.experience_levels = experience_levels or ['junior', 'mid', 'senior']
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs based on experience level."""
        if not self.experience_levels:
            return jobs
        
        filtered_jobs = []
        
        for job in jobs:
            try:
                job_level = self._extract_experience_level(job)
                if job_level in self.experience_levels:
                    filtered_jobs.append(job)
            except Exception as e:
                logger.warning(f"⚠️ Error filtering job by experience level: {e}")
                continue
        
        return filtered_jobs
    
    def _extract_experience_level(self, job: Dict) -> str:
        """Extract experience level from job data."""
        # Check if experience level is already extracted
        if 'experience_level' in job:
            return job['experience_level']
        
        # Extract from title and description
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        
        # Junior/Entry level indicators
        junior_keywords = ['entry level', 'junior', 'graduate', 'intern', 'trainee', '0-2 years', '1-2 years']
        if any(keyword in title or keyword in description for keyword in junior_keywords):
            return 'junior'
        
        # Senior level indicators
        senior_keywords = ['senior', 'lead', 'principal', 'manager', '5+ years', '7+ years', '10+ years']
        if any(keyword in title or keyword in description for keyword in senior_keywords):
            return 'senior'
        
        # Mid level indicators
        mid_keywords = ['mid-level', 'intermediate', '3-5 years', '4-6 years']
        if any(keyword in title or keyword in description for keyword in mid_keywords):
            return 'mid'
        
        return 'unknown'


class SalaryFilter:
    """Filter jobs based on salary criteria."""
    
    def __init__(self, min_salary: Optional[float] = None, max_salary: Optional[float] = None):
        self.min_salary = min_salary
        self.max_salary = max_salary
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs based on salary criteria."""
        if not self.min_salary and not self.max_salary:
            return jobs
        
        filtered_jobs = []
        
        for job in jobs:
            try:
                salary_range = self._extract_salary_range(job)
                if salary_range and self._salary_matches_criteria(salary_range):
                    filtered_jobs.append(job)
            except Exception as e:
                logger.warning(f"⚠️ Error filtering job by salary: {e}")
                continue
        
        return filtered_jobs
    
    def _extract_salary_range(self, job: Dict) -> Optional[Dict]:
        """Extract salary range from job data."""
        salary_text = job.get('salary', '')
        if not salary_text:
            return None
        
        try:
            # Extract numeric values
            numbers = re.findall(r'\$?(\d+(?:,\d+)*)', salary_text)
            if len(numbers) >= 2:
                min_salary = float(numbers[0].replace(',', ''))
                max_salary = float(numbers[1].replace(',', ''))
                return {'min': min_salary, 'max': max_salary, 'average': (min_salary + max_salary) / 2}
        except Exception:
            pass
        
        return None
    
    def _salary_matches_criteria(self, salary_range: Dict) -> bool:
        """Check if salary range matches criteria."""
        if self.min_salary and salary_range['max'] < self.min_salary:
            return False
        
        if self.max_salary and salary_range['min'] > self.max_salary:
            return False
        
        return True


class LocationFilter:
    """Filter jobs based on location criteria."""
    
    def __init__(self, locations: Optional[List[str]] = None):
        self.locations = locations
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs based on location criteria."""
        if not self.locations:
            return jobs
        
        filtered_jobs = []
        
        for job in jobs:
            try:
                job_location = job.get('location', '').lower()
                if any(location.lower() in job_location for location in self.locations):
                    filtered_jobs.append(job)
            except Exception as e:
                logger.warning(f"⚠️ Error filtering job by location: {e}")
                continue
        
        return filtered_jobs


class KeywordFilter:
    """Filter jobs based on keyword criteria."""
    
    def __init__(self, keywords: Optional[List[str]] = None, exclude_keywords: Optional[List[str]] = None):
        self.keywords = keywords
        self.exclude_keywords = exclude_keywords or []
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs based on keyword criteria."""
        filtered_jobs = []
        
        for job in jobs:
            try:
                if self._job_matches_keywords(job):
                    filtered_jobs.append(job)
            except Exception as e:
                logger.warning(f"⚠️ Error filtering job by keywords: {e}")
                continue
        
        return filtered_jobs
    
    def _job_matches_keywords(self, job: Dict) -> bool:
        """Check if job matches keyword criteria."""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        company = job.get('company', '').lower()
        
        # Check for excluded keywords
        for exclude_keyword in self.exclude_keywords:
            if (exclude_keyword.lower() in title or 
                exclude_keyword.lower() in description or 
                exclude_keyword.lower() in company):
                return False
        
        # Check for required keywords
        if self.keywords:
            for keyword in self.keywords:
                if (keyword.lower() in title or 
                    keyword.lower() in description or 
                    keyword.lower() in company):
                    return True
            return False
        
        return True


class UniversalJobFilter:
    """Universal job filter that combines multiple filtering criteria."""
    
    def __init__(self, criteria: FilterCriteria):
        self.criteria = criteria
        self.filters = []
        
        # Initialize individual filters
        if criteria.date_range_days:
            self.filters.append(JobDateFilter(criteria.date_range_days))
        
        if criteria.experience_levels:
            self.filters.append(ExperienceLevelFilter(criteria.experience_levels))
        
        if criteria.min_salary or criteria.max_salary:
            self.filters.append(SalaryFilter(criteria.min_salary, criteria.max_salary))
        
        if criteria.locations:
            self.filters.append(LocationFilter(criteria.locations))
        
        if criteria.keywords or criteria.exclude_keywords:
            self.filters.append(KeywordFilter(criteria.keywords, criteria.exclude_keywords))
    
    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Apply all filters to job list."""
        filtered_jobs = jobs
        
        for filter_obj in self.filters:
            filtered_jobs = filter_obj.filter_jobs(filtered_jobs)
            logger.info(f"📊 After {filter_obj.__class__.__name__}: {len(filtered_jobs)} jobs remaining")
        
        return filtered_jobs
    
    def get_filter_stats(self, original_count: int, filtered_count: int) -> Dict:
        """Get statistics about the filtering process."""
        return {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'removed_count': original_count - filtered_count,
            'retention_rate': (filtered_count / original_count * 100) if original_count > 0 else 0,
            'filters_applied': len(self.filters)
        }


# Convenience functions
def filter_jobs_by_experience(jobs: List[Dict], experience_levels: List[str]) -> List[Dict]:
    """Filter jobs by experience level."""
    filter_obj = ExperienceLevelFilter(experience_levels)
    return filter_obj.filter_jobs(jobs)


def filter_jobs_by_salary(jobs: List[Dict], min_salary: Optional[float] = None, max_salary: Optional[float] = None) -> List[Dict]:
    """Filter jobs by salary range."""
    filter_obj = SalaryFilter(min_salary, max_salary)
    return filter_obj.filter_jobs(jobs)


def filter_jobs_by_location(jobs: List[Dict], locations: List[str]) -> List[Dict]:
    """Filter jobs by location."""
    filter_obj = LocationFilter(locations)
    return filter_obj.filter_jobs(jobs)


def filter_jobs_by_keywords(jobs: List[Dict], keywords: Optional[List[str]] = None, exclude_keywords: Optional[List[str]] = None) -> List[Dict]:
    """Filter jobs by keywords."""
    filter_obj = KeywordFilter(keywords, exclude_keywords)
    return filter_obj.filter_jobs(jobs) 