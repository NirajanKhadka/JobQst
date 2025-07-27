"""
Optimized Job Batcher for memory-efficient batch processing.

This module provides an optimized job batching system for the scraper pipeline
with advanced features including memory monitoring, configurable batch sizes,
and intelligent batch optimization algorithms.

Features:
- Memory-efficient job batching with monitoring
- Configurable batch sizes based on system resources
- Memory usage tracking and optimization
- Batch optimization algorithms
- Performance metrics and monitoring
- Integration with existing pipeline components
"""

import asyncio
import time
import logging
import psutil
from typing import Dict, List, Optional, Any, Generator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import gc

logger = logging.getLogger(__name__)


@dataclass
class BatchMetrics:
    """Metrics for batch processing performance tracking."""
    total_batches: int = 0
    total_jobs_processed: int = 0
    avg_batch_size: float = 0.0
    avg_batch_time: float = 0.0
    memory_usage_mb: float = 0.0
    peak_memory_mb: float = 0.0
    batch_times: List[float] = field(default_factory=list)
    batch_sizes: List[int] = field(default_factory=list)
    memory_readings: List[float] = field(default_factory=list)
    last_optimization: datetime = field(default_factory=datetime.now)
    optimization_count: int = 0


@dataclass
class BatchConfig:
    """Configuration for job batching."""
    initial_batch_size: int = 20
    min_batch_size: int = 5
    max_batch_size: int = 100
    memory_threshold_mb: float = 1024.0
    memory_safety_margin: float = 0.8
    optimization_interval: int = 60
    batch_timeout: int = 300
    enable_memory_monitoring: bool = True
    enable_auto_optimization: bool = True


class MemoryMonitor:
    """Memory usage monitoring and optimization."""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.process = psutil.Process()
        self.memory_readings = deque(maxlen=100)
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.memory_readings.append(memory_mb)
            return memory_mb
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0.0
            
    def get_memory_percentage(self) -> float:
        """Get memory usage as percentage of available memory."""
        try:
            memory_percent = self.process.memory_percent()
            return memory_percent
        except Exception as e:
            logger.warning(f"Failed to get memory percentage: {e}")
            return 0.0
            
    def is_memory_safe(self) -> bool:
        """Check if current memory usage is within safe limits."""
        memory_mb = self.get_memory_usage()
        return memory_mb < (self.config.memory_threshold_mb * self.config.memory_safety_margin)
        
    def get_memory_trend(self) -> str:
        """Get memory usage trend (increasing, decreasing, stable)."""
        if len(self.memory_readings) < 3:
            return "stable"
            
        recent = list(self.memory_readings)[-3:]
        if recent[2] > recent[1] > recent[0]:
            return "increasing"
        elif recent[2] < recent[1] < recent[0]:
            return "decreasing"
        else:
            return "stable"
            
    def should_optimize(self) -> bool:
        """Determine if memory optimization is needed."""
        if not self.config.enable_auto_optimization:
            return False
            
        memory_mb = self.get_memory_usage()
        memory_percent = self.get_memory_percentage()
        
        # Check if memory usage is high
        if memory_mb > self.config.memory_threshold_mb:
            return True
            
        # Check if memory usage is increasing rapidly
        if self.get_memory_trend() == "increasing" and memory_percent > 70:
            return True
            
        return False


class OptimizedJobBatcher:
    """
    Optimized job batcher with memory monitoring and intelligent optimization.
    
    Features:
    - Memory-efficient job batching with monitoring
    - Configurable batch sizes based on system resources
    - Memory usage tracking and optimization
    - Batch optimization algorithms
    - Performance metrics and monitoring
    - Integration with existing pipeline components
    """
    
    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()
        
        # Initialize components
        self.memory_monitor = MemoryMonitor(self.config)
        self.metrics = BatchMetrics()
        
        # Batch management
        self.current_batch_size = self.config.initial_batch_size
        self.current_batch = []
        self.is_running = False
        
        # Performance tracking
        self.batch_start_time = None
        self.optimization_task = None
        
        logger.info(f"OptimizedJobBatcher initialized: batch_size={self.current_batch_size}")
        
    async def start(self) -> None:
        """Start the job batcher and optimization monitoring."""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start optimization monitoring
        if self.config.enable_auto_optimization:
            self.optimization_task = asyncio.create_task(self._optimization_loop())
            
        logger.info("OptimizedJobBatcher started")
        
    async def stop(self) -> None:
        """Stop the job batcher and cleanup resources."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Stop optimization monitoring
        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass
                
        # Process any remaining jobs in current batch
        if self.current_batch:
            await self._process_current_batch()
            
        logger.info("OptimizedJobBatcher stopped")
        
    async def add_job(self, job: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Add a job to the current batch. Returns a batch if ready for processing.
        
        Args:
            job: Job dictionary to add to batch
            
        Returns:
            List of jobs if batch is ready for processing, None otherwise
        """
        if not self.is_running:
            raise RuntimeError("Job batcher not started")
            
        # Add job to current batch
        self.current_batch.append(job)
        
        # Check if batch is ready for processing
        if len(self.current_batch) >= self.current_batch_size:
            return await self._process_current_batch()
            
        return None
        
    async def force_process_batch(self) -> List[Dict[str, Any]]:
        """Force processing of current batch regardless of size."""
        if not self.current_batch:
            return []
            
        return await self._process_current_batch()
        
    async def _process_current_batch(self) -> List[Dict[str, Any]]:
        """Process the current batch and return the jobs."""
        if not self.current_batch:
            return []
            
        batch_start = time.time()
        batch_size = len(self.current_batch)
        
        # Update metrics
        self.metrics.total_batches += 1
        self.metrics.total_jobs_processed += batch_size
        self.metrics.batch_sizes.append(batch_size)
        
        # Get memory usage
        memory_mb = self.memory_monitor.get_memory_usage()
        self.metrics.memory_readings.append(memory_mb)
        self.metrics.memory_usage_mb = memory_mb
        self.metrics.peak_memory_mb = max(self.metrics.peak_memory_mb, memory_mb)
        
        # Process batch
        jobs_to_process = self.current_batch.copy()
        self.current_batch.clear()
        
        # Record batch processing time
        batch_time = time.time() - batch_start
        self.metrics.batch_times.append(batch_time)
        
        # Update averages
        if self.metrics.batch_sizes:
            self.metrics.avg_batch_size = sum(self.metrics.batch_sizes) / len(self.metrics.batch_sizes)
        if self.metrics.batch_times:
            self.metrics.avg_batch_time = sum(self.metrics.batch_times) / len(self.metrics.batch_times)
            
        logger.info(f"Processed batch: {batch_size} jobs, {batch_time:.2f}s, {memory_mb:.1f}MB")
        
        return jobs_to_process
        
    async def _optimization_loop(self) -> None:
        """Background optimization loop."""
        while self.is_running:
            try:
                await self._perform_optimization()
                await asyncio.sleep(self.config.optimization_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization error: {e}")
                await asyncio.sleep(5)  # Brief pause on error
                
    async def _perform_optimization(self) -> None:
        """Perform batch size optimization based on system performance."""
        try:
            # Check if optimization is needed
            if not self.memory_monitor.should_optimize():
                return
                
            # Get current performance metrics
            memory_mb = self.memory_monitor.get_memory_usage()
            memory_percent = self.memory_monitor.get_memory_percentage()
            memory_trend = self.memory_monitor.get_memory_trend()
            
            # Calculate optimal batch size
            optimal_size = self._calculate_optimal_batch_size(
                memory_mb, memory_percent, memory_trend
            )
            
            # Apply optimization if significant change
            if abs(optimal_size - self.current_batch_size) > 2:
                old_size = self.current_batch_size
                self.current_batch_size = optimal_size
                self.metrics.optimization_count += 1
                self.metrics.last_optimization = datetime.now()
                
                logger.info(f"Batch size optimized: {old_size} -> {optimal_size} "
                           f"(memory: {memory_mb:.1f}MB, {memory_percent:.1f}%)")
                
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            
    def _calculate_optimal_batch_size(self, memory_mb: float, memory_percent: float, 
                                    memory_trend: str) -> int:
        """Calculate optimal batch size based on system performance."""
        # Base size on memory usage
        if memory_percent > 80:
            # High memory usage - reduce batch size
            optimal_size = max(self.config.min_batch_size, 
                             int(self.current_batch_size * 0.7))
        elif memory_percent < 50:
            # Low memory usage - can increase batch size
            optimal_size = min(self.config.max_batch_size,
                             int(self.current_batch_size * 1.2))
        else:
            # Moderate memory usage - keep current size
            optimal_size = self.current_batch_size
            
        # Adjust based on memory trend
        if memory_trend == "increasing":
            optimal_size = max(self.config.min_batch_size, 
                             int(optimal_size * 0.8))
        elif memory_trend == "decreasing":
            optimal_size = min(self.config.max_batch_size,
                             int(optimal_size * 1.1))
            
        # Ensure within bounds
        optimal_size = max(self.config.min_batch_size, 
                          min(self.config.max_batch_size, optimal_size))
        
        return optimal_size
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current batch processing metrics."""
        return {
            "total_batches": self.metrics.total_batches,
            "total_jobs_processed": self.metrics.total_jobs_processed,
            "avg_batch_size": self.metrics.avg_batch_size,
            "avg_batch_time": self.metrics.avg_batch_time,
            "current_batch_size": self.current_batch_size,
            "current_batch_count": len(self.current_batch),
            "memory_usage_mb": self.metrics.memory_usage_mb,
            "peak_memory_mb": self.metrics.peak_memory_mb,
            "optimization_count": self.metrics.optimization_count,
            "last_optimization": self.metrics.last_optimization.isoformat(),
            "memory_trend": self.memory_monitor.get_memory_trend(),
            "memory_percentage": self.memory_monitor.get_memory_percentage()
        }
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the job batcher."""
        memory_mb = self.memory_monitor.get_memory_usage()
        memory_percent = self.memory_monitor.get_memory_percentage()
        
        # Determine health status
        if memory_percent > 90:
            status = "critical"
        elif memory_percent > 80:
            status = "warning"
        elif memory_percent > 60:
            status = "degraded"
        else:
            status = "healthy"
            
        return {
            "status": status,
            "memory_usage_mb": memory_mb,
            "memory_percentage": memory_percent,
            "current_batch_size": self.current_batch_size,
            "current_batch_count": len(self.current_batch),
            "is_running": self.is_running
        }
        
    async def batch_generator(self, jobs: List[Dict[str, Any]]) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Generator that yields batches of jobs for processing.
        
        Args:
            jobs: List of jobs to batch
            
        Yields:
            Batches of jobs ready for processing
        """
        for job in jobs:
            batch = await self.add_job(job)
            if batch:
                yield batch
                
        # Yield any remaining jobs
        if self.current_batch:
            yield await self.force_process_batch() 