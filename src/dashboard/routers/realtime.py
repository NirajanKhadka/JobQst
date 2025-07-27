"""
Real-time monitoring router for the AutoJobAgent Dashboard API.

This module provides REST API endpoints for controlling real-time monitoring,
accessing live metrics, and managing real-time dashboard updates.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from src.dashboard.components.real_time_monitor import real_time_monitor

# Set up router and logging
router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/start")
async def start_real_time_monitoring(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Start real-time monitoring and broadcasting.
    
    Args:
        background_tasks: FastAPI background tasks
        
    Returns:
        Dictionary containing operation result
    """
    try:
        if real_time_monitor.monitoring_active:
            return {
                "status": "already_running",
                "message": "Real-time monitoring is already active",
                "broadcast_interval": real_time_monitor.broadcast_interval,
                "timestamp": datetime.now().isoformat()
            }
        
        # Start monitoring in background
        background_tasks.add_task(real_time_monitor.start_monitoring)
        
        return {
            "status": "started",
            "message": "Real-time monitoring started successfully",
            "broadcast_interval": real_time_monitor.broadcast_interval,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting real-time monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start real-time monitoring: {str(e)}")


@router.post("/stop")
async def stop_real_time_monitoring() -> Dict[str, Any]:
    """
    Stop real-time monitoring and broadcasting.
    
    Returns:
        Dictionary containing operation result
    """
    try:
        if not real_time_monitor.monitoring_active:
            return {
                "status": "not_running",
                "message": "Real-time monitoring is not currently active",
                "timestamp": datetime.now().isoformat()
            }
        
        real_time_monitor.stop_monitoring()
        
        return {
            "status": "stopped",
            "message": "Real-time monitoring stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping real-time monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop real-time monitoring: {str(e)}")


@router.get("/status")
async def get_monitoring_status() -> Dict[str, Any]:
    """
    Get current real-time monitoring status.
    
    Returns:
        Dictionary containing monitoring status information
    """
    try:
        return {
            "monitoring_active": real_time_monitor.monitoring_active,
            "broadcast_interval": real_time_monitor.broadcast_interval,
            "metrics_history_count": len(real_time_monitor.metrics_history),
            "status_history_count": len(real_time_monitor.status_history),
            "last_broadcast_time": real_time_monitor.last_broadcast_time.isoformat() if real_time_monitor.last_broadcast_time else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")


@router.get("/current-metrics")
async def get_current_metrics() -> Dict[str, Any]:
    """
    Get current pipeline metrics.
    
    Returns:
        Dictionary containing current metrics and trends
    """
    try:
        current_metrics = real_time_monitor.get_current_metrics()
        
        if not current_metrics:
            # If no metrics available, collect them now
            metrics = await real_time_monitor._collect_pipeline_metrics()
            current_metrics = {
                "metrics": metrics.__dict__,
                "trends": {"trend": "no_historical_data"}
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            **current_metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current metrics: {str(e)}")


@router.get("/current-status")
async def get_current_status() -> Dict[str, Any]:
    """
    Get current system status.
    
    Returns:
        Dictionary containing current system status and trends
    """
    try:
        current_status = real_time_monitor.get_current_status()
        
        if not current_status:
            # If no status available, collect it now
            status = await real_time_monitor._collect_system_status()
            current_status = {
                "status": status.__dict__,
                "trends": {"trend": "no_historical_data"}
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            **current_status
        }
        
    except Exception as e:
        logger.error(f"Error getting current status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current status: {str(e)}")


@router.get("/metrics-history")
async def get_metrics_history(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of metrics records to return")
) -> Dict[str, Any]:
    """
    Get pipeline metrics history.
    
    Args:
        limit: Maximum number of metrics records to return
        
    Returns:
        Dictionary containing metrics history
    """
    try:
        history = real_time_monitor.get_metrics_history(limit)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "history": history,
            "total_records": len(history),
            "monitoring_active": real_time_monitor.monitoring_active
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics history: {str(e)}")


@router.get("/status-history")
async def get_status_history(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of status records to return")
) -> Dict[str, Any]:
    """
    Get system status history.
    
    Args:
        limit: Maximum number of status records to return
        
    Returns:
        Dictionary containing status history
    """
    try:
        history = real_time_monitor.get_status_history(limit)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "history": history,
            "total_records": len(history),
            "monitoring_active": real_time_monitor.monitoring_active
        }
        
    except Exception as e:
        logger.error(f"Error getting status history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status history: {str(e)}")


@router.get("/dashboard-data")
async def get_dashboard_data() -> Dict[str, Any]:
    """
    Get comprehensive dashboard data for real-time display.
    
    Returns:
        Dictionary containing all dashboard data
    """
    try:
        # Get current metrics and status
        current_metrics = real_time_monitor.get_current_metrics()
        current_status = real_time_monitor.get_current_status()
        
        # If no data available, collect it now
        if not current_metrics:
            metrics = await real_time_monitor._collect_pipeline_metrics()
            current_metrics = {
                "metrics": metrics.__dict__,
                "trends": {"trend": "no_historical_data"}
            }
        
        if not current_status:
            status = await real_time_monitor._collect_system_status()
            current_status = {
                "status": status.__dict__,
                "trends": {"trend": "no_historical_data"}
            }
        
        # Get recent history for charts
        metrics_history = real_time_monitor.get_metrics_history(20)  # Last 20 for charts
        status_history = real_time_monitor.get_status_history(20)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": real_time_monitor.monitoring_active,
            "current_metrics": current_metrics,
            "current_status": current_status,
            "metrics_history": metrics_history,
            "status_history": status_history,
            "data_freshness": {
                "metrics_count": len(metrics_history),
                "status_count": len(status_history),
                "last_update": current_metrics.get("metrics", {}).get("timestamp") if current_metrics else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/live-stats")
async def get_live_stats() -> Dict[str, Any]:
    """
    Get live statistics for dashboard widgets.
    
    Returns:
        Dictionary containing live statistics
    """
    try:
        # Collect fresh metrics and status
        metrics = await real_time_monitor._collect_pipeline_metrics()
        status = await real_time_monitor._collect_system_status()
        
        # Calculate additional stats
        queue_health = "healthy"
        if metrics.jobs_in_deadletter > 50:
            queue_health = "critical"
        elif metrics.jobs_in_deadletter > 10:
            queue_health = "warning"
        
        system_health = status.overall_status
        
        return {
            "timestamp": datetime.now().isoformat(),
            "pipeline_stats": {
                "jobs_in_queue": metrics.jobs_in_queue,
                "jobs_in_deadletter": metrics.jobs_in_deadletter,
                "total_processed": metrics.total_jobs_processed,
                "success_rate": metrics.success_rate,
                "queue_health": queue_health
            },
            "system_stats": {
                "cpu_percent": status.cpu_percent,
                "memory_percent": status.memory_percent,
                "disk_percent": status.disk_percent,
                "system_health": system_health
            },
            "connectivity": {
                "redis_connected": status.redis_connected,
                "database_connected": status.database_connected,
                "websocket_connections": status.websocket_connections
            },
            "overall_health": {
                "status": "healthy" if queue_health == "healthy" and system_health == "healthy" else "degraded",
                "components_healthy": sum([
                    queue_health == "healthy",
                    system_health == "healthy",
                    status.redis_connected,
                    status.database_connected
                ]),
                "total_components": 4
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting live stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get live stats: {str(e)}")


@router.post("/broadcast-test")
async def broadcast_test_message() -> Dict[str, Any]:
    """
    Broadcast a test message to all connected WebSocket clients.
    
    Returns:
        Dictionary containing broadcast result
    """
    try:
        from src.dashboard.websocket import manager as websocket_manager
        
        test_message = {
            "type": "test_broadcast",
            "message": "This is a test broadcast from the real-time monitoring system",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "monitoring_active": real_time_monitor.monitoring_active,
                "connected_clients": len(websocket_manager.active_connections)
            }
        }
        
        clients_reached = await websocket_manager.broadcast(test_message)
        
        return {
            "status": "success",
            "message": "Test broadcast sent successfully",
            "clients_reached": clients_reached,
            "test_message": test_message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting test message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to broadcast test message: {str(e)}")


@router.get("/websocket-info")
async def get_websocket_info() -> Dict[str, Any]:
    """
    Get information about WebSocket connections.
    
    Returns:
        Dictionary containing WebSocket connection information
    """
    try:
        from src.dashboard.websocket import manager as websocket_manager
        
        connection_stats = websocket_manager.get_connection_stats()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "connection_stats": connection_stats,
            "monitoring_integration": {
                "real_time_monitoring_active": real_time_monitor.monitoring_active,
                "broadcast_interval": real_time_monitor.broadcast_interval,
                "last_broadcast": real_time_monitor.last_broadcast_time.isoformat() if real_time_monitor.last_broadcast_time else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get WebSocket info: {str(e)}")