"""
Performance Monitoring for JobQst Dashboard
Tracks query performance and DuckDB metrics for optimization
"""
import time
import logging
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for database queries"""
    query_type: str
    profile_name: str
    duration_ms: float
    timestamp: str
    row_count: int = 0
    cache_hit: bool = False
    error: str = ""


@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    active_connections: int = 0


class PerformanceMonitor:
    """
    Performance monitoring system for dashboard and database operations
    
    Features:
    - Query performance tracking
    - System resource monitoring  
    - Slow query detection
    - Performance trend analysis
    - Alert thresholds
    """
    
    def __init__(
        self,
        max_metrics_history: int = 10000,
        slow_query_threshold_ms: float = 1000.0,
        memory_alert_threshold: float = 85.0
    ):
        """
        Initialize performance monitor
        
        Args:
            max_metrics_history: Maximum metrics to keep in memory
            slow_query_threshold_ms: Threshold for slow query alerts (ms)
            memory_alert_threshold: Memory usage alert threshold (%)
        """
        self.max_history = max_metrics_history
        self.slow_query_threshold = slow_query_threshold_ms
        self.memory_alert_threshold = memory_alert_threshold
        
        # Metrics storage
        self.query_metrics: deque = deque(maxlen=max_metrics_history)
        self.system_metrics: deque = deque(maxlen=max_metrics_history)
        
        # Performance counters
        self.query_counters = defaultdict(int)
        self.slow_queries = deque(maxlen=100)  # Last 100 slow queries
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Monitoring state
        self._monitoring_active = False
        self._monitor_thread = None
        
        logger.info("Performance monitor initialized")
    
    def start_monitoring(self, interval_seconds: int = 30) -> None:
        """Start continuous system monitoring"""
        if self._monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info(f"System monitoring started (interval: {interval_seconds}s)")
    
    def stop_monitoring(self) -> None:
        """Stop system monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def track_query(
        self,
        query_type: str,
        profile_name: str,
        duration_ms: float,
        row_count: int = 0,
        cache_hit: bool = False,
        error: str = ""
    ) -> None:
        """Track database query performance"""
        with self._lock:
            metrics = QueryMetrics(
                query_type=query_type,
                profile_name=profile_name,
                duration_ms=duration_ms,
                timestamp=datetime.now().isoformat(),
                row_count=row_count,
                cache_hit=cache_hit,
                error=error
            )
            
            self.query_metrics.append(metrics)
            self.query_counters[query_type] += 1
            
            # Track slow queries
            if duration_ms > self.slow_query_threshold:
                self.slow_queries.append(metrics)
                logger.warning(
                    f"Slow query detected: {query_type} took {duration_ms:.1f}ms"
                )
    
    def get_performance_summary(
        self, hours_back: int = 24
    ) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self._lock:
            cutoff = datetime.now() - timedelta(hours=hours_back)
            
            # Filter recent metrics
            recent_queries = [
                q for q in self.query_metrics
                if datetime.fromisoformat(q.timestamp) > cutoff
            ]
            
            recent_system = [
                s for s in self.system_metrics
                if datetime.fromisoformat(s.timestamp) > cutoff
            ]
            
            # Query statistics
            query_stats = self._analyze_queries(recent_queries)
            
            # System statistics
            system_stats = self._analyze_system_metrics(recent_system)
            
            # Cache performance
            cache_stats = self._analyze_cache_performance(recent_queries)
            
            return {
                'time_window_hours': hours_back,
                'query_stats': query_stats,
                'system_stats': system_stats,
                'cache_stats': cache_stats,
                'slow_queries_count': len([
                    q for q in recent_queries
                    if q.duration_ms > self.slow_query_threshold
                ]),
                'total_queries': len(recent_queries),
                'alerts': self._generate_alerts(recent_queries, recent_system)
            }
    
    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent slow queries for analysis"""
        with self._lock:
            return [
                asdict(q) for q in list(self.slow_queries)[-limit:]
            ]
    
    def get_query_trends(
        self, query_type: str = None, hours_back: int = 24
    ) -> Dict[str, Any]:
        """Get query performance trends over time"""
        with self._lock:
            cutoff = datetime.now() - timedelta(hours=hours_back)
            
            # Filter queries
            queries = [
                q for q in self.query_metrics
                if datetime.fromisoformat(q.timestamp) > cutoff
            ]
            
            if query_type:
                queries = [q for q in queries if q.query_type == query_type]
            
            if not queries:
                return {'error': 'No queries found for the specified criteria'}
            
            # Group by hour
            hourly_stats = defaultdict(list)
            for query in queries:
                hour_key = datetime.fromisoformat(query.timestamp).strftime('%Y-%m-%d %H:00')
                hourly_stats[hour_key].append(query.duration_ms)
            
            # Calculate hourly averages
            trend_data = {}
            for hour, durations in hourly_stats.items():
                trend_data[hour] = {
                    'avg_duration_ms': statistics.mean(durations),
                    'max_duration_ms': max(durations),
                    'query_count': len(durations),
                    'p95_duration_ms': statistics.quantiles(durations, n=20)[18] if len(durations) > 5 else max(durations)
                }
            
            return {
                'query_type': query_type or 'all',
                'time_window_hours': hours_back,
                'trend_data': trend_data,
                'total_queries': len(queries)
            }
    
    def get_current_system_status(self) -> Dict[str, Any]:
        """Get current system performance status"""
        try:
            # Current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            
            # Database connection info (if available)
            db_connections = self._get_db_connection_count()
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_io_read_mb_per_sec': getattr(disk_io, 'read_bytes', 0) / (1024**2),
                'disk_io_write_mb_per_sec': getattr(disk_io, 'write_bytes', 0) / (1024**2),
                'db_connections': db_connections,
                'status': 'healthy'
            }
            
            # Add status warnings
            if cpu_percent > 90:
                status['status'] = 'cpu_high'
            elif memory.percent > self.memory_alert_threshold:
                status['status'] = 'memory_high'
            elif db_connections > 20:
                status['status'] = 'connections_high'
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'status': 'error'
            }
    
    # ============= PRIVATE METHODS =============
    
    def _monitor_loop(self, interval_seconds: int) -> None:
        """Background monitoring loop"""
        while self._monitoring_active:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                
                metrics = SystemMetrics(
                    timestamp=datetime.now().isoformat(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_io_read_mb=getattr(disk_io, 'read_bytes', 0) / (1024**2),
                    disk_io_write_mb=getattr(disk_io, 'write_bytes', 0) / (1024**2),
                    active_connections=self._get_db_connection_count()
                )
                
                with self._lock:
                    self.system_metrics.append(metrics)
                
                # Sleep until next interval
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval_seconds)
    
    def _analyze_queries(self, queries: List[QueryMetrics]) -> Dict[str, Any]:
        """Analyze query performance metrics"""
        if not queries:
            return {'total_queries': 0}
        
        durations = [q.duration_ms for q in queries]
        
        # Group by query type
        by_type = defaultdict(list)
        for query in queries:
            by_type[query.query_type].append(query.duration_ms)
        
        type_stats = {}
        for qtype, type_durations in by_type.items():
            type_stats[qtype] = {
                'count': len(type_durations),
                'avg_duration_ms': statistics.mean(type_durations),
                'max_duration_ms': max(type_durations),
                'min_duration_ms': min(type_durations)
            }
        
        return {
            'total_queries': len(queries),
            'avg_duration_ms': statistics.mean(durations),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations),
            'p95_duration_ms': statistics.quantiles(durations, n=20)[18] if len(durations) > 5 else max(durations),
            'by_type': type_stats
        }
    
    def _analyze_system_metrics(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Analyze system performance metrics"""
        if not metrics:
            return {'no_data': True}
        
        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_percent for m in metrics]
        
        return {
            'avg_cpu_percent': statistics.mean(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'avg_memory_percent': statistics.mean(memory_values),
            'max_memory_percent': max(memory_values),
            'samples_count': len(metrics)
        }
    
    def _analyze_cache_performance(self, queries: List[QueryMetrics]) -> Dict[str, Any]:
        """Analyze cache hit rates"""
        if not queries:
            return {'no_data': True}
        
        cache_hits = sum(1 for q in queries if q.cache_hit)
        total_cacheable = len([q for q in queries if hasattr(q, 'cache_hit')])
        
        hit_rate = (cache_hits / total_cacheable * 100) if total_cacheable > 0 else 0
        
        return {
            'cache_hits': cache_hits,
            'total_queries': len(queries),
            'hit_rate_percent': round(hit_rate, 2),
            'cache_enabled': total_cacheable > 0
        }
    
    def _generate_alerts(
        self, queries: List[QueryMetrics], system_metrics: List[SystemMetrics]
    ) -> List[Dict[str, Any]]:
        """Generate performance alerts"""
        alerts = []
        
        # Slow query alerts
        slow_queries = [q for q in queries if q.duration_ms > self.slow_query_threshold]
        if len(slow_queries) > 10:
            alerts.append({
                'type': 'slow_queries',
                'severity': 'warning',
                'message': f'{len(slow_queries)} slow queries detected',
                'details': f'Queries taking over {self.slow_query_threshold}ms'
            })
        
        # Memory alerts
        if system_metrics:
            max_memory = max(m.memory_percent for m in system_metrics)
            if max_memory > self.memory_alert_threshold:
                alerts.append({
                    'type': 'high_memory',
                    'severity': 'warning',
                    'message': f'High memory usage: {max_memory:.1f}%',
                    'details': f'Exceeded threshold of {self.memory_alert_threshold}%'
                })
        
        return alerts
    
    def _get_db_connection_count(self) -> int:
        """Get current database connection count"""
        try:
            # This would need to be implemented based on the specific database
            # For now, return a placeholder
            return 0
        except Exception:
            return 0


# Context manager for query timing
class QueryTimer:
    """Context manager for tracking query performance"""
    
    def __init__(
        self,
        monitor: PerformanceMonitor,
        query_type: str,
        profile_name: str,
        cache_hit: bool = False
    ):
        self.monitor = monitor
        self.query_type = query_type
        self.profile_name = profile_name
        self.cache_hit = cache_hit
        self.start_time = None
        self.row_count = 0
        self.error = ""
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type:
            self.error = str(exc_val)
        
        self.monitor.track_query(
            query_type=self.query_type,
            profile_name=self.profile_name,
            duration_ms=duration_ms,
            row_count=self.row_count,
            cache_hit=self.cache_hit,
            error=self.error
        )
    
    def set_row_count(self, count: int):
        """Set number of rows processed"""
        self.row_count = count


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def track_query_performance(
    query_type: str, profile_name: str, cache_hit: bool = False
) -> QueryTimer:
    """Get query timer context manager"""
    monitor = get_performance_monitor()
    return QueryTimer(monitor, query_type, profile_name, cache_hit)
