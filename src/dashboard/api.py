"""
Dashboard API module - simple REST endpoints for dashboard data
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


def get_dashboard_data(profile_name: str = "default") -> Dict[str, Any]:
    """Get basic dashboard data"""
    try:
        from ..core.user_profile_manager import UserProfileManager
        from ..core.job_database import JobDatabase
        
        # Basic data for dashboard
        job_db = JobDatabase(profile_name)
        stats = job_db.get_job_statistics()
        
        return {
            "status": "success",
            "profile": profile_name,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_jobs_data(profile_name: str = "default", limit: int = 100) -> Dict[str, Any]:
    """Get jobs data for dashboard"""
    try:
        from ..core.job_database import JobDatabase
        
        job_db = JobDatabase(profile_name)
        jobs = job_db.get_recent_jobs(limit=limit)
        
        return {
            "status": "success",
            "jobs": jobs,
            "count": len(jobs),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting jobs data: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_health_status() -> Dict[str, Any]:
    """Get system health status"""
    try:
        from .services.health_monitor import HealthMonitor
        
        monitor = HealthMonitor()
        health = monitor.check_system_health()
        
        return {
            "status": "success",
            "health": health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
