"""
Scheduling Service for JobQst Dashboard
Automated job search scheduling and background task management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled job search"""

    name: str
    profile_name: str
    keywords: List[str]
    location: str
    schedule_type: str  # daily, weekly, twice_daily, custom
    time: str  # HH:MM format
    days: List[str]  # for weekly schedules
    enabled: bool = True
    created_at: datetime = None
    last_run: datetime = None


class JobScheduler:
    """Manages automated job search scheduling"""

    def __init__(self):
        """Initialize the scheduler"""
        self.scheduler = BackgroundScheduler(
            jobstores={"default": MemoryJobStore()},
            executors={"default": ThreadPoolExecutor(max_workers=3)},
            job_defaults={"coalesce": False, "max_instances": 1},
        )
        self.schedules: Dict[str, ScheduleConfig] = {}
        self._load_schedules()

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Job scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Job scheduler stopped")

    def create_schedule(self, config: ScheduleConfig) -> str:
        """Create a new scheduled job search"""
        schedule_id = f"schedule_{len(self.schedules) + 1}"
        config.created_at = datetime.now()

        # Add job to scheduler based on type
        if config.schedule_type == "daily_9am":
            self.scheduler.add_job(
                func=self._run_job_search,
                trigger="cron",
                hour=9,
                minute=0,
                args=[config],
                id=schedule_id,
                name=config.name,
            )
        elif config.schedule_type == "twice_daily":
            # Add two jobs for 9 AM and 6 PM
            self.scheduler.add_job(
                func=self._run_job_search,
                trigger="cron",
                hour=9,
                minute=0,
                args=[config],
                id=f"{schedule_id}_morning",
                name=f"{config.name} (Morning)",
            )
            self.scheduler.add_job(
                func=self._run_job_search,
                trigger="cron",
                hour=18,
                minute=0,
                args=[config],
                id=f"{schedule_id}_evening",
                name=f"{config.name} (Evening)",
            )
        elif config.schedule_type == "weekly_monday":
            self.scheduler.add_job(
                func=self._run_job_search,
                trigger="cron",
                day_of_week="mon",
                hour=9,
                minute=0,
                args=[config],
                id=schedule_id,
                name=config.name,
            )

        self.schedules[schedule_id] = config
        self._save_schedules()
        logger.info(f"Created schedule: {config.name}")
        return schedule_id

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a scheduled job search"""
        try:
            # Remove from scheduler
            if self.scheduler.get_job(schedule_id):
                self.scheduler.remove_job(schedule_id)

            # Handle twice daily schedules
            morning_id = f"{schedule_id}_morning"
            evening_id = f"{schedule_id}_evening"
            if self.scheduler.get_job(morning_id):
                self.scheduler.remove_job(morning_id)
            if self.scheduler.get_job(evening_id):
                self.scheduler.remove_job(evening_id)

            # Remove from memory
            if schedule_id in self.schedules:
                del self.schedules[schedule_id]
                self._save_schedules()
                logger.info(f"Deleted schedule: {schedule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting schedule {schedule_id}: {e}")
            return False

    def get_schedules(self) -> List[Dict[str, Any]]:
        """Get all current schedules"""
        schedules = []
        for schedule_id, config in self.schedules.items():
            # Get next run time from scheduler
            job = self.scheduler.get_job(schedule_id)
            next_run = job.next_run_time if job else None

            schedules.append(
                {
                    "id": schedule_id,
                    "name": config.name,
                    "profile": config.profile_name,
                    "keywords": config.keywords,
                    "location": config.location,
                    "schedule_type": config.schedule_type,
                    "enabled": config.enabled,
                    "created_at": config.created_at.isoformat() if config.created_at else None,
                    "last_run": config.last_run.isoformat() if config.last_run else None,
                    "next_run": next_run.isoformat() if next_run else None,
                }
            )

        return schedules

    def toggle_schedule(self, schedule_id: str) -> bool:
        """Enable/disable a schedule"""
        if schedule_id not in self.schedules:
            return False

        config = self.schedules[schedule_id]
        if config.enabled:
            # Disable
            if self.scheduler.get_job(schedule_id):
                self.scheduler.pause_job(schedule_id)
            config.enabled = False
        else:
            # Enable
            if self.scheduler.get_job(schedule_id):
                self.scheduler.resume_job(schedule_id)
            config.enabled = True

        self._save_schedules()
        return True

    def _run_job_search(self, config: ScheduleConfig):
        """Execute a scheduled job search"""
        try:
            logger.info(f"Running scheduled job search: {config.name}")

            # Import here to avoid circular imports
            from src.services.job_scraping_service import JobScrapingService
            from src.services.job_analysis_service import JobAnalysisService

            # Run job search
            scraper = JobScrapingService()
            keywords_str = ",".join(config.keywords)

            # Scrape jobs
            scraper.scrape_jobs(
                profile_name=config.profile_name, keywords=keywords_str, location=config.location
            )

            # Auto-analyze if configured
            analyzer = JobAnalysisService()
            analyzer.analyze_jobs(profile_name=config.profile_name)

            # Update last run time
            config.last_run = datetime.now()
            self.schedules[config.name] = config
            self._save_schedules()

            logger.info(f"Completed scheduled job search: {config.name}")

        except Exception as e:
            logger.error(f"Error in scheduled job search {config.name}: {e}")

    def _load_schedules(self):
        """Load schedules from file"""
        try:
            with open("data/schedules.json", "r") as f:
                data = json.load(f)
                for schedule_id, schedule_data in data.items():
                    config = ScheduleConfig(
                        name=schedule_data["name"],
                        profile_name=schedule_data["profile_name"],
                        keywords=schedule_data["keywords"],
                        location=schedule_data["location"],
                        schedule_type=schedule_data["schedule_type"],
                        time=schedule_data["time"],
                        days=schedule_data.get("days", []),
                        enabled=schedule_data.get("enabled", True),
                    )
                    if schedule_data.get("created_at"):
                        config.created_at = datetime.fromisoformat(schedule_data["created_at"])
                    if schedule_data.get("last_run"):
                        config.last_run = datetime.fromisoformat(schedule_data["last_run"])
                    self.schedules[schedule_id] = config
        except FileNotFoundError:
            logger.info("No existing schedules found")
        except Exception as e:
            logger.error(f"Error loading schedules: {e}")

    def _save_schedules(self):
        """Save schedules to file"""
        try:
            data = {}
            for schedule_id, config in self.schedules.items():
                data[schedule_id] = {
                    "name": config.name,
                    "profile_name": config.profile_name,
                    "keywords": config.keywords,
                    "location": config.location,
                    "schedule_type": config.schedule_type,
                    "time": config.time,
                    "days": config.days,
                    "enabled": config.enabled,
                    "created_at": config.created_at.isoformat() if config.created_at else None,
                    "last_run": config.last_run.isoformat() if config.last_run else None,
                }

            with open("data/schedules.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving schedules: {e}")


# Global scheduler instance
job_scheduler = JobScheduler()
