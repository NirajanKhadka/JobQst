from __future__ import annotations

"""Dashboard cache adapters backed by the shared UnifiedCacheService."""

import hashlib
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

from src.dashboard.analytics import (
    compute_company_stats,
    compute_job_metrics,
    compute_location_stats,
    dataframe_fingerprint,
    ensure_dataframe,
)
from src.core.unified_cache_service import CacheConfig, UnifiedCacheService

logger = logging.getLogger(__name__)


class DashboardCache:
    """Adapter that exposes the legacy dashboard cache API."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        self._config = CacheConfig(
            max_size=max_size,
            default_ttl_seconds=default_ttl,
            enable_statistics=True,
            thread_safe=True,
        )
        self._cache = UnifiedCacheService(self._config)
        logger.info(
            "DashboardCache initialised using UnifiedCacheService: max=%s ttl=%ss",
            max_size,
            default_ttl,
        )

    def get(self, key: str) -> Optional[Any]:
        """Return cached value when present and unexpired."""
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the cache."""
        self._cache.set(key, value, ttl_seconds=ttl)

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """Invalidate entries matching the optional regex pattern."""
        return self._cache.invalidate(pattern)

    def get_stats(self) -> Dict[str, Any]:
        """Expose cache statistics for monitoring widgets."""
        stats = self._cache.get_statistics()
        stats.update(
            {
                "max_size": self._config.max_size,
                "default_ttl": self._config.default_ttl_seconds,
            }
        )
        return stats

    def clear_stats(self) -> None:
        """Reset accumulated cache statistics."""
        self._cache.clear_statistics()


class CachedAggregations:
    """Support cached aggregation helpers for dashboard analytics."""

    def __init__(self, cache: DashboardCache) -> None:
        self.cache = cache

    def _generate_cache_key(
        self,
        profile_name: str,
        operation: str,
        **kwargs: Any,
    ) -> str:
        key_parts = [profile_name, operation]
        if kwargs:
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get_company_stats(
        self,
        df,
        profile_name: str,
        top_n: int = 15,
    ) -> Dict[str, Any]:
        dataframe = ensure_dataframe(df)
        cache_key = self._generate_cache_key(
            profile_name,
            "company_stats",
            top_n=top_n,
            fingerprint=dataframe_fingerprint(dataframe),
        )
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            stats = compute_company_stats(dataframe, top_n=top_n).to_dict()
            self.cache.set(cache_key, stats, ttl=300)
            return stats
        except Exception as error:  # pragma: no cover - defensive logging
            logger.error("Error computing company stats: %s", error)
            return {"companies": [], "counts": [], "total_companies": 0}

    def get_location_stats(
        self,
        df,
        profile_name: str,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        dataframe = ensure_dataframe(df)
        cache_key = self._generate_cache_key(
            profile_name,
            "location_stats",
            top_n=top_n,
            fingerprint=dataframe_fingerprint(dataframe),
        )
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            stats = compute_location_stats(dataframe, top_n=top_n).to_dict()
            self.cache.set(cache_key, stats, ttl=300)
            return stats
        except Exception as error:  # pragma: no cover - defensive logging
            logger.error("Error computing location stats: %s", error)
            return {"locations": [], "counts": [], "total_locations": 0}

    def get_job_metrics(self, df, profile_name: str) -> Dict[str, Any]:
        dataframe = ensure_dataframe(df)
        cache_key = self._generate_cache_key(
            profile_name,
            "job_metrics",
            fingerprint=dataframe_fingerprint(dataframe),
        )
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            metrics = compute_job_metrics(dataframe).to_dict()
            self.cache.set(cache_key, metrics, ttl=180)
            return metrics
        except Exception as error:  # pragma: no cover - defensive logging
            logger.error("Error computing job metrics: %s", error)
            return {
                "total_jobs": 0,
                "avg_match_score": 0.0,
                "status_counts": {},
                "score_distribution": {"ranges": [], "counts": []},
            }


def cached_operation(cache_key_func: Callable = None, ttl: int = 300):
    """Decorator that caches expensive operations via the unified cache."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_dashboard_cache()
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                func_name = func.__name__
                key_parts = [func_name, *map(str, args)]
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result

        return wrapper

    return decorator


_dashboard_cache: Optional[DashboardCache] = None


def get_dashboard_cache() -> DashboardCache:
    """Return the global dashboard cache adapter instance."""
    global _dashboard_cache
    if _dashboard_cache is None:
        _dashboard_cache = DashboardCache(max_size=1000, default_ttl=300)
    return _dashboard_cache


def get_cached_aggregations() -> CachedAggregations:
    """Return aggregation helpers wired to the shared cache."""
    return CachedAggregations(get_dashboard_cache())


def invalidate_profile_cache(profile_name: str) -> int:
    """Invalidate cache entries related to a specific profile."""
    cache = get_dashboard_cache()
    return cache.invalidate(pattern=profile_name)


def get_cache_performance_stats() -> Dict[str, Any]:
    """Expose cache performance metrics for monitoring panels."""
    cache = get_dashboard_cache()
    return cache.get_stats()
