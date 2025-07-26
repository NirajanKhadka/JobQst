"""
Job Worker Function for Enhanced 2-Worker Job Processing System
Implements worker function compatible with multiprocessing.Pool for parallel job processing.
"""

import logging
import time
import traceback
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.hybrid_processor import HybridProcessingEngine, HybridProcessingResult
from src.core.job_database import ModernJobDatabase, get_job_db
from src.utils.profile_helpers import get_available_profiles

# Configure logging for worker processes
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobProcessingError(Exception):
    """Custom exception for job processing errors."""
    pass

def worker_function(job_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Worker function for multiprocessing.Pool that processes a batch of jobs.
    
    This function is designed to be used with multiprocessing.Pool.map() and processes
    multiple jobs in a single worker process using the hybrid processing engine.
    
    Args:
        job_batch: List of job dictionaries to process
        
    Returns:
        List of processed job dictionaries with updated status and analysis
    """
    worker_id = os.getpid()
    logger.info(f"Worker {worker_id} starting batch processing of {len(job_batch)} jobs")
    
    processed_jobs = []
    start_time = time.time()
    
    try:
        # Initialize hybrid processing engine for this worker
        hybrid_processor = HybridProcessingEngine()
        
        # Process each job in the batch
        for i, job_data in enumerate(job_batch):
            try:
                processed_job = process_single_job(job_data, hybrid_processor, worker_id, i + 1)
                processed_jobs.append(processed_job)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} failed to process job {job_data.get('id', 'unknown')}: {e}")
                # Create error result to maintain batch integrity
                error_job = create_error_job_result(job_data, str(e))
                processed_jobs.append(error_job)
        
        processing_time = time.time() - start_time
        logger.info(f"Worker {worker_id} completed batch processing in {processing_time:.2f}s")
        
        return processed_jobs
        
    except Exception as e:
        logger.error(f"Worker {worker_id} batch processing failed: {e}")
        logger.error(f"Worker {worker_id} traceback: {traceback.format_exc()}")
        
        # Return error results for all jobs to maintain batch integrity
        return [create_error_job_result(job, f"Batch processing failed: {e}") for job in job_batch]

def process_single_job(job_data: Dict[str, Any], 
                      hybrid_processor: HybridProcessingEngine,
                      worker_id: int,
                      job_number: int) -> Dict[str, Any]:
    """
    Process a single job using the hybrid processing engine.
    
    Args:
        job_data: Job data dictionary
        hybrid_processor: Initialized hybrid processing engine
        worker_id: Worker process ID for logging
        job_number: Job number in batch for logging
        
    Returns:
        Processed job dictionary with updated status and analysis
    """
    job_id = job_data.get('id', 'unknown')
    logger.debug(f"Worker {worker_id} processing job {job_number}: {job_id}")
    
    start_time = time.time()
    
    try:
        # Validate job data
        if not validate_job_data(job_data):
            raise JobProcessingError("Invalid job data structure")
        
        # Process job with hybrid engine
        hybrid_result = hybrid_processor.process_job(job_data)
        
        # Convert hybrid result to job update format
        processed_job = convert_hybrid_result_to_job_data(job_data, hybrid_result)
        
        # Update job status to 'processed'
        processed_job['status'] = 'processed'
        processed_job['processed_at'] = time.time()
        processed_job['processing_worker_id'] = worker_id
        processed_job['processing_time'] = time.time() - start_time
        
        logger.debug(f"Worker {worker_id} completed job {job_number} in {processed_job['processing_time']:.2f}s")
        
        return processed_job
        
    except Exception as e:
        logger.error(f"Worker {worker_id} failed to process job {job_id}: {e}")
        raise JobProcessingError(f"Job processing failed: {e}")

def validate_job_data(job_data: Dict[str, Any]) -> bool:
    """
    Validate that job data has required fields for processing.
    
    Args:
        job_data: Job data dictionary
        
    Returns:
        True if job data is valid, False otherwise
    """
    # Check for ID and title
    if not job_data.get('id') and not job_data.get('job_id'):
        logger.warning("Job data missing ID field")
        return False
    
    if not job_data.get('title'):
        logger.warning("Job data missing title field")
        return False
    
    # Check for description (can be 'description' or 'job_description')
    if not job_data.get('description') and not job_data.get('job_description'):
        logger.warning("Job data missing description field")
        return False
    
    # Check that status is 'scraped' (ready for processing)
    if job_data.get('status') != 'scraped':
        logger.warning(f"Job {job_data.get('id', job_data.get('job_id'))} has status '{job_data.get('status')}', expected 'scraped'")
        return False
    
    return True

def convert_hybrid_result_to_job_data(original_job: Dict[str, Any], 
                                    hybrid_result: HybridProcessingResult) -> Dict[str, Any]:
    """
    Convert hybrid processing result back to job data format.
    
    Args:
        original_job: Original job data dictionary
        hybrid_result: Result from hybrid processing engine
        
    Returns:
        Updated job data dictionary with processing results
    """
    # Start with original job data
    processed_job = original_job.copy()
    
    # Update with hybrid processing results
    if hybrid_result.title:
        processed_job['title'] = hybrid_result.title
    
    if hybrid_result.company:
        processed_job['company'] = hybrid_result.company
    
    if hybrid_result.location:
        processed_job['location'] = hybrid_result.location
    
    if hybrid_result.salary_range:
        processed_job['salary_range'] = hybrid_result.salary_range
    
    if hybrid_result.experience_level:
        processed_job['experience_level'] = hybrid_result.experience_level
    
    if hybrid_result.employment_type:
        processed_job['employment_type'] = hybrid_result.employment_type
    
    # Add enhanced analysis data
    processed_job['required_skills'] = hybrid_result.required_skills
    processed_job['job_requirements'] = hybrid_result.job_requirements
    processed_job['compatibility_score'] = hybrid_result.compatibility_score
    processed_job['analysis_confidence'] = hybrid_result.analysis_confidence
    processed_job['extracted_benefits'] = hybrid_result.extracted_benefits
    processed_job['analysis_reasoning'] = hybrid_result.reasoning
    
    # Add processing metadata
    processed_job['custom_logic_confidence'] = hybrid_result.custom_logic_confidence
    processed_job['llm_processing_time'] = hybrid_result.llm_processing_time
    processed_job['total_processing_time'] = hybrid_result.total_processing_time
    processed_job['processing_method'] = hybrid_result.processing_method
    processed_job['fallback_used'] = hybrid_result.fallback_used
    
    return processed_job

def create_error_job_result(job_data: Dict[str, Any], error_message: str) -> Dict[str, Any]:
    """
    Create error result for failed job processing.
    
    Args:
        job_data: Original job data
        error_message: Error message describing the failure
        
    Returns:
        Job data with error status and information
    """
    error_job = job_data.copy()
    
    # Set error status and information
    error_job['status'] = 'processing_error'
    error_job['error_message'] = error_message
    error_job['processed_at'] = time.time()
    error_job['processing_worker_id'] = os.getpid()
    
    # Set default values for missing analysis data
    error_job['required_skills'] = []
    error_job['job_requirements'] = []
    error_job['compatibility_score'] = 0.0
    error_job['analysis_confidence'] = 0.0
    error_job['extracted_benefits'] = []
    error_job['analysis_reasoning'] = f"Processing failed: {error_message}"
    error_job['processing_method'] = 'error'
    error_job['fallback_used'] = True
    
    return error_job

def batch_jobs_for_processing(jobs: List[Dict[str, Any]], batch_size: int = 5) -> List[List[Dict[str, Any]]]:
    """
    Batch jobs for multiprocessing worker distribution.
    
    Args:
        jobs: List of job dictionaries to batch
        batch_size: Number of jobs per batch
        
    Returns:
        List of job batches for worker processing
    """
    batches = []
    
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]
        batches.append(batch)
    
    logger.info(f"Created {len(batches)} batches from {len(jobs)} jobs (batch_size={batch_size})")
    
    return batches

def update_jobs_in_database(processed_jobs: List[Dict[str, Any]], profile_name: str) -> Tuple[int, int]:
    """
    Update processed jobs in the database.
    
    Args:
        processed_jobs: List of processed job dictionaries
        profile_name: Profile name for database selection
        
    Returns:
        Tuple of (successful_updates, failed_updates)
    """
    successful_updates = 0
    failed_updates = 0
    
    try:
        db = get_job_db(profile_name)
        
        for job in processed_jobs:
            try:
                # Update job in database
                success = db.update_job(job['id'], job)
                
                if success:
                    successful_updates += 1
                    logger.debug(f"Updated job {job['id']} in database")
                else:
                    failed_updates += 1
                    logger.warning(f"Failed to update job {job['id']} in database")
                    
            except Exception as e:
                failed_updates += 1
                logger.error(f"Error updating job {job.get('id', 'unknown')} in database: {e}")
        
        logger.info(f"Database update complete: {successful_updates} successful, {failed_updates} failed")
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        failed_updates = len(processed_jobs)
    
    return successful_updates, failed_updates

# Worker initialization function for multiprocessing
def init_worker():
    """
    Initialize worker process for multiprocessing.Pool.
    
    This function is called once per worker process to set up logging
    and any other worker-specific initialization.
    """
    worker_id = os.getpid()
    
    # Configure worker-specific logging
    worker_logger = logging.getLogger(f"worker_{worker_id}")
    worker_logger.info(f"Worker {worker_id} initialized")
    
    # Set up any worker-specific resources here
    # (database connections, etc. should be created per-job to avoid sharing issues)

# Convenience functions for testing and integration
def test_worker_function():
    """Test the worker function with sample data."""
    sample_jobs = [
        {
            'id': 'test_job_1',
            'title': 'Software Engineer',
            'description': 'Looking for a software engineer with Python experience',
            'company': 'TechCorp',
            'location': 'Toronto, ON',
            'status': 'scraped',
            'url': 'https://example.com/job1'
        },
        {
            'id': 'test_job_2',
            'title': 'Data Scientist',
            'description': 'Data scientist role requiring Python and machine learning',
            'company': 'DataCorp',
            'location': 'Vancouver, BC',
            'status': 'scraped',
            'url': 'https://example.com/job2'
        }
    ]
    
    logger.info("Testing worker function with sample data...")
    
    try:
        results = worker_function(sample_jobs)
        logger.info(f"Worker function test completed successfully with {len(results)} results")
        
        for result in results:
            logger.info(f"Processed job {result['id']}: status={result['status']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Worker function test failed: {e}")
        return False

if __name__ == "__main__":
    # Run test when executed directly
    test_worker_function()