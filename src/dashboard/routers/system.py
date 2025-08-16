"""
System router for the AutoJobAgent Dashboard API.

This module provides REST API endpoints for system control operations including
health checks, status monitoring, pause/resume functionality, and system metrics.
"""

import json
import logging
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException
from src.services.real_worker_monitor_service import RealWorkerMonitorService
from src.dashboard.websocket import manager as websocket_manager

# Set up router and logging
router = APIRouter()
logger = logging.getLogger(__name__)

# Configuration
IPC_FILE = Path("output/ipc.json")


def get_pause_status() -> bool:
    """
    Get the current pause status from IPC file.
    
    Returns:
        True if system is paused, False otherwise
        
    Note:
        Returns False if IPC file doesn't exist or can't be read.
    """
    if not IPC_FILE.exists():
        return False
    
    try:
        with open(IPC_FILE, "r") as f:
            data = json.load(f)
            return data.get("pause", False)
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        logger.warning(f"Error reading pause status: {e}")
        return False


def set_pause_status(pause: bool) -> bool:
    """
    Set the system pause status in IPC file.
    
    Args:
        pause: True to pause system, False to resume
        
    Returns:
        True if status was set successfully, False otherwise
    """
    try:
        # Ensure output directory exists
        IPC_FILE.parent.mkdir(exist_ok=True)
        
        # Read existing data or create new
        existing_data = {}
        if IPC_FILE.exists():
            try:
                with open(IPC_FILE, "r") as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Update pause status and timestamp
        existing_data.update({
            "pause": pause,
            "last_updated": datetime.now().isoformat(),
            "updated_by": "dashboard"
        })
        
        # Write updated data
        with open(IPC_FILE, "w") as f:
            json.dump(existing_data, f, indent=2)
        
        logger.info(f"System pause status set to: {pause}")
        return True
        
    except Exception as e:
        logger.error(f"Error setting pause status: {e}")
        return False


def get_system_resources() -> Dict[str, Any]:
    """
    Get current system resource usage.
    
    Returns:
        Dictionary containing CPU, memory, and disk usage information
    """
    try:
        return {
            "cpu": {
                "percent_used": round(psutil.cpu_percent(interval=1), 1),
                "cores": psutil.cpu_count()
            },
            "memory": {
                "percent_used": round(psutil.virtual_memory().percent, 1),
                "available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 1)
            },
            "disk": {
                "percent_used": round(psutil.disk_usage('/').percent, 1) if hasattr(psutil.disk_usage('/'), 'percent') else 0,
                "free_gb": round(psutil.disk_usage('/').free / (1024**3), 1) if hasattr(psutil.disk_usage('/'), 'free') else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting system resources: {e}")
        return {
            "cpu": {"percent_used": 0, "cores": 0},
            "memory": {"percent_used": 0, "available_gb": 0, "total_gb": 0},
            "disk": {"percent_used": 0, "free_gb": 0}
        }


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns:
        Dictionary containing health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AutoJobAgent Dashboard"
    }


@router.get("/system-status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get comprehensive system status including health and resource usage.
    
    Returns:
        Dictionary containing system status information
    """
    try:
        resources = get_system_resources()
        pause_status = get_pause_status()
        
        # Determine overall health based on resource usage
        cpu_usage = resources.get("cpu", {}).get("percent_used", 0)
        memory_usage = resources.get("memory", {}).get("percent_used", 0)
        
        if cpu_usage > 90 or memory_usage > 90:
            health_status = "Critical"
        elif cpu_usage > 75 or memory_usage > 75:
            health_status = "Warning"
        else:
            health_status = "Healthy"
        
        return {
            "overall_health": {
                "status": health_status,
                "timestamp": datetime.now().isoformat()
            },
            "system_resources": resources,
            "system_control": {
                "paused": pause_status,
                "ipc_file_exists": IPC_FILE.exists()
            },
            "databases": {
                "status": "Connected",  # Could be Improved with actual DB checks
                "connection_count": 1
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/action/pause")
async def pause_system() -> Dict[str, str]:
    """
    Pause the AutoJobAgent system.
    
    Returns:
        Dictionary containing operation result
    """
    try:
        if set_pause_status(True):
            logger.info("System paused via dashboard API")
            return {
                "status": "paused",
                "message": "System has been paused successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to pause system")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing system: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/action/resume")
async def resume_system() -> Dict[str, str]:
    """
    Resume the AutoJobAgent system.
    
    Returns:
        Dictionary containing operation result
    """
    try:
        if set_pause_status(False):
            logger.info("System resumed via dashboard API")
            return {
                "status": "resumed", 
                "message": "System has been resumed successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to resume system")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming system: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get current system control status.
    
    Returns:
        Dictionary containing current pause status and metadata
    """
    try:
        pause_status = get_pause_status()
        
        # Get additional status info from IPC file
        additional_info = {}
        if IPC_FILE.exists():
            try:
                with open(IPC_FILE, "r") as f:
                    data = json.load(f)
                    additional_info = {
                        "last_updated": data.get("last_updated", "Unknown"),
                        "updated_by": data.get("updated_by", "Unknown")
                    }
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            "paused": pause_status,
            "ipc_file_exists": IPC_FILE.exists(),
            "timestamp": datetime.now().isoformat(),
            **additional_info
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/logs")
async def get_recent_logs(
    lines: int = 50,
    level: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get recent system logs.
    
    Args:
        lines: Number of recent log lines to return (default: 50)
        level: Filter by log level (optional)
        
    Returns:
        Dictionary containing recent log entries
        
    Note:
        This is a placeholder implementation. In production, this would
        read from actual log files or logging system.
    """
    try:
        # Placeholder implementation
        # In a real system, this would read from log files
        recent_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "Dashboard API endpoint accessed",
                "module": "dashboard.system"
            }
        ]
        
        return {
            "logs": recent_logs,
            "total_lines": len(recent_logs),
            "filtered_by_level": level,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


worker_monitor = RealWorkerMonitorService()

@router.post("/start_worker")
async def start_worker(request: Request) -> Dict[str, Any]:
    """
    Start a specific worker service.
    
    Args:
        request: FastAPI request containing service_name and optional profile_name
        
    Returns:
        Dictionary containing operation success status and service name
        
    Raises:
        HTTPException: If service_name is missing from request
    """
    data = await request.json()
    service_name = data.get("service_name")
    profile_name = data.get("profile_name", "default")
    if not service_name:
        raise HTTPException(status_code=400, detail="Missing service_name")
    success = worker_monitor.start_service(service_name, profile_name)
    # Broadcast updated status
    await websocket_manager.broadcast({
        "type": "worker_status_update",
        "worker_status": worker_monitor.get_worker_pool_status()
    })
    return {"success": success, "service_name": service_name}

@router.post("/stop_worker")
async def stop_worker(request: Request) -> Dict[str, Any]:
    """
    Stop a specific worker service.
    
    Args:
        request: FastAPI request containing service_name
        
    Returns:
        Dictionary containing operation success status and service name
        
    Raises:
        HTTPException: If service_name is missing from request
    """
    data = await request.json()
    service_name = data.get("service_name")
    if not service_name:
        raise HTTPException(status_code=400, detail="Missing service_name")
    success = worker_monitor.stop_service(service_name)
    # Broadcast updated status
    await websocket_manager.broadcast({
        "type": "worker_status_update",
        "worker_status": worker_monitor.get_worker_pool_status()
    })
    return {"success": success, "service_name": service_name}

@router.get("/worker_status")
async def worker_status() -> Dict[str, Any]:
    """
    Get the current status of all worker services.
    
    Returns:
        Dictionary containing status information for all workers
    """
    return worker_monitor.get_worker_pool_status()

@router.post("/start_all_workers")
async def start_all_workers(request: Request) -> Dict[str, Any]:
    """
    Start all available worker services.
    
    Args:
        request: FastAPI request containing optional profile_name
        
    Returns:
        Dictionary containing start results for all workers
    """
    profile_name = (await request.json()).get("profile_name", "default")
    results = {}
    for worker in worker_monitor.worker_descriptions.keys():
        results[worker] = worker_monitor.start_service(worker, profile_name)
    await websocket_manager.broadcast({
        "type": "worker_status_update",
        "worker_status": worker_monitor.get_worker_pool_status()
    })
    return {"results": results}

@router.post("/stop_all_workers")
async def stop_all_workers() -> Dict[str, Any]:
    """
    Stop all running worker services.
    
    Returns:
        Dictionary containing stop results for all workers
    """
    results = {}
    for worker in worker_monitor.worker_descriptions.keys():
        results[worker] = worker_monitor.stop_service(worker)
    await websocket_manager.broadcast({
        "type": "worker_status_update",
        "worker_status": worker_monitor.get_worker_pool_status()
    })
    return {"results": results}

@router.post("/restart_all_workers")
async def restart_all_workers(request: Request) -> Dict[str, Any]:
    """
    Restart all worker services by stopping and then starting them.
    
    Args:
        request: FastAPI request containing optional profile_name
        
    Returns:
        Dictionary containing both stop and start results for all workers
    """
    profile_name = (await request.json()).get("profile_name", "default")
    stop_results = {}
    start_results = {}
    for worker in worker_monitor.worker_descriptions.keys():
        stop_results[worker] = worker_monitor.stop_service(worker)
    for worker in worker_monitor.worker_descriptions.keys():
        start_results[worker] = worker_monitor.start_service(worker, profile_name)
    await websocket_manager.broadcast({
        "type": "worker_status_update",
        "worker_status": worker_monitor.get_worker_pool_status()
    })
    return {"stop_results": stop_results, "start_results": start_results}
