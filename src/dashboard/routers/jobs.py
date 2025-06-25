import json
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List

from src.core.job_database import get_job_db
from src.utils import get_available_profiles

router = APIRouter()

async def get_jobs_enhanced(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    profile: str = "",
    site: str = "",
    search: str = "",
    applied: bool = False,
    experience: str = "",
    table_format: bool = False
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
async def get_jobs(request: Request, limit: int = 50, offset: int = 0, profile: str = "", site: str = "", search: str = "", applied: bool = False):
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
async def apply_to_job(request: Request, job_id: int, profile: str = ""):
    profile_to_use = profile or request.cookies.get("autojob_profile")
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")

    db = get_job_db(profile_to_use)
    job = db.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.mark_applied(job['url'], 'Applied via Dashboard')
    return {"success": True, "message": f"Application initiated for {job.get('title', 'job')}"}

@router.get("/api/sites")
async def get_available_sites(request: Request, profile: str = ""):
    profile_to_use = profile or request.cookies.get("autojob_profile")
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")
        
    db = get_job_db(profile_to_use)
    sites = db.get_unique_sites()
    return {"sites": sites}