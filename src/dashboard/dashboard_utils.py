"""
Shared dashboard utilities for status formatting, real-time updates, and common operations.
"""

from typing import Dict, List, Optional
from datetime import datetime
import json


def format_job_status(status: str) -> Dict[str, str]:
    """Format job status for dashboard display."""
    status_colors = {
        "scraped": "blue",
        "pending_review": "yellow",
        "approved": "green",
        "rejected": "red",
        "applied": "purple",
        "interview": "orange",
        "hired": "darkgreen",
        "rejected_after_interview": "darkred",
    }

    return {
        "status": status,
        "color": status_colors.get(status, "gray"),
        "label": status.replace("_", " ").title(),
    }


def get_dashboard_stats(jobs: List[Dict]) -> Dict[str, int]:
    """Calculate dashboard statistics from job list."""
    stats = {
        "total_jobs": len(jobs),
        "scraped": 0,
        "pending_review": 0,
        "approved": 0,
        "rejected": 0,
        "applied": 0,
        "interview": 0,
        "hired": 0,
        "rejected_after_interview": 0,
    }

    for job in jobs:
        status = job.get("status", "scraped")
        if status in stats:
            stats[status] += 1

    return stats


def format_real_time_update(update_type: str, data: Dict) -> Dict:
    """Format real-time update for WebSocket transmission."""
    return {"type": update_type, "timestamp": datetime.now().isoformat(), "data": data}


def get_job_summary(job: Dict) -> Dict:
    """Extract key information for job summary display."""
    return {
        "id": job.get("id"),
        "title": job.get("title", "Unknown"),
        "company": job.get("company", "Unknown"),
        "location": job.get("location", "Unknown"),
        "status": format_job_status(job.get("status", "scraped")),
        "scraped_date": job.get("scraped_date"),
        "ats_system": job.get("ats_system", "Unknown"),
        "experience_level": job.get("experience_level", "Unknown"),
    }


def filter_jobs_for_dashboard(jobs: List[Dict], filters: Dict) -> List[Dict]:
    """Filter jobs based on dashboard filter criteria."""
    filtered_jobs = jobs

    # Status filter
    if "status" in filters and filters["status"]:
        filtered_jobs = [j for j in filtered_jobs if j.get("status") == filters["status"]]

    # Company filter
    if "company" in filters and filters["company"]:
        filtered_jobs = [
            j for j in filtered_jobs if filters["company"].lower() in j.get("company", "").lower()
        ]

    # Location filter
    if "location" in filters and filters["location"]:
        filtered_jobs = [
            j for j in filtered_jobs if filters["location"].lower() in j.get("location", "").lower()
        ]

    # Experience level filter
    if "experience_level" in filters and filters["experience_level"]:
        filtered_jobs = [
            j for j in filtered_jobs if j.get("experience_level") == filters["experience_level"]
        ]

    return filtered_jobs


def get_dashboard_health_status() -> Dict:
    """Get overall dashboard health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "database": "connected",
            "scrapers": "available",
            "job_applier": "ready",
            "manual_review": "ready",
        },
    }
