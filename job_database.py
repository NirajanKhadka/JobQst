"""
Job Database module - Import bridge for backward compatibility.
This file provides backward compatibility for imports after the refactor.
"""

# Import all functions from the correct location
from src.core.job_database import *

# Re-export commonly used functions for backward compatibility
__all__ = [
    'JobDatabase',
    'get_job_db',
    'create_job_db',
    'save_job',
    'get_jobs',
    'update_job_status',
    'delete_job',
    'get_job_by_id',
    'get_jobs_by_status',
    'get_jobs_by_profile',
    'get_jobs_by_company',
    'get_jobs_by_location',
    'get_jobs_by_date_range',
    'get_jobs_by_experience_level',
    'get_jobs_by_keyword',
    'get_jobs_by_site',
    'get_jobs_by_ats',
    'get_jobs_by_application_status',
    'get_jobs_by_interview_status',
    'get_jobs_by_offer_status',
    'get_jobs_by_rejection_status',
    'get_jobs_by_withdrawal_status',
    'get_jobs_by_manual_review_status',
    'get_jobs_by_unknown_status',
    'get_jobs_by_error_status',
    'get_jobs_by_timeout_status',
    'get_jobs_by_captcha_status',
    'get_jobs_by_network_error_status',
    'get_jobs_by_browser_error_status',
    'get_jobs_by_parsing_error_status',
    'get_jobs_by_validation_error_status',
    'get_jobs_by_database_error_status',
    'get_jobs_by_file_error_status',
    'get_jobs_by_permission_error_status',
    'get_jobs_by_resource_error_status',
    'get_jobs_by_configuration_error_status',
    'get_jobs_by_integration_error_status',
    'get_jobs_by_external_error_status',
    'get_jobs_by_unknown_error_status'
] 