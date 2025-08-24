"""
Configuration service for dashboard
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    # Import existing config manager
    from ..dash_app.utils.config_manager import (
        get_config as get_dashboard_config,
        DashboardConfig
    )
    CONFIG_AVAILABLE = True
except ImportError:
    logger.warning("Dashboard config manager not available")
    CONFIG_AVAILABLE = False
    DashboardConfig = None


class ConfigService:
    """Configuration service that bridges to existing config functionality"""
    
    def __init__(self):
        """Initialize config service"""
        self._config = None
        if CONFIG_AVAILABLE:
            try:
                self._config = get_dashboard_config()
                logger.info("Config service initialized with dashboard config")
            except Exception as e:
                logger.error(f"Failed to initialize config: {e}")
    
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
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "app": {
                "title": "JobLens Dashboard",
                "debug": True,
                "host": "127.0.0.1",
                "port": 8050
            },
            "data": {
                "refresh_interval": 30000,
                "max_jobs_display": 1000,
                "cache_timeout": 300
            },
            "ui": {
                "items_per_page": 25,
                "chart_height": 400
            },
            "features": {
                "auto_save": True,
                "real_time_updates": True,
                "export_enabled": True
            }
        }


# Global instance
_config_service_instance = None


def get_config_service() -> ConfigService:
    """Get the global config service instance"""
    global _config_service_instance
    if _config_service_instance is None:
        _config_service_instance = ConfigService()
    return _config_service_instance
