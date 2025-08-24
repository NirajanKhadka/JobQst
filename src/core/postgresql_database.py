import os
import json
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from contextlib import contextmanager
import threading
from queue import Queue

from .job_record import JobRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLJobDatabase:
    """PostgreSQL-based job database with connection pooling"""
    
    def __init__(self, profile_name: str = None):
        self.profile_name = profile_name
        self._lock = threading.Lock()
        self._connection_pool = Queue(maxsize=10)
        
        # Get database config from environment
        self.db_config = {
            'host': os.getenv('DATABASE_HOST', 'localhost'),
            'port': int(os.getenv('DATABASE_PORT', 5432)),
            'database': os.getenv('DATABASE_NAME', 'autojob'),
            'user': os.getenv('DATABASE_USER', 'postgres'),
            'password': os.getenv('DATABASE_PASSWORD', 'password')
        }
        
        self._init_pool()
        self._init_indexes()
        logger.info(f"✅ PostgreSQL database initialized for profile: {profile_name}")

    def _init_pool(self):
        """Initialize connection pool"""
        for _ in range(10):
            try:
                conn = psycopg2.connect(**self.db_config)
                conn.autocommit = True
                self._connection_pool.put(conn)
            except Exception as e:
                logger.error(f"Failed to create connection: {e}")
                break

    @contextmanager
    def _get_connection(self):
        """Get connection from pool"""
        conn = None
        try:
            conn = self._connection_pool.get(timeout=5)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                self._connection_pool.put(conn)

    def _init_indexes(self):
        """Create additional indexes for performance"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create additional indexes if they don't exist
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_jobs_profile_created "
                "ON jobs(profile_name, created_at);",
                "CREATE INDEX IF NOT EXISTS idx_jobs_status_score "
                "ON jobs(status, fit_score);",
                "CREATE INDEX IF NOT EXISTS idx_jobs_date_range "
                "ON jobs(date_posted) WHERE date_posted IS NOT NULL;",
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")

    def add_job(self, job_data: Dict) -> bool:
        """Add a new job to the database"""
        try:
            logger.info(f"🔄 add_job called with job: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Set profile name
                if self.profile_name:
                    job_data['profile_name'] = self.profile_name
                
                # Map JobSpy fields to our database schema
                job_id = job_data.get('id', job_data.get('job_id'))
                
                # Generate ID if not provided
                if not job_id:
                    import hashlib
                    url = job_data.get('url', job_data.get('job_url', ''))
                    title = job_data.get('title', '')
                    company = job_data.get('company', '')
                    # Create a unique ID based on URL, title, and company
                    id_string = f"{url}_{title}_{company}"
                    job_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                
                mapped_data = {
                    'id': job_id,
                    'title': job_data.get('title'),
                    'company': job_data.get('company'),
                    'location': job_data.get('location'),
                    'url': job_data.get('url', job_data.get('job_url')),
                    'summary': job_data.get('summary', job_data.get('description', ''))[:1000] if job_data.get('summary') or job_data.get('description') else None,
                    'description': job_data.get('description', job_data.get('job_description')),
                    'date_posted': job_data.get('date_posted'),
                    'source': job_data.get('source', job_data.get('site')),
                    'keywords': job_data.get('keywords'),
                    'job_type': job_data.get('job_type'),
                    'experience_level': job_data.get('experience_level'),
                    'salary_range': job_data.get('salary_range'),
                    'requirements': job_data.get('requirements'),
                    'benefits': job_data.get('benefits'),
                    'skills': job_data.get('skills'),
                    'status': job_data.get('status', 'new'),
                    'profile_name': self.profile_name
                }
                
                logger.info(f"💾 Attempting to save job with ID: {mapped_data['id']}")
                
                # Insert job
                cursor.execute("""
                    INSERT INTO jobs (
                        id, title, company, location, url, summary, description,
                        date_posted, source, keywords, job_type, experience_level,
                        salary_range, requirements, benefits, skills, status, profile_name
                    ) VALUES (
                        %(id)s, %(title)s, %(company)s, %(location)s, %(url)s,
                        %(summary)s, %(description)s, %(date_posted)s, %(source)s,
                        %(keywords)s, %(job_type)s, %(experience_level)s,
                        %(salary_range)s, %(requirements)s, %(benefits)s,
                        %(skills)s, %(status)s, %(profile_name)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        company = EXCLUDED.company,
                        location = EXCLUDED.location,
                        updated_at = CURRENT_TIMESTAMP
                """, mapped_data)
                
                conn.commit()
                success = cursor.rowcount > 0
                
                if success:
                    logger.info(f"✅ Successfully saved job: {mapped_data['title']} at {mapped_data['company']}")
                else:
                    logger.warning(f"⚠️ Job save returned 0 rows affected: {mapped_data['title']}")
                
                return success
                
        except Exception as e:
            logger.error(f"❌ Error adding job: {e}")
            logger.error(f"Job data keys: {list(job_data.keys())}")
            return False

    def get_jobs(self, profile_name: str = None, limit: int = None,
                 processed: bool = None, applied: bool = None) -> List[Dict]:
        """Get jobs from database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Build query
                where_conditions = []
                params = {}
                
                if profile_name:
                    where_conditions.append("profile_name = %(profile_name)s")
                    params['profile_name'] = profile_name
                elif self.profile_name:
                    where_conditions.append("profile_name = %(profile_name)s")
                    params['profile_name'] = self.profile_name
                
                if processed is not None:
                    if processed:
                        where_conditions.append("status IN ('processed', 'analyzed')")
                    else:
                        where_conditions.append("status IN ('new', 'scraped')")
                
                if applied is not None:
                    where_conditions.append("applied = %(applied)s")
                    params['applied'] = applied
                
                # Add 14-day retention filter
                retention_days = int(os.getenv('JOB_RETENTION_DAYS', 14))
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                where_conditions.append("created_at >= %(cutoff_date)s")
                params['cutoff_date'] = cutoff_date
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                query = f"""
                    SELECT * FROM jobs 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []

    def update_job_processing(self, job_id: int, processed: bool = True,
                            fit_score: float = None, 
                            fit_explanation: str = None) -> bool:
        """Update job processing status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                update_data = {
                    'job_id': job_id,
                    'status': 'processed' if processed else 'new',
                    'updated_at': datetime.now()
                }
                
                if fit_score is not None:
                    update_data['fit_score'] = fit_score
                
                if fit_explanation:
                    update_data['fit_explanation'] = fit_explanation
                
                cursor.execute("""
                    UPDATE jobs 
                    SET status = %(status)s,
                        fit_score = COALESCE(%(fit_score)s, fit_score),
                        updated_at = %(updated_at)s
                    WHERE id = %(job_id)s
                """, update_data)
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating job processing: {e}")
            return False

    def mark_job_applied(self, job_id: int, applied: bool = True) -> bool:
        """Mark job as applied"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE jobs 
                    SET applied = %(applied)s,
                        applied_date = %(applied_date)s,
                        updated_at = %(updated_at)s
                    WHERE id = %(job_id)s
                """, {
                    'job_id': job_id,
                    'applied': applied,
                    'applied_date': datetime.now() if applied else None,
                    'updated_at': datetime.now()
                })
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error marking job applied: {e}")
            return False

    def get_job_counts(self, profile_name: str = None) -> Dict[str, int]:
        """Get job counts for dashboard"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                profile = profile_name or self.profile_name
                
                # 14-day retention filter
                retention_days = int(os.getenv('JOB_RETENTION_DAYS', 14))
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status IN ('processed', 'analyzed')) as processed,
                        COUNT(*) FILTER (WHERE status IN ('new', 'scraped')) as pending,
                        COUNT(*) FILTER (WHERE applied = true) as applied
                    FROM jobs 
                    WHERE profile_name = %s AND created_at >= %s
                """, (profile, cutoff_date))
                
                row = cursor.fetchone()
                
                return {
                    'total': row[0] if row else 0,
                    'processed': row[1] if row else 0,
                    'pending': row[2] if row else 0,
                    'applied': row[3] if row else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting job counts: {e}")
            return {'total': 0, 'processed': 0, 'pending': 0, 'applied': 0}

    def delete_old_jobs(self) -> int:
        """Delete jobs older than retention period"""
        try:
            retention_days = int(os.getenv('JOB_RETENTION_DAYS', 14))
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM jobs 
                    WHERE created_at < %s
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    logger.info(f"🗑️ Deleted {deleted_count} old jobs")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error deleting old jobs: {e}")
            return 0

    def get_all_profiles(self) -> List[str]:
        """Get all profile names"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 14-day retention filter
                retention_days = int(os.getenv('JOB_RETENTION_DAYS', 14))
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                cursor.execute("""
                    SELECT DISTINCT profile_name 
                    FROM jobs 
                    WHERE created_at >= %s
                    ORDER BY profile_name
                """, (cutoff_date,))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting profiles: {e}")
            return []

    def get_jobs_for_processing(self, limit: int = 50) -> List[Dict]:
        """Get jobs that need processing (scraped but not processed)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                
                cursor.execute("""
                    SELECT * FROM jobs 
                    WHERE status IN ('scraped', 'new') 
                    AND profile_name = %s
                    ORDER BY created_at DESC 
                    LIMIT %s
                """, (self.profile_name, limit))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting jobs for processing: {e}")
            return []

    def update_job_analysis(self, job_id: str, analysis_data: Dict):
        """Update job analysis data."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert analysis_data to JSON string for storage
                analysis_json = json.dumps(analysis_data)
                
                # Update the job with analysis data
                cursor.execute("""
                    UPDATE jobs 
                    SET analysis_result = %s,
                        compatibility_score = %s,
                        match_score = %s,
                        fit_score = %s,
                        status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    analysis_json,
                    analysis_data.get('compatibility_score', 0.0),
                    analysis_data.get('match_score', 0.0),
                    analysis_data.get('fit_score', 0.0),
                    analysis_data.get('status', 'processed'),
                    job_id
                ))
                
                conn.commit()
                logger.info(f"Updated analysis data for job {job_id}")
                
        except Exception as e:
            logger.error(f"Error updating job analysis for {job_id}: {e}")

    def update_job_status(self, job_id: str, new_status: str) -> bool:
        """Update job status by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE jobs 
                    SET status = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                """, (new_status, job_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating job status for {job_id}: {e}")
            return False

    def get_job_by_url(self, url: str) -> Dict:
        """Get job by URL to check for duplicates."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute("SELECT * FROM jobs WHERE url = %s", (url,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting job by URL: {e}")
            return None

    def update_job_metadata(self, job_id: str, metadata: Dict) -> bool:
        """Update job metadata fields."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query based on provided metadata
                update_fields = []
                values = []
                
                for key, value in metadata.items():
                    if key in ['search_term', 'search_location', 'updated_at']:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
                
                if not update_fields:
                    return False
                
                # Add updated_at if not provided
                if 'updated_at' not in metadata:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                
                values.append(job_id)
                
                query = f"""
                    UPDATE jobs 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """
                
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating job metadata for {job_id}: {e}")
            return False
    
    def update_job(self, job_id: int, update_data: Dict) -> bool:
        """
        Update job with arbitrary data dictionary using row ID.
        
        Args:
            job_id: Database row ID (integer primary key)
            update_data: Dictionary of fields to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic UPDATE query from update_data
                set_clauses = []
                values = []
                
                for key, value in update_data.items():
                    if key == 'analysis_data' and isinstance(value, dict):
                        # Convert dict to JSON string for analysis_data
                        set_clauses.append("analysis_data = %s")
                        values.append(json.dumps(value))
                    else:
                        set_clauses.append(f"{key} = %s")
                        values.append(value)
                
                # Always update timestamp
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.append(job_id)
                
                query = f"""
                    UPDATE jobs 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                """
                
                cursor.execute(query, values)
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated job with ID {job_id}")
                    return True
                else:
                    logger.warning(f"No job found with ID {job_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Error updating job {job_id}: {e}")
            return False

    def close(self):
        """Close all connections"""
        while not self._connection_pool.empty():
            try:
                conn = self._connection_pool.get_nowait()
                conn.close()
            except:
                pass


# Compatibility class - alias for the old JobDB
class JobDB(PostgreSQLJobDatabase):
    """Compatibility wrapper for existing code"""
    pass
