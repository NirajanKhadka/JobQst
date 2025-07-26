"""
FastAPI application for the AutoJobAgent Dashboard.

This module sets up the main FastAPI application with routers, templates,
static files, and WebSocket endpoints for the dashboard functionality.
"""

from typing import Dict, Any
from pathlib import Path
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .routers import jobs, stats, system, profiles
from .websocket import manager, websocket_endpoint

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
