"""
Lazy loading system for dashboard components and data.

This module provides Automated lazy loading capabilities:
- Component lazy loading for UI elements
- Data lazy loading with progressive fetching
- Image and asset lazy loading
- Module lazy loading with dynamic imports
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union, Tuple, Set
import threading
from collections import defaultdict
import weakref
import importlib
from functools import wraps

logger = logging.getLogger(__name__)


class LoadingState(Enum):
    """Loading states for lazy-loaded components."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    STALE = "stale"


class LoadingPriority(Enum):
    """Loading priorities."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class LoadableItem:
    """Represents a lazy-loadable item."""
    key: str
    loader: Callable
    state: LoadingState = LoadingState.UNLOADED
    data: Any = None
    error: Optional[Exception] = None
    last_loaded: Optional[datetime] = None
    load_count: int = 0
    priority: LoadingPriority = LoadingPriority.NORMAL
    ttl: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """Check if item has expired."""
        if self.ttl is None or self.last_loaded is None:
            return False
        return (datetime.now() - self.last_loaded).total_seconds() > self.ttl
    
    @property
    def needs_reload(self) -> bool:
        """Check if item needs reloading."""
        return (
            self.state == LoadingState.UNLOADED or
            self.state == LoadingState.FAILED or
            self.state == LoadingState.STALE or
            self.is_expired
        )


class LazyLoadStrategy(ABC):
    """Abstract base class for lazy loading strategies."""
    
    @abstractmethod
    async def should_load(self, item: LoadableItem, context: Dict[str, Any]) -> bool:
        """Determine if item should be loaded."""
        pass
    
    @abstractmethod
    def get_load_priority(self, item: LoadableItem, context: Dict[str, Any]) -> LoadingPriority:
        """Get loading priority for item."""
        pass


class OnDemandStrategy(LazyLoadStrategy):
    """Load items only when explicitly requested."""
    
    async def should_load(self, item: LoadableItem, context: Dict[str, Any]) -> bool:
        """Load only when explicitly requested."""
        return context.get('explicit_request', False)
    
    def get_load_priority(self, item: LoadableItem, context: Dict[str, Any]) -> LoadingPriority:
        """Return item's configured priority."""
        return item.priority


class ViewportStrategy(LazyLoadStrategy):
    """Load items when they come into viewport or close to it."""
    
    def __init__(self, viewport_margin: float = 200.0):
        self.viewport_margin = viewport_margin
    
    async def should_load(self, item: LoadableItem, context: Dict[str, Any]) -> bool:
        """Load when item is in or near viewport."""
        viewport = context.get('viewport', {})
        item_position = item.metadata.get('position', {})
        
        if not viewport or not item_position:
            return False
        
        # Check if item is within expanded viewport
        item_top = item_position.get('top', 0)
        item_bottom = item_position.get('bottom', 0)
        viewport_top = viewport.get('top', 0) - self.viewport_margin
        viewport_bottom = viewport.get('bottom', 0) + self.viewport_margin
        
        return item_bottom >= viewport_top and item_top <= viewport_bottom
    
    def get_load_priority(self, item: LoadableItem, context: Dict[str, Any]) -> LoadingPriority:
        """Higher priority for items closer to viewport center."""
        viewport = context.get('viewport', {})
        item_position = item.metadata.get('position', {})
        
        if not viewport or not item_position:
            return item.priority
        
        viewport_center = (viewport.get('top', 0) + viewport.get('bottom', 0)) / 2
        item_center = (item_position.get('top', 0) + item_position.get('bottom', 0)) / 2
        
        distance = abs(viewport_center - item_center)
        
        # Closer items get higher priority
        if distance < 100:
            return LoadingPriority.CRITICAL
        elif distance < 300:
            return LoadingPriority.HIGH
        else:
            return LoadingPriority.NORMAL


class PredictiveStrategy(LazyLoadStrategy):
    """Predictively load items based on user behavior."""
    
    def __init__(self, prediction_model: Optional[Callable] = None):
        self.prediction_model = prediction_model
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.prediction_cache: Dict[str, float] = {}
    
    async def should_load(self, item: LoadableItem, context: Dict[str, Any]) -> bool:
        """Load based on prediction score."""
        score = await self._get_prediction_score(item, context)
        threshold = context.get('prediction_threshold', 0.7)
        return score >= threshold
    
    def get_load_priority(self, item: LoadableItem, context: Dict[str, Any]) -> LoadingPriority:
        """Priority based on prediction score."""
        score = self.prediction_cache.get(item.key, 0.0)
        
        if score >= 0.9:
            return LoadingPriority.CRITICAL
        elif score >= 0.7:
            return LoadingPriority.HIGH
        elif score >= 0.5:
            return LoadingPriority.NORMAL
        else:
            return LoadingPriority.LOW
    
    async def _get_prediction_score(self, item: LoadableItem, context: Dict[str, Any]) -> float:
        """Calculate prediction score for item."""
        if self.prediction_model:
            try:
                score = await self.prediction_model(item, context, self.access_patterns)
                self.prediction_cache[item.key] = score
                return score
            except Exception as e:
                logger.error(f"Error in prediction model: {e}")
        
        # Fallback: simple frequency-based prediction
        access_times = self.access_patterns.get(item.key, [])
        recent_accesses = [
            t for t in access_times
            if (datetime.now() - t).total_seconds() < 3600  # Last hour
        ]
        
        score = min(len(recent_accesses) / 10.0, 1.0)  # Normalize to 0-1
        self.prediction_cache[item.key] = score
        return score
    
    def record_access(self, key: str) -> None:
        """Record access pattern for prediction."""
        self.access_patterns[key].append(datetime.now())
        
        # Keep only recent access times
        cutoff = datetime.now() - timedelta(hours=24)
        self.access_patterns[key] = [
            t for t in self.access_patterns[key] if t >= cutoff
        ]


class LazyLoader:
    """Main lazy loading orchestrator."""
    
    def __init__(
        self,
        strategy: LazyLoadStrategy,
        max_concurrent_loads: int = 5,
        load_timeout: int = 30
    ):
        self.strategy = strategy
        self.max_concurrent_loads = max_concurrent_loads
        self.load_timeout = load_timeout
        
        self.items: Dict[str, LoadableItem] = {}
        self.loading_queue: List[LoadableItem] = []
        self.active_loads: Set[str] = set()
        self.load_semaphore = asyncio.Semaphore(max_concurrent_loads)
        
        self._lock = threading.RLock()
        self._load_task = None
        self._running = False
    
    def register_item(
        self,
        key: str,
        loader: Callable,
        priority: LoadingPriority = LoadingPriority.NORMAL,
        ttl: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a lazy-loadable item."""
        with self._lock:
            item = LoadableItem(
                key=key,
                loader=loader,
                priority=priority,
                ttl=ttl,
                dependencies=dependencies or [],
                metadata=metadata or {}
            )
            self.items[key] = item
    
    def unregister_item(self, key: str) -> None:
        """Unregister a lazy-loadable item."""
        with self._lock:
            if key in self.items:
                del self.items[key]
            
            # Remove from loading queue
            self.loading_queue = [item for item in self.loading_queue if item.key != key]
    
    async def load_item(self, key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Load a specific item."""
        context = context or {}
        
        with self._lock:
            if key not in self.items:
                raise ValueError(f"Item '{key}' not registered")
            
            item = self.items[key]
        
        # Check if already loaded and not expired
        if item.state == LoadingState.LOADED and not item.is_expired:
            return item.data
        
        # Check if currently loading
        if item.state == LoadingState.LOADING:
            return await self._wait_for_load(key)
        
        # Load the item
        return await self._load_item_internal(item, context)
    
    async def _load_item_internal(self, item: LoadableItem, context: Dict[str, Any]) -> Any:
        """Internal item loading logic."""
        async with self.load_semaphore:
            if item.key in self.active_loads:
                return await self._wait_for_load(item.key)
            
            self.active_loads.add(item.key)
            item.state = LoadingState.LOADING
            
            try:
                # Load dependencies first
                for dep_key in item.dependencies:
                    if dep_key in self.items:
                        await self.load_item(dep_key, context)
                
                # Load the item
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(item.loader):
                    data = await asyncio.wait_for(
                        item.loader(context),
                        timeout=self.load_timeout
                    )
                else:
                    data = await asyncio.get_event_loop().run_in_executor(
                        None, item.loader, context
                    )
                
                load_time = time.time() - start_time
                
                # Update item state
                item.data = data
                item.state = LoadingState.LOADED
                item.last_loaded = datetime.now()
                item.load_count += 1
                item.error = None
                
                logger.debug(f"Loaded item '{item.key}' in {load_time:.2f}s")
                return data
                
            except Exception as e:
                item.state = LoadingState.FAILED
                item.error = e
                logger.error(f"Failed to load item '{item.key}': {e}")
                raise
            
            finally:
                self.active_loads.discard(item.key)
    
    async def _wait_for_load(self, key: str) -> Any:
        """Wait for an item to finish loading."""
        max_wait = self.load_timeout
        wait_interval = 0.1
        waited = 0
        
        while waited < max_wait:
            item = self.items.get(key)
            if not item:
                raise ValueError(f"Item '{key}' not found")
            
            if item.state == LoadingState.LOADED:
                return item.data
            elif item.state == LoadingState.FAILED:
                if item.error:
                    raise item.error
                else:
                    raise RuntimeError(f"Item '{key}' failed to load")
            
            await asyncio.sleep(wait_interval)
            waited += wait_interval
        
        raise TimeoutError(f"Timed out waiting for item '{key}' to load")
    
    async def preload_items(self, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Preload items based on strategy."""
        context = context or {}
        preloaded = []
        
        with self._lock:
            candidate_items = [
                item for item in self.items.values()
                if item.needs_reload
            ]
        
        # Determine which items should be loaded
        load_candidates = []
        for item in candidate_items:
            try:
                if await self.strategy.should_load(item, context):
                    priority = self.strategy.get_load_priority(item, context)
                    load_candidates.append((item, priority))
            except Exception as e:
                logger.error(f"Error checking load strategy for '{item.key}': {e}")
        
        # Sort by priority
        load_candidates.sort(key=lambda x: x[1].value)
        
        # Load items
        load_tasks = []
        for item, _ in load_candidates:
            if len(load_tasks) < self.max_concurrent_loads:
                task = asyncio.create_task(self._load_item_internal(item, context))
                load_tasks.append((task, item.key))
            else:
                break
        
        # Wait for loads to complete
        for task, key in load_tasks:
            try:
                await task
                preloaded.append(key)
            except Exception as e:
                logger.error(f"Error preloading item '{key}': {e}")
        
        return preloaded
    
    def invalidate_item(self, key: str) -> None:
        """Mark an item as stale."""
        with self._lock:
            if key in self.items:
                self.items[key].state = LoadingState.STALE
    
    def invalidate_pattern(self, pattern: str) -> List[str]:
        """Invalidate items matching a pattern."""
        import fnmatch
        invalidated = []
        
        with self._lock:
            for key in self.items:
                if fnmatch.fnmatch(key, pattern):
                    self.items[key].state = LoadingState.STALE
                    invalidated.append(key)
        
        return invalidated
    
    def get_item_stats(self, key: str) -> Optional[Dict[str, Any]]:
        """Get statistics for an item."""
        with self._lock:
            item = self.items.get(key)
            if not item:
                return None
            
            return {
                "key": item.key,
                "state": item.state.value,
                "load_count": item.load_count,
                "last_loaded": item.last_loaded.isoformat() if item.last_loaded else None,
                "is_expired": item.is_expired,
                "priority": item.priority.value,
                "has_error": item.error is not None,
                "dependencies": item.dependencies,
                "metadata": item.metadata
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall lazy loader statistics."""
        with self._lock:
            stats = {
                "total_items": len(self.items),
                "states": defaultdict(int),
                "priorities": defaultdict(int),
                "active_loads": len(self.active_loads),
                "total_loads": sum(item.load_count for item in self.items.values()),
                "failed_items": [],
                "expired_items": []
            }
            
            for item in self.items.values():
                stats["states"][item.state.value] += 1
                stats["priorities"][item.priority.value] += 1
                
                if item.state == LoadingState.FAILED:
                    stats["failed_items"].append(item.key)
                
                if item.is_expired:
                    stats["expired_items"].append(item.key)
            
            return dict(stats)
    
    def start_background_loading(self) -> None:
        """Start background loading task."""
        if not self._running:
            self._running = True
            self._load_task = asyncio.create_task(self._background_load_loop())
    
    def stop_background_loading(self) -> None:
        """Stop background loading task."""
        self._running = False
        if self._load_task and not self._load_task.done():
            self._load_task.cancel()
    
    async def _background_load_loop(self) -> None:
        """Background loading loop."""
        while self._running:
            try:
                await asyncio.sleep(1)  # Check every second
                
                # Preload items if strategy supports it
                if hasattr(self.strategy, 'background_context'):
                    context = await self.strategy.background_context()
                    await self.preload_items(context)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background loading: {e}")
    
    def __del__(self):
        """Cleanup resources."""
        self.stop_background_loading()


class ComponentLazyLoader:
    """Specialized lazy loader for UI components."""
    
    def __init__(self, lazy_loader: LazyLoader):
        self.lazy_loader = lazy_loader
        self.component_registry: Dict[str, Dict[str, Any]] = {}
    
    def register_component(
        self,
        component_id: str,
        component_factory: Callable,
        render_placeholder: Optional[Callable] = None,
        **kwargs
    ) -> None:
        """Register a lazy-loadable UI component."""
        def component_loader(context):
            return component_factory(**context)
        
        self.lazy_loader.register_item(
            f"component:{component_id}",
            component_loader,
            **kwargs
        )
        
        self.component_registry[component_id] = {
            "factory": component_factory,
            "placeholder": render_placeholder
        }
    
    async def render_component(
        self,
        component_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Render a component, loading it lazily if needed."""
        context = context or {}
        
        try:
            component = await self.lazy_loader.load_item(f"component:{component_id}", context)
            return component
        except Exception as e:
            logger.error(f"Error loading component '{component_id}': {e}")
            
            # Return placeholder if available
            placeholder = self.component_registry.get(component_id, {}).get('placeholder')
            if placeholder:
                return placeholder(error=e)
            
            # Return error component
            return {"type": "error", "message": str(e)}


class DataLazyLoader:
    """Specialized lazy loader for data fetching."""
    
    def __init__(self, lazy_loader: LazyLoader):
        self.lazy_loader = lazy_loader
        self.data_sources: Dict[str, Callable] = {}
    
    def register_data_source(
        self,
        source_id: str,
        fetch_function: Callable,
        cache_ttl: Optional[int] = None,
        **kwargs
    ) -> None:
        """Register a lazy-loadable data source."""
        def data_loader(context):
            return fetch_function(**context)
        
        self.lazy_loader.register_item(
            f"data:{source_id}",
            data_loader,
            ttl=cache_ttl,
            **kwargs
        )
        
        self.data_sources[source_id] = fetch_function
    
    async def fetch_data(
        self,
        source_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Fetch data from a source, loading it lazily if needed."""
        context = params or {}
        
        try:
            data = await self.lazy_loader.load_item(f"data:{source_id}", context)
            return data
        except Exception as e:
            logger.error(f"Error fetching data from '{source_id}': {e}")
            raise


# Decorator for lazy loading functions
def lazy_load(
    key: Optional[str] = None,
    priority: LoadingPriority = LoadingPriority.NORMAL,
    ttl: Optional[int] = None,
    dependencies: Optional[List[str]] = None
):
    """Decorator to make a function lazy-loadable."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would need to be integrated with a global lazy loader instance
            # For now, it's a placeholder for the concept
            return await func(*args, **kwargs)
        
        # Store lazy loading metadata
        wrapper._lazy_load_key = key or func.__name__
        wrapper._lazy_load_priority = priority
        wrapper._lazy_load_ttl = ttl
        wrapper._lazy_load_dependencies = dependencies or []
        
        return wrapper
    
    return decorator


# Module lazy loading utilities
class ModuleLazyLoader:
    """Lazy loader for Python modules."""
    
    def __init__(self):
        self.loaded_modules: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def register_module(self, name: str, module_path: str) -> None:
        """Register a module for lazy loading."""
        with self._lock:
            self.loaded_modules[name] = {
                "path": module_path,
                "module": None,
                "loaded": False
            }
    
    def load_module(self, name: str) -> Any:
        """Load a module lazily."""
        with self._lock:
            if name not in self.loaded_modules:
                raise ValueError(f"Module '{name}' not registered")
            
            module_info = self.loaded_modules[name]
            
            if not module_info["loaded"]:
                try:
                    module_info["module"] = importlib.import_module(module_info["path"])
                    module_info["loaded"] = True
                    logger.debug(f"Lazy loaded module: {name}")
                except Exception as e:
                    logger.error(f"Error loading module '{name}': {e}")
                    raise
            
            return module_info["module"]
    
    def is_loaded(self, name: str) -> bool:
        """Check if a module is loaded."""
        with self._lock:
            return self.loaded_modules.get(name, {}).get("loaded", False)
