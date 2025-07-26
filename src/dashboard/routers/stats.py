"""
Statistics router for the AutoJobAgent Dashboard API.

This module provides REST API endpoints for retrieving various statistics
including job counts, application metrics, and profile-specific data.
"""

import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Query

from src.core.job_database import get_job_db
from src.utils.profile_helpers import get_available_profiles

# Set up router and logging
router = APIRouter()
logger = logging.getLogger(__name__)


def get_comprehensive_stats(profile_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive job and application statistics for available profiles.
    
    Args:
        profile_filter: Optional profile name to filter stats for specific profile
        
    Returns:
        Dictionary containing comprehensive statistics across all categories
        
    Note:
        Handles errors gracefully and logs issues with individual profiles.
    """
    try:
        profiles = get_available_profiles()
        
        if profile_filter and profile_filter not in profiles:
            logger.warning(f"Profile '{profile_filter}' not found in available profiles")
            profiles = []
        elif profile_filter:
            profiles = [profile_filter]
        
        comprehensive_stats = {
            "job_stats": {
                "total_jobs": 0,
                "total_applications": 0,
                "successful_applications": 0,
                "failed_applications": 0,
                "unapplied_jobs": 0,
                "manual_review_needed": 0,
                "application_success_rate": 0,
                "last_scraped_ago": "Never"
            },
            "application_stats": {
                "today": 0,
                "this_week": 0,
                "this_month": 0,
                "pending": 0,
                "in_progress": 0
            },
            "profile_stats": {},
            "performance_stats": {
                "avg_response_time": 0,
                "active_scrapers": 0,
                "system_health": "healthy"
            },
            "duplicate_stats": {
                "total_duplicates": 0,
                "duplicate_rate": 0
            }
        }

        total_jobs = 0
        total_applications = 0
        successful_applications = 0
        
        for profile_name in profiles:
            try:
                db = get_job_db(profile_name)
                job_stats = db.get_stats()
                
                # Add to profile-specific stats
                comprehensive_stats["profile_stats"][profile_name] = {
                    "jobs": job_stats,
                    "last_updated": job_stats.get("last_updated", "Unknown")
                }
                
                # Aggregate totals
                profile_total = job_stats.get("total_jobs", 0)
                profile_applied = job_stats.get("applied_jobs", 0)
                profile_successful = job_stats.get("successful_applications", 0)
                
                total_jobs += profile_total
                total_applications += profile_applied
                successful_applications += profile_successful
                
            except Exception as e:
                logger.error(f"Error getting stats for profile {profile_name}: {e}")
                comprehensive_stats["profile_stats"][profile_name] = {
                    "error": str(e),
                    "jobs": {}
                }

        # Update aggregated stats
        comprehensive_stats["job_stats"].update({
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "successful_applications": successful_applications,
            "failed_applications": total_applications - successful_applications,
            "unapplied_jobs": total_jobs - total_applications,
            "application_success_rate": round(
                (successful_applications / total_applications * 100) 
                if total_applications > 0 else 0, 1
            )
        })
        
        return comprehensive_stats
        
    except Exception as e:
        logger.error(f"Error generating comprehensive stats: {e}")
        return {
            "error": str(e),
            "job_stats": {},
            "application_stats": {},
            "profile_stats": {}
        }


@router.get("/comprehensive-stats")
async def comprehensive_stats(
    profile: Optional[str] = Query(None, description="Filter stats for specific profile")
) -> Dict[str, Any]:
    """
    Get comprehensive statistics across all profiles or for a specific profile.
    
    Args:
        profile: Optional profile name to filter results
        
    Returns:
        Dictionary containing comprehensive statistics
    """
    try:
        return get_comprehensive_stats(profile_filter=profile)
    except Exception as e:
        logger.error(f"Error in comprehensive_stats endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/job-stats")
async def job_stats(
    profile: Optional[str] = Query(None, description="Filter stats for specific profile")
) -> Dict[str, Any]:
    """
    Get job-specific statistics.
    
    Args:
        profile: Optional profile name to filter results
        
    Returns:
        Dictionary containing job statistics
    """
    try:
        stats = get_comprehensive_stats(profile_filter=profile)
        return stats.get("job_stats", {})
    except Exception as e:
        logger.error(f"Error in job_stats endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/application-stats")
async def application_stats(
    profile: Optional[str] = Query(None, description="Filter stats for specific profile")
) -> Dict[str, Any]:
    """
    Get application-specific statistics.
    
    Args:
        profile: Optional profile name to filter results
        
    Returns:
        Dictionary containing application statistics
    """
    try:
        stats = get_comprehensive_stats(profile_filter=profile)
        return stats.get("application_stats", {})
    except Exception as e:
        logger.error(f"Error in application_stats endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/profile-stats")
async def profile_stats() -> Dict[str, Any]:
    """
    Get profile-specific statistics for all available profiles.
    
    Returns:
        Dictionary containing statistics for each profile
    """
    try:
        stats = get_comprehensive_stats()
        return stats.get("profile_stats", {})
    except Exception as e:
        logger.error(f"Error in profile_stats endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health-stats")
async def health_stats() -> Dict[str, Any]:
    """
    Get system health statistics.
    
    Returns:
        Dictionary containing system health information
    """
    try:
        profiles = get_available_profiles()
        active_profiles = 0
        
        for profile_name in profiles:
            try:
                db = get_job_db(profile_name)
                # Simple health check - if we can get stats, profile is healthy
                db.get_stats()
                active_profiles += 1
            except Exception:
                pass
        
        return {
            "total_profiles": len(profiles),
            "active_profiles": active_profiles,
            "system_status": "healthy" if active_profiles > 0 else "degraded",
            "uptime": "Unknown",  # Could be implemented with system start time
            "memory_usage": "Unknown",  # Could be implemented with psutil
            "database_connections": active_profiles
        }
        
    except Exception as e:
        logger.error(f"Error in health_stats endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Profiles endpoint moved to dedicated profiles router for better organization
