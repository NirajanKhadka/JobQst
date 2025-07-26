#!/usr/bin/env python3
"""
Simple URL Filter - Basic but reliable job URL validation
"""

import re
from typing import Dict, List, Any, Tuple

class SimpleJobURLFilter:
    """Simple and reliable job URL filter."""
    
    def __init__(self):
        # Patterns for obviously broken URLs
        self.broken_patterns = [
            r'https://www\.eluta\.ca/job/\d+$',  # eluta.ca/job/1, job/2, etc.
            r'https://[^/]+/$',                  # Just domain with slash
            r'https://[^/]+$',                   # Just domain
            r'.*localhost.*',                    # Local URLs
            r'.*127\.0\.0\.1.*',                # Local IP
            r'.*test.*debug.*',                  # Test URLs
        ]
        
        # Minimum requirements for valid URLs
        self.min_url_length = 40  # Real job URLs are usually longer
        
    def is_valid_job_url(self, url: str) -> bool:
        """
        Simple validation - returns True if URL looks like a real job posting.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL appears valid
        """
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        
        # Basic length check
        if len(url) < self.min_url_length:
            return False
        
        # Check for broken patterns
        for pattern in self.broken_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return False
        
        # Must start with http/https
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Must have a meaningful path (not just domain)
        if url.count('/') < 3:  # https://domain.com/path
            return False
        
        # Should contain job-related indicators in the URL
        job_indicators = ['job', 'career', 'position', 'vacancy', 'employment', 'work']
        url_lower = url.lower()
        
        # Either the URL path contains job keywords OR it's from a known job board
        has_job_keyword = any(keyword in url_lower for keyword in job_indicators)
        
        # Known job board domains (even if they don't have job keywords in URL)
        job_board_domains = [
            'workday', 'greenhouse', 'lever', 'bamboohr', 'smartrecruiters',
            'jobvite', 'icims', 'taleo', 'successfactors', 'cornerstone',
            'bombardier.com', 'microsoft.com', 'google.com', 'amazon.com'
        ]
        
        is_known_job_board = any(domain in url_lower for domain in job_board_domains)
        
        return has_job_keyword or is_known_job_board
    
    def filter_jobs(self, jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter jobs into valid and invalid based on URL.
        
        Returns:
            Tuple of (valid_jobs, invalid_jobs)
        """
        valid_jobs = []
        invalid_jobs = []
        
        for job in jobs:
            url = job.get('url', '')
            
            if self.is_valid_job_url(url):
                valid_jobs.append(job)
            else:
                invalid_jobs.append(job)
        
        return valid_jobs, invalid_jobs
    
    def get_invalid_reason(self, url: str) -> str:
        """Get reason why URL is invalid."""
        if not url:
            return "Empty URL"
        
        if len(url) < self.min_url_length:
            return f"URL too short (< {self.min_url_length} chars)"
        
        for pattern in self.broken_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                if 'eluta.ca/job' in pattern:
                    return "Broken Eluta URL (missing job details)"
                return f"Matches broken pattern: {pattern}"
        
        if not url.startswith(('http://', 'https://')):
            return "Invalid URL scheme"
        
        if url.count('/') < 3:
            return "URL too simple (just domain)"
        
        return "No job indicators found"

# Global filter instance
_url_filter = None

def get_simple_url_filter() -> SimpleJobURLFilter:
    """Get global URL filter instance."""
    global _url_filter
    if _url_filter is None:
        _url_filter = SimpleJobURLFilter()
    return _url_filter