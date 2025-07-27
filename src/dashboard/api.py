"""
FastAPI application for the AutoJobAgent Dashboard.

This module sets up the main FastAPI application with routers, templates,
static files, and WebSocket endpoints for the dashboard functionality.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging
import uuid
import json
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .routers import jobs, stats, system, profiles, health, realtime, errors, queue
from .websocket import manager, websocket_endpoint
from src.pipeline.redis_queue import RedisQueue
from src.core.job_database import get_job_db

# Set up logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AutoJobAgent Dashboard",
    description="Real-time dashboard for job automation and application tracking",
    version="1.0.0"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Set up templates and static files
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"Mounted static files from {STATIC_DIR}")
else:
    logger.warning(f"Static directory not found: {STATIC_DIR}")

# Include routers
app.include_router(jobs.router, prefix="/api", tags=["jobs"])
app.include_router(stats.router, prefix="/api", tags=["stats"])
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(profiles.router, prefix="/api", tags=["profiles"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(realtime.router, prefix="/api/realtime", tags=["realtime"])
app.include_router(errors.router, prefix="/api/errors", tags=["errors"])
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])

# WebSocket endpoint
app.add_websocket_route("/ws", websocket_endpoint)

logger.info("Dashboard API initialized with all routers and endpoints")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """
    Render the main dashboard page.
    
    Args:
        request: FastAPI request object
        
    Returns:
        HTML response with the dashboard template
        
    Raises:
        HTTPException: If template cannot be rendered
    """
    try:
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering dashboard template: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring.
    
    Returns:
        Dictionary containing health status information
    """
    return {
        "status": "healthy",
        "service": "AutoJobAgent Dashboard",
        "websocket_connections": len(manager.active_connections),
        "routes_loaded": len(app.routes)
    }


# Redis Monitoring Endpoints
@app.get("/api/redis/queue-status")
async def get_redis_queue_status(queue_name: str = "jobs:main") -> Dict[str, Any]:
    """
    Get Redis queue statistics and status.
    
    Args:
        queue_name: Name of the Redis queue to check
        
    Returns:
        Dictionary containing queue statistics
    """
    try:
        redis_queue = RedisQueue(queue_name=queue_name)
        await redis_queue.connect()
        
        # Get queue length
        queue_length = await redis_queue.redis.llen(queue_name)
        deadletter_length = await redis_queue.redis.llen(redis_queue.deadletter_name)
        
        # Get Redis info
        redis_info = await redis_queue.redis.info()
        
        # Calculate processing metrics
        total_processed = queue_length + deadletter_length
        success_rate = ((queue_length / total_processed) * 100) if total_processed > 0 else 100
        
        await redis_queue.close()
        
        return {
            "queue_name": queue_name,
            "queue_length": queue_length,
            "deadletter_length": deadletter_length,
            "total_processed": total_processed,
            "success_rate": round(success_rate, 2),
            "redis_status": {
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory": redis_info.get("used_memory_human", "Unknown"),
                "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
                "redis_version": redis_info.get("redis_version", "Unknown")
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting Redis queue status: {e}")
        raise HTTPException(status_code=500, detail=f"Redis connection error: {str(e)}")


@app.get("/api/redis/dead-letter")
async def get_dead_letter_queue(queue_name: str = "jobs:main", limit: int = 50) -> Dict[str, Any]:
    """
    Get dead-letter queue contents and management interface.
    
    Args:
        queue_name: Name of the main Redis queue
        limit: Maximum number of dead-letter items to return
        
    Returns:
        Dictionary containing dead-letter queue data
    """
    try:
        redis_queue = RedisQueue(queue_name=queue_name)
        await redis_queue.connect()
        
        # Get dead-letter queue items
        deadletter_items = []
        deadletter_length = await redis_queue.redis.llen(redis_queue.deadletter_name)
        
        if deadletter_length > 0:
            # Get items from dead-letter queue (up to limit)
            items = await redis_queue.redis.lrange(redis_queue.deadletter_name, 0, limit - 1)
            for item in items:
                try:
                    job_data = json.loads(item)
                    deadletter_items.append({
                        "job_id": job_data.get("job_id", "Unknown"),
                        "title": job_data.get("title", "Unknown"),
                        "company": job_data.get("company", "Unknown"),
                        "error_reason": job_data.get("error_reason", "Processing failed"),
                        "retry_count": job_data.get("retry_count", 0),
                        "failed_at": job_data.get("failed_at", datetime.now().isoformat()),
                        "raw_data": item
                    })
                except json.JSONDecodeError:
                    deadletter_items.append({
                        "job_id": "Invalid",
                        "title": "Corrupted Data",
                        "company": "Unknown",
                        "error_reason": "JSON decode error",
                        "retry_count": 0,
                        "failed_at": datetime.now().isoformat(),
                        "raw_data": item
                    })
        
        await redis_queue.close()
        
        return {
            "queue_name": queue_name,
            "deadletter_name": redis_queue.deadletter_name,
            "total_items": deadletter_length,
            "items_returned": len(deadletter_items),
            "items": deadletter_items,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dead-letter queue: {e}")
        raise HTTPException(status_code=500, detail=f"Redis connection error: {str(e)}")


@app.post("/api/redis/dead-letter/retry")
async def retry_dead_letter_job(request: Request) -> Dict[str, Any]:
    """
    Retry a job from the dead-letter queue.
    
    Args:
        request: FastAPI request containing job_index to retry
        
    Returns:
        Dictionary containing retry operation result
    """
    try:
        data = await request.json()
        job_index = data.get("job_index", 0)
        queue_name = data.get("queue_name", "jobs:main")
        
        redis_queue = RedisQueue(queue_name=queue_name)
        await redis_queue.connect()
        
        # Get the job from dead-letter queue
        job_data = await redis_queue.redis.lindex(redis_queue.deadletter_name, job_index)
        
        if not job_data:
            await redis_queue.close()
            raise HTTPException(status_code=404, detail="Job not found in dead-letter queue")
        
        # Parse and modify job data
        try:
            job_dict = json.loads(job_data)
            job_dict["retry_count"] = job_dict.get("retry_count", 0) + 1
            job_dict["retried_at"] = datetime.now().isoformat()
            job_dict["correlation_id"] = str(uuid.uuid4())
            
            # Remove from dead-letter and add back to main queue
            await redis_queue.redis.lrem(redis_queue.deadletter_name, 1, job_data)
            await redis_queue.enqueue(job_dict)
            
            await redis_queue.close()
            
            return {
                "success": True,
                "message": "Job successfully moved back to processing queue",
                "job_id": job_dict.get("job_id", "Unknown"),
                "retry_count": job_dict.get("retry_count", 1),
                "timestamp": datetime.now().isoformat()
            }
            
        except json.JSONDecodeError:
            await redis_queue.close()
            raise HTTPException(status_code=400, detail="Corrupted job data in dead-letter queue")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying dead-letter job: {e}")
        raise HTTPException(status_code=500, detail=f"Retry operation failed: {str(e)}")


@app.delete("/api/redis/dead-letter/clear")
async def clear_dead_letter_queue(queue_name: str = "jobs:main") -> Dict[str, Any]:
    """
    Clear all items from the dead-letter queue.
    
    Args:
        queue_name: Name of the main Redis queue
        
    Returns:
        Dictionary containing clear operation result
    """
    try:
        redis_queue = RedisQueue(queue_name=queue_name)
        await redis_queue.connect()
        
        # Get count before clearing
        items_count = await redis_queue.redis.llen(redis_queue.deadletter_name)
        
        # Clear the dead-letter queue
        await redis_queue.redis.delete(redis_queue.deadletter_name)
        
        await redis_queue.close()
        
        return {
            "success": True,
            "message": f"Dead-letter queue cleared successfully",
            "items_removed": items_count,
            "queue_name": queue_name,
            "deadletter_name": redis_queue.deadletter_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing dead-letter queue: {e}")
        raise HTTPException(status_code=500, detail=f"Clear operation failed: {str(e)}")


@app.get("/api/pipeline/health")
async def get_pipeline_health() -> Dict[str, Any]:
    """
    Get overall pipeline health check including Redis, database, and workers.
    
    Returns:
        Dictionary containing comprehensive pipeline health status
    """
    try:
        health_status = {
            "overall_status": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat(),
            "correlation_id": str(uuid.uuid4())
        }
        
        # Check Redis connectivity
        try:
            redis_queue = RedisQueue(queue_name="jobs:main")
            await redis_queue.connect()
            redis_info = await redis_queue.redis.info()
            await redis_queue.close()
            
            health_status["components"]["redis"] = {
                "status": "healthy",
                "connected_clients": redis_info.get("connected_clients", 0),
                "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
                "memory_usage": redis_info.get("used_memory_human", "Unknown")
            }
        except Exception as e:
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check Database connectivity
        try:
            db = get_job_db()
            job_count = db.get_job_count()
            
            health_status["components"]["database"] = {
                "status": "healthy",
                "total_jobs": job_count,
                "connection_pool_size": 5  # From ModernJobDatabase
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check WebSocket connections
        health_status["components"]["websocket"] = {
            "status": "healthy",
            "active_connections": len(manager.active_connections),
            "total_messages_sent": manager.get_connection_stats().get("total_messages_sent", 0)
        }
        
        # Determine overall status
        unhealthy_components = [
            comp for comp, data in health_status["components"].items()
            if data.get("status") == "unhealthy"
        ]
        
        if unhealthy_components:
            health_status["overall_status"] = "critical" if len(unhealthy_components) > 1 else "degraded"
            health_status["unhealthy_components"] = unhealthy_components
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting pipeline health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/api/pipeline/metrics")
async def get_pipeline_metrics(time_range: str = "1h") -> Dict[str, Any]:
    """
    Get pipeline performance metrics including throughput and success rates.
    
    Args:
        time_range: Time range for metrics (1h, 24h, 7d)
        
    Returns:
        Dictionary containing pipeline performance metrics
    """
    try:
        # This would typically integrate with a metrics collection system
        # For now, we'll provide basic metrics from database and Redis
        
        db = get_job_db()
        redis_queue = RedisQueue(queue_name="jobs:main")
        await redis_queue.connect()
        
        # Get basic metrics
        total_jobs = db.get_job_count()
        queue_length = await redis_queue.redis.llen("jobs:main")
        deadletter_length = await redis_queue.redis.llen("jobs:main:deadletter")
        
        # Calculate success rate
        processed_jobs = total_jobs
        failed_jobs = deadletter_length
        success_rate = ((processed_jobs - failed_jobs) / processed_jobs * 100) if processed_jobs > 0 else 100
        
        # Get recent job stats
        job_stats = db.get_job_stats()
        
        await redis_queue.close()
        
        metrics = {
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": str(uuid.uuid4()),
            "throughput": {
                "total_jobs_processed": processed_jobs,
                "jobs_in_queue": queue_length,
                "jobs_failed": failed_jobs,
                "success_rate_percent": round(success_rate, 2),
                "average_processing_time": 0.0  # Would be calculated from actual metrics
            },
            "performance": {
                "queue_processing_rate": 0.0,  # Jobs per minute
                "error_rate_percent": round((failed_jobs / processed_jobs * 100) if processed_jobs > 0 else 0, 2),
                "system_resource_usage": {
                    "cpu_percent": 0.0,  # Would integrate with system monitoring
                    "memory_percent": 0.0,
                    "disk_usage_percent": 0.0
                }
            },
            "database_metrics": {
                "total_jobs": job_stats.get("total_jobs", 0),
                "applied_jobs": job_stats.get("applied_jobs", 0),
                "pending_jobs": job_stats.get("pending_jobs", 0),
                "duplicate_jobs": job_stats.get("duplicate_jobs", 0)
            },
            "redis_metrics": {
                "main_queue_length": queue_length,
                "deadletter_queue_length": deadletter_length,
                "total_queued_jobs": queue_length + deadletter_length
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting pipeline metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> HTMLResponse:
    """
    Handle 404 errors with a custom page.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception details
        
    Returns:
        HTML response with 404 page
    """
    try:
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": "Page not found", "status_code": 404}
        )
    except Exception:
        # Fallback if template is missing
        return HTMLResponse(
            content="<h1>404 - Page Not Found</h1>",
            status_code=404
        )


def create_app() -> FastAPI:
    """
    Application factory function.
    
    Returns:
        Configured FastAPI application instance
    """
    return app


if __name__ == "__main__":
    import sys

    if sys.argv[0].endswith("api.py"):
        print("[ERROR] Do not run this file directly. Use: python -m src.dashboard.api")
        sys.exit(1)
    
    import uvicorn
    
    logger.info("Starting dashboard API server on http://0.0.0.0:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
