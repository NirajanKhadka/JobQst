"""
Job filtering utilities for matching and filtering job opportunities.
"""

import re
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from .job_data import JobData


@dataclass
class FilterCriteria:
    """Criteria for filtering jobs."""
    keywords: Optional[List[str]] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    company: Optional[str] = None
    remote_allowed: Optional[bool] = None
    skills_required: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None


class JobFilter:
    """Job filtering engine with multiple filtering strategies."""
    
    def __init__(self, criteria: FilterCriteria):
        self.criteria = criteria
    
    def filter_jobs(self, jobs: List[JobData]) -> List[JobData]:
        """Filter jobs based on criteria."""
        filtered_jobs = []
        
        for job in jobs:
            if self._matches_criteria(job):
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def _matches_criteria(self, job: JobData) -> bool:
        """Check if a job matches all criteria."""
        # Keyword matching
        if self.criteria.keywords and not self._matches_keywords(job):
            return False
        
        # Location matching
        if self.criteria.location and not self._matches_location(job):
            return False
        
        # Salary matching
        if self.criteria.salary_min or self.criteria.salary_max:
            if not self._matches_salary(job):
                return False
        
        # Experience level matching
        if self.criteria.experience_level and not self._matches_experience(job):
            return False
        
        # Job type matching
        if self.criteria.job_type and not self._matches_job_type(job):
            return False
        
        # Company matching
        if self.criteria.company and not self._matches_company(job):
            return False
        
        # Remote work matching
        if self.criteria.remote_allowed is not None and not self._matches_remote(job):
            return False
        
        # Skills matching
        if self.criteria.skills_required and not self._matches_skills(job):
            return False
        
        # Exclude keywords
        if self.criteria.exclude_keywords and self._matches_exclude_keywords(job):
            return False
        
        return True
    
    def _matches_keywords(self, job: JobData) -> bool:
        """Check if job matches any of the required keywords."""
        if not self.criteria.keywords:
            return True
        
        search_text = f"{job.title} {job.summary} {job.company}".lower()
        
        for keyword in self.criteria.keywords:
            if keyword.lower() in search_text:
                return True
        
        return False
    
    def _matches_location(self, job: JobData) -> bool:
        """Check if job location matches criteria."""
        if not self.criteria.location or not job.location:
            return True
        
        location_pattern = re.compile(re.escape(self.criteria.location.lower()))
        return bool(location_pattern.search(job.location.lower()))
    
    def _matches_salary(self, job: JobData) -> bool:
        """Check if job salary matches criteria."""
        # Extract salary from job data (assuming salary is stored as string or number)
        job_salary = self._extract_salary(job)
        
        if job_salary is None:
            return True  # If no salary info, don't filter out
        
        if self.criteria.salary_min and job_salary < self.criteria.salary_min:
            return False
        
        if self.criteria.salary_max and job_salary > self.criteria.salary_max:
            return False
        
        return True
    
    def _extract_salary(self, job: JobData) -> Optional[float]:
        """Extract salary from job data."""
        # This is a simplified implementation
        # In a real system, you might have structured salary data
        if hasattr(job, 'salary') and job.salary:
            try:
                return float(job.salary)
            except (ValueError, TypeError):
                pass
        
        # Try to extract from summary
        if job.summary:
            salary_pattern = r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+)?(?:year|month|hour)'
            match = re.search(salary_pattern, job.summary, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        return None
    
    def _matches_experience(self, job: JobData) -> bool:
        """Check if job experience level matches criteria."""
        if not self.criteria.experience_level or not job.summary:
            return True
        
        experience_levels = {
            'entry': ['entry', 'junior', 'beginner', '0-2', '0-1'],
            'mid': ['mid', 'intermediate', '3-5', '2-5'],
            'senior': ['senior', 'lead', 'principal', '5+', '6+'],
            'executive': ['executive', 'director', 'vp', 'cto', 'ceo']
        }
        
        target_level = self.criteria.experience_level.lower()
        if target_level not in experience_levels:
            return True
        
        search_text = job.summary.lower()
        for level_keyword in experience_levels[target_level]:
            if level_keyword in search_text:
                return True
        
        return False
    
    def _matches_job_type(self, job: JobData) -> bool:
        """Check if job type matches criteria."""
        if not self.criteria.job_type or not job.summary:
            return True
        
        job_types = {
            'full-time': ['full-time', 'full time', 'permanent'],
            'part-time': ['part-time', 'part time'],
            'contract': ['contract', 'contractor', 'temporary'],
            'internship': ['internship', 'intern', 'co-op']
        }
        
        target_type = self.criteria.job_type.lower()
        if target_type not in job_types:
            return True
        
        search_text = job.summary.lower()
        for type_keyword in job_types[target_type]:
            if type_keyword in search_text:
                return True
        
        return False
    
    def _matches_company(self, job: JobData) -> bool:
        """Check if company matches criteria."""
        if not self.criteria.company or not job.company:
            return True
        
        company_pattern = re.compile(re.escape(self.criteria.company.lower()))
        return bool(company_pattern.search(job.company.lower()))
    
    def _matches_remote(self, job: JobData) -> bool:
        """Check if remote work policy matches criteria."""
        if self.criteria.remote_allowed is None:
            return True
        
        if not job.summary:
            return True
        
        remote_keywords = ['remote', 'work from home', 'wfh', 'telecommute', 'virtual']
        has_remote = any(keyword in job.summary.lower() for keyword in remote_keywords)
        
        return has_remote == self.criteria.remote_allowed
    
    def _matches_skills(self, job: JobData) -> bool:
        """Check if job requires specified skills."""
        if not self.criteria.skills_required or not job.summary:
            return True
        
        search_text = job.summary.lower()
        required_skills = [skill.lower() for skill in self.criteria.skills_required]
        
        # Check if at least one required skill is mentioned
        for skill in required_skills:
            if skill in search_text:
                return True
        
        return False
    
    def _matches_exclude_keywords(self, job: JobData) -> bool:
        """Check if job contains excluded keywords."""
        if not self.criteria.exclude_keywords:
            return False
        
        search_text = f"{job.title} {job.summary}".lower()
        
        for keyword in self.criteria.exclude_keywords:
            if keyword.lower() in search_text:
                return True
        
        return False


def create_filter_from_profile(profile_data: Dict[str, Any]) -> JobFilter:
    """Create a job filter from user profile data."""
    criteria = FilterCriteria(
        keywords=profile_data.get('keywords', []),
        location=profile_data.get('location'),
        salary_min=profile_data.get('salary_min'),
        salary_max=profile_data.get('salary_max'),
        experience_level=profile_data.get('experience_level'),
        job_type=profile_data.get('job_type'),
        company=profile_data.get('preferred_companies', []),
        remote_allowed=profile_data.get('remote_allowed'),
        skills_required=profile_data.get('skills', []),
        exclude_keywords=profile_data.get('exclude_keywords', [])
    )
    
    return JobFilter(criteria)


def filter_jobs_by_priority(jobs: List[JobData], priority_keywords: List[str]) -> List[JobData]:
    """Filter and sort jobs by priority keywords."""
    if not priority_keywords:
        return jobs
    
    def calculate_priority_score(job: JobData) -> int:
        search_text = f"{job.title} {job.summary}".lower()
        score = 0
        for keyword in priority_keywords:
            if keyword.lower() in search_text:
                score += 1
        return score
    
    # Calculate priority scores
    jobs_with_scores = [(job, calculate_priority_score(job)) for job in jobs]
    
    # Sort by priority score (descending)
    jobs_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return only jobs with priority score > 0
    return [job for job, score in jobs_with_scores if score > 0]


def filter_duplicate_jobs(jobs: List[JobData], similarity_threshold: float = 0.8) -> List[JobData]:
    """Filter out duplicate or very similar jobs."""
    if not jobs:
        return []
    
    def calculate_similarity(job1: JobData, job2: JobData) -> float:
        """Calculate similarity between two jobs."""
        # Simple similarity based on title and company
        title_similarity = 1.0 if job1.title == job2.title else 0.0
        company_similarity = 1.0 if job1.company == job2.company else 0.0
        
        # Weighted average
        return (title_similarity * 0.7) + (company_similarity * 0.3)
    
    unique_jobs = []
    
    for job in jobs:
        is_duplicate = False
        
        for unique_job in unique_jobs:
            similarity = calculate_similarity(job, unique_job)
            if similarity >= similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_jobs.append(job)
    
    return unique_jobs 