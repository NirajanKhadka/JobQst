#!/usr/bin/env python3
"""
Service Manager - Handles service lifecycle management
Single responsibility: Start, stop, and monitor individual services
Max 300 lines following development standards
"""

import logging
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class ServiceManager:
    """
    Manages individual service lifecycle operations.
    Follows single responsibility principle - only handles service start/stop/status.
    """
    
    def __init__(self):
        """Initialize service manager with mock services for now."""
        self._services = {
            "processor_worker_1": MockService("processor_worker_1", "Job processor worker #1"),
            "processor_worker_2": MockService("processor_worker_2", "Job processor worker #2"),
            "processor_worker_3": MockService("processor_worker_3", "Job processor worker #3"),
            "processor_worker_4": MockService("processor_worker_4", "Job processor worker #4"),
            "processor_worker_5": MockService("processor_worker_5", "Job processor worker #5"),
            "applicator": MockService("applicator", "Automated job application submission"),
        }
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all available services."""
        return self._services
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of a specific service."""
        if service_name in self._services:
            return self._services[service_name].get_status()
        return {"status": "not_found", "error": f"Service {service_name} not found"}
    
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services."""
        return {k: v.get_status() for k, v in self._services.items()}
    
    def start_service(self, service_name: str, profile_name: str) -> bool:
        """Start a specific service."""
        if service_name in self._services:
            self._services[service_name].status = "running"
            self._services[service_name].start_time = datetime.now()
            logger.info(f"Started service {service_name} for profile {profile_name}")
            return True
        logger.error(f"Service {service_name} not found")
        return False
    
    def stop_service(self, service_name: str) -> bool:
        """Stop a specific service."""
        if service_name in self._services:
            self._services[service_name].status = "stopped"
            self._services[service_name].start_time = None
            logger.info(f"Stopped service {service_name}")
            return True
        logger.error(f"Service {service_name} not found")
        return False
    
    def restart_service(self, service_name: str, profile_name: str) -> bool:
        """Restart a specific service."""
        if self.stop_service(service_name):
            return self.start_service(service_name, profile_name)
        return False
    
    def get_running_services(self) -> List[str]:
        """Get list of currently running services."""
        return [name for name, service in self._services.items() 
                if service.status == "running"]
    
    def stop_all_services(self) -> int:
        """Stop all running services. Returns count of stopped services."""
        stopped_count = 0
        for service_name in self.get_running_services():
            if self.stop_service(service_name):
                stopped_count += 1
        return stopped_count


class MockService:
    """Mock service for development and testing."""
    
    def __init__(self, name: str, description: str, status: str = "stopped"):
        self.name = name
        self.description = description
        self.status = status
        self.start_time = None
        self.resource_usage = {"cpu": 0.0, "memory": 0.0}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status."""
        uptime = "00:00:00"
        if self.start_time and self.status == "running":
            delta = datetime.now() - self.start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        return {
            "status": self.status,
            "description": self.description,
            "uptime": uptime,
            "start_time": self.start_time,
            "processed_count": 0,
            "cpu_usage": self.resource_usage["cpu"],
            "memory_usage": self.resource_usage["memory"]
        }


# Global service manager instance
_service_manager = None

def get_service_manager() -> ServiceManager:
    """Get global service manager instance."""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager