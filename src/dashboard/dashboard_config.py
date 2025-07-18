#!/usr/bin/env python3
"""
Dashboard Configuration
Centralized configuration for the AutoJobAgent Streamlit dashboard.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import json


class DashboardConfig:
    """Configuration manager for the dashboard."""

    def __init__(self):
        self.config_file = Path("dashboard_config.json")
        self.default_config = {
            "dashboard": {
                "port": 8501,
                "host": "localhost",
                "auto_refresh": True,
                "refresh_interval": 30,
                "max_jobs_display": 2000,
                "cache_ttl": 60,
            },
            "ui": {
                "theme": "light",
                "layout": "wide",
                "sidebar_state": "expanded",
                "page_title": "AutoJobAgent Dashboard",
                "page_icon": "💼",
            },
            "charts": {"height": 400, "color_scheme": "viridis", "enable_animations": True},
            "table": {
                "height": 400,
                "enable_sorting": True,
                "enable_filtering": True,
                "rows_per_page": 25,
            },
            "logging": {
                "level": "INFO",
                "file": "dashboard.log",
                "max_size": "10MB",
                "backup_count": 5,
            },
            "performance": {
                "enable_caching": True,
                "cache_ttl": 60,
                "max_concurrent_requests": 10,
                "timeout": 30,
            },
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self.merge_configs(self.default_config, config)
            else:
                # Create default config file
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user config with defaults."""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation (e.g., 'dashboard.port')."""
        keys = key.split(".")
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> bool:
        """Set configuration value by dot notation."""
        keys = key.split(".")
        config = self.config
        try:
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            return self.save_config(self.config)
        except Exception as e:
            print(f"Error setting config: {e}")
            return False

    def get_dashboard_settings(self) -> Dict[str, Any]:
        """Get dashboard-specific settings."""
        return self.config.get("dashboard", {})

    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI-specific settings."""
        return self.config.get("ui", {})

    def get_chart_settings(self) -> Dict[str, Any]:
        """Get chart-specific settings."""
        return self.config.get("charts", {})

    def get_table_settings(self) -> Dict[str, Any]:
        """Get table-specific settings."""
        return self.config.get("table", {})

    def get_logging_settings(self) -> Dict[str, Any]:
        """Get logging-specific settings."""
        return self.config.get("logging", {})

    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-specific settings."""
        return self.config.get("performance", {})


# Global config instance
dashboard_config = DashboardConfig()


def get_config() -> DashboardConfig:
    """Get the global dashboard configuration."""
    return dashboard_config


def get_setting(key: str, default: Any = None) -> Any:
    """Get a configuration setting."""
    return dashboard_config.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """Set a configuration setting."""
    return dashboard_config.set(key, value)
