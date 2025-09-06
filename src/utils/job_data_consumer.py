"""
Job Data Consumer Module
Provides job data consumption and processing functionality.
"""

from typing import Dict, List, Optional, Any, Callable
from rich.console import Console
import json
import csv


class JobDataConsumer:
    """Consumes and processes job data from various sources."""

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile
        self.console = Console()
        self.processed_jobs = []

    def consume_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consume and process a list of jobs."""
        processed_jobs = []

        for job in jobs:
            processed_job = self.process_job(job)
            if processed_job:
                processed_jobs.append(processed_job)

        self.processed_jobs.extend(processed_jobs)
        return processed_jobs

    def process_job(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single job."""
        if not job or not isinstance(job, dict):
            return None

        # Add processing metadata
        processed_job = {
            **job,
            "processed_at": self.get_current_timestamp(),
            "profile_id": self.profile.get("profile_name", "default"),
            "status": "processed",
        }

        # Validate required fields
        if not processed_job.get("title") or not processed_job.get("url"):
            processed_job["status"] = "invalid"
            return processed_job

        return processed_job

    def filter_jobs(
        self, jobs: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter jobs based on criteria."""
        filtered_jobs = []

        for job in jobs:
            if self.matches_filters(job, filters):
                filtered_jobs.append(job)

        return filtered_jobs

    def matches_filters(self, job: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if a job matches the given filters."""
        for key, value in filters.items():
            if key in job:
                if isinstance(value, str) and value.lower() not in str(job[key]).lower():
                    return False
                elif isinstance(value, (int, float)) and job[key] != value:
                    return False
                elif isinstance(value, bool) and job[key] != value:
                    return False

        return True

    def export_jobs(
        self, jobs: List[Dict[str, Any]], format: str = "json", filename: str = None
    ) -> str:
        """Export jobs to various formats."""
        if not filename:
            filename = f"jobs_export_{self.get_current_timestamp()}"

        if format.lower() == "json":
            return self.export_to_json(jobs, filename)
        elif format.lower() == "csv":
            return self.export_to_csv(jobs, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def export_to_json(self, jobs: List[Dict[str, Any]], filename: str) -> str:
        """Export jobs to JSON format."""
        filepath = f"{filename}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        return filepath

    def export_to_csv(self, jobs: List[Dict[str, Any]], filename: str) -> str:
        """Export jobs to CSV format."""
        filepath = f"{filename}.csv"

        if not jobs:
            return filepath

        fieldnames = jobs[0].keys()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs)

        return filepath

    def get_statistics(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the jobs."""
        if not jobs:
            return {"total": 0, "sites": {}, "locations": {}}

        stats = {
            "total": len(jobs),
            "sites": {},
            "locations": {},
            "experience_levels": {},
            "salary_ranges": {},
        }

        for job in jobs:
            # Count sites
            site = job.get("site", "unknown")
            stats["sites"][site] = stats["sites"].get(site, 0) + 1

            # Count locations
            location = job.get("location", "unknown")
            stats["locations"][location] = stats["locations"].get(location, 0) + 1

            # Count experience levels
            exp_level = job.get("experience_level", "unknown")
            stats["experience_levels"][exp_level] = stats["experience_levels"].get(exp_level, 0) + 1

        return stats

    def get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime

        return datetime.now().strftime("%Y%m%d_%H%M%S")

