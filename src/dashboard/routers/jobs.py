import json
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Dict, List
import asyncio
import logging

from src.core.job_database import get_job_db
from src.utils import get_available_profiles

# Import our applier functionality
try:
    from applier import JobApplier
    APPLIER_AVAILABLE = True
except ImportError:
    APPLIER_AVAILABLE = False
    logging.warning("Applier module not available - using basic application marking only")

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_jobs_enhanced(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    profile: str = "",
    site: str = "",
    search: str = "",
    applied: bool = False,
    experience: str = "",
    table_format: bool = False,
):
    profile_from_cookie = request.cookies.get("autojob_profile", "")
    profile_to_use = profile or profile_from_cookie or get_available_profiles()[0]

    if not profile_to_use:
        return [] if not table_format else ""

    try:
        db = get_job_db(profile=profile_to_use)
        filters = {"site": site, "applied": applied, "experience": experience}
        filters = {k: v for k, v in filters.items() if v}

        jobs = db.get_jobs(limit=limit, offset=offset, filters=filters, search_query=search)

        if not jobs:
            return {"jobs": [], "total_jobs": 0}

        return {
            "jobs": jobs,
            "total": db.get_job_count(filters=filters, search_query=search),
            "profile": profile_to_use,
        }
    except Exception as e:
        return {"jobs": [], "total": 0, "error": str(e)}


@router.get("/api/jobs")
async def get_jobs(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    profile: str = "",
    site: str = "",
    search: str = "",
    applied: bool = False,
):
    return await get_jobs_enhanced(request, limit, offset, profile, site, search, applied)


@router.get("/api/job/{job_id}")
async def get_job_details(request: Request, job_id: int, profile: str = ""):
    profile_to_use = profile or request.cookies.get("autojob_profile")
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")

    db = get_job_db(profile_to_use)
    job = db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/api/job/{job_id}/apply")
async def apply_to_job(request: Request, job_id: int, profile: str = "", mode: str = "manual"):
    """
    Apply to a job with different modes:
    - manual: Just mark as applied in database (default)
    - hybrid: Open job page and let user apply manually with guidance
    - auto: Full automation (if implemented)
    """
    profile_to_use = profile or request.cookies.get("autojob_profile")
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")

    db = get_job_db(profile_to_use)
    job = db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        if mode == "manual":
            # Simple database marking - user applies manually
            db.update_job_status(job_id, application_status="applied", 
                               processing_notes="Applied via Dashboard (Manual)")
            return {
                "success": True, 
                "message": f"Marked as applied: {job.get('title', 'job')} at {job.get('company', 'company')}",
                "mode": "manual",
                "job_url": job.get("url")
            }
        
        elif mode == "hybrid" and APPLIER_AVAILABLE:
            # Use applier for guided application
            applier = JobApplier(profile_name=profile_to_use)
            
            # Start application process in background
            result = await asyncio.get_event_loop().run_in_executor(
                None, applier.apply_to_job, job.get("url")
            )
            
            if result.get("success"):
                db.update_job_status(job_id, application_status="applied",
                                   processing_notes="Applied via Dashboard (Hybrid)")
                return {
                    "success": True,
                    "message": f"Application process completed for {job.get('title', 'job')}",
                    "mode": "hybrid",
                    "details": result.get("details", "")
                }
            else:
                return {
                    "success": False,
                    "message": f"Application failed: {result.get('error', 'Unknown error')}",
                    "mode": "hybrid"
                }
        
        else:
            # Fallback to manual mode
            db.update_job_status(job_id, application_status="applied", 
                               processing_notes="Applied via Dashboard (Fallback)")
            return {
                "success": True, 
                "message": f"Marked as applied (applier not available): {job.get('title', 'job')}",
                "mode": "manual_fallback",
                "job_url": job.get("url")
            }
            
    except Exception as e:
        logger.error(f"Error applying to job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")


@router.get("/api/application-modes")
async def get_application_modes():
    """Get available application modes for the dashboard."""
    modes = [
        {
            "id": "manual",
            "name": "Manual Apply",
            "description": "Mark as applied and open job page",
            "available": True
        }
    ]
    
    if APPLIER_AVAILABLE:
        modes.append({
            "id": "hybrid",
            "name": "Guided Apply",
            "description": "AI-assisted application with user interaction",
            "available": True
        })
    
    return {"modes": modes, "default": "manual"}


@router.get("/api/sites")
async def get_available_sites(request: Request, profile: str = ""):
    profile_to_use = profile or request.cookies.get("autojob_profile")
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")

    db = get_job_db(profile_to_use)
    sites = db.get_unique_sites()
    return {"sites": sites}
