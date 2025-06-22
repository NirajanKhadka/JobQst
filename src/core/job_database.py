#!/usr/bin/env python3
"""
Modern Job Database - Simple, robust, and easy to debug
Enhanced with better error handling and modern Python patterns.
"""

import sqlite3
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading
from queue import Queue
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobRecord:
    """Simple job record structure."""
    title: str
    company: str
    location: str = ""
    summary: str = ""
    url: str = ""
    search_keyword: str = ""
    site: str = "unknown"
    scraped_at: str = ""
    job_id: str = ""
    raw_data: Optional[Dict[str, Any]] = None
    analysis_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}
        if self.analysis_data is None:
            self.analysis_data = {}
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
        if not self.job_id:
            self.job_id = self._generate_job_id()
    
    def _generate_job_id(self) -> str:
        """Generate a unique job ID."""
        content = f"{self.title}{self.company}{self.url}{self.scraped_at}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_hash(self) -> str:
        """Get hash for duplicate detection."""
        content = f"{self.title.lower()}{self.company.lower()}"
        return hashlib.md5(content.encode()).hexdigest()

class ModernJobDatabase:
    """
    Modern job database with simple, robust operations.
    Enhanced error handling and easy debugging.
    """
    
    def __init__(self, db_path: str = "data/jobs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._connection_pool = Queue(maxsize=5)
        self._init_pool()
        self._init_database()
        logger.info(f"✅ Modern job database initialized: {self.db_path}")
    
    def _init_pool(self):
        """Initialize connection pool."""
        for _ in range(5):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._connection_pool.put(conn)
    
    @property
    def conn(self):
        """Backward compatibility property for direct connection access."""
        # Get a connection from the pool for backward compatibility
        try:
            conn = self._connection_pool.get(timeout=1)
            # Return it immediately to avoid blocking the pool
            self._connection_pool.put(conn)
            return conn
        except Exception:
            # If pool is empty, create a temporary connection
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
    
    @property
    def cursor(self):
        """Backward compatibility property for direct cursor access."""
        return self.conn.cursor()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection from pool."""
        conn = None
        try:
            conn = self._connection_pool.get(timeout=5)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                try:
                    self._connection_pool.put(conn)
                except:
                    # If pool is full, close connection
                    conn.close()
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with self._get_connection() as conn:
                # Check if jobs table exists
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='jobs'
                """)
                
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    # Create new table with full schema
                    conn.execute("""
                        CREATE TABLE jobs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            job_id TEXT UNIQUE,
                            title TEXT NOT NULL,
                            company TEXT NOT NULL,
                            location TEXT,
                            summary TEXT,
                            url TEXT,
                            search_keyword TEXT,
                            site TEXT,
                            scraped_at TEXT,
                            raw_data TEXT,
                            analysis_data TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            applied INTEGER DEFAULT 0
                        )
                    """)
                    
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)
                    """)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_title_company ON jobs(title, company)
                    """)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_site ON jobs(site)
                    """)
                    conn.execute("""
                        CREATE INDEX IF NOT EXISTS idx_scraped_at ON jobs(scraped_at)
                    """)
                    
                    conn.commit()
                    logger.info("✅ Database tables initialized")
                else:
                    # Check if job_id column exists
                    cursor = conn.execute("PRAGMA table_info(jobs)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    if 'job_id' not in columns:
                        # Add job_id column to existing table
                        logger.info("🔄 Adding job_id column to existing database...")
                        conn.execute("ALTER TABLE jobs ADD COLUMN job_id TEXT")
                        conn.execute("CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)")
                        
                        # Generate job_id for existing records
                        cursor = conn.execute("SELECT id, title, company, url, scraped_at FROM jobs WHERE job_id IS NULL OR job_id = ''")
                        existing_jobs = cursor.fetchall()
                        
                        for job_row in existing_jobs:
                            job_id, title, company, url, scraped_at = job_row
                            # Generate job_id based on existing data
                            content = f"{title}{company}{url}{scraped_at or ''}"
                            job_id_hash = hashlib.md5(content.encode()).hexdigest()[:12]
                            
                            conn.execute("UPDATE jobs SET job_id = ? WHERE id = ?", (job_id_hash, job_id))
                        
                        conn.commit()
                        logger.info(f"✅ Added job_id column and populated {len(existing_jobs)} existing records")
                    
                    # Check if raw_data and analysis_data columns exist
                    if 'raw_data' not in columns:
                        logger.info("🔄 Adding raw_data column to existing database...")
                        conn.execute("ALTER TABLE jobs ADD COLUMN raw_data TEXT")
                        conn.commit()
                    
                    if 'analysis_data' not in columns:
                        logger.info("🔄 Adding analysis_data column to existing database...")
                        conn.execute("ALTER TABLE jobs ADD COLUMN analysis_data TEXT")
                        conn.commit()
                    
                    if 'applied' not in columns:
                        logger.info("🔄 Adding applied column to existing database...")
                        conn.execute("ALTER TABLE jobs ADD COLUMN applied INTEGER DEFAULT 0")
                        conn.commit()
                    
                    # Check if status column exists
                    if 'status' not in columns:
                        logger.info("🔄 Adding status column to existing database...")
                        conn.execute("ALTER TABLE jobs ADD COLUMN status TEXT DEFAULT 'new'")
                        conn.commit()
                    
                    # Make job_hash nullable if it exists and is NOT NULL
                    if 'job_hash' in columns:
                        cursor = conn.execute("PRAGMA table_info(jobs)")
                        columns_info = cursor.fetchall()
                        job_hash_info = next((col for col in columns_info if col[1] == 'job_hash'), None)
                        if job_hash_info and job_hash_info[3] == 1:  # NOT NULL constraint
                            logger.info("🔄 Making job_hash nullable...")
                            # SQLite doesn't support ALTER COLUMN to change NOT NULL, so we need to recreate
                            # For now, we'll handle this in the add_job method
                    
                    logger.info("✅ Database schema updated")
                
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self.get_job_stats()
    
    def add_job(self, job_data: Union[Dict, JobRecord]) -> bool:
        """
        Add a job to the database.
        Returns True if added, False if duplicate.
        """
        try:
            # Convert to JobRecord if needed
            if isinstance(job_data, dict):
                # Extract only the fields that JobRecord supports
                supported_fields = {
                    'title', 'company', 'location', 'summary', 'url', 
                    'search_keyword', 'site', 'scraped_at', 'job_id'
                }
                
                # Create a clean dict with only supported fields
                clean_data = {}
                for key, value in job_data.items():
                    if key in supported_fields:
                        clean_data[key] = value
                    elif key == 'found_by_keyword':
                        clean_data['search_keyword'] = value
                    elif key == 'source':
                        clean_data['site'] = value
                    elif key == 'posted_date':
                        clean_data['scraped_at'] = value
                
                # Add raw_data for any extra fields
                clean_data['raw_data'] = job_data
                
                job_record = JobRecord(**clean_data)
            else:
                job_record = job_data
            
            with self._get_connection() as conn:
                # Check for duplicates
                if self._is_duplicate(conn, job_record):
                    logger.info(f"🔍 Duplicate job found: {job_record.title} at {job_record.company}")
                    return False
                
                # Check if job_hash column exists and is NOT NULL
                cursor = conn.execute("PRAGMA table_info(jobs)")
                columns_info = cursor.fetchall()
                job_hash_info = next((col for col in columns_info if col[1] == 'job_hash'), None)
                has_job_hash_not_null = job_hash_info and job_hash_info[3] == 1
                
                if has_job_hash_not_null:
                    # Use old schema with job_hash
                    job_hash = job_record.get_hash()
                    conn.execute("""
                        INSERT INTO jobs (
                            job_hash, title, company, location, summary, url,
                            search_keyword, site, scraped_at, raw_data, analysis_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job_hash,
                        job_record.title,
                        job_record.company,
                        job_record.location,
                        job_record.summary,
                        job_record.url,
                        job_record.search_keyword,
                        job_record.site,
                        job_record.scraped_at,
                        json.dumps(job_record.raw_data),
                        json.dumps(job_record.analysis_data)
                    ))
                else:
                    # Use new schema with job_id
                    conn.execute("""
                        INSERT INTO jobs (
                            job_id, title, company, location, summary, url,
                            search_keyword, site, scraped_at, raw_data, analysis_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        job_record.job_id,
                        job_record.title,
                        job_record.company,
                        job_record.location,
                        job_record.summary,
                        job_record.url,
                        job_record.search_keyword,
                        job_record.site,
                        job_record.scraped_at,
                        json.dumps(job_record.raw_data),
                        json.dumps(job_record.analysis_data)
                    ))
                
                conn.commit()
                logger.info(f"✅ Job added: {job_record.title} at {job_record.company}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to add job: {e}")
            return False
    
    def _is_duplicate(self, conn, job_record: JobRecord) -> bool:
        """Check if a job is a duplicate based on URL or a combination of title, company, and location."""
        try:
            # Method 1: Check URL (most reliable)
            if job_record.url:
                cursor = conn.execute("SELECT id FROM jobs WHERE url = ?", (job_record.url,))
                if cursor.fetchone():
                    logger.debug(f"Duplicate found by URL: {job_record.url}")
                    return True

            # Method 2: Check job_id
            if job_record.job_id:
                cursor = conn.execute("SELECT id FROM jobs WHERE job_id = ?", (job_record.job_id,))
                if cursor.fetchone():
                    logger.debug(f"Duplicate found by job_id: {job_record.job_id}")
                    return True
            
            # Method 3: Check title, company, AND location for non-URL jobs
            cursor = conn.execute("""
                SELECT id FROM jobs 
                WHERE LOWER(title) = LOWER(?) AND LOWER(company) = LOWER(?) AND LOWER(location) = LOWER(?)
            """, (job_record.title, job_record.company, job_record.location))
            
            if cursor.fetchone():
                logger.debug(f"Duplicate found by content: {job_record.title} at {job_record.company}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Duplicate check failed: {e}")
            return False # Fail safe
    
    def get_jobs(self, limit: int = 100, offset: int = 0, site: Optional[str] = None, filters: Optional[Dict] = None, search_query: Optional[str] = None) -> List[Dict]:
        """
        Get jobs from the database with optional filters and a search query.
        """
        with self._get_connection() as conn:
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
            
            if filters:
                for key, value in filters.items():
                    if value is None or value == '':
                        continue
                    if key in ['location', 'site']:
                        conditions.append(f"{key} LIKE ?")
                        params.append(f"%{value}%")
                    elif key == 'applied' and value in ['true', 'false']:
                        # This column doesn't exist yet, but this prepares for it
                        pass
                    elif key == 'experience' and value:
                        conditions.append("json_extract(analysis_data, '$.requirements.experience_level') LIKE ?")
                        params.append(f"%{value}%")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            try:
                cursor = conn.execute(query, params)
                jobs = [dict(row) for row in cursor.fetchall()]
                logger.info(f"✅ Retrieved {len(jobs)} jobs with query: {query}")
                return jobs
            except sqlite3.OperationalError as e:
                logger.error(f"❌ Error fetching jobs: {e}. Query was: {query}")
                return []
    
    def get_job_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                stats = {}
                
                # Total jobs
                cursor = conn.execute("SELECT COUNT(*) as count FROM jobs")
                stats['total_jobs'] = cursor.fetchone()['count']
                
                # Jobs by site
                cursor = conn.execute("""
                    SELECT site, COUNT(*) as count 
                    FROM jobs 
                    GROUP BY site 
                    ORDER BY count DESC
                """)
                stats['jobs_by_site'] = dict(cursor.fetchall())
                
                # Recent jobs (last 24 hours)
                yesterday = (datetime.now() - timedelta(days=1)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) as count 
                    FROM jobs 
                    WHERE scraped_at > ?
                """, (yesterday,))
                stats['recent_jobs'] = cursor.fetchone()['count']
                
                # Database size
                cursor = conn.execute("SELECT COUNT(*) as count FROM jobs")
                stats['database_size'] = cursor.fetchone()['count']
                
                logger.info(f"✅ Retrieved database stats: {stats['total_jobs']} total jobs")
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {'total_jobs': 0, 'jobs_by_site': {}, 'recent_jobs': 0, 'database_size': 0}
    
    def search_jobs(self, query: str, limit: int = 50) -> List[Dict]:
        """Search jobs by title, company, or summary."""
        try:
            with self._get_connection() as conn:
                search_term = f"%{query.lower()}%"
                
                cursor = conn.execute("""
                    SELECT * FROM jobs 
                    WHERE LOWER(title) LIKE ? 
                       OR LOWER(company) LIKE ? 
                       OR LOWER(summary) LIKE ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (search_term, search_term, search_term, limit))
                
                rows = cursor.fetchall()
                jobs = []
                
                for row in rows:
                    job = dict(row)
                    try:
                        job['raw_data'] = json.loads(job['raw_data']) if job['raw_data'] else {}
                        job['analysis_data'] = json.loads(job['analysis_data']) if job['analysis_data'] else {}
                    except:
                        job['raw_data'] = {}
                        job['analysis_data'] = {}
                    
                    jobs.append(job)
                
                logger.info(f"✅ Search found {len(jobs)} jobs for '{query}'")
                return jobs
                
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up jobs older than specified days."""
        try:
            with self._get_connection() as conn:
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                cursor = conn.execute(
                    "DELETE FROM jobs WHERE scraped_at < ?",
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"✅ Cleaned up {deleted_count} old jobs")
                return deleted_count
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return 0

    def clear_all_jobs(self) -> bool:
        """Clear all jobs from the database for a fresh start."""
        try:
            with self._get_connection() as conn:
                # Get count before deletion
                cursor = conn.execute("SELECT COUNT(*) FROM jobs")
                result = cursor.fetchone()
                job_count = result[0] if result else 0
                
                # Delete all jobs
                conn.execute("DELETE FROM jobs")
                conn.commit()
                
                logger.info(f"✅ Cleared all {job_count} jobs from database")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to clear jobs: {e}")
            return False
    
    def get_duplicates(self) -> List[Dict]:
        """Find potential duplicate jobs."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT title, company, COUNT(*) as count
                    FROM jobs 
                    GROUP BY LOWER(title), LOWER(company)
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                """)
                
                duplicates = []
                for row in cursor.fetchall():
                    duplicates.append(dict(row))
                
                logger.info(f"✅ Found {len(duplicates)} potential duplicate groups")
                return duplicates
                
        except Exception as e:
            logger.error(f"❌ Duplicate detection failed: {e}")
            return []
    
    def get_unique_sites(self) -> List[str]:
        """Get a list of unique job sites from the database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT DISTINCT site FROM jobs WHERE site IS NOT NULL AND site != ''")
                sites = [row[0] for row in cursor.fetchall()]
                return sites
        except Exception as e:
            logger.error(f"❌ Failed to get unique sites: {e}")
            return []
    
    def close(self):
        """Close all connections in the pool."""
        logger.info("Closing database connections...")
        while not self._connection_pool.empty():
            try:
                conn = self._connection_pool.get_nowait()
                conn.close()
            except Exception:
                break
    
    def get_all_jobs(self, limit: int = 1000) -> List[Dict]:
        """Get all jobs from the database."""
        return self.get_jobs(limit=limit)
    
    def add_jobs_batch(self, jobs: List[Dict]) -> int:
        """Add multiple jobs in a more performant batch operation."""
        added_count = 0
        
        # Use a set to track processed URLs or job_ids to avoid duplicates within the batch
        processed_identifiers = set()

        jobs_to_insert = []
        for job_data in jobs:
            try:
                # Basic validation
                if not job_data.get("title") or not job_data.get("company"):
                    continue

                # Create a unique identifier for the job to prevent duplicates within the batch
                identifier = job_data.get("url") or job_data.get("job_id")
                if not identifier:
                    identifier = f"{job_data['title']}{job_data['company']}"

                if identifier in processed_identifiers:
                    continue
                
                job_record = JobRecord(**{k: v for k, v in job_data.items() if k in JobRecord.__annotations__})
                
                # Check for duplicates in the database before adding to the batch
                with self._get_connection() as conn_check:
                    if self._is_duplicate(conn_check, job_record):
                        logger.info(f"🔍 Duplicate job found (skipping): {job_record.title}")
                        continue

                jobs_to_insert.append(job_record)
                processed_identifiers.add(identifier)
                
            except Exception as e:
                logger.warning(f"⚠️ Could not process job for batch insert: {job_data.get('title')} - {e}")

        if not jobs_to_insert:
            return 0
            
        try:
            with self._get_connection() as conn:
                conn.execute("BEGIN TRANSACTION")
                try:
                    for job in jobs_to_insert:
                        # Use the new schema with job_id
                        conn.execute("""
                            INSERT OR IGNORE INTO jobs (
                                job_id, title, company, location, summary, url,
                                search_keyword, site, scraped_at, raw_data, analysis_data, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            job.job_id,
                            job.title,
                            job.company,
                            job.location,
                            job.summary,
                            job.url,
                            job.search_keyword,
                            job.site,
                            job.scraped_at,
                            json.dumps(job.raw_data),
                            json.dumps(job.analysis_data),
                            job_data.get("status", "new") # Add status from dict
                        ))
                    conn.commit()
                    added_count = len(jobs_to_insert)
                    logger.info(f"✅ Batch inserted {added_count} new jobs.")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"❌ Batch insert failed, transaction rolled back: {e}")
                    # Fallback to individual inserts if batch fails
                    added_count = self._add_jobs_individually(jobs_to_insert)

        except Exception as e:
            logger.error(f"❌ Failed to get connection for batch insert: {e}")
            added_count = self._add_jobs_individually(jobs_to_insert)
            
        return added_count

    def _add_jobs_individually(self, jobs: List[JobRecord]) -> int:
        """Fallback to add jobs one by one."""
        count = 0
        for job in jobs:
            if self.add_job(job):
                count += 1
        return count
    
    def get_job_count(self, filters: Optional[Dict] = None, search_query: Optional[str] = None) -> int:
        """Get the total number of jobs matching the filters."""
        with self._get_connection() as conn:
            query = "SELECT COUNT(*) FROM jobs"
            params: List[Union[str, int]] = []
            conditions = []

            if search_query:
                search_term = f"%{search_query}%"
                conditions.append("(title LIKE ? OR company LIKE ? OR summary LIKE ?)")
                params.extend([search_term, search_term, search_term])

            if filters:
                for key, value in filters.items():
                    if value is None or value == '':
                        continue
                    if key == 'site':
                        conditions.append("site LIKE ?")
                        params.append(f"%{value}%")
                    elif key == 'applied' and value in ['true', 'false']:
                        # This column doesn't exist yet, but this prepares for it
                        pass
                    elif key == 'experience' and value:
                        conditions.append("json_extract(analysis_data, '$.requirements.experience_level') LIKE ?")
                        params.append(f"%{value}%")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            try:
                cursor = conn.execute(query, params)
                count = cursor.fetchone()[0]
                return count
            except sqlite3.OperationalError as e:
                logger.error(f"❌ Error getting job count: {e}. Query: {query}")
                return 0
    
    def mark_applied(self, job_url: str, status: str = 'Applied') -> bool:
        """Mark a job as applied by its URL."""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "UPDATE jobs SET applied = 1, updated_at = CURRENT_TIMESTAMP WHERE url = ?",
                    (job_url,)
                )
                conn.commit()
                logger.info(f"✅ Marked job as applied: {job_url}")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to mark job as applied: {e}")
            return False

    def get_job_by_id(self, job_id: int) -> Optional[Dict]:
        """Get a single job by its primary key ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get job by id {job_id}: {e}")
            return None

# Global database instance
_job_db = None
_db_lock = threading.Lock()

def get_job_db(profile: str = None, db_path: str = None) -> ModernJobDatabase:
    """
    Get database instance for a specific profile or use default path.
    
    Args:
        profile: Profile name (e.g., 'Nirajan', 'StressTest')
        db_path: Direct database path (overrides profile)
    
    Returns:
        ModernJobDatabase instance
    """
    global _job_db
    
    # Determine the database path
    if db_path:
        # Use provided path directly
        final_db_path = db_path
    elif profile:
        # Use profile-specific database
        final_db_path = f"profiles/{profile}/{profile}.db"
    else:
        # Use default database
        final_db_path = "data/jobs.db"
    
    # For now, always create a new instance to support multiple databases
    # In the future, we could implement a database pool per profile
    return ModernJobDatabase(final_db_path)

def close_job_db():
    """Close the global job database connection."""
    global _job_db
    if _job_db:
        _job_db.close()
        _job_db = None

# Backward compatibility alias
JobDatabase = ModernJobDatabase
