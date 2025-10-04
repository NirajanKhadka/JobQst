#!/usr/bin/env python3
"""
Job Cache Manager
Handles automatic caching and processing of scraped jobs every minute.
"""

import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from .job_database import get_job_db
from .job_data import JobData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobCacheManager:
    """Manages automatic job caching and processing."""

    def __init__(self, profile_name: str = "Nirajan"):
        self.profile_name = profile_name
        self.db = get_job_db()
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.running = False
        self.cache_thread = None

    def start_caching(self):
        """Start the automatic caching process."""
        if self.running:
            logger.info("Cache manager is already running")
            return

        self.running = True
        self.cache_thread = threading.Thread(target=self._cache_loop, daemon=True)
        self.cache_thread.start()
        logger.info(f"Job cache manager started for profile: {self.profile_name}")

    def stop_caching(self):
        """Stop the automatic caching process."""
        self.running = False
        if self.cache_thread:
            self.cache_thread.join(timeout=5)
        logger.info("Job cache manager stopped")

    def _cache_loop(self):
        """Main caching loop that runs every minute."""
        while self.running:
            try:
                self._process_cache()
                time.sleep(60)  # Wait 1 minute
            except Exception as e:
                logger.error(f"Error in cache loop: {e}")
                time.sleep(60)  # Continue after error

    def _process_cache(self):
        """Process cached job data and update database."""
        logger.info("Processing job cache...")

        # Find all cache files
        cache_files = list(self.cache_dir.glob("*.json"))

        for cache_file in cache_files:
            try:
                # Load cached data
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)

                # Process each job in the cache
                for job_data in cached_data.get("jobs", []):
                    self._process_job(job_data)

                # Move processed cache file to processed directory
                processed_dir = self.cache_dir / "processed"
                processed_dir.mkdir(exist_ok=True)
                cache_file.rename(processed_dir / cache_file.name)

                logger.info(f"Processed cache file: {cache_file.name}")

            except Exception as e:
                logger.error(f"Error processing cache file {cache_file}: {e}")

    def _process_job(self, job_data: Dict[str, Any]):
        """Process a single job and add to database."""
        try:
            # Create job data object
            job_record = JobData(
                title=job_data.get("title", ""),
                company=job_data.get("company", ""),
                location=job_data.get("location", ""),
                url=job_data.get("url", ""),
                summary=job_data.get("summary", ""),
                search_keyword=job_data.get("search_keyword", ""),
                site=job_data.get("site", "unknown"),
                salary=job_data.get("salary_range", ""),
                job_type=job_data.get("job_type", ""),
                posted_date=job_data.get("posted_date", ""),
                scraped_at=datetime.now().isoformat(),
                raw_data=job_data,
            )

            # Add to database
            if self.db.add_job(job_record):
                logger.info(f"Added job: {job_record.title} at {job_record.company}")
            else:
                logger.info(f"Job already exists: {job_record.title} at {job_record.company}")

        except Exception as e:
            logger.error(f"Error processing job {job_data.get('title', 'Unknown')}: {e}")

    def update_job_status(self, job_id: str, new_status: str, notes: str = ""):
        """Update job status in database."""
        try:
            with self.db._get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET status = ?, processing_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE job_id = ?",
                    (new_status, notes, job_id),
                )
                conn.commit()
                logger.info(f"Updated job {job_id} status to {new_status}")
        except Exception as e:
            logger.error(f"Error updating job status: {e}")

    def mark_job_applied(self, job_id: str, application_date: Optional[str] = None):
        """Mark a job as applied."""
        if application_date is None:
            application_date = datetime.now().isoformat()

        try:
            with self.db._get_connection() as conn:
                conn.execute(
                    """UPDATE jobs SET 
                       status = 'applied', 
                       applied = 1, 
                       application_status = 'applied',
                       application_date = ?, 
                       updated_at = CURRENT_TIMESTAMP 
                       WHERE job_id = ?""",
                    (application_date, job_id),
                )
                conn.commit()
                logger.info(f"Marked job {job_id} as applied")
        except Exception as e:
            logger.error(f"Error marking job as applied: {e}")

    def get_jobs_by_status(self, status: str) -> List[Dict]:
        """Get jobs by status."""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC", (status,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting jobs by status: {e}")
            return []

    def get_pending_jobs(self) -> List[Dict]:
        """Get jobs that need processing."""
        return self.get_jobs_by_status("scraped")

    def get_applied_jobs(self) -> List[Dict]:
        """Get jobs that have been applied to."""
        return self.get_jobs_by_status("applied")


# Global cache manager instance
_cache_manager = None


def get_cache_manager(profile_name: str) -> JobCacheManager:
    """Get or create the global cache manager instance."""
    if not profile_name:
        raise ValueError("Profile name is required")
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = JobCacheManager(profile_name)
    return _cache_manager


def start_job_caching(profile_name: str):
    """Start the job caching system."""
    if not profile_name:
        raise ValueError("Profile name is required")
    manager = get_cache_manager(profile_name)
    manager.start_caching()


def stop_job_caching():
    """Stop the job caching system."""
    global _cache_manager
    if _cache_manager:
        _cache_manager.stop_caching()
        _cache_manager = None
