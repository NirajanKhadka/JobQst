"""
Performance optimization utilities for JobQst
Implements lazy loading, caching, and resource management
"""

import asyncio
import functools
import time
import logging
from typing import Dict, Any, Optional, Callable
from contextlib import asynccontextmanager
import psutil

logger = logging.getLogger(__name__)


class LazyImporter:
    """Lazy import manager for heavy dependencies"""
    
    def __init__(self):
        self._imports: Dict[str, Any] = {}
        self._import_times: Dict[str, float] = {}
    
    def lazy_import(self, module_name: str, package: Optional[str] = None):
        """Decorator for lazy importing heavy modules"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if module_name not in self._imports:
                    start_time = time.time()
                    try:
                        if package:
                            module = __import__(f"{package}.{module_name}", 
                                              fromlist=[module_name])
                        else:
                            module = __import__(module_name)
                        self._imports[module_name] = module
                        import_time = time.time() - start_time
                        self._import_times[module_name] = import_time
                        logger.info(f"Lazy loaded {module_name} in {import_time:.2f}s")
                    except ImportError as e:
                        logger.warning(f"Failed to import {module_name}: {e}")
                        self._imports[module_name] = None
                
                # Inject module into function globals
                func.__globals__[module_name] = self._imports[module_name]
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_import_stats(self) -> Dict[str, float]:
        """Get import timing statistics"""
        return self._import_times.copy()


class PerformanceMonitor:
    """System performance monitoring"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self._start_time = time.time()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'uptime': time.time() - self._start_time,
            'process_count': len(psutil.pids()),
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    
    def memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def performance_timer(self, operation_name: str):
        """Context manager for timing operations"""
        @asynccontextmanager
        async def timer():
            start_time = time.time()
            try:
                yield
            finally:
                duration = time.time() - start_time
                self.metrics[operation_name] = duration
                logger.info(f"{operation_name} completed in {duration:.2f}s")
        
        return timer()


class ResourceManager:
    """Smart resource allocation and management"""
    
    def __init__(self):
        self.cpu_count = psutil.cpu_count()
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        
    def optimal_worker_count(self, task_type: str = 'io_bound') -> int:
        """Calculate optimal worker count based on system resources"""
        if task_type == 'cpu_bound':
            return max(1, self.cpu_count - 1)
        elif task_type == 'io_bound':
            return min(32, max(4, self.cpu_count * 4))
        else:  # mixed workload
            return max(2, self.cpu_count * 2)
    
    def should_use_heavy_processing(self) -> bool:
        """Determine if system can handle heavy ML processing"""
        memory_available_gb = psutil.virtual_memory().available / (1024**3)
        cpu_usage = psutil.cpu_percent(interval=1)
        
        return (
            memory_available_gb > 2.0 and  # At least 2GB free memory
            cpu_usage < 80 and             # CPU usage below 80%
            self.cpu_count >= 4            # At least 4 CPU cores
        )
    
    async def adaptive_delay(self, base_delay: float = 1.0) -> None:
        """Adaptive delay based on system load"""
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_usage = psutil.virtual_memory().percent
        
        # Increase delay if system is under heavy load
        if cpu_usage > 80 or memory_usage > 85:
            delay = base_delay * 2
        elif cpu_usage > 60 or memory_usage > 70:
            delay = base_delay * 1.5
        else:
            delay = base_delay
        
        await asyncio.sleep(delay)


class CacheManager:
    """Intelligent caching system"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set item in cache with optional TTL"""
        # Cleanup if cache is full
        if len(self.cache) >= self.max_size:
            self._cleanup_cache()
        
        self.cache[key] = value
        self.access_times[key] = time.time()
        
        if ttl:
            # Schedule cleanup after TTL
            asyncio.create_task(self._cleanup_after_ttl(key, ttl))
    
    def _cleanup_cache(self) -> None:
        """Remove least recently used items"""
        if not self.access_times:
            return
        
        # Remove 25% of oldest items
        remove_count = max(1, len(self.cache) // 4)
        oldest_keys = sorted(self.access_times.keys(), 
                           key=lambda k: self.access_times[k])[:remove_count]
        
        for key in oldest_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    async def _cleanup_after_ttl(self, key: str, ttl: float) -> None:
        """Remove item after TTL expires"""
        await asyncio.sleep(ttl)
        self.cache.pop(key, None)
        self.access_times.pop(key, None)


# Global instances
lazy_importer = LazyImporter()
performance_monitor = PerformanceMonitor()
resource_manager = ResourceManager()
cache_manager = CacheManager()


# Decorators for easy usage
def lazy_import(module_name: str, package: Optional[str] = None):
    """Decorator for lazy importing"""
    return lazy_importer.lazy_import(module_name, package)


def monitor_performance(operation_name: str):
    """Decorator for monitoring function performance"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with performance_monitor.performance_timer(operation_name):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                performance_monitor.metrics[operation_name] = duration
                logger.info(f"{operation_name} completed in {duration:.2f}s")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def cached(ttl: Optional[float] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


# Example usage and integration functions
@lazy_import('torch')
@monitor_performance('ml_processing')
def heavy_ml_processing(data):
    """Example of heavy ML processing with lazy loading"""
    if torch is None:
        logger.warning("PyTorch not available, using fallback")
        return simple_fallback_processing(data)
    
    # Use PyTorch for processing
    return torch.tensor(data).mean().item()


def simple_fallback_processing(data):
    """Lightweight fallback for ML processing"""
    return sum(data) / len(data) if data else 0


@cached(ttl=300)  # Cache for 5 minutes
def expensive_computation(param1, param2):
    """Example of expensive computation with caching"""
    time.sleep(2)  # Simulate expensive operation
    return param1 * param2 + 42
