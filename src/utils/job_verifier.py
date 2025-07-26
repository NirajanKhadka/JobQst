#!/usr/bin/env python3
"""
Job Verifier - Ensures jobs are only marked as processed when all required fields are filled
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JobVerifier:
    """Verifies that jobs have all required fields before marking as processed."""
    
    # Required fields for a job to be considered "processed"
    REQUIRED_FIELDS = [
        'title',
        'company', 
        'description',
        'url'
    ]
    
    # Optional but important fields
    IMPORTANT_FIELDS = [
        'salary',
        'keywords',
        'location',
        'experience_level'
    ]
    
    # Fields that should not have placeholder values
    PLACEHOLDER_VALUES = [
        'Pending Processing',
        'Job from URL',
        'No title available',
        'No company available',
        'No description available',
        '',
        None
    ]
    
    def __init__(self):
        self.verification_stats = {
            'total_verified': 0,
            'passed_verification': 0,
            'failed_verification': 0,
            'common_missing_fields': {}
        }
    
    def verify_job_completeness(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify if a job has all required fields filled properly.
        
        Returns:
            Dict with verification results including:
            - is_complete: bool
            - missing_required: List[str]
            - missing_important: List[str]
            - has_placeholders: List[str]
            - completion_score: float (0.0 to 1.0)
        """
        self.verification_stats['total_verified'] += 1
        
        missing_required = []
        missing_important = []
        has_placeholders = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            value = job.get(field)
            if not value or value in self.PLACEHOLDER_VALUES:
                missing_required.append(field)
                # Track common missing fields
                self.verification_stats['common_missing_fields'][field] = \
                    self.verification_stats['common_missing_fields'].get(field, 0) + 1
        
        # Check important fields
        for field in self.IMPORTANT_FIELDS:
            value = job.get(field)
            if not value or value in self.PLACEHOLDER_VALUES:
                missing_important.append(field)
        
        # Check for placeholder values in any field
        for field, value in job.items():
            if value in self.PLACEHOLDER_VALUES:
                has_placeholders.append(field)
        
        # Calculate completion score
        total_fields = len(self.REQUIRED_FIELDS) + len(self.IMPORTANT_FIELDS)
        filled_fields = total_fields - len(missing_required) - len(missing_important)
        completion_score = filled_fields / total_fields if total_fields > 0 else 0.0
        
        is_complete = len(missing_required) == 0
        
        if is_complete:
            self.verification_stats['passed_verification'] += 1
        else:
            self.verification_stats['failed_verification'] += 1
        
        return {
            'is_complete': is_complete,
            'missing_required': missing_required,
            'missing_important': missing_important,
            'has_placeholders': has_placeholders,
            'completion_score': completion_score,
            'verification_timestamp': datetime.now().isoformat()
        }
    
    def get_recommended_status(self, job: Dict[str, Any]) -> str:
        """
        Get recommended status based on job completeness.
        
        Returns:
            'processed' - if all required fields are filled
            'needs_processing' - if missing required fields
            'scraped' - if only basic URL info available
        """
        verification = self.verify_job_completeness(job)
        
        if verification['is_complete']:
            return 'processed'
        elif len(verification['missing_required']) <= 2:  # Missing 1-2 required fields
            return 'needs_processing'
        else:
            return 'scraped'
    
    def should_mark_as_processed(self, job: Dict[str, Any]) -> bool:
        """
        Determine if a job should be marked as processed.
        
        Returns True only if ALL required fields are properly filled.
        """
        verification = self.verify_job_completeness(job)
        return verification['is_complete']
    
    def get_missing_fields_summary(self, job: Dict[str, Any]) -> str:
        """Get a human-readable summary of missing fields."""
        verification = self.verify_job_completeness(job)
        
        if verification['is_complete']:
            return "✅ Job is complete"
        
        summary_parts = []
        
        if verification['missing_required']:
            summary_parts.append(f"Missing required: {', '.join(verification['missing_required'])}")
        
        if verification['missing_important']:
            summary_parts.append(f"Missing important: {', '.join(verification['missing_important'])}")
        
        if verification['has_placeholders']:
            summary_parts.append(f"Has placeholders: {', '.join(verification['has_placeholders'])}")
        
        return " | ".join(summary_parts)
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        return {
            **self.verification_stats,
            'success_rate': (
                self.verification_stats['passed_verification'] / 
                max(self.verification_stats['total_verified'], 1)
            ) * 100
        }
    
    def reset_stats(self):
        """Reset verification statistics."""
        self.verification_stats = {
            'total_verified': 0,
            'passed_verification': 0,
            'failed_verification': 0,
            'common_missing_fields': {}
        }

# Global verifier instance
_job_verifier = None

def get_job_verifier() -> JobVerifier:
    """Get global job verifier instance."""
    global _job_verifier
    if _job_verifier is None:
        _job_verifier = JobVerifier()
    return _job_verifier