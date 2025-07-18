from fastapi import APIRouter
from typing import Dict

from src.core.job_database import get_job_db
from src.utils import profile_helpers

router = APIRouter()


def get_comprehensive_stats() -> Dict:
    """
    Get comprehensive job and application statistics for all available profiles.
    """
    profiles = profile_helpers.get_available_profiles()
    comprehensive_stats = {
        "job_stats": {},
        "application_stats": {},
        "profile_stats": {},
    }

    total_jobs = 0
    for profile_name in profiles:
        try:
            db = get_job_db(profile_name)
            job_stats = db.get_stats()
            comprehensive_stats["profile_stats"][profile_name] = {"jobs": job_stats}
            total_jobs += job_stats.get("total_jobs", 0)
        except Exception as e:
            print(f"Error getting stats for profile {profile_name}: {e}")

    comprehensive_stats["job_stats"] = {"total_jobs": total_jobs}
    return comprehensive_stats


@router.get("/api/comprehensive-stats")
async def comprehensive_stats():
    return get_comprehensive_stats()


@router.get("/api/job-stats")
async def job_stats():
    stats = get_comprehensive_stats()
    return stats.get("job_stats", {})


@router.get("/api/application-stats")
async def application_stats():
    stats = get_comprehensive_stats()
    return stats.get("application_stats", {})


@router.get("/api/profile-stats")
async def profile_stats():
    stats = get_comprehensive_stats()
    return stats.get("profile_stats", {})
