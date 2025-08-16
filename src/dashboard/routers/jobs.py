"""
Jobs router for the AutoJobAgent Dashboard API.

This module provides REST API endpoints for job-related operations including
job listing, filtering, details retrieval, and job application functionality.
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query
from pydantic import BaseModel

from src.core.job_database import get_job_db
from src.utils.profile_helpers import get_available_profiles

# Import our applier functionality
try:
    from src.job_applier.job_applier import JobApplier
    APPLIER_AVAILABLE = True
except ImportError:
    try:
        from src.ats.Improved_universal_applier import ImprovedUniversalApplier as JobApplier
        APPLIER_AVAILABLE = True
    except ImportError:
        APPLIER_AVAILABLE = False
        logging.warning("Applier module not available - using basic application marking only")

# Set up router and logging
router = APIRouter()
logger = logging.getLogger(__name__)


class JobApplicationRequest(BaseModel):
    """Request model for job application."""
    mode: str = "manual"
    notes: Optional[str] = None


class JobFilters(BaseModel):
    """Model for job filtering parameters."""
    site: Optional[str] = None
    applied: Optional[bool] = None
    experience: Optional[str] = None
    search: Optional[str] = None


async def get_jobs_Improved(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    profile: str = "",
    site: str = "",
    search: str = "",
    applied: Optional[bool] = None,
    experience: str = "",
    table_format: bool = False,
) -> Dict[str, Any]:
    """
    Enhanced job retrieval with filtering and pagination.
    
    Args:
        request: FastAPI request object
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip for pagination
        profile: User profile name
        site: Filter by job site
        search: Search query for job titles/descriptions
        applied: Filter by application status
        experience: Filter by experience level
        table_format: Whether to format for table display
        
    Returns:
        Dictionary containing jobs and metadata
    """
    # Get profile from cookie or parameter
    profile_from_cookie = request.cookies.get("autojob_profile", "")
    profile_to_use = profile or profile_from_cookie
    
    if not profile_to_use:
        available_profiles = get_available_profiles()
        if available_profiles:
            profile_to_use = available_profiles[0]
        else:
            return {"jobs": [], "total_jobs": 0, "error": "No profiles available"}

    try:
        db = get_job_db(profile=profile_to_use)
        
        # Build filters dictionary
        filters = {}
        if site:
            filters["site"] = site
        if applied is not None:
            filters["applied"] = applied
        if experience:
            filters["experience"] = experience

        # Get jobs with filters
        jobs = db.get_jobs(
            limit=limit, 
            offset=offset, 
            filters=filters, 
            search_query=search
        )

        if not jobs:
            return {"jobs": [], "total_jobs": 0, "profile": profile_to_use}

        # Get total count for pagination
        total_count = db.get_job_count(filters=filters, search_query=search)

        return {
            "jobs": jobs,
            "total_jobs": total_count,
            "profile": profile_to_use,
            "filters_applied": filters,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving jobs for profile {profile_to_use}: {e}")
        return {"jobs": [], "total_jobs": 0, "error": str(e)}


@router.get("/jobs")
async def get_jobs(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    profile: str = Query("", description="User profile name"),
    site: str = Query("", description="Filter by job site"),
    search: str = Query("", description="Search in job titles and descriptions"),
    applied: Optional[bool] = Query(None, description="Filter by application status"),
    experience: str = Query("", description="Filter by experience level"),
) -> Dict[str, Any]:
    """
    Get paginated list of jobs with optional filtering.
    
    Returns:
        Dictionary containing jobs, total count, and pagination info
    """
    return await get_jobs_Improved(
        request, limit, offset, profile, site, search, applied, experience
    )


@router.get("/job/{job_id}")
async def get_job_details(
    request: Request, 
    job_id: int, 
    profile: str = Query("", description="User profile name")
) -> Dict[str, Any]:
    """
    Get detailed information for a specific job.
    
    Args:
        request: FastAPI request object
        job_id: Unique job identifier
        profile: User profile name
        
    Returns:
        Dictionary containing job details
        
    Raises:
        HTTPException: If job not found or profile invalid
    """
    profile_to_use = profile or request.cookies.get("autojob_profile")
    
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")

    try:
        db = get_job_db(profile_to_use)
        job = db.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
            
        return {
            "job": job,
            "profile": profile_to_use
        }
        
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/job/{job_id}/apply")
async def apply_to_job(
    request: Request, 
    job_id: int, 
    job_request: JobApplicationRequest,
    profile: str = Query("", description="User profile name")
) -> Dict[str, Any]:
    """
    Apply to a job with different application modes.
    
    Args:
        request: FastAPI request object
        job_id: Unique job identifier
        job_request: Application request details
        profile: User profile name
        
    Returns:
        Dictionary containing application result
        
    Raises:
        HTTPException: If job not found or application fails
    """
    profile_to_use = profile or request.cookies.get("autojob_profile")
    
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")

    try:
        db = get_job_db(profile_to_use)
        job = db.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        mode = job_request.mode
        notes = job_request.notes or f"Applied via Dashboard ({mode.title()})"

        if mode == "manual":
            # Simple database marking - user applies manually
            db.update_job_status(
                job_id, 
                application_status="applied", 
                processing_notes=notes
            )
            
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
                db.update_job_status(
                    job_id, 
                    application_status="applied",
                    processing_notes=notes
                )
                return {
                    "success": True,
                    "message": f"Application completed for {job.get('title', 'job')}",
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
            db.update_job_status(
                job_id, 
                application_status="applied", 
                processing_notes=f"Applied via Dashboard (Fallback: {mode})"
            )
            
            return {
                "success": True, 
                "message": f"Marked as applied: {job.get('title', 'job')} (applier not available)",
                "mode": "manual_fallback",
                "job_url": job.get("url")
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying to job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")


@router.get("/application-modes")
async def get_application_modes() -> Dict[str, Any]:
    """
    Get available application modes for the dashboard.
    
    Returns:
        Dictionary containing available application modes and default mode
    """
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
    
    return {
        "modes": modes, 
        "default": "manual",
        "applier_available": APPLIER_AVAILABLE
    }


@router.get("/sites")
async def get_available_sites(
    request: Request, 
    profile: str = Query("", description="User profile name")
) -> Dict[str, List[Dict[str, str]]]:
    """
    Get list of available job sites for filtering.
    
    Args:
        request: FastAPI request object
        profile: User profile name
        
    Returns:
        Dictionary containing list of available sites
        
    Raises:
        HTTPException: If profile invalid
    """
    profile_to_use = profile or request.cookies.get("autojob_profile")
    
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")

    try:
        db = get_job_db(profile_to_use)
        sites = db.get_unique_sites()
        
        # Format sites for dropdown
        formatted_sites = [
            {"value": site, "label": site.title()} 
            for site in sites if site
        ]
        
        return {"sites": formatted_sites}
        
    except Exception as e:
        logger.error(f"Error retrieving sites for profile {profile_to_use}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/job/{job_id}")
async def delete_job(
    request: Request,
    job_id: int,
    profile: str = Query("", description="User profile name")
) -> Dict[str, Any]:
    """
    Delete a specific job.
    
    Args:
        request: FastAPI request object
        job_id: Unique job identifier
        profile: User profile name
        
    Returns:
        Dictionary containing deletion result
        
    Raises:
        HTTPException: If job not found or deletion fails
    """
    profile_to_use = profile or request.cookies.get("autojob_profile")
    
    if not profile_to_use:
        raise HTTPException(status_code=400, detail="Profile not specified")

    try:
        db = get_job_db(profile_to_use)
        
        # Check if job exists
        job = db.get_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete the job
        success = db.delete_job(job_id)
        
        if success:
            return {
                "success": True,
                "message": f"Job '{job.get('title', 'Unknown')}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete job")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
