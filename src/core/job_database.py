import sqlite3
import json
import hashlib
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from contextlib import contextmanager
import threading
from queue import Queue
from dataclasses import dataclass

from .job_record import JobRecord
from .db_queries import DBQueries

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result from batch job insertion."""
    total_processed: int
    inserted_count: int
    skipped_duplicates: int
    failed_count: int
    errors: List[str]
    processing_time: float
    batch_id: str


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
                    -- Improved 2-worker system fields
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
                    error_message TEXT,
                    batch_id TEXT,
                    insertion_method TEXT DEFAULT 'single'
                )
            """
            )
            
            # Add missing columns for backward compatibility
            self._add_missing_columns(conn)
            
            # Create indexes for duplicate checking performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title_company "
                        "ON jobs(title, company)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title_location "
                        "ON jobs(title, location)")
    
    def _add_missing_columns(self, conn):
        """Add missing columns for backward compatibility."""
        try:
            # Get existing columns
            cursor = conn.execute("PRAGMA table_info(jobs)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # List of columns that should exist
            required_columns = [
                ('processed_at', 'TEXT'),
                ('processing_worker_id', 'INTEGER'),
                ('processing_time', 'REAL DEFAULT 0.0'),
                ('error_message', 'TEXT'),
                ('compatibility_score', 'REAL DEFAULT 0.0'),
                ('analysis_confidence', 'REAL DEFAULT 0.0'),
                ('processing_method', 'TEXT DEFAULT "unknown"'),
                ('fallback_used', 'INTEGER DEFAULT 0'),
                ('batch_id', 'TEXT'),
                ('insertion_method', 'TEXT DEFAULT "single"'),
                # AI Strategy Analysis Phase 2 fields
                ('semantic_score', 'REAL DEFAULT 0.0'),
                ('cache_status', 'TEXT DEFAULT "miss"'),
                ('profile_similarity', 'REAL DEFAULT 0.0'),
                ('embedding_cached', 'INTEGER DEFAULT 0'),
                ('html_cached', 'INTEGER DEFAULT 0'),
                # Smart Deduplication fields
                ('sources', 'TEXT'),  # JSON array of source sites
                ('source_urls', 'TEXT'),  # JSON array of all URLs
                ('source_sites', 'TEXT'),  # JSON array of site names
                ('merged_from_count', 'INTEGER DEFAULT 1'),
                ('merged_at', 'TEXT'),
                ('deduplication_method', 'TEXT'),
                # Location type and bookmarking
                ('location_type', 'TEXT'),  # remote, hybrid, onsite
                ('is_bookmarked', 'INTEGER DEFAULT 0'),
                ('bookmarked_at', 'TEXT'),
                # Notification tracking
                ('notification_sent', 'INTEGER DEFAULT 0'),
                ('notification_sent_at', 'TEXT')
            ]
            
            # Add missing columns
            for column_name, column_type in required_columns:
                if column_name not in existing_columns:
                    try:
                        conn.execute(f"ALTER TABLE jobs ADD COLUMN "
                                   f"{column_name} {column_type}")
                        logger.info(f"Added missing column: {column_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" not in str(e):
                            logger.warning(f"Could not add column "
                                         f"{column_name}: {e}")
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error adding missing columns: {e}")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at "
                        "ON jobs(scraped_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status "
                        "ON jobs(status)")
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

    def add_jobs_batch(self, jobs_data: List[Dict], 
                      batch_size: int = 100,
                      skip_duplicates: bool = True,
                      default_status: str = 'new') -> BatchResult:
        """
        Smart batch insert for multiple jobs with duplicate checking.
        
        Args:
            jobs_data: List of job dictionaries to insert
            batch_size: Number of jobs to process per transaction
            skip_duplicates: Whether to skip duplicate jobs
            default_status: Default status for new jobs
            
        Returns:
            BatchResult with detailed statistics
        """
        batch_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        
        total_processed = 0
        inserted_count = 0
        skipped_duplicates = 0
        failed_count = 0
        errors = []
        
        logger.info(f"Starting batch insert: {len(jobs_data)} jobs, "
                   f"batch_size={batch_size}, batch_id={batch_id}")
        
        try:
            # Process jobs in chunks
            for i in range(0, len(jobs_data), batch_size):
                chunk = jobs_data[i:i + batch_size]
                chunk_result = self._process_job_chunk(
                    chunk, batch_id, skip_duplicates, default_status
                )
                
                total_processed += chunk_result['processed']
                inserted_count += chunk_result['inserted']
                skipped_duplicates += chunk_result['skipped']
                failed_count += chunk_result['failed']
                errors.extend(chunk_result['errors'])
                
                logger.debug(f"Chunk {i//batch_size + 1}: "
                           f"inserted={chunk_result['inserted']}, "
                           f"skipped={chunk_result['skipped']}")
                
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            errors.append(f"Batch processing error: {str(e)}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = BatchResult(
            total_processed=total_processed,
            inserted_count=inserted_count,
            skipped_duplicates=skipped_duplicates,
            failed_count=failed_count,
            errors=errors,
            processing_time=processing_time,
            batch_id=batch_id
        )
        
        logger.info(f"Batch {batch_id} completed: "
                   f"inserted={inserted_count}, "
                   f"skipped={skipped_duplicates}, "
                   f"failed={failed_count}, "
                   f"time={processing_time:.2f}s")
        
        return result

    def _process_job_chunk(self, chunk: List[Dict], batch_id: str,
                          skip_duplicates: bool, default_status: str) -> Dict:
        """Process a single chunk of jobs in one transaction."""
        processed = 0
        inserted = 0
        skipped = 0
        failed = 0
        errors = []
        
        with self._get_connection() as conn:
            try:
                # Begin transaction
                conn.execute("BEGIN")
                
                # Bulk duplicate check for URLs (performance optimization)
                existing_urls = set()
                if skip_duplicates:
                    urls = [job.get('url', '') for job in chunk 
                           if job.get('url')]
                    if urls:
                        placeholders = ','.join(['?' for _ in urls])
                        cursor = conn.execute(
                            f"SELECT url FROM jobs WHERE url IN ({placeholders})",
                            urls
                        )
                        existing_urls = {row[0] for row in cursor.fetchall()}
                
                # Process each job in the chunk
                for job_data in chunk:
                    processed += 1
                    try:
                        # Quick duplicate check
                        if skip_duplicates and job_data.get('url') in existing_urls:
                            skipped += 1
                            continue
                        
                        # Convert to JobRecord
                        if isinstance(job_data, dict):
                            job_record = JobRecord(
                                **{k: v for k, v in job_data.items() 
                                  if k in JobRecord.__annotations__}
                            )
                        else:
                            job_record = job_data
                        
                        # Additional duplicate check for non-URL duplicates
                        if skip_duplicates and self._is_duplicate(conn, job_record):
                            skipped += 1
                            continue
                        
                        # Prepare job data for insertion
                        job_values = self._prepare_job_values(
                            job_record, batch_id, default_status
                        )
                        
                        # Insert job
                        fields = list(job_values.keys())
                        values = list(job_values.values())
                        placeholders = ','.join(['?' for _ in fields])
                        field_names = ','.join(fields)
                        
                        conn.execute(
                            f"INSERT INTO jobs ({field_names}) VALUES ({placeholders})",
                            values
                        )
                        inserted += 1
                        
                    except Exception as e:
                        failed += 1
                        error_msg = f"Job insert failed: {str(e)}"
                        errors.append(error_msg)
                        logger.debug(error_msg)
                
                # Commit transaction
                conn.commit()
                
            except Exception as e:
                # Rollback on chunk failure
                conn.rollback()
                error_msg = f"Chunk transaction failed: {str(e)}"
                errors.append(error_msg)
                failed = len(chunk)
                inserted = 0
                logger.error(error_msg)
        
        return {
            'processed': processed,
            'inserted': inserted,
            'skipped': skipped,
            'failed': failed,
            'errors': errors
        }

    def _prepare_job_values(self, job_record: JobRecord, batch_id: str,
                           default_status: str) -> Dict:
        """Prepare job values for insertion with batch metadata."""
        fields = [
            "job_id", "title", "company", "location", "url", "summary",
            "search_keyword", "site", "scraped_at", "status", "experience_level",
            "keywords", "job_description", "salary_range", "job_type",
            "remote_option", "requirements", "benefits", "match_score",
            "processing_notes", "application_date", "application_status",
            "raw_data", "analysis_data", "batch_id", "insertion_method"
        ]
        
        values = {}
        for field in fields:
            if field == 'batch_id':
                values[field] = batch_id
            elif field == 'insertion_method':
                values[field] = 'batch'
            elif field == 'status' and not hasattr(job_record, 'status'):
                values[field] = default_status
            elif hasattr(job_record, field):
                value = getattr(job_record, field)
                # Convert lists/dicts to JSON strings
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                values[field] = value
            else:
                values[field] = None
        
        return values

    def _is_duplicate(self, conn, job_record: JobRecord) -> bool:
        """
        Improved duplicate checking with multiple criteria.
        
        Checks in order of reliability:
        1. URL match (most reliable)
        2. Title + Company match (fallback)
        3. Title + Location match (last resort for missing company)
        """
        # Primary check: URL match
        if job_record.url:
            cursor = conn.execute("SELECT id FROM jobs WHERE url = ?", (job_record.url,))
            if cursor.fetchone():
                logger.info(f"Duplicate found by URL: {job_record.url}")
                return True
        
        # Secondary check: Title + Company match
        if job_record.title and job_record.company:
            # Safely convert to string and handle potential None/float values
            title_str = str(job_record.title).strip() if job_record.title is not None else ""
            company_str = str(job_record.company).strip() if job_record.company is not None else ""
            
            if title_str and company_str:
                cursor = conn.execute(
                    "SELECT id FROM jobs WHERE LOWER(title) = LOWER(?) AND LOWER(company) = LOWER(?)", 
                    (title_str, company_str)
                )
                if cursor.fetchone():
                    logger.info(f"Duplicate found by title+company: {title_str} at {company_str}")
                    return True
        
        # Tertiary check: Title + Location match (for cases where company name varies)
        if job_record.title and job_record.location and not job_record.company:
            # Safely convert to string and handle potential None/float values
            title_str = str(job_record.title).strip() if job_record.title is not None else ""
            location_str = str(job_record.location).strip() if job_record.location is not None else ""
            
            if title_str and location_str:
                cursor = conn.execute(
                    "SELECT id FROM jobs WHERE LOWER(title) = LOWER(?) AND LOWER(location) = LOWER(?)", 
                    (title_str, location_str)
                )
                if cursor.fetchone():
                    logger.info(f"Duplicate found by title+location: {title_str} in {location_str}")
                    return True
        
        return False

    def is_duplicate_job(self, job_data: Dict) -> bool:
        """
        Check if job data represents a duplicate using multiple criteria.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            bool: True if duplicate found, False otherwise
        """
        try:
            with self._get_connection() as conn:
                # Safely convert to string and handle potential None/float values
                job_url = str(job_data.get("url", "")).strip() if job_data.get("url") is not None else ""
                job_title = str(job_data.get("title", "")).strip() if job_data.get("title") is not None else ""
                job_company = str(job_data.get("company", "")).strip() if job_data.get("company") is not None else ""
                job_location = str(job_data.get("location", "")).strip() if job_data.get("location") is not None else ""
                
                # Primary check: URL match
                if job_url:
                    cursor = conn.execute("SELECT id FROM jobs WHERE url = ?", (job_url,))
                    if cursor.fetchone():
                        return True
                
                # Secondary check: Title + Company match
                if job_title and job_company:
                    cursor = conn.execute(
                        "SELECT id FROM jobs WHERE LOWER(title) = LOWER(?) AND LOWER(company) = LOWER(?)", 
                        (job_title, job_company)
                    )
                    if cursor.fetchone():
                        return True
                
                # Tertiary check: Title + Location match
                if job_title and job_location and not job_company:
                    cursor = conn.execute(
                        "SELECT id FROM jobs WHERE LOWER(title) = LOWER(?) AND LOWER(location) = LOWER(?)", 
                        (job_title, job_location)
                    )
                    if cursor.fetchone():
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
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
    
    def get_job_count(self, **kwargs) -> int:
        with self._get_connection() as conn:
            return DBQueries(conn).get_job_count(**kwargs)

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

    def get_job_by_url(self, url: str) -> Optional[Dict]:
        """Get job by URL for duplicate checking."""
        if not url:
            return None
        
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE url = ? LIMIT 1", (url,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_job_metadata(self, job_id: int, metadata: Dict) -> bool:
        """Update job metadata fields."""
        try:
            with self._get_connection() as conn:
                # Build update query dynamically based on provided metadata
                update_fields = []
                values = []
                
                for field, value in metadata.items():
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
            logger.error(f"Error updating job metadata {job_id}: {e}")
            return False

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

    def get_jobs_for_processing(self, limit: int = 50) -> List[Dict]:
        """Get jobs that need processing (scraped but not processed)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM jobs 
                    WHERE status IN ('scraped', 'new') 
                    AND (processed_at IS NULL OR processed_at = '')
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting jobs for processing: {e}")
            return []

    def update_job_analysis(self, job_id: str, analysis_data: Dict):
        """Update job analysis data."""
        try:
            with self._get_connection() as conn:
                # Convert analysis_data to JSON string for storage
                analysis_json = json.dumps(analysis_data)
                
                # Update the job with analysis data
                conn.execute("""
                    UPDATE jobs 
                    SET analysis_data = ?,
                        compatibility_score = ?,
                        processing_method = ?,
                        processed_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = ?
                """, (
                    analysis_json,
                    analysis_data.get('compatibility_score', 0.0),
                    analysis_data.get('processing_method', 'unknown'),
                    datetime.now().isoformat(),
                    job_id
                ))
                conn.commit()
                logger.info(f"Updated analysis data for job {job_id}")
        except Exception as e:
            logger.error(f"Error updating job analysis for {job_id}: {e}")

    def get_unprocessed_job_count(self) -> int:
        """Get count of jobs that need processing."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM jobs 
                    WHERE (processed_at IS NULL OR processed_at = '') 
                    AND status != 'processed'
                """)
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting unprocessed job count: {e}")
            return 0

    def get_system_status(self) -> Dict:
        """Get system status including database statistics."""
        try:
            with self._get_connection() as conn:
                # Get basic job counts
                cursor = conn.execute("SELECT COUNT(*) FROM jobs")
                total_jobs = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'scraped'")
                scraped_jobs = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'processed'")
                processed_jobs = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM jobs WHERE application_status = 'applied'")
                applied_jobs = cursor.fetchone()[0]
                
                # Get recent activity
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM jobs 
                    WHERE created_at > datetime('now', '-24 hours')
                """)
                recent_jobs = cursor.fetchone()[0]
                
                return {
                    "database_status": "healthy",
                    "total_jobs": total_jobs,
                    "scraped_jobs": scraped_jobs,
                    "processed_jobs": processed_jobs,
                    "applied_jobs": applied_jobs,
                    "recent_jobs_24h": recent_jobs,
                    "database_path": str(self.db_path),
                    "database_size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "database_status": "error",
                "error": str(e),
                "total_jobs": 0,
                "scraped_jobs": 0,
                "processed_jobs": 0,
                "applied_jobs": 0,
                "recent_jobs_24h": 0
            }

    def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Remove jobs older than specified days"""
        try:
            with self._get_connection() as conn:
                # Calculate the cutoff date
                cutoff_query = """
                    DELETE FROM jobs
                    WHERE scraped_at < datetime('now', '-{} days')
                    OR created_at < datetime('now', '-{} days')
                """.format(days_old, days_old)
                
                cursor = conn.execute(cutoff_query)
                deleted_count = cursor.rowcount
                
                logger.info(f"Cleaned up {deleted_count} jobs older than "
                            f"{days_old} days")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
            return 0

    def close(self):
        while not self._connection_pool.empty():
            self._connection_pool.get_nowait().close()

    def update_job_sources(self, job_id: int, sources: List[str], 
                          source_urls: List[str], merged_count: int = 1) -> bool:
        """Update job with source information from deduplication."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE jobs SET 
                        sources = ?,
                        source_urls = ?,
                        source_sites = ?,
                        merged_from_count = ?,
                        merged_at = ?,
                        deduplication_method = 'smart_merge',
                        status = 'merged'
                    WHERE id = ?
                """, (
                    json.dumps(sources),
                    json.dumps(source_urls), 
                    json.dumps(list(set(sources))),  # Unique sites
                    merged_count,
                    datetime.now().isoformat(),
                    job_id
                ))
                return True
        except Exception as e:
            logger.error(f"Error updating job sources: {e}")
            return False

    def add_job_with_deduplication(self, job_data: Dict[str, Any]) -> bool:
        """Add job with smart deduplication and merging."""
        from ..services.smart_deduplication_service import SmartDeduplicationService
        
        try:
            # Check for existing duplicates
            with self._get_connection() as conn:
                existing_jobs = []
                
                # Get potential duplicates by URL
                url = job_data.get('url', '')
                if url:
                    cursor = conn.execute("SELECT * FROM jobs WHERE url = ?", (url,))
                    existing_jobs.extend([dict(row) for row in cursor.fetchall()])
                
                # Get potential duplicates by title+company
                title = job_data.get('title', '')
                company = job_data.get('company', '')
                if title and company and not existing_jobs:
                    cursor = conn.execute(
                        "SELECT * FROM jobs WHERE LOWER(title) = LOWER(?) AND LOWER(company) = LOWER(?",
                        (title, company)
                    )
                    existing_jobs.extend([dict(row) for row in cursor.fetchall()])
                
                if existing_jobs:
                    # Merge with existing job
                    dedup_service = SmartDeduplicationService()
                    all_jobs = existing_jobs + [job_data]
                    merged_jobs, stats = dedup_service.find_and_merge_duplicates(all_jobs)
                    
                    if merged_jobs:
                        merged_job = merged_jobs[0]
                        # Update the existing job with merged data
                        existing_id = existing_jobs[0]['id']
                        self._update_job_data(existing_id, merged_job)
                        logger.info(f"Merged job into existing ID {existing_id}: {title}")
                        return True
                
                # No duplicates found, add as new job
                return self.add_job(job_data)
                
        except Exception as e:
            logger.error(f"Error adding job with deduplication: {e}")
            return False

    def _update_job_data(self, job_id: int, job_data: Dict[str, Any]) -> bool:
        """Update existing job with new data."""
        try:
            with self._get_connection() as conn:
                # Build update query dynamically
                update_fields = []
                values = []
                
                for field, value in job_data.items():
                    if field != 'id':  # Don't update ID
                        update_fields.append(f"{field} = ?")
                        if isinstance(value, (list, dict)):
                            values.append(json.dumps(value))
                        else:
                            values.append(value)
                
                if update_fields:
                    query = f"UPDATE jobs SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?"
                    values.extend([datetime.now().isoformat(), job_id])
                    conn.execute(query, values)
                    return True
                    
        except Exception as e:
            logger.error(f"Error updating job data: {e}")
            return False

    def bookmark_job(self, job_id: int, bookmarked: bool = True) -> bool:
        """Bookmark or unbookmark a job."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE jobs SET 
                        is_bookmarked = ?,
                        bookmarked_at = ?
                    WHERE id = ?
                """, (
                    1 if bookmarked else 0,
                    datetime.now().isoformat() if bookmarked else None,
                    job_id
                ))
                return True
        except Exception as e:
            logger.error(f"Error bookmarking job: {e}")
            return False

    def get_bookmarked_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all bookmarked jobs."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM jobs 
                    WHERE is_bookmarked = 1 
                    ORDER BY bookmarked_at DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting bookmarked jobs: {e}")
            return []

    def detect_location_type(self, job_data: Dict[str, Any]) -> str:
        """Detect if job is remote, hybrid, or onsite based on description."""
        text_fields = [
            job_data.get('title', ''),
            job_data.get('description', ''),
            job_data.get('job_description', ''),
            job_data.get('location', ''),
            job_data.get('summary', '')
        ]
        
        full_text = ' '.join(str(field) for field in text_fields if field).lower()
        
        # Remote indicators
        remote_keywords = ['remote', 'work from home', 'wfh', 'telecommute', 'distributed']
        # Hybrid indicators  
        hybrid_keywords = ['hybrid', 'flexible', 'remote-friendly', 'work from office sometimes']
        # Onsite indicators
        onsite_keywords = ['on-site', 'onsite', 'in-office', 'office-based']
        
        remote_count = sum(1 for keyword in remote_keywords if keyword in full_text)
        hybrid_count = sum(1 for keyword in hybrid_keywords if keyword in full_text)
        onsite_count = sum(1 for keyword in onsite_keywords if keyword in full_text)
        
        if remote_count > 0 and hybrid_count == 0:
            return 'remote'
        elif hybrid_count > 0 or (remote_count > 0 and onsite_count > 0):
            return 'hybrid'
        elif onsite_count > 0:
            return 'onsite'
        else:
            return 'unknown'

    def update_location_types(self) -> int:
        """Update location types for all jobs that don't have them set."""
        try:
            with self._get_connection() as conn:
                # Get jobs without location type
                cursor = conn.execute("""
                    SELECT id, title, description, job_description, location, summary 
                    FROM jobs 
                    WHERE location_type IS NULL OR location_type = ''
                """)
                
                jobs_to_update = cursor.fetchall()
                updated_count = 0
                
                for job in jobs_to_update:
                    job_dict = dict(job)
                    location_type = self.detect_location_type(job_dict)
                    
                    conn.execute("""
                        UPDATE jobs SET location_type = ? WHERE id = ?
                    """, (location_type, job_dict['id']))
                    
                    updated_count += 1
                
                logger.info(f"Updated location types for {updated_count} jobs")
                return updated_count
                
        except Exception as e:
            logger.error(f"Error updating location types: {e}")
            return 0


# Backward compatibility alias for tests
JobDatabase = ModernJobDatabase


def get_job_db(profile: Optional[str] = None):
    """Get job database instance based on configuration"""
    
    # Check if PostgreSQL is configured
    database_type = os.getenv('DATABASE_TYPE', 'sqlite')
    
    if database_type == 'postgresql':
        # Import here to avoid circular imports
        from .postgresql_database import PostgreSQLJobDatabase
        return PostgreSQLJobDatabase(profile_name=profile)
    else:
        # Use SQLite (default)
        db_path = (f"profiles/{profile}/{profile}.db"
                   if profile else "data/jobs.db")
        return ModernJobDatabase(db_path)
