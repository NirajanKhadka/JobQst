"""
Utils module for AutoJobAgent.
Provides utility functions for document generation, job analysis, and other core functionality.
"""

# Import key functions for easy access
from .document_generator import customize
from .job_analyzer import JobAnalyzer, JobRequirements
from .job_data_enhancer import JobDataEnhancer, JobEnhancement
from .dynamic_gmail_verifier import DynamicGmailVerifier, verify_applications_with_gmail, EmailMatch
from .enhanced_error_tolerance import ErrorTracker, RobustOperations
from .enhanced_database_manager import DatabaseManager
from .scraping_coordinator import OptimizedScrapingCoordinator, ScrapingMetrics
from .resume_analyzer import ResumeAnalyzer
from .manual_review_manager import ManualReviewManager
from .error_tolerance_handler import RobustOperationManager, SystemHealthMonitor
from .gmail_verifier import GmailVerifier, ApplicationConfirmation

__all__ = [
    'customize',
    'JobAnalyzer',
    'JobRequirements', 
    'JobDataEnhancer',
    'JobEnhancement',
    'DynamicGmailVerifier',
    'verify_applications_with_gmail',
    'EmailMatch',
    'ErrorTracker',
    'RobustOperations',
    'DatabaseManager',
    'OptimizedScrapingCoordinator',
    'ScrapingMetrics',
    'ResumeAnalyzer',
    'ManualReviewManager',
    'RobustOperationManager',
    'SystemHealthMonitor',
    'GmailVerifier',
    'ApplicationConfirmation'
]
