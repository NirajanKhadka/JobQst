#!/usr/bin/env python3
"""
JobQst Synchronization Fix
Comprehensive solution for scraper→database→dashboard sync issues
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Enhanced batch result for scraper compatibility"""

    total_processed: int
    inserted_count: int
    skipped_duplicates: int
    failed_count: int
    processing_time: float
    batch_id: str
    errors: List[str]


class JobDataConverter:
    """Convert between scraper data and JobData objects"""

    @staticmethod
    def scraper_dict_to_job_data(scraper_data: Dict[str, Any]) -> "JobData":
        """Convert scraper dictionary to JobData object"""
        from ..core.job_data import JobData

        return JobData(
            title=scraper_data.get("title", ""),
            company=scraper_data.get("company", ""),
            location=scraper_data.get("location", ""),
            url=scraper_data.get("url", ""),  # Map url correctly
            summary=scraper_data.get("summary", ""),
            salary=scraper_data.get("salary_range", ""),
            job_type=scraper_data.get("job_type", ""),
            posted_date=scraper_data.get("scraped_at", ""),
            site=scraper_data.get("site", ""),
            search_keyword=scraper_data.get("search_keyword", ""),
            scraped_at=scraper_data.get("scraped_at", datetime.now().isoformat()),
            raw_data=scraper_data.get("raw_data", {}),
        )

    @staticmethod
    def normalize_job_fields(job_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field names for dashboard compatibility"""
        normalized = job_dict.copy()

        # Fix field mapping issues
        if "url" in normalized and "job_url" not in normalized:
            normalized["job_url"] = normalized["url"]

        if "fit_score" in normalized and "match_score" not in normalized:
            normalized["match_score"] = normalized["fit_score"]

        if "job_description" in normalized and "description" not in normalized:
            normalized["description"] = normalized["job_description"]

        return normalized


# Enhanced DuckDB methods to add to duckdb_database.py
ENHANCED_DUCKDB_METHODS = '''
    def add_jobs_batch_enhanced(
        self, 
        jobs_data: List[Dict[str, Any]], 
        batch_size: int = 100,
        skip_duplicates: bool = True,
        default_status: str = 'new'
    ) -> BatchResult:
        """Enhanced batch insert compatible with scraper expectations"""
        start_time = time.time()
        
        if not jobs_data:
            return BatchResult(
                total_processed=0, inserted_count=0, skipped_duplicates=0,
                failed_count=0, processing_time=0.0, batch_id="empty",
                errors=[]
            )
        
        try:
            from .sync_fix import JobDataConverter
            
            # Convert scraper dicts to JobData objects
            job_objects = []
            errors = []
            
            for i, job_dict in enumerate(jobs_data):
                try:
                    # Ensure required fields and set defaults
                    job_dict = job_dict.copy()
                    job_dict.setdefault('status', default_status)
                    
                    # Convert to JobData object
                    job_obj = JobDataConverter.scraper_dict_to_job_data(job_dict)
                    job_objects.append(job_obj)
                except Exception as e:
                    errors.append(f"Job {i}: {str(e)}")
            
            # Use existing add_jobs_batch method
            inserted_count = self.add_jobs_batch(job_objects)
            
            processing_time = time.time() - start_time
            batch_id = f"batch_{int(start_time)}"
            
            return BatchResult(
                total_processed=len(jobs_data),
                inserted_count=inserted_count,
                skipped_duplicates=len(jobs_data) - inserted_count - len(errors),
                failed_count=len(errors),
                processing_time=processing_time,
                batch_id=batch_id,
                errors=errors
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Enhanced batch insert failed: {e}")
            
            return BatchResult(
                total_processed=len(jobs_data),
                inserted_count=0,
                skipped_duplicates=0,
                failed_count=len(jobs_data),
                processing_time=processing_time,
                batch_id=f"failed_{int(start_time)}",
                errors=[str(e)]
            )
    
    def _job_data_to_minimal_dict_enhanced(self, job_data) -> Dict[str, Any]:
        """Enhanced version with better field mapping"""
        # Get base dict
        job_dict = self._job_data_to_minimal_dict(job_data)
        
        # Add missing fields that dashboard expects
        job_dict.update({
            'job_url': job_dict.get('url', ''),  # Dashboard compatibility
            'match_score': job_dict.get('fit_score', 0),  # Dashboard compatibility
            'posted_date': job_dict.get('date_posted'),
            'view_job': f"[🔗 View Job]({job_dict.get('url', '')})" if job_dict.get('url') else 'No URL'
        })
        
        return job_dict
'''

# Fix for DataLoader field mapping
DATALOADER_FIX = '''
    def load_jobs_data(self, profile_name='Nirajan'):
        """Fixed version with proper field mapping"""
        try:
            from src.core.job_database import get_job_db
            from .sync_fix import JobDataConverter
            
            db = get_job_db(profile_name)
            jobs = db.get_jobs()
            
            if jobs and len(jobs) > 0:
                # Normalize all job fields
                normalized_jobs = []
                for job in jobs:
                    normalized_job = JobDataConverter.normalize_job_fields(job)
                    normalized_jobs.append(normalized_job)
                
                df = pd.DataFrame(normalized_jobs)
                logger.info(f"✅ Loaded {len(df)} jobs with proper field mapping")
                return df
                
        except Exception as e:
            logger.error(f"Error loading jobs data: {e}")
            return pd.DataFrame()
'''

print("🔧 JobQst Sync Fix Implementation Created")
print("📋 This file contains the comprehensive solution for all sync issues")
