"""
Utils module for AutoJobAgent.
Provides utility functions for document generation, job analysis, and other core functionality.
"""

# Import key functions for easy access
from .document_generator import customize
from .job_analysis_engine import JobAnalysisEngine
from .enhanced_error_tolerance import ErrorTracker, RobustOperations
from .enhanced_database_manager import DatabaseManager
from .scraping_coordinator import OptimizedScrapingCoordinator, ScrapingMetrics
from .resume_analyzer import ResumeAnalyzer
from .manual_review_manager import ManualReviewManager
from .error_tolerance_handler import RobustOperationManager, SystemHealthMonitor
from .simple_gmail_checker import SimpleGmailChecker, create_gmail_checker
from .profile_helpers import get_available_profiles

# Export new modules
from .job_analyzer import JobAnalyzer
from .job_data_consumer import JobDataConsumer
from .job_data_enhancer import JobDataEnhancer
from .gmail_verifier import GmailVerifier

# Export profile and job helpers
from .profile_helpers import load_profile
from .job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
from .file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv

# Export job filters
from .job_filters import JobFilter, JobDateFilter, ExperienceLevelFilter, UniversalJobFilter

__all__ = [
    'customize',
    'JobAnalysisEngine',
    'ErrorTracker',
    'RobustOperations',
    'DatabaseManager',
    'OptimizedScrapingCoordinator',
    'ScrapingMetrics',
    'ResumeAnalyzer',
    'ManualReviewManager',
    'RobustOperationManager',
    'SystemHealthMonitor',
    'SimpleGmailChecker',
    'create_gmail_checker',
    'get_available_profiles',
    'JobAnalyzer',
    'JobDataConsumer',
    'JobDataEnhancer',
    'GmailVerifier',
    'load_profile',
    'generate_job_hash',
    'is_duplicate_job',
    'sort_jobs',
    'save_jobs_to_json',
    'load_jobs_from_json',
    'save_jobs_to_csv',
    'JobFilter',
    'JobDateFilter',
    'ExperienceLevelFilter',
    'UniversalJobFilter'
]
