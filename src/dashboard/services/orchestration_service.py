"""
Orchestration service for dashboard
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ApplicationStatus(Enum):
    """Application status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"

try:
    # Bridge to existing orchestration service
    from ...services.orchestration_service import orchestration_service
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    logger.warning("Main orchestration service not available")
    ORCHESTRATION_AVAILABLE = False
    orchestration_service = None


class OrchestrationService:
    """Orchestration service for dashboard"""
    
    def __init__(self):
        """Initialize orchestration service"""
        self.name = "orchestration_service"
        self._service = orchestration_service if ORCHESTRATION_AVAILABLE else None
        logger.info("Dashboard orchestration service initialized")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        if self._service:
            try:
                return self._service.get_service_status()
            except Exception as e:
                logger.error(f"Error getting service status: {e}")
                return self._default_status()
        return self._default_status()
    
    def get_worker_status(self) -> Dict[str, Any]:
        """Get worker status"""
        if self._service:
            try:
                return self._service.get_worker_status()
            except Exception as e:
                logger.error(f"Error getting worker status: {e}")
                return self._default_worker_status()
        return self._default_worker_status()
    
    def start_operation(self, operation_type: str, 
                       profile_name: str = 'Nirajan') -> Dict[str, Any]:
        """Start an operation"""
        if self._service:
            try:
                return self._service.start_operation(operation_type, profile_name)
            except Exception as e:
                logger.error(f"Error starting operation: {e}")
                return {'success': False, 'message': str(e)}
        return {'success': False, 'message': 'Service not available'}
    
    def stop_operation(self, operation_id: str) -> Dict[str, Any]:
        """Stop an operation"""
        if self._service:
            try:
                return self._service.stop_operation(operation_id)
            except Exception as e:
                logger.error(f"Error stopping operation: {e}")
                return {'success': False, 'message': str(e)}
        return {'success': False, 'message': 'Service not available'}
    
    def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get operation status"""
        if self._service:
            try:
                return self._service.get_operation_status(operation_id)
            except Exception as e:
                logger.error(f"Error getting operation status: {e}")
                return self._default_operation_status()
        return self._default_operation_status()
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent operations"""
        if self._service:
            try:
                return self._service.get_recent_operations(limit)
            except Exception as e:
                logger.error(f"Error getting recent operations: {e}")
                return []
        return []
    
    def _default_status(self) -> Dict[str, Any]:
        """Default service status"""
        return {
            'status': 'unknown',
            'uptime': 0,
            'last_updated': datetime.now().isoformat(),
            'active_operations': 0
        }
    
    def _default_worker_status(self) -> Dict[str, Any]:
        """Default worker status"""
        return {
            'active_workers': 0,
            'idle_workers': 0,
            'total_workers': 0,
            'queue_size': 0
        }
    
    def _default_operation_status(self) -> Dict[str, Any]:
        """Default operation status"""
        return {
            'status': 'unknown',
            'progress': 0,
            'started_at': None,
            'estimated_completion': None
        }


# Global instance
_orchestration_service_instance = None


def get_orchestration_service() -> OrchestrationService:
    """Get the global orchestration service instance"""
    global _orchestration_service_instance
    if _orchestration_service_instance is None:
        _orchestration_service_instance = OrchestrationService()
    return _orchestration_service_instance

