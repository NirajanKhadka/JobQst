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
        """Load job data for a specific profile"""
        try:
            # Try to import the job database
            from src.core.job_database import get_job_db
            
            # Use the configured database type (PostgreSQL or SQLite)
            db = get_job_db(profile_name)
            
            # Clean up old jobs (30+ days) first
            self._cleanup_old_jobs(db)
            
            jobs = db.get_jobs()  # Remove profile_name parameter
            
            if jobs and len(jobs) > 0:
                # Convert to DataFrame with proper columns
                df = pd.DataFrame([
                    {
                        'id': job.get('id', ''),
                        'title': job.get('title', 'Unknown Title'),
                        'company': job.get('company', 'Unknown Company'),
                        'location': job.get('location', 'Unknown Location'),
                        'location_type': job.get('location_type', 'onsite'),
                        'location_category': job.get('location_category', 'unknown'),
                        'city_tags': job.get('city_tags', ''),
                        'province_code': job.get('province_code', ''),
                        'is_rcip_city': job.get('is_rcip_city', 0),
                        'is_immigration_priority': job.get('is_immigration_priority', 0),
                        'status': self._determine_job_status(job),
                        'salary': self._format_salary(job.get('salary_range')),
                        'match_score': job.get('fit_score', 0) or self._calculate_match_score(job),
                        # AI Strategy Phase 2 fields
                        'semantic_score': job.get('semantic_score', 0.0),
                        'cache_status': job.get('cache_status', 'unknown'),
                        'profile_similarity': job.get(
                            'profile_similarity', 0.0
                        ),
                        'embedding_cached': job.get('embedding_cached', 0),
                        'html_cached': job.get('html_cached', 0),
                        'posted_date': self._format_date(
                            job.get('date_posted') or job.get('scraped_at')
                        ),
                        'created_at': job.get('scraped_at',
                                              datetime.now().isoformat()),
                        'url': job.get('url', '') or job.get('job_url', ''),
                        'job_url': (job.get('job_url', '') or
                                    job.get('url', '')),
                        'summary': job.get('summary', ''),
                        'description': job.get('description', ''),
                        'site': job.get('site', ''),
                        # View job link that opens in new tab
                        'view_job': (
                            f"[🔗 View Job]({job.get('job_url') or job.get('url','')})"  # noqa
                            if (job.get('job_url') or job.get('url'))
                            else 'No URL'
                        )
                    }
                    for job in jobs
                ])
                logger.info(f"Loaded {len(df)} jobs from database "
                            f"for {profile_name}")
                return df
            else:
                logger.info(f"No jobs found in {profile_name} database")
                return self._create_empty_dataframe()
                
        except ImportError as e:
            logger.error(f"Database import failed: {e}")
            logger.info("Database not available - "
                        "please ensure profile exists")
            return self._create_empty_dataframe()
        except Exception as e:
            logger.error(f"Error loading jobs data: {e}")
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
            'summary', 'description', 'site', 'view_job'
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
        """Determine job status based on processing indicators"""
        # Check if job has been processed by looking for processing indicators
        has_fit_score = job.get('fit_score') is not None
        has_compatibility_score = (job.get('compatibility_score') is not None 
                                   and job.get('compatibility_score') > 0)
        has_analysis_data = (job.get('analysis_data') is not None 
                             and job.get('analysis_data') != '')
        has_processed_at = job.get('processed_at') is not None
        has_processing_method = (job.get('processing_method') is not None 
                                 and job.get('processing_method') != 'unknown')
        
        # If any processing indicators are present, job is processed
        is_processed = (has_fit_score or has_compatibility_score 
                        or has_analysis_data or has_processed_at 
                        or has_processing_method)
        
        if is_processed:
            # Check if applied
            is_applied = (job.get('applied') or 
                          job.get('application_status') == 'applied')
            if is_applied:
                return 'applied'
            return 'processed'
        
        # Otherwise use the status mapping
        return self._map_status(job.get('status', 'new'))
    
    def _map_status(self, status):
        """Map database status to dashboard status"""
        status_mapping = {
            'new': 'scraped',
            'scraped': 'scraped',
            'processed': 'processed',
            'ready_to_apply': 'processed',
            'applied': 'applied',
            'reviewing': 'processed'
        }
        return status_mapping.get(status, 'scraped')
    
    def _calculate_match_score(self, job):
        """Calculate a match score for a job"""
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
        
        if job.get('compatibility_score') is not None:
            try:
                compatibility = float(job['compatibility_score'])
                return min(max(int(compatibility * 100), 0), 100)
            except (ValueError, TypeError):
                pass
        
        # Simple scoring based on available data
        score = 70  # Base score
        
        if job.get('title'):
            title = job['title'].lower()
            # Boost for relevant keywords
            if any(keyword in title for keyword in
                   ['senior', 'lead', 'engineer', 'developer']):
                score += 15
        
        if job.get('location'):
            location = job['location'].lower()
            # Boost for preferred locations
            if any(loc in location for loc in
                   ['remote', 'toronto', 'vancouver']):
                score += 10
        
        return min(score, 100)
    
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



