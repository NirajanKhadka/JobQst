"""
Utils module for AutoJobAgent.
Provides utility functions for job analysis, and other core functionality.
"""

# Import core utilities
# from .job_analysis_engine import JobAnalysisEngine  # Not available
from .error_tolerance import ErrorTracker, reliableOperations
# from .scraping_coordinator import OptimizedScrapingCoordinator, ScrapingMetrics, ScrapingCoordinator  # Not available
# from .resume_analyzer import ResumeAnalyzer  # Not available
from .manual_review_manager import ManualReviewManager
from .error_tolerance_handler import reliableOperationManager, SystemHealthMonitor
from .simple_gmail_checker import SimpleGmailChecker, create_gmail_checker

# Core profile and job helpers (should always work)
from .profile_helpers import get_available_profiles, load_profile
from .job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
from .file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv

# Additional modules (commented out if not available)
# from .job_analyzer import JobAnalyzer
# from .job_data_consumer import JobDataConsumer
# from .job_data_enhancer import JobDataEnhancer

# Export job filters from core module
from src.core.job_filters import JobFilter, filter_entry_level_jobs, remove_duplicates

__all__ = [
    "ErrorTracker",
    "reliableOperations",
    "ManualReviewManager",
    "reliableOperationManager",
    "SystemHealthMonitor",
    "SimpleGmailChecker",
    "create_gmail_checker",
    "get_available_profiles",
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

