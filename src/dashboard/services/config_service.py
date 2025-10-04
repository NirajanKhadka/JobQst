"""
Configuration service for dashboard
"""

import logging
from typing import Dict, Any, List

from src.dashboard.services.base_service import BaseService, cache_result

logger = logging.getLogger(__name__)

# Import profile service
try:
    from src.dashboard.services.profile_service import get_profile_service

    PROFILE_SERVICE_AVAILABLE = True
except ImportError:
    logger.warning("ProfileService not available")
    PROFILE_SERVICE_AVAILABLE = False

try:
    # Import existing config manager
    from src.dashboard.dash_app.utils.config_manager import (
        get_config as get_dashboard_config,
        DashboardConfig,
    )

    CONFIG_AVAILABLE = True
except ImportError:
    logger.warning("Dashboard config manager not available")
    CONFIG_AVAILABLE = False
    DashboardConfig = None


class ConfigService(BaseService):
    """Configuration service that bridges to existing config functionality"""

    def __init__(self):
        """Initialize config service"""
        super().__init__()
        self._config = None
        if CONFIG_AVAILABLE:
            try:
                self._config = get_dashboard_config()
                logger.info("Config service initialized with dashboard config")
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize config: {e}")
                self._initialized = False
        else:
            self._initialized = False

    def initialize(self) -> bool:
        """Initialize the service."""
        if CONFIG_AVAILABLE:
            try:
                self._config = get_dashboard_config()
                self._initialized = True
                logger.info("Config service initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize config: {e}")
                self._initialized = False
                return False
        return False

    def health_check(self) -> Dict[str, Any]:
        """Check service health status."""
        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "config_available": CONFIG_AVAILABLE,
            "profile_service_available": PROFILE_SERVICE_AVAILABLE,
            "has_config_instance": self._config is not None,
            "cache_stats": self.get_cache_stats(),
        }

    @property
    def config(self):
        """Get config instance"""
        if self._config is None and CONFIG_AVAILABLE:
            try:
                self._config = get_dashboard_config()
            except Exception as e:
                logger.error(f"Failed to create config: {e}")
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        if self.config:
            try:
                return self.config.get(key, default)
            except Exception as e:
                logger.error(f"Error getting config key {key}: {e}")
                return default
        return default

    def set(self, key: str, value: Any) -> bool:
        """Set configuration value by key"""
        if self.config:
            try:
                return self.config.set(key, value)
            except Exception as e:
                logger.error(f"Error setting config key {key}: {e}")
                return False
        return False

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        if self.config:
            try:
                return self.config.get_all()
            except Exception as e:
                logger.error(f"Error getting all config: {e}")
                return self._default_config()
        return self._default_config()

    def save(self) -> bool:
        """Save configuration to file"""
        if self.config:
            try:
                return self.config.save()
            except Exception as e:
                logger.error(f"Error saving config: {e}")
                return False
        return False

    def reload(self) -> bool:
        """Reload configuration from file"""
        if self.config:
            try:
                return self.config.reload()
            except Exception as e:
                logger.error(f"Error reloading config: {e}")
                return False
        return False

    def validate(self) -> bool:
        """Validate configuration"""
        if self.config:
            try:
                return self.config.validate()
            except Exception as e:
                logger.error(f"Error validating config: {e}")
                return False
        return False

    @cache_result(timeout=300)  # 5 minute cache
    def get_available_profiles(self) -> List[str]:
        """Get list of available user profiles"""
        if PROFILE_SERVICE_AVAILABLE:
            try:
                profile_service = get_profile_service()
                return profile_service.get_available_profiles()
            except Exception as e:
                logger.error(f"Error getting available profiles: {e}")
                return []
        else:
            logger.warning("ProfileService not available")
            return []

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "app": {"title": "JobQst Dashboard", "debug": True, "host": "127.0.0.1", "port": 8050},
            "data": {"refresh_interval": 30000, "max_jobs_display": 1000, "cache_timeout": 300},
            "ui": {"items_per_page": 25, "chart_height": 400},
            "features": {"auto_save": True, "real_time_updates": True, "export_enabled": True},
        }


# Global instance
_config_service_instance = None


def get_config_service() -> ConfigService:
    """Get the global config service instance"""
    global _config_service_instance
    if _config_service_instance is None:
        _config_service_instance = ConfigService()
    return _config_service_instance
