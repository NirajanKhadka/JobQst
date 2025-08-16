#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Healing Service Factory
Creates and manages services with automatic failure recovery capabilities.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Protocol
from dataclasses import dataclass
from enum import Enum
import psutil
import asyncio

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPING = "stopping"


@dataclass
class ServiceHealth:
    """Service health information."""
    name: str
    status: ServiceStatus
    last_check: datetime
    error_count: int
    last_error: Optional[str]
    uptime: timedelta
    memory_usage: float
    cpu_usage: float


class ServiceProtocol(Protocol):
    """Protocol for services managed by the factory."""
    
    def start(self) -> bool:
        """Start the service."""
        ...
    
    def stop(self) -> bool:
        """Stop the service."""
        ...
    
    def restart(self) -> bool:
        """Restart the service."""
        ...
    
    def health_check(self) -> bool:
        """Check if service is healthy."""
        ...
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        ...


class RecoveryStrategy:
    """Recovery strategy for failed services."""
    
    def __init__(self, name: str, max_retries: int = 3, 
                 backoff_factor: float = 2.0):
        self.name = name
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_count = 0
        self.last_attempt = None
    
    def should_retry(self) -> bool:
        """Check if we should attempt recovery."""
        if self.retry_count >= self.max_retries:
            return False
        
        if self.last_attempt:
            # Exponential backoff
            wait_time = (self.backoff_factor ** self.retry_count) * 60
            time_since_last = (datetime.now() - self.last_attempt).seconds
            return time_since_last >= wait_time
        
        return True
    
    def record_attempt(self) -> None:
        """Record a recovery attempt."""
        self.retry_count += 1
        self.last_attempt = datetime.now()
    
    def reset(self) -> None:
        """Reset retry counter."""
        self.retry_count = 0
        self.last_attempt = None


class HealthMonitor:
    """Monitor service health and trigger recovery."""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.services = {}
        self.health_data = {}
        self.running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        self.recovery_callbacks = {}
    
    def register_service(self, name: str, service: ServiceProtocol,
                        recovery_callback: Optional[Callable] = None) -> None:
        """Register a service for monitoring."""
        with self.lock:
            self.services[name] = service
            self.health_data[name] = ServiceHealth(
                name=name,
                status=ServiceStatus.UNKNOWN,
                last_check=datetime.now(),
                error_count=0,
                last_error=None,
                uptime=timedelta(),
                memory_usage=0.0,
                cpu_usage=0.0
            )
            if recovery_callback:
                self.recovery_callbacks[name] = recovery_callback
        
        logger.info(f"Registered service for monitoring: {name}")
    
    def start_monitoring(self) -> None:
        """Start health monitoring."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self.monitor_thread.start()
        logger.info("Health monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Health monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                self._check_all_services()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Longer sleep on error
    
    def _check_all_services(self) -> None:
        """Check health of all registered services."""
        with self.lock:
            services_to_check = list(self.services.items())
        
        for name, service in services_to_check:
            try:
                self._check_service_health(name, service)
            except Exception as e:
                logger.error(f"Error checking service {name}: {e}")
                self._update_health_status(name, ServiceStatus.UNKNOWN, str(e))
    
    def _check_service_health(self, name: str, service: ServiceProtocol) -> None:
        """Check health of a specific service."""
        try:
            # Basic health check
            is_healthy = service.health_check()
            
            # Get detailed status
            status_info = service.get_status()
            
            # Update health data
            with self.lock:
                health = self.health_data[name]
                health.last_check = datetime.now()
                
                if is_healthy:
                    if health.status == ServiceStatus.UNHEALTHY:
                        # Recovery detected
                        logger.info(f"Service {name} recovered")
                    
                    health.status = ServiceStatus.HEALTHY
                    health.error_count = 0
                    health.last_error = None
                else:
                    health.error_count += 1
                    health.status = ServiceStatus.UNHEALTHY
                    health.last_error = status_info.get('error', 'Unknown error')
                    
                    # Trigger recovery if callback exists
                    if name in self.recovery_callbacks:
                        self._trigger_recovery(name)
                
                # Update resource usage
                self._update_resource_usage(name, health)
        
        except Exception as e:
            logger.error(f"Failed to check service {name}: {e}")
            self._update_health_status(name, ServiceStatus.UNKNOWN, str(e))
    
    def _update_health_status(self, name: str, status: ServiceStatus,
                             error: Optional[str] = None) -> None:
        """Update service health status."""
        with self.lock:
            if name in self.health_data:
                health = self.health_data[name]
                health.status = status
                health.last_check = datetime.now()
                if error:
                    health.last_error = error
                    health.error_count += 1
    
    def _update_resource_usage(self, name: str, health: ServiceHealth) -> None:
        """Update resource usage information."""
        try:
            # Basic resource monitoring
            process = psutil.Process()
            health.memory_usage = process.memory_percent()
            health.cpu_usage = process.cpu_percent()
        except Exception:
            # Not critical if we can't get resource info
            pass
    
    def _trigger_recovery(self, name: str) -> None:
        """Trigger recovery for a failed service."""
        if name in self.recovery_callbacks:
            try:
                recovery_func = self.recovery_callbacks[name]
                logger.info(f"Triggering recovery for service: {name}")
                recovery_func()
            except Exception as e:
                logger.error(f"Recovery failed for service {name}: {e}")
    
    def get_health_summary(self) -> Dict[str, ServiceHealth]:
        """Get health summary for all services."""
        with self.lock:
            return dict(self.health_data)


class AutoHealingServiceFactory:
    """
    Service factory with auto-healing capabilities.
    
    Features:
    - Automatic service health monitoring
    - Recovery strategies for failed services
    - Graceful degradation support
    - Resource usage tracking
    """
    
    def __init__(self):
        self.services = {}
        self.health_monitor = HealthMonitor()
        self.recovery_strategies = {}
        self.service_dependencies = {}
        
        logger.info("AutoHealingServiceFactory initialized")
    
    @classmethod
    def create_resilient_services(cls) -> 'AutoHealingServiceFactory':
        """Create factory with default resilient configuration."""
        factory = cls()
        factory.health_monitor.start_monitoring()
        return factory
    
    def register_service(self, name: str, service: ServiceProtocol,
                        recovery_strategy: Optional[RecoveryStrategy] = None,
                        dependencies: Optional[List[str]] = None) -> None:
        """Register a service with auto-healing."""
        self.services[name] = service
        
        # Set up recovery strategy
        if recovery_strategy is None:
            recovery_strategy = RecoveryStrategy(name)
        self.recovery_strategies[name] = recovery_strategy
        
        # Set up dependencies
        if dependencies:
            self.service_dependencies[name] = dependencies
        
        # Register with health monitor
        self.health_monitor.register_service(
            name, service, lambda: self._auto_heal_service(name)
        )
        
        logger.info(f"Registered resilient service: {name}")
    
    def get_service(self, name: str) -> Optional[ServiceProtocol]:
        """Get a service by name."""
        return self.services.get(name)
    
    def start_service(self, name: str) -> bool:
        """Start a service."""
        if name not in self.services:
            logger.error(f"Service not found: {name}")
            return False
        
        try:
            service = self.services[name]
            result = service.start()
            if result:
                # Reset recovery strategy on successful start
                if name in self.recovery_strategies:
                    self.recovery_strategies[name].reset()
                logger.info(f"Service started: {name}")
            return result
        except Exception as e:
            logger.error(f"Failed to start service {name}: {e}")
            return False
    
    def stop_service(self, name: str) -> bool:
        """Stop a service."""
        if name not in self.services:
            logger.error(f"Service not found: {name}")
            return False
        
        try:
            service = self.services[name]
            result = service.stop()
            if result:
                logger.info(f"Service stopped: {name}")
            return result
        except Exception as e:
            logger.error(f"Failed to stop service {name}: {e}")
            return False
    
    def restart_service(self, name: str) -> bool:
        """Restart a service."""
        if name not in self.services:
            logger.error(f"Service not found: {name}")
            return False
        
        logger.info(f"Restarting service: {name}")
        
        # Stop first
        self.stop_service(name)
        time.sleep(2)  # Brief pause
        
        # Then start
        return self.start_service(name)
    
    def _auto_heal_service(self, name: str) -> None:
        """Automatically heal a failed service."""
        if name not in self.recovery_strategies:
            logger.warning(f"No recovery strategy for service: {name}")
            return
        
        strategy = self.recovery_strategies[name]
        
        if not strategy.should_retry():
            logger.warning(
                f"Max recovery attempts reached for service: {name}"
            )
            return
        
        logger.info(f"Attempting auto-heal for service: {name}")
        strategy.record_attempt()
        
        try:
            # Try restart
            if self.restart_service(name):
                logger.info(f"Auto-heal successful for service: {name}")
                strategy.reset()
            else:
                logger.warning(f"Auto-heal failed for service: {name}")
        except Exception as e:
            logger.error(f"Auto-heal error for service {name}: {e}")
    
    def get_service_health(self, name: str) -> Optional[ServiceHealth]:
        """Get health information for a service."""
        health_summary = self.health_monitor.get_health_summary()
        return health_summary.get(name)
    
    def get_all_services_health(self) -> Dict[str, ServiceHealth]:
        """Get health information for all services."""
        return self.health_monitor.get_health_summary()
    
    def monitor_and_heal_services(self) -> None:
        """Monitor all services and perform healing as needed."""
        health_summary = self.get_all_services_health()
        
        for name, health in health_summary.items():
            if health.status == ServiceStatus.UNHEALTHY:
                logger.info(f"Detected unhealthy service: {name}")
                # Auto-healing is triggered automatically by monitor
    
    def shutdown(self) -> None:
        """Shutdown the factory and all services."""
        logger.info("Shutting down AutoHealingServiceFactory")
        
        # Stop health monitoring
        self.health_monitor.stop_monitoring()
        
        # Stop all services
        for name in list(self.services.keys()):
            try:
                self.stop_service(name)
            except Exception as e:
                logger.error(f"Error stopping service {name}: {e}")
        
        logger.info("AutoHealingServiceFactory shutdown complete")


# Global factory instance
_global_factory = None


def get_auto_healing_factory() -> AutoHealingServiceFactory:
    """Get global auto-healing factory instance."""
    global _global_factory
    if _global_factory is None:
        _global_factory = AutoHealingServiceFactory.create_resilient_services()
    return _global_factory
