from typing import List, Dict, Optional
from datetime import datetime, timedelta
from rich.console import Console
from .job_database import JobDatabase

console = Console()


class DBQueries:
    """Database query helper using unified database interface."""

    def __init__(self, db: JobDatabase):
        """Initialize with unified database interface."""
        self.db = db

    def get_jobs(
        self,
        limit: int = 100,
        offset: int = 0,
        site: Optional[str] = None,
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None,
    ) -> List[Dict]:
        """Get jobs using unified database interface."""
        try:
            # Use unified database method
            jobs = self.db.get_top_jobs(limit + offset)

            # Apply filters if needed
            if site:
                jobs = [job for job in jobs if job.get("source") == site]

            if search_query:
                search_term = search_query.lower()
                jobs = [
                    job
                    for job in jobs
                    if (
                        search_term in job.get("title", "").lower()
                        or search_term in job.get("company", "").lower()
                        or search_term in job.get("summary", "").lower()
                    )
                ]

            # Apply filters
            if filters:
                for key, value in filters.items():
                    if key == "applied" and isinstance(value, bool):
                        jobs = [job for job in jobs if job.get("applied", False) == value]
                    elif key == "experience" and value:
                        jobs = [job for job in jobs if job.get("experience_level") == value]
                    elif key == "site" and value:
                        jobs = [job for job in jobs if job.get("source") == value]

            # Apply offset and limit
            return jobs[offset : offset + limit]

        except Exception as e:
            console.print(f"[red]Error fetching jobs: {e}[/red]")
            return []

    def get_job_stats(self) -> Dict:
        """Get job statistics using unified database interface."""
        try:
            jobs = self.db.get_all_jobs()

            if not jobs:
                return {
                    "total_jobs": 0,
                    "applied_jobs": 0,
                    "successful_applications": 0,
                    "failed_applications": 0,
                    "unapplied_jobs": 0,
                    "manual_review_needed": 0,
                    "application_success_rate": 0,
                    "jobs_by_site": {},
                    "unique_companies": 0,
                    "unique_sites": 0,
                    "recent_jobs": 0,
                    "last_scraped_ago": "Never",
                }

            # Calculate statistics
            total_jobs = len(jobs)
            applied_jobs = len(
                [
                    job
                    for job in jobs
                    if job.get("applied", False) or job.get("application_status") == "applied"
                ]
            )

            successful_applications = len(
                [
                    job
                    for job in jobs
                    if job.get("application_status") in ["applied", "interview", "hired"]
                ]
            )

            failed_applications = len(
                [job for job in jobs if job.get("application_status") in ["rejected", "failed"]]
            )

            unapplied_jobs = len(
                [
                    job
                    for job in jobs
                    if not job.get("applied", False)
                    and job.get("application_status") in [None, "not_applied"]
                ]
            )

            manual_review_needed = len(
                [
                    job
                    for job in jobs
                    if job.get("status") in ["pending_review", "needs_review"]
                    or job.get("application_status") == "pending_review"
                ]
            )

            # Jobs by site
            jobs_by_site = {}
            for job in jobs:
                site = job.get("source", "unknown")
                jobs_by_site[site] = jobs_by_site.get(site, 0) + 1

            unique_companies = len(
                set(job.get("company", "") for job in jobs if job.get("company"))
            )
            unique_sites = len(set(job.get("source", "") for job in jobs if job.get("source")))

            # Recent jobs (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            recent_jobs = len(
                [
                    job
                    for job in jobs
                    if job.get("created_at")
                    and datetime.fromisoformat(job["created_at"].replace("Z", "+00:00")) > yesterday
                ]
            )

            # Application success rate
            application_success_rate = round(
                (successful_applications / applied_jobs * 100) if applied_jobs > 0 else 0, 1
            )

            # Calculate last scraped time
            latest_job = max(
                jobs, key=lambda x: x.get("created_at", "1970-01-01T00:00:00Z"), default=None
            )

            last_scraped_ago = "Never"
            if latest_job and latest_job.get("created_at"):
                try:
                    latest_time = datetime.fromisoformat(
                        latest_job["created_at"].replace("Z", "+00:00")
                    )
                    delta = datetime.now(latest_time.tzinfo) - latest_time

                    if delta.days > 0:
                        last_scraped_ago = f"{delta.days} days ago"
                    elif delta.seconds > 3600:
                        last_scraped_ago = f"{delta.seconds // 3600} hours ago"
                    elif delta.seconds > 60:
                        last_scraped_ago = f"{delta.seconds // 60} minutes ago"
                    else:
                        last_scraped_ago = "Just now"
                except Exception:
                    last_scraped_ago = "Unknown"

            return {
                "total_jobs": total_jobs,
                "applied_jobs": applied_jobs,
                "successful_applications": successful_applications,
                "failed_applications": failed_applications,
                "unapplied_jobs": unapplied_jobs,
                "manual_review_needed": manual_review_needed,
                "application_success_rate": application_success_rate,
                "jobs_by_site": jobs_by_site,
                "unique_companies": unique_companies,
                "unique_sites": unique_sites,
                "recent_jobs": recent_jobs,
                "last_scraped_ago": last_scraped_ago,
            }

        except Exception as e:
            console.print(f"[red]Error fetching job stats: {e}[/red]")
            return {
                "total_jobs": 0,
                "applied_jobs": 0,
                "successful_applications": 0,
                "failed_applications": 0,
                "unapplied_jobs": 0,
                "manual_review_needed": 0,
                "application_success_rate": 0,
                "jobs_by_site": {},
                "unique_companies": 0,
                "unique_sites": 0,
                "recent_jobs": 0,
                "last_scraped_ago": "Never",
            }

    def search_jobs(self, query: str, limit: int = 50) -> List[Dict]:
        """Search jobs using unified database interface."""
        try:
            all_jobs = self.db.get_all_jobs()
            search_term = query.lower()

            matching_jobs = [
                job
                for job in all_jobs
                if (
                    search_term in job.get("title", "").lower()
                    or search_term in job.get("company", "").lower()
                    or search_term in job.get("summary", "").lower()
                )
            ]

            # Sort by created_at descending
            matching_jobs.sort(
                key=lambda x: x.get("created_at", "1970-01-01T00:00:00Z"), reverse=True
            )

            return matching_jobs[:limit]

        except Exception as e:
            console.print(f"[red]Error searching jobs: {e}[/red]")
            return []

    def get_unapplied_jobs(self, limit: int = 100) -> List[Dict]:
        """Get unapplied jobs using unified database interface."""
        try:
            all_jobs = self.db.get_all_jobs()

            unapplied = [job for job in all_jobs if not job.get("applied", False)]

            # Sort by created_at descending
            unapplied.sort(key=lambda x: x.get("created_at", "1970-01-01T00:00:00Z"), reverse=True)

            return unapplied[:limit]

        except Exception as e:
            console.print(f"[red]Error fetching unapplied jobs: {e}[/red]")
            return []

    def get_job_count(
        self,
        site: Optional[str] = None,
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """Get job count using unified database interface."""
        try:
            jobs = self.get_jobs(
                limit=10000,  # Get all jobs for counting
                site=site,
                filters=filters,
                search_query=search_query,
            )
            return len(jobs)

        except Exception as e:
            console.print(f"[red]Error fetching job count: {e}[/red]")
            return 0
