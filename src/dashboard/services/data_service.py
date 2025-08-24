"""
Data service for dashboard - Bridge to existing dash app data loader
"""
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

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
        if DASH_APP_AVAILABLE:
            try:
                self._data_loader = DataLoader()
                logger.info("Data service initialized with dash app loader")
            except Exception as e:
                logger.error(f"Failed to initialize data loader: {e}")
    
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


# Global instance
_data_service_instance = None


def get_data_service() -> DataService:
    """Get the global data service instance"""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance
