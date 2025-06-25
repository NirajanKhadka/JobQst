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
    'get_available_profiles'
]
