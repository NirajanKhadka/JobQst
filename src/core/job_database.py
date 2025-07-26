import sqlite3
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from contextlib import contextmanager
import threading
from queue import Queue

from .job_record import JobRecord
from .db_queries import DBQueries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModernJobDatabase:
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._connection_pool = Queue(maxsize=5)
        self._init_pool()
        self._init_database()
        logger.info(f"✅ Modern job database initialized: {self.db_path}")

    def _init_pool(self):
        for _ in range(5):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._connection_pool.put(conn)

    @contextmanager
    def _get_connection(self):
        conn = self._connection_pool.get(timeout=5)
        try:
            yield conn
        finally:
            self._connection_pool.put(conn)

    def _init_database(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY, 
                    job_id TEXT UNIQUE, 
                    title TEXT, 
                    company TEXT, 
                    location TEXT, 
                    summary TEXT, 
                    url TEXT, 
                    search_keyword TEXT, 
                    site TEXT, 
                    scraped_at TEXT, 
                    applied INTEGER DEFAULT 0, 
                    status TEXT DEFAULT 'scraped',
                    experience_level TEXT,
                    keywords TEXT,
                    job_description TEXT,
                    salary_range TEXT,
                    job_type TEXT,
                    remote_option TEXT,
                    requirements TEXT,
                    benefits TEXT,
                    match_score REAL DEFAULT 0,
                    processing_notes TEXT,
                    application_date TEXT,
                    application_status TEXT DEFAULT 'not_applied',
                    raw_data TEXT, 
                    analysis_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    -- Enhanced 2-worker system fields
                    employment_type TEXT,
                    required_skills TEXT,
                    job_requirements TEXT,
                    compatibility_score REAL DEFAULT 0.0,
                    analysis_confidence REAL DEFAULT 0.0,
                    extracted_benefits TEXT,
                    analysis_reasoning TEXT,
                    custom_logic_confidence REAL DEFAULT 0.0,
                    llm_processing_time REAL DEFAULT 0.0,
                    total_processing_time REAL DEFAULT 0.0,
                    processing_method TEXT DEFAULT 'unknown',
                    fallback_used INTEGER DEFAULT 0,
                    processed_at TEXT,
                    processing_worker_id INTEGER,
                    processing_time REAL DEFAULT 0.0,
                    error_message TEXT
                )
            """
            )
            conn.commit()

    def add_job(self, job_data: Union[Dict, JobRecord]) -> bool:
        if isinstance(job_data, dict):
            job_record = JobRecord(
                **{k: v for k, v in job_data.items() if k in JobRecord.__annotations__}
            )
        else:
            job_record = job_data

        with self._get_connection() as conn:
            if self._is_duplicate(conn, job_record):
                return False

            # Prepare all fields for insertion
            fields = [
                "job_id",
                "title",
                "company",
                "location",
                "url",
                "summary",
                "search_keyword",
                "site",
                "scraped_at",
                "status",
                "experience_level",
                "keywords",
                "job_description",
                "salary_range",
                "job_type",
                "remote_option",
                "requirements",
                "benefits",
                "match_score",
                "processing_notes",
                "application_date",
                "application_status",
                "raw_data",
                "analysis_data",
            ]

            # Create placeholders for SQL
            placeholders = ", ".join(["?" for _ in fields])
            field_names = ", ".join(fields)

            # Prepare values
            values = []
            for field in fields:
                if hasattr(job_record, field):
                    value = getattr(job_record, field)
                    # Convert lists/dicts to JSON strings
                    if isinstance(value, (list, dict)):
                        import json

                        value = json.dumps(value)
                    values.append(value)
                else:
                    values.append(None)

            conn.execute(f"INSERT INTO jobs ({field_names}) VALUES ({placeholders})", values)
            conn.commit()
            return True

    def _is_duplicate(self, conn, job_record: JobRecord) -> bool:
        if job_record.url:
            cursor = conn.execute("SELECT id FROM jobs WHERE url = ?", (job_record.url,))
            if cursor.fetchone():
                return True
        return False

    def get_jobs(self, **kwargs) -> List[Dict]:
        with self._get_connection() as conn:
            return DBQueries(conn).get_jobs(**kwargs)

    def get_job_stats(self) -> Dict:
        with self._get_connection() as conn:
            return DBQueries(conn).get_job_stats()

    def get_stats(self) -> Dict:
        """Alias for get_job_stats for backward compatibility."""
        return self.get_job_stats()

    def search_jobs(self, query: str, limit: int = 50) -> List[Dict]:
        with self._get_connection() as conn:
            return DBQueries(conn).search_jobs(query, limit)

    def get_unapplied_jobs(self, limit: int = 100) -> List[Dict]:
        with self._get_connection() as conn:
            return DBQueries(conn).get_unapplied_jobs(limit)

    def mark_applied(self, job_url: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("UPDATE jobs SET applied = 1 WHERE url = ?", (job_url,))
            conn.commit()
            return True

    def update_application_status(self, job_id: int, status: str, notes: str = None) -> bool:
        """Update application status for a job."""
        try:
            with self._get_connection() as conn:
                if notes:
                    conn.execute(
                        "UPDATE jobs SET application_status = ?, processing_notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (status, notes, job_id)
                    )
                else:
                    conn.execute(
                        "UPDATE jobs SET application_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (status, job_id)
                    )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            return False

    # Backward compatibility methods for tests
    def delete_job(self, job_id: int) -> bool:
        """Delete job by ID. Returns True if successful, False if not found."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False

    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Get job by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_jobs_by_company(self, company: str) -> List[Dict]:
        """Get jobs by company name."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE company LIKE ?", (f"%{company}%",))
            return [dict(row) for row in cursor.fetchall()]

    def get_jobs_by_location(self, location: str) -> List[Dict]:
        """Get jobs by location."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE location LIKE ?", (f"%{location}%",))
            return [dict(row) for row in cursor.fetchall()]

    def get_jobs_by_keyword(self, keyword: str) -> List[Dict]:
        """Get jobs by search keyword."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE search_keyword LIKE ?", (f"%{keyword}%",)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_jobs_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get jobs by date range."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE created_at BETWEEN ? AND ?", (start_date, end_date)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_job_count(self) -> int:
        """Get total number of jobs."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM jobs")
            return cursor.fetchone()[0]

    def get_companies(self) -> List[str]:
        """Get list of unique companies."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT company FROM jobs WHERE company IS NOT NULL")
            return [row[0] for row in cursor.fetchall()]

    def get_locations(self) -> List[str]:
        """Get list of unique locations."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT location FROM jobs WHERE location IS NOT NULL")
            return [row[0] for row in cursor.fetchall()]

    def get_keywords(self) -> List[str]:
        """Get list of unique search keywords."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT DISTINCT search_keyword FROM jobs WHERE search_keyword IS NOT NULL"
            )
            return [row[0] for row in cursor.fetchall()]

    def clear_all_jobs(self) -> bool:
        """Clear all jobs from database."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM jobs")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error clearing jobs: {e}")
            return False

    def backup_database(self, backup_path: str) -> bool:
        """Backup database to specified path."""
        try:
            import shutil

            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return False

    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False

    def get_all_jobs(self) -> List[Dict]:
        """Get all jobs from database."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_jobs_by_status(self, status: str, limit: int = None) -> List[Dict]:
        """Get jobs by status."""
        with self._get_connection() as conn:
            if limit:
                cursor = conn.execute("SELECT * FROM jobs WHERE status = ? LIMIT ?", (status, limit))
            else:
                cursor = conn.execute("SELECT * FROM jobs WHERE status = ?", (status,))
            return [dict(row) for row in cursor.fetchall()]

    def update_job(self, job_id: int, job_data: Dict) -> bool:
        """Update job with new data by ID."""
        try:
            with self._get_connection() as conn:
                # Build update query dynamically based on provided fields
                update_fields = []
                values = []
                
                for field, value in job_data.items():
                    if field != 'id':  # Don't update ID
                        update_fields.append(f"{field} = ?")
                        # Convert lists/dicts to JSON strings
                        if isinstance(value, (list, dict)):
                            import json
                            value = json.dumps(value)
                        values.append(value)
                
                if not update_fields:
                    return False
                
                # Add updated_at timestamp
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                values.append(job_id)
                
                query = f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = ?"
                conn.execute(query, values)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False

    def update_job_status(self, job_id: int, new_status: str) -> bool:
        """Update job status by ID."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_status, job_id),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False

    def update_job_url(self, job_id: int, new_url: str) -> bool:
        """Update job URL by ID."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_url, job_id),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating job URL: {e}")
            return False

    def close(self):
        while not self._connection_pool.empty():
            self._connection_pool.get_nowait().close()


# Backward compatibility alias for tests
JobDatabase = ModernJobDatabase


def get_job_db(profile: Optional[str] = None) -> "ModernJobDatabase":
    db_path = f"profiles/{profile}/{profile}.db" if profile else "data/jobs.db"
    return ModernJobDatabase(db_path)
