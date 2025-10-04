"""Dashboard data service that delegates to the shared data-access layer."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from src.dashboard.analytics import (
    compute_company_stats,
    compute_job_metrics,
    compute_location_stats,
)
from src.dashboard.services.cache_service import get_cached_aggregations

from ...core.dashboard_data_access import (
    DashboardDataAccess,
    DashboardDataAccessError,
    DashboardDataResponse,
    get_dashboard_data_access,
)

logger = logging.getLogger(__name__)

# Import profile service
try:
    from src.dashboard.services.profile_service import get_profile_service

    profile_service_available = True
except ImportError:
    logger.warning("ProfileService not available")
    profile_service_available = False
    get_profile_service = None

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:  # pragma: no cover - psutil optional dependency
    psutil = None
    PSUTIL_AVAILABLE = False
    PSUTIL_AVAILABLE = False

from src.core.job_database import get_job_db


@dataclass
class _StatsBundle:
    """Helper container for computed dashboard statistics."""

    dataframe: pd.DataFrame
    response: DashboardDataResponse


class DataService:
    """Data service that exposes dashboard-friendly data primitives."""

    def __init__(
        self,
        data_access: Optional[DashboardDataAccess] = None,
    ) -> None:
        """Initialise the service with the shared data access layer."""
        self._data_access = data_access or get_dashboard_data_access()
        logger.info("Data service initialised with shared dashboard data access")

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------
    def get_jobs_data(self, profile_name: str) -> List[Dict[str, Any]]:
        """Return job records for a profile using the shared data access layer."""
        try:
            return self._fetch_bundle(profile_name).response.records
        except DashboardDataAccessError as error:
            logger.error("Error loading jobs data: %s", error)
            return []

    def get_available_profiles(self) -> List[str]:
        """Return the list of available profiles."""
        if profile_service_available:
            try:
                profile_service = get_profile_service()
                return profile_service.get_available_profiles()
            except Exception as error:  # pragma: no cover - defensive logging
                logger.error("Error getting profiles from ProfileService: %s", error)
        # Fallback to empty list
        return []

    def get_job_stats(self, profile_name: str) -> Dict[str, Any]:
        """Calculate high-level job statistics for the given profile."""
        try:
            dataframe = self._fetch_bundle(profile_name).dataframe
        except DashboardDataAccessError as error:
            logger.error("Error getting job stats: %s", error)
            return self._default_stats()

        if dataframe.empty:
            return self._default_stats()

        stats = {
            "total_jobs": int(len(dataframe)),
            "new_jobs": int((dataframe["status"] == "new").sum()),
            "ready_to_apply": int((dataframe["status"] == "ready_to_apply").sum()),
            "applied_jobs": int((dataframe["status"] == "applied").sum()),
            "needs_review": int((dataframe["status"] == "needs_review").sum()),
            "average_match_score": float(dataframe["match_score"].fillna(0).mean()),
        }
        return stats

    def get_system_health(self) -> Dict[str, Any]:
        """Return basic system health metrics (CPU, memory, disk)."""
        if not PSUTIL_AVAILABLE:
            return self._default_health()
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "db_status": "healthy",
                "api_status": "running",
            }
        except Exception as error:
            logger.error("Error getting system health: %s", error)
            return self._default_health()

    def get_processing_status(self, profile_name: str) -> Dict[str, Any]:
        """Return lightweight processing status derived from job storage."""
        try:
            job_db = get_job_db(profile_name)
            jobs = job_db.get_jobs()
        except Exception as error:
            logger.error("Error getting processing status: %s", error)
            return self._default_processing_status()

        processed = sum(
            1
            for job in jobs
            if job.get("stage1_score") is not None or job.get("final_score") is not None
        )
        total = len(jobs)
        pending = max(total - processed, 0)

        return {
            "current_operation": "idle",
            "progress": float(processed / total * 100) if total else 0.0,
            "jobs_processed": processed,
            "errors": 0,
            "last_run": None,
            "queue_size": pending,
        }

    def _default_stats(self) -> Dict[str, Any]:
        """Default job statistics"""
        return {
            "total_jobs": 0,
            "new_jobs": 0,
            "applied_jobs": 0,
            "reviewed_jobs": 0,
            "average_match_score": 0.0,
        }

    def _default_health(self) -> Dict[str, Any]:
        """Default system health"""
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
            "db_status": "unknown",
            "api_status": "unknown",
        }

    def _default_processing_status(self) -> Dict[str, Any]:
        """Default processing status"""
        return {
            "current_operation": "idle",
            "progress": 0,
            "jobs_processed": 0,
            "errors": 0,
            "last_run": None,
        }

    def get_profiles(self) -> List[str]:
        """Get list of available user profiles"""
        if profile_service_available:
            try:
                profile_service = get_profile_service()
                return profile_service.get_available_profiles()
            except Exception as e:
                logger.error(f"Error getting profiles from ProfileService: {e}")
                return []
        return self.get_available_profiles()

    def load_job_data(self, profile_name: str) -> pd.DataFrame:
        """Load job data for a specific profile and return as DataFrame."""
        try:
            return self._fetch_bundle(profile_name).dataframe
        except DashboardDataAccessError as error:
            logger.error(
                "Error loading job data for %s: %s",
                profile_name,
                error,
            )
            return pd.DataFrame()

    # ============= UNIFIED CACHE AGGREGATION METHODS =============

    def get_cached_company_stats(self, profile_name: str, top_n: int = 15) -> Dict[str, Any]:
        """Get company statistics with caching for improved performance"""
        try:
            dataframe = self._fetch_bundle(profile_name).dataframe
        except DashboardDataAccessError as error:
            logger.error("Error computing company stats: %s", error)
            return compute_company_stats(pd.DataFrame()).to_dict()

        aggregations = get_cached_aggregations()
        return aggregations.get_company_stats(
            dataframe,
            profile_name=profile_name,
            top_n=top_n,
        )

    def get_cached_location_stats(self, profile_name: str, top_n: int = 10) -> Dict[str, Any]:
        """Get location statistics with caching for improved performance"""
        try:
            dataframe = self._fetch_bundle(profile_name).dataframe
        except DashboardDataAccessError as error:
            logger.error("Error computing location stats: %s", error)
            return compute_location_stats(pd.DataFrame()).to_dict()

        aggregations = get_cached_aggregations()
        return aggregations.get_location_stats(
            dataframe,
            profile_name=profile_name,
            top_n=top_n,
        )

    def get_cached_job_metrics(self, profile_name: str) -> Dict[str, Any]:
        """Get job metrics with caching for improved performance"""
        try:
            dataframe = self._fetch_bundle(profile_name).dataframe
        except DashboardDataAccessError as error:
            logger.error("Error computing job metrics: %s", error)
            return compute_job_metrics(pd.DataFrame()).to_dict()

        aggregations = get_cached_aggregations()
        return aggregations.get_job_metrics(dataframe, profile_name=profile_name)

    def invalidate_cache(self, profile_name: str = None) -> Dict[str, Any]:
        """
        Invalidate cache for profile or entire cache

        Args:
            profile_name: If provided, invalidate only this profile's cache
                         If None, clear entire cache

        Returns:
            Dictionary with invalidation results
        """
        try:
            if profile_name:
                count = self._data_access.clear_profile_cache(profile_name)
                return {
                    "success": True,
                    "message": f"Invalidated {count} entries for {profile_name}",
                    "invalidated_count": count,
                }
            count = self._data_access.clear_profile_cache(None)
            return {
                "success": True,
                "message": f"Invalidated cache entries ({count} total)",
                "invalidated_count": count,
            }
        except Exception as error:
            logger.error("Error invalidating cache: %s", error)
            return {
                "success": False,
                "message": f"Cache invalidation failed: {error}",
                "invalidated_count": 0,
            }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            stats = self._data_access.get_cache_stats()
            return {"cache_available": True, **stats}
        except Exception as error:
            logger.error("Error getting cache stats: %s", error)
            return {
                "cache_available": False,
                "message": f"Error getting stats: {error}",
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_bundle(self, profile_name: str) -> _StatsBundle:
        """Retrieve dashboard data and wrap it for downstream consumers."""
        response = self._data_access.get_jobs(profile_name)
        return _StatsBundle(dataframe=response.dataframe, response=response)


# Global instance
_data_service_instance = None


def get_data_service() -> DataService:
    """Get the global data service instance"""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = DataService()
    return _data_service_instance
