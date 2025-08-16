"""
Performance Monitoring Module
Provides comprehensive performance tracking and optimization insights.
"""

import time
import threading
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from rich.console import Console

console = Console()

# Try to import psutil, fall back to basic monitoring if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    console.print("[yellow]⚠️ psutil not available, using basic performance monitoring[/yellow]")


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    start_time: float
    end_time: float
    duration: float
    peak_memory_mb: float
    avg_cpu_percent: float
    jobs_processed: int
    jobs_per_second: float
    errors_count: int
    success_rate: float


class PerformanceMonitor:
    """
    Real-time performance monitoring for job automation processes.
    
    Features:
    - Memory usage tracking (with psutil) or basic monitoring
    - CPU utilization monitoring (with psutil) or estimation
    - Job processing rate calculation
    - Error rate tracking
    - Performance recommendations
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory_mb: float = 0.0
        self.cpu_samples: list = []
        self.jobs_processed: int = 0
        self.errors_count: int = 0
        self.monitoring: bool = False
        self.monitor_thread: Optional[threading.Thread] = None
        
    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        self.start_time = time.time()
        self.monitoring = True
        self.peak_memory_mb = 0.0
        self.cpu_samples = []
        self.jobs_processed = 0
        self.errors_count = 0
        
        # Start background monitoring thread only if psutil is available
        if PSUTIL_AVAILABLE:
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            console.print("[cyan]⚡ Improved performance monitoring started[/cyan]")
        else:
            console.print("[cyan]⚡ Basic performance monitoring started[/cyan]")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return performance metrics."""
        self.end_time = time.time()
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        duration = self.end_time - (self.start_time or 0)
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        jobs_per_second = self.jobs_processed / duration if duration > 0 else 0
        success_rate = ((self.jobs_processed - self.errors_count) / self.jobs_processed * 100) if self.jobs_processed > 0 else 0
        
        metrics = {
            "duration": duration,
            "peak_memory_mb": self.peak_memory_mb,
            "avg_cpu_percent": avg_cpu,
            "jobs_processed": self.jobs_processed,
            "jobs_per_second": jobs_per_second,
            "errors_count": self.errors_count,
            "success_rate": success_rate
        }
        
        console.print("[green]✅ Performance monitoring stopped[/green]")
        return metrics
    
    def record_job_processed(self) -> None:
        """Record that a job was processed."""
        self.jobs_processed += 1
    
    def record_error(self) -> None:
        """Record that an error occurred."""
        self.errors_count += 1
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop (only runs if psutil is available)."""
        if not PSUTIL_AVAILABLE:
            return
            
        while self.monitoring:
            try:
                # Monitor memory usage
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
                
                # Monitor CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_samples.append(cpu_percent)
                
                # Keep only recent samples to avoid memory growth
                if len(self.cpu_samples) > 60:  # Keep last 60 samples
                    self.cpu_samples = self.cpu_samples[-30:]
                
                time.sleep(1)
                
            except Exception as e:
                console.print(f"[yellow]⚠️ Monitoring error: {e}[/yellow]")
                time.sleep(5)  # Wait longer on error
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        if not self.start_time:
            return {}
        
        current_time = time.time()
        duration = current_time - self.start_time
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        jobs_per_second = self.jobs_processed / duration if duration > 0 else 0
        
        # Basic memory estimation if psutil not available
        if not PSUTIL_AVAILABLE and self.peak_memory_mb == 0:
            self.peak_memory_mb = 50.0  # Estimate 50MB baseline
        
        return {
            "running_time": duration,
            "current_memory_mb": self.peak_memory_mb,
            "avg_cpu_percent": avg_cpu,
            "jobs_processed": self.jobs_processed,
            "current_rate": jobs_per_second,
            "errors": self.errors_count
        }
    
    def get_performance_recommendations(self, metrics: Dict[str, Any]) -> list:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Memory recommendations
        if metrics.get("peak_memory_mb", 0) > 1000:  # > 1GB
            recommendations.append("🧠 High memory usage detected. Consider reducing batch size or worker count.")
        
        # CPU recommendations  
        if metrics.get("avg_cpu_percent", 0) > 80:
            recommendations.append("⚡ High CPU usage. Consider reducing worker count or adding delays.")
        elif metrics.get("avg_cpu_percent", 0) < 30 and PSUTIL_AVAILABLE:
            recommendations.append("🚀 Low CPU usage. You can increase worker count for better performance.")
        
        # Speed recommendations
        jobs_per_second = metrics.get("jobs_per_second", 0)
        if jobs_per_second < 0.5:
            recommendations.append("🐌 Low processing rate. Check network connectivity and optimize scraping logic.")
        elif jobs_per_second > 2.0:
            recommendations.append("⚡ Excellent processing rate! Current configuration is well optimized.")
        
        # Error rate recommendations
        if metrics.get("success_rate", 100) < 90:
            recommendations.append("⚠️ High error rate detected. Check network stability and target site availability.")
        
        # psutil recommendation
        if not PSUTIL_AVAILABLE:
            recommendations.append("📦 Install psutil for Improved performance monitoring: pip install psutil")
        
        return recommendations
