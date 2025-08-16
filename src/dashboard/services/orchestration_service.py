#!/usr/bin/env python3
"""
Orchestration service for dashboard integration with background services.
Provides interface to job application processor, document generation, and system orchestration.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import sys
import json
from enum import Enum

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class ApplicationStatus(Enum):
    """Job application status enumeration."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class DocumentGenerationStatus(Enum):
    """Document generation status enumeration."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"


class OrchestrationService:
    """
    Service for interfacing with background orchestration services.
    Implements the orchestration standards from Development Standards.
    """
    
    def __init__(self, cache_ttl: int = 30):
        """
        Initialize OrchestrationService.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 30s)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._background_processors = {}
        self._document_generators = {}
        
    async def get_application_queue_status(self) -> Dict[str, Any]:
        """
        Get real-time job application queue status.
        Implements orchestration standard: Track and expose real-time status.
        
        Returns:
            Dict containing application queue information
        """
        cache_key = "application_queue"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            # Try to get from background services
            queue_status = await self._check_application_processors()
            
            # Aggregate queue information
            status = {
                "total_queued": queue_status.get("queued_count", 0),
                "in_progress": queue_status.get("in_progress_count", 0),
                "completed_today": queue_status.get("completed_today", 0),
                "failed_today": queue_status.get("failed_today", 0),
                "rate_limit_status": queue_status.get("rate_limit", {}),
                "worker_status": queue_status.get("workers", []),
                "last_application": queue_status.get("last_application", None),
                "estimated_completion": queue_status.get("estimated_completion", None),
                "queue_health": queue_status.get("health", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
            self._set_cache(cache_key, status)
            return status
            
        except Exception as e:
            logger.error(f"Error getting application queue status: {e}")
            return self._get_fallback_application_status()
    
    async def trigger_job_application(self, job_id: str, priority: str = "normal") -> Dict[str, Any]:
        """
        Trigger individual job application ('Apply Now' functionality).
        Implements orchestration standard: Allow triggering individual applications.
        
        Args:
            job_id: Job identifier
            priority: Application priority (low, normal, high, urgent)
            
        Returns:
            Dict containing trigger result and status
        """
        try:
            # Validate inputs
            if not job_id:
                raise ValueError("Job ID is required")
            
            if priority not in ["low", "normal", "high", "urgent"]:
                priority = "normal"
            
            # Try to queue job application
            result = await self._queue_job_application(job_id, priority)
            
            if result.get("success", False):
                # Clear cache to force refresh
                self._clear_cache_key("application_queue")
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "priority": priority,
                    "queue_position": result.get("queue_position", 0),
                    "estimated_start": result.get("estimated_start", None),
                    "message": f"Job {job_id} queued successfully with {priority} priority",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "job_id": job_id,
                    "error": result.get("error", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error triggering job application for {job_id}: {e}")
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_document_generation_status(self) -> Dict[str, Any]:
        """
        Get document generation worker pool status.
        Implements orchestration standard: Support parallel/concurrent generation.
        
        Returns:
            Dict containing document generation status
        """
        cache_key = "document_generation"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        try:
            # Check document generation services
            doc_status = await self._check_document_generators()
            
            status = {
                "active_workers": doc_status.get("active_workers", 0),
                "max_workers": doc_status.get("max_workers", 5),
                "queue_length": doc_status.get("queue_length", 0),
                "documents_generated_today": doc_status.get("generated_today", 0),
                "generation_rate": doc_status.get("rate_per_hour", 0),
                "worker_health": doc_status.get("worker_health", []),
                "recent_generations": doc_status.get("recent_generations", []),
                "error_rate": doc_status.get("error_rate", 0),
                "avg_generation_time": doc_status.get("avg_time_seconds", 0),
                "service_health": doc_status.get("health", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
            self._set_cache(cache_key, status)
            return status
            
        except Exception as e:
            logger.error(f"Error getting document generation status: {e}")
            return self._get_fallback_document_status()
    
    async def pause_resume_application(self, job_id: str, action: str) -> Dict[str, Any]:
        """
        Manual override for job applications (pause/resume/cancel).
        Implements orchestration standard: Allow manual override.
        
        Args:
            job_id: Job identifier
            action: Action to perform (pause, resume, cancel)
            
        Returns:
            Dict containing action result
        """
        try:
            if action not in ["pause", "resume", "cancel"]:
                raise ValueError(f"Invalid action: {action}")
            
            # Try to perform action on background service
            result = await self._control_job_application(job_id, action)
            
            if result.get("success", False):
                # Clear cache to force refresh
                self._clear_cache_key("application_queue")
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "action": action,
                    "new_status": result.get("new_status", "unknown"),
                    "message": f"Job {job_id} {action}d successfully",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "job_id": job_id,
                    "action": action,
                    "error": result.get("error", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error {action}ing job {job_id}: {e}")
            return {
                "success": False,
                "job_id": job_id,
                "action": action,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_audit_trail(self, job_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get complete audit trail of application attempts.
        Implements orchestration standard: Maintain complete audit trail.
        
        Args:
            job_id: Optional job ID to filter by
            limit: Maximum number of entries to return
            
        Returns:
            List of audit trail entries
        """
        try:
            # Get audit trail from background services
            audit_data = await self._get_audit_trail_data(job_id, limit)
            
            # Format audit entries
            audit_trail = []
            for entry in audit_data.get("entries", []):
                audit_trail.append({
                    "timestamp": entry.get("timestamp"),
                    "job_id": entry.get("job_id"),
                    "action": entry.get("action"),
                    "status": entry.get("status"),
                    "user": entry.get("user", "system"),
                    "details": entry.get("details", {}),
                    "duration": entry.get("duration_seconds"),
                    "error": entry.get("error")
                })
            
            return audit_trail
            
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            return []
    
    async def get_orchestration_health(self) -> Dict[str, Any]:
        """
        Get overall orchestration system health.
        
        Returns:
            Dict containing health status of all orchestration services
        """
        try:
            # Check all orchestration components
            app_health = await self._check_application_processors()
            doc_health = await self._check_document_generators()
            
            # Determine overall health
            services_healthy = 0
            total_services = 0
            
            # Application processor health
            if app_health.get("health") == "healthy":
                services_healthy += 1
            total_services += 1
            
            # Document generator health
            if doc_health.get("health") == "healthy":
                services_healthy += 1
            total_services += 1
            
            # Calculate overall status
            if services_healthy == total_services:
                overall_status = "healthy"
            elif services_healthy > 0:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"
            
            return {
                "overall_status": overall_status,
                "services_healthy": services_healthy,
                "total_services": total_services,
                "application_processor": {
                    "status": app_health.get("health", "unknown"),
                    "workers": app_health.get("workers", []),
                    "queue_length": app_health.get("queued_count", 0)
                },
                "document_generator": {
                    "status": doc_health.get("health", "unknown"),
                    "workers": doc_health.get("active_workers", 0),
                    "queue_length": doc_health.get("queue_length", 0)
                },
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting orchestration health: {e}")
            return {
                "overall_status": "unknown",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    # Private helper methods
    
    async def _check_application_processors(self) -> Dict[str, Any]:
        """Check application processor services."""
        try:
            # Try to import and check orchestration services
            try:
                from src.services.orchestration_service import get_orchestration_service
                orchestration = get_orchestration_service()
                return await orchestration.get_application_status()
            except ImportError:
                # Fallback to process-based checking
                return await self._check_processes_for_applications()
            
        except Exception as e:
            logger.warning(f"Could not check application processors: {e}")
            return self._get_fallback_application_status()
    
    async def _check_document_generators(self) -> Dict[str, Any]:
        """Check document generation services."""
        try:
            # Try to import and check document services
            try:
                from src.services.document_service import get_document_service
                doc_service = get_document_service()
                return await doc_service.get_generation_status()
            except ImportError:
                # Fallback to process-based checking
                return await self._check_processes_for_documents()
            
        except Exception as e:
            logger.warning(f"Could not check document generators: {e}")
            return self._get_fallback_document_status()
    
    async def _check_processes_for_applications(self) -> Dict[str, Any]:
        """Fallback: Check processes for application workers."""
        import psutil
        
        app_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline'], ad_value=''):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'python' in proc.info.get('name', '').lower() and 'apply' in cmdline:
                    app_processes.append({
                        "pid": proc.info['pid'],
                        "status": "running",
                        "cmdline": cmdline
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "health": "healthy" if app_processes else "stopped",
            "workers": app_processes,
            "queued_count": 0,
            "in_progress_count": len(app_processes),
            "completed_today": 0,
            "failed_today": 0
        }
    
    async def _check_processes_for_documents(self) -> Dict[str, Any]:
        """Fallback: Check processes for document generation workers."""
        import psutil
        
        doc_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline'], ad_value=''):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'python' in proc.info.get('name', '').lower() and any(keyword in cmdline for keyword in ['document', 'generate']):
                    doc_processes.append({
                        "pid": proc.info['pid'],
                        "status": "running",
                        "cmdline": cmdline
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "health": "healthy" if doc_processes else "stopped",
            "active_workers": len(doc_processes),
            "max_workers": 5,
            "queue_length": 0,
            "generated_today": 0,
            "worker_health": doc_processes
        }
    
    async def _queue_job_application(self, job_id: str, priority: str) -> Dict[str, Any]:
        """Queue a job application with the background service."""
        # This would interface with the actual background service
        # For now, return a mock successful response
        return {
            "success": True,
            "queue_position": 1,
            "estimated_start": (datetime.now() + timedelta(minutes=5)).isoformat()
        }
    
    async def _control_job_application(self, job_id: str, action: str) -> Dict[str, Any]:
        """Control (pause/resume/cancel) a job application."""
        # This would interface with the actual background service
        # For now, return a mock successful response
        return {
            "success": True,
            "new_status": f"{action}d"
        }
    
    async def _get_audit_trail_data(self, job_id: Optional[str], limit: int) -> Dict[str, Any]:
        """Get audit trail data from background services."""
        # This would interface with the actual audit system
        # For now, return mock data
        return {
            "entries": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "job_id": job_id or "example_job",
                    "action": "queued",
                    "status": "success",
                    "user": "dashboard",
                    "details": {"priority": "normal"}
                }
            ]
        }
    
    def _get_fallback_application_status(self) -> Dict[str, Any]:
        """Fallback application status when services unavailable."""
        return {
            "total_queued": 0,
            "in_progress": 0,
            "completed_today": 0,
            "failed_today": 0,
            "rate_limit_status": {"requests_remaining": 0, "reset_time": None},
            "worker_status": [],
            "queue_health": "unknown",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_fallback_document_status(self) -> Dict[str, Any]:
        """Fallback document status when services unavailable."""
        return {
            "active_workers": 0,
            "max_workers": 5,
            "queue_length": 0,
            "documents_generated_today": 0,
            "generation_rate": 0,
            "worker_health": [],
            "service_health": "unknown",
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
    
    def _clear_cache_key(self, cache_key: str):
        """Clear specific cache key."""
        self._cache.pop(cache_key, None)
        self._cache_timestamps.pop(cache_key, None)
    
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("OrchestrationService cache cleared")


# Global service instance
_orchestration_service = None

def get_orchestration_service() -> OrchestrationService:
    """Get singleton OrchestrationService instance."""
    global _orchestration_service
    if _orchestration_service is None:
        _orchestration_service = OrchestrationService()
    return _orchestration_service
