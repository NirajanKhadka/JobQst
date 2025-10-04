"""
Cache Manager for Dashboard Performance Optimization
Implements caching for analytics data with TTL support
Task 17 from dashboard-enhancements spec
"""

from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Simple in-memory cache with TTL support for dashboard analytics."""
    
    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            default_ttl_seconds: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache = {}
        self._timestamps = {}
        self.default_ttl = default_ttl_seconds
        logger.info(f"CacheManager initialized with {default_ttl_seconds}s TTL")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if expired/not found
        """
        if key not in self._cache:
            return None
        
        # Check if expired
        timestamp = self._timestamps.get(key)
        if timestamp and datetime.now() > timestamp:
            # Expired, remove from cache
            del self._cache[key]
            del self._timestamps[key]
            logger.debug(f"Cache expired for key: {key}")
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return self._cache[key]
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = value
        self._timestamps[key] = expiry
        logger.debug(f"Cached key: {key} (expires in {ttl}s)")
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache entry or entire cache.
        
        Args:
            key: Specific key to clear, or None to clear all
        """
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            logger.debug(f"Cleared cache for key: {key}")
        else:
            self._cache.clear()
            self._timestamps.clear()
            logger.info("Cleared entire cache")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_keys = len(self._cache)
        expired_keys = sum(
            1 for key, timestamp in self._timestamps.items()
            if datetime.now() > timestamp
        )
        
        return {
            "total_keys": total_keys,
            "active_keys": total_keys - expired_keys,
            "expired_keys": expired_keys
        }


# Global cache instance
_global_cache = CacheManager(default_ttl_seconds=3600)  # 1 hour default


def get_cache() -> CacheManager:
    """Get global cache instance."""
    return _global_cache


def cached(ttl_seconds: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Time-to-live in seconds (default: 1 hour)
        key_prefix: Prefix for cache key
        
    Example:
        @cached(ttl_seconds=1800, key_prefix="skill_analysis")
        def analyze_skills(user_id):
            # expensive operation
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"Using cached result for {func.__name__}")
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


# Convenience functions for common cache operations
def cache_skill_analysis(user_id: str, data: Any) -> None:
    """Cache skill analysis results for 1 hour."""
    cache = get_cache()
    cache.set(f"skill_analysis:{user_id}", data, ttl_seconds=3600)


def get_cached_skill_analysis(user_id: str) -> Optional[Any]:
    """Get cached skill analysis results."""
    cache = get_cache()
    return cache.get(f"skill_analysis:{user_id}")


def cache_market_insights(data: Any) -> None:
    """Cache market insights for 1 hour."""
    cache = get_cache()
    cache.set("market_insights", data, ttl_seconds=3600)


def get_cached_market_insights() -> Optional[Any]:
    """Get cached market insights."""
    cache = get_cache()
    return cache.get("market_insights")


def cache_success_prediction(user_id: str, data: Any) -> None:
    """Cache success prediction for 1 hour."""
    cache = get_cache()
    cache.set(f"success_prediction:{user_id}", data, ttl_seconds=3600)


def get_cached_success_prediction(user_id: str) -> Optional[Any]:
    """Get cached success prediction."""
    cache = get_cache()
    return cache.get(f"success_prediction:{user_id}")


def clear_user_cache(user_id: str) -> None:
    """Clear all cached data for a specific user."""
    cache = get_cache()
    cache.clear(f"skill_analysis:{user_id}")
    cache.clear(f"success_prediction:{user_id}")
    logger.info(f"Cleared cache for user: {user_id}")


def clear_all_cache() -> None:
    """Clear entire cache."""
    cache = get_cache()
    cache.clear()
    logger.info("Cleared all cache")
