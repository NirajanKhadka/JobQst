"""
Real-time monitoring components for the AutoJobAgent Dashboard.

This module provides real-time monitoring components that integrate with
WebSocket connections to provide live updates of pipeline status, metrics,
and health information.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from src.dashboard.websocket import manager as websocket_manager
from src.pipeline.redis_queue import RedisQueue
from src.core.job_database import get_job_db
from src.health_checks.pipeline_health_monitor import pipeline_health_monitor

logger = logging.getLogger(__name__)


@dataclass
class PipelineMetrics:
    """Data class for pipeline metrics."""
    timestamp: str
    jobs_in_queue: int
    jobs_in_deadletter: int
    total_jobs_processed: int
    jobs_processed_today: int
    success_rate: float
    average_processing_time: float
    active_workers: int
    system_health: str


@dataclass
class SystemStatus:
    """Data class for system status."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    redis_connected: bool
    database_connected: bool
    websocket_connections: int
    overall_status: str


class RealTimeMonitor:
    """
    Real-time monitoring system for pipeline and system metrics.
    
    Features:
    - Live pipeline metrics broadcasting
    - System resource monitoring
    - Health status updates
    - Error and alert notifications
    - Performance trend tracking
    """
    
    def __init__(self, broadcast_interval: int = 5):
        self.broadcast_interval = broadcast_interval
        self.monitoring_active = False
        self.metrics_history = []
        self.status_history = []
        self.last_broadcast_time = None
        
        logger.info(f"Real-time monitor initialized with {broadcast_interval}s interval")
    
    async def start_monitoring(self):
        """Start real-time monitoring and broadcasting."""
        if self.monitoring_active:
            logger.warning("Real-time monitoring is already active")
            return
        
        self.monitoring_active = True
        logger.info("Starting real-time monitoring")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._pipeline_metrics_loop()),
            asyncio.create_task(self._system_status_loop()),
            asyncio.create_task(self._health_status_loop()),
            asyncio.create_task(self._error_monitoring_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in real-time monitoring: {e}")
        finally:
            self.monitoring_active = False
    
    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        logger.info("Real-time monitoring stopped")
    
    async def _pipeline_metrics_loop(self):
        """Monitor and broadcast pipeline metrics."""
        while self.monitoring_active:
            try:
                metrics = await self._collect_pipeline_metrics()
                
                # Store metrics history
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > 100:  # Keep last 100 metrics
                    self.metrics_history = self.metrics_history[-100:]
                
                # Broadcast metrics
                await websocket_manager.broadcast({
                    "type": "pipeline_metrics_update",
                    "metrics": asdict(metrics),
                    "trends": self._calculate_metrics_trends()
                })
                
                await asyncio.sleep(self.broadcast_interval)
                
            except Exception as e:
                logger.error(f"Error in pipeline metrics loop: {e}")
                await asyncio.sleep(self.broadcast_interval)
    
    async def _system_status_loop(self):
        """Monitor and broadcast system status."""
        while self.monitoring_active:
            try:
                status = await self._collect_system_status()
                
                # Store status history
                self.status_history.append(status)
                if len(self.status_history) > 100:  # Keep last 100 status updates
                    self.status_history = self.status_history[-100:]
                
                # Broadcast status
                await websocket_manager.broadcast({
                    "type": "system_status_update",
                    "status": asdict(status),
                    "trends": self._calculate_status_trends()
                })
                
                await asyncio.sleep(self.broadcast_interval * 2)  # Less frequent than metrics
                
            except Exception as e:
                logger.error(f"Error in system status loop: {e}")
                await asyncio.sleep(self.broadcast_interval * 2)
    
    async def _health_status_loop(self):
        """Monitor and broadcast health status."""
        while self.monitoring_active:
            try:
                # Get health status from pipeline health monitor
                if pipeline_health_monitor.monitoring_active:
                    health_summary = pipeline_health_monitor.get_health_summary()
                else:
                    # Perform one-time health check
                    health_status = await pipeline_health_monitor.perform_comprehensive_health_check()
                    health_summary = {
                        "current_status": health_status["overall_status"],
                        "trend": "stable",
                        "last_check_time": health_status["timestamp"]
                    }
                
                # Broadcast health status
                await websocket_manager.broadcast({
                    "type": "health_status_update",
                    "health_summary": health_summary,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(self.broadcast_interval * 6)  # Every 30 seconds if interval is 5
                
            except Exception as e:
                logger.error(f"Error in health status loop: {e}")
                await asyncio.sleep(self.broadcast_interval * 6)
    
    async def _error_monitoring_loop(self):
        """Monitor for errors and critical events."""
        while self.monitoring_active:
            try:
                # Check for recent errors in Redis dead-letter queue
                redis_queue = RedisQueue(queue_name="jobs:main")
                await redis_queue.connect()
                
                deadletter_length = await redis_queue.redis.llen("jobs:main:deadletter")
                
                # If dead-letter queue has grown significantly, broadcast alert
                if deadletter_length > 10:  # Threshold for alert
                    recent_errors = []
                    
                    # Get recent dead-letter items
                    items = await redis_queue.redis.lrange("jobs:main:deadletter", 0, 4)  # Last 5 items
                    for item in items:
                        try:
                            error_data = json.loads(item)
                            recent_errors.append({
                                "job_id": error_data.get("job_id", "Unknown"),
                                "title": error_data.get("title", "Unknown"),
                                "error_reason": error_data.get("error_reason", "Unknown"),
                                "failed_at": error_data.get("failed_at", datetime.now().isoformat())
                            })
                        except json.JSONDecodeError:
                            continue
                    
                    # Broadcast error alert
                    await websocket_manager.broadcast({
                        "type": "error_alert",
                        "alert": {
                            "severity": "warning",
                            "message": f"Dead-letter queue has {deadletter_length} failed jobs",
                            "recent_errors": recent_errors,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                
                await redis_queue.close()
                await asyncio.sleep(self.broadcast_interval * 4)  # Every 20 seconds if interval is 5
                
            except Exception as e:
                logger.error(f"Error in error monitoring loop: {e}")
                await asyncio.sleep(self.broadcast_interval * 4)
    
    async def _collect_pipeline_metrics(self) -> PipelineMetrics:
        """Collect current pipeline metrics."""
        try:
            # Get Redis queue metrics
            redis_queue = RedisQueue(queue_name="jobs:main")
            await redis_queue.connect()
            
            jobs_in_queue = await redis_queue.redis.llen("jobs:main")
            jobs_in_deadletter = await redis_queue.redis.llen("jobs:main:deadletter")
            
            await redis_queue.close()
            
            # Get database metrics
            db = get_job_db()
            total_jobs = db.get_job_count()
            job_stats = db.get_job_stats()
            
            # Calculate jobs processed today
            today = datetime.now().date()
            jobs_today = len([
                job for job in db.get_jobs(limit=1000) 
                if job.get("created_at", "").startswith(str(today))
            ])
            
            # Calculate success rate
            total_processed = total_jobs
            failed_jobs = jobs_in_deadletter
            success_rate = ((total_processed - failed_jobs) / total_processed * 100) if total_processed > 0 else 100
            
            # Get system health
            if pipeline_health_monitor.monitoring_active:
                health_summary = pipeline_health_monitor.get_health_summary()
                system_health = health_summary.get("current_status", "unknown")
            else:
                system_health = "unknown"
            
            return PipelineMetrics(
                timestamp=datetime.now().isoformat(),
                jobs_in_queue=jobs_in_queue,
                jobs_in_deadletter=jobs_in_deadletter,
                total_jobs_processed=total_jobs,
                jobs_processed_today=jobs_today,
                success_rate=round(success_rate, 2),
                average_processing_time=0.0,  # Would need to track this separately
                active_workers=0,  # Would need worker monitoring
                system_health=system_health
            )
            
        except Exception as e:
            logger.error(f"Error collecting pipeline metrics: {e}")
            return PipelineMetrics(
                timestamp=datetime.now().isoformat(),
                jobs_in_queue=0,
                jobs_in_deadletter=0,
                total_jobs_processed=0,
                jobs_processed_today=0,
                success_rate=0.0,
                average_processing_time=0.0,
                active_workers=0,
                system_health="error"
            )
    
    async def _collect_system_status(self) -> SystemStatus:
        """Collect current system status."""
        try:
            import psutil
            
            # Get system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            # Test Redis connection
            redis_connected = True
            try:
                redis_queue = RedisQueue(queue_name="jobs:main")
                await redis_queue.connect()
                await redis_queue.close()
            except:
                redis_connected = False
            
            # Test database connection
            database_connected = True
            try:
                db = get_job_db()
                db.get_job_count()
            except:
                database_connected = False
            
            # Get WebSocket connections
            websocket_connections = len(websocket_manager.active_connections)
            
            # Determine overall status
            if not redis_connected or not database_connected:
                overall_status = "critical"
            elif cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
                overall_status = "critical"
            elif cpu_percent > 75 or memory_percent > 75 or disk_percent > 85:
                overall_status = "degraded"
            else:
                overall_status = "healthy"
            
            return SystemStatus(
                timestamp=datetime.now().isoformat(),
                cpu_percent=round(cpu_percent, 1),
                memory_percent=round(memory_percent, 1),
                disk_percent=round(disk_percent, 1),
                redis_connected=redis_connected,
                database_connected=database_connected,
                websocket_connections=websocket_connections,
                overall_status=overall_status
            )
            
        except Exception as e:
            logger.error(f"Error collecting system status: {e}")
            return SystemStatus(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                redis_connected=False,
                database_connected=False,
                websocket_connections=0,
                overall_status="error"
            )
    
    def _calculate_metrics_trends(self) -> Dict[str, Any]:
        """Calculate trends from metrics history."""
        if len(self.metrics_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent = self.metrics_history[-5:]  # Last 5 metrics
        
        # Calculate trends
        queue_trend = self._calculate_trend([m.jobs_in_queue for m in recent])
        success_rate_trend = self._calculate_trend([m.success_rate for m in recent])
        
        return {
            "queue_length_trend": queue_trend,
            "success_rate_trend": success_rate_trend,
            "data_points": len(recent),
            "time_span_minutes": len(recent) * (self.broadcast_interval / 60)
        }
    
    def _calculate_status_trends(self) -> Dict[str, Any]:
        """Calculate trends from status history."""
        if len(self.status_history) < 2:
            return {"trend": "insufficient_data"}
        
        recent = self.status_history[-5:]  # Last 5 status updates
        
        # Calculate trends
        cpu_trend = self._calculate_trend([s.cpu_percent for s in recent])
        memory_trend = self._calculate_trend([s.memory_percent for s in recent])
        
        return {
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "data_points": len(recent),
            "time_span_minutes": len(recent) * (self.broadcast_interval * 2 / 60)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_percent = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        if diff_percent > 10:
            return "increasing"
        elif diff_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Get the most recent metrics."""
        if not self.metrics_history:
            return None
        
        return {
            "metrics": asdict(self.metrics_history[-1]),
            "trends": self._calculate_metrics_trends()
        }
    
    def get_current_status(self) -> Optional[Dict[str, Any]]:
        """Get the most recent system status."""
        if not self.status_history:
            return None
        
        return {
            "status": asdict(self.status_history[-1]),
            "trends": self._calculate_status_trends()
        }
    
    def get_metrics_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get metrics history."""
        history = self.metrics_history[-limit:] if self.metrics_history else []
        return [asdict(metrics) for metrics in history]
    
    def get_status_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get status history."""
        history = self.status_history[-limit:] if self.status_history else []
        return [asdict(status) for status in history]


# Global real-time monitor instance
real_time_monitor = RealTimeMonitor()