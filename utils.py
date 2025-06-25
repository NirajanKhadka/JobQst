"""
Utils module - Import bridge for backward compatibility.
This file provides backward compatibility for imports after the refactor.
"""

# Import all functions from the correct location
from src.utils.profile_helpers import load_profile, get_available_profiles
from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv
from src.utils.document_generator import customize, DocumentGenerator

# Re-export commonly used functions for backward compatibility
__all__ = [
    'get_available_profiles',
    'load_profile',
    'check_pause_signal',
    'set_pause_signal',
    'create_temp_file',
    'get_browser_user_data_dir',
    'NeedsHumanException',
    'generate_job_hash',
    'save_jobs_to_json',
    'load_jobs_from_json',
    'save_jobs_to_csv'
] 