"""
Configuration management for the dashboard
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DashboardConfig:
    """Manages dashboard configuration settings"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self._config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path"""
        return str(Path(__file__).parent / "config" / "dashboard_config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            else:
                logger.info("Configuration file not found, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "app": {
                "title": "JobQst Dashboard",
                "theme": "bootstrap",
                "debug": True,
                "host": "127.0.0.1",
                "port": 8050,
                "auto_reload": True
            },
            "data": {
                "refresh_interval": 30000,  # milliseconds
                "max_jobs_display": 1000,
                "cache_timeout": 300,  # seconds
                "export_formats": ["csv", "excel", "json"]
            },
            "ui": {
                "items_per_page": 25,
                "chart_height": 400,
                "sidebar_width": 250,
                "date_format": "%Y-%m-%d",
                "datetime_format": "%Y-%m-%d %H:%M:%S"
            },
            "features": {
                "auto_save": True,
                "real_time_updates": True,
                "export_enabled": True,
                "filters_enabled": True,
                "analytics_enabled": True
            },
            "alerts": {
                "show_success": True,
                "show_errors": True,
                "auto_dismiss": True,
                "dismiss_timeout": 5000  # milliseconds
            },
            "performance": {
                "lazy_loading": True,
                "pagination": True,
                "virtual_scrolling": False,
                "compression": True
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception as e:
            logger.error(f"Error getting config value for key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value by key (supports dot notation)"""
        try:
            keys = key.split('.')
            config = self._config
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            return True
            
        except Exception as e:
            logger.error(f"Error setting config value for key '{key}': {e}")
            return False
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def reload(self) -> bool:
        """Reload configuration from file"""
        try:
            self._config = self._load_config()
            logger.info("Configuration reloaded")
            return True
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self._config = self._get_default_config()
            logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            def deep_update(base_dict, update_dict):
                for key, value in update_dict.items():
                    if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                        deep_update(base_dict[key], value)
                    else:
                        base_dict[key] = value
            
            deep_update(self._config, updates)
            logger.info("Configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False
    
    def validate(self) -> bool:
        """Validate configuration"""
        try:
            required_sections = ['app', 'data', 'ui', 'features']
            for section in required_sections:
                if section not in self._config:
                    logger.error(f"Missing required configuration section: {section}")
                    return False
            
            # Validate specific values
            port = self.get('app.port')
            if not isinstance(port, int) or port < 1 or port > 65535:
                logger.error("Invalid port number in configuration")
                return False
            
            refresh_interval = self.get('data.refresh_interval')
            if not isinstance(refresh_interval, int) or refresh_interval < 1000:
                logger.error("Invalid refresh interval in configuration")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return False

# Global configuration instance
_config_instance = None

def get_config() -> DashboardConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = DashboardConfig()
    return _config_instance

def reload_config():
    """Reload the global configuration"""
    global _config_instance
    if _config_instance:
        _config_instance.reload()
    else:
        _config_instance = DashboardConfig()

# Convenience functions
def get_app_config():
    """Get app configuration"""
    return get_config().get('app', {})

def get_ui_config():
    """Get UI configuration"""
    return get_config().get('ui', {})

def get_data_config():
    """Get data configuration"""
    return get_config().get('data', {})

def get_features_config():
    """Get features configuration"""
    return get_config().get('features', {})
