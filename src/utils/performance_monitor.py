"""
Performance Monitoring System for AutoJobAgent

This module provides comprehensive performance monitoring, metrics collection,
and performance analysis for the job automation system.
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not available. Metrics will be logged only.")

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Data class for storing performance metrics."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_threads: int
    active_processes: int
    job_scraping_rate: float  # jobs per minute
    application_success_rate: float  # percentage
    average_response_time: float  # milliseconds
    error_rate: float  # percentage
    queue_size: int
    worker_count: int


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.

    Tracks system resources, application metrics, and provides
    real-time performance analysis and alerting.
    """

    def __init__(
        self,
        metrics_file: str = "performance_metrics.json",
        prometheus_port: int = 8000,
        enable_prometheus: bool = True,
    ):
        """
        Initialize the performance monitor.

        Args:
            metrics_file: File to store historical metrics
            prometheus_port: Port for Prometheus metrics endpoint
            enable_prometheus: Whether to enable Prometheus metrics
        """
        self.metrics_file = Path(metrics_file)
        self.prometheus_port = prometheus_port
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE

        # Historical metrics storage
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 10000  # Keep last 10k metrics

        # Performance counters
        self.jobs_scraped = 0
        self.applications_submitted = 0
        self.applications_successful = 0
        self.errors_occurred = 0
        self.start_time = time.time()

        # Threading
        self.monitoring_thread = None
        self.stop_monitoring = False
        self.monitoring_interval = 30  # seconds

        # Initialize Prometheus metrics if available
        if self.enable_prometheus:
            self._init_prometheus_metrics()
            try:
                start_http_server(self.prometheus_port)
                logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")
                self.enable_prometheus = False

        # Load historical metrics
        self._load_metrics()

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        # System metrics
        self.prometheus_metrics = {
            "cpu_percent": Gauge("autojob_cpu_percent", "CPU usage percentage"),
            "memory_percent": Gauge("autojob_memory_percent", "Memory usage percentage"),
            "memory_used_mb": Gauge("autojob_memory_used_mb", "Memory used in MB"),
            "disk_usage_percent": Gauge("autojob_disk_usage_percent", "Disk usage percentage"),
            "active_threads": Gauge("autojob_active_threads", "Number of active threads"),
            "active_processes": Gauge("autojob_active_processes", "Number of active processes"),
            # Application metrics
            "jobs_scraped_total": Counter("autojob_jobs_scraped_total", "Total jobs scraped"),
            "applications_submitted_total": Counter(
                "autojob_applications_submitted_total", "Total applications submitted"
            ),
            "applications_successful_total": Counter(
                "autojob_applications_successful_total", "Total successful applications"
            ),
            "errors_total": Counter("autojob_errors_total", "Total errors occurred"),
            # Performance metrics
            "job_scraping_rate": Gauge(
                "autojob_scraping_rate_jobs_per_minute", "Job scraping rate"
            ),
            "application_success_rate": Gauge(
                "autojob_application_success_rate_percent", "Application success rate"
            ),
            "average_response_time": Gauge(
                "autojob_average_response_time_ms", "Average response time"
            ),
            "error_rate": Gauge("autojob_error_rate_percent", "Error rate"),
            "queue_size": Gauge("autojob_queue_size", "Current queue size"),
            "worker_count": Gauge("autojob_worker_count", "Number of active workers"),
            # Network metrics
            "network_bytes_sent": Counter("autojob_network_bytes_sent", "Network bytes sent"),
            "network_bytes_recv": Counter("autojob_network_bytes_recv", "Network bytes received"),
        }

    def start_monitoring(self):
        """Start continuous performance monitoring."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Performance monitoring is already running")
            return

        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop continuous performance monitoring."""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Performance monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self.stop_monitoring:
            try:
                metrics = self.collect_metrics()
                self.record_metrics(metrics)
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def collect_metrics(self) -> PerformanceMetrics:
        """Collect current system and application metrics."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            network = psutil.net_io_counters()

            # Application metrics
            current_time = time.time()
            elapsed_minutes = (current_time - self.start_time) / 60

            job_scraping_rate = self.jobs_scraped / max(elapsed_minutes, 1)
            application_success_rate = (
                (self.applications_successful / max(self.applications_submitted, 1)) * 100
                if self.applications_submitted > 0
                else 0
            )
            error_rate = (
                (self.errors_occurred / max(self.jobs_scraped + self.applications_submitted, 1))
                * 100
                if (self.jobs_scraped + self.applications_submitted) > 0
                else 0
            )

            # Calculate average response time from recent metrics
            recent_metrics = self.metrics_history[-10:] if self.metrics_history else []
            average_response_time = (
                sum(m.average_response_time for m in recent_metrics) / len(recent_metrics)
                if recent_metrics
                else 0
            )

            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                disk_usage_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_threads=threading.active_count(),
                active_processes=len(psutil.pids()),
                job_scraping_rate=job_scraping_rate,
                application_success_rate=application_success_rate,
                average_response_time=average_response_time,
                error_rate=error_rate,
                queue_size=self._get_queue_size(),
                worker_count=self._get_worker_count(),
            )

            # Update Prometheus metrics
            if self.enable_prometheus:
                self._update_prometheus_metrics(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            # Return default metrics on error
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                active_threads=0,
                active_processes=0,
                job_scraping_rate=0.0,
                application_success_rate=0.0,
                average_response_time=0.0,
                error_rate=0.0,
                queue_size=0,
                worker_count=0,
            )

    def _update_prometheus_metrics(self, metrics: PerformanceMetrics):
        """Update Prometheus metrics."""
        if not self.enable_prometheus:
            return

        try:
            # System metrics
            self.prometheus_metrics["cpu_percent"].set(metrics.cpu_percent)
            self.prometheus_metrics["memory_percent"].set(metrics.memory_percent)
            self.prometheus_metrics["memory_used_mb"].set(metrics.memory_used_mb)
            self.prometheus_metrics["disk_usage_percent"].set(metrics.disk_usage_percent)
            self.prometheus_metrics["active_threads"].set(metrics.active_threads)
            self.prometheus_metrics["active_processes"].set(metrics.active_processes)

            # Application metrics
            self.prometheus_metrics["job_scraping_rate"].set(metrics.job_scraping_rate)
            self.prometheus_metrics["application_success_rate"].set(
                metrics.application_success_rate
            )
            self.prometheus_metrics["average_response_time"].set(metrics.average_response_time)
            self.prometheus_metrics["error_rate"].set(metrics.error_rate)
            self.prometheus_metrics["queue_size"].set(metrics.queue_size)
            self.prometheus_metrics["worker_count"].set(metrics.worker_count)

            # Network metrics
            self.prometheus_metrics["network_bytes_sent"].inc(metrics.network_bytes_sent)
            self.prometheus_metrics["network_bytes_recv"].inc(metrics.network_bytes_recv)

        except Exception as e:
            logger.error(f"Error updating Prometheus metrics: {e}")

    def _get_queue_size(self) -> int:
        """Get current queue size from Celery."""
        try:
            from src.core.celery_app import celery_app

            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            if stats:
                return sum(len(worker.get("pool", {}).get("size", 0)) for worker in stats.values())
            return 0
        except Exception:
            return 0

    def _get_worker_count(self) -> int:
        """Get current worker count from Celery."""
        try:
            from src.core.celery_app import celery_app

            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            return len(stats) if stats else 0
        except Exception:
            return 0

    def record_metrics(self, metrics: PerformanceMetrics):
        """Record metrics to history."""
        self.metrics_history.append(metrics)

        # Limit history size
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size :]

        # Save to file periodically
        if len(self.metrics_history) % 10 == 0:  # Save every 10 metrics
            self._save_metrics()

    def _save_metrics(self):
        """Save metrics to file."""
        try:
            metrics_data = [asdict(m) for m in self.metrics_history]
            # Convert datetime to string for JSON serialization
            for metric in metrics_data:
                metric["timestamp"] = metric["timestamp"].isoformat()

            with open(self.metrics_file, "w") as f:
                json.dump(metrics_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def _load_metrics(self):
        """Load metrics from file."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, "r") as f:
                    metrics_data = json.load(f)

                for metric_data in metrics_data:
                    # Convert string back to datetime
                    metric_data["timestamp"] = datetime.fromisoformat(metric_data["timestamp"])
                    self.metrics_history.append(PerformanceMetrics(**metric_data))

                logger.info(f"Loaded {len(self.metrics_history)} historical metrics")
        except Exception as e:
            logger.error(f"Error loading metrics: {e}")

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {"error": "No metrics available for the specified time period"}

        return {
            "period_hours": hours,
            "metrics_count": len(recent_metrics),
            "average_cpu_percent": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            "average_memory_percent": sum(m.memory_percent for m in recent_metrics)
            / len(recent_metrics),
            "average_job_scraping_rate": sum(m.job_scraping_rate for m in recent_metrics)
            / len(recent_metrics),
            "average_application_success_rate": sum(
                m.application_success_rate for m in recent_metrics
            )
            / len(recent_metrics),
            "average_error_rate": sum(m.error_rate for m in recent_metrics) / len(recent_metrics),
            "peak_cpu_percent": max(m.cpu_percent for m in recent_metrics),
            "peak_memory_percent": max(m.memory_percent for m in recent_metrics),
            "total_jobs_scraped": self.jobs_scraped,
            "total_applications_submitted": self.applications_submitted,
            "total_applications_successful": self.applications_successful,
            "total_errors": self.errors_occurred,
            "uptime_hours": (time.time() - self.start_time) / 3600,
        }

    def record_job_scraped(self):
        """Record a job scraping event."""
        self.jobs_scraped += 1
        if self.enable_prometheus:
            self.prometheus_metrics["jobs_scraped_total"].inc()

    def record_application_submitted(self, successful: bool = True):
        """Record an application submission event."""
        self.applications_submitted += 1
        if successful:
            self.applications_successful += 1
            if self.enable_prometheus:
                self.prometheus_metrics["applications_successful_total"].inc()

        if self.enable_prometheus:
            self.prometheus_metrics["applications_submitted_total"].inc()

    def record_error(self):
        """Record an error event."""
        self.errors_occurred += 1
        if self.enable_prometheus:
            self.prometheus_metrics["errors_total"].inc()

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts based on thresholds."""
        alerts = []

        if not self.metrics_history:
            return alerts

        latest_metrics = self.metrics_history[-1]

        # CPU usage alert
        if latest_metrics.cpu_percent > 80:
            alerts.append(
                {
                    "type": "high_cpu",
                    "severity": "warning",
                    "message": f"High CPU usage: {latest_metrics.cpu_percent:.1f}%",
                    "value": latest_metrics.cpu_percent,
                    "threshold": 80,
                }
            )

        # Memory usage alert
        if latest_metrics.memory_percent > 85:
            alerts.append(
                {
                    "type": "high_memory",
                    "severity": "warning",
                    "message": f"High memory usage: {latest_metrics.memory_percent:.1f}%",
                    "value": latest_metrics.memory_percent,
                    "threshold": 85,
                }
            )

        # Error rate alert
        if latest_metrics.error_rate > 10:
            alerts.append(
                {
                    "type": "high_error_rate",
                    "severity": "critical",
                    "message": f"High error rate: {latest_metrics.error_rate:.1f}%",
                    "value": latest_metrics.error_rate,
                    "threshold": 10,
                }
            )

        # Low success rate alert
        if latest_metrics.application_success_rate < 50:
            alerts.append(
                {
                    "type": "low_success_rate",
                    "severity": "warning",
                    "message": f"Low application success rate: {latest_metrics.application_success_rate:.1f}%",
                    "value": latest_metrics.application_success_rate,
                    "threshold": 50,
                }
            )

        return alerts


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def start_performance_monitoring():
    """Start global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.start_monitoring()


def stop_performance_monitoring():
    """Stop global performance monitoring."""
    global _performance_monitor
    if _performance_monitor:
        _performance_monitor.stop_monitoring()


# Convenience functions for recording events
def record_job_scraped():
    """Record a job scraping event."""
    monitor = get_performance_monitor()
    monitor.record_job_scraped()


def record_application_submitted(successful: bool = True):
    """Record an application submission event."""
    monitor = get_performance_monitor()
    monitor.record_application_submitted(successful)


def record_error():
    """Record an error event."""
    monitor = get_performance_monitor()
    monitor.record_error()


# Performance decorator for timing functions
def monitor_performance(func_name: str = None):
    """Decorator to monitor function performance."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # Record successful execution
                return result
            except Exception as e:
                # Record error
                record_error()
                raise
            finally:
                # Record execution time
                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                monitor = get_performance_monitor()
                if monitor.metrics_history:
                    monitor.metrics_history[-1].average_response_time = execution_time

        return wrapper

    return decorator


# Main functionality moved to CLI module or tests
# Import and use the functions directly

    try:
        # Simulate some activity
        for i in range(10):
            record_job_scraped()
            record_application_submitted(successful=True)
            time.sleep(5)

        # Get performance summary
        summary = monitor.get_performance_summary(hours=1)
        print("Performance Summary:")
        print(json.dumps(summary, indent=2))

        # Get alerts
        alerts = monitor.get_alerts()
        if alerts:
            print("\nAlerts:")
            for alert in alerts:
                print(f"- {alert['message']}")

    finally:
        monitor.stop_monitoring()
