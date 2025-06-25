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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY, job_id TEXT UNIQUE, title TEXT, company TEXT, 
                    location TEXT, summary TEXT, url TEXT, search_keyword TEXT, site TEXT, 
                    scraped_at TEXT, applied INTEGER DEFAULT 0, status TEXT DEFAULT 'new',
                    raw_data TEXT, analysis_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_job(self, job_data: Union[Dict, JobRecord]) -> bool:
        if isinstance(job_data, dict):
            job_record = JobRecord(**{k: v for k, v in job_data.items() if k in JobRecord.__annotations__})
        else:
            job_record = job_data

        with self._get_connection() as conn:
            if self._is_duplicate(conn, job_record):
                return False
            
            conn.execute(
                "INSERT INTO jobs (job_id, title, company, location, url) VALUES (?, ?, ?, ?, ?)",
                (job_record.job_id, job_record.title, job_record.company, job_record.location, job_record.url)
            )
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

    def close(self):
        while not self._connection_pool.empty():
            self._connection_pool.get_nowait().close()

def get_job_db(profile: Optional[str] = None) -> "ModernJobDatabase":
    db_path = f"profiles/{profile}/{profile}.db" if profile else "data/jobs.db"
    return ModernJobDatabase(db_path)
