"""
reliable Service Manager for AutoJobAgent Dashboard
Handles reliable startup and monitoring of core services
"""

import subprocess
import psutil
import time
import logging
import socket
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import os
import sys
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ServiceInfo:
    name: str
    status: ServiceStatus
    pid: Optional[int] = None
    port: Optional[int] = None
    command: Optional[str] = None
    error_message: Optional[str] = None
    last_check: Optional[float] = None

class reliableServiceManager:
    """Manages core services with reliable error handling and recovery."""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.project_root = Path(__file__).parent.parent.parent
        self.processes: Dict[str, subprocess.Popen] = {}
        
        # Service configurations
        self.service_configs = {
            "ollama": {
                "command": ["ollama", "serve"],
                "port": 11434,
                "check_url": "http://localhost:11434/api/version",
                "required": False,
                "description": "Ollama AI Service"
            },
            "job_processor": {
                "command": [sys.executable, "main.py", "--action", "process", "--headless"],
                "port": None,
                "check_process": True,
                "required": True,
                "description": "Job Processing Service"
            },
            "scraper": {
                "command": [sys.executable, "main.py", "--action", "scrape", "--headless"],
                "port": None,
                "check_process": True,
                "required": True,
                "description": "Job Scraping Service"
            }
        }
        
        # Initialize service status
        for service_name in self.service_configs:
            self.services[service_name] = ServiceInfo(
                name=service_name,
                status=ServiceStatus.UNKNOWN
            )
    
    def check_service_status(self, service_name: str) -> ServiceStatus:
        """Check the current status of a service."""
        if service_name not in self.service_configs:
            return ServiceStatus.UNKNOWN
        
        config = self.service_configs[service_name]
        service_info = self.services[service_name]
        
        try:
            # Check by port if specified
            if config.get("port"):
                if self._is_port_open("localhost", config["port"]):
                    service_info.status = ServiceStatus.RUNNING
                    service_info.port = config["port"]
                else:
                    service_info.status = ServiceStatus.STOPPED
            
            # Check by process if specified
            elif config.get("check_process"):
                if self._is_process_running(service_name):
                    service_info.status = ServiceStatus.RUNNING
                else:
                    service_info.status = ServiceStatus.STOPPED
            
            service_info.last_check = time.time()
            
        except Exception as e:
            logger.error(f"Error checking service {service_name}: {e}")
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
        
        return service_info.status
    
    def start_service(self, service_name: str) -> bool:
        """Start a service with reliable error handling."""
        if service_name not in self.service_configs:
            logger.error(f"Unknown service: {service_name}")
            return False
        
        config = self.service_configs[service_name]
        service_info = self.services[service_name]
        
        try:
            # Check if already running
            if self.check_service_status(service_name) == ServiceStatus.RUNNING:
                logger.info(f"Service {service_name} is already running")
                return True
            
            service_info.status = ServiceStatus.STARTING
            logger.info(f"Starting service: {service_name}")
            
            # Prepare command
            command = config["command"].copy()
            
            # Set working directory to project root
            cwd = self.project_root
            
            # Prepare environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.project_root)
            
            # Start the process
            if service_name == "ollama":
                # Special handling for Ollama
                process = self._start_ollama_service()
            else:
                # Standard process startup
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                )
            
            if process:
                self.processes[service_name] = process
                service_info.pid = process.pid
                service_info.command = " ".join(command)
                
                # Wait a moment and check if it started successfully
                time.sleep(2)
                
                if self.check_service_status(service_name) == ServiceStatus.RUNNING:
                    logger.info(f"Service {service_name} started successfully (PID: {process.pid})")
                    return True
                else:
                    logger.error(f"Service {service_name} failed to start properly")
                    service_info.status = ServiceStatus.ERROR
                    return False
            else:
                service_info.status = ServiceStatus.ERROR
                service_info.error_message = "Failed to create process"
                return False
                
        except Exception as e:
            logger.error(f"Error starting service {service_name}: {e}")
            service_info.status = ServiceStatus.ERROR
            service_info.error_message = str(e)
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """Stop a service gracefully."""
        if service_name not in self.service_configs:
            return False
        
        service_info = self.services[service_name]
        
        try:
            # Stop the process if we have it
            if service_name in self.processes:
                process = self.processes[service_name]
                if process.poll() is None:  # Still running
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    
                    del self.processes[service_name]
            
            # Also try to kill by process name
            self._kill_process_by_name(service_name)
            
            service_info.status = ServiceStatus.STOPPED
            service_info.pid = None
            service_info.error_message = None
            
            logger.info(f"Service {service_name} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping service {service_name}: {e}")
            service_info.error_message = str(e)
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """Restart a service."""
        logger.info(f"Restarting service: {service_name}")
        self.stop_service(service_name)
        time.sleep(2)
        return self.start_service(service_name)
    
    def get_all_service_status(self) -> Dict[str, ServiceInfo]:
        """Get status of all services."""
        for service_name in self.services:
            self.check_service_status(service_name)
        return self.services.copy()
    
    def start_all_services(self) -> Dict[str, bool]:
        """Start all services and return results."""
        results = {}
        
        # Start services in order of dependency
        service_order = ["ollama", "job_processor", "scraper"]
        
        for service_name in service_order:
            if service_name in self.service_configs:
                results[service_name] = self.start_service(service_name)
                
                # Add delay between service starts
                if results[service_name]:
                    time.sleep(1)
        
        return results
    
    def stop_all_services(self) -> Dict[str, bool]:
        """Stop all services."""
        results = {}
        
        for service_name in self.services:
            results[service_name] = self.stop_service(service_name)
        
        return results
    
    def get_service_health(self) -> Dict[str, any]:
        """Get comprehensive health information."""
        health = {
            "timestamp": time.time(),
            "services": {},
            "system": self._get_system_health(),
            "overall_status": "healthy"
        }
        
        failed_services = 0
        total_services = len(self.services)
        
        for service_name, service_info in self.get_all_service_status().items():
            config = self.service_configs[service_name]
            
            service_health = {
                "status": service_info.status.value,
                "required": config.get("required", False),
                "description": config.get("description", service_name),
                "pid": service_info.pid,
                "port": service_info.port,
                "error": service_info.error_message,
                "last_check": service_info.last_check
            }
            
            health["services"][service_name] = service_health
            
            # Count failures
            if service_info.status in [ServiceStatus.ERROR, ServiceStatus.STOPPED]:
                if config.get("required", False):
                    failed_services += 1
        
        # Determine overall status
        if failed_services > 0:
            health["overall_status"] = "degraded"
        if failed_services >= total_services // 2:
            health["overall_status"] = "unhealthy"
        
        return health
    
    def _is_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False
    
    def _is_process_running(self, service_name: str) -> bool:
        """Check if a process is running by name."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info.get('cmdline', []))
                
                # Check for service-specific patterns
                if service_name == "job_processor":
                    if 'main.py' in cmdline and 'process' in cmdline:
                        return True
                elif service_name == "scraper":
                    if 'main.py' in cmdline and 'scrape' in cmdline:
                        return True
                elif service_name in cmdline.lower():
                    return True
            
            return False
        except Exception:
            return False
    
    def _kill_process_by_name(self, service_name: str):
        """Kill processes by service name."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info.get('cmdline', []))
                
                should_kill = False
                if service_name == "job_processor" and 'main.py' in cmdline and 'process' in cmdline:
                    should_kill = True
                elif service_name == "scraper" and 'main.py' in cmdline and 'scrape' in cmdline:
                    should_kill = True
                elif service_name in cmdline.lower():
                    should_kill = True
                
                if should_kill:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        proc.kill()
        except Exception as e:
            logger.warning(f"Error killing processes for {service_name}: {e}")
    
    def _start_ollama_service(self) -> Optional[subprocess.Popen]:
        """Special handling for Ollama service startup."""
        try:
            # Check if Ollama is installed
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.warning("Ollama not installed or not in PATH")
                return None
            
            # Start Ollama serve
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            return process
            
        except Exception as e:
            logger.error(f"Error starting Ollama: {e}")
            return None
    
    def _get_system_health(self) -> Dict[str, any]:
        """Get system health metrics."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
                "python_version": sys.version,
                "platform": sys.platform
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"error": str(e)}

# Global service manager instance
_service_manager = None

def get_service_manager() -> reliableServiceManager:
    """Get the global service manager instance."""
    global _service_manager
    if _service_manager is None:
        _service_manager = reliableServiceManager()
    return _service_manager