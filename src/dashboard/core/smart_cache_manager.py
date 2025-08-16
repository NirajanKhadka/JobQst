#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Cache Manager
Automated caching system without AI - pattern-based caching.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, OrderedDict
import threading

logger = logging.getLogger(__name__)


class AccessPatternTracker:
    """Track access patterns for Automated caching decisions."""
    
    def __init__(self):
        self.access_counts = defaultdict(int)
        self.access_times = defaultdict(list)
        self.last_access = {}
        self.lock = threading.Lock()
    
    def track_access(self, key: str) -> None:
        """Track when a key is accessed."""
        with self.lock:
            now = datetime.now()
            self.access_counts[key] += 1
            self.access_times[key].append(now)
            self.last_access[key] = now
            
            # Keep only recent access times (last hour)
            cutoff = now - timedelta(hours=1)
            self.access_times[key] = [
                t for t in self.access_times[key] if t > cutoff
            ]
    
    def get_access_frequency(self, key: str) -> float:
        """Get access frequency per minute for a key."""
        with self.lock:
            if key not in self.access_times:
                return 0.0
            
            recent_accesses = len(self.access_times[key])
            return recent_accesses / 60.0  # per minute
    
    def get_frequent_keys(self, min_frequency: float = 0.1) -> List[str]:
        """Get keys accessed frequently."""
        return [key for key in self.access_counts.keys()
                if self.get_access_frequency(key) >= min_frequency]
    
    def should_preload(self, key: str) -> bool:
        """Determine if key should be preloaded."""
        frequency = self.get_access_frequency(key)
        return frequency > 0.5  # More than once every 2 minutes


class CacheInvalidationEngine:
    """Automated cache invalidation based on data change patterns."""
    
    def __init__(self):
        self.invalidation_rules = {}
        self.dependency_map = defaultdict(set)
        self.lock = threading.Lock()
    
    def add_invalidation_rule(self, trigger_pattern: str,
                              affected_keys: List[str]) -> None:
        """Add rule for cache invalidation."""
        with self.lock:
            self.invalidation_rules[trigger_pattern] = affected_keys
            for key in affected_keys:
                self.dependency_map[trigger_pattern].add(key)
    
    def get_keys_to_invalidate(self, trigger: str) -> List[str]:
        """Get keys that should be invalidated for a trigger."""
        with self.lock:
            keys_to_invalidate = set()
            
            # Direct pattern matches
            if trigger in self.invalidation_rules:
                keys_to_invalidate.update(self.invalidation_rules[trigger])
            
            # Pattern-based matches
            for pattern, keys in self.invalidation_rules.items():
                if pattern in trigger or trigger in pattern:
                    keys_to_invalidate.update(keys)
            
            return list(keys_to_invalidate)


class ConfigurableCacheManager:
    """
    Automated caching manager with pattern-based optimization.
    
    Features:
    - LRU cache with Automated sizing
    - Pattern-based preloading
    - Configurable invalidation rules
    - Access pattern tracking
    - Memory-efficient storage
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.cache_metadata = {}
        self.pattern_tracker = AccessPatternTracker()
        self.invalidation_engine = CacheInvalidationEngine()
        self.lock = threading.Lock()
        
        # Set up common invalidation rules
        self._setup_default_invalidation_rules()
        
        logger.info(
            f"ConfigurableCacheManager initialized: "
            f"max_size={max_size}, ttl={default_ttl}s"
        )
    
    def _setup_default_invalidation_rules(self) -> None:
        """Set up common cache invalidation rules."""
        # Job data changes
        self.invalidation_engine.add_invalidation_rule(
            "job_data_update", 
            ["job_metrics", "job_table", "job_analytics", "dashboard_overview"]
        )
        
        # System status changes
        self.invalidation_engine.add_invalidation_rule(
            "service_status_change",
            ["system_metrics", "health_status", "orchestration_status"]
        )
        
        # Profile changes
        self.invalidation_engine.add_invalidation_rule(
            "profile_change",
            ["job_table", "profile_settings", "dashboard_overview"]
        )
    
    def Configurable_get(self, key: str, loader_func: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """
        Get data with Automated caching strategy.
        
        Args:
            key: Cache key
            loader_func: Function to load data if not cached
            ttl: Time to live in seconds (optional)
        
        Returns:
            Cached or freshly loaded data
        """
        # Track access pattern
        self.pattern_tracker.track_access(key)
        
        with self.lock:
            # Check if key exists and is valid
            if key in self.cache:
                metadata = self.cache_metadata[key]
                
                # Check TTL
                if metadata['expires_at'] > time.time():
                    # Move to end (LRU)
                    self.cache.move_to_end(key)
                    logger.debug(f"Cache hit for key: {key}")
                    return self.cache[key]
                else:
                    # Expired
                    self._remove_key(key)
                    logger.debug(f"Cache expired for key: {key}")
            
            # Cache miss - load data
            logger.debug(f"Cache miss for key: {key}")
            
        # Load data outside of lock
        try:
            data = loader_func()
        except Exception as e:
            logger.error(f"Failed to load data for key {key}: {e}")
            raise
        
        # Store in cache
        self._store(key, data, ttl or self.default_ttl)
        return data
    
    def _store(self, key: str, data: Any, ttl: int) -> None:
        """Store data in cache with metadata."""
        with self.lock:
            # Remove oldest items if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                self._remove_key(oldest_key)
            
            # Store data and metadata
            self.cache[key] = data
            self.cache_metadata[key] = {
                'created_at': time.time(),
                'expires_at': time.time() + ttl,
                'access_count': 1,
                'size_estimate': self._estimate_size(data)
            }
            
            logger.debug(f"Stored in cache: {key} (TTL: {ttl}s)")
    
    def _remove_key(self, key: str) -> None:
        """Remove key from cache and metadata."""
        if key in self.cache:
            del self.cache[key]
        if key in self.cache_metadata:
            del self.cache_metadata[key]
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate memory size of data."""
        try:
            if hasattr(data, '__len__'):
                return len(str(data))
            return 100  # Default estimate
        except:
            return 100
    
    def invalidate_Configurable(self, trigger: str) -> None:
        """Invalidate cache based on trigger pattern."""
        keys_to_invalidate = self.invalidation_engine.get_keys_to_invalidate(trigger)
        
        with self.lock:
            for key in keys_to_invalidate:
                if key in self.cache:
                    self._remove_key(key)
                    logger.debug(f"Invalidated cache key: {key} (trigger: {trigger})")
        
        if keys_to_invalidate:
            logger.info(f"Invalidated {len(keys_to_invalidate)} cache keys for trigger: {trigger}")
    
    def preload_frequent_data(self, loaders: Dict[str, Callable[[], Any]]) -> None:
        """Preload frequently accessed data."""
        frequent_keys = self.pattern_tracker.get_frequent_keys()
        
        for key in frequent_keys:
            if key in loaders and key not in self.cache:
                try:
                    logger.debug(f"Preloading frequent key: {key}")
                    data = loaders[key]()
                    self._store(key, data, self.default_ttl)
                except Exception as e:
                    logger.warning(f"Failed to preload key {key}: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_size = sum(meta['size_estimate'] for meta in self.cache_metadata.values())
            
            return {
                'cache_size': len(self.cache),
                'max_size': self.max_size,
                'total_estimated_size': total_size,
                'hit_rate': self._calculate_hit_rate(),
                'frequent_keys': self.pattern_tracker.get_frequent_keys(),
                'cache_keys': list(self.cache.keys())
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        # Simple implementation - could be Improved
        total_accesses = sum(self.pattern_tracker.access_counts.values())
        if total_accesses == 0:
            return 0.0
        
        cache_hits = sum(meta['access_count'] for meta in self.cache_metadata.values())
        return min(cache_hits / total_accesses, 1.0)
    
    def clear_cache(self) -> None:
        """Clear all cache data."""
        with self.lock:
            self.cache.clear()
            self.cache_metadata.clear()
        logger.info("Cache cleared")
    
    def add_invalidation_rule(self, trigger_pattern: str, affected_keys: List[str]) -> None:
        """Add custom invalidation rule."""
        self.invalidation_engine.add_invalidation_rule(trigger_pattern, affected_keys)
        logger.info(f"Added invalidation rule: {trigger_pattern} -> {affected_keys}")


# Global cache instance
_global_cache = None


def get_Configurable_cache() -> ConfigurableCacheManager:
    """Get global smart cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ConfigurableCacheManager()
    return _global_cache
