"""
Utils module - Import bridge for backward compatibility.
This file provides backward compatibility for imports after the refactor.
"""

# Import all functions from the correct location
from src.core.utils import *

# Re-export commonly used functions for backward compatibility
__all__ = [
    'get_available_profiles',
    'save_document_as_pdf',
    'load_profile',
    'detect_available_browsers',
    'hash_job',
    'load_session',
    'save_session',
    'check_pause_signal',
    'set_pause_signal',
    'create_temp_file',
    'get_browser_user_data_dir',
    'NeedsHumanException'
] 