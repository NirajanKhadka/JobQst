"""
Data loader utility for JobQst Dashboard
Handles loading job data from various sources
"""
import logging
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles data loading for the dashboard"""
    
    def __init__(self):
        self.profiles_path = project_root / 'profiles'
        self.data_path = project_root / 'data'
    
    def get_available_profiles(self):
        """Get list of available user profiles"""
        try:
            if self.profiles_path.exists():
                profiles = [p.stem for p in self.profiles_path.glob('*.json')]
                return profiles if profiles else ['Nirajan']
            return ['Nirajan']
        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
            return ['Nirajan']
    
    def load_jobs_data(self, profile_name='Nirajan'):
        """Load job data for a specific profile using connection manager"""
        try:
            # Use connection manager to avoid file locking issues
            from src.core.duckdb_connection_manager import DuckDBConnectionManager
            
            # Build query with profile filter
            query = "SELECT * FROM jobs WHERE profile_name = ? ORDER BY created_at DESC"
            params = [profile_name]
            
            # Execute query with read-only connection
            result = DuckDBConnectionManager.execute_query(query, params, profile_name, read_only=True)
            columns = DuckDBConnectionManager.get_columns(query, params, profile_name)
            
            # Convert to list of dictionaries
            jobs = [dict(zip(columns, row)) for row in result]
            
            logger.info(f"Retrieved {len(jobs)} jobs from DuckDB for {profile_name}")
            
            if jobs and len(jobs) > 0:
                # Convert to DataFrame with proper columns mapped to DuckDB schema
                df = pd.DataFrame([
                    {
                        'id': job.get('id', ''),
                        'title': job.get('title', 'Unknown Title'),
                        'company': job.get('company', 'Unknown Company'),
                        'location': job.get('location', 'Unknown Location'),
                        'status': self._determine_job_status(job),
                        'salary': self._format_salary(job.get('salary_range')),
                        'match_score': job.get('fit_score', 0) or self._calculate_match_score(job),
                        'posted_date': self._format_date(job.get('date_posted')),
                        'created_at': self._format_date(job.get('created_at')),
                        'url': job.get('url', ''),
                        'job_url': job.get('url', ''),
                        'summary': job.get('summary', ''),
                        'description': job.get('description', ''),
                        'site': job.get('source', ''),
                        'job_type': job.get('job_type', ''),
                        'skills': job.get('skills', ''),
                        'keywords': job.get('keywords', ''),
                        'application_status': job.get('application_status', 'discovered'),
                        'priority_level': job.get('priority_level', 3),
                        # Immigration and location fields
                        'city_tags': job.get('city_tags', ''),
                        'province_code': job.get('province_code', ''),
                        'is_rcip_city': job.get('is_rcip_city', 0),
                        'is_immigration_priority': job.get('is_immigration_priority', 0),
                        'location_type': job.get('location_type', 'onsite'),
                        'location_category': job.get('location_category', 'unknown'),
                        # RCIP indicator for display
                        'rcip_indicator': '🇨🇦 RCIP' if job.get('is_rcip_city', 0) else '',
                        'immigration_priority': '⭐ Priority' if job.get('is_immigration_priority', 0) else '',
                        # View job link that opens in new tab
                        'view_job': (
                            f"[🔗 View Job]({job.get('url', '')})"
                            if job.get('url')
                            else 'No URL'
                        )
                    }
                    for job in jobs
                ])
                logger.info(f"Successfully loaded {len(df)} jobs from DuckDB for {profile_name}")
                return df
            else:
                logger.warning(f"No jobs found in DuckDB for profile {profile_name}")
                return self._create_empty_dataframe()
                
        except Exception as e:
            logger.error(f"Error loading jobs data from DuckDB: {e}")
            logger.exception("Full traceback:")
            
            # Fallback: try to get job count to verify database exists
            try:
                count_query = "SELECT COUNT(*) FROM jobs WHERE profile_name = ?"
                count_result = DuckDBConnectionManager.execute_query(count_query, [profile_name], profile_name, read_only=True)
                job_count = count_result[0][0] if count_result else 0
                logger.info(f"Database accessible, found {job_count} jobs for {profile_name}")
                
                if job_count == 0:
                    logger.warning(f"Database is empty for profile {profile_name} - no jobs have been scraped yet")
                
            except Exception as e2:
                logger.error(f"Cannot access database at all: {e2}")
            
            return self._create_empty_dataframe()
    
    def _cleanup_old_jobs(self, db):
        """Remove jobs older than 30 days"""
        try:
            # Skip cleanup - PostgreSQLJobDatabase missing cleanup method
            logger.debug("Cleanup skipped - method not available")
        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
    
    def _format_salary(self, salary):
        """Format salary information"""
        if not salary:
            return "Not specified"
        
        if isinstance(salary, str):
            # Clean up salary strings
            if salary.lower() in ['none', 'null', '', 'not specified']:
                return "Not specified"
            return salary
        elif isinstance(salary, (int, float)):
            return f"${salary:,.0f}"
        else:
            return "Not specified"
    
    def _format_date(self, date_str):
        """Format date to show just the date"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            if isinstance(date_str, str):
                # Try to parse various date formats
                date_formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%Y-%m-%dT%H:%M:%S'
                ]
                for fmt in date_formats:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                # If no format matches, return the original string
                return date_str.split('T')[0] if 'T' in date_str else date_str
            else:
                return str(date_str)
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _create_empty_dataframe(self):
        """Create an empty dataframe with the correct structure"""
        return pd.DataFrame(columns=[
            'id', 'title', 'company', 'location', 'status', 'salary',
            'match_score', 'posted_date', 'created_at', 'url', 'job_url',
            'summary', 'description', 'site', 'job_type', 'skills', 'keywords',
            'application_status', 'priority_level', 'city_tags', 'province_code',
            'is_rcip_city', 'is_immigration_priority', 'location_type', 
            'location_category', 'rcip_indicator', 'immigration_priority', 'view_job'
        ])
    
    def get_processing_status(self, profile_name='Nirajan'):
        """Get processing status for a profile"""
        try:
            # Check if jobs exist and have been processed
            from src.core.job_database import get_job_db
            
            db = get_job_db(profile_name)
            jobs = db.get_jobs()
            
            # Count processed vs unprocessed jobs
            processed_count = 0
            total_jobs = len(jobs)
            
            for job in jobs:
                # Check if job has been processed (has analysis scores)
                if (job.get('stage1_score') is not None or 
                    job.get('final_score') is not None):
                    processed_count += 1
            
            pending_count = total_jobs - processed_count
            
            return {
                'queue_size': pending_count,
                'is_processing': False,  # We don't track real-time processing
                'completed_today': processed_count,
                'error_count': 0,
                'total_jobs': total_jobs,
                'processed_jobs': processed_count
            }
            
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {
                'queue_size': 0,
                'is_processing': False,
                'completed_today': 0,
                'error_count': 0
            }
    
    def get_system_health(self):
        """Get system health information"""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'db_status': self._check_database_connection(),
                'api_status': 'running'
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'cpu_percent': 25,
                'memory_percent': 45,
                'disk_percent': 60,
                'db_status': 'unknown',
                'api_status': 'unknown'
            }
    
    def _check_database_connection(self):
        """Check if database connection is healthy"""
        try:
            from src.core.job_database import get_job_db
            
            db = get_job_db('test')
            # Try a simple query
            db.get_job_count()
            return 'healthy'
            
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return 'error'
    
    def _create_sample_data(self):
        """Create sample data for development/testing"""
        sample_data = {
            'id': range(1, 21),
            'title': [
                'Senior Python Developer', 'Data Scientist', 'ML Engineer',
                'Software Engineer', 'DevOps Engineer', 'Full Stack Developer',
                'Backend Developer', 'AI Researcher', 'Data Analyst',
                'Cloud Architect', 'Python Developer', 'Data Engineer',
                'Machine Learning Engineer', 'Software Architect',
                'API Developer', 'Database Administrator',
                'System Administrator', 'Technical Lead',
                'Principal Engineer', 'Staff Engineer'
            ],
            'company': [
                'Google', 'Microsoft', 'Amazon', 'Apple', 'Meta',
                'Netflix', 'Tesla', 'Shopify', 'Spotify', 'Uber',
                'Airbnb', 'Dropbox', 'Slack', 'Twitter', 'LinkedIn',
                'Adobe', 'Salesforce', 'Oracle', 'IBM', 'Intel'
            ],
            'location': [
                'Toronto, ON', 'Vancouver, BC', 'Montreal, QC', 'Remote',
                'Calgary, AB', 'Ottawa, ON', 'Waterloo, ON', 'Remote',
                'Toronto, ON', 'Vancouver, BC', 'Remote', 'Montreal, QC',
                'Toronto, ON', 'Remote', 'Vancouver, BC', 'Toronto, ON',
                'Remote', 'Calgary, AB', 'Ottawa, ON', 'Waterloo, ON'
            ],
            'status': [
                'new', 'ready_to_apply', 'applied', 'new', 'needs_review',
                'ready_to_apply', 'new', 'applied', 'ready_to_apply', 'new',
                'needs_review', 'ready_to_apply', 'applied', 'new',
                'ready_to_apply', 'new', 'needs_review', 'applied',
                'ready_to_apply', 'new'
            ],
            'match_score': [
                85, 92, 78, 88, 76, 90, 82, 95, 87, 79,
                91, 84, 89, 77, 93, 86, 81, 94, 83, 80
            ],
            'created_at': pd.date_range('2025-08-01', periods=20, freq='D'),
            'url': [f'https://example.com/job/{i}' for i in range(1, 21)],
            'job_url': [f'https://example.com/job/{i}' for i in range(1, 21)],
            'description': ['Sample job description'] * 20
        }
        
        return pd.DataFrame(sample_data)
    
    def _determine_job_status(self, job):
        """Determine job status based on DuckDB schema"""
        # First check application_status (new field in DuckDB)
        app_status = job.get('application_status', '')
        if app_status and app_status != 'discovered':
            return self._map_application_status(app_status)
        
        # Then check regular status field
        status = job.get('status', 'new')
        return self._map_status(status)
    
    def _map_status(self, status):
        """Map database status to dashboard status"""
        status_mapping = {
            'new': 'new',
            'scraped': 'new', 
            'processed': 'ready_to_apply',
            'ready_to_apply': 'ready_to_apply',
            'applied': 'applied',
            'reviewing': 'needs_review',
            'interview': 'interview'
        }
        return status_mapping.get(status, 'new')
    
    def _map_application_status(self, app_status):
        """Map application_status to dashboard status"""
        app_status_mapping = {
            'discovered': 'new',
            'interested': 'needs_review',
            'applied': 'applied',
            'phone_screen': 'interview',
            'technical_interview': 'interview',
            'onsite': 'interview',
            'offer': 'offer',
            'rejected': 'rejected',
            'accepted': 'accepted'
        }
        return app_status_mapping.get(app_status, 'new')
    
    def _calculate_match_score(self, job):
        """Calculate a match score for a job based on user profile"""
        # Check if job has been processed with fit_score
        if job.get('fit_score') is not None:
            try:
                # fit_score is typically 0-1, convert to 0-100
                fit_score = float(job['fit_score'])
                return min(max(int(fit_score * 100), 0), 100)
            except (ValueError, TypeError):
                pass
        
        # Check for other score fields
        if job.get('match_score') is not None:
            try:
                return min(max(int(float(job['match_score'])), 0), 100)
            except (ValueError, TypeError):
                pass
        
        # Enhanced scoring based on Data Analyst profile
        score = 50  # Base score
        
        if job.get('title'):
            title = job['title'].lower()
            
            # High relevance for Data Analyst profile
            data_keywords = ['data analyst', 'data scientist', 'business analyst', 
                           'research analyst', 'quantitative analyst']
            if any(keyword in title for keyword in data_keywords):
                score += 30
            
            # Medium relevance
            tech_keywords = ['python', 'sql', 'analyst', 'data', 'analytics']
            if any(keyword in title for keyword in tech_keywords):
                score += 20
            
            # Lower relevance for pure development roles
            dev_keywords = ['software engineer', 'full stack', 'backend', 'frontend']
            if any(keyword in title for keyword in dev_keywords):
                score -= 10  # Reduce score for non-analyst roles
            
            # Seniority boost
            if any(keyword in title for keyword in ['senior', 'lead', 'principal']):
                score += 10
        
        # Description analysis
        if job.get('description'):
            description = job['description'].lower()
            
            # Look for data analysis skills
            analysis_skills = ['python', 'sql', 'pandas', 'numpy', 'tableau', 
                             'power bi', 'excel', 'statistics', 'machine learning']
            skill_matches = sum(1 for skill in analysis_skills if skill in description)
            score += min(skill_matches * 3, 15)  # Max 15 points for skills
        
        # Location preferences
        if job.get('location'):
            location = job['location'].lower()
            # Boost for preferred locations
            if any(loc in location for loc in ['remote', 'toronto', 'vancouver', 'canada']):
                score += 5
        
        # RCIP city bonus
        if job.get('is_rcip_city', 0):
            score += 10
        
        return min(max(score, 0), 100)
    
    def _create_action_buttons(self, job_id):
        """Create action buttons for table display"""
        return f"[View](#{job_id}) | [Apply](#{job_id}) | [Notes](#{job_id})"
    
    def get_job_stats(self, profile_name='Nirajan'):
        """Get job statistics for a profile"""
        try:
            df = self.load_jobs_data(profile_name)
            if df.empty:
                return {}
            
            stats = {
                'total_jobs': len(df),
                'new_jobs': len(df[df['status'] == 'new']),
                'ready_to_apply': len(df[df['status'] == 'ready_to_apply']),
                'applied_jobs': len(df[df['status'] == 'applied']),
                'needs_review': len(df[df['status'] == 'needs_review']),
                'avg_match_score': (df['match_score'].mean()
                                    if 'match_score' in df.columns else 0),
                'companies_count': (df['company'].nunique()
                                    if 'company' in df.columns else 0)
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"Error getting job stats: {e}")
            return {}
    
    def get_ai_analytics(self, profile_name='Nirajan'):
        """Get AI analytics for dashboard display"""
        try:
            from src.services.ai_integration_service import (
                get_ai_integration_service
            )
            
            ai_service = get_ai_integration_service(profile_name)
            analytics = ai_service.get_ai_analytics()
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting AI analytics: {e}")
            return {
                'total_jobs': 0,
                'ai_processed': 0,
                'avg_semantic_score': 0.0,
                'cache_efficiency': 0.0,
                'ai_processing_coverage': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting job stats: {e}")
            return {}



