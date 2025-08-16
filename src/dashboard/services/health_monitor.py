#!/usr/bin/env python3
"""
Health monitoring system for comprehensive dashboard health checks.
Provides system-wide health monitoring with automatic recovery capabilities.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys
from enum import Enum

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class ServiceType(Enum):
    """Service type enumeration."""
    DATABASE = "database"
    ORCHESTRATION = "orchestration"
    SYSTEM = "system"
    NETWORK = "network"
    CACHE = "cache"


class HealthMonitor:
    """
    System-wide health monitoring with automatic recovery capabilities.
    Implements comprehensive health checks for all dashboard services.
    """
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize HealthMonitor.
        
        Args:
            check_interval: Health check interval in seconds (default: 60s)
        """
        self.check_interval = check_interval
        self._health_history: List[Dict[str, Any]] = []
        self._max_history = 100
        self._recovery_attempts: Dict[str, int] = {}
        self._max_recovery_attempts = 3
        self._background_monitoring = False
        
    async def check_service_health(self) -> Dict[str, Any]:
        """
        Check health of all services.
        
        Returns:
            Dict containing comprehensive health status
        """
        try:
            health_results = {}
            overall_status = HealthStatus.HEALTHY
            
            # Check all service types
            checks = [
                ("database", self._check_database_health()),
                ("system", self._check_system_health()),
                ("orchestration", self._check_orchestration_health()),
                ("network", self._check_network_health()),
                ("cache", self._check_cache_health())
            ]
            
            # Run all checks concurrently
            for service_name, check_coro in checks:
                try:
                    health_results[service_name] = await check_coro
                    
                    # Update overall status based on individual service health
                    service_status = HealthStatus(health_results[service_name]["status"])
                    if service_status == HealthStatus.UNHEALTHY:
                        overall_status = HealthStatus.UNHEALTHY
                    elif service_status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                        
                except Exception as e:
                    logger.error(f"Health check failed for {service_name}: {e}")
                    health_results[service_name] = {
                        "status": HealthStatus.UNKNOWN.value,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    if overall_status != HealthStatus.UNHEALTHY:
                        overall_status = HealthStatus.DEGRADED
            
            # Create summary
            summary = {
                "overall_status": overall_status.value,
                "services": health_results,
                "timestamp": datetime.now().isoformat(),
                "check_duration": await self._calculate_check_duration(),
                "recovery_status": self._get_recovery_status()
            }
            
            # Store in history
            self._add_to_history(summary)
            
            # Trigger recovery if needed
            await self._trigger_recovery_if_needed(health_results)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in comprehensive health check: {e}")
            return {
                "overall_status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database service health."""
        try:
            # Import services dynamically to avoid circular imports
            from src.dashboard.services.data_service import get_data_service
            data_service = get_data_service()
            
            # Check data service health
            health_status = data_service.get_health_status()
            
            if health_status.get("status") == "healthy":
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "profiles_count": health_status.get("profiles_count", 0),
                    "database_healthy": health_status.get("database_healthy", False),
                    "cache_size": health_status.get("cache_size", 0),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY.value,
                    "error": health_status.get("error", "Database unhealthy"),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system service health."""
        try:
            from src.dashboard.services.system_service import get_system_service
            system_service = get_system_service()
            
            # Get system metrics
            metrics = await system_service.get_system_metrics()
            
            # Determine health based on metrics
            cpu_healthy = metrics.get("cpu_percent", 0) < 80
            memory_healthy = metrics.get("memory_percent", 0) < 80
            disk_healthy = metrics.get("disk_usage", 0) < 90
            
            if cpu_healthy and memory_healthy and disk_healthy:
                status = HealthStatus.HEALTHY
            elif metrics.get("cpu_percent", 0) > 90 or metrics.get("memory_percent", 0) > 90:
                status = HealthStatus.UNHEALTHY
            else:
                status = HealthStatus.DEGRADED
            
            return {
                "status": status.value,
                "cpu_percent": metrics.get("cpu_percent", 0),
                "memory_percent": metrics.get("memory_percent", 0),
                "disk_usage": metrics.get("disk_usage", 0),
                "network_status": metrics.get("network_status", "unknown"),
                "services": metrics.get("services", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_orchestration_health(self) -> Dict[str, Any]:
        """Check orchestration service health."""
        try:
            from src.dashboard.services.orchestration_service import get_orchestration_service
            orchestration_service = get_orchestration_service()
            
            # Get orchestration health
            health = await orchestration_service.get_orchestration_health()
            
            return {
                "status": health.get("overall_status", HealthStatus.UNKNOWN.value),
                "services_healthy": health.get("services_healthy", 0),
                "total_services": health.get("total_services", 0),
                "application_processor": health.get("application_processor", {}),
                "document_generator": health.get("document_generator", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Orchestration health check failed: {e}")
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_network_health(self) -> Dict[str, Any]:
        """Check network connectivity health."""
        try:
            import aiohttp
            
            # Test multiple endpoints for reliability
            endpoints = [
                "https://www.google.com",
                "https://github.com",
                "https://httpbin.org/status/200"
            ]
            
            successful_connections = 0
            connection_times = []
            
            for endpoint in endpoints:
                try:
                    start_time = datetime.now()
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.get(endpoint) as response:
                            if response.status == 200:
                                successful_connections += 1
                                connection_time = (datetime.now() - start_time).total_seconds()
                                connection_times.append(connection_time)
                except Exception:
                    continue
            
            # Determine network health
            success_rate = successful_connections / len(endpoints)
            avg_response_time = sum(connection_times) / len(connection_times) if connection_times else 0
            
            if success_rate >= 0.8 and avg_response_time < 2.0:
                status = HealthStatus.HEALTHY
            elif success_rate >= 0.5:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "successful_connections": successful_connections,
                "total_endpoints": len(endpoints),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Network health check failed: {e}")
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache service health."""
        try:
            # Check all services with caching
            cache_stats = {}
            
            # Check DataService cache
            try:
                from src.dashboard.services.data_service import get_data_service
                data_service = get_data_service()
                cache_stats["data_service"] = {
                    "cache_size": len(data_service._cache),
                    "status": "healthy"
                }
            except Exception as e:
                cache_stats["data_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Check SystemService cache
            try:
                from src.dashboard.services.system_service import get_system_service
                system_service = get_system_service()
                cache_stats["system_service"] = {
                    "cache_size": len(system_service._cache),
                    "status": "healthy"
                }
            except Exception as e:
                cache_stats["system_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Determine overall cache health
            healthy_caches = sum(1 for stats in cache_stats.values() if stats.get("status") == "healthy")
            total_caches = len(cache_stats)
            
            if healthy_caches == total_caches:
                status = HealthStatus.HEALTHY
            elif healthy_caches > 0:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return {
                "status": status.value,
                "healthy_caches": healthy_caches,
                "total_caches": total_caches,
                "cache_details": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def trigger_health_recovery(self, service: str) -> Dict[str, Any]:
        """
        Attempt automatic service recovery.
        
        Args:
            service: Service name to recover
            
        Returns:
            Dict containing recovery result
        """
        try:
            # Check if we've exceeded max recovery attempts
            attempts = self._recovery_attempts.get(service, 0)
            if attempts >= self._max_recovery_attempts:
                return {
                    "success": False,
                    "service": service,
                    "error": f"Max recovery attempts ({self._max_recovery_attempts}) exceeded",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Increment recovery attempts
            self._recovery_attempts[service] = attempts + 1
            
            # Attempt service-specific recovery
            recovery_result = await self._perform_service_recovery(service)
            
            if recovery_result.get("success", False):
                # Reset recovery attempts on success
                self._recovery_attempts[service] = 0
                
            return {
                "success": recovery_result.get("success", False),
                "service": service,
                "recovery_action": recovery_result.get("action", "unknown"),
                "message": recovery_result.get("message", "Recovery attempted"),
                "attempt": attempts + 1,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error recovering service {service}: {e}")
            return {
                "success": False,
                "service": service,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _perform_service_recovery(self, service: str) -> Dict[str, Any]:
        """Perform service-specific recovery actions."""
        try:
            if service == "database":
                # Clear data service cache
                from src.dashboard.services.data_service import get_data_service
                data_service = get_data_service()
                data_service.clear_cache()
                return {"success": True, "action": "cache_cleared", "message": "Database cache cleared"}
                
            elif service == "system":
                # Clear system service cache
                from src.dashboard.services.system_service import get_system_service
                system_service = get_system_service()
                system_service.clear_cache()
                return {"success": True, "action": "cache_cleared", "message": "System cache cleared"}
                
            elif service == "orchestration":
                # Clear orchestration service cache
                from src.dashboard.services.orchestration_service import get_orchestration_service
                orchestration_service = get_orchestration_service()
                orchestration_service.clear_cache()
                return {"success": True, "action": "cache_cleared", "message": "Orchestration cache cleared"}
                
            elif service == "cache":
                # Clear all caches
                await self._clear_all_caches()
                return {"success": True, "action": "all_caches_cleared", "message": "All caches cleared"}
                
            else:
                return {"success": False, "action": "none", "message": f"No recovery action for service: {service}"}
                
        except Exception as e:
            logger.error(f"Recovery action failed for {service}: {e}")
            return {"success": False, "action": "failed", "message": str(e)}
    
    async def _clear_all_caches(self):
        """Clear all service caches."""
        services = [
            ("data_service", "get_data_service"),
            ("system_service", "get_system_service"),
            ("orchestration_service", "get_orchestration_service")
        ]
        
        for service_name, service_func in services:
            try:
                module = __import__(f"src.dashboard.services.{service_name}", fromlist=[service_func])
                service = getattr(module, service_func)()
                if hasattr(service, 'clear_cache'):
                    service.clear_cache()
            except Exception as e:
                logger.warning(f"Could not clear cache for {service_name}: {e}")
    
    async def _trigger_recovery_if_needed(self, health_results: Dict[str, Any]):
        """Trigger recovery for unhealthy services."""
        for service_name, health_data in health_results.items():
            if health_data.get("status") == HealthStatus.UNHEALTHY.value:
                logger.warning(f"Service {service_name} is unhealthy, attempting recovery")
                recovery_result = await self.trigger_health_recovery(service_name)
                logger.info(f"Recovery result for {service_name}: {recovery_result}")
    
    async def _calculate_check_duration(self) -> float:
        """Calculate duration of health checks."""
        # This would track actual check duration
        return 0.5  # Mock duration
    
    def _get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery status."""
        return {
            "active_recoveries": len([k for k, v in self._recovery_attempts.items() if v > 0]),
            "total_attempts": sum(self._recovery_attempts.values()),
            "services_in_recovery": list(self._recovery_attempts.keys())
        }
    
    def _add_to_history(self, health_summary: Dict[str, Any]):
        """Add health check result to history."""
        self._health_history.append(health_summary)
        
        # Trim history if too long
        if len(self._health_history) > self._max_history:
            self._health_history = self._health_history[-self._max_history:]
    
    def get_health_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent health check history."""
        return self._health_history[-limit:]
    
    async def start_background_monitoring(self):
        """Start background health monitoring."""
        if self._background_monitoring:
            logger.warning("Background monitoring already running")
            return
        
        self._background_monitoring = True
        logger.info(f"Starting background health monitoring (interval: {self.check_interval}s)")
        
        try:
            while self._background_monitoring:
                await self.check_service_health()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("Background health monitoring cancelled")
        finally:
            self._background_monitoring = False
    
    def stop_background_monitoring(self):
        """Stop background health monitoring."""
        self._background_monitoring = False
        logger.info("Background health monitoring stopped")


# Global monitor instance
_health_monitor = None

def get_health_monitor() -> HealthMonitor:
    """Get singleton HealthMonitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor
