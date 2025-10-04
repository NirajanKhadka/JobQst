"""
Profile Service for Dashboard
Centralized profile management with caching to eliminate duplicate profile loading logic
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

# Import profile utilities
try:
    from src.utils.profile_helpers import get_available_profiles as _get_available_profiles
    from src.core.user_profile_manager import get_profile_manager, ProfileData

    PROFILE_SYSTEM_AVAILABLE = True
except ImportError:
    logger.warning("Profile system not available")
    PROFILE_SYSTEM_AVAILABLE = False
    ProfileData = Any  # Type placeholder when not available


class ProfileService:
    """
    Centralized profile service with caching

    Features:
    - Cached profile list retrieval
    - Profile validation
    - Thread-safe operations
    - Automatic cache invalidation
    """

    def __init__(self, cache_ttl_seconds: int = 300):
        """
        Initialize profile service

        Args:
            cache_ttl_seconds: Cache TTL in seconds (default: 5 minutes)
        """
        self.name = "profile_service"
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._lock = threading.RLock()

        # Cache storage
        self._profiles_cache: Optional[List[str]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._profile_data_cache: Dict[str, Tuple[Any, datetime]] = {}

        logger.info(f"ProfileService initialized with {cache_ttl_seconds}s cache TTL")

    def get_available_profiles(self, force_refresh: bool = False) -> List[str]:
        """
        Get list of available profiles with caching

        Args:
            force_refresh: Force cache refresh if True

        Returns:
            List of profile names
        """
        with self._lock:
            # Check cache validity
            if not force_refresh and self._is_cache_valid():
                logger.debug(f"Returning cached profiles ({len(self._profiles_cache)} profiles)")
                return self._profiles_cache.copy()

            # Refresh cache
            try:
                if PROFILE_SYSTEM_AVAILABLE:
                    profiles = _get_available_profiles()
                    logger.info(f"✅ Loaded {len(profiles)} profiles from file system")
                else:
                    logger.warning("Profile system not available, returning empty list")
                    profiles = []

                # Update cache
                self._profiles_cache = profiles
                self._cache_timestamp = datetime.now()

                return profiles.copy()

            except Exception as e:
                logger.error(f"❌ Error loading profiles: {e}")
                # Return stale cache if available
                if self._profiles_cache is not None:
                    logger.warning("Returning stale cache due to error")
                    return self._profiles_cache.copy()
                return []

    def get_profile_data(self, profile_name: str, force_refresh: bool = False) -> Optional[Any]:
        """
        Get profile data with caching

        Args:
            profile_name: Profile name
            force_refresh: Force cache refresh if True

        Returns:
            ProfileData object or None if not found
        """
        if not PROFILE_SYSTEM_AVAILABLE:
            logger.warning("Profile system not available")
            return None

        with self._lock:
            # Check profile data cache
            if not force_refresh and profile_name in self._profile_data_cache:
                cached_data, cached_time = self._profile_data_cache[profile_name]
                if datetime.now() - cached_time < self.cache_ttl:
                    logger.debug(f"Returning cached data for profile '{profile_name}'")
                    return cached_data

            # Load profile data
            try:
                manager = get_profile_manager()
                profile_data = manager.get_profile(profile_name)

                if profile_data:
                    # Cache the data
                    self._profile_data_cache[profile_name] = (profile_data, datetime.now())
                    logger.info(f"✅ Loaded profile data for '{profile_name}'")
                else:
                    logger.warning(f"⚠️ Profile '{profile_name}' not found")

                return profile_data

            except Exception as e:
                logger.error(f"❌ Error loading profile '{profile_name}': {e}")
                return None

    def validate_profile(self, profile_name: str) -> bool:
        """
        Check if a profile exists

        Args:
            profile_name: Profile name to validate

        Returns:
            True if profile exists, False otherwise
        """
        profiles = self.get_available_profiles()
        return profile_name in profiles

    def invalidate_cache(self, profile_name: Optional[str] = None) -> None:
        """
        Invalidate profile cache

        Args:
            profile_name: Specific profile to invalidate, or None for all profiles
        """
        with self._lock:
            if profile_name is None:
                # Invalidate all caches
                self._profiles_cache = None
                self._cache_timestamp = None
                self._profile_data_cache.clear()
                logger.info("🔄 Invalidated all profile caches")
            else:
                # Invalidate specific profile data
                if profile_name in self._profile_data_cache:
                    del self._profile_data_cache[profile_name]
                    logger.info(f"🔄 Invalidated cache for profile '{profile_name}'")

                # Also invalidate profile list cache to pick up new/deleted profiles
                self._profiles_cache = None
                self._cache_timestamp = None

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                "profiles_cached": len(self._profiles_cache) if self._profiles_cache else 0,
                "profile_data_cached": len(self._profile_data_cache),
                "cache_valid": self._is_cache_valid(),
                "cache_age_seconds": (
                    (datetime.now() - self._cache_timestamp).total_seconds()
                    if self._cache_timestamp
                    else None
                ),
                "ttl_seconds": self.cache_ttl.total_seconds(),
            }

    def _is_cache_valid(self) -> bool:
        """Check if the profiles list cache is still valid"""
        if self._profiles_cache is None or self._cache_timestamp is None:
            return False
        return datetime.now() - self._cache_timestamp < self.cache_ttl


# Global instance
_profile_service_instance: Optional[ProfileService] = None


def get_profile_service() -> ProfileService:
    """
    Get the global profile service instance

    Returns:
        ProfileService singleton instance
    """
    global _profile_service_instance
    if _profile_service_instance is None:
        _profile_service_instance = ProfileService(cache_ttl_seconds=300)  # 5 minute cache
    return _profile_service_instance
