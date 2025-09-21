#!/usr/bin/env python3
"""
Real-Time Job Processing Status Manager for JobQst
Manages live job counts and processing status across multiple profiles
Follows DEVELOPMENT_STANDARDS.md guidelines
"""

import time
import json
import threading
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Import unified database interface (DuckDB-first)
from .job_database import get_job_db

# Setup logging per standards
logger = logging.getLogger(__name__)


@dataclass
class JobCounts:
    """Job count statistics for a profile."""
    total_jobs: int = 0
    scraped_jobs: int = 0
    processed_jobs: int = 0
    analyzed_jobs: int = 0
    applied_jobs: int = 0
    pending_processing: int = 0
    error_jobs: int = 0
    last_updated: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass 
class ProcessingStatus:
    """Real-time processing status."""
    is_processing: bool = False
    current_job_title: str = ""
    progress_percentage: int = 0
    jobs_per_minute: float = 0.0
    estimated_completion: str = ""
    active_workers: int = 0
    last_activity: str = ""


class RealTimeJobStatusManager:
    """
    Manages real-time job processing status and counts across multiple profiles.
    
    Design Principles:
    - Single responsibility: Track job status only
    - Thread-safe operations with proper locking
    - Fast read operations for dashboard updates
    - Memory-efficient with configurable cache TTL
    """
    
    def __init__(self, cache_ttl: int = 30):
        """
        Initialize the status manager.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default 30s per standards)
        """
        self.cache_ttl = cache_ttl
        self._status_cache: Dict[str, JobCounts] = {}
        self._processing_status: Dict[str, ProcessingStatus] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        
        # Activity tracking
        self._activity_log: List[Dict[str, Any]] = []
        self._max_activity_log = 100  # Keep last 100 activities
        
        logger.info("✅ RealTimeJobStatusManager initialized")
    
    def get_job_counts(self, profile_name: str, force_refresh: bool = False) -> JobCounts:
        """
        Get current job counts for a profile.
        
        Args:
            profile_name: Profile identifier
            force_refresh: Skip cache and fetch fresh data
            
        Returns:
            JobCounts object with current statistics
        """
        with self._lock:
            # Check cache validity
            if not force_refresh and self._is_cache_valid(profile_name):
                return self._status_cache.get(profile_name, JobCounts())
            
            # Fetch fresh data
            counts = self._fetch_job_counts_from_db(profile_name)
            
            # Update cache
            self._status_cache[profile_name] = counts
            self._cache_timestamps[profile_name] = datetime.now()
            
            # Log activity
            self._log_activity("job_counts_updated", profile_name, {
                "total_jobs": counts.total_jobs,
                "processed_jobs": counts.processed_jobs
            })
            
            return counts
    
    def update_processing_status(
        self, 
        profile_name: str, 
        is_processing: bool,
        current_job_title: str = "",
        progress_percentage: int = 0,
        active_workers: int = 0
    ) -> None:
        """
        Update real-time processing status.
        
        Args:
            profile_name: Profile identifier
            is_processing: Whether processing is active
            current_job_title: Title of job currently being processed
            progress_percentage: Processing progress (0-100)
            active_workers: Number of active worker threads
        """
        with self._lock:
            if profile_name not in self._processing_status:
                self._processing_status[profile_name] = ProcessingStatus()
            
            status = self._processing_status[profile_name]
            status.is_processing = is_processing
            status.current_job_title = current_job_title
            status.progress_percentage = progress_percentage
            status.active_workers = active_workers
            status.last_activity = datetime.now().isoformat()
            
            # Calculate processing rate
            if is_processing:
                status.jobs_per_minute = self._calculate_processing_rate(profile_name)
                status.estimated_completion = self._estimate_completion_time(profile_name)
            
            # Log significant status changes
            if is_processing:
                self._log_activity("processing_started", profile_name, {
                    "job_title": current_job_title,
                    "progress": progress_percentage,
                    "workers": active_workers
                })
            else:
                self._log_activity("processing_completed", profile_name, {})
    
    def get_processing_status(self, profile_name: str) -> ProcessingStatus:
        """Get current processing status for a profile."""
        with self._lock:
            return self._processing_status.get(profile_name, ProcessingStatus())
    
    def get_all_profile_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive status for all profiles.
        
        Returns:
            Dictionary mapping profile names to their complete status
        """
        with self._lock:
            all_statuses = {}
            
            # Get all known profiles from cache and processing status
            all_profiles = set(self._status_cache.keys()) | set(self._processing_status.keys())
            
            for profile_name in all_profiles:
                job_counts = self.get_job_counts(profile_name)
                processing_status = self.get_processing_status(profile_name)
                
                all_statuses[profile_name] = {
                    "job_counts": job_counts.to_dict(),
                    "processing_status": asdict(processing_status),
                    "last_updated": job_counts.last_updated
                }
            
            return all_statuses
    
    def mark_job_processed(self, profile_name: str, job_id: str, job_title: str = "") -> None:
        """
        Mark a single job as processed and update counts.
        
        Args:
            profile_name: Profile identifier
            job_id: Unique job identifier
            job_title: Job title for logging
        """
        with self._lock:
            # Invalidate cache to force refresh
            if profile_name in self._cache_timestamps:
                del self._cache_timestamps[profile_name]
            
            # Log the processing completion
            self._log_activity("job_processed", profile_name, {
                "job_id": job_id,
                "job_title": job_title
            })
            
            # Update processing status progress
            if profile_name in self._processing_status:
                status = self._processing_status[profile_name]
                if status.is_processing:
                    # Estimate new progress based on job completion
                    counts = self.get_job_counts(profile_name, force_refresh=True)
                    if counts.total_jobs > 0:
                        processed_ratio = counts.processed_jobs / counts.total_jobs
                        status.progress_percentage = min(int(processed_ratio * 100), 100)
    
    def get_recent_activity(self, profile_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent processing activity.
        
        Args:
            profile_name: Filter by profile (None for all)
            limit: Maximum number of activities to return
            
        Returns:
            List of recent activities
        """
        with self._lock:
            activities = self._activity_log.copy()
            
            # Filter by profile if specified
            if profile_name:
                activities = [a for a in activities if a.get("profile_name") == profile_name]
            
            # Return most recent activities
            return activities[-limit:] if activities else []
    
    def cleanup_old_data(self, max_age_hours: int = 24) -> None:
        """
        Clean up old cached data and activity logs.
        
        Args:
            max_age_hours: Maximum age of data to keep
        """
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Clean old cache entries
            expired_profiles = [
                profile for profile, timestamp in self._cache_timestamps.items()
                if timestamp < cutoff_time
            ]
            
            for profile in expired_profiles:
                self._status_cache.pop(profile, None)
                self._cache_timestamps.pop(profile, None)
                logger.debug(f"Cleaned expired cache for profile: {profile}")
            
            # Clean old activity logs
            cutoff_timestamp = cutoff_time.isoformat()
            self._activity_log = [
                activity for activity in self._activity_log
                if activity.get("timestamp", "") > cutoff_timestamp
            ]
            
            logger.info(f"Cleanup completed. Removed {len(expired_profiles)} expired cache entries")
    
    # Private helper methods
    
    def _is_cache_valid(self, profile_name: str) -> bool:
        """Check if cached data is still valid."""
        if profile_name not in self._cache_timestamps:
            return False
        
        cache_age = datetime.now() - self._cache_timestamps[profile_name]
        return cache_age.total_seconds() < self.cache_ttl
    
    def _fetch_job_counts_from_db(self, profile_name: str) -> JobCounts:
        """
        Fetch current job counts from DuckDB database.
        
        Args:
            profile_name: Profile identifier
            
        Returns:
            JobCounts with current statistics
        """
        try:
            # Use unified database interface (DuckDB-first)
            db = get_job_db(profile_name)
            
            # Count jobs by status using DuckDB
            query = """
                SELECT
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'scraped' THEN 1 ELSE 0 END) 
                        as scraped_jobs,
                    SUM(CASE WHEN status IN ('processed', 'analyzed', 'enhanced') 
                        THEN 1 ELSE 0 END) as processed_jobs,
                    SUM(CASE WHEN analysis_data IS NOT NULL THEN 1 ELSE 0 END) 
                        as analyzed_jobs,
                    SUM(CASE WHEN application_status = 'applied' THEN 1 ELSE 0 END) 
                        as applied_jobs,
                    SUM(CASE WHEN status = 'scraped' AND 
                        application_status = 'not_applied' THEN 1 ELSE 0 END) 
                        as pending_processing,
                    SUM(CASE WHEN status = 'error' OR error_message IS NOT NULL 
                        THEN 1 ELSE 0 END) as error_jobs
                FROM jobs
            """
            
            result = db.execute_query(query)
            
            if result and len(result) > 0:
                row = result[0]
                return JobCounts(
                    total_jobs=int(row[0]) if row[0] else 0,
                    scraped_jobs=int(row[1]) if row[1] else 0,
                    processed_jobs=int(row[2]) if row[2] else 0,
                    analyzed_jobs=int(row[3]) if row[3] else 0,
                    applied_jobs=int(row[4]) if row[4] else 0,
                    pending_processing=int(row[5]) if row[5] else 0,
                    error_jobs=int(row[6]) if row[6] else 0,
                    last_updated=datetime.now().isoformat()
                )
            else:
                return JobCounts(last_updated=datetime.now().isoformat())
                
        except Exception as e:
            logger.error(f"Error fetching job counts for {profile_name}: {e}")
            return JobCounts(
                error_jobs=1,  # Indicate there's an error
                last_updated=datetime.now().isoformat()
            )
    
    def _calculate_processing_rate(self, profile_name: str) -> float:
        """Calculate current processing rate in jobs per minute."""
        # Get recent processing activities
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_activities = [
            a for a in self._activity_log
            if (a.get("profile_name") == profile_name and
                a.get("action") == "job_processed" and
                datetime.fromisoformat(a.get("timestamp", "")) > cutoff_time)
        ]
        
        if len(recent_activities) < 2:
            return 0.0
        
        # Calculate rate based on recent activity
        time_span = (
            datetime.fromisoformat(recent_activities[-1]["timestamp"]) - 
            datetime.fromisoformat(recent_activities[0]["timestamp"])
        ).total_seconds() / 60.0  # Convert to minutes
        
        if time_span > 0:
            return len(recent_activities) / time_span
        return 0.0
    
    def _estimate_completion_time(self, profile_name: str) -> str:
        """Estimate completion time based on current processing rate."""
        counts = self._status_cache.get(profile_name)
        if not counts or counts.pending_processing == 0:
            return "Complete"
        
        rate = self._calculate_processing_rate(profile_name)
        if rate <= 0:
            return "Unknown"
        
        minutes_remaining = counts.pending_processing / rate
        completion_time = datetime.now() + timedelta(minutes=minutes_remaining)
        
        return completion_time.strftime("%H:%M:%S")
    
    def _log_activity(self, action: str, profile_name: str, details: Dict[str, Any]) -> None:
        """Log processing activity with rotation."""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "profile_name": profile_name,
            "details": details
        }
        
        self._activity_log.append(activity)
        
        # Rotate log if too large
        if len(self._activity_log) > self._max_activity_log:
            self._activity_log = self._activity_log[-self._max_activity_log:]


# Global singleton instance
_status_manager: Optional[RealTimeJobStatusManager] = None


def get_status_manager() -> RealTimeJobStatusManager:
    """Get the global status manager instance (singleton pattern)."""
    global _status_manager
    if _status_manager is None:
        _status_manager = RealTimeJobStatusManager()
    return _status_manager


def get_job_counts(profile_name: str, force_refresh: bool = False) -> JobCounts:
    """Convenience function to get job counts."""
    return get_status_manager().get_job_counts(profile_name, force_refresh)


def mark_job_processed(profile_name: str, job_id: str, job_title: str = "") -> None:
    """Convenience function to mark job as processed."""
    get_status_manager().mark_job_processed(profile_name, job_id, job_title)


def update_processing_status(
    profile_name: str, 
    is_processing: bool,
    current_job_title: str = "",
    progress_percentage: int = 0,
    active_workers: int = 0
) -> None:
    """Convenience function to update processing status."""
    get_status_manager().update_processing_status(
        profile_name, is_processing, current_job_title, progress_percentage, active_workers
    )

