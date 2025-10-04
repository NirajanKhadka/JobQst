"""
RCIP Enrichment Service
Enriches job data with RCIP (Regional and Community Immigration Program) tagging,
ranking boosts, and immigration priority information.
"""

from typing import Dict, List, Any, Optional
from dataclasses import asdict
import logging
from src.utils.location_categorizer import LocationCategorizer, LocationInfo

logger = logging.getLogger(__name__)


class RCIPEnrichmentService:
    """Service for enriching jobs with RCIP and immigration priority data."""

    def __init__(self, ranking_boost: float = 0.15):
        """
        Initialize RCIP enrichment service.

        Args:
            ranking_boost: Score boost for RCIP jobs (default 0.15 = 15% boost)
        """
        self.location_categorizer = LocationCategorizer()
        self.ranking_boost = ranking_boost
        # Get RCIP cities from location categorizer
        self.rcip_cities = self.location_categorizer.rcip_cities
        logger.info(f"Initialized RCIPEnrichmentService with {len(self.rcip_cities)} RCIP cities")

    def enrich_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single job with RCIP information.

        Args:
            job: Job dictionary to enrich

        Returns:
            Enriched job dictionary with RCIP fields
        """
        location = job.get("location", "")

        if not location:
            # No location - set defaults
            job["is_rcip_city"] = False
            job["is_immigration_priority"] = False
            job["city_tags"] = []
            job["location_category"] = "unknown"
            return job

        # Analyze location using categorizer
        location_info: LocationInfo = self.location_categorizer.analyze_location(location)

        # Add RCIP fields to job
        job["is_rcip_city"] = location_info.is_rcip_city
        job["is_immigration_priority"] = location_info.is_immigration_priority
        job["city_tags"] = ",".join(location_info.city_tags) if location_info.city_tags else ""
        job["location_category"] = location_info.location_category
        job["location_type"] = location_info.location_type
        job["province_code"] = location_info.province_code
        job["city"] = location_info.city
        job["province"] = location_info.province

        # Apply ranking boost for RCIP jobs
        if location_info.is_rcip_city:
            # Apply boost to all scoring fields independently
            if "fit_score" in job and job["fit_score"] is not None:
                job["fit_score"] = min(1.0, job["fit_score"] + self.ranking_boost)

            if "compatibility_score" in job and job["compatibility_score"] is not None:
                job["compatibility_score"] = min(
                    1.0, job["compatibility_score"] + self.ranking_boost
                )

            if "match_score" in job and job["match_score"] is not None:
                job["match_score"] = min(1.0, job["match_score"] + self.ranking_boost)

            # Add tags field for UI badges
            existing_tags = job.get("tags", [])
            if isinstance(existing_tags, str):
                existing_tags = existing_tags.split(",") if existing_tags else []
            if "RCIP" not in existing_tags:
                existing_tags.append("RCIP")
            job["tags"] = existing_tags

            logger.debug(f"Applied RCIP boost to job '{job.get('title')}' in {location_info.city}")

        return job

    def enrich_jobs_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich multiple jobs with RCIP information.

        Args:
            jobs: List of job dictionaries to enrich

        Returns:
            List of enriched job dictionaries
        """
        enriched_jobs = []
        rcip_count = 0
        immigration_priority_count = 0

        for job in jobs:
            enriched_job = self.enrich_job(job)
            enriched_jobs.append(enriched_job)

            if enriched_job.get("is_rcip_city"):
                rcip_count += 1
            if enriched_job.get("is_immigration_priority"):
                immigration_priority_count += 1

        logger.info(
            f"Enriched {len(jobs)} jobs: {rcip_count} RCIP jobs, "
            f"{immigration_priority_count} immigration priority jobs"
        )

        return enriched_jobs

    def get_rcip_summary(self) -> Dict[str, Any]:
        """
        Get summary of RCIP cities and configuration.

        Returns:
            Dictionary with RCIP configuration summary
        """
        rcip_by_province = self.location_categorizer.get_rcip_cities_summary()

        return {
            "total_rcip_cities": len(self.rcip_cities),
            "ranking_boost": self.ranking_boost,
            "rcip_cities_by_province": rcip_by_province,
            "location_categories": ["major_city", "rcip_city", "immigration_priority", "custom"],
        }

    def apply_rcip_filter(
        self,
        jobs: List[Dict[str, Any]],
        rcip_only: bool = False,
        immigration_priority: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Filter jobs based on RCIP or immigration priority status.

        Args:
            jobs: List of jobs to filter
            rcip_only: If True, return only RCIP jobs
            immigration_priority: If True, return immigration priority jobs

        Returns:
            Filtered list of jobs
        """
        if not rcip_only and not immigration_priority:
            return jobs

        filtered_jobs = []
        for job in jobs:
            if rcip_only and job.get("is_rcip_city"):
                filtered_jobs.append(job)
            elif immigration_priority and job.get("is_immigration_priority"):
                filtered_jobs.append(job)

        logger.info(
            f"Filtered {len(jobs)} jobs to {len(filtered_jobs)} "
            f"(RCIP={rcip_only}, Immigration={immigration_priority})"
        )

        return filtered_jobs

    def sort_by_rcip_priority(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort jobs with RCIP jobs prioritized at the top.

        Args:
            jobs: List of jobs to sort

        Returns:
            Sorted list with RCIP jobs first, then by score
        """

        def sort_key(job):
            # RCIP jobs get priority (0), non-RCIP get (1)
            rcip_priority = 0 if job.get("is_rcip_city") else 1
            # Then sort by score (higher is better, so negate)
            score = -(job.get("fit_score", 0.0) or job.get("compatibility_score", 0.0) or 0.0)
            return (rcip_priority, score)

        sorted_jobs = sorted(jobs, key=sort_key)

        rcip_count = sum(1 for job in sorted_jobs if job.get("is_rcip_city"))
        logger.info(f"Sorted {len(jobs)} jobs with {rcip_count} RCIP jobs prioritized")

        return sorted_jobs


# Singleton instance
_rcip_service_instance: Optional[RCIPEnrichmentService] = None


def get_rcip_service(ranking_boost: float = 0.15) -> RCIPEnrichmentService:
    """
    Get singleton instance of RCIP enrichment service.

    Args:
        ranking_boost: Score boost for RCIP jobs (only used on first call)

    Returns:
        RCIPEnrichmentService instance
    """
    global _rcip_service_instance
    if _rcip_service_instance is None:
        _rcip_service_instance = RCIPEnrichmentService(ranking_boost=ranking_boost)
    return _rcip_service_instance
