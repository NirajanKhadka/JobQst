"""
Utils module for AutoJobAgent.
Provides utility functions for document generation, job analysis, and other core functionality.
"""

"""
Utils module for AutoJobAgent.
Provides utility functions for document generation, job analysis, and other core functionality.
"""

# Import key functions - dependencies are now properly installed
from src.document_modifier.document_modifier import customize

# Import core utilities
from .job_analysis_engine import JobAnalysisEngine
from .enhanced_error_tolerance import ErrorTracker, RobustOperations
from .scraping_coordinator import OptimizedScrapingCoordinator, ScrapingMetrics, ScrapingCoordinator
from .resume_analyzer import ResumeAnalyzer
from .manual_review_manager import ManualReviewManager
from .error_tolerance_handler import RobustOperationManager, SystemHealthMonitor
from .simple_gmail_checker import SimpleGmailChecker, create_gmail_checker

# Core profile and job helpers (should always work)
from .profile_helpers import get_available_profiles, load_profile
from .job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
from .file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv

# Additional modules  
from .job_analyzer import JobAnalyzer
from .job_data_consumer import JobDataConsumer
from .job_data_enhancer import JobDataEnhancer

# Export job filters from core module
from src.core.job_filters import JobFilter, filter_entry_level_jobs, remove_duplicates

__all__ = [
    "customize",
    "JobAnalysisEngine",
    "ErrorTracker",
    "RobustOperations",
    "OptimizedScrapingCoordinator",
    "ScrapingMetrics",
    "ScrapingCoordinator",
    "ResumeAnalyzer",
    "ManualReviewManager",
    "RobustOperationManager",
    "SystemHealthMonitor",
    "SimpleGmailChecker",
    "create_gmail_checker",
    "get_available_profiles",
    "JobAnalyzer",
    "JobDataConsumer",
    "JobDataEnhancer",
    "GmailVerifier",
    "load_profile",
    "generate_job_hash",
    "is_duplicate_job",
    "sort_jobs",
    "save_jobs_to_json",
    "load_jobs_from_json",
    "save_jobs_to_csv",
    "JobFilter",
    "filter_entry_level_jobs",
    "remove_duplicates",
]
