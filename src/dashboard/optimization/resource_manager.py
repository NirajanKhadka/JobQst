"""
Resource management system for optimal performance.

This module provides Automated resource management:
- CPU usage monitoring and optimization
- Memory management and allocation
- Thread pool management
- Connection pooling
- Resource quotas and limits
"""

import asyncio
import logging
import psutil
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from collections import deque, defaultdict
import weakref
import gc
import os

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of managed resources."""
    CPU = "cpu"
    MEMORY = "memory"
    THREADS = "threads"
    CONNECTIONS = "connections"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"


class PriorityLevel(Enum):
    """Resource allocation priorities."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ResourceQuota:
    """Resource quota configuration."""
    resource_type: ResourceType
    max_value: float
    warning_threshold: float = 0.8
    critical_threshold: float = 0.9
    auto_scale: bool = False
    scale_factor: float = 1.5


@dataclass
class ResourceUsage:
    """Resource usage snapshot."""
    resource_type: ResourceType
    current_value: float
    max_value: float
    percentage: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_warning(self) -> bool:
        """Check if usage is at warning level."""
        return self.percentage >= 80.0
    
    @property
    def is_critical(self) -> bool:
        """Check if usage is at critical level."""
        return self.percentage >= 90.0


@dataclass
class ResourceAllocation:
    """Resource allocation request."""
    resource_type: ResourceType
    requested_amount: float
    priority: PriorityLevel
    max_wait_time: float = 30.0
    callback: Optional[Callable] = None


class ResourceManager(ABC):
    """Abstract base class for resource managers."""
    
    @abstractmethod
    async def allocate(self, allocation: ResourceAllocation) -> bool:
        """Allocate resources."""
        pass
    
    @abstractmethod
    async def release(self, resource_type: ResourceType, amount: float) -> None:
        """Release resources."""
        pass
    
    @abstractmethod
    def get_usage(self) -> ResourceUsage:
        """Get current resource usage."""
        pass
    
    @abstractmethod
    async def optimize(self) -> Dict[str, Any]:
        """Optimize resource usage."""
        pass


class CPUManager(ResourceManager):
    """CPU resource manager."""
    
    def __init__(
        self,
        max_cpu_percent: float = 80.0,
        monitoring_interval: float = 1.0
    ):
        self.max_cpu_percent = max_cpu_percent
        self.monitoring_interval = monitoring_interval
        
        self.cpu_history: deque = deque(maxlen=100)
        self.allocated_cpu: float = 0.0
        self.cpu_semaphore = asyncio.Semaphore(100)  # Percentage-based
        
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
    
    async def allocate(self, allocation: ResourceAllocation) -> bool:
        """Allocate CPU resources."""
        if allocation.resource_type != ResourceType.CPU:
            return False
        
        try:
            # Wait for available CPU resources
            await asyncio.wait_for(
                self.cpu_semaphore.acquire(),
                timeout=allocation.max_wait_time
            )
            
            with self._lock:
                self.allocated_cpu += allocation.requested_amount
            
            return True
        
        except asyncio.TimeoutError:
            logger.warning(f"CPU allocation timeout for {allocation.requested_amount}%")
            return False
    
    async def release(self, resource_type: ResourceType, amount: float) -> None:
        """Release CPU resources."""
        if resource_type != ResourceType.CPU:
            return
        
        with self._lock:
            self.allocated_cpu = max(0, self.allocated_cpu - amount)
        
        self.cpu_semaphore.release()
    
    def get_usage(self) -> ResourceUsage:
        """Get current CPU usage."""
        current_cpu = psutil.cpu_percent()
        
        return ResourceUsage(
            resource_type=ResourceType.CPU,
            current_value=current_cpu,
            max_value=100.0,
            percentage=current_cpu
        )
    
    async def optimize(self) -> Dict[str, Any]:
        """Optimize CPU usage."""
        current_usage = self.get_usage()
        optimizations = []
        
        # Check if CPU is overloaded
        if current_usage.percentage > self.max_cpu_percent:
            # Reduce thread pool sizes
            optimizations.append("reduce_thread_pools")
            
            # Suggest process prioritization
            optimizations.append("adjust_process_priority")
        
        return {
            "current_cpu": current_usage.percentage,
            "optimizations_applied": optimizations
        }
    
    def start_monitoring(self) -> None:
        """Start CPU monitoring."""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    def stop_monitoring(self) -> None:
        """Stop CPU monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
    
    async def _monitor_loop(self) -> None:
        """CPU monitoring loop."""
        while self._monitoring:
            try:
                cpu_usage = psutil.cpu_percent()
                self.cpu_history.append((datetime.now(), cpu_usage))
                
                # Adjust semaphore based on current load
                if cpu_usage > self.max_cpu_percent:
                    # Reduce available permits
                    if self.cpu_semaphore._value > 10:
                        try:
                            self.cpu_semaphore.acquire_nowait()
                        except:
                            pass
                
                await asyncio.sleep(self.monitoring_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in CPU monitoring: {e}")


class MemoryManager(ResourceManager):
    """Memory resource manager."""
    
    def __init__(
        self,
        max_memory_mb: Optional[float] = None,
        gc_threshold_mb: float = 100.0
    ):
        self.max_memory_mb = max_memory_mb or (psutil.virtual_memory().total / 1024 / 1024 * 0.8)
        self.gc_threshold_mb = gc_threshold_mb
        
        self.allocated_memory: float = 0.0
        self.memory_allocations: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    async def allocate(self, allocation: ResourceAllocation) -> bool:
        """Allocate memory resources."""
        if allocation.resource_type != ResourceType.MEMORY:
            return False
        
        current_memory = self._get_current_memory_usage()
        
        with self._lock:
            if current_memory + allocation.requested_amount > self.max_memory_mb:
                # Try to free memory first
                await self._try_free_memory(allocation.requested_amount)
                
                # Check again
                current_memory = self._get_current_memory_usage()
                if current_memory + allocation.requested_amount > self.max_memory_mb:
                    return False
            
            self.allocated_memory += allocation.requested_amount
            allocation_id = str(id(allocation))
            self.memory_allocations[allocation_id] = allocation.requested_amount
        
        return True
    
    async def release(self, resource_type: ResourceType, amount: float) -> None:
        """Release memory resources."""
        if resource_type != ResourceType.MEMORY:
            return
        
        with self._lock:
            self.allocated_memory = max(0, self.allocated_memory - amount)
        
        # Trigger garbage collection if needed
        if amount > self.gc_threshold_mb:
            gc.collect()
    
    def get_usage(self) -> ResourceUsage:
        """Get current memory usage."""
        memory = psutil.virtual_memory()
        current_mb = memory.used / 1024 / 1024
        
        return ResourceUsage(
            resource_type=ResourceType.MEMORY,
            current_value=current_mb,
            max_value=self.max_memory_mb,
            percentage=(current_mb / self.max_memory_mb) * 100
        )
    
    async def optimize(self) -> Dict[str, Any]:
        """Optimize memory usage."""
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory usage before and after
        usage_before = self.get_usage()
        await asyncio.sleep(0.1)  # Brief pause
        usage_after = self.get_usage()
        
        memory_freed = usage_before.current_value - usage_after.current_value
        
        return {
            "gc_collected": collected,
            "memory_freed_mb": memory_freed,
            "current_usage_percent": usage_after.percentage
        }
    
    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return psutil.virtual_memory().used / 1024 / 1024
    
    async def _try_free_memory(self, needed_mb: float) -> None:
        """Try to free memory."""
        # Force garbage collection
        gc.collect()
        
        # Additional cleanup strategies could be implemented here
        # e.g., clearing caches, reducing buffer sizes, etc.


class ThreadPoolManager(ResourceManager):
    """Thread pool resource manager."""
    
    def __init__(
        self,
        max_threads: int = 50,
        thread_timeout: float = 300.0
    ):
        self.max_threads = max_threads
        self.thread_timeout = thread_timeout
        
        self.thread_pools: Dict[str, ThreadPoolExecutor] = {}
        self.pool_configs: Dict[str, Dict] = {}
        self.active_threads: int = 0
        self._lock = threading.RLock()
    
    async def allocate(self, allocation: ResourceAllocation) -> bool:
        """Allocate thread resources."""
        if allocation.resource_type != ResourceType.THREADS:
            return False
        
        requested_threads = int(allocation.requested_amount)
        
        with self._lock:
            if self.active_threads + requested_threads > self.max_threads:
                return False
            
            self.active_threads += requested_threads
        
        return True
    
    async def release(self, resource_type: ResourceType, amount: float) -> None:
        """Release thread resources."""
        if resource_type != ResourceType.THREADS:
            return
        
        released_threads = int(amount)
        
        with self._lock:
            self.active_threads = max(0, self.active_threads - released_threads)
    
    def get_usage(self) -> ResourceUsage:
        """Get current thread usage."""
        return ResourceUsage(
            resource_type=ResourceType.THREADS,
            current_value=float(self.active_threads),
            max_value=float(self.max_threads),
            percentage=(self.active_threads / self.max_threads) * 100
        )
    
    async def optimize(self) -> Dict[str, Any]:
        """Optimize thread pool usage."""
        optimizations = []
        
        with self._lock:
            # Check for idle thread pools
            idle_pools = []
            for pool_name, pool in self.thread_pools.items():
                if hasattr(pool, '_threads') and len(pool._threads) == 0:
                    idle_pools.append(pool_name)
            
            # Shutdown idle pools
            for pool_name in idle_pools:
                pool = self.thread_pools.pop(pool_name)
                pool.shutdown(wait=False)
                optimizations.append(f"shutdown_idle_pool_{pool_name}")
        
        return {
            "optimizations_applied": optimizations,
            "active_pools": len(self.thread_pools),
            "active_threads": self.active_threads
        }
    
    def create_pool(
        self,
        pool_name: str,
        max_workers: int,
        priority: PriorityLevel = PriorityLevel.NORMAL
    ) -> ThreadPoolExecutor:
        """Create a new thread pool."""
        with self._lock:
            if pool_name in self.thread_pools:
                return self.thread_pools[pool_name]
            
            pool = ThreadPoolExecutor(
                max_workers=max_workers,
                thread_name_prefix=f"{pool_name}_"
            )
            
            self.thread_pools[pool_name] = pool
            self.pool_configs[pool_name] = {
                "max_workers": max_workers,
                "priority": priority,
                "created_at": datetime.now()
            }
            
            return pool
    
    def get_pool(self, pool_name: str) -> Optional[ThreadPoolExecutor]:
        """Get existing thread pool."""
        return self.thread_pools.get(pool_name)
    
    def shutdown_pool(self, pool_name: str, wait: bool = True) -> bool:
        """Shutdown a thread pool."""
        with self._lock:
            if pool_name not in self.thread_pools:
                return False
            
            pool = self.thread_pools.pop(pool_name)
            self.pool_configs.pop(pool_name, None)
            
            pool.shutdown(wait=wait)
            return True


class ConnectionPoolManager(ResourceManager):
    """Connection pool resource manager."""
    
    def __init__(
        self,
        max_connections: int = 100,
        connection_timeout: float = 30.0,
        idle_timeout: float = 300.0
    ):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        
        self.connection_pools: Dict[str, List] = defaultdict(list)
        self.active_connections: Dict[str, int] = defaultdict(int)
        self.connection_metadata: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    async def allocate(self, allocation: ResourceAllocation) -> bool:
        """Allocate connection resources."""
        if allocation.resource_type != ResourceType.CONNECTIONS:
            return False
        
        pool_name = allocation.callback.__name__ if allocation.callback else "default"
        requested_connections = int(allocation.requested_amount)
        
        with self._lock:
            current_total = sum(self.active_connections.values())
            if current_total + requested_connections > self.max_connections:
                return False
            
            self.active_connections[pool_name] += requested_connections
        
        return True
    
    async def release(self, resource_type: ResourceType, amount: float) -> None:
        """Release connection resources."""
        if resource_type != ResourceType.CONNECTIONS:
            return
        
        released_connections = int(amount)
        
        with self._lock:
            # Find pool with connections to release
            for pool_name in self.active_connections:
                if self.active_connections[pool_name] >= released_connections:
                    self.active_connections[pool_name] -= released_connections
                    break
    
    def get_usage(self) -> ResourceUsage:
        """Get current connection usage."""
        with self._lock:
            total_active = sum(self.active_connections.values())
        
        return ResourceUsage(
            resource_type=ResourceType.CONNECTIONS,
            current_value=float(total_active),
            max_value=float(self.max_connections),
            percentage=(total_active / self.max_connections) * 100
        )
    
    async def optimize(self) -> Dict[str, Any]:
        """Optimize connection pools."""
        optimizations = []
        
        with self._lock:
            # Clean up idle connections
            for pool_name, connections in self.connection_pools.items():
                idle_connections = []
                for conn in connections:
                    metadata = self.connection_metadata.get(id(conn), {})
                    last_used = metadata.get('last_used', datetime.now())
                    
                    if (datetime.now() - last_used).total_seconds() > self.idle_timeout:
                        idle_connections.append(conn)
                
                # Remove idle connections
                for conn in idle_connections:
                    connections.remove(conn)
                    if hasattr(conn, 'close'):
                        try:
                            conn.close()
                        except:
                            pass
                
                if idle_connections:
                    optimizations.append(f"closed_{len(idle_connections)}_idle_connections_{pool_name}")
        
        return {
            "optimizations_applied": optimizations,
            "active_pools": len(self.connection_pools),
            "total_connections": sum(self.active_connections.values())
        }
    
    async def get_connection(self, pool_name: str, factory: Callable) -> Any:
        """Get connection from pool."""
        with self._lock:
            pool = self.connection_pools[pool_name]
            
            if pool:
                conn = pool.pop()
                self.connection_metadata[id(conn)] = {
                    'last_used': datetime.now(),
                    'pool_name': pool_name
                }
                return conn
            
            # Create new connection if under limit
            total_active = sum(self.active_connections.values())
            if total_active < self.max_connections:
                conn = await factory()
                self.active_connections[pool_name] += 1
                self.connection_metadata[id(conn)] = {
                    'created_at': datetime.now(),
                    'last_used': datetime.now(),
                    'pool_name': pool_name
                }
                return conn
            
            return None
    
    async def return_connection(self, pool_name: str, connection: Any) -> None:
        """Return connection to pool."""
        with self._lock:
            self.connection_pools[pool_name].append(connection)
            self.connection_metadata[id(connection)]['last_used'] = datetime.now()


class GlobalResourceManager:
    """Global resource manager coordinating all resource types."""
    
    def __init__(self):
        self.managers: Dict[ResourceType, ResourceManager] = {
            ResourceType.CPU: CPUManager(),
            ResourceType.MEMORY: MemoryManager(),
            ResourceType.THREADS: ThreadPoolManager(),
            ResourceType.CONNECTIONS: ConnectionPoolManager()
        }
        
        self.quotas: Dict[ResourceType, ResourceQuota] = {}
        self.monitoring_enabled: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def set_quota(self, quota: ResourceQuota) -> None:
        """Set resource quota."""
        self.quotas[quota.resource_type] = quota
    
    async def allocate_resources(
        self,
        allocations: List[ResourceAllocation]
    ) -> Dict[ResourceType, bool]:
        """Allocate multiple resources atomically."""
        results = {}
        allocated = []
        
        try:
            # Try to allocate all resources
            for allocation in allocations:
                manager = self.managers.get(allocation.resource_type)
                if manager:
                    success = await manager.allocate(allocation)
                    results[allocation.resource_type] = success
                    
                    if success:
                        allocated.append(allocation)
                    else:
                        # Rollback previous allocations
                        for prev_allocation in allocated:
                            prev_manager = self.managers.get(prev_allocation.resource_type)
                            if prev_manager:
                                await prev_manager.release(
                                    prev_allocation.resource_type,
                                    prev_allocation.requested_amount
                                )
                        return {rt: False for rt in [a.resource_type for a in allocations]}
                else:
                    results[allocation.resource_type] = False
            
            return results
        
        except Exception as e:
            logger.error(f"Error allocating resources: {e}")
            # Rollback on error
            for allocation in allocated:
                manager = self.managers.get(allocation.resource_type)
                if manager:
                    await manager.release(
                        allocation.resource_type,
                        allocation.requested_amount
                    )
            return {rt: False for rt in [a.resource_type for a in allocations]}
    
    async def release_resources(
        self,
        releases: List[Tuple[ResourceType, float]]
    ) -> None:
        """Release multiple resources."""
        for resource_type, amount in releases:
            manager = self.managers.get(resource_type)
            if manager:
                await manager.release(resource_type, amount)
    
    def get_system_usage(self) -> Dict[ResourceType, ResourceUsage]:
        """Get usage for all resource types."""
        usage = {}
        for resource_type, manager in self.managers.items():
            try:
                usage[resource_type] = manager.get_usage()
            except Exception as e:
                logger.error(f"Error getting usage for {resource_type}: {e}")
        
        return usage
    
    async def optimize_all_resources(self) -> Dict[str, Any]:
        """Optimize all managed resources."""
        optimization_results = {}
        
        for resource_type, manager in self.managers.items():
            try:
                result = await manager.optimize()
                optimization_results[resource_type.value] = result
            except Exception as e:
                logger.error(f"Error optimizing {resource_type}: {e}")
                optimization_results[resource_type.value] = {"error": str(e)}
        
        return optimization_results
    
    def start_monitoring(self, interval: float = 30.0) -> None:
        """Start resource monitoring."""
        if not self.monitoring_enabled:
            self.monitoring_enabled = True
            self._monitor_task = asyncio.create_task(self._monitoring_loop(interval))
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self.monitoring_enabled = False
        if self._monitor_task:
            self._monitor_task.cancel()
    
    async def _monitoring_loop(self, interval: float) -> None:
        """Resource monitoring loop."""
        while self.monitoring_enabled:
            try:
                usage = self.get_system_usage()
                
                # Check quotas and trigger optimizations if needed
                for resource_type, resource_usage in usage.items():
                    quota = self.quotas.get(resource_type)
                    if quota:
                        if resource_usage.percentage > quota.critical_threshold * 100:
                            logger.warning(f"Critical resource usage: {resource_type.value} at {resource_usage.percentage:.1f}%")
                            # Trigger optimization
                            manager = self.managers.get(resource_type)
                            if manager:
                                await manager.optimize()
                
                await asyncio.sleep(interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        usage = self.get_system_usage()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "resource_usage": {
                rt.value: {
                    "current": usage[rt].current_value,
                    "max": usage[rt].max_value,
                    "percentage": usage[rt].percentage,
                    "status": "critical" if usage[rt].is_critical else "warning" if usage[rt].is_warning else "normal"
                }
                for rt, usage in usage.items()
            },
            "quotas": {
                rt.value: {
                    "max_value": quota.max_value,
                    "warning_threshold": quota.warning_threshold,
                    "critical_threshold": quota.critical_threshold,
                    "auto_scale": quota.auto_scale
                }
                for rt, quota in self.quotas.items()
            }
        }
        
        return report


# Context manager for resource allocation
class ResourceContext:
    """Context manager for automatic resource management."""
    
    def __init__(
        self,
        resource_manager: GlobalResourceManager,
        allocations: List[ResourceAllocation]
    ):
        self.resource_manager = resource_manager
        self.allocations = allocations
        self.allocated_successfully = False
    
    async def __aenter__(self):
        """Allocate resources on context entry."""
        results = await self.resource_manager.allocate_resources(self.allocations)
        self.allocated_successfully = all(results.values())
        
        if not self.allocated_successfully:
            raise RuntimeError("Failed to allocate required resources")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release resources on context exit."""
        if self.allocated_successfully:
            releases = [
                (allocation.resource_type, allocation.requested_amount)
                for allocation in self.allocations
            ]
            await self.resource_manager.release_resources(releases)


# Utility functions
def create_resource_allocation(
    resource_type: ResourceType,
    amount: float,
    priority: PriorityLevel = PriorityLevel.NORMAL,
    max_wait: float = 30.0
) -> ResourceAllocation:
    """Create a resource allocation request."""
    return ResourceAllocation(
        resource_type=resource_type,
        requested_amount=amount,
        priority=priority,
        max_wait_time=max_wait
    )
