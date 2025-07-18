from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .routers import jobs, stats, system
from .websocket import manager, websocket_endpoint

app = FastAPI(title="AutoJobAgent Dashboard")

# Set up paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Set up templates and static files
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers
app.include_router(jobs.router)
app.include_router(stats.router)
app.include_router(system.router)

# WebSocket endpoint
app.add_websocket_route("/ws", websocket_endpoint)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


if __name__ == "__main__":
    import sys

    if sys.argv[0].endswith("api.py"):
        print("[ERROR] Do not run this file directly. Use: python -m src.dashboard.api")
        sys.exit(1)
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
