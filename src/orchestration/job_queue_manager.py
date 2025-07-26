#!/usr/bin/env python3
"""
Job Queue Manager - Handles job queue operations and status tracking
Optimized for high-performance producer-consumer job processing
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job processing status enumeration."""
    SCRAPED = "scraped"           # URL collected, ready for processing
    PROCESSING = "processing"     # Currently being processed
    COMPLETED = "completed"       # Successfully processed
    FAILED = "failed"            # Processing failed
    RETRY = "retry"              # Marked for retry
    DEAD_LETTER = "dead_letter"  # Failed too many times


class JobPriority(int, Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class JobQueueItem:
    """Job queue item data structure."""
    id: Optional[int] = None
    url: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    source_site: str = ""
    search_keyword: str = ""
    status: JobStatus = JobStatus.SCRAPED
    priority: JobPriority = JobPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 3
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    worker_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class JobQueueManager:
    """High-performance job queue manager with status tracking and retry logic."""
    
    def __init__(self, db_path: str = "job_queue.db", max_connections: int = 10):
        """
        Initialize job queue manager.
        
        Args:
            db_path: Path to SQLite database
            max_connections: Maximum database connections
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self._local = threading.local()
        self._initialize_database()
        
        logger.info(f"JobQueueManager initialized: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
        
        return self._local.connection
    
    @contextmanager
    def _get_cursor(self):
        """Get database cursor with automatic commit/rollback."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def _initialize_database(self):
        """Initialize database schema."""
        with self._get_cursor() as cursor:
            # Create job queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT DEFAULT '',
                    company TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    source_site TEXT DEFAULT '',
                    search_keyword TEXT DEFAULT '',
                    status TEXT DEFAULT 'scraped',
                    priority INTEGER DEFAULT 2,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    processed_at TEXT,
                    error_message TEXT,
                    processing_time REAL,
                    worker_id TEXT,
                    metadata TEXT
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON job_queue(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_priority ON job_queue(priority DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON job_queue(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_priority ON job_queue(status, priority DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_site ON job_queue(source_site)")
            
            # Create job processing stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    avg_processing_time REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, status)
                )
            """)
            
            logger.info("Database schema initialized")
    
    def add_job(self, job: JobQueueItem) -> bool:
        """
        Add job to queue.
        
        Args:
            job: Job queue item
            
        Returns:
            bool: True if added successfully
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute("""
                    INSERT OR IGNORE INTO job_queue 
                    (url, title, company, location, source_site, search_keyword, 
                     status, priority, max_retries, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job.url,
                    job.title,
                    job.company,
                    job.location,
                    job.source_site,
                    job.search_keyword,
                    job.status.value,
                    job.priority.value,
                    job.max_retries,
                    json.dumps(job.metadata) if job.metadata else None
                ))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error adding job to queue: {e}")
            return False
    
    def add_jobs_batch(self, jobs: List[JobQueueItem]) -> int:
        """
        Add multiple jobs in batch for better performance.
        
        Args:
            jobs: List of job queue items
            
        Returns:
            int: Number of jobs added
        """
        if not jobs:
            return 0
        
        try:
            with self._get_cursor() as cursor:
                job_data = [
                    (
                        job.url,
                        job.title,
                        job.company,
                        job.location,
                        job.source_site,
                        job.search_keyword,
                        job.status.value,
                        job.priority.value,
                        job.max_retries,
                        json.dumps(job.metadata) if job.metadata else None
                    )
                    for job in jobs
                ]
                
                cursor.executemany("""
                    INSERT OR IGNORE INTO job_queue 
                    (url, title, company, location, source_site, search_keyword, 
                     status, priority, max_retries, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, job_data)
                
                added_count = cursor.rowcount
                logger.info(f"Added {added_count} jobs to queue in batch")
                return added_count
                
        except Exception as e:
            logger.error(f"Error adding jobs batch to queue: {e}")
            return 0
    
    def get_next_jobs(self, limit: int = 10, worker_id: str = None) -> List[JobQueueItem]:
        """
        Get next jobs for processing with proper locking.
        
        Args:
            limit: Maximum number of jobs to retrieve
            worker_id: Worker identifier
            
        Returns:
            List of job queue items
        """
        try:
            with self._get_cursor() as cursor:
                # Get jobs with priority ordering and lock them
                cursor.execute("""
                    UPDATE job_queue 
                    SET status = 'processing', 
                        worker_id = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id IN (
                        SELECT id FROM job_queue 
                        WHERE status IN ('scraped', 'retry')
                        ORDER BY priority DESC, created_at ASC
                        LIMIT ?
                    )
                """, (worker_id, limit))
                
                if cursor.rowcount == 0:
                    return []
                
                # Retrieve the locked jobs
                cursor.execute("""
                    SELECT * FROM job_queue 
                    WHERE status = 'processing' AND worker_id = ?
                    ORDER BY priority DESC, created_at ASC
                    LIMIT ?
                """, (worker_id, limit))
                
                jobs = []
                for row in cursor.fetchall():
                    job = JobQueueItem(
                        id=row['id'],
                        url=row['url'],
                        title=row['title'],
                        company=row['company'],
                        location=row['location'],
                        source_site=row['source_site'],
                        search_keyword=row['search_keyword'],
                        status=JobStatus(row['status']),
                        priority=JobPriority(row['priority']),
                        retry_count=row['retry_count'],
                        max_retries=row['max_retries'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        processed_at=row['processed_at'],
                        error_message=row['error_message'],
                        processing_time=row['processing_time'],
                        worker_id=row['worker_id'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None
                    )
                    jobs.append(job)
                
                logger.info(f"Retrieved {len(jobs)} jobs for processing")
                return jobs
                
        except Exception as e:
            logger.error(f"Error getting next jobs: {e}")
            return []
    
    def update_job_status(self, job_id: int, status: JobStatus, 
                         error_message: str = None, processing_time: float = None) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            error_message: Error message if failed
            processing_time: Processing time in seconds
            
        Returns:
            bool: True if updated successfully
        """
        try:
            with self._get_cursor() as cursor:
                update_fields = [
                    "status = ?",
                    "updated_at = CURRENT_TIMESTAMP"
                ]
                params = [status.value]
                
                if status == JobStatus.COMPLETED:
                    update_fields.append("processed_at = CURRENT_TIMESTAMP")
                
                if error_message:
                    update_fields.append("error_message = ?")
                    params.append(error_message)
                
                if processing_time is not None:
                    update_fields.append("processing_time = ?")
                    params.append(processing_time)
                
                # Handle retry logic
                if status == JobStatus.FAILED:
                    update_fields.append("retry_count = retry_count + 1")
                
                params.append(job_id)
                
                cursor.execute(f"""
                    UPDATE job_queue 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, params)
                
                # Check if job should be moved to dead letter queue
                if status == JobStatus.FAILED:
                    cursor.execute("""
                        UPDATE job_queue 
                        SET status = 'dead_letter'
                        WHERE id = ? AND retry_count >= max_retries
                    """, (job_id,))
                    
                    # If not dead letter, mark for retry
                    cursor.execute("""
                        UPDATE job_queue 
                        SET status = 'retry'
                        WHERE id = ? AND retry_count < max_retries AND status = 'failed'
                    """, (job_id,))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics."""
        try:
            with self._get_cursor() as cursor:
                # Status counts
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM job_queue 
                    GROUP BY status
                """)
                status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Priority distribution
                cursor.execute("""
                    SELECT priority, COUNT(*) as count 
                    FROM job_queue 
                    WHERE status IN ('scraped', 'retry')
                    GROUP BY priority
                """)
                priority_counts = {row['priority']: row['count'] for row in cursor.fetchall()}
                
                # Processing performance
                cursor.execute("""
                    SELECT 
                        AVG(processing_time) as avg_time,
                        MIN(processing_time) as min_time,
                        MAX(processing_time) as max_time,
                        COUNT(*) as processed_count
                    FROM job_queue 
                    WHERE status = 'completed' AND processing_time IS NOT NULL
                """)
                perf_stats = cursor.fetchone()
                
                # Recent activity (last 24 hours)
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM job_queue 
                    WHERE updated_at > datetime('now', '-1 day')
                    GROUP BY status
                """)
                recent_activity = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Source site distribution
                cursor.execute("""
                    SELECT source_site, COUNT(*) as count 
                    FROM job_queue 
                    GROUP BY source_site
                    ORDER BY count DESC
                    LIMIT 10
                """)
                source_stats = {row['source_site']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'status_counts': status_counts,
                    'priority_counts': priority_counts,
                    'performance': {
                        'avg_processing_time': perf_stats['avg_time'] if perf_stats['avg_time'] else 0,
                        'min_processing_time': perf_stats['min_time'] if perf_stats['min_time'] else 0,
                        'max_processing_time': perf_stats['max_time'] if perf_stats['max_time'] else 0,
                        'total_processed': perf_stats['processed_count'] or 0
                    },
                    'recent_activity': recent_activity,
                    'source_distribution': source_stats,
                    'queue_depth': status_counts.get('scraped', 0) + status_counts.get('retry', 0),
                    'total_jobs': sum(status_counts.values())
                }
                
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}
    
    def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """
        Clean up old completed/failed jobs.
        
        Args:
            days_old: Remove jobs older than this many days
            
        Returns:
            int: Number of jobs removed
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM job_queue 
                    WHERE status IN ('completed', 'dead_letter') 
                    AND updated_at < datetime('now', '-{} days')
                """.format(days_old))
                
                removed_count = cursor.rowcount
                logger.info(f"Cleaned up {removed_count} old jobs")
                return removed_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
            return 0
    
    def reset_stuck_jobs(self, hours_stuck: int = 2) -> int:
        """
        Reset jobs that have been stuck in processing status.
        
        Args:
            hours_stuck: Reset jobs stuck for more than this many hours
            
        Returns:
            int: Number of jobs reset
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute("""
                    UPDATE job_queue 
                    SET status = 'retry', 
                        worker_id = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE status = 'processing' 
                    AND updated_at < datetime('now', '-{} hours')
                """.format(hours_stuck))
                
                reset_count = cursor.rowcount
                if reset_count > 0:
                    logger.warning(f"Reset {reset_count} stuck jobs")
                return reset_count
                
        except Exception as e:
            logger.error(f"Error resetting stuck jobs: {e}")
            return 0
    
    def get_jobs_by_status(self, status: JobStatus, limit: int = 100) -> List[JobQueueItem]:
        """Get jobs by status for monitoring/debugging."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM job_queue 
                    WHERE status = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (status.value, limit))
                
                jobs = []
                for row in cursor.fetchall():
                    job = JobQueueItem(
                        id=row['id'],
                        url=row['url'],
                        title=row['title'],
                        company=row['company'],
                        location=row['location'],
                        source_site=row['source_site'],
                        search_keyword=row['search_keyword'],
                        status=JobStatus(row['status']),
                        priority=JobPriority(row['priority']),
                        retry_count=row['retry_count'],
                        max_retries=row['max_retries'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        processed_at=row['processed_at'],
                        error_message=row['error_message'],
                        processing_time=row['processing_time'],
                        worker_id=row['worker_id'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else None
                    )
                    jobs.append(job)
                
                return jobs
                
        except Exception as e:
            logger.error(f"Error getting jobs by status: {e}")
            return []


if __name__ == "__main__":
    # Test the job queue manager
    queue_manager = JobQueueManager("test_queue.db")
    
    # Add test jobs
    test_jobs = [
        JobQueueItem(
            url="https://example.com/job1",
            title="Python Developer",
            company="Tech Corp",
            location="Remote",
            source_site="eluta",
            search_keyword="python",
            priority=JobPriority.HIGH
        ),
        JobQueueItem(
            url="https://example.com/job2",
            title="Data Scientist",
            company="AI Company",
            location="Toronto",
            source_site="indeed",
            search_keyword="data science",
            priority=JobPriority.NORMAL
        )
    ]
    
    # Add jobs
    added = queue_manager.add_jobs_batch(test_jobs)
    print(f"Added {added} jobs")
    
    # Get stats
    stats = queue_manager.get_queue_stats()
    print("Queue Stats:", json.dumps(stats, indent=2))
    
    # Get next jobs for processing
    jobs = queue_manager.get_next_jobs(limit=5, worker_id="test_worker")
    print(f"Retrieved {len(jobs)} jobs for processing")
    
    # Update job status
    if jobs:
        success = queue_manager.update_job_status(
            jobs[0].id, 
            JobStatus.COMPLETED, 
            processing_time=2.5
        )
        print(f"Updated job status: {success}")
    
    # Final stats
    final_stats = queue_manager.get_queue_stats()
    print("Final Stats:", json.dumps(final_stats, indent=2))