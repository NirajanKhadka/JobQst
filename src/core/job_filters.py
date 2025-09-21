"""
Job filtering utilities to focus on relevant job types.
Filters out irrelevant jobs based on profile preferences.
"""

from typing import List, Dict, Any, Set
import re
from rich.console import Console

console = Console()


class JobRelevanceFilter:
    """Filter jobs based on relevance to user profile and preferences."""
    
    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.target_roles = self._extract_target_roles()
        self.excluded_keywords = self._get_excluded_keywords()
        
    def _extract_target_roles(self) -> Set[str]:
        """Extract target job roles from profile."""
        # Primary target roles based on profile
        target_roles = {
            "software developer",
            "python developer", 
            "software engineer",
            "python engineer",
            "application developer",
            "web developer",
            "api developer",
            "microservices developer"
        }
        
        # Add roles from profile keywords if they match patterns
        keywords = self.profile.get('keywords', [])
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if any(role in keyword_lower for role in ["developer", "engineer"]):
                if not any(excluded in keyword_lower for excluded in ["backend", "full stack", "fullstack", "front end", "frontend"]):
                    target_roles.add(keyword_lower)
        
        return target_roles
    
    def _get_excluded_keywords(self) -> Set[str]:
        """Get keywords that indicate irrelevant job types."""
        return {
            # Backend-specific roles (too narrow)
            "backend developer",
            "back-end developer", 
            "back end developer",
            "backend engineer",
            "back-end engineer",
            
            # Full-stack roles (too broad)
            "full stack developer",
            "fullstack developer", 
            "full-stack developer",
            "full stack engineer",
            "fullstack engineer",
            
            # Frontend-specific roles
            "frontend developer",
            "front-end developer",
            "front end developer",
            "ui developer",
            "react developer",
            
            # Very senior roles
            "principal engineer",
            "staff engineer", 
            "distinguished engineer",
            "chief technology officer",
            "engineering manager",
            "technical lead",
            
            # Specialized roles outside scope
            "devops engineer",
            "site reliability engineer",
            "platform engineer",
            "infrastructure engineer",
            "security engineer",
            "data engineer",  # Unless specifically wanted
            "machine learning engineer",  # Unless specifically wanted
            
            # Internship/junior roles (if not wanted)
            "intern",
            "co-op",
            "entry level",
            "junior developer"
        }
    
    def is_relevant_job(self, job: Dict[str, Any]) -> bool:
        """Check if a job is relevant based on title and description."""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        company = job.get('company', '').lower()
        
        # Skip if title contains excluded keywords
        for excluded in self.excluded_keywords:
            if excluded in title:
                return False
        
        # Check if title matches target roles
        for target_role in self.target_roles:
            if target_role in title:
                return True
        
        # Additional checks for software developer variations
        if any(term in title for term in ["software", "python", "application", "web"]):
            if any(term in title for term in ["developer", "engineer"]):
                # Make sure it's not backend/fullstack
                if not any(excluded in title for excluded in ["backend", "back-end", "full stack", "fullstack"]):
                    return True
        
        return False
    
    def filter_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter a list of jobs to only include relevant ones."""
        if not jobs:
            return []
        
        relevant_jobs = []
        filtered_count = 0
        
        for job in jobs:
            if self.is_relevant_job(job):
                relevant_jobs.append(job)
            else:
                filtered_count += 1
        
        console.print(f"[cyan]🎯 Job filtering: {len(relevant_jobs)} relevant, {filtered_count} filtered out[/cyan]")
        
        return relevant_jobs
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of filter configuration."""
        return {
            "target_roles": list(self.target_roles),
            "excluded_keywords": list(self.excluded_keywords),
            "profile_name": self.profile.get('name', 'Unknown')
        }


def filter_jobs_by_relevance(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convenience function to filter jobs by relevance."""
    filter_instance = JobRelevanceFilter(profile)
    return filter_instance.filter_jobs(jobs)


def filter_entry_level_jobs(jobs: List[Dict[str, Any]], include_entry_level: bool = True) -> List[Dict[str, Any]]:
    """Filter jobs based on experience level requirements."""
    if include_entry_level:
        return jobs
    
    filtered_jobs = []
    for job in jobs:
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        
        # Skip entry-level indicators
        entry_level_terms = ['intern', 'co-op', 'entry level', 'junior', 'graduate', 'new grad']
        
        if not any(term in title or term in description for term in entry_level_terms):
            filtered_jobs.append(job)
    
    return filtered_jobs


def remove_duplicates(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate jobs based on title and company."""
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        # Create a key based on title and company
        title = job.get('title', '').lower().strip()
        company = job.get('company', '').lower().strip()
        key = f"{title}|{company}"
        
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    
    if len(unique_jobs) != len(jobs):
        console.print(f"[cyan]🔄 Removed {len(jobs) - len(unique_jobs)} duplicate jobs[/cyan]")
    
    return unique_jobs


def apply_all_filters(jobs: List[Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Apply all job filters in sequence."""
    if not jobs:
        return []
    
    console.print(f"[cyan]🔍 Starting with {len(jobs)} jobs[/cyan]")
    
    # Remove duplicates first
    jobs = remove_duplicates(jobs)
    
    # Filter by relevance
    jobs = filter_jobs_by_relevance(jobs, profile)
    
    # Filter entry level if needed (based on profile experience)
    experience_level = profile.get('experience_level', '').lower()
    if 'senior' in experience_level or 'mid' in experience_level:
        jobs = filter_entry_level_jobs(jobs, include_entry_level=False)
    
    console.print(f"[green]✅ Final filtered jobs: {len(jobs)}[/green]")
    
    return jobs