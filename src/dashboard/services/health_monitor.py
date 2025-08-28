"""
Health monitor service for dashboard
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HealthMonitor:
    """Health monitoring service"""
    
    def __init__(self):
        """Initialize health monitor"""
        self.name = "health_monitor"
        self._alerts = []
        self._metrics_history = []
        logger.info("Health monitor initialized")
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        try:
            # Get basic health metrics
            health_status = self._get_basic_health()
            
            # Add alerts if any issues
            alerts = self._check_for_alerts(health_status)
            
            return {
                'overall_status': self._determine_overall_status(health_status),
                'components': health_status,
                'alerts': alerts,
                'last_checked': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return self._default_health_status()
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health metrics history"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return [
                metric for metric in self._metrics_history
                if datetime.fromisoformat(metric.get('timestamp', ''))
                >= cutoff_time
            ]
        except Exception as e:
            logger.error(f"Error getting health history: {e}")
            return []
    
    def add_alert(self, alert_type: str, message: str, 
                  severity: str = 'info') -> None:
        """Add a health alert"""
        try:
            alert = {
                'type': alert_type,
                'message': message,
                'severity': severity,
                'timestamp': datetime.now().isoformat(),
                'id': len(self._alerts)
            }
            self._alerts.append(alert)
            
            # Keep only last 100 alerts
            if len(self._alerts) > 100:
                self._alerts = self._alerts[-100:]
                
        except Exception as e:
            logger.error(f"Error adding alert: {e}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        try:
            # Return alerts from last 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            return [
                alert for alert in self._alerts
                if datetime.fromisoformat(alert.get('timestamp', ''))
                >= cutoff_time
            ]
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def clear_alerts(self) -> bool:
        """Clear all alerts"""
        try:
            self._alerts = []
            return True
        except Exception as e:
            logger.error(f"Error clearing alerts: {e}")
            return False
    
    def _get_basic_health(self) -> Dict[str, str]:
        """Get basic health status for components"""
        return {
            'database': 'healthy',
            'scraping_service': 'healthy',
            'processing_service': 'healthy',
            'dashboard': 'healthy',
            'api': 'healthy'
        }
    
    def _check_for_alerts(self, health_status: Dict[str, str]) -> List[str]:
        """Check for any health alerts"""
        alerts = []
        for component, status in health_status.items():
            if status != 'healthy':
                alerts.append(f"{component} is {status}")
        return alerts
    
    def _determine_overall_status(self, health_status: Dict[str, str]) -> str:
        """Determine overall system status"""
        statuses = list(health_status.values())
        if all(status == 'healthy' for status in statuses):
            return 'healthy'
        elif any(status == 'critical' for status in statuses):
            return 'critical'
        elif any(status == 'warning' for status in statuses):
            return 'warning'
        else:
            return 'degraded'
    
    def _default_health_status(self) -> Dict[str, Any]:
        """Default health status"""
        return {
            'overall_status': 'unknown',
            'components': {
                'database': 'unknown',
                'scraping_service': 'unknown',
                'processing_service': 'unknown',
                'dashboard': 'unknown',
                'api': 'unknown'
            },
            'alerts': [],
            'last_checked': datetime.now().isoformat()
        }


# Global instance
_health_monitor_instance = None


def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance"""
    global _health_monitor_instance
    if _health_monitor_instance is None:
        _health_monitor_instance = HealthMonitor()
    return _health_monitor_instance
