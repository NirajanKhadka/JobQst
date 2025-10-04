#!/usr/bin/env python3
"""
Unified Cache Service for JobQst
Replaces the three separate caching implementations with a single,
clean, and maintainable caching system that follows DEVELOPMENT_STANDARDS.md
"""

import hashlib
import logging
import threading
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration following clean code principles"""

    max_size: int = 1000
    default_ttl_seconds: int = 300  # 5 minutes
    enable_statistics: bool = True
    thread_safe: bool = True


class CacheEntry:
    """Individual cache entry with TTL support"""

    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
        self.last_accessed = self.created_at
        self.access_count = 1

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() > self.expires_at

    def access(self) -> Any:
        """Update access statistics and return value"""
        self.last_accessed = time.time()
        self.access_count += 1
        return self.value


class CacheStatistics:
    """Cache performance statistics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.invalidations = 0
        self.total_sets = 0

    def hit_rate_percent(self) -> float:
        """Calculate cache hit rate as percentage"""
        total_requests = self.hits + self.misses
        if total_requests == 0:
            return 0.0
        return (self.hits / total_requests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary for API responses"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "invalidations": self.invalidations,
            "total_sets": self.total_sets,
            "hit_rate_percent": round(self.hit_rate_percent(), 2),
            "total_requests": self.hits + self.misses,
        }


class UnifiedCacheService:
    """
    Single cache service replacing all previous caching implementations

    Features:
    - TTL-based expiration
    - LRU eviction policy
    - Thread-safe operations (optional)
    - Pattern-based invalidation
    - Comprehensive statistics
    - Memory-efficient storage

    Follows DEVELOPMENT_STANDARDS.md:
    - Clean, descriptive naming
    - Type annotations
    - Comprehensive error handling
    - No global state
    """

    def __init__(self, config: CacheConfig = None):
        """Initialize unified cache service"""
        self.config = config or CacheConfig()
        self.cache_entries: Dict[str, CacheEntry] = {}
        self.statistics = CacheStatistics()

        # Thread safety (only if needed)
        if self.config.thread_safe:
            self.lock = threading.RLock()
        else:
            self.lock = None

        logger.info(
            f"Unified cache service initialized: "
            f"max_size={self.config.max_size}, "
            f"ttl={self.config.default_ttl_seconds}s"
        )

    def _with_lock(self, operation: Callable):
        """Execute operation with optional thread safety"""
        if self.lock:
            with self.lock:
                return operation()
        else:
            return operation()

    def get(self, cache_key: str) -> Optional[Any]:
        """
        Get cached value if exists and not expired

        Args:
            cache_key: Unique cache key

        Returns:
            Cached value or None if not found/expired
        """

        def _get_operation():
            if cache_key not in self.cache_entries:
                self.statistics.misses += 1
                return None

            entry = self.cache_entries[cache_key]

            # Check expiration
            if entry.is_expired():
                del self.cache_entries[cache_key]
                self.statistics.misses += 1
                return None

            # Update statistics and return value
            self.statistics.hits += 1
            return entry.access()

        return self._with_lock(_get_operation)

    def set(self, cache_key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set cached value with optional custom TTL

        Args:
            cache_key: Unique cache key
            value: Value to cache
            ttl_seconds: Time to live (uses default if None)
        """

        def _set_operation():
            ttl = ttl_seconds or self.config.default_ttl_seconds

            # Evict if at capacity and adding new key
            if (
                len(self.cache_entries) >= self.config.max_size
                and cache_key not in self.cache_entries
            ):
                self._evict_lru()

            self.cache_entries[cache_key] = CacheEntry(value, ttl)
            self.statistics.total_sets += 1

        return self._with_lock(_set_operation)

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries by pattern or clear all

        Args:
            pattern: Regex pattern to match keys (None = clear all)

        Returns:
            Number of entries invalidated
        """

        def _invalidate_operation():
            if pattern is None:
                # Clear entire cache
                invalidated_count = len(self.cache_entries)
                self.cache_entries.clear()
                self.statistics.invalidations += invalidated_count
                return invalidated_count

            # Pattern-based invalidation
            compiled_pattern = re.compile(pattern)
            keys_to_remove = [
                key for key in self.cache_entries.keys() if compiled_pattern.search(key)
            ]

            for key in keys_to_remove:
                del self.cache_entries[key]

            invalidated_count = len(keys_to_remove)
            self.statistics.invalidations += invalidated_count
            return invalidated_count

        return self._with_lock(_invalidate_operation)

    def _evict_lru(self) -> None:
        """Evict least recently used item (internal method)"""
        if not self.cache_entries:
            return

        # Find entry with oldest last_accessed time
        lru_key = min(self.cache_entries.keys(), key=lambda k: self.cache_entries[k].last_accessed)

        del self.cache_entries[lru_key]
        self.statistics.evictions += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""

        def _stats_operation():
            stats = self.statistics.to_dict()
            stats.update(
                {
                    "current_size": len(self.cache_entries),
                    "max_size": self.config.max_size,
                    "memory_usage_percent": round(
                        (len(self.cache_entries) / self.config.max_size) * 100, 2
                    ),
                    "default_ttl_seconds": self.config.default_ttl_seconds,
                }
            )
            return stats

        return self._with_lock(_stats_operation)

    def clear_statistics(self) -> None:
        """Reset all cache statistics"""

        def _clear_stats_operation():
            self.statistics = CacheStatistics()

        return self._with_lock(_clear_stats_operation)

    @staticmethod
    def generate_cache_key(*key_parts: Any) -> str:
        """
        Generate consistent cache key from components

        Args:
            key_parts: Components to include in cache key

        Returns:
            MD5 hash of serialized key components
        """
        # Convert all parts to strings and join
        key_string = "|".join(str(part) for part in key_parts)

        # Generate consistent hash
        return hashlib.md5(key_string.encode("utf-8")).hexdigest()


# Decorator for easy caching of function results
def cached_function(
    cache_service: UnifiedCacheService,
    ttl_seconds: int = 300,
    key_generator: Optional[Callable] = None,
):
    """
    Decorator for caching function results

    Args:
        cache_service: Cache service instance to use
        ttl_seconds: Time to live for cached results
        key_generator: Custom key generation function
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = UnifiedCacheService.generate_cache_key(
                    func.__name__, args, sorted(kwargs.items())
                )

            # Try cache first
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Compute and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl_seconds)
            return result

        return wrapper

    return decorator


# Decorator for caching method results
def cached_method(ttl_seconds: int = 300, key_generator: Optional[Callable] = None):
    """
    Decorator for caching method results on service classes

    Args:
        ttl_seconds: Time to live for cached results
        key_generator: Custom key generation function
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Ensure service has cache attribute
            if not hasattr(self, "_unified_cache"):
                self._unified_cache = UnifiedCacheService()

            # Generate cache key
            if key_generator:
                cache_key = key_generator(self, *args, **kwargs)
            else:
                cache_key = UnifiedCacheService.generate_cache_key(
                    self.__class__.__name__, func.__name__, args, sorted(kwargs.items())
                )

            # Try cache first
            cached_result = self._unified_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Compute and cache result
            result = func(self, *args, **kwargs)
            self._unified_cache.set(cache_key, result, ttl_seconds)
            return result

        return wrapper

    return decorator


# Global cache service instance (singleton pattern)
_global_cache_service: Optional[UnifiedCacheService] = None


def get_global_cache_service() -> UnifiedCacheService:
    """Get or create global cache service instance"""
    global _global_cache_service
    if _global_cache_service is None:
        _global_cache_service = UnifiedCacheService()
    return _global_cache_service


def configure_global_cache(config: CacheConfig) -> None:
    """Configure global cache service with custom settings"""
    global _global_cache_service
    _global_cache_service = UnifiedCacheService(config)
