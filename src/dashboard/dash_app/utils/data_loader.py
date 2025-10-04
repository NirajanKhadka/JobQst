from __future__ import annotations

"""Dashboard DataLoader bridging Dash components to the shared data layer."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

load_dotenv()

from src.core.dashboard_data_access import DEFAULT_COLUMNS, DashboardDataAccessError
from src.dashboard.services.data_service import DataService, get_data_service

logger = logging.getLogger(__name__)


class DataLoader:
    """Provide dashboard-friendly access to profile-scoped job data."""

    def __init__(
        self,
        profile_name: Optional[str] = None,
        data_service: Optional[DataService] = None,
    ) -> None:
        self._profile_name = profile_name
        self._data_service = data_service or get_data_service()
        logger.debug("DataLoader initialised for profile=%s", profile_name)

    # ------------------------------------------------------------------
    # Profile helpers
    # ------------------------------------------------------------------
    def set_profile(self, profile_name: str) -> None:
        """Persist the active profile for repeated calls."""
        self._profile_name = profile_name

    def get_current_profile(self) -> Optional[str]:
        """Return the currently configured profile name."""
        return self._profile_name

    def _resolve_profile(self, profile_name: Optional[str]) -> str:
        resolved = profile_name or self._profile_name
        if resolved is None:
            raise ValueError(
                "Profile name is required. No profile set on DataLoader instance.\n"
                "Either pass profile_name parameter or set via set_profile()."
            )
        return resolved

    # ------------------------------------------------------------------
    # Core data access
    # ------------------------------------------------------------------
    def get_available_profiles(self) -> List[str]:
        """Return all profiles visible to the dashboard."""
        profiles = self._data_service.get_profiles()
        if not profiles:
            logger.warning("No profiles available via DataService")
        return profiles

    def load_jobs_data(self, profile_name: Optional[str] = None) -> pd.DataFrame:
        """Return a pandas DataFrame of jobs for the selected profile."""
        resolved = self._resolve_profile(profile_name)
        try:
            dataframe = self._data_service.load_job_data(resolved)
        except DashboardDataAccessError as error:
            logger.error("Dashboard data access failure: %s", error)
            return self._create_empty_dataframe()
        except Exception as error:  # pragma: no cover - defensive logging
            logger.error("Unexpected error loading jobs data: %s", error)
            return self._create_empty_dataframe()

        if dataframe.empty:
            logger.info("No jobs found for profile %s", resolved)
            return self._create_empty_dataframe()
        return dataframe

    def get_jobs_data(self, profile_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return a list of job dictionaries for the selected profile."""
        resolved = self._resolve_profile(profile_name)
        try:
            return self._data_service.get_jobs_data(resolved)
        except DashboardDataAccessError as error:
            logger.error("Dashboard data access failure: %s", error)
            return []
        except Exception as error:  # pragma: no cover - defensive logging
            logger.error("Unexpected error getting jobs data: %s", error)
            return []

    def get_job_stats(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Return aggregate job statistics used by sidebar widgets."""
        resolved = self._resolve_profile(profile_name)
        stats = self._data_service.get_job_stats(resolved)
        if not stats:
            logger.debug("No job stats returned for profile %s", resolved)
        return stats

    # ------------------------------------------------------------------
    # System & processing signals
    # ------------------------------------------------------------------
    def get_system_health(self) -> Dict[str, Any]:
        """Return system health metrics surfaced in the dashboard header."""
        return self._data_service.get_system_health()

    def get_processing_status(
        self,
        profile_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return processing pipeline status for the active profile."""
        resolved = self._resolve_profile(profile_name)
        return self._data_service.get_processing_status(resolved)

    # ------------------------------------------------------------------
    # Cache insights
    # ------------------------------------------------------------------
    def get_cache_stats(self) -> Dict[str, Any]:
        """Expose cache statistics for diagnostics panels."""
        return self._data_service.get_cache_stats()

    def invalidate_cache(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Invalidate cached dashboard data for a profile or all profiles."""
        resolved = profile_name or self._profile_name
        return self._data_service.invalidate_cache(resolved)

    # ------------------------------------------------------------------
    # Analytics helpers
    # ------------------------------------------------------------------
    def get_ai_analytics(
        self,
        profile_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return AI analytics metrics; fall back to defaults on failure."""
        resolved = self._resolve_profile(profile_name)
        try:
            from src.services.ai_integration_service import (
                get_ai_integration_service,
            )

            ai_service = get_ai_integration_service(resolved)
            analytics = ai_service.get_ai_analytics()
            return analytics
        except Exception as error:
            logger.error("Error getting AI analytics: %s", error)
            return {
                "total_jobs": 0,
                "ai_processed": 0,
                "avg_semantic_score": 0.0,
                "cache_efficiency": 0.0,
                "ai_processing_coverage": 0.0,
            }

    # ------------------------------------------------------------------
    # Enhanced Stats Methods for Dashboard Enhancements
    # ------------------------------------------------------------------
    def get_enhanced_stats(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get enhanced statistics for professional stat cards.
        
        Returns:
            Dictionary with:
                - total_jobs: int
                - new_today: int
                - high_match: int (fit_score >= 70)
                - rcip_jobs: int
                - new_this_week: int
                - high_match_percentage: float
        """
        from datetime import datetime, timedelta
        
        resolved = self._resolve_profile(profile_name)
        
        try:
            df = self.load_jobs_data(resolved)
            
            if df.empty:
                return {
                    "total_jobs": 0,
                    "new_today": 0,
                    "high_match": 0,
                    "rcip_jobs": 0,
                    "new_this_week": 0,
                    "high_match_percentage": 0.0
                }
            
            # Total jobs
            total_jobs = len(df)
            
            # New today (posted_date is today)
            today = datetime.now().date()
            new_today = 0
            if 'posted_date' in df.columns:
                df['posted_date_parsed'] = pd.to_datetime(df['posted_date'], errors='coerce')
                new_today = len(df[df['posted_date_parsed'].dt.date == today])
            
            # New this week
            week_ago = today - timedelta(days=7)
            new_this_week = 0
            if 'posted_date' in df.columns:
                new_this_week = len(df[df['posted_date_parsed'].dt.date >= week_ago])
            
            # High match (fit_score >= 70)
            high_match = 0
            if 'fit_score' in df.columns:
                high_match = len(df[df['fit_score'] >= 70])
            
            # RCIP jobs
            rcip_jobs = 0
            if 'is_rcip' in df.columns:
                rcip_jobs = len(df[df['is_rcip'] == True])
            elif 'rcip' in df.columns:
                rcip_jobs = len(df[df['rcip'] == True])
            
            # High match percentage
            high_match_percentage = (high_match / total_jobs * 100) if total_jobs > 0 else 0.0
            
            return {
                "total_jobs": total_jobs,
                "new_today": new_today,
                "high_match": high_match,
                "rcip_jobs": rcip_jobs,
                "new_this_week": new_this_week,
                "high_match_percentage": round(high_match_percentage, 1)
            }
        
        except Exception as error:
            logger.error("Error calculating enhanced stats: %s", error)
            return {
                "total_jobs": 0,
                "new_today": 0,
                "high_match": 0,
                "rcip_jobs": 0,
                "new_this_week": 0,
                "high_match_percentage": 0.0
            }
    
    def get_skill_analysis_data(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get data for skill gap analysis.
        
        Returns:
            Dictionary with:
                - user_skills: List[str]
                - jobs: List[Dict]
                - total_jobs: int
        """
        resolved = self._resolve_profile(profile_name)
        
        try:
            # Get user skills from profile
            user_skills = []
            try:
                from src.core.user_profile_manager import ModernUserProfileManager
                profile_manager = ModernUserProfileManager()
                profile = profile_manager.get_profile(resolved)
                if profile:
                    user_skills = profile.skills or []
            except Exception as e:
                logger.warning(f"Could not load user skills: {e}")
            
            # Get jobs data
            jobs = self.get_jobs_data(resolved)
            
            return {
                "user_skills": user_skills,
                "jobs": jobs,
                "total_jobs": len(jobs)
            }
        
        except Exception as error:
            logger.error("Error getting skill analysis data: %s", error)
            return {
                "user_skills": [],
                "jobs": [],
                "total_jobs": 0
            }
    
    def get_success_prediction_data(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get data for success prediction.
        
        Returns:
            Dictionary with:
                - user_skills: List[str]
                - jobs: List[Dict]
                - user_experience_years: Optional[int]
        """
        resolved = self._resolve_profile(profile_name)
        
        try:
            # Get user profile data
            user_skills = []
            user_experience_years = None
            
            try:
                from src.core.user_profile_manager import ModernUserProfileManager
                profile_manager = ModernUserProfileManager()
                profile = profile_manager.get_profile(resolved)
                if profile:
                    user_skills = profile.skills or []
                    # Try to extract experience years
                    user_experience_years = profile.experience_years
            except Exception as e:
                logger.warning(f"Could not load user profile data: {e}")
            
            # Get jobs data
            jobs = self.get_jobs_data(resolved)
            
            return {
                "user_skills": user_skills,
                "jobs": jobs,
                "user_experience_years": user_experience_years
            }
        
        except Exception as error:
            logger.error("Error getting success prediction data: %s", error)
            return {
                "user_skills": [],
                "jobs": [],
                "user_experience_years": None
            }

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _create_empty_dataframe(self) -> pd.DataFrame:
        """Create an empty DataFrame matching the canonical dashboard schema."""
        return pd.DataFrame(columns=list(DEFAULT_COLUMNS))
