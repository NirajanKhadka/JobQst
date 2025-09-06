"""
Data service for dashboard - Bridge to existing dash app data loader
Enhanced with intelligent query caching for improved performance
"""
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Import caching system
try:
    from .cache_service import (
        get_dashboard_cache, get_cached_aggregations,
        invalidate_profile_cache, get_cache_performance_stats
    )
    CACHING_AVAILABLE = True
except ImportError:
    logger.warning("Caching service not available")
    CACHING_AVAILABLE = False

# Import profile utilities
try:
    from ...utils.profile_helpers import get_available_profiles
    PROFILE_HELPERS_AVAILABLE = True
except ImportError:
    logger.warning("Profile helpers not available")
    PROFILE_HELPERS_AVAILABLE = False

try:
    # Import existing data loader
    from ..dash_app.utils.data_loader import DataLoader
    DASH_APP_AVAILABLE = True
except ImportError:
    logger.warning("Dash app data loader not available")
    DASH_APP_AVAILABLE = False
    DataLoader = None


class DataService:
    """Data service that bridges to existing dashboard data functionality"""
    
    def __init__(self):
        """Initialize data service"""
        self._data_loader = None
        self._cached_aggregations = None
        
        if DASH_APP_AVAILABLE:
            try:
                self._data_loader = DataLoader()
                logger.info("Data service initialized with dash app loader")
            except Exception as e:
                logger.error(f"Failed to initialize data loader: {e}")
        
        # Initialize caching if available
        if CACHING_AVAILABLE:
            try:
                self._cached_aggregations = get_cached_aggregations()
                logger.info("Data service initialized with caching support")
            except Exception as e:
                logger.error(f"Failed to initialize caching: {e}")
    
    @property
    def data_loader(self):
        """Get data loader instance"""
        if self._data_loader is None and DASH_APP_AVAILABLE:
            try:
                self._data_loader = DataLoader()
            except Exception as e:
                logger.error(f"Failed to create data loader: {e}")
        return self._data_loader
    
    def get_jobs_data(self, profile_name: str = 'Nirajan') -> List[Dict[str, Any]]:
        """Get jobs data for a profile"""
        if self.data_loader:
            try:
                df = self.data_loader.load_jobs_data(profile_name)
                return df.to_dict('records')
            except Exception as e:
                logger.error(f"Error loading jobs data: {e}")
                return []
        return []
    
    def get_available_profiles(self) -> List[str]:
        """Get list of available profiles"""
        if self.data_loader:
            try:
                return self.data_loader.get_available_profiles()
            except Exception as e:
                logger.error(f"Error getting profiles: {e}")
                return ['Nirajan']
        return ['Nirajan']
    
    def get_job_stats(self, profile_name: str = 'Nirajan') -> Dict[str, Any]:
        """Get job statistics for a profile"""
        if self.data_loader:
            try:
                return self.data_loader.get_job_stats(profile_name)
            except Exception as e:
                logger.error(f"Error getting job stats: {e}")
                return self._default_stats()
        return self._default_stats()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health information"""
        if self.data_loader:
            try:
                return self.data_loader.get_system_health()
            except Exception as e:
                logger.error(f"Error getting system health: {e}")
                return self._default_health()
        return self._default_health()
    
    def get_processing_status(self, profile_name: str = 'Nirajan') -> Dict[str, Any]:
        """Get processing status for a profile"""
        if self.data_loader:
            try:
                return self.data_loader.get_processing_status(profile_name)
            except Exception as e:
                logger.error(f"Error getting processing status: {e}")
                return self._default_processing_status()
        return self._default_processing_status()
    
    def _default_stats(self) -> Dict[str, Any]:
        """Default job statistics"""
        return {
            'total_jobs': 0,
            'new_jobs': 0,
            'applied_jobs': 0,
            'reviewed_jobs': 0,
            'average_match_score': 0.0
        }
    
    def _default_health(self) -> Dict[str, Any]:
        """Default system health"""
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_percent': 0,
            'db_status': 'unknown',
            'api_status': 'unknown'
        }
    
    def _default_processing_status(self) -> Dict[str, Any]:
        """Default processing status"""
        return {
            'current_operation': 'idle',
            'progress': 0,
            'jobs_processed': 0,
            'errors': 0,
            'last_run': None
        }
    
    def get_profiles(self) -> List[str]:
        """Get list of available user profiles"""
        if PROFILE_HELPERS_AVAILABLE:
            try:
                return get_available_profiles()
            except Exception as e:
                logger.error(f"Error getting profiles from helpers: {e}")
                return ['Nirajan']
        else:
            # Fallback to data loader method
            return self.get_available_profiles()
    
    def load_job_data(self, profile_name: str) -> pd.DataFrame:
        """Load job data for a specific profile and return as DataFrame"""
        try:
            jobs_data = self.get_jobs_data(profile_name)
            if jobs_data:
                return pd.DataFrame(jobs_data)
            else:
                # Return empty DataFrame with expected columns
                return pd.DataFrame(columns=[
                    'id', 'title', 'company', 'location', 'applied',
                    'match_score', 'scraped_at', 'experience_level'
                ])
        except Exception as e:
            logger.error(f"Error loading job data for {profile_name}: {e}")
            return pd.DataFrame()

    # ============= CACHED AGGREGATION METHODS =============

    def get_cached_company_stats(
        self, profile_name: str = 'Nirajan', top_n: int = 15
    ) -> Dict[str, Any]:
        """Get cached company statistics for improved performance"""
        if not CACHING_AVAILABLE or not self._cached_aggregations:
            # Fallback to regular job stats
            return self.get_job_stats(profile_name)
        
        try:
            df = self.load_job_data(profile_name)
            return self._cached_aggregations.get_company_stats(
                df, profile_name, top_n
            )
        except Exception as e:
            logger.error(f"Error getting cached company stats: {e}")
            return {'companies': [], 'counts': [], 'total_companies': 0}
    
    def get_cached_location_stats(
        self, profile_name: str = 'Nirajan', top_n: int = 10
    ) -> Dict[str, Any]:
        """Get cached location statistics for improved performance"""
        if not CACHING_AVAILABLE or not self._cached_aggregations:
            # Return basic location info
            return {'locations': [], 'counts': [], 'total_locations': 0}
        
        try:
            df = self.load_job_data(profile_name)
            return self._cached_aggregations.get_location_stats(
                df, profile_name, top_n
            )
        except Exception as e:
            logger.error(f"Error getting cached location stats: {e}")
            return {'locations': [], 'counts': [], 'total_locations': 0}
    
    def get_cached_job_metrics(
        self, profile_name: str = 'Nirajan'
    ) -> Dict[str, Any]:
        """Get cached job metrics for improved performance"""
        if not CACHING_AVAILABLE or not self._cached_aggregations:
            # Fallback to regular job stats
            return self.get_job_stats(profile_name)
        
        try:
            df = self.load_job_data(profile_name)
            return self._cached_aggregations.get_job_metrics(df, profile_name)
        except Exception as e:
            logger.error(f"Error getting cached job metrics: {e}")
            return {
                'total_jobs': 0,
                'avg_match_score': 0.0,
                'status_counts': {},
                'score_distribution': {'ranges': [], 'counts': []}
            }
    
    def invalidate_cache(self, profile_name: str = None) -> Dict[str, Any]:
        """
        Invalidate cache for profile or entire cache
        
        Args:
            profile_name: If provided, invalidate only this profile's cache
                         If None, clear entire cache
        
        Returns:
            Dictionary with invalidation results
        """
        if not CACHING_AVAILABLE:
            return {
                'success': False,
                'message': 'Caching not available',
                'invalidated_count': 0
            }
        
        try:
            if profile_name:
                count = invalidate_profile_cache(profile_name)
                return {
                    'success': True,
                    'message': (
                        f'Invalidated {count} entries for {profile_name}'
                    ),
                    'invalidated_count': count
                }
            else:
                cache = get_dashboard_cache()
                count = cache.invalidate()
                return {
                    'success': True,
                    'message': f'Invalidated entire cache ({count} entries)',
                    'invalidated_count': count
                }
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return {
                'success': False,
                'message': f'Cache invalidation failed: {e}',
                'invalidated_count': 0
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        if not CACHING_AVAILABLE:
            return {
                'cache_available': False,
                'message': 'Caching not available'
            }
        
        try:
            stats = get_cache_performance_stats()
            return {
                'cache_available': True,
                **stats
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                'cache_available': False,
                'message': f'Error getting stats: {e}'
            }


# Global instance
_data_service_instance = None


def get_data_service() -> DataService:
    """Get the global data service instance"""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance

