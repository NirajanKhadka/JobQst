import sqlite3
import json
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from rich.console import Console

console = Console()


class DBQueries:
    def __init__(self, db_connection):
        self.conn = db_connection

    def get_jobs(
        self,
        limit: int = 100,
        offset: int = 0,
        site: Optional[str] = None,
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None,
    ) -> List[Dict]:
        query = "SELECT * FROM jobs"
        params: List[Union[str, int]] = []
        conditions = []

        if site:
            conditions.append("site = ?")
            params.append(site)

        if search_query:
            search_term = f"%{search_query}%"
            conditions.append("(title LIKE ? OR company LIKE ? OR summary LIKE ?)")
            params.extend([search_term, search_term, search_term])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            cursor = self.conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            console.print(f"[red]Error fetching jobs: {e}[/red]")
            return []

    def get_job_stats(self) -> Dict:
        try:
            stats = {}
            
            # Total jobs count
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM jobs")
            stats["total_jobs"] = cursor.fetchone()["count"]
            
            # Applied jobs count (using both 'applied' column and application_status)
            cursor = self.conn.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE applied = 1 OR application_status = 'applied'"
            )
            stats["applied_jobs"] = cursor.fetchone()["count"]
            
            # Successful applications (jobs with successful application status)
            cursor = self.conn.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE application_status IN ('applied', 'interview', 'hired')"
            )
            stats["successful_applications"] = cursor.fetchone()["count"]
            
            # Failed applications
            cursor = self.conn.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE application_status IN ('rejected', 'failed')"
            )
            stats["failed_applications"] = cursor.fetchone()["count"]
            
            # Unapplied jobs
            cursor = self.conn.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE (applied = 0 OR applied IS NULL) AND (application_status IS NULL OR application_status = 'not_applied')"
            )
            stats["unapplied_jobs"] = cursor.fetchone()["count"]
            
            # Manual review needed (jobs with certain statuses)
            cursor = self.conn.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE status IN ('pending_review', 'needs_review') OR application_status = 'pending_review'"
            )
            stats["manual_review_needed"] = cursor.fetchone()["count"]

            # Jobs by site breakdown
            cursor = self.conn.execute(
                "SELECT site, COUNT(*) as count FROM jobs GROUP BY site ORDER BY count DESC"
            )
            stats["jobs_by_site"] = dict(cursor.fetchall())

            # Unique companies count
            cursor = self.conn.execute("SELECT COUNT(DISTINCT company) as count FROM jobs WHERE company IS NOT NULL")
            stats["unique_companies"] = cursor.fetchone()["count"]
            
            # Unique sites count
            cursor = self.conn.execute("SELECT COUNT(DISTINCT site) as count FROM jobs WHERE site IS NOT NULL")
            stats["unique_sites"] = cursor.fetchone()["count"]

            # Recent jobs (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor = self.conn.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE scraped_at > ?", (yesterday,)
            )
            stats["recent_jobs"] = cursor.fetchone()["count"]
            
            # Calculate application success rate
            total_applications = stats.get("applied_jobs", 0)
            successful = stats.get("successful_applications", 0)
            stats["application_success_rate"] = round(
                (successful / total_applications * 100) if total_applications > 0 else 0, 1
            )
            
            # Last scraped time
            cursor = self.conn.execute(
                "SELECT scraped_at FROM jobs ORDER BY scraped_at DESC LIMIT 1"
            )
            last_scraped = cursor.fetchone()
            if last_scraped and last_scraped["scraped_at"]:
                try:
                    last_time = datetime.fromisoformat(last_scraped["scraped_at"].replace('Z', '+00:00'))
                    time_diff = datetime.now() - last_time
                    if time_diff.days > 0:
                        stats["last_scraped_ago"] = f"{time_diff.days} days ago"
                    elif time_diff.seconds > 3600:
                        hours = time_diff.seconds // 3600
                        stats["last_scraped_ago"] = f"{hours} hours ago"
                    elif time_diff.seconds > 60:
                        minutes = time_diff.seconds // 60
                        stats["last_scraped_ago"] = f"{minutes} minutes ago"
                    else:
                        stats["last_scraped_ago"] = "Just now"
                except:
                    stats["last_scraped_ago"] = "Unknown"
            else:
                stats["last_scraped_ago"] = "Never"

            return stats
        except Exception as e:
            console.print(f"[red]Failed to get stats: {e}[/red]")
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
                "last_scraped_ago": "Never"
            }

    def search_jobs(self, query: str, limit: int = 50) -> List[Dict]:
        search_term = f"%{query.lower()}%"
        cursor = self.conn.execute(
            "SELECT * FROM jobs WHERE LOWER(title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(summary) LIKE ? ORDER BY created_at DESC LIMIT ?",
            (search_term, search_term, search_term, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_unapplied_jobs(self, limit: int = 100) -> List[Dict]:
        cursor = self.conn.execute(
            "SELECT * FROM jobs WHERE applied = 0 OR applied IS NULL ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_job_count(
        self,
        site: Optional[str] = None,
        filters: Optional[Dict] = None,
        search_query: Optional[str] = None,
    ) -> int:
        query = "SELECT COUNT(*) FROM jobs"
        params: List[Union[str, int]] = []
        conditions = []

        if site:
            conditions.append("site = ?")
            params.append(site)

        if search_query:
            search_term = f"%{search_query}%"
            conditions.append("(title LIKE ? OR company LIKE ? OR summary LIKE ?)")
            params.extend([search_term, search_term, search_term])

        if filters:
            for key, value in filters.items():
                if key == "applied" and isinstance(value, bool):
                    conditions.append("applied = ?")
                    params.append(1 if value else 0)
                elif key == "experience" and value:
                    conditions.append("experience_level = ?")
                    params.append(value)
                elif key == "site" and value:
                    conditions.append("site = ?")
                    params.append(value)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        try:
            cursor = self.conn.execute(query, params)
            return cursor.fetchone()[0]
        except sqlite3.OperationalError as e:
            console.print(f"[red]Error fetching job count: {e}[/red]")
            return 0
