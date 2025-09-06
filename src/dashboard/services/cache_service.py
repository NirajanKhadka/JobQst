"""
Dashboard Query Caching System for JobQst
Implements intelligent caching for expensive aggregations to improve
dashboard performance. Follows JobQst development standards for
maintainability and performance
"""
import time
import hashlib
import logging
import threading
from typing import Dict, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class DashboardCache:
    """
    High-performance caching system for dashboard queries
    
    Features:
    - TTL-based expiration
    - LRU eviction policy
    - Thread-safe operations
    - Intelligent cache invalidation
    - Memory-efficient storage
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache with configurable parameters
        
        Args:
            max_size: Maximum number of cached items (LRU eviction)
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # Cache hit/miss statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'invalidations': 0
        }
        
        logger.info(
            f"Dashboard cache initialized: max_size={max_size}, "
            f"ttl={default_ttl}s"
        )
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if exists and not expired"""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            now = time.time()
            
            # Check if expired
            if now > entry['expires_at']:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                self._stats['misses'] += 1
                return None
            
            # Update access time for LRU
            self._access_times[key] = now
            self._stats['hits'] += 1
            return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional custom TTL"""
        with self._lock:
            ttl = ttl or self.default_ttl
            now = time.time()
            
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = {
                'value': value,
                'created_at': now,
                'expires_at': now + ttl
            }
            self._access_times[key] = now
    
    def invalidate(self, pattern: str = None) -> int:
        """
        Invalidate cache entries
        
        Args:
            pattern: If provided, invalidate keys containing this pattern
                    If None, clear entire cache
        
        Returns:
            Number of entries invalidated
        """
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                self._access_times.clear()
                self._stats['invalidations'] += count
                return count
            
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
            
            self._stats['invalidations'] += len(keys_to_remove)
            return len(keys_to_remove)
    
    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=self._access_times.get)
        del self._cache[lru_key]
        del self._access_times[lru_key]
        self._stats['evictions'] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (
                self._stats['hits'] / total_requests * 100
                if total_requests > 0 else 0
            )
            
            return {
                **self._stats,
                'total_requests': total_requests,
                'hit_rate_percent': round(hit_rate, 2),
                'cache_size': len(self._cache),
                'max_size': self.max_size
            }
    
    def clear_stats(self) -> None:
        """Reset cache statistics"""
        with self._lock:
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'invalidations': 0
            }


class CachedAggregations:
    """
    Cached aggregation functions for expensive dashboard operations
    Implements caching for company stats, location analytics, and job metrics
    """
    
    def __init__(self, cache: DashboardCache):
        self.cache = cache
        
    def _generate_cache_key(
        self, profile_name: str, operation: str, **kwargs
    ) -> str:
        """Generate deterministic cache key"""
        # Include profile, operation, and sorted kwargs
        key_parts = [profile_name, operation]
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}={v}" for k, v in sorted_kwargs])
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_company_stats(
        self, df, profile_name: str, top_n: int = 15
    ) -> Dict[str, Any]:
        """Get cached company statistics"""
        cache_key = self._generate_cache_key(
            profile_name, "company_stats",
            top_n=top_n, row_count=len(df)
        )
        
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute expensive aggregation
        try:
            if 'company' not in df.columns or df.empty:
                result = {'companies': [], 'counts': [], 'total_companies': 0}
            else:
                company_counts = df['company'].value_counts().head(top_n)
                result = {
                    'companies': company_counts.index.tolist(),
                    'counts': company_counts.values.tolist(),
                    'total_companies': df['company'].nunique()
                }
            
            # Cache for 5 minutes
            self.cache.set(cache_key, result, ttl=300)
            return result
            
        except Exception as e:
            logger.error(f"Error computing company stats: {e}")
            return {'companies': [], 'counts': [], 'total_companies': 0}
    
    def get_location_stats(
        self, df, profile_name: str, top_n: int = 10
    ) -> Dict[str, Any]:
        """Get cached location statistics"""
        cache_key = self._generate_cache_key(
            profile_name, "location_stats",
            top_n=top_n, row_count=len(df)
        )
        
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute expensive aggregation
        try:
            if 'location' not in df.columns or df.empty:
                result = {'locations': [], 'counts': [], 'total_locations': 0}
            else:
                # Clean location data
                df_clean = df.copy()
                df_clean['location_clean'] = df_clean['location'].str.strip()
                location_counts = (
                    df_clean['location_clean'].value_counts().head(top_n)
                )
                
                result = {
                    'locations': location_counts.index.tolist(),
                    'counts': location_counts.values.tolist(),
                    'total_locations': df_clean['location_clean'].nunique()
                }
            
            # Cache for 5 minutes
            self.cache.set(cache_key, result, ttl=300)
            return result
            
        except Exception as e:
            logger.error(f"Error computing location stats: {e}")
            return {'locations': [], 'counts': [], 'total_locations': 0}
    
    def get_job_metrics(self, df, profile_name: str) -> Dict[str, Any]:
        """Get cached job metrics and statistics"""
        cache_key = self._generate_cache_key(
            profile_name, "job_metrics",
            row_count=len(df)
        )
        
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Compute expensive aggregations
        try:
            if df.empty:
                result = {
                    'total_jobs': 0,
                    'avg_match_score': 0.0,
                    'status_counts': {},
                    'score_distribution': {'ranges': [], 'counts': []}
                }
            else:
                # Status counts
                status_counts = {}
                if 'status' in df.columns:
                    status_counts = df['status'].value_counts().to_dict()
                
                # Match score statistics
                avg_score = 0.0
                score_distribution = {'ranges': [], 'counts': []}
                if 'match_score' in df.columns:
                    avg_score = df['match_score'].mean()
                    
                    # Score distribution bins
                    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
                    labels = ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%']
                    
                    # Create score ranges without pandas
                    score_ranges = []
                    for score in df['match_score']:
                        for i, threshold in enumerate(bins[1:]):
                            if score <= threshold:
                                score_ranges.append(labels[i])
                                break
                    
                    # Count occurrences
                    from collections import Counter
                    score_counts = Counter(score_ranges)
                    
                    score_distribution = {
                        'ranges': list(score_counts.keys()),
                        'counts': list(score_counts.values())
                    }
                
                result = {
                    'total_jobs': len(df),
                    'avg_match_score': float(avg_score),
                    'status_counts': status_counts,
                    'score_distribution': score_distribution
                }
            
            # Cache for 3 minutes (job metrics change more frequently)
            self.cache.set(cache_key, result, ttl=180)
            return result
            
        except Exception as e:
            logger.error(f"Error computing job metrics: {e}")
            return {
                'total_jobs': 0,
                'avg_match_score': 0.0,
                'status_counts': {},
                'score_distribution': {'ranges': [], 'counts': []}
            }


def cached_operation(cache_key_func: Callable = None, ttl: int = 300):
    """
    Decorator for caching expensive operations
    
    Args:
        cache_key_func: Function to generate cache key from args/kwargs
        ttl: Time to live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance (assumed to be available globally)
            cache = get_dashboard_cache()
            
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                # Default key generation
                func_name = func.__name__
                key_parts = (
                    [func_name] + [str(arg) for arg in args] +
                    [f"{k}={v}" for k, v in sorted(kwargs.items())]
                )
                cache_key = hashlib.md5(
                    "|".join(key_parts).encode()
                ).hexdigest()
            
            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator


# Global cache instance
_dashboard_cache = None


def get_dashboard_cache() -> DashboardCache:
    """Get global dashboard cache instance"""
    global _dashboard_cache
    if _dashboard_cache is None:
        _dashboard_cache = DashboardCache(max_size=1000, default_ttl=300)
    return _dashboard_cache


def get_cached_aggregations() -> CachedAggregations:
    """Get cached aggregations helper"""
    return CachedAggregations(get_dashboard_cache())


def invalidate_profile_cache(profile_name: str) -> int:
    """Invalidate all cache entries for a specific profile"""
    cache = get_dashboard_cache()
    return cache.invalidate(pattern=profile_name)


def get_cache_performance_stats() -> Dict[str, Any]:
    """Get cache performance statistics for monitoring"""
    cache = get_dashboard_cache()
    return cache.get_stats()
