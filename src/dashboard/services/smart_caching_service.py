#!/usr/bin/env python3
"""
Configurable Caching Service - Automated caching service (pattern-based, no AI)
Part of Phase 4: Configurable Services implementation

This service provides Automated caching capabilities without AI complexity.
Uses pattern-based optimization with Configurable invalidation strategies.
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AccessPattern:
    """Track access patterns for Configurable caching"""
    key: str
    access_count: int = 0
    last_access: Optional[datetime] = None
    first_access: Optional[datetime] = None
    access_frequency: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl: Optional[int] = None
    tags: Set[str] = None
    size_bytes: int = 0

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()


class AccessPatternTracker:
    """Track access patterns for Configurable caching decisions"""
    
    def __init__(self, max_patterns: int = 1000):
        self.patterns: Dict[str, AccessPattern] = {}
        self.max_patterns = max_patterns
        self.access_history = deque(maxlen=10000)
        self._lock = threading.RLock()
    
    def track_access(self, key: str, is_hit: bool = True) -> None:
        """Track data access patterns"""
        with self._lock:
            now = datetime.now()
            
            if key not in self.patterns:
                if len(self.patterns) >= self.max_patterns:
                    # Remove least frequently accessed pattern
                    min_key = min(self.patterns.keys(), 
                                key=lambda k: self.patterns[k].access_count)
                    del self.patterns[min_key]
                
                self.patterns[key] = AccessPattern(
                    key=key,
                    first_access=now
                )
            
            pattern = self.patterns[key]
            pattern.access_count += 1
            pattern.last_access = now
            
            if is_hit:
                pattern.cache_hits += 1
            else:
                pattern.cache_misses += 1
            
            # Calculate frequency (accesses per hour)
            if pattern.first_access:
                duration = (now - pattern.first_access).total_seconds() / 3600
                pattern.access_frequency = pattern.access_count / max(duration, 0.1)
            
            # Track in history for pattern analysis
            self.access_history.append((key, now, is_hit))
    
    def get_frequent_patterns(self, threshold: float = 1.0) -> Dict[str, AccessPattern]:
        """Get frequently accessed data patterns"""
        with self._lock:
            return {
                key: pattern for key, pattern in self.patterns.items()
                if pattern.access_frequency >= threshold
            }
    
    def predict_next_access(self, current_key: str, limit: int = 5) -> List[str]:
        """Predict next likely data access based on patterns"""
        with self._lock:
            # Find sequences in access history
            sequences = defaultdict(list)
            history_list = list(self.access_history)
            
            for i in range(len(history_list) - 1):
                current = history_list[i][0]
                next_item = history_list[i + 1][0]
                sequences[current].append(next_item)
            
            if current_key in sequences:
                # Count frequency of next items
                next_counts = defaultdict(int)
                for next_item in sequences[current_key]:
                    next_counts[next_item] += 1
                
                # Return most frequent next items
                sorted_next = sorted(next_counts.items(), 
                                   key=lambda x: x[1], reverse=True)
                return [item[0] for item in sorted_next[:limit]]
            
            return []

class CacheInvalidationEngine:
    """Engine for smart cache invalidation"""
    
    def __init__(self):
        self.invalidation_rules: Dict[str, List[str]] = {}
        self.tag_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def add_invalidation_rule(self, trigger_pattern: str, affected_patterns: List[str]) -> None:
        """Add invalidation rule for pattern-based invalidation"""
        with self._lock:
            self.invalidation_rules[trigger_pattern] = affected_patterns
    
    def add_tag_dependency(self, tag: str, dependent_keys: List[str]) -> None:
        """Add tag-based dependency for invalidation"""
        with self._lock:
            for key in dependent_keys:
                self.tag_dependencies[tag].add(key)
    
    def get_keys_to_invalidate(self, trigger: str) -> Set[str]:
        """Get keys that should be invalidated based on trigger"""
        with self._lock:
            keys_to_invalidate = set()
            
            # Check pattern-based rules
            for pattern, affected in self.invalidation_rules.items():
                if pattern in trigger or trigger in pattern:
                    keys_to_invalidate.update(affected)
            
            # Check tag-based dependencies
            if trigger in self.tag_dependencies:
                keys_to_invalidate.update(self.tag_dependencies[trigger])
            
            return keys_to_invalidate

class ConfigurableCachingService:
    """Automated caching service (pattern-based, no AI)"""
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: int = 300,
                 enable_persistence: bool = False,
                 cache_dir: Optional[str] = None):
        """
        Initialize Configurable caching service
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
            enable_persistence: Enable disk persistence
            cache_dir: Directory for persistent cache
        """
        self.cache_store: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_persistence = enable_persistence
        self.cache_dir = Path(cache_dir) if cache_dir else Path("cache")
        
        # Configurable components
        self.access_tracker = AccessPatternTracker()
        self.invalidation_engine = CacheInvalidationEngine()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'invalidations': 0,
            'preloads': 0
        }
        
        self._lock = threading.RLock()
        
        # Setup persistence
        if self.enable_persistence:
            self.cache_dir.mkdir(exist_ok=True)
            self._load_persistent_cache()
    
    def get_with_Configurable_cache(self, key: str, loader: Callable[[], Any], 
                           ttl: Optional[int] = None, tags: Optional[Set[str]] = None) -> Any:
        """Get data with Automated caching strategy"""
        with self._lock:
            # Check if key exists and is valid
            if key in self.cache_store:
                entry = self.cache_store[key]
                
                # Check TTL
                if entry.ttl:
                    age = (datetime.now() - entry.created_at).total_seconds()
                    if age > entry.ttl:
                        # Expired, remove entry
                        del self.cache_store[key]
                        self.access_tracker.track_access(key, is_hit=False)
                        self.stats['misses'] += 1
                    else:
                        # Valid cache hit
                        entry.last_accessed = datetime.now()
                        entry.access_count += 1
                        self.access_tracker.track_access(key, is_hit=True)
                        self.stats['hits'] += 1
                        return entry.value
                else:
                    # No TTL, always valid
                    entry.last_accessed = datetime.now()
                    entry.access_count += 1
                    self.access_tracker.track_access(key, is_hit=True)
                    self.stats['hits'] += 1
                    return entry.value
            
            # Cache miss - load data
            try:
                value = loader()
                
                # Store in cache
                self._store_with_eviction(key, value, ttl or self.default_ttl, tags)
                self.access_tracker.track_access(key, is_hit=False)
                self.stats['misses'] += 1
                
                # Trigger Configurable preloading
                self._trigger_Configurable_preload(key)
                
                return value
            
            except Exception as e:
                logger.error(f"Error loading data for key {key}: {e}")
                raise
    
    def _store_with_eviction(self, key: str, value: Any, ttl: int, tags: Optional[Set[str]]) -> None:
        """Store value with Configurable eviction if needed"""
        # Calculate approximate size
        try:
            size_bytes = len(str(value).encode('utf-8'))
        except:
            size_bytes = 1024  # Default estimate
        
        # Check if we need to evict
        if len(self.cache_store) >= self.max_size:
            self._Configurable_evict()
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl=ttl,
            tags=tags or set(),
            size_bytes=size_bytes
        )
        
        self.cache_store[key] = entry
        
        # Persist if enabled
        if self.enable_persistence:
            self._persist_entry(entry)
    
    def _Configurable_evict(self) -> None:
        """Automatedly evict cache entries"""
        if not self.cache_store:
            return
        
        # Get access patterns
        patterns = self.access_tracker.patterns
        
        # Score entries for eviction (lower score = more likely to evict)
        scores = {}
        for key, entry in self.cache_store.items():
            pattern = patterns.get(key)
            
            # Base score on access frequency and recency
            frequency_score = pattern.access_frequency if pattern else 0
            recency_score = (datetime.now() - entry.last_accessed).total_seconds()
            
            # Lower score = more likely to evict
            scores[key] = frequency_score - (recency_score / 3600)
        
        # Evict lowest scored entry
        key_to_evict = min(scores.keys(), key=lambda k: scores[k])
        del self.cache_store[key_to_evict]
        self.stats['evictions'] += 1
        
        logger.debug(f"Evicted cache key: {key_to_evict}")
    
    def _trigger_Configurable_preload(self, accessed_key: str) -> None:
        """Trigger Configurable preloading based on access patterns"""
        try:
            predicted_keys = self.access_tracker.predict_next_access(accessed_key)
            
            for pred_key in predicted_keys[:3]:  # Limit preloading
                if pred_key not in self.cache_store:
                    # This is where you'd trigger background preloading
                    # For now, just log the prediction
                    logger.debug(f"Predicted next access: {pred_key}")
                    self.stats['preloads'] += 1
        
        except Exception as e:
            logger.error(f"Error in Configurable preloading: {e}")
    
    def invalidate_Configurable(self, pattern: str) -> int:
        """Invalidate cache entries based on data change patterns"""
        with self._lock:
            keys_to_invalidate = self.invalidation_engine.get_keys_to_invalidate(pattern)
            
            # Add pattern-based invalidation
            keys_to_remove = set()
            for key in self.cache_store.keys():
                if pattern in key or any(tag in pattern for tag in self.cache_store[key].tags):
                    keys_to_remove.add(key)
            
            keys_to_invalidate.update(keys_to_remove)
            
            # Remove entries
            for key in keys_to_invalidate:
                if key in self.cache_store:
                    del self.cache_store[key]
                    self.stats['invalidations'] += 1
            
            logger.info(f"Invalidated {len(keys_to_invalidate)} cache entries for pattern: {pattern}")
            return len(keys_to_invalidate)
    
    def preload_based_on_patterns(self, preload_functions: Dict[str, Callable]) -> None:
        """Preload data based on access patterns"""
        frequent_patterns = self.access_tracker.get_frequent_patterns(threshold=2.0)
        
        for key, pattern in frequent_patterns.items():
            if key not in self.cache_store and key in preload_functions:
                try:
                    # Preload frequently accessed data
                    value = preload_functions[key]()
                    self._store_with_eviction(key, value, self.default_ttl, None)
                    logger.debug(f"Preloaded cache key: {key}")
                    self.stats['preloads'] += 1
                
                except Exception as e:
                    logger.error(f"Error preloading key {key}: {e}")
    
    def _persist_entry(self, entry: CacheEntry) -> None:
        """Persist cache entry to disk"""
        try:
            cache_file = self.cache_dir / f"{hashlib.md5(entry.key.encode()).hexdigest()}.json"
            
            # Prepare serializable data
            data = {
                'key': entry.key,
                'value': entry.value,
                'created_at': entry.created_at.isoformat(),
                'last_accessed': entry.last_accessed.isoformat(),
                'access_count': entry.access_count,
                'ttl': entry.ttl,
                'tags': list(entry.tags),
                'size_bytes': entry.size_bytes
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, default=str)
        
        except Exception as e:
            logger.error(f"Error persisting cache entry {entry.key}: {e}")
    
    def _load_persistent_cache(self) -> None:
        """Load persistent cache from disk"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Recreate cache entry
                entry = CacheEntry(
                    key=data['key'],
                    value=data['value'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    last_accessed=datetime.fromisoformat(data['last_accessed']),
                    access_count=data['access_count'],
                    ttl=data.get('ttl'),
                    tags=set(data.get('tags', [])),
                    size_bytes=data.get('size_bytes', 1024)
                )
                
                # Check if entry is still valid
                if entry.ttl:
                    age = (datetime.now() - entry.created_at).total_seconds()
                    if age <= entry.ttl:
                        self.cache_store[entry.key] = entry
                else:
                    self.cache_store[entry.key] = entry
        
        except Exception as e:
            logger.error(f"Error loading persistent cache: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'cache_size': len(self.cache_store),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'total_requests': total_requests,
                **self.stats,
                'patterns_tracked': len(self.access_tracker.patterns),
                'invalidation_rules': len(self.invalidation_engine.invalidation_rules)
            }
    
    def clear_cache(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self.cache_store.clear()
            if self.enable_persistence:
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
            logger.info("Cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        with self._lock:
            return {
                'statistics': self.get_statistics(),
                'entries': [
                    {
                        'key': key,
                        'created_at': entry.created_at.isoformat(),
                        'last_accessed': entry.last_accessed.isoformat(),
                        'access_count': entry.access_count,
                        'size_bytes': entry.size_bytes,
                        'tags': list(entry.tags),
                        'ttl': entry.ttl
                    }
                    for key, entry in self.cache_store.items()
                ],
                'frequent_patterns': {
                    key: asdict(pattern) 
                    for key, pattern in self.access_tracker.get_frequent_patterns().items()
                }
            }

# Global instance for easy access
_Configurable_cache_service = None

def get_Configurable_cache_service(**kwargs) -> ConfigurableCachingService:
    """Get or create global smart cache service instance"""
    global _Configurable_cache_service
    if _Configurable_cache_service is None:
        _Configurable_cache_service = ConfigurableCachingService(**kwargs)
    return _Configurable_cache_service
