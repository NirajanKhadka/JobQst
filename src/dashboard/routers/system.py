import json
from fastapi import APIRouter, Request
from pathlib import Path

router = APIRouter()

IPC_FILE = Path("output/ipc.json")


def get_pause_status() -> bool:
    if not IPC_FILE.exists():
        return False
    try:
        with open(IPC_FILE, "r") as f:
            return json.load(f).get("pause", False)
    except (json.JSONDecodeError, FileNotFoundError):
        return False


def set_pause_status(pause: bool) -> bool:
    try:
        with open(IPC_FILE, "w") as f:
            json.dump({"pause": pause}, f)
        return True
    except Exception:
        return False


@router.get("/api/health")
def health_check():
    return {"status": "healthy"}


@router.get("/api/system-status")
async def get_system_status():
    # This is a simplified version. A real implementation would gather more metrics.
    return {
        "overall_health": {"status": "Healthy"},
        "databases": {"status": "Connected"},
        "system_resources": {"cpu": {"percent_used": 0}},
    }


@router.post("/action/pause")
async def pause():
    if set_pause_status(True):
        return {"status": "paused"}
    return {"status": "error"}


@router.post("/action/resume")
async def resume():
    if set_pause_status(False):
        return {"status": "resumed"}
    return {"status": "error"}


@router.get("/status")
async def status():
    return {"paused": get_pause_status()}
