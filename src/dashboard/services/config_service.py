#!/usr/bin/env python3
"""
Configuration service for dashboard profile and settings management.
Handles profile validation, settings, and configuration state.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import json
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.profile_helpers import get_available_profiles

logger = logging.getLogger(__name__)


class ConfigService:
    """
    Service for managing dashboard configuration, profiles, and settings.
    Provides secure profile validation and settings management.
    """
    
    def __init__(self):
        """Initialize ConfigService with default settings."""
        self._cache: Dict[str, Any] = {}
        self._available_profiles: List[str] = []
        self._default_settings = {
            "auto_refresh": True,
            "refresh_interval": 10,
            "max_jobs_display": 1000,
            "cache_ttl": 300,
            "debug_mode": False
        }
    
    def get_available_profiles(self) -> List[str]:
        """
        Get list of available profiles with caching.
        
        Returns:
            List of valid profile names
        """
        if not self._available_profiles:
            try:
                self._available_profiles = get_available_profiles()
                logger.info(f"Found {len(self._available_profiles)} available profiles")
            except Exception as e:
                logger.error(f"Error getting available profiles: {e}")
                self._available_profiles = []
        
        return self._available_profiles
    
    def validate_profile_name(self, profile_name: str) -> bool:
        """
        Validate profile name against available profiles.
        
        Args:
            profile_name: Profile name to validate
            
        Returns:
            True if profile is valid, False otherwise
        """
        if not profile_name:
            return False
        
        available_profiles = self.get_available_profiles()
        is_valid = profile_name in available_profiles
        
        if not is_valid:
            logger.warning(f"Invalid profile name attempted: {profile_name}")
        
        return is_valid
    
    def get_default_profile(self) -> str:
        """
        Get default profile name.
        
        Returns:
            Default profile name or first available profile
        """
        available_profiles = self.get_available_profiles()
        
        if not available_profiles:
            logger.error("No available profiles found")
            return "default"
        
        # Prefer "Nirajan" if available, otherwise use first profile
        default_profile = "Nirajan" if "Nirajan" in available_profiles else available_profiles[0]
        return default_profile
    
    def get_profile_config(self, profile_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific profile.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Profile configuration dictionary
        """
        if not self.validate_profile_name(profile_name):
            logger.error(f"Cannot get config for invalid profile: {profile_name}")
            return {}
        
        try:
            profile_path = Path(f"profiles/{profile_name}")
            config_file = profile_path / "config.json"
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config
            else:
                # Return default config structure
                return {
                    "profile_name": profile_name,
                    "created_at": datetime.now().isoformat(),
                    "settings": self._default_settings.copy()
                }
                
        except Exception as e:
            logger.error(f"Error loading profile config for {profile_name}: {e}")
            return {}
    
    def save_profile_config(self, profile_name: str, config: Dict[str, Any]) -> bool:
        """
        Save configuration for a specific profile.
        
        Args:
            profile_name: Name of the profile
            config: Configuration dictionary to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.validate_profile_name(profile_name):
            logger.error(f"Cannot save config for invalid profile: {profile_name}")
            return False
        
        try:
            profile_path = Path(f"profiles/{profile_name}")
            profile_path.mkdir(parents=True, exist_ok=True)
            
            config_file = profile_path / "config.json"
            config["updated_at"] = datetime.now().isoformat()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Profile config saved for {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving profile config for {profile_name}: {e}")
            return False
    
    def get_dashboard_settings(self, profile_name: str = None) -> Dict[str, Any]:
        """
        Get dashboard-specific settings.
        
        Args:
            profile_name: Optional profile name for profile-specific settings
            
        Returns:
            Dashboard settings dictionary
        """
        settings = self._default_settings.copy()
        
        if profile_name and self.validate_profile_name(profile_name):
            profile_config = self.get_profile_config(profile_name)
            profile_settings = profile_config.get("settings", {})
            settings.update(profile_settings)
        
        return settings
    
    def update_dashboard_settings(self, profile_name: str, settings: Dict[str, Any]) -> bool:
        """
        Update dashboard settings for a profile.
        
        Args:
            profile_name: Profile name
            settings: Settings dictionary to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.validate_profile_name(profile_name):
            return False
        
        try:
            config = self.get_profile_config(profile_name)
            if "settings" not in config:
                config["settings"] = {}
            
            config["settings"].update(settings)
            return self.save_profile_config(profile_name, config)
            
        except Exception as e:
            logger.error(f"Error updating dashboard settings for {profile_name}: {e}")
            return False
    
    def get_database_path(self, profile_name: str) -> str:
        """
        Get database path for a profile.
        
        Args:
            profile_name: Profile name
            
        Returns:
            Database file path
        """
        if not self.validate_profile_name(profile_name):
            logger.error(f"Cannot get database path for invalid profile: {profile_name}")
            return ""
        
        return f"profiles/{profile_name}/{profile_name}.db"
    
    def validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize settings values.
        
        Args:
            settings: Settings dictionary to validate
            
        Returns:
            Validated and sanitized settings
        """
        validated = {}
        
        # Validate refresh_interval
        if "refresh_interval" in settings:
            interval = settings["refresh_interval"]
            if isinstance(interval, (int, float)) and 5 <= interval <= 300:
                validated["refresh_interval"] = int(interval)
            else:
                logger.warning(f"Invalid refresh_interval: {interval}, using default")
        
        # Validate auto_refresh
        if "auto_refresh" in settings:
            validated["auto_refresh"] = bool(settings["auto_refresh"])
        
        # Validate max_jobs_display
        if "max_jobs_display" in settings:
            max_jobs = settings["max_jobs_display"]
            if isinstance(max_jobs, int) and 100 <= max_jobs <= 5000:
                validated["max_jobs_display"] = max_jobs
            else:
                logger.warning(f"Invalid max_jobs_display: {max_jobs}, using default")
        
        # Validate cache_ttl
        if "cache_ttl" in settings:
            ttl = settings["cache_ttl"]
            if isinstance(ttl, int) and 60 <= ttl <= 3600:
                validated["cache_ttl"] = ttl
            else:
                logger.warning(f"Invalid cache_ttl: {ttl}, using default")
        
        # Validate debug_mode
        if "debug_mode" in settings:
            validated["debug_mode"] = bool(settings["debug_mode"])
        
        return validated
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get configuration service health status.
        
        Returns:
            Health status dictionary
        """
        try:
            profiles = self.get_available_profiles()
            
            return {
                "status": "healthy",
                "profiles_count": len(profiles),
                "available_profiles": profiles,
                "default_profile": self.get_default_profile(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking config service health: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def refresh_profiles(self):
        """Refresh the cached list of available profiles."""
        self._available_profiles = []
        self.get_available_profiles()


# Global service instance
_config_service = None

def get_config_service() -> ConfigService:
    """Get singleton ConfigService instance."""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service
