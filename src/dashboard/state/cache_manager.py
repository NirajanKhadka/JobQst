"""
Cache Manager

This module provides Automated caching capabilities for the dashboard.
It handles multi-level caching, cache invalidation, and memory management
with support for different cache strategies.
"""

import asyncio
import hashlib
import json
import pickle
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import logging
import weakref
import gzip
import os

# Set up logging
logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels in order of speed."""
    MEMORY = "memory"       # Fastest, limited capacity
    DISK = "disk"          # Medium speed, larger capacity
    DISTRIBUTED = "distributed"  # Slower, shared across instances


class CacheStrategy(Enum):
    """Cache invalidation strategies."""
    LRU = "lru"            # Least Recently Used
    LFU = "lfu"            # Least Frequently Used
    TTL = "ttl"            # Time To Live
    FIFO = "fifo"          # First In, First Out
    ADAPTIVE = "adaptive"   # Adaptive based on usage patterns


@dataclass
class CacheEntry:
    """Represents a cache entry."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: Optional[timedelta] = None
    size_bytes: int = 0
    tags: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl is None:
            return False
        return datetime.now() > (self.created_at + self.ttl)
    
    def update_access(self):
        """Update access statistics."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def calculate_size(self):
        """Calculate entry size in bytes."""
        try:
            self.size_bytes = len(pickle.dumps(self.value))
        except Exception:
            self.size_bytes = len(str(self.value).encode('utf-8'))


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        pass
    
    @abstractmethod
    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set cache entry."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    def keys(self) -> List[str]:
        """Get all cache keys."""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get total cache size in bytes."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, max_size_mb: int = 100):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        with self._lock:
            entry = self.cache.get(key)
            if entry and not entry.is_expired():
                entry.update_access()
                return entry
            elif entry and entry.is_expired():
                del self.cache[key]
            return None
    
    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set cache entry."""
        with self._lock:
            entry.calculate_size()
            
            # Check if we need to make space
            self._evict_if_needed(entry.size_bytes)
            
            self.cache[key] = entry
            return True
    
    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            return True
    
    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self._lock:
            return list(self.cache.keys())
    
    def size(self) -> int:
        """Get total cache size in bytes."""
        with self._lock:
            return sum(entry.size_bytes for entry in self.cache.values())
    
    def _evict_if_needed(self, new_entry_size: int):
        """Evict entries if needed to make space."""
        current_size = self.size()
        
        while current_size + new_entry_size > self.max_size_bytes and self.cache:
            # Find LRU entry
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].last_accessed
            )
            
            entry_size = self.cache[oldest_key].size_bytes
            del self.cache[oldest_key]
            current_size -= entry_size
            
            logger.debug(f"Evicted cache entry {oldest_key} ({entry_size} bytes)")


class DiskCache(CacheBackend):
    """Disk-based cache backend."""
    
    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 1000, compress: bool = True):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.compress = compress
        self._lock = threading.RLock()
        
        # Index file for metadata
        self.index_file = self.cache_dir / "cache_index.json"
        self.index: Dict[str, Dict[str, Any]] = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load cache index from disk."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading cache index: {e}")
        return {}
    
    def _save_index(self):
        """Save cache index to disk."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache index: {e}")
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Hash key to create valid filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        with self._lock:
            if key not in self.index:
                return None
            
            file_path = self._get_file_path(key)
            if not file_path.exists():
                # Clean up stale index entry
                del self.index[key]
                self._save_index()
                return None
            
            try:
                # Load entry from disk
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                if self.compress:
                    data = gzip.decompress(data)
                
                entry = pickle.loads(data)
                
                # Check expiration
                if entry.is_expired():
                    self.delete(key)
                    return None
                
                entry.update_access()
                
                # Update index
                self.index[key]['last_accessed'] = entry.last_accessed.isoformat()
                self.index[key]['access_count'] = entry.access_count
                self._save_index()
                
                return entry
                
            except Exception as e:
                logger.error(f"Error loading cache entry {key}: {e}")
                # Clean up corrupted entry
                self.delete(key)
                return None
    
    def set(self, key: str, entry: CacheEntry) -> bool:
        """Set cache entry."""
        with self._lock:
            try:
                file_path = self._get_file_path(key)
                
                # Serialize entry
                data = pickle.dumps(entry)
                
                if self.compress:
                    data = gzip.compress(data)
                
                entry.size_bytes = len(data)
                
                # Check space and evict if needed
                self._evict_if_needed(entry.size_bytes)
                
                # Write to disk
                with open(file_path, 'wb') as f:
                    f.write(data)
                
                # Update index
                self.index[key] = {
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed': entry.last_accessed.isoformat(),
                    'access_count': entry.access_count,
                    'size_bytes': entry.size_bytes,
                    'tags': list(entry.tags),
                    'dependencies': list(entry.dependencies)
                }
                
                self._save_index()
                return True
                
            except Exception as e:
                logger.error(f"Error saving cache entry {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        with self._lock:
            try:
                file_path = self._get_file_path(key)
                
                if file_path.exists():
                    file_path.unlink()
                
                if key in self.index:
                    del self.index[key]
                    self._save_index()
                
                return True
                
            except Exception as e:
                logger.error(f"Error deleting cache entry {key}: {e}")
                return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            try:
                # Remove all cache files
                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink()
                
                # Clear index
                self.index.clear()
                self._save_index()
                
                return True
                
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return False
    
    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self._lock:
            return list(self.index.keys())
    
    def size(self) -> int:
        """Get total cache size in bytes."""
        with self._lock:
            return sum(entry['size_bytes'] for entry in self.index.values())
    
    def _evict_if_needed(self, new_entry_size: int):
        """Evict entries if needed to make space."""
        current_size = self.size()
        
        while current_size + new_entry_size > self.max_size_bytes and self.index:
            # Find LRU entry
            oldest_key = min(
                self.index.keys(),
                key=lambda k: datetime.fromisoformat(self.index[k]['last_accessed'])
            )
            
            entry_size = self.index[oldest_key]['size_bytes']
            self.delete(oldest_key)
            current_size -= entry_size
            
            logger.debug(f"Evicted disk cache entry {oldest_key} ({entry_size} bytes)")


class MultiLevelCache:
    """Multi-level cache with automatic promotion/demotion."""
    
    def __init__(self, 
                 memory_cache_mb: int = 100,
                 disk_cache_mb: int = 1000,
                 cache_dir: str = "cache"):
        self.memory_cache = MemoryCache(memory_cache_mb)
        self.disk_cache = DiskCache(cache_dir, disk_cache_mb)
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'memory_hits': 0,
            'disk_hits': 0,
            'misses': 0,
            'promotions': 0,
            'demotions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (checks all levels)."""
        with self._lock:
            # Try memory cache first
            entry = self.memory_cache.get(key)
            if entry:
                self.stats['memory_hits'] += 1
                return entry.value
            
            # Try disk cache
            entry = self.disk_cache.get(key)
            if entry:
                self.stats['disk_hits'] += 1
                
                # Promote to memory if frequently accessed
                if entry.access_count > 5:
                    self.memory_cache.set(key, entry)
                    self.stats['promotions'] += 1
                
                return entry.value
            
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, 
            value: Any, 
            ttl: Optional[timedelta] = None,
            tags: Optional[Set[str]] = None,
            dependencies: Optional[Set[str]] = None,
            level: CacheLevel = CacheLevel.MEMORY) -> bool:
        """Set value in cache."""
        with self._lock:
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                tags=tags or set(),
                dependencies=dependencies or set()
            )
            
            if level == CacheLevel.MEMORY:
                return self.memory_cache.set(key, entry)
            elif level == CacheLevel.DISK:
                return self.disk_cache.set(key, entry)
            else:
                # Auto-select level based on value size
                entry.calculate_size()
                if entry.size_bytes < 1024 * 100:  # < 100KB
                    return self.memory_cache.set(key, entry)
                else:
                    return self.disk_cache.set(key, entry)
    
    def delete(self, key: str) -> bool:
        """Delete from all cache levels."""
        with self._lock:
            memory_deleted = self.memory_cache.delete(key)
            disk_deleted = self.disk_cache.delete(key)
            return memory_deleted or disk_deleted
    
    def invalidate_by_tags(self, tags: Set[str]) -> int:
        """Invalidate all entries with any of the given tags."""
        deleted_count = 0
        
        # Check memory cache
        for key in list(self.memory_cache.keys()):
            entry = self.memory_cache.get(key)
            if entry and tags.intersection(entry.tags):
                self.memory_cache.delete(key)
                deleted_count += 1
        
        # Check disk cache
        for key in list(self.disk_cache.keys()):
            entry = self.disk_cache.get(key)
            if entry and tags.intersection(entry.tags):
                self.disk_cache.delete(key)
                deleted_count += 1
        
        logger.info(f"Invalidated {deleted_count} cache entries with tags: {tags}")
        return deleted_count
    
    def clear(self) -> bool:
        """Clear all cache levels."""
        with self._lock:
            memory_cleared = self.memory_cache.clear()
            disk_cleared = self.disk_cache.clear()
            return memory_cleared and disk_cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = sum(self.stats.values())
            hit_rate = 0
            
            if total_requests > 0:
                hits = self.stats['memory_hits'] + self.stats['disk_hits']
                hit_rate = (hits / total_requests) * 100
            
            return {
                **self.stats,
                'total_requests': total_requests,
                'hit_rate_percent': hit_rate,
                'memory_size_bytes': self.memory_cache.size(),
                'disk_size_bytes': self.disk_cache.size(),
                'memory_entries': len(self.memory_cache.keys()),
                'disk_entries': len(self.disk_cache.keys())
            }


class CacheManager:
    """Main cache management class with invalidation strategies."""
    
    def __init__(self, 
                 memory_cache_mb: int = 100,
                 disk_cache_mb: int = 1000,
                 cache_dir: str = "cache"):
        self.cache = MultiLevelCache(memory_cache_mb, disk_cache_mb, cache_dir)
        self.invalidation_rules: Dict[str, Set[str]] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup_loop():
            while not self._stop_cleanup.wait(300):  # 5 minutes
                try:
                    self._cleanup_expired_entries()
                    self._optimize_cache()
                except Exception as e:
                    logger.error(f"Error in cache cleanup: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_expired_entries(self):
        """Remove expired cache entries."""
        # This is handled automatically by the cache backends
        pass
    
    def _optimize_cache(self):
        """Optimize cache performance by analyzing usage patterns."""
        stats = self.cache.get_stats()
        
        # If hit rate is low, consider adjusting cache sizes
        if stats['hit_rate_percent'] < 50 and stats['total_requests'] > 100:
            logger.info(f"Low cache hit rate: {stats['hit_rate_percent']:.1f}%")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.cache.get(key)
    
    def set(self, key: str, 
            value: Any,
            ttl_seconds: Optional[int] = None,
            tags: Optional[List[str]] = None,
            dependencies: Optional[List[str]] = None,
            level: Optional[CacheLevel] = None) -> bool:
        """Set value in cache with metadata."""
        ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else None
        tag_set = set(tags) if tags else set()
        dep_set = set(dependencies) if dependencies else set()
        
        # Update dependency graph
        if dependencies:
            for dep in dependencies:
                if dep not in self.dependency_graph:
                    self.dependency_graph[dep] = set()
                self.dependency_graph[dep].add(key)
        
        return self.cache.set(
            key=key,
            value=value,
            ttl=ttl,
            tags=tag_set,
            dependencies=dep_set,
            level=level or CacheLevel.MEMORY
        )
    
    def delete(self, key: str) -> bool:
        """Delete key and cascade to dependents."""
        # Delete main key
        deleted = self.cache.delete(key)
        
        # Cascade delete to dependent keys
        dependents = self.dependency_graph.get(key, set())
        for dependent in dependents:
            self.cache.delete(dependent)
            logger.debug(f"Cascade deleted dependent key: {dependent}")
        
        # Clean up dependency graph
        if key in self.dependency_graph:
            del self.dependency_graph[key]
        
        return deleted
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate keys matching a pattern."""
        import re
        
        deleted_count = 0
        pattern_re = re.compile(pattern)
        
        all_keys = set(self.cache.memory_cache.keys()) | set(self.cache.disk_cache.keys())
        
        for key in all_keys:
            if pattern_re.match(key):
                self.delete(key)
                deleted_count += 1
        
        logger.info(f"Invalidated {deleted_count} keys matching pattern: {pattern}")
        return deleted_count
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate all entries with any of the given tags."""
        return self.cache.invalidate_by_tags(set(tags))
    
    def warm_cache(self, warm_func: Callable[[], Dict[str, Any]]):
        """Warm the cache with pre-computed values."""
        try:
            warm_data = warm_func()
            for key, value in warm_data.items():
                self.set(key, value, ttl_seconds=3600)  # 1 hour TTL
            
            logger.info(f"Warmed cache with {len(warm_data)} entries")
            
        except Exception as e:
            logger.error(f"Error warming cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = self.cache.get_stats()
        stats.update({
            'dependency_rules': len(self.dependency_graph),
            'invalidation_rules': len(self.invalidation_rules)
        })
        return stats
    
    def clear_all(self) -> bool:
        """Clear all cache data."""
        self.dependency_graph.clear()
        self.invalidation_rules.clear()
        return self.cache.clear()
    
    def shutdown(self):
        """Shutdown cache manager and cleanup resources."""
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5)


# Global cache manager instance
cache_manager = CacheManager()


# Decorator for caching function results
def cached(ttl_seconds: Optional[int] = None,
           tags: Optional[List[str]] = None,
           key_func: Optional[Callable] = None):
    """Decorator to cache function results."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
                cache_key = hashlib.md5(str(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(
                key=cache_key,
                value=result,
                ttl_seconds=ttl_seconds,
                tags=tags
            )
            
            return result
        
        return wrapper
    return decorator


# Convenience functions
def get_cached(key: str, default: Any = None) -> Any:
    """Get value from cache with default."""
    result = cache_manager.get(key)
    return result if result is not None else default


def set_cached(key: str, value: Any, **kwargs) -> bool:
    """Set value in cache."""
    return cache_manager.set(key, value, **kwargs)


def clear_cache_by_tags(tags: List[str]) -> int:
    """Clear cache entries by tags."""
    return cache_manager.invalidate_by_tags(tags)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return cache_manager.get_stats()
