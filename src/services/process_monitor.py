#!/usr/bin/env python3
"""
ProcessMonitor - Real-time process monitoring using psutil
Replaces mock data with actual process statistics for dashboard worker status.
"""

import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Data class for process information"""
    pid: int
    name: str
    description: str
    start_time: datetime
    status: str


class ProcessMonitor:
    """
    Real-time process monitoring using psutil library.
    Provides accurate CPU usage, memory consumption, and uptime data.
    """

    def __init__(self):
        """Initialize the process monitor."""
        self.monitored_processes: Dict[str, psutil.Process] = {}
        self.process_metadata: Dict[str, ProcessInfo] = {}
        logger.info("ProcessMonitor initialized")

    def register_process(self, service_name: str, pid: int, description: str = "") -> bool:
        """
        Register a process for monitoring.
        
        Args:
            service_name: Unique identifier for the service
            pid: Process ID to monitor
            description: Human-readable description of the process
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            process = psutil.Process(pid)
            
            # Verify process exists and is accessible
            if not process.is_running():
                logger.warning(f"Process {pid} is not running, cannot register {service_name}")
                return False
            
            # Store process and metadata
            self.monitored_processes[service_name] = process
            self.process_metadata[service_name] = ProcessInfo(
                pid=pid,
                name=process.name(),
                description=description or f"{process.name()} worker",
                start_time=datetime.fromtimestamp(process.create_time()),
                status="running"
            )
            
            logger.info(f"Registered process {service_name} (PID: {pid})")
            return True
            
        except psutil.NoSuchProcess:
            logger.error(f"Process {pid} does not exist, cannot register {service_name}")
            return False
        except psutil.AccessDenied:
            logger.error(f"Access denied to process {pid}, cannot register {service_name}")
            return False
        except Exception as e:
            logger.error(f"Error registering process {service_name}: {e}")
            return False

    def unregister_process(self, service_name: str) -> bool:
        """
        Unregister a process from monitoring.
        
        Args:
            service_name: Service identifier to unregister
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            if service_name in self.monitored_processes:
                del self.monitored_processes[service_name]
            if service_name in self.process_metadata:
                del self.process_metadata[service_name]
            logger.info(f"Unregistered process {service_name}")
            return True
        except Exception as e:
            logger.error(f"Error unregistering process {service_name}: {e}")
            return False

    def get_process_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get detailed process status using psutil.
        
        Args:
            service_name: Service identifier
            
        Returns:
            Dict containing process status information
        """
        if service_name not in self.monitored_processes:
            return self._create_not_found_status(service_name)
        
        try:
            process = self.monitored_processes[service_name]
            metadata = self.process_metadata[service_name]
            
            # Check if process is still running
            if not process.is_running():
                return self._create_stopped_status(service_name)
            
            # Get process status
            status_info = {
                'service_name': service_name,
                'status': 'running',
                'description': metadata.description,
                'pid': metadata.pid,
                'name': metadata.name,
                'cpu_usage': self.get_cpu_usage(service_name),
                'memory_usage': self.get_memory_usage(service_name),
                'uptime': self._format_uptime(self.get_uptime(service_name)),
                'uptime_seconds': self.get_uptime(service_name).total_seconds(),
                'start_time': metadata.start_time.isoformat(),
                'process_status': process.status(),
                'num_threads': process.num_threads(),
                'resource_usage': {
                    'cpu': self.get_cpu_usage(service_name),
                    'memory': self.get_memory_usage(service_name).get('percent', 0.0)
                }
            }
            
            return status_info
            
        except psutil.NoSuchProcess:
            return self._create_stopped_status(service_name)
        except psutil.AccessDenied:
            return self._create_limited_access_status(service_name)
        except Exception as e:
            logger.error(f"Error getting status for {service_name}: {e}")
            return self._create_error_status(service_name, str(e))

    def get_cpu_usage(self, service_name: str) -> float:
        """
        Get real CPU usage percentage for a process.
        
        Args:
            service_name: Service identifier
            
        Returns:
            float: CPU usage percentage (0.0-100.0)
        """
        if service_name not in self.monitored_processes:
            return 0.0
        
        try:
            process = self.monitored_processes[service_name]
            if not process.is_running():
                return 0.0
            
            # Get CPU percentage with 1-second interval for accuracy
            cpu_percent = process.cpu_percent(interval=1)
            return round(cpu_percent, 2)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0
        except Exception as e:
            logger.error(f"Error getting CPU usage for {service_name}: {e}")
            return 0.0

    def get_memory_usage(self, service_name: str) -> Dict[str, Any]:
        """
        Get memory usage information for a process.
        
        Args:
            service_name: Service identifier
            
        Returns:
            Dict containing memory usage information
        """
        if service_name not in self.monitored_processes:
            return {'rss': 0, 'vms': 0, 'percent': 0.0}
        
        try:
            process = self.monitored_processes[service_name]
            if not process.is_running():
                return {'rss': 0, 'vms': 0, 'percent': 0.0}
            
            # Get memory info
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            return {
                'rss': memory_info.rss,  # Resident Set Size
                'vms': memory_info.vms,  # Virtual Memory Size
                'percent': round(memory_percent, 2),
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2)
            }
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {'rss': 0, 'vms': 0, 'percent': 0.0}
        except Exception as e:
            logger.error(f"Error getting memory usage for {service_name}: {e}")
            return {'rss': 0, 'vms': 0, 'percent': 0.0}

    def get_uptime(self, service_name: str) -> timedelta:
        """
        Calculate actual process uptime.
        
        Args:
            service_name: Service identifier
            
        Returns:
            timedelta: Process uptime
        """
        if service_name not in self.process_metadata:
            return timedelta(0)
        
        try:
            metadata = self.process_metadata[service_name]
            process = self.monitored_processes[service_name]
            
            if not process.is_running():
                return timedelta(0)
            
            # Calculate uptime from process start time
            current_time = datetime.now()
            uptime = current_time - metadata.start_time
            return uptime
            
        except Exception as e:
            logger.error(f"Error calculating uptime for {service_name}: {e}")
            return timedelta(0)

    def is_process_alive(self, service_name: str) -> bool:
        """
        Check if a monitored process is still running.
        
        Args:
            service_name: Service identifier
            
        Returns:
            bool: True if process is running, False otherwise
        """
        if service_name not in self.monitored_processes:
            return False
        
        try:
            process = self.monitored_processes[service_name]
            return process.is_running()
        except Exception:
            return False

    def get_all_monitored_processes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status for all monitored processes.
        
        Returns:
            Dict mapping service names to their status information
        """
        all_status = {}
        for service_name in list(self.monitored_processes.keys()):
            all_status[service_name] = self.get_process_status(service_name)
        return all_status

    def cleanup_dead_processes(self) -> int:
        """
        Remove dead processes from monitoring.
        
        Returns:
            int: Number of dead processes removed
        """
        dead_processes = []
        
        for service_name in list(self.monitored_processes.keys()):
            if not self.is_process_alive(service_name):
                dead_processes.append(service_name)
        
        for service_name in dead_processes:
            self.unregister_process(service_name)
            logger.info(f"Cleaned up dead process: {service_name}")
        
        return len(dead_processes)

    def _format_uptime(self, uptime: timedelta) -> str:
        """Format uptime as human-readable string."""
        total_seconds = int(uptime.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _create_not_found_status(self, service_name: str) -> Dict[str, Any]:
        """Create status for unregistered service."""
        return {
            'service_name': service_name,
            'status': 'not_registered',
            'description': 'Service not registered for monitoring',
            'pid': None,
            'cpu_usage': 0.0,
            'memory_usage': {'rss': 0, 'vms': 0, 'percent': 0.0},
            'uptime': '00:00:00',
            'uptime_seconds': 0,
            'resource_usage': {'cpu': 0.0, 'memory': 0.0}
        }

    def _create_stopped_status(self, service_name: str) -> Dict[str, Any]:
        """Create status for stopped process."""
        metadata = self.process_metadata.get(service_name)
        return {
            'service_name': service_name,
            'status': 'stopped',
            'description': metadata.description if metadata else 'Stopped process',
            'pid': metadata.pid if metadata else None,
            'cpu_usage': 0.0,
            'memory_usage': {'rss': 0, 'vms': 0, 'percent': 0.0},
            'uptime': '00:00:00',
            'uptime_seconds': 0,
            'resource_usage': {'cpu': 0.0, 'memory': 0.0}
        }

    def _create_limited_access_status(self, service_name: str) -> Dict[str, Any]:
        """Create status for process with limited access."""
        metadata = self.process_metadata.get(service_name)
        return {
            'service_name': service_name,
            'status': 'limited_access',
            'description': f"{metadata.description if metadata else 'Process'} (Limited Access)",
            'pid': metadata.pid if metadata else None,
            'cpu_usage': 0.0,
            'memory_usage': {'rss': 0, 'vms': 0, 'percent': 0.0},
            'uptime': 'Access Denied',
            'uptime_seconds': 0,
            'resource_usage': {'cpu': 0.0, 'memory': 0.0}
        }

    def _create_error_status(self, service_name: str, error_msg: str) -> Dict[str, Any]:
        """Create status for process with error."""
        return {
            'service_name': service_name,
            'status': 'error',
            'description': f'Error monitoring process: {error_msg}',
            'pid': None,
            'cpu_usage': 0.0,
            'memory_usage': {'rss': 0, 'vms': 0, 'percent': 0.0},
            'uptime': 'Error',
            'uptime_seconds': 0,
            'resource_usage': {'cpu': 0.0, 'memory': 0.0}
        }