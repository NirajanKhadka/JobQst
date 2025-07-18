#!/usr/bin/env python3
"""
Data service for dashboard components.
Handles data loading, caching, and processing.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.job_database import get_job_db, ModernJobDatabase
from src.utils.profile_helpers import get_available_profiles

logger = logging.getLogger(__name__)


class DataService:
    """
    Service for managing dashboard data operations.
    Similar to consumer pattern but for data management.
    """
    
    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl  # 5 minutes default
        self._cache = {}
        self._cache_timestamps = {}
        
    def get_profiles(self) -> List[str]:
        """Get available profiles with caching"""
        cache_key = "profiles"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            profiles = get_available_profiles()
            self._set_cache(cache_key, profiles)
            return profiles
        except Exception as e:
            logger.error(f"Error getting profiles: {e}")
            return []
    
    def load_job_data(self, profile_name: str) -> pd.DataFrame:
        """Load job data for a specific profile with caching"""
        cache_key = f"jobs_{profile_name}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            # Get database connection
            db = get_job_db(profile_name)
            jobs = db.get_jobs(limit=1000)
            
            if jobs:
                df = pd.DataFrame(jobs)
                # Ensure proper datetime parsing
                for date_col in ["posted_date", "scraped_at", "updated_at"]:
                    if date_col in df.columns:
                        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                
                self._set_cache(cache_key, df)
                return df
            else:
                # Return empty DataFrame with expected columns
                empty_df = pd.DataFrame(columns=[
                    'id', 'title', 'company', 'location', 'applied', 
                    'match_score', 'scraped_at', 'experience_level'
                ])
                self._set_cache(cache_key, empty_df)
                return empty_df
                
        except Exception as e:
            logger.error(f"Error loading job data for profile {profile_name}: {e}")
            return pd.DataFrame()
    
    def get_job_metrics(self, profile_name: str) -> Dict[str, Any]:
        """Get job metrics for a profile"""
        cache_key = f"metrics_{profile_name}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            df = self.load_job_data(profile_name)
            
            if df.empty:
                metrics = {
                    'total_jobs': 0,
                    'applied_jobs': 0,
                    'pending_jobs': 0,
                    'avg_match_score': 0,
                    'unique_companies': 0,
                    'recent_jobs': 0
                }
            else:
                metrics = {
                    'total_jobs': len(df),
                    'applied_jobs': len(df[df.get('applied', pd.Series([0] * len(df))) == 1]),
                    'pending_jobs': len(df[df.get('applied', pd.Series([0] * len(df))) != 1]),
                    'avg_match_score': df['match_score'].mean() if 'match_score' in df.columns else 0,
                    'unique_companies': df['company'].nunique() if 'company' in df.columns else 0,
                    'recent_jobs': self._count_recent_jobs(df)
                }
            
            self._set_cache(cache_key, metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for profile {profile_name}: {e}")
            return {
                'total_jobs': 0,
                'applied_jobs': 0,
                'pending_jobs': 0,
                'avg_match_score': 0,
                'unique_companies': 0,
                'recent_jobs': 0
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            profiles = self.get_profiles()
            
            # Test database connectivity
            db_healthy = True
            error_msg = None
            
            if profiles:
                try:
                    test_profile = profiles[0]
                    db = get_job_db(test_profile)
                    db.get_job_count()
                except Exception as e:
                    db_healthy = False
                    error_msg = str(e)
            
            return {
                'status': 'healthy' if db_healthy else 'unhealthy',
                'profiles_count': len(profiles),
                'database_healthy': db_healthy,
                'error': error_msg,
                'cache_size': len(self._cache),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking health status: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def clear_cache(self, profile_name: Optional[str] = None):
        """Clear cache for specific profile or all profiles"""
        if profile_name:
            # Clear specific profile cache
            keys_to_remove = [k for k in self._cache.keys() if profile_name in k]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
        else:
            # Clear all cache
            self._cache.clear()
            self._cache_timestamps.clear()
        
        logger.info(f"Cache cleared for {'all profiles' if not profile_name else profile_name}")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache or cache_key not in self._cache_timestamps:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return elapsed < self.cache_ttl
    
    def _set_cache(self, cache_key: str, data: Any):
        """Set cache entry with timestamp"""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()
    
    def _count_recent_jobs(self, df: pd.DataFrame) -> int:
        """Count jobs scraped in the last 7 days"""
        if 'scraped_at' not in df.columns:
            return 0
        
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            recent_jobs = df[df['scraped_at'] > cutoff_date]
            return len(recent_jobs)
        except Exception:
            return 0


# Global service instance
_data_service = None

def get_data_service() -> DataService:
    """Get singleton data service instance"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service
