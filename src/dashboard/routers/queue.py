"""
Queue management router for the AutoJobAgent Dashboard API.

This module provides REST API endpoints for queue management operations
including queue monitoring, job manipulation, and batch operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Path, Request

from src.dashboard.components.queue_manager import queue_manager, QueueOperation

# Set up router and logging
router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_queue_stats(
    queue_name: Optional[str] = Query(None, description="Name of the queue to analyze")
) -> Dict[str, Any]:
    """
    Get comprehensive queue statistics.
    
    Args:
        queue_name: Name of the queue to analyze
        
    Returns:
        Dictionary containing detailed queue statistics
    """
    try:
        stats = await queue_manager.get_queue_stats(queue_name)
        return {
            "timestamp": datetime.now().isoformat(),
            "stats": stats.__dict__
        }
        
    except Exception as e:
        logger.error(f"Error getting queue stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")


@router.get("/contents")
async def get_queue_contents(
    queue_name: Optional[str] = Query(None, description="Name of the queue"),
    queue_type: str = Query("main", description="Type of queue (main or deadletter)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> Dict[str, Any]:
    """
    Get contents of a queue with pagination.
    
    Args:
        queue_name: Name of the queue
        queue_type: Type of queue ("main" or "deadletter")
        limit: Maximum number of items to return
        offset: Number of items to skip
        
    Returns:
        Dictionary containing queue contents
    """
    try:
        if queue_type not in ["main", "deadletter"]:
            raise HTTPException(status_code=400, detail="queue_type must be 'main' or 'deadletter'")
        
        contents = await queue_manager.get_queue_contents(
            queue_name=queue_name,
            queue_type=queue_type,
            limit=limit,
            offset=offset
        )
        
        return contents
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue contents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue contents: {str(e)}")


@router.post("/batch-operation")
async def perform_batch_operation(request: Request) -> Dict[str, Any]:
    """
    Perform batch operations on queue items.
    
    Request body should contain:
    - operation: Type of operation (move_to_main, move_to_deadletter, delete, retry)
    - job_positions: List of job positions to operate on
    - queue_name: Optional queue name
    - source_queue_type: Source queue type ("main" or "deadletter")
    - target_queue_type: Optional target queue type for move operations
    
    Returns:
        Dictionary containing batch operation results
    """
    try:
        data = await request.json()
        
        # Validate required fields
        if "operation" not in data:
            raise HTTPException(status_code=400, detail="Missing required field: operation")
        if "job_positions" not in data:
            raise HTTPException(status_code=400, detail="Missing required field: job_positions")
        
        # Parse operation
        try:
            operation = QueueOperation(data["operation"])
        except ValueError:
            valid_operations = [op.value for op in QueueOperation]
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid operation. Valid operations: {valid_operations}"
            )
        
        # Validate job positions
        job_positions = data["job_positions"]
        if not isinstance(job_positions, list) or not job_positions:
            raise HTTPException(status_code=400, detail="job_positions must be a non-empty list")
        
        # Validate position values
        for pos in job_positions:
            if not isinstance(pos, int) or pos < 0:
                raise HTTPException(status_code=400, detail="All job positions must be non-negative integers")
        
        # Get optional parameters
        queue_name = data.get("queue_name")
        source_queue_type = data.get("source_queue_type", "main")
        target_queue_type = data.get("target_queue_type")
        
        # Validate queue types
        if source_queue_type not in ["main", "deadletter"]:
            raise HTTPException(status_code=400, detail="source_queue_type must be 'main' or 'deadletter'")
        
        if target_queue_type and target_queue_type not in ["main", "deadletter"]:
            raise HTTPException(status_code=400, detail="target_queue_type must be 'main' or 'deadletter'")
        
        # Perform batch operation
        result = await queue_manager.perform_batch_operation(
            operation=operation,
            job_positions=job_positions,
            queue_name=queue_name,
            source_queue_type=source_queue_type,
            target_queue_type=target_queue_type
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "result": result.__dict__
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing batch operation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to perform batch operation: {str(e)}")


@router.delete("/clear")
async def clear_queue(
    queue_name: Optional[str] = Query(None, description="Name of the queue"),
    queue_type: str = Query("deadletter", description="Type of queue to clear (main or deadletter)")
) -> Dict[str, Any]:
    """
    Clear all items from a queue.
    
    Args:
        queue_name: Name of the queue
        queue_type: Type of queue to clear ("main" or "deadletter")
        
    Returns:
        Dictionary containing clear operation results
    """
    try:
        if queue_type not in ["main", "deadletter"]:
            raise HTTPException(status_code=400, detail="queue_type must be 'main' or 'deadletter'")
        
        # Add safety check for main queue
        if queue_type == "main":
            logger.warning(f"Clearing main queue requested for {queue_name or 'default'}")
        
        result = await queue_manager.clear_queue(
            queue_name=queue_name,
            queue_type=queue_type
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear queue: {str(e)}")


@router.post("/reorder")
async def reorder_queue(request: Request) -> Dict[str, Any]:
    """
    Reorder queue items based on criteria.
    
    Request body should contain:
    - queue_name: Optional queue name
    - new_order: Optional specific order of positions
    - sort_by: Sorting criteria ("priority", "retry_count", "queued_at")
    
    Returns:
        Dictionary containing reorder operation results
    """
    try:
        data = await request.json()
        
        queue_name = data.get("queue_name")
        new_order = data.get("new_order")
        sort_by = data.get("sort_by", "priority")
        
        # Validate sort_by
        valid_sort_options = ["priority", "retry_count", "queued_at"]
        if sort_by not in valid_sort_options:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid sort_by option. Valid options: {valid_sort_options}"
            )
        
        # Validate new_order if provided
        if new_order is not None:
            if not isinstance(new_order, list):
                raise HTTPException(status_code=400, detail="new_order must be a list")
            
            for pos in new_order:
                if not isinstance(pos, int) or pos < 0:
                    raise HTTPException(status_code=400, detail="All positions in new_order must be non-negative integers")
        
        result = await queue_manager.reorder_queue(
            queue_name=queue_name,
            new_order=new_order,
            sort_by=sort_by
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering queue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reorder queue: {str(e)}")


@router.get("/operations/history")
async def get_operation_history(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of operations to return")
) -> Dict[str, Any]:
    """
    Get history of queue operations.
    
    Args:
        limit: Maximum number of operations to return
        
    Returns:
        Dictionary containing operation history
    """
    try:
        history = await queue_manager.get_operation_history(limit)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "history": history,
            "total_operations": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting operation history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get operation history: {str(e)}")


@router.get("/dashboard-data")
async def get_queue_dashboard_data(
    queue_name: Optional[str] = Query(None, description="Name of the queue")
) -> Dict[str, Any]:
    """
    Get comprehensive queue data for dashboard display.
    
    Args:
        queue_name: Name of the queue
        
    Returns:
        Dictionary containing all queue dashboard data
    """
    try:
        # Get queue statistics
        stats = await queue_manager.get_queue_stats(queue_name)
        
        # Get recent contents from both queues
        main_contents = await queue_manager.get_queue_contents(
            queue_name=queue_name,
            queue_type="main",
            limit=10,
            offset=0
        )
        
        deadletter_contents = await queue_manager.get_queue_contents(
            queue_name=queue_name,
            queue_type="deadletter",
            limit=10,
            offset=0
        )
        
        # Get recent operation history
        operation_history = await queue_manager.get_operation_history(10)
        
        # Compile dashboard data
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "queue_name": queue_name or queue_manager.default_queue,
            "stats": stats.__dict__,
            "main_queue": {
                "total_items": main_contents["total_items"],
                "recent_items": main_contents["items"][:5],  # Show only first 5
                "health": stats.queue_health
            },
            "deadletter_queue": {
                "total_items": deadletter_contents["total_items"],
                "recent_items": deadletter_contents["items"][:5],  # Show only first 5
                "needs_attention": deadletter_contents["total_items"] > 10
            },
            "recent_operations": operation_history[:5],  # Show only last 5 operations
            "alerts": [],
            "quick_actions": [
                {
                    "action": "clear_deadletter",
                    "label": "Clear Dead-letter Queue",
                    "enabled": deadletter_contents["total_items"] > 0,
                    "severity": "warning"
                },
                {
                    "action": "retry_failed",
                    "label": "Retry Failed Jobs",
                    "enabled": deadletter_contents["total_items"] > 0,
                    "severity": "info"
                },
                {
                    "action": "reorder_queue",
                    "label": "Optimize Queue Order",
                    "enabled": main_contents["total_items"] > 1,
                    "severity": "info"
                }
            ]
        }
        
        # Add alerts based on queue conditions
        if stats.deadletter_queue_length > 50:
            dashboard_data["alerts"].append({
                "type": "high_deadletter_count",
                "severity": "critical",
                "message": f"Dead-letter queue has {stats.deadletter_queue_length} items - immediate attention required"
            })
        elif stats.deadletter_queue_length > 10:
            dashboard_data["alerts"].append({
                "type": "moderate_deadletter_count",
                "severity": "warning",
                "message": f"Dead-letter queue has {stats.deadletter_queue_length} items - review recommended"
            })
        
        if stats.main_queue_length > 1000:
            dashboard_data["alerts"].append({
                "type": "high_queue_backlog",
                "severity": "warning",
                "message": f"Main queue has {stats.main_queue_length} items - consider scaling processing"
            })
        
        if stats.queue_health in ["critical", "degraded"]:
            dashboard_data["alerts"].append({
                "type": "queue_health_issue",
                "severity": "critical" if stats.queue_health == "critical" else "warning",
                "message": f"Queue health is {stats.queue_health} - investigation needed"
            })
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting queue dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue dashboard data: {str(e)}")


@router.get("/health")
async def get_queue_health(
    queue_name: Optional[str] = Query(None, description="Name of the queue")
) -> Dict[str, Any]:
    """
    Get queue health status and recommendations.
    
    Args:
        queue_name: Name of the queue
        
    Returns:
        Dictionary containing queue health information
    """
    try:
        stats = await queue_manager.get_queue_stats(queue_name)
        
        # Calculate health metrics
        health_score = 100
        issues = []
        recommendations = []
        
        # Check dead-letter queue
        if stats.deadletter_queue_length > 50:
            health_score -= 40
            issues.append("Critical: High number of failed jobs in dead-letter queue")
            recommendations.append("Investigate and resolve dead-letter queue items immediately")
        elif stats.deadletter_queue_length > 10:
            health_score -= 20
            issues.append("Warning: Moderate number of failed jobs in dead-letter queue")
            recommendations.append("Review and retry failed jobs in dead-letter queue")
        
        # Check main queue backlog
        if stats.main_queue_length > 1000:
            health_score -= 20
            issues.append("Warning: High queue backlog")
            recommendations.append("Consider scaling processing capacity")
        elif stats.main_queue_length > 500:
            health_score -= 10
            issues.append("Info: Moderate queue backlog")
            recommendations.append("Monitor processing rate")
        
        # Check processing rate
        if stats.processing_rate < 1.0 and stats.main_queue_length > 100:
            health_score -= 15
            issues.append("Warning: Low processing rate with queue backlog")
            recommendations.append("Check worker availability and performance")
        
        # Determine overall health level
        if health_score >= 90:
            health_level = "excellent"
        elif health_score >= 75:
            health_level = "good"
        elif health_score >= 60:
            health_level = "fair"
        elif health_score >= 40:
            health_level = "poor"
        else:
            health_level = "critical"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "queue_name": queue_name or queue_manager.default_queue,
            "health_score": max(0, health_score),
            "health_level": health_level,
            "queue_health": stats.queue_health,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": {
                "main_queue_length": stats.main_queue_length,
                "deadletter_queue_length": stats.deadletter_queue_length,
                "processing_rate": stats.processing_rate,
                "average_wait_time": stats.average_wait_time
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting queue health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue health: {str(e)}")