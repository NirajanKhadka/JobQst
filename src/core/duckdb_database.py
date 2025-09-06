"""
DuckDB Database Implementation for JobQst
Optimized analytics database with minimal schema (17 essential fields).

Performance Benefits:
- 10-100x faster than SQLite for analytical queries
- File-based deployment (no Docker required)
- Optimized for aggregations, filtering, and analytics
- Columnar storage for dashboard performance

Schema: Reduced from 30 fields to 17 essential fields based on dashboard.
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
        
        # Connect to DuckDB
        self.conn = duckdb.connect(self.db_path)
        
        # Create table with minimal schema (17 essential fields)
        self._create_table()
        
        logger.info(f"DuckDB database initialized: {self.db_path}")
    
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
        
        # Execute table creation
        tables = [notes_sql, interviews_sql, communications_sql, documents_sql]
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
        ]
        
        for index_sql in tracking_indexes:
            try:
                self.conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Tracking index creation warning: {e}")
    
    def add_job(self, job_data: JobData) -> bool:
        """Add a single job to the database."""
        try:
            # Convert JobData to minimal field dict
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
    
    def add_jobs_batch(self, jobs_data: List[JobData]) -> int:
        """Add multiple jobs efficiently using pandas."""
        if not jobs_data:
            return 0
            
        try:
            # Convert to minimal dicts
            job_dicts = [self._job_data_to_minimal_dict(job)
                         for job in jobs_data]
            
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
                COUNT(CASE WHEN created_at > datetime('now', '-1 day') THEN 1 END) as recent_jobs,
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
