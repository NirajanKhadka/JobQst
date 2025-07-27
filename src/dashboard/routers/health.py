"""
Health router for the AutoJobAgent Dashboard API.

This module provides REST API endpoints for health monitoring including
pipeline health checks, system diagnostics, and alerting management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from src.health_checks.pipeline_health_monitor import pipeline_health_monitor
from src.health_checks.system_health_checker import SystemHealthChecker
from src.utils.profile_helpers import get_available_profiles

# Set up router and logging
router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/pipeline-health")
async def get_pipeline_health() -> Dict[str, Any]:
    """
    Get comprehensive pipeline health status.
    
    Returns:
        Dictionary containing detailed pipeline health information
    """
    try:
        health_status = await pipeline_health_monitor.perform_comprehensive_health_check()
        return health_status
    except Exception as e:
        logger.error(f"Error getting pipeline health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/system-health")
async def get_system_health(profile: Optional[str] = Query(None, description="Profile to check")) -> Dict[str, Any]:
    """
    Get system health status using the enhanced system health checker.
    
    Args:
        profile: Optional profile name to check specific profile health
        
    Returns:
        Dictionary containing system health information
    """
    try:
        # Get profile for health check
        if profile:
            profiles = get_available_profiles()
            if profile not in profiles:
                raise HTTPException(status_code=404, detail=f"Profile '{profile}' not found")
            profile_data = {"profile_name": profile}
        else:
            profile_data = {"profile_name": "default"}
        
        # Perform system health check
        health_checker = SystemHealthChecker(profile_data)
        health_results = health_checker.run_comprehensive_check()
        
        # Get recommendations
        recommendations = health_checker.get_health_recommendations(health_results)
        
        # Calculate overall health score
        healthy_components = sum(1 for status in health_results.values() if status)
        total_components = len(health_results)
        health_score = (healthy_components / total_components) * 100 if total_components > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "profile": profile_data["profile_name"],
            "overall_health_score": round(health_score, 1),
            "overall_status": "healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "critical",
            "component_results": health_results,
            "recommendations": recommendations,
            "healthy_components": healthy_components,
            "total_components": total_components
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=f"System health check failed: {str(e)}")


@router.get("/health-history")
async def get_health_history(limit: int = Query(50, ge=1, le=200)) -> Dict[str, Any]:
    """
    Get health check history.
    
    Args:
        limit: Maximum number of health check records to return
        
    Returns:
        Dictionary containing health check history
    """
    try:
        history = pipeline_health_monitor.get_health_history(limit)
        summary = pipeline_health_monitor.get_health_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "history": history,
            "summary": summary,
            "total_records": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting health history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve health history: {str(e)}")


@router.get("/health-summary")
async def get_health_summary() -> Dict[str, Any]:
    """
    Get health status summary and trends.
    
    Returns:
        Dictionary containing health summary information
    """
    try:
        summary = pipeline_health_monitor.get_health_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve health summary: {str(e)}")


@router.post("/start-monitoring")
async def start_health_monitoring(
    background_tasks: BackgroundTasks,
    interval_seconds: int = Query(30, ge=10, le=300, description="Monitoring interval in seconds")
) -> Dict[str, Any]:
    """
    Start continuous health monitoring.
    
    Args:
        background_tasks: FastAPI background tasks
        interval_seconds: Monitoring interval in seconds
        
    Returns:
        Dictionary containing operation result
    """
    try:
        if pipeline_health_monitor.monitoring_active:
            return {
                "status": "already_running",
                "message": "Health monitoring is already active",
                "interval_seconds": interval_seconds,
                "timestamp": datetime.now().isoformat()
            }
        
        # Start monitoring in background
        background_tasks.add_task(pipeline_health_monitor.start_monitoring, interval_seconds)
        
        return {
            "status": "started",
            "message": "Health monitoring started successfully",
            "interval_seconds": interval_seconds,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting health monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start health monitoring: {str(e)}")


@router.post("/stop-monitoring")
async def stop_health_monitoring() -> Dict[str, Any]:
    """
    Stop continuous health monitoring.
    
    Returns:
        Dictionary containing operation result
    """
    try:
        if not pipeline_health_monitor.monitoring_active:
            return {
                "status": "not_running",
                "message": "Health monitoring is not currently active",
                "timestamp": datetime.now().isoformat()
            }
        
        pipeline_health_monitor.stop_monitoring()
        
        return {
            "status": "stopped",
            "message": "Health monitoring stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping health monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop health monitoring: {str(e)}")


@router.get("/monitoring-status")
async def get_monitoring_status() -> Dict[str, Any]:
    """
    Get current health monitoring status.
    
    Returns:
        Dictionary containing monitoring status information
    """
    try:
        return {
            "monitoring_active": pipeline_health_monitor.monitoring_active,
            "monitor_id": pipeline_health_monitor.monitor_id,
            "alert_thresholds": pipeline_health_monitor.alert_thresholds,
            "health_history_count": len(pipeline_health_monitor.health_history),
            "last_alert_times": {
                key: time.isoformat() for key, time in pipeline_health_monitor.last_alert_times.items()
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")


@router.get("/diagnostics")
async def run_diagnostics(
    component: Optional[str] = Query(None, description="Specific component to diagnose"),
    deep_check: bool = Query(False, description="Perform deep diagnostic checks")
) -> Dict[str, Any]:
    """
    Run diagnostic checks on system components.
    
    Args:
        component: Specific component to diagnose (redis, database, system, pipeline)
        deep_check: Whether to perform deep diagnostic checks
        
    Returns:
        Dictionary containing diagnostic results
    """
    try:
        diagnostics_start_time = datetime.now()
        
        # Get comprehensive health check
        health_status = await pipeline_health_monitor.perform_comprehensive_health_check()
        
        diagnostics = {
            "timestamp": diagnostics_start_time.isoformat(),
            "component_filter": component,
            "deep_check": deep_check,
            "diagnostics": {}
        }
        
        # Filter by component if specified
        if component:
            if component in health_status["components"]:
                diagnostics["diagnostics"][component] = health_status["components"][component]
            else:
                raise HTTPException(status_code=404, detail=f"Component '{component}' not found")
        else:
            diagnostics["diagnostics"] = health_status["components"]
        
        # Add additional diagnostic information if deep check is requested
        if deep_check:
            diagnostics["deep_diagnostics"] = {
                "system_info": health_status.get("system_info", {}),
                "performance_metrics": health_status.get("performance_metrics", {}),
                "recent_alerts": health_status.get("alerts", [])
            }
        
        diagnostics["duration_seconds"] = (datetime.now() - diagnostics_start_time).total_seconds()
        
        return diagnostics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running diagnostics: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnostics failed: {str(e)}")


@router.get("/alert-history")
async def get_alert_history(
    severity: Optional[str] = Query(None, description="Filter by alert severity"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of alerts to return")
) -> Dict[str, Any]:
    """
    Get alert history from health monitoring.
    
    Args:
        severity: Filter alerts by severity (critical, degraded, warning)
        limit: Maximum number of alerts to return
        
    Returns:
        Dictionary containing alert history
    """
    try:
        # Get recent health history which contains alerts
        history = pipeline_health_monitor.get_health_history(limit * 2)  # Get more to filter
        
        alerts = []
        for check in history:
            if "alerts" in check["status"] and check["status"]["alerts"]:
                for alert in check["status"]["alerts"]:
                    if not severity or alert.get("severity") == severity:
                        alerts.append({
                            "check_timestamp": check["timestamp"],
                            **alert
                        })
        
        # Sort by timestamp and limit
        alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        alerts = alerts[:limit]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "total_alerts": len(alerts),
            "severity_filter": severity,
            "alert_counts": {
                "critical": len([a for a in alerts if a.get("severity") == "critical"]),
                "degraded": len([a for a in alerts if a.get("severity") == "degraded"]),
                "warning": len([a for a in alerts if a.get("severity") == "warning"])
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alert history: {str(e)}")


@router.post("/test-alert")
async def test_alert_system() -> Dict[str, Any]:
    """
    Test the alert system by sending a test alert.
    
    Returns:
        Dictionary containing test result
    """
    try:
        test_alert = {
            "type": "test_alert",
            "severity": "warning",
            "message": "This is a test alert from the health monitoring system",
            "timestamp": datetime.now().isoformat(),
            "component": "health_monitor",
            "details": {
                "test": True,
                "monitor_id": pipeline_health_monitor.monitor_id
            }
        }
        
        await pipeline_health_monitor._send_alert(test_alert)
        
        return {
            "status": "success",
            "message": "Test alert sent successfully",
            "alert": test_alert,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending test alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test alert: {str(e)}")