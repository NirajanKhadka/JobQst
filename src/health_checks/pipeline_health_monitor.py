"""
Pipeline Health Monitor Module
Provides comprehensive health monitoring for the job scraper pipeline.
"""

import asyncio
import logging
import uuid
import json
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.pipeline.redis_queue import RedisQueue
from src.core.job_database import get_job_db
from src.dashboard.websocket import manager as websocket_manager

logger = logging.getLogger(__name__)


class PipelineHealthMonitor:
    """
    Comprehensive health monitoring for the job scraper pipeline.
    
    Features:
    - Redis connectivity and queue monitoring
    - Database health and performance checks
    - System resource monitoring
    - Pipeline stage performance tracking
    - Alerting for critical failures
    - Real-time health status broadcasting
    """
    
    def __init__(self, alert_thresholds: Optional[Dict[str, Any]] = None):
        self.monitor_id = str(uuid.uuid4())
        self.alert_thresholds = alert_thresholds or self._get_default_thresholds()
        self.health_history = []
        self.last_alert_times = {}
        self.monitoring_active = False
        
        logger.info(f"[{self.monitor_id}] Pipeline health monitor initialized")
    
    def _get_default_thresholds(self) -> Dict[str, Any]:
        """Get default alert thresholds."""
        return {
            "cpu_percent": 85.0,
            "memory_percent": 90.0,
            "disk_percent": 95.0,
            "redis_queue_length": 1000,
            "deadletter_queue_length": 50,
            "database_response_time": 5.0,  # seconds
            "redis_response_time": 2.0,  # seconds
            "alert_cooldown_minutes": 15
        }
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """
        Start continuous health monitoring.
        
        Args:
            interval_seconds: Monitoring interval in seconds
        """
        self.monitoring_active = True
        logger.info(f"[{self.monitor_id}] Starting continuous health monitoring (interval: {interval_seconds}s)")
        
        while self.monitoring_active:
            try:
                health_status = await self.perform_comprehensive_health_check()
                
                # Store health history
                self.health_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "status": health_status
                })
                
                # Keep only last 100 health checks
                if len(self.health_history) > 100:
                    self.health_history = self.health_history[-100:]
                
                # Check for alerts
                await self._check_and_send_alerts(health_status)
                
                # Broadcast health status via WebSocket
                await self._broadcast_health_status(health_status)
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"[{self.monitor_id}] Error in health monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop continuous health monitoring."""
        self.monitoring_active = False
        logger.info(f"[{self.monitor_id}] Health monitoring stopped")
    
    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all pipeline components.
        
        Returns:
            Dictionary containing detailed health status
        """
        check_id = str(uuid.uuid4())
        check_start_time = datetime.now()
        
        logger.debug(f"[{check_id}] Starting comprehensive health check")
        
        health_status = {
            "check_id": check_id,
            "timestamp": check_start_time.isoformat(),
            "overall_status": "healthy",
            "components": {},
            "alerts": [],
            "performance_metrics": {},
            "system_info": {}
        }
        
        # Check Redis health
        redis_health = await self._check_redis_health()
        health_status["components"]["redis"] = redis_health
        
        # Check Database health
        db_health = await self._check_database_health()
        health_status["components"]["database"] = db_health
        
        # Check System resources
        system_health = await self._check_system_resources()
        health_status["components"]["system"] = system_health
        health_status["system_info"] = system_health.get("details", {})
        
        # Check WebSocket connections
        websocket_health = self._check_websocket_health()
        health_status["components"]["websocket"] = websocket_health
        
        # Check Pipeline queues
        pipeline_health = await self._check_pipeline_queues()
        health_status["components"]["pipeline"] = pipeline_health
        
        # Calculate overall status
        component_statuses = [comp.get("status", "unknown") for comp in health_status["components"].values()]
        critical_count = component_statuses.count("critical")
        degraded_count = component_statuses.count("degraded")
        
        if critical_count > 0:
            health_status["overall_status"] = "critical"
        elif degraded_count > 1:
            health_status["overall_status"] = "critical"
        elif degraded_count > 0:
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "healthy"
        
        # Calculate performance metrics
        check_duration = (datetime.now() - check_start_time).total_seconds()
        health_status["performance_metrics"] = {
            "health_check_duration_seconds": check_duration,
            "components_checked": len(health_status["components"]),
            "critical_components": critical_count,
            "degraded_components": degraded_count
        }
        
        logger.debug(f"[{check_id}] Health check completed in {check_duration:.2f}s - Status: {health_status['overall_status']}")
        
        return health_status
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        start_time = datetime.now()
        
        try:
            redis_queue = RedisQueue(queue_name="jobs:main")
            await redis_queue.connect()
            
            # Test basic operations
            test_key = f"health_check_{self.monitor_id}"
            await redis_queue.redis.set(test_key, "test_value", ex=60)
            test_value = await redis_queue.redis.get(test_key)
            await redis_queue.redis.delete(test_key)
            
            # Get Redis info
            redis_info = await redis_queue.redis.info()
            
            # Get queue lengths
            main_queue_length = await redis_queue.redis.llen("jobs:main")
            deadletter_length = await redis_queue.redis.llen("jobs:main:deadletter")
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            await redis_queue.close()
            
            # Determine status
            status = "healthy"
            if response_time > self.alert_thresholds["redis_response_time"]:
                status = "degraded"
            if main_queue_length > self.alert_thresholds["redis_queue_length"]:
                status = "degraded"
            if deadletter_length > self.alert_thresholds["deadletter_queue_length"]:
                status = "critical"
            
            return {
                "status": status,
                "response_time_seconds": response_time,
                "connected": True,
                "queue_lengths": {
                    "main_queue": main_queue_length,
                    "deadletter_queue": deadletter_length
                },
                "redis_info": {
                    "version": redis_info.get("redis_version", "Unknown"),
                    "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory": redis_info.get("used_memory_human", "Unknown")
                },
                "test_operations": {
                    "set_get_delete": test_value == "test_value"
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "connected": False,
                "error": str(e),
                "response_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        start_time = datetime.now()
        
        try:
            db = get_job_db()
            
            # Test basic operations
            job_count = db.get_job_count()
            job_stats = db.get_job_stats()
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Determine status
            status = "healthy"
            if response_time > self.alert_thresholds["database_response_time"]:
                status = "degraded"
            
            return {
                "status": status,
                "response_time_seconds": response_time,
                "connected": True,
                "job_count": job_count,
                "job_stats": job_stats,
                "database_path": str(db.db_path),
                "connection_pool_size": 5  # From ModernJobDatabase
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "connected": False,
                "error": str(e),
                "response_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Determine status
            status = "healthy"
            if (cpu_percent > self.alert_thresholds["cpu_percent"] or 
                memory_percent > self.alert_thresholds["memory_percent"] or
                disk_percent > self.alert_thresholds["disk_percent"]):
                status = "critical"
            elif (cpu_percent > self.alert_thresholds["cpu_percent"] * 0.8 or
                  memory_percent > self.alert_thresholds["memory_percent"] * 0.8 or
                  disk_percent > self.alert_thresholds["disk_percent"] * 0.8):
                status = "degraded"
            
            return {
                "status": status,
                "details": {
                    "cpu": {
                        "percent_used": round(cpu_percent, 1),
                        "cores": cpu_count
                    },
                    "memory": {
                        "percent_used": round(memory_percent, 1),
                        "available_gb": round(memory_available_gb, 1),
                        "total_gb": round(memory_total_gb, 1)
                    },
                    "disk": {
                        "percent_used": round(disk_percent, 1),
                        "free_gb": round(disk_free_gb, 1),
                        "total_gb": round(disk_total_gb, 1)
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e),
                "details": {}
            }
    
    def _check_websocket_health(self) -> Dict[str, Any]:
        """Check WebSocket connection health."""
        try:
            connection_stats = websocket_manager.get_connection_stats()
            active_connections = connection_stats["active_connections"]
            
            status = "healthy"
            # WebSocket health is generally good if the manager is responsive
            
            return {
                "status": status,
                "active_connections": active_connections,
                "total_messages_sent": connection_stats["total_messages_sent"],
                "average_messages_per_connection": connection_stats["average_messages_per_connection"]
            }
            
        except Exception as e:
            return {
                "status": "degraded",
                "error": str(e),
                "active_connections": 0
            }
    
    async def _check_pipeline_queues(self) -> Dict[str, Any]:
        """Check pipeline queue health and performance."""
        try:
            redis_queue = RedisQueue(queue_name="jobs:main")
            await redis_queue.connect()
            
            # Get queue metrics
            main_queue_length = await redis_queue.redis.llen("jobs:main")
            deadletter_length = await redis_queue.redis.llen("jobs:main:deadletter")
            
            await redis_queue.close()
            
            # Determine status based on queue lengths
            status = "healthy"
            if deadletter_length > self.alert_thresholds["deadletter_queue_length"]:
                status = "critical"
            elif main_queue_length > self.alert_thresholds["redis_queue_length"]:
                status = "degraded"
            
            return {
                "status": status,
                "queue_metrics": {
                    "main_queue_length": main_queue_length,
                    "deadletter_queue_length": deadletter_length,
                    "total_queued_jobs": main_queue_length + deadletter_length
                },
                "thresholds": {
                    "main_queue_warning": self.alert_thresholds["redis_queue_length"],
                    "deadletter_critical": self.alert_thresholds["deadletter_queue_length"]
                }
            }
            
        except Exception as e:
            return {
                "status": "critical",
                "error": str(e),
                "queue_metrics": {}
            }
    
    async def _check_and_send_alerts(self, health_status: Dict[str, Any]):
        """Check health status and send alerts if necessary."""
        current_time = datetime.now()
        alerts_sent = []
        
        # Check overall status
        if health_status["overall_status"] in ["critical", "degraded"]:
            alert_key = f"overall_status_{health_status['overall_status']}"
            
            if self._should_send_alert(alert_key, current_time):
                alert = {
                    "type": "system_health",
                    "severity": health_status["overall_status"],
                    "message": f"System health is {health_status['overall_status']}",
                    "timestamp": current_time.isoformat(),
                    "details": health_status["components"]
                }
                
                await self._send_alert(alert)
                alerts_sent.append(alert)
                self.last_alert_times[alert_key] = current_time
        
        # Check individual components
        for component_name, component_data in health_status["components"].items():
            if component_data.get("status") == "critical":
                alert_key = f"component_{component_name}_critical"
                
                if self._should_send_alert(alert_key, current_time):
                    alert = {
                        "type": "component_failure",
                        "severity": "critical",
                        "component": component_name,
                        "message": f"Component {component_name} is in critical state",
                        "timestamp": current_time.isoformat(),
                        "details": component_data
                    }
                    
                    await self._send_alert(alert)
                    alerts_sent.append(alert)
                    self.last_alert_times[alert_key] = current_time
        
        health_status["alerts"] = alerts_sent
    
    def _should_send_alert(self, alert_key: str, current_time: datetime) -> bool:
        """Check if an alert should be sent based on cooldown period."""
        if alert_key not in self.last_alert_times:
            return True
        
        last_alert_time = self.last_alert_times[alert_key]
        cooldown_minutes = self.alert_thresholds["alert_cooldown_minutes"]
        
        return (current_time - last_alert_time) > timedelta(minutes=cooldown_minutes)
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Send alert via available channels."""
        try:
            # Log the alert
            logger.warning(f"[{self.monitor_id}] ALERT: {alert['message']}")
            
            # Broadcast via WebSocket
            await websocket_manager.broadcast({
                "type": "health_alert",
                "alert": alert
            })
            
            # Could add additional alert channels here (email, Slack, etc.)
            
        except Exception as e:
            logger.error(f"[{self.monitor_id}] Failed to send alert: {e}")
    
    async def _broadcast_health_status(self, health_status: Dict[str, Any]):
        """Broadcast health status via WebSocket."""
        try:
            await websocket_manager.broadcast({
                "type": "health_status_update",
                "health_status": health_status
            })
        except Exception as e:
            logger.debug(f"[{self.monitor_id}] Failed to broadcast health status: {e}")
    
    def get_health_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent health check history."""
        return self.health_history[-limit:] if self.health_history else []
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of recent health status."""
        if not self.health_history:
            return {"status": "no_data", "message": "No health data available"}
        
        recent_checks = self.health_history[-10:]  # Last 10 checks
        
        # Count statuses
        status_counts = {}
        for check in recent_checks:
            status = check["status"]["overall_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Determine trend
        if len(recent_checks) >= 2:
            latest_status = recent_checks[-1]["status"]["overall_status"]
            previous_status = recent_checks[-2]["status"]["overall_status"]
            
            if latest_status == "healthy" and previous_status != "healthy":
                trend = "improving"
            elif latest_status != "healthy" and previous_status == "healthy":
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "unknown"
        
        return {
            "current_status": recent_checks[-1]["status"]["overall_status"],
            "trend": trend,
            "recent_status_counts": status_counts,
            "last_check_time": recent_checks[-1]["timestamp"],
            "checks_performed": len(self.health_history)
        }


# Global health monitor instance
pipeline_health_monitor = PipelineHealthMonitor()