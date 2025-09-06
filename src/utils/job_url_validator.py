#!/usr/bin/env python3
"""
Job URL Validator - Filters out invalid, broken, or low-quality job URLs
"""

import re
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JobURLValidator:
    """Validates and filters job URLs to ensure they're legitimate and processable."""
    
    def __init__(self):
        # Known job board domains and their URL patterns
        self.job_board_patterns = {
            'eluta': {
                'domain': 'eluta.ca',
                'valid_patterns': [
                    r'https://www\.eluta\.ca/job/[a-zA-Z0-9\-]+/\d+',  # Real Eluta URLs
                    r'https://www\.eluta\.ca/jobs/[a-zA-Z0-9\-]+',
                ],
                'invalid_patterns': [
                    r'https://www\.eluta\.ca/job/\d+$',  # Just job/1, job/2, etc.
                    r'https://www\.eluta\.ca/job/[^/]+$',  # Missing job ID
                ]
            },
            'workday': {
                'domain': 'myworkdayjobs.com',
                'valid_patterns': [
                    r'https://[^.]+\.wd\d+\.myworkdayjobs\.com/.+/job/.+',
                ],
                'invalid_patterns': [
                    r'https://[^.]+\.wd\d+\.myworkdayjobs\.com/$',  # Just domain
                ]
            },
            'greenhouse': {
                'domain': 'greenhouse.io',
                'valid_patterns': [
                    r'https://job-boards\.greenhouse\.io/[^/]+/jobs/\d+',
                    r'https://boards\.greenhouse\.io/[^/]+/jobs/\d+',
                ],
                'invalid_patterns': []
            },
            'lever': {
                'domain': 'lever.co',
                'valid_patterns': [
                    r'https://jobs\.lever\.co/[^/]+/[a-f0-9\-]+',
                ],
                'invalid_patterns': []
            },
            'indeed': {
                'domain': 'indeed.com',
                'valid_patterns': [
                    r'https://[^.]*\.indeed\.com/viewjob\?jk=.+',
                ],
                'invalid_patterns': []
            },
            'linkedin': {
                'domain': 'linkedin.com',
                'valid_patterns': [
                    r'https://www\.linkedin\.com/jobs/view/\d+',
                ],
                'invalid_patterns': []
            }
        }
        
        # Generic invalid patterns that apply to all URLs
        self.generic_invalid_patterns = [
            r'https?://[^/]+/$',  # Just domain with trailing slash
            r'https?://[^/]+$',   # Just domain
            r'.*\?.*test.*',      # Test URLs
            r'.*\?.*debug.*',     # Debug URLs
            r'.*localhost.*',     # Local development URLs
            r'.*127\.0\.0\.1.*',  # Local IP URLs
        ]
        
        # Minimum URL length (very short URLs are likely invalid)
        self.min_url_length = 30
        
        # Maximum URL length (extremely long URLs might be malformed)
        self.max_url_length = 500
        
        self.validation_stats = {
            'total_validated': 0,
            'valid_urls': 0,
            'invalid_urls': 0,
            'invalid_reasons': {}
        }
    
    def validate_job_url(self, url: str) -> Dict[str, Any]:
        """
        Validate a job URL and return detailed validation results.
        
        Returns:
            Dict with validation results including:
            - is_valid: bool
            - reason: str (if invalid)
            - job_board: str (detected job board)
            - confidence: float (0.0 to 1.0)
            - suggestions: List[str] (improvement suggestions)
        """
        self.validation_stats['total_validated'] += 1
        
        if not url or not isinstance(url, str):
            return self._invalid_result("URL is empty or not a string")
        
        url = url.strip()
        
        # Basic URL format validation
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return self._invalid_result("Invalid URL format")
        except Exception:
            return self._invalid_result("URL parsing failed")
        
        # Length validation
        if len(url) < self.min_url_length:
            return self._invalid_result(f"URL too short (min {self.min_url_length} chars)")
        
        if len(url) > self.max_url_length:
            return self._invalid_result(f"URL too long (max {self.max_url_length} chars)")
        
        # Check generic invalid patterns
        for pattern in self.generic_invalid_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return self._invalid_result(f"Matches invalid pattern: {pattern}")
        
        # Detect job board and validate against specific patterns
        job_board = self._detect_job_board(url)
        
        if job_board == 'unknown':
            # For unknown job boards, do basic validation
            return self._validate_unknown_job_board(url)
        
        # Validate against job board specific patterns
        board_config = self.job_board_patterns[job_board]
        
        # Check invalid patterns first
        for invalid_pattern in board_config['invalid_patterns']:
            if re.match(invalid_pattern, url, re.IGNORECASE):
                return self._invalid_result(f"Matches {job_board} invalid pattern")
        
        # Check valid patterns
        is_valid_pattern = False
        for valid_pattern in board_config['valid_patterns']:
            if re.match(valid_pattern, url, re.IGNORECASE):
                is_valid_pattern = True
                break
        
        if not is_valid_pattern and board_config['valid_patterns']:
            return self._invalid_result(f"Doesn't match any {job_board} valid patterns")
        
        # URL is valid
        self.validation_stats['valid_urls'] += 1
        
        return {
            'is_valid': True,
            'job_board': job_board,
            'confidence': 0.9,  # High confidence for known patterns
            'validation_timestamp': datetime.now().isoformat(),
            'suggestions': []
        }
    
    def _detect_job_board(self, url: str) -> str:
        """Detect which job board a URL belongs to."""
        url_lower = url.lower()
        
        for board_name, config in self.job_board_patterns.items():
            if config['domain'] in url_lower:
                return board_name
        
        return 'unknown'
    
    def _validate_unknown_job_board(self, url: str) -> Dict[str, Any]:
        """Validate URLs from unknown job boards with basic checks."""
        parsed = urllib.parse.urlparse(url)
        
        # Must have a path (not just domain)
        if not parsed.path or parsed.path == '/':
            return self._invalid_result("Unknown job board URL has no path")
        
        # Should contain job-related keywords in path
        job_keywords = ['job', 'career', 'position', 'vacancy', 'opening', 'employment']
        path_lower = parsed.path.lower()
        
        has_job_keyword = any(keyword in path_lower for keyword in job_keywords)
        
        if not has_job_keyword:
            return self._invalid_result("URL doesn't contain job-related keywords")
        
        # URL seems valid for unknown job board
        self.validation_stats['valid_urls'] += 1
        
        return {
            'is_valid': True,
            'job_board': 'unknown',
            'confidence': 0.6,  # Lower confidence for unknown boards
            'validation_timestamp': datetime.now().isoformat(),
            'suggestions': ['Consider adding this job board to known patterns']
        }
    
    def _invalid_result(self, reason: str) -> Dict[str, Any]:
        """Create an invalid validation result."""
        self.validation_stats['invalid_urls'] += 1
        
        # Track invalid reasons
        self.validation_stats['invalid_reasons'][reason] = \
            self.validation_stats['invalid_reasons'].get(reason, 0) + 1
        
        return {
            'is_valid': False,
            'reason': reason,
            'job_board': 'unknown',
            'confidence': 0.0,
            'validation_timestamp': datetime.now().isoformat(),
            'suggestions': ['Fix URL format or remove from database']
        }
    
    def filter_valid_jobs(self, jobs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filter a list of jobs, separating valid from invalid ones.
        
        Returns:
            Tuple of (valid_jobs, invalid_jobs)
        """
        valid_jobs = []
        invalid_jobs = []
        
        for job in jobs:
            url = job.get('url', '')
            validation = self.validate_job_url(url)
            
            # Add validation info to job
            job['url_validation'] = validation
            
            if validation['is_valid']:
                valid_jobs.append(job)
            else:
                invalid_jobs.append(job)
        
        return valid_jobs, invalid_jobs
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        total = max(self.validation_stats['total_validated'], 1)
        
        return {
            **self.validation_stats,
            'valid_percentage': (self.validation_stats['valid_urls'] / total) * 100,
            'invalid_percentage': (self.validation_stats['invalid_urls'] / total) * 100
        }
    
    def suggest_url_fixes(self, invalid_url: str) -> List[str]:
        """Suggest possible fixes for invalid URLs."""
        suggestions = []
        
        # Common Eluta URL fixes
        if 'eluta.ca/job/' in invalid_url:
            if re.match(r'https://www\.eluta\.ca/job/\d+$', invalid_url):
                suggestions.append("This appears to be a broken Eluta URL. Real Eluta URLs should include job title and ID.")
                suggestions.append("Example: https://www.eluta.ca/job/python-developer/12345")
        
        # Generic suggestions
        if len(invalid_url) < 30:
            suggestions.append("URL is too short - it might be incomplete")
        
        if not any(keyword in invalid_url.lower() for keyword in ['job', 'career', 'position']):
            suggestions.append("URL doesn't contain job-related keywords")
        
        return suggestions
    
    def reset_stats(self):
        """Reset validation statistics."""
        self.validation_stats = {
            'total_validated': 0,
            'valid_urls': 0,
            'invalid_urls': 0,
            'invalid_reasons': {}
        }

# Global validator instance
_url_validator = None

def get_job_url_validator() -> JobURLValidator:
    """Get global job URL validator instance."""
    global _url_validator
    if _url_validator is None:
        _url_validator = JobURLValidator()
    return _url_validator
