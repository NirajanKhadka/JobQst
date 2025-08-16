#!/usr/bin/env python3
"""
System Monitor - Handles performance tracking and metrics
Single responsibility: Monitor system resources and service health
Max 300 lines following development standards
"""

import logging
import psutil
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .service_manager import get_service_manager
from .worker_pool_manager import get_worker_pool_manager

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics data class."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    process_count: int
    uptime_seconds: float

@dataclass
class ServiceHealthMetrics:
    """Service health metrics data class."""
    service_name: str
    status: str
    uptime: str
    cpu_usage: float
    memory_usage: float
    processed_count: int
    error_count: int
    last_activity: Optional[datetime]

class SystemMonitor:
    """
    Monitors system performance and service health.
    Follows single responsibility principle - only handles monitoring/metrics.
    """
    
    def __init__(self, history_limit: int = 100):
        """Initialize system monitor."""
        self.history_limit = history_limit
        self.metrics_history: List[SystemMetrics] = []
        self.service_manager = get_service_manager()
        self.worker_pool_manager = get_worker_pool_manager()
        self.start_time = datetime.now()
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system performance metrics."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                network_io={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                },
                process_count=len(psutil.pids()),
                uptime_seconds=(datetime.now() - self.start_time).total_seconds()
            )
            
            # Add to history and maintain limit
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.history_limit:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_usage_percent=0.0,
                network_io={"bytes_sent": 0, "bytes_recv": 0},
                process_count=0,
                uptime_seconds=0.0
            )
    
    def get_service_health_metrics(self) -> List[ServiceHealthMetrics]:
        """Get health metrics for all services."""
        health_metrics = []
        all_services = self.service_manager.get_all_services_status()
        
        for service_name, status_data in all_services.items():
            health_metric = ServiceHealthMetrics(
                service_name=service_name,
                status=status_data.get("status", "unknown"),
                uptime=status_data.get("uptime", "00:00:00"),
                cpu_usage=status_data.get("cpu_usage", 0.0),
                memory_usage=status_data.get("memory_usage", 0.0),
                processed_count=status_data.get("processed_count", 0),
                error_count=status_data.get("error_count", 0),
                last_activity=status_data.get("last_activity")
            )
            health_metrics.append(health_metric)
        
        return health_metrics
    
    def get_worker_pool_health(self) -> Dict[str, Any]:
        """Get worker pool health summary."""
        pool_status = self.worker_pool_manager.get_worker_pool_status()
        performance_metrics = self.worker_pool_manager.get_worker_performance_metrics()
        
        return {
            "pool_status": pool_status,
            "performance": performance_metrics,
            "health_score": self._calculate_pool_health_score(pool_status, performance_metrics)
        }
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        current_metrics = self.collect_system_metrics()
        service_health = self.get_service_health_metrics()
        worker_health = self.get_worker_pool_health()
        
        # Calculate health scores
        system_health_score = self._calculate_system_health_score(current_metrics)
        service_health_score = self._calculate_service_health_score(service_health)
        
        overall_health_score = (system_health_score + service_health_score + worker_health["health_score"]) / 3
        
        return {
            "overall_health_score": overall_health_score,
            "system_health_score": system_health_score,
            "service_health_score": service_health_score,
            "worker_pool_health_score": worker_health["health_score"],
            "system_metrics": current_metrics,
            "service_count": len(service_health),
            "running_services": len([s for s in service_health if s.status == "running"]),
            "alerts": self._generate_health_alerts(current_metrics, service_health)
        }
    
    def get_metrics_history(self, minutes: int = 30) -> List[SystemMetrics]:
        """Get metrics history for the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def _calculate_system_health_score(self, metrics: SystemMetrics) -> float:
        """Calculate system health score (0-100)."""
        # Simple scoring based on resource usage
        cpu_score = max(0, 100 - metrics.cpu_percent)
        memory_score = max(0, 100 - metrics.memory_percent)
        disk_score = max(0, 100 - metrics.disk_usage_percent)
        
        return (cpu_score + memory_score + disk_score) / 3
    
    def _calculate_service_health_score(self, service_health: List[ServiceHealthMetrics]) -> float:
        """Calculate overall service health score (0-100)."""
        if not service_health:
            return 0.0
        
        running_services = len([s for s in service_health if s.status == "running"])
        total_services = len(service_health)
        
        # Base score on running services ratio
        base_score = (running_services / total_services) * 100
        
        # Adjust for error rates
        total_errors = sum(s.error_count for s in service_health)
        total_processed = sum(s.processed_count for s in service_health)
        
        if total_processed > 0:
            error_rate = total_errors / total_processed
            error_penalty = min(error_rate * 50, 30)  # Max 30 point penalty
            base_score -= error_penalty
        
        return max(0, base_score)
    
    def _calculate_pool_health_score(self, pool_status: Dict[str, Any], performance: Dict[str, Any]) -> float:
        """Calculate worker pool health score (0-100)."""
        if pool_status["total_workers"] == 0:
            return 0.0
        
        # Base score on worker availability
        availability_score = (pool_status["running_workers"] / pool_status["total_workers"]) * 100
        
        # Adjust for performance
        efficiency_score = performance.get("efficiency_score", 0.0)
        
        return (availability_score + efficiency_score) / 2
    
    def _generate_health_alerts(self, metrics: SystemMetrics, service_health: List[ServiceHealthMetrics]) -> List[Dict[str, str]]:
        """Generate health alerts based on current metrics."""
        alerts = []
        
        # System resource alerts
        if metrics.cpu_percent > 90:
            alerts.append({"level": "critical", "message": f"High CPU usage: {metrics.cpu_percent:.1f}%"})
        elif metrics.cpu_percent > 75:
            alerts.append({"level": "warning", "message": f"Elevated CPU usage: {metrics.cpu_percent:.1f}%"})
        
        if metrics.memory_percent > 90:
            alerts.append({"level": "critical", "message": f"High memory usage: {metrics.memory_percent:.1f}%"})
        elif metrics.memory_percent > 75:
            alerts.append({"level": "warning", "message": f"Elevated memory usage: {metrics.memory_percent:.1f}%"})
        
        if metrics.disk_usage_percent > 95:
            alerts.append({"level": "critical", "message": f"Disk space critical: {metrics.disk_usage_percent:.1f}%"})
        elif metrics.disk_usage_percent > 85:
            alerts.append({"level": "warning", "message": f"Low disk space: {metrics.disk_usage_percent:.1f}%"})
        
        # Service alerts
        failed_services = [s for s in service_health if s.status == "failed"]
        if failed_services:
            service_names = ", ".join([s.service_name for s in failed_services])
            alerts.append({"level": "critical", "message": f"Failed services: {service_names}"})
        
        return alerts


# Global system monitor instance
_system_monitor = None

def get_system_monitor() -> SystemMonitor:
    """Get global system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor