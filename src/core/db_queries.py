import sqlite3
import json
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from rich.console import Console

console = Console()

class DBQueries:
    def __init__(self, db_connection):
        self.conn = db_connection

    def get_jobs(self, limit: int = 100, offset: int = 0, site: Optional[str] = None, filters: Optional[Dict] = None, search_query: Optional[str] = None) -> List[Dict]:
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
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM jobs")
            stats['total_jobs'] = cursor.fetchone()['count']
            
            cursor = self.conn.execute("SELECT site, COUNT(*) as count FROM jobs GROUP BY site ORDER BY count DESC")
            stats['jobs_by_site'] = dict(cursor.fetchall())
            
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM jobs WHERE scraped_at > ?", (yesterday,))
            stats['recent_jobs'] = cursor.fetchone()['count']
            
            return stats
        except Exception as e:
            console.print(f"[red]Failed to get stats: {e}[/red]")
            return {}

    def search_jobs(self, query: str, limit: int = 50) -> List[Dict]:
        search_term = f"%{query.lower()}%"
        cursor = self.conn.execute(
            "SELECT * FROM jobs WHERE LOWER(title) LIKE ? OR LOWER(company) LIKE ? OR LOWER(summary) LIKE ? ORDER BY created_at DESC LIMIT ?",
            (search_term, search_term, search_term, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_unapplied_jobs(self, limit: int = 100) -> List[Dict]:
        cursor = self.conn.execute("SELECT * FROM jobs WHERE applied = 0 OR applied IS NULL ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]