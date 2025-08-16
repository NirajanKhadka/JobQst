#!/usr/bin/env python3
"""
Worker Pool Manager - Manages 5-worker document generation pool
Single responsibility: Coordinate parallel document generation workers
Max 300 lines following development standards
"""

import logging
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading
import queue
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .service_manager import get_service_manager

logger = logging.getLogger(__name__)

class WorkerPoolManager:
    """
    Manages the 5-worker document generation pool.
    Follows single responsibility principle - only handles worker coordination.
    """
    
    def __init__(self, max_workers: int = 5):
        """Initialize worker pool manager."""
        self.max_workers = max_workers
        self.service_manager = get_service_manager()
        self.work_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.active_workers = {}
        self.worker_stats = {
            "total_jobs_processed": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_processing_time": 0.0
        }
    
    def get_worker_services(self) -> List[str]:
        """Get list of worker service names."""
        return [f"processor_worker_{i}" for i in range(1, self.max_workers + 1)]
    
    def get_worker_pool_status(self) -> Dict[str, Any]:
        """Get overall worker pool status."""
        worker_services = self.get_worker_services()
        running_workers = 0
        total_processed = 0
        
        for worker_name in worker_services:
            status = self.service_manager.get_service_status(worker_name)
            if status.get("status") == "running":
                running_workers += 1
                total_processed += status.get("processed_count", 0)
        
        return {
            "total_workers": self.max_workers,
            "running_workers": running_workers,
            "idle_workers": self.max_workers - running_workers,
            "queue_size": self.work_queue.qsize(),
            "total_processed": total_processed,
            "stats": self.worker_stats
        }
    
    def start_worker_pool(self, profile_name: str) -> Dict[str, bool]:
        """Start all workers in the pool."""
        results = {}
        worker_services = self.get_worker_services()
        
        for worker_name in worker_services:
            success = self.service_manager.start_service(worker_name, profile_name)
            results[worker_name] = success
            if success:
                logger.info(f"Started worker {worker_name}")
            else:
                logger.error(f"Failed to start worker {worker_name}")
        
        return results
    
    def stop_worker_pool(self) -> Dict[str, bool]:
        """Stop all workers in the pool."""
        results = {}
        worker_services = self.get_worker_services()
        
        for worker_name in worker_services:
            success = self.service_manager.stop_service(worker_name)
            results[worker_name] = success
            if success:
                logger.info(f"Stopped worker {worker_name}")
            else:
                logger.error(f"Failed to stop worker {worker_name}")
        
        return results
    
    def get_individual_worker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed status for each individual worker."""
        worker_services = self.get_worker_services()
        worker_statuses = {}
        
        for worker_name in worker_services:
            worker_statuses[worker_name] = self.service_manager.get_service_status(worker_name)
        
        return worker_statuses
    
    def add_job_to_queue(self, job_data: Dict[str, Any]) -> bool:
        """Add a document generation job to the worker queue."""
        try:
            self.work_queue.put(job_data, timeout=1)
            logger.info(f"Added job to queue: {job_data.get('job_id', 'unknown')}")
            return True
        except queue.Full:
            logger.error("Worker queue is full, cannot add job")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        return {
            "pending_jobs": self.work_queue.qsize(),
            "completed_results": self.result_queue.qsize(),
            "max_queue_size": self.work_queue.maxsize if hasattr(self.work_queue, 'maxsize') else "unlimited"
        }
    
    def scale_worker_pool(self, new_size: int, profile_name: str) -> bool:
        """Scale the worker pool up or down."""
        if new_size < 1 or new_size > 10:
            logger.error(f"Invalid worker pool size: {new_size}. Must be between 1-10")
            return False
        
        current_workers = self.get_worker_services()
        
        if new_size > self.max_workers:
            # Scale up - start additional workers
            for i in range(self.max_workers + 1, new_size + 1):
                worker_name = f"processor_worker_{i}"
                # Would need to add new service to service manager
                logger.info(f"Would scale up to include {worker_name}")
        elif new_size < self.max_workers:
            # Scale down - stop excess workers
            for i in range(new_size + 1, self.max_workers + 1):
                worker_name = f"processor_worker_{i}"
                self.service_manager.stop_service(worker_name)
                logger.info(f"Scaled down by stopping {worker_name}")
        
        self.max_workers = new_size
        return True
    
    def get_worker_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the worker pool."""
        worker_statuses = self.get_individual_worker_status()
        
        total_cpu = 0.0
        total_memory = 0.0
        active_workers = 0
        
        for worker_name, status in worker_statuses.items():
            if status.get("status") == "running":
                active_workers += 1
                total_cpu += status.get("cpu_usage", 0.0)
                total_memory += status.get("memory_usage", 0.0)
        
        avg_cpu = total_cpu / active_workers if active_workers > 0 else 0.0
        avg_memory = total_memory / active_workers if active_workers > 0 else 0.0
        
        return {
            "active_workers": active_workers,
            "average_cpu_usage": avg_cpu,
            "average_memory_usage": avg_memory,
            "total_cpu_usage": total_cpu,
            "total_memory_usage": total_memory,
            "efficiency_score": self._calculate_efficiency_score(active_workers, avg_cpu)
        }
    
    def _calculate_efficiency_score(self, active_workers: int, avg_cpu: float) -> float:
        """Calculate worker pool efficiency score (0-100)."""
        if active_workers == 0:
            return 0.0
        
        # Simple efficiency calculation based on worker utilization
        utilization_score = min(avg_cpu / 80.0, 1.0) * 100  # 80% CPU is optimal
        worker_ratio_score = (active_workers / self.max_workers) * 100
        
        return (utilization_score + worker_ratio_score) / 2


# Global worker pool manager instance
_worker_pool_manager = None

def get_worker_pool_manager() -> WorkerPoolManager:
    """Get global worker pool manager instance."""
    global _worker_pool_manager
    if _worker_pool_manager is None:
        _worker_pool_manager = WorkerPoolManager()
    return _worker_pool_manager