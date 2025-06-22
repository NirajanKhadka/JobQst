"""
ATS (Applicant Tracking System) module.
Provides ATS detection and job application functionality.
"""

from .ats_based_applicator import ATSBasedApplicator
from .enhanced_job_applicator import EnhancedJobApplicator
from .csv_applicator import CSVJobApplicator

# Import ATS submitter classes for registry
from .bamboohr import BambooHRSubmitter
from .greenhouse import GreenhouseSubmitter
from .icims import ICIMSSubmitter
from .lever import LeverSubmitter
from .workday import WorkdaySubmitter
from .fallback_submitters import FallbackATSSubmitter
from .base_submitter import BaseATSSubmitter

# ATS detection function
def detect(url: str) -> str:
    """
    Detect ATS system from URL.
    
    Args:
        url: Job application URL
        
    Returns:
        ATS system name (workday, icims, greenhouse, etc.)
    """
    url_lower = url.lower()
    
    if 'workday' in url_lower:
        return 'workday'
    elif 'icims' in url_lower:
        return 'icims'
    elif 'greenhouse' in url_lower:
        return 'greenhouse'
    elif 'lever' in url_lower:
        return 'lever'
    elif 'bamboohr' in url_lower:
        return 'bamboohr'
    elif 'smartrecruiters' in url_lower:
        return 'smartrecruiters'
    else:
        return 'unknown'

def get_submitter(ats_name: str, browser_context=None):
    """
    Get appropriate submitter for ATS system.
    
    Args:
        ats_name: ATS system name
        browser_context: Browser context for automation (unused for now)
        
    Returns:
        Appropriate applicator instance
    """
    # For now, return a generic applicator
    # The profile name will be set when the applicator is used
    return ATSBasedApplicator("Nirajan")  # Default profile name

class ATSRegistry:
    """Registry for ATS submitter classes."""
    
    def __init__(self):
        self.submitters = {
            'bamboohr': BambooHRSubmitter,
            'greenhouse': GreenhouseSubmitter,
            'icims': ICIMSSubmitter,
            'lever': LeverSubmitter,
            'workday': WorkdaySubmitter,
            'fallback': FallbackATSSubmitter,
            'base': BaseATSSubmitter,
        }
    
    def get_submitter(self, ats_name: str):
        """Get a submitter class by name."""
        return self.submitters.get(ats_name.lower())
    
    def list_submitters(self):
        """List all available submitter names."""
        return list(self.submitters.keys())
    
    def get_default_submitter(self):
        """Get the default submitter class."""
        return self.submitters.get('base')

def get_ats_registry():
    """Return a registry of ATS submitter classes by name."""
    return ATSRegistry()

__all__ = ['detect', 'get_submitter', 'ATSBasedApplicator', 'EnhancedJobApplicator', 'CSVJobApplicator']
