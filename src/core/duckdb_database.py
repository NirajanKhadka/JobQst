"""
DuckDB Database Implementation for JobQst
Optimized analytics database with minimal schema (17 essential fields).

Performance Benefits:
- Columnar storage optimized for analytical queries
- File-based deployment (no Docker required)
- Vectorized operations for aggregations, filtering, and analytics
- Optimized for dashboard performance with minimal memory footprint

Schema: Reduced from 30 fields to 17 essential fields based on dashboard needs.
"""

import logging
import pandas as pd
import duckdb
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .job_data import JobData

logger = logging.getLogger(__name__)


class DuckDBJobDatabase:
    """
    DuckDB-based job database optimized for analytics performance.
    
    Features:
    - Minimal 17-field schema (vs 30 in PostgreSQL)
    - Vectorized operations with pandas integration
    - Optimized for dashboard analytics queries
    - File-based storage (no server required)
    """
    
    def __init__(self, db_path: str = "data/jobs_duckdb.db",
                 profile_name: Optional[str] = None):
        """Initialize DuckDB connection with minimal schema."""
        self.profile_name = profile_name
        
        # Handle profile-specific paths
        if profile_name:
            self.db_path = f"profiles/{profile_name}/{profile_name}_duckdb.db"
        else:
            self.db_path = db_path
            
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection as None - will connect when needed
        self.conn = None
        
        # Connect and create table
        self._ensure_connection()
        self._create_table()
        
        logger.info(f"DuckDB database initialized: {self.db_path}")
    
    def _ensure_connection(self):
        """Ensure database connection is active"""
        if self.conn is None:
            try:
                self.conn = duckdb.connect(self.db_path)
            except Exception as e:
                logger.error(f"Failed to connect to DuckDB: {e}")
                # Try read-only connection for dashboard
                try:
                    self.conn = duckdb.connect(self.db_path, read_only=True)
                    logger.info("Connected to DuckDB in read-only mode")
                except Exception as e2:
                    logger.error(f"Failed to connect in read-only mode: {e2}")
                    raise e2
    
    def _create_table(self):
        """Create jobs table with enhanced schema for job tracking."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS jobs (
            id VARCHAR PRIMARY KEY,
            title VARCHAR NOT NULL,
            company VARCHAR NOT NULL,
            location VARCHAR,
            salary_range VARCHAR,
            description TEXT,
            summary TEXT,
            skills TEXT,
            keywords TEXT,
            url VARCHAR,
            source VARCHAR,
            date_posted DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            profile_name VARCHAR,
            status VARCHAR DEFAULT 'new',
            fit_score FLOAT,
            job_type VARCHAR,
            -- Immigration and location fields
            city_tags VARCHAR,
            province_code VARCHAR,
            is_rcip_city INTEGER DEFAULT 0,
            is_immigration_priority INTEGER DEFAULT 0,
            location_type VARCHAR, -- remote, hybrid, onsite
            location_category VARCHAR, -- urban, rural, etc
            -- Enhanced job tracking fields
            application_status VARCHAR DEFAULT 'discovered',
            -- Status options: discovered, interested, applied, phone_screen,
            -- technical_interview, onsite, offer, rejected, accepted
            application_date DATE,
            application_notes TEXT,
            follow_up_date DATE,
            recruiter_name VARCHAR,
            recruiter_email VARCHAR,
            recruiter_phone VARCHAR,
            salary_offered VARCHAR,
            response_date DATE,
            interview_scheduled_date DATE,
            interview_type VARCHAR, -- phone, video, onsite, technical
            interview_notes TEXT,
            offer_details TEXT,
            rejection_reason TEXT,
            priority_level INTEGER DEFAULT 3, -- 1-5 scale (1=highest priority)
            application_deadline DATE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        self.conn.execute(create_sql)
        
        # Create additional tables for comprehensive job tracking
        self._create_tracking_tables()
        
        # Create indexes for common queries
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_date_posted "
            "ON jobs(date_posted);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_profile_name "
            "ON jobs(profile_name);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_application_status "
            "ON jobs(application_status);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_fit_score "
            "ON jobs(fit_score);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_created_at "
            "ON jobs(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_priority_level "
            "ON jobs(priority_level);",
            "CREATE INDEX IF NOT EXISTS idx_jobs_follow_up_date "
            "ON jobs(follow_up_date);"
        ]
        
        for query in index_queries:
            try:
                self.conn.execute(query)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
    
    def _create_tracking_tables(self):
        """Create additional tables for comprehensive job tracking."""
        
        # Job notes table for detailed tracking
        notes_sql = """
        CREATE TABLE IF NOT EXISTS job_notes (
            id INTEGER PRIMARY KEY,
            job_id VARCHAR NOT NULL,
            note_type VARCHAR, -- application, interview, follow_up, general
            note_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reminder_date DATE,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
        """
        
        # Job interviews table
        interviews_sql = """
        CREATE TABLE IF NOT EXISTS job_interviews (
            id INTEGER PRIMARY KEY,
            job_id VARCHAR NOT NULL,
            interview_date TIMESTAMP,
            interview_type VARCHAR, -- phone, video, onsite, technical
            interviewer_name VARCHAR,
            interviewer_email VARCHAR,
            location VARCHAR,
            notes TEXT,
            preparation_notes TEXT,
            outcome VARCHAR, -- scheduled, completed, cancelled, rescheduled
            rating INTEGER, -- 1-5 how well it went
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
        """
        
        # Job communications table
        communications_sql = """
        CREATE TABLE IF NOT EXISTS job_communications (
            id INTEGER PRIMARY KEY,
            job_id VARCHAR NOT NULL,
            communication_type VARCHAR, -- email, phone, message, meeting
            direction VARCHAR, -- inbound, outbound
            contact_person VARCHAR,
            subject VARCHAR,
            content TEXT,
            communication_date TIMESTAMP,
            follow_up_required BOOLEAN DEFAULT FALSE,
            follow_up_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
        """
        
        # Job documents table
        documents_sql = """
        CREATE TABLE IF NOT EXISTS job_documents (
            id INTEGER PRIMARY KEY,
            job_id VARCHAR NOT NULL,
            document_type VARCHAR, -- resume, cover_letter, portfolio
            document_name VARCHAR NOT NULL,
            file_path VARCHAR,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
        """
        
        # Manual review queue table
        manual_review_sql = """
        CREATE TABLE IF NOT EXISTS manual_review_queue (
            id INTEGER PRIMARY KEY,
            job_id VARCHAR NOT NULL,
            review_type VARCHAR NOT NULL, -- duplicate, low_quality, etc
            priority INTEGER DEFAULT 3, -- 1-5 scale (1=highest priority)
            status VARCHAR DEFAULT 'pending', -- pending, in_progress, resolved
            description TEXT,
            context_data TEXT, -- JSON string with additional context
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_to VARCHAR,
            reviewer VARCHAR,
            reviewed_at TIMESTAMP,
            resolution TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );
        """
        
        # Execute table creation
        tables = [
            notes_sql, interviews_sql, communications_sql,
            documents_sql, manual_review_sql
        ]
        for sql in tables:
            try:
                self.conn.execute(sql)
            except Exception as e:
                logger.error(f"Error creating tracking table: {e}")
        
        # Create indexes for tracking tables
        tracking_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_job_notes_job_id "
            "ON job_notes(job_id);",
            "CREATE INDEX IF NOT EXISTS idx_job_interviews_job_id "
            "ON job_interviews(job_id);",
            "CREATE INDEX IF NOT EXISTS idx_job_communications_job_id "
            "ON job_communications(job_id);",
            "CREATE INDEX IF NOT EXISTS idx_job_documents_job_id "
            "ON job_documents(job_id);",
            "CREATE INDEX IF NOT EXISTS idx_manual_review_job_id "
            "ON manual_review_queue(job_id);",
            "CREATE INDEX IF NOT EXISTS idx_manual_review_status "
            "ON manual_review_queue(status);",
        ]
        
        for index_sql in tracking_indexes:
            try:
                self.conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Tracking index creation warning: {e}")
    
    def add_job(self, job_data) -> bool:
        """Add a single job to the database."""
        try:
            # Handle both JobData objects and dictionaries
            if isinstance(job_data, dict):
                job_dict = self._dict_to_minimal_dict(job_data)
            else:
                # Assume it's a JobData object
                job_dict = self._job_data_to_minimal_dict(job_data)
            
            # Check if job already exists
            if self._job_exists(job_dict['id']):
                logger.debug(f"Job {job_dict['id']} already exists, skipping")
                return False
            
            # Insert job
            placeholders = ', '.join(['?' for _ in job_dict.keys()])
            columns = ', '.join(job_dict.keys())
            
            insert_sql = (f"INSERT INTO jobs ({columns}) "
                          f"VALUES ({placeholders})")
            self.conn.execute(insert_sql, list(job_dict.values()))
            
            logger.debug(f"Added job: {job_dict['title']} "
                         f"at {job_dict['company']}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding job: {e}")
            return False
    
    def save_job(self, job_data: JobData) -> bool:
        """Save a job to the database (alias for add_job for compatibility)"""
        return self.add_job(job_data)
    
    def add_jobs_batch(self, jobs_data) -> int:
        """Add multiple jobs efficiently using pandas."""
        if not jobs_data:
            return 0
            
        try:
            # Convert to minimal dicts - handle both JobData objects and dictionaries
            job_dicts = []
            for job in jobs_data:
                if isinstance(job, dict):
                    job_dicts.append(self._dict_to_minimal_dict(job))
                else:
                    job_dicts.append(self._job_data_to_minimal_dict(job))
            
            # Create DataFrame
            df = pd.DataFrame(job_dicts)
            
            # Remove duplicates within batch
            df = df.drop_duplicates(subset=['id'])
            
            # Filter out existing jobs
            existing_ids = self._get_existing_ids(df['id'].tolist())
            df = df[~df['id'].isin(existing_ids)]
            
            if df.empty:
                logger.info("No new jobs to add (all duplicates)")
                return 0
            
            # Batch insert using DuckDB's pandas integration
            self.conn.execute("INSERT INTO jobs SELECT * FROM df")
            
            added_count = len(df)
            logger.info(f"Added {added_count} new jobs to DuckDB")
            return added_count
            
        except Exception as e:
            logger.error(f"Error in batch job insertion: {e}")
            return 0
    
    def get_jobs(self,
                 profile_name: Optional[str] = None,
                 limit: Optional[int] = None,
                 status_filter: Optional[str] = None,
                 company_filter: Optional[str] = None,
                 location_filter: Optional[str] = None,
                 min_fit_score: Optional[float] = None
                 ) -> List[Dict[str, Any]]:
        """Get jobs with optional filtering."""
        try:
            self._ensure_connection()
            
            query = "SELECT * FROM jobs WHERE 1=1"
            params = []
            
            # Add filters
            if profile_name:
                query += " AND profile_name = ?"
                params.append(profile_name)
            elif self.profile_name:
                query += " AND profile_name = ?"
                params.append(self.profile_name)
                
            if status_filter:
                query += " AND status = ?"
                params.append(status_filter)
                
            if company_filter:
                query += " AND company ILIKE ?"
                params.append(f"%{company_filter}%")
                
            if location_filter:
                query += " AND location ILIKE ?"
                params.append(f"%{location_filter}%")
                
            if min_fit_score is not None:
                query += " AND fit_score >= ?"
                params.append(min_fit_score)
            
            # Order by most recent
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.conn.execute(query, params).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            
            return [dict(zip(columns, row)) for row in result]
            
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []
    
    def get_all_jobs(self, profile_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all jobs for the profile."""
        return self.get_jobs(profile_name=profile_name)
    
    def get_top_jobs(self, limit: int = 50, profile_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get top jobs with limit."""
        return self.get_jobs(profile_name=profile_name, limit=limit)
    
    def get_analytics_data(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get analytics data optimized for dashboard display."""
        try:
            profile_filter = ""
            params = []
            
            if profile_name:
                profile_filter = "WHERE profile_name = ?"
                params = [profile_name]
            elif self.profile_name:
                profile_filter = "WHERE profile_name = ?"
                params = [self.profile_name]
            
            # Basic stats
            stats_query = f"""
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT location) as unique_locations,
                AVG(fit_score) as avg_fit_score,
                MAX(fit_score) as max_fit_score,
                COUNT(CASE WHEN status = 'applied' THEN 1 END) as applied_count,
                COUNT(CASE WHEN status = 'interview' THEN 1 END) as interview_count,
                COUNT(CASE WHEN status = 'new' THEN 1 END) as new_count
            FROM jobs {profile_filter}
            """
            
            stats = self.conn.execute(stats_query, params).fetchone()
            
            # Top companies
            companies_query = f"""
            SELECT company, COUNT(*) as job_count
            FROM jobs {profile_filter}
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT 10
            """
            
            companies = self.conn.execute(companies_query, params).fetchall()
            
            # Jobs by date  
            if profile_filter:
                # Already has WHERE clause, use AND
                dates_query = f"""
                SELECT date_posted, COUNT(*) as job_count
                FROM jobs {profile_filter}
                AND date_posted IS NOT NULL
                GROUP BY date_posted
                ORDER BY date_posted DESC
                LIMIT 30
                """
            else:
                # No WHERE clause yet
                dates_query = """
                SELECT date_posted, COUNT(*) as job_count
                FROM jobs
                WHERE date_posted IS NOT NULL
                GROUP BY date_posted
                ORDER BY date_posted DESC
                LIMIT 30
                """
            
            dates = self.conn.execute(dates_query, params).fetchall()
            
            return {
                'total_jobs': stats[0] or 0,
                'unique_companies': stats[1] or 0,
                'unique_locations': stats[2] or 0,
                'avg_fit_score': round(stats[3] or 0, 2),
                'max_fit_score': stats[4] or 0,
                'applied_count': stats[5] or 0,
                'interview_count': stats[6] or 0,
                'new_count': stats[7] or 0,
                'top_companies': [{'company': row[0], 'count': row[1]} for row in companies],
                'jobs_by_date': [{'date': row[0], 'count': row[1]} for row in dates]
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics data: {e}")
            return {'total_jobs': 0}
    
    def update_job_status(self, job_id: str, new_status: str) -> bool:
        """Update job status."""
        try:
            self.conn.execute("UPDATE jobs SET status = ? WHERE id = ?", [new_status, job_id])
            return True
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return False
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        try:
            self.conn.execute("DELETE FROM jobs WHERE id = ?", [job_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting job: {e}")
            return False
    
    def get_job_count(self, profile_name: Optional[str] = None) -> int:
        """Get total job count."""
        try:
            self._ensure_connection()
            
            if profile_name or self.profile_name:
                result = self.conn.execute(
                    "SELECT COUNT(*) FROM jobs WHERE profile_name = ?", 
                    [profile_name or self.profile_name]
                ).fetchone()
            else:
                result = self.conn.execute("SELECT COUNT(*) FROM jobs").fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting job count: {e}")
            return 0
    
    def get_job_stats(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get job statistics for health checks and monitoring."""
        try:
            profile_filter = ""
            params = []
            
            if profile_name or self.profile_name:
                profile_filter = "WHERE profile_name = ?"
                params = [profile_name or self.profile_name]
            
            # Get basic statistics
            stats_query = f"""
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT source) as unique_sites,
                COUNT(CASE WHEN created_at > (CURRENT_TIMESTAMP - INTERVAL 1 DAY)
                      THEN 1 END) as recent_jobs,
                MAX(created_at) as last_created
            FROM jobs {profile_filter}
            """
            
            result = self.conn.execute(stats_query, params).fetchone()
            
            if not result:
                return {
                    "total_jobs": 0,
                    "unique_companies": 0,
                    "unique_sites": 0,
                    "recent_jobs": 0,
                    "last_scraped_ago": "Never"
                }
            
            # Calculate time since last job
            last_scraped_ago = "Never"
            if result[4]:  # last_created
                try:
                    from datetime import datetime
                    last_time = datetime.fromisoformat(result[4])
                    delta = datetime.now() - last_time
                    
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
                "total_jobs": result[0] or 0,
                "unique_companies": result[1] or 0,
                "unique_sites": result[2] or 0,
                "recent_jobs": result[3] or 0,
                "last_scraped_ago": last_scraped_ago
            }
            
        except Exception as e:
            logger.error(f"Error getting job stats: {e}")
            return {
                "total_jobs": 0,
                "unique_companies": 0,
                "unique_sites": 0,
                "recent_jobs": 0,
                "last_scraped_ago": "Never"
            }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed")
    
    def _dict_to_minimal_dict(self, job_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert job dictionary to minimal field dictionary for database."""
        # Generate ID if not present
        job_id = job_dict.get('id')
        if not job_id:
            title = job_dict.get('title', 'Unknown')
            company = job_dict.get('company', 'Unknown')
            location = job_dict.get('location', 'Unknown')
            job_id = f"{company}_{title}_{location}".replace(" ", "_").lower()
        
        # Convert posted_date to proper format
        date_posted = job_dict.get('date_posted') or job_dict.get('posted_date')
        if isinstance(date_posted, str):
            try:
                date_posted = datetime.strptime(date_posted, '%Y-%m-%d').date()
            except:
                date_posted = None
        elif isinstance(date_posted, datetime):
            date_posted = date_posted.date()
        
        return {
            'id': job_id,
            'title': job_dict.get('title', 'Unknown Title'),
            'company': job_dict.get('company', 'Unknown Company'),
            'location': job_dict.get('location', ''),
            'salary_range': job_dict.get('salary') or job_dict.get('salary_range', ''),
            'description': job_dict.get('description', ''),
            'summary': job_dict.get('summary', ''),
            'skills': job_dict.get('skills', ''),
            'keywords': job_dict.get('keywords', ''),
            'url': job_dict.get('url') or job_dict.get('job_url', ''),
            'source': job_dict.get('site') or job_dict.get('source', 'jobspy'),
            'date_posted': date_posted,
            'created_at': datetime.now(),
            'profile_name': self.profile_name or job_dict.get('profile_name', 'default'),
            'status': job_dict.get('status', 'new'),
            'fit_score': job_dict.get('fit_score'),
            'job_type': job_dict.get('job_type', ''),
            # Immigration and location fields
            'city_tags': job_dict.get('city_tags', ''),
            'province_code': job_dict.get('province_code', ''),
            'is_rcip_city': job_dict.get('is_rcip_city', 0),
            'is_immigration_priority': job_dict.get('is_immigration_priority', 0),
            'location_type': job_dict.get('location_type', 'onsite'),
            'location_category': job_dict.get('location_category', 'unknown')
        }
    
    def _job_data_to_minimal_dict(self, job_data: JobData) -> Dict[str, Any]:
        """Convert JobData to minimal field dictionary."""
        # Generate ID if not present
        job_id = getattr(job_data, 'id', None)
        if not job_id:
            job_id = f"{job_data.company}_{job_data.title}_{job_data.location}".replace(" ", "_").lower()
        
        # Convert posted_date to proper format
        date_posted = getattr(job_data, 'posted_date', None)
        if isinstance(date_posted, str):
            try:
                date_posted = datetime.strptime(date_posted, '%Y-%m-%d').date()
            except:
                date_posted = None
        elif isinstance(date_posted, datetime):
            date_posted = date_posted.date()
        
        return {
            'id': job_id,
            'title': job_data.title,
            'company': job_data.company,
            'location': job_data.location or '',
            'salary_range': job_data.salary or '',  # Map salary to salary_range
            'description': getattr(job_data, 'description', ''),  # Not in JobData
            'summary': job_data.summary or '',
            'skills': getattr(job_data, 'skills', ''),  # Not in JobData
            'keywords': job_data.search_keyword or '',  # Map search_keyword to keywords
            'url': job_data.url or '',
            'source': job_data.site or 'unknown',  # Map site to source
            'date_posted': date_posted,
            'created_at': datetime.now(),
            'profile_name': self.profile_name or getattr(job_data, 'profile_name', 'default'),
            'status': getattr(job_data, 'status', 'new'),  # Not in JobData
            'fit_score': getattr(job_data, 'fit_score', None),  # Not in JobData
            'job_type': job_data.job_type or ''
        }
    
    def _job_exists(self, job_id: str) -> bool:
        """Check if job exists."""
        result = self.conn.execute("SELECT 1 FROM jobs WHERE id = ? LIMIT 1", [job_id]).fetchone()
        return result is not None
    
    def _get_existing_ids(self, job_ids: List[str]) -> List[str]:
        """Get list of existing job IDs from provided list."""
        if not job_ids:
            return []
            
        placeholders = ', '.join(['?' for _ in job_ids])
        query = f"SELECT id FROM jobs WHERE id IN ({placeholders})"
        result = self.conn.execute(query, job_ids).fetchall()
        return [row[0] for row in result]

    def get_jobs_for_processing(self, limit: int = 10, 
                               profile_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get jobs that need processing (for pipeline testing and processing)."""
        try:
            self._ensure_connection()
            
            query = """
            SELECT * FROM jobs 
            WHERE 1=1
            """
            params = []
            
            # Add profile filter
            if profile_name:
                query += " AND profile_name = ?"
                params.append(profile_name)
            elif self.profile_name:
                query += " AND profile_name = ?"
                params.append(self.profile_name)
            
            # Prioritize jobs that haven't been processed yet
            query += """
            AND (fit_score IS NULL OR fit_score = 0)
            ORDER BY created_at DESC
            LIMIT ?
            """
            params.append(limit)
            
            result = self.conn.execute(query, params).fetchall()
            columns = [desc[0] for desc in self.conn.description]
            
            jobs = [dict(zip(columns, row)) for row in result]
            logger.info(f"Retrieved {len(jobs)} jobs for processing")
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting jobs for processing: {e}")
            return []
    
    def update_job_processing_status(self, job_id: str, 
                                   processing_data: Dict[str, Any]) -> bool:
        """Update job with processing results."""
        try:
            # Check if job exists
            if not self._job_exists(job_id):
                logger.warning(f"Job {job_id} not found for processing update")
                return False
            
            # Build update query based on provided processing data
            update_fields = []
            update_values = []
            
            # Handle fit_score
            if 'fit_score' in processing_data:
                update_fields.append("fit_score = ?")
                update_values.append(processing_data['fit_score'])
            
            # Handle status
            if 'status' in processing_data:
                update_fields.append("status = ?")
                update_values.append(processing_data['status'])
            
            # Handle summary
            if 'summary' in processing_data:
                update_fields.append("summary = ?")
                update_values.append(processing_data['summary'])
            
            # Handle skills
            if 'skills' in processing_data:
                update_fields.append("skills = ?")
                update_values.append(processing_data['skills'])
            
            # Always update last_updated
            update_fields.append("last_updated = ?")
            update_values.append(datetime.now())
            
            if not update_fields:
                logger.warning("No fields to update in processing data")
                return False
            
            # Add job_id for WHERE clause
            update_values.append(job_id)
            
            # Execute update
            update_sql = f"""
            UPDATE jobs 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            self.conn.execute(update_sql, update_values)
            logger.debug(f"Updated processing data for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job processing status: {e}")
            return False

    def update_job_analysis(self, job_id: str,
                            analysis_data: Dict[str, Any]) -> bool:
        """Update job with analysis results."""
        try:
            # Check if job exists
            if not self._job_exists(job_id):
                logger.warning(f"Job {job_id} not found for analysis update")
                return False
            
            # Build update query based on provided analysis data
            update_fields = []
            update_values = []
            
            # Handle fit_score (main compatibility score)
            if 'fit_score' in analysis_data:
                update_fields.append("fit_score = ?")
                update_values.append(analysis_data['fit_score'])
            
            # Handle status
            if 'status' in analysis_data:
                update_fields.append("status = ?")
                update_values.append(analysis_data['status'])
            
            # Handle summary
            if 'summary' in analysis_data:
                update_fields.append("summary = ?")
                update_values.append(analysis_data['summary'])
            
            # Handle skills
            if 'skills' in analysis_data:
                update_fields.append("skills = ?")
                update_values.append(analysis_data['skills'])
            
            # Always update last_updated
            update_fields.append("last_updated = ?")
            update_values.append(datetime.now())
            
            if not update_fields:
                logger.warning("No fields to update in analysis data")
                return False
            
            # Add job_id for WHERE clause
            update_values.append(job_id)
            
            # Execute update
            update_sql = f"""
            UPDATE jobs 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            self.conn.execute(update_sql, update_values)
            logger.debug(f"Updated analysis data for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job analysis: {e}")
            return False
            
            # Handle match_score (for compatibility)
            if 'match_score' in analysis_data:
                update_fields.append("match_score = ?")
                update_values.append(analysis_data['match_score'])
            
            # Add job_id for WHERE clause
            update_values.append(job_id)
            
            if not update_fields:
                logger.warning("No valid analysis fields provided for update")
                return False
            
            # Add timestamp
            update_fields.append("last_updated = current_timestamp")
            
            # Execute update
            query = f"""
                UPDATE jobs
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            
            self.conn.execute(query, update_values)
            self.conn.commit()
            
            logger.debug(f"Updated job {job_id} with analysis data")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job analysis for {job_id}: {e}")
            self.conn.rollback()
            return False

    def get_job_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get a job by its URL to check for duplicates."""
        try:
            if not url:
                return None
                
            result = self.conn.execute(
                "SELECT * FROM jobs WHERE url = ? LIMIT 1",
                [url]
            ).fetchone()
            
            if result:
                # Convert to dictionary using column names
                columns = [desc[0] for desc in self.conn.description]
                return dict(zip(columns, result))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting job by URL '{url}': {e}")
            return None
    
    def update_job_metadata(self, job_id: str,
                            metadata: Dict[str, Any]) -> bool:
        """Update job metadata fields."""
        try:
            if not metadata:
                return True
                
            # Build dynamic update query based on provided metadata
            set_clauses = []
            values = []
            
            # Map of allowed metadata fields to actual DB columns
            allowed_mappings = {
                'updated_at': 'last_updated',
                'last_updated': 'last_updated',
                'status': 'status',
                'application_status': 'application_status',
                'source': 'source'
                # Note: search_term and search_location are not in the
                # minimal DuckDB schema, so they are ignored
            }
            
            for key, value in metadata.items():
                if key in allowed_mappings:
                    column_name = allowed_mappings[key]
                    set_clauses.append(f"{column_name} = ?")
                    values.append(value)
            
            if not set_clauses:
                logger.debug(f"No valid metadata fields to update "
                             f"for job {job_id} (fields provided: "
                             f"{list(metadata.keys())})")
                return True
            
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?"
            values.append(job_id)
            
            self.conn.execute(query, values)
            logger.debug(f"Updated metadata for job {job_id}: {metadata}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job metadata for {job_id}: {e}")
            return False
