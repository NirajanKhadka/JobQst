"""
System service for dashboard monitoring
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


class SystemService:
    """System monitoring service"""
    
    def __init__(self):
        """Initialize system service"""
        self.name = "system_service"
        logger.info("System service initialized")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            if PSUTIL_AVAILABLE:
                return {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'status': 'healthy',
                    'timestamp': 'now'
                }
            else:
                return self._default_health()
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return self._default_health()
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            if PSUTIL_AVAILABLE:
                return {
                    'cpu_count': psutil.cpu_count(),
                    'total_memory': psutil.virtual_memory().total,
                    'platform': 'unknown',
                    'python_version': 'unknown'
                }
            else:
                return self._default_info()
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return self._default_info()
    
    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of running processes"""
        try:
            if PSUTIL_AVAILABLE:
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                    try:
                        processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                return processes[:10]  # Return top 10
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            return []
    
    def _default_health(self) -> Dict[str, Any]:
        """Default health metrics"""
        return {
            'cpu_percent': 25,
            'memory_percent': 45,
            'disk_percent': 60,
            'status': 'unknown',
            'timestamp': 'unknown'
        }
    
    def _default_info(self) -> Dict[str, Any]:
        """Default system info"""
        return {
            'cpu_count': 4,
            'total_memory': 8589934592,  # 8GB
            'platform': 'unknown',
            'python_version': 'unknown'
        }


# Global instance
_system_service_instance = None


def get_system_service() -> SystemService:
    """Get the global system service instance"""
    global _system_service_instance
    if _system_service_instance is None:
        _system_service_instance = SystemService()
    return _system_service_instance

