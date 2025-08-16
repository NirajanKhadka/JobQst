#!/usr/bin/env python3
"""
System service for dashboard health monitoring and metrics.
Handles non-blocking system metrics, service discovery, and health checks.
"""

import asyncio
import socket
import psutil
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class SystemService:
    """
    Service for system metrics, health monitoring, and service discovery.
    Provides non-blocking operations with Automated caching.
    """
    
    def __init__(self, cache_ttl: int = 10):
        """
        Initialize SystemService.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 10s)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._background_refresh_running = False
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics with non-blocking operations and caching.
        
        Returns:
            Dict containing system metrics and health information
        """
        cache_key = "system_metrics"
        
        # Return cached data if valid
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            # Start background refresh if not running
            if not self._background_refresh_running:
                asyncio.create_task(self._background_refresh_metrics())
            
            metrics = await self._collect_metrics_async()
            self._set_cache(cache_key, metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return self._get_fallback_metrics()
    
    async def _collect_metrics_async(self) -> Dict[str, Any]:
        """Collect system metrics asynchronously with non-blocking calls."""
        try:
            # Use non-blocking CPU measurement
            cpu_percent = psutil.cpu_percent(interval=0.1)  # Much faster than interval=1
            
            # Memory and disk are already non-blocking
            memory = psutil.virtual_memory()
            disk_path = 'C:\\' if sys.platform == 'win32' else '/'
            disk = psutil.disk_usage(disk_path)
            
            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_usage": disk.percent,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Add network connectivity check (with timeout)
            try:
                import aiohttp
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                    async with session.get("https://www.google.com") as response:
                        metrics["network_status"] = "connected" if response.status == 200 else "disconnected"
            except Exception:
                metrics["network_status"] = "disconnected"
            
            # Add service status checks
            metrics["services"] = await self._check_services_async()
            
            # Add orchestration status
            metrics["orchestration"] = await self._check_orchestration_status()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error in _collect_metrics_async: {e}")
            return self._get_fallback_metrics()
    
    async def _check_services_async(self) -> Dict[str, str]:
        """Check service status asynchronously."""
        services_status = {}
        
        # Check Streamlit ports
        streamlit_ports = [8501, 8502, 8503, 8505]
        for port in streamlit_ports:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection('127.0.0.1', port),
                    timeout=1.0
                )
                writer.close()
                await writer.wait_closed()
                services_status[f"streamlit_{port}"] = "running"
            except Exception:
                services_status[f"streamlit_{port}"] = "stopped"
        
        # Check Ollama (port 11434)
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection('127.0.0.1', 11434),
                timeout=1.0
            )
            writer.close()
            await writer.wait_closed()
            services_status["ollama"] = "running"
        except Exception:
            services_status["ollama"] = "stopped"
        
        return services_status
    
    async def _check_orchestration_status(self) -> Dict[str, str]:
        """Check orchestration services status."""
        orchestration_status = {}
        
        try:
            # Check for background processes efficiently
            for proc in psutil.process_iter(['pid', 'name', 'cmdline'], ad_value=''):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    name = proc.info.get('name', '')
                    
                    # Check for specific orchestration processes
                    if 'main.py' in cmdline:
                        if 'scrape' in cmdline:
                            orchestration_status['scraper'] = 'running'
                        elif 'process' in cmdline:
                            orchestration_status['processor'] = 'running'
                        elif 'apply' in cmdline:
                            orchestration_status['applicator'] = 'running'
                    
                    # Check for document generation
                    if 'python' in name.lower() and any(keyword in cmdline for keyword in ['document', 'generate']):
                        orchestration_status['document_generator'] = 'running'
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Set default status for services not detected
            default_services = ['scraper', 'processor', 'applicator', 'document_generator']
            for service in default_services:
                if service not in orchestration_status:
                    orchestration_status[service] = 'stopped'
                    
        except Exception as e:
            logger.warning(f"Could not check orchestration processes: {e}")
            orchestration_status = {service: 'unknown' for service in ['scraper', 'processor', 'applicator', 'document_generator']}
        
        return orchestration_status
    
    async def _background_refresh_metrics(self):
        """Background task to refresh metrics cache."""
        self._background_refresh_running = True
        try:
            while True:
                await asyncio.sleep(self.cache_ttl)
                
                # Refresh metrics in background
                try:
                    metrics = await self._collect_metrics_async()
                    self._set_cache("system_metrics", metrics)
                    logger.debug("Background metrics refresh completed")
                except Exception as e:
                    logger.warning(f"Background metrics refresh failed: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Background metrics refresh cancelled")
        finally:
            self._background_refresh_running = False
    
    def get_service_health(self) -> Dict[str, Any]:
        """
        Get overall service health status.
        
        Returns:
            Dict containing health status information
        """
        try:
            # Get cached metrics if available
            cache_key = "system_metrics"
            if self._is_cache_valid(cache_key):
                metrics = self._cache[cache_key]
            else:
                # Return basic health check
                metrics = {
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "services": {},
                    "orchestration": {}
                }
            
            # Determine overall health
            cpu_healthy = metrics.get("cpu_percent", 0) < 80
            memory_healthy = metrics.get("memory_percent", 0) < 80
            
            if cpu_healthy and memory_healthy:
                overall_status = "healthy"
            elif metrics.get("cpu_percent", 0) > 90 or metrics.get("memory_percent", 0) > 90:
                overall_status = "unhealthy"
            else:
                overall_status = "degraded"
            
            return {
                "overall_status": overall_status,
                "system": {
                    "cpu_percent": metrics.get("cpu_percent", 0),
                    "memory_percent": metrics.get("memory_percent", 0),
                    "disk_usage": metrics.get("disk_usage", 0),
                },
                "services": metrics.get("services", {}),
                "orchestration": metrics.get("orchestration", {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting service health: {e}")
            return {
                "overall_status": "unknown",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache or cache_key not in self._cache_timestamps:
            return False
        
        elapsed = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return elapsed < self.cache_ttl
    
    def _set_cache(self, cache_key: str, data: Any):
        """Set cache entry with timestamp."""
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = datetime.now()
    
    def _get_fallback_metrics(self) -> Dict[str, Any]:
        """Get basic fallback metrics when collection fails."""
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_usage": 0,
            "network_status": "unknown",
            "services": {},
            "orchestration": {},
            "error": "Metrics collection failed",
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("SystemService cache cleared")


# Global service instance
_system_service = None

def get_system_service() -> SystemService:
    """Get singleton SystemService instance."""
    global _system_service
    if _system_service is None:
        _system_service = SystemService()
    return _system_service
