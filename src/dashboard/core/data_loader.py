#!/usr/bin/env python3
"""
Core Data Loading Module
Handles all data loading and caching for the dashboard.
"""

import pandas as pd
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# Import services
try:
    from src.dashboard.services.data_service import get_data_service
    HAS_DATA_SERVICE = True
except ImportError:
    HAS_DATA_SERVICE = False
    get_data_service = None

try:
    from src.core.job_database import ModernJobDatabase
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    ModernJobDatabase = None


def load_job_data(profile_name: str) -> pd.DataFrame:
    """Load job data from database using DataService or fallback."""
    try:
        if HAS_DATA_SERVICE and get_data_service:
            # Use DataService which handles caching and status derivation
            data_service = get_data_service()
            return data_service.load_job_data(profile_name)
        else:
            # Fallback to direct database access
            return _load_job_data_fallback(profile_name)
            
    except Exception as e:
        logger.error(f"Failed to load job data for profile {profile_name}: {e}")
        return pd.DataFrame()


def _load_job_data_fallback(profile_name: str) -> pd.DataFrame:
    """Fallback job data loading when service is not available."""
    try:
        if not HAS_DATABASE:
            logger.error("Database module not available")
            return pd.DataFrame()
            
        db_path = f"profiles/{profile_name}/{profile_name}.db"
        
        if not Path(db_path).exists():
            logger.warning(f"Database file not found: {db_path}")
            return pd.DataFrame()

        db = ModernJobDatabase(db_path=db_path)
        jobs = db.get_jobs(limit=2000)
        
        if jobs:
            df = pd.DataFrame(jobs)
            # Ensure proper datetime parsing
            for date_col in ["posted_date", "scraped_at", "created_at", "updated_at"]:
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            return df
        
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Fallback data loading failed: {e}")
        return pd.DataFrame()


def get_available_profiles() -> list:
    """Get list of available profiles."""
    try:
        from src.utils.profile_helpers import get_available_profiles
        return get_available_profiles()
    except ImportError:
        # Fallback: scan profiles directory
        profiles_dir = Path("profiles")
        if profiles_dir.exists():
            return [p.name for p in profiles_dir.iterdir() if p.is_dir()]
        return ["Nirajan"]  # Default fallback
