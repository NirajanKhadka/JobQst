#!/usr/bin/env python3
"""
WorkerStatusTracker - High-level worker state management
Tracks worker tasks, states, and provides meaningful descriptions.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from enum import Enum

# Import AI service monitoring components
try:
    from src.services.ollama_connection_checker import get_ollama_checker
    AI_MONITORING_AVAILABLE = True
except ImportError:
    AI_MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)


class WorkerState(Enum):
    """Worker state enumeration"""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPED = "stopped"
    STARTING = "starting"


@dataclass
class WorkerStatus:
    """Comprehensive worker status information"""
    service_name: str
    status: str  # 'running', 'stopped', 'error', 'idle'
    description: str  # Meaningful description instead of "No description"
    pid: Optional[int] = None
    cpu_usage: float = 0.0  # Real CPU percentage
    memory_usage: Dict[str, Any] = field(default_factory=dict)  # RSS, VMS, etc.
    uptime: str = "00:00:00"  # Formatted uptime string
    current_task: Optional[str] = None  # What the worker is currently doing
    processed_count: int = 0  # Jobs processed
    error_count: int = 0  # Number of errors
    last_activity: Optional[datetime] = None  # Last time worker did something
    resource_usage: Dict[str, float] = field(default_factory=dict)  # CPU, memory percentages
    worker_state: WorkerState = WorkerState.IDLE
    start_time: Optional[datetime] = None
    last_error: Optional[str] = None


class WorkerStatusTracker:
    """
    Tracks high-level worker states and current tasks.
    Provides meaningful worker descriptions and processing statistics.
    """

    def __init__(self):
        """Initialize the worker status tracker."""
        self.worker_states: Dict[str, WorkerStatus] = {}
        self.worker_descriptions: Dict[str, str] = {
            # Default descriptions for common worker types
            "processor_worker_1": "Primary job processor - analyzes and classifies scraped jobs",
            "processor_worker_2": "Secondary job processor - handles overflow and backup processing",
            "processor_worker_3": "Tertiary job processor - ensures high availability processing",
            "processor_worker_4": "Additional job processor - scales processing capacity",
            "processor_worker_5": "Additional job processor - maximum throughput processing",
            "job_scraper": "Web scraper - collects job postings from various job boards",
            "scheduler": "Task scheduler - manages automated job processing workflows",
            "health_monitor": "System health monitor - tracks application performance",
            "ai_service_monitor": "AI service health monitor - tracks Ollama and AI analysis status"
        }
        
        # Initialize AI service monitoring
        self.ai_service_status = {
            'ollama_available': False,
            'last_check': None,
            'connection_status': 'unknown',
            'available_models': [],
            'analysis_method_distribution': {
                'ai': 0,
                'Improved_rule_based': 0,
                'fallback': 0
            },
            'last_successful_ai': None,
            'consecutive_failures': 0
        }
        
        # Initialize AI connection checker if available
        self.ollama_checker = None
        if AI_MONITORING_AVAILABLE:
            try:
                self.ollama_checker = get_ollama_checker()
                logger.info("AI service monitoring enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize AI service monitoring: {e}")
        
        logger.info("WorkerStatusTracker initialized")

    def register_worker(self, worker_name: str, description: str = "") -> WorkerStatus:
        """
        Register a new worker for tracking.
        
        Args:
            worker_name: Unique worker identifier
            description: Custom description for the worker
            
        Returns:
            WorkerStatus: Initial worker status
        """
        # Use custom description or default based on worker name
        final_description = description or self._get_default_description(worker_name)
        
        worker_status = WorkerStatus(
            service_name=worker_name,
            status="stopped",
            description=final_description,
            worker_state=WorkerState.STOPPED,
            start_time=datetime.now()
        )
        
        self.worker_states[worker_name] = worker_status
        logger.info(f"Registered worker: {worker_name}")
        return worker_status

    def update_worker_task(self, worker_name: str, current_task: str) -> bool:
        """
        Update what task a worker is currently processing.
        
        Args:
            worker_name: Worker identifier
            current_task: Description of current task
            
        Returns:
            bool: True if update successful
        """
        if worker_name not in self.worker_states:
            logger.warning(f"Worker {worker_name} not registered, cannot update task")
            return False
        
        try:
            worker = self.worker_states[worker_name]
            worker.current_task = current_task
            worker.last_activity = datetime.now()
            worker.worker_state = WorkerState.PROCESSING
            worker.status = "running"
            
            logger.debug(f"Updated task for {worker_name}: {current_task}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task for {worker_name}: {e}")
            return False

    def set_worker_idle(self, worker_name: str) -> bool:
        """
        Mark worker as idle (waiting for tasks).
        
        Args:
            worker_name: Worker identifier
            
        Returns:
            bool: True if update successful
        """
        if worker_name not in self.worker_states:
            logger.warning(f"Worker {worker_name} not registered, cannot set idle")
            return False
        
        try:
            worker = self.worker_states[worker_name]
            worker.current_task = None
            worker.worker_state = WorkerState.IDLE
            worker.status = "running"
            worker.last_activity = datetime.now()
            
            logger.debug(f"Set worker {worker_name} to idle")
            return True
            
        except Exception as e:
            logger.error(f"Error setting worker {worker_name} to idle: {e}")
            return False

    def set_worker_error(self, worker_name: str, error_msg: str) -> bool:
        """
        Mark worker as in error state.
        
        Args:
            worker_name: Worker identifier
            error_msg: Error message description
            
        Returns:
            bool: True if update successful
        """
        if worker_name not in self.worker_states:
            logger.warning(f"Worker {worker_name} not registered, cannot set error")
            return False
        
        try:
            worker = self.worker_states[worker_name]
            worker.worker_state = WorkerState.ERROR
            worker.status = "error"
            worker.last_error = error_msg
            worker.error_count += 1
            worker.last_activity = datetime.now()
            
            logger.warning(f"Set worker {worker_name} to error state: {error_msg}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting worker {worker_name} to error state: {e}")
            return False

    def set_worker_stopped(self, worker_name: str) -> bool:
        """
        Mark worker as stopped.
        
        Args:
            worker_name: Worker identifier
            
        Returns:
            bool: True if update successful
        """
        if worker_name not in self.worker_states:
            logger.warning(f"Worker {worker_name} not registered, cannot set stopped")
            return False
        
        try:
            worker = self.worker_states[worker_name]
            worker.worker_state = WorkerState.STOPPED
            worker.status = "stopped"
            worker.current_task = None
            worker.last_activity = datetime.now()
            
            logger.info(f"Set worker {worker_name} to stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error setting worker {worker_name} to stopped: {e}")
            return False

    def increment_processed_count(self, worker_name: str) -> bool:
        """
        Increment the processed job count for a worker.
        
        Args:
            worker_name: Worker identifier
            
        Returns:
            bool: True if update successful
        """
        if worker_name not in self.worker_states:
            return False
        
        try:
            worker = self.worker_states[worker_name]
            worker.processed_count += 1
            worker.last_activity = datetime.now()
            
            logger.debug(f"Incremented processed count for {worker_name}: {worker.processed_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing processed count for {worker_name}: {e}")
            return False

    def get_worker_description(self, worker_name: str) -> str:
        """
        Get meaningful worker description instead of 'No description'.
        
        Args:
            worker_name: Worker identifier
            
        Returns:
            str: Meaningful description of the worker
        """
        if worker_name in self.worker_states:
            return self.worker_states[worker_name].description
        
        return self._get_default_description(worker_name)

    def get_processing_statistics(self, worker_name: str) -> Dict[str, Any]:
        """
        Get jobs processed, errors, success rate for a worker.
        
        Args:
            worker_name: Worker identifier
            
        Returns:
            Dict containing processing statistics
        """
        if worker_name not in self.worker_states:
            return {
                'processed_count': 0,
                'error_count': 0,
                'success_rate': 0.0,
                'last_activity': None,
                'current_task': None
            }
        
        worker = self.worker_states[worker_name]
        total_attempts = worker.processed_count + worker.error_count
        success_rate = (worker.processed_count / total_attempts * 100) if total_attempts > 0 else 0.0
        
        return {
            'processed_count': worker.processed_count,
            'error_count': worker.error_count,
            'success_rate': round(success_rate, 2),
            'last_activity': worker.last_activity.isoformat() if worker.last_activity else None,
            'current_task': worker.current_task,
            'worker_state': worker.worker_state.value,
            'last_error': worker.last_error
        }

    def get_worker_status(self, worker_name: str) -> Optional[WorkerStatus]:
        """
        Get complete worker status.
        
        Args:
            worker_name: Worker identifier
            
        Returns:
            WorkerStatus or None if not found
        """
        return self.worker_states.get(worker_name)

    def get_all_worker_statuses(self) -> Dict[str, WorkerStatus]:
        """
        Get all worker statuses.
        
        Returns:
            Dict mapping worker names to their statuses
        """
        return self.worker_states.copy()

    def update_worker_resources(self, worker_name: str, cpu_usage: float, 
                               memory_usage: Dict[str, Any], uptime: str) -> bool:
        """
        Update worker resource usage information.
        
        Args:
            worker_name: Worker identifier
            cpu_usage: CPU usage percentage
            memory_usage: Memory usage information
            uptime: Formatted uptime string
            
        Returns:
            bool: True if update successful
        """
        if worker_name not in self.worker_states:
            return False
        
        try:
            worker = self.worker_states[worker_name]
            worker.cpu_usage = cpu_usage
            worker.memory_usage = memory_usage
            worker.uptime = uptime
            worker.resource_usage = {
                'cpu': cpu_usage,
                'memory': memory_usage.get('percent', 0.0)
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating resources for {worker_name}: {e}")
            return False

    def is_worker_idle_too_long(self, worker_name: str, idle_threshold_minutes: int = 5) -> bool:
        """
        Check if worker has been idle for too long.
        
        Args:
            worker_name: Worker identifier
            idle_threshold_minutes: Minutes before considering worker inactive
            
        Returns:
            bool: True if worker has been idle too long
        """
        if worker_name not in self.worker_states:
            return False
        
        worker = self.worker_states[worker_name]
        
        if worker.worker_state != WorkerState.IDLE:
            return False
        
        if not worker.last_activity:
            return True  # No activity recorded
        
        idle_time = datetime.now() - worker.last_activity
        return idle_time > timedelta(minutes=idle_threshold_minutes)

    def get_idle_workers(self) -> List[str]:
        """
        Get list of workers that are currently idle.
        
        Returns:
            List of worker names that are idle
        """
        idle_workers = []
        for worker_name, worker in self.worker_states.items():
            if worker.worker_state == WorkerState.IDLE:
                idle_workers.append(worker_name)
        return idle_workers

    def get_active_workers(self) -> List[str]:
        """
        Get list of workers that are currently processing tasks.
        
        Returns:
            List of worker names that are actively processing
        """
        active_workers = []
        for worker_name, worker in self.worker_states.items():
            if worker.worker_state == WorkerState.PROCESSING:
                active_workers.append(worker_name)
        return active_workers

    def get_error_workers(self) -> List[str]:
        """
        Get list of workers that are in error state.
        
        Returns:
            List of worker names that have errors
        """
        error_workers = []
        for worker_name, worker in self.worker_states.items():
            if worker.worker_state == WorkerState.ERROR:
                error_workers.append(worker_name)
        return error_workers

    def cleanup_old_workers(self, max_age_hours: int = 24) -> int:
        """
        Remove worker records that are too old.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            int: Number of workers cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_workers = []
        
        for worker_name, worker in self.worker_states.items():
            if (worker.start_time and worker.start_time < cutoff_time and 
                worker.worker_state == WorkerState.STOPPED):
                old_workers.append(worker_name)
        
        for worker_name in old_workers:
            del self.worker_states[worker_name]
            logger.info(f"Cleaned up old worker record: {worker_name}")
        
        return len(old_workers)

    def update_ai_service_status(self, analysis_method_stats: Dict[str, int] = None) -> bool:
        """
        Update AI service status and analysis method distribution.
        
        Args:
            analysis_method_stats: Dictionary with analysis method counts
            
        Returns:
            bool: True if update successful
        """
        try:
            # Update Ollama connection status
            if self.ollama_checker:
                self.ai_service_status['ollama_available'] = self.ollama_checker.is_available()
                self.ai_service_status['last_check'] = datetime.now().isoformat()
                
                if self.ai_service_status['ollama_available']:
                    self.ai_service_status['connection_status'] = 'connected'
                    self.ai_service_status['available_models'] = self.ollama_checker.get_available_models()
                    self.ai_service_status['consecutive_failures'] = 0
                else:
                    self.ai_service_status['connection_status'] = 'disconnected'
                    self.ai_service_status['consecutive_failures'] += 1
            
            # Update analysis method distribution
            if analysis_method_stats:
                self.ai_service_status['analysis_method_distribution'].update(analysis_method_stats)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating AI service status: {e}")
            return False
    
    def get_ai_service_status(self) -> Dict[str, Any]:
        """
        Get current AI service status.
        
        Returns:
            Dict containing AI service status information
        """
        # Update status before returning
        self.update_ai_service_status()
        
        status = self.ai_service_status.copy()
        
        # Add connection checker statistics if available
        if self.ollama_checker:
            try:
                checker_stats = self.ollama_checker.get_statistics()
                status['connection_stats'] = checker_stats
            except Exception as e:
                logger.debug(f"Could not get connection checker stats: {e}")
        
        return status
    
    def get_ai_service_health_summary(self) -> Dict[str, Any]:
        """
        Get AI service health summary for dashboard display.
        
        Returns:
            Dict containing health summary
        """
        ai_status = self.get_ai_service_status()
        
        # Determine overall health
        if ai_status['ollama_available']:
            health_status = 'healthy'
            health_color = 'green'
        elif ai_status['consecutive_failures'] < 3:
            health_status = 'degraded'
            health_color = 'yellow'
        else:
            health_status = 'unhealthy'
            health_color = 'red'
        
        # Calculate analysis method percentages
        total_analyses = sum(ai_status['analysis_method_distribution'].values())
        method_percentages = {}
        if total_analyses > 0:
            for method, count in ai_status['analysis_method_distribution'].items():
                method_percentages[method] = round((count / total_analyses) * 100, 1)
        
        return {
            'health_status': health_status,
            'health_color': health_color,
            'ollama_available': ai_status['ollama_available'],
            'connection_status': ai_status['connection_status'],
            'available_models_count': len(ai_status['available_models']),
            'consecutive_failures': ai_status['consecutive_failures'],
            'last_check': ai_status['last_check'],
            'analysis_method_percentages': method_percentages,
            'primary_analysis_method': max(ai_status['analysis_method_distribution'], 
                                         key=ai_status['analysis_method_distribution'].get) if total_analyses > 0 else 'none'
        }
    
    def register_ai_service_worker(self) -> WorkerStatus:
        """
        Register AI service monitor as a worker.
        
        Returns:
            WorkerStatus for AI service monitor
        """
        return self.register_worker(
            "ai_service_monitor",
            "AI service health monitor - tracks Ollama and AI analysis status"
        )
    
    def update_ai_service_worker_status(self) -> bool:
        """
        Update AI service monitor worker status based on current AI health.
        
        Returns:
            bool: True if update successful
        """
        worker_name = "ai_service_monitor"
        
        # Register worker if not exists
        if worker_name not in self.worker_states:
            self.register_ai_service_worker()
        
        try:
            ai_health = self.get_ai_service_health_summary()
            
            # Update worker task based on AI service status
            if ai_health['health_status'] == 'healthy':
                self.update_worker_task(worker_name, f"Monitoring AI services - {ai_health['available_models_count']} models available")
            elif ai_health['health_status'] == 'degraded':
                self.update_worker_task(worker_name, f"AI services degraded - {ai_health['consecutive_failures']} recent failures")
            else:
                self.set_worker_error(worker_name, f"AI services unavailable - {ai_health['consecutive_failures']} consecutive failures")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating AI service worker status: {e}")
            return False

    def _get_default_description(self, worker_name: str) -> str:
        """Get default description based on worker name patterns."""
        # Check for exact match first
        if worker_name in self.worker_descriptions:
            return self.worker_descriptions[worker_name]
        
        # Pattern matching for dynamic worker names
        if "processor_worker" in worker_name:
            return f"Job processor worker - analyzes and classifies scraped jobs"
        elif "scraper" in worker_name.lower():
            return f"Web scraper worker - collects job postings from job boards"
        elif "scheduler" in worker_name.lower():
            return f"Task scheduler worker - manages automated workflows"
        elif "monitor" in worker_name.lower():
            return f"System monitoring worker - tracks application health"
        else:
            return f"AutoJobAgent worker - {worker_name.replace('_', ' ').title()}"
