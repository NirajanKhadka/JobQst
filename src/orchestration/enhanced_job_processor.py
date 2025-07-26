"""
Enhanced Job Processor Orchestrator
Main orchestrator for the 2-worker multiprocessing job processing system.
"""

import logging
import time
import multiprocessing as mp
from multiprocessing import Pool
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sys
import os
from dataclasses import dataclass
from enum import Enum

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.job_database import ModernJobDatabase, get_job_db
from src.orchestration.job_worker import worker_function, batch_jobs_for_processing, init_worker, update_jobs_in_database
from src.ai.gpu_ollama_client import get_gpu_ollama_client
from src.utils.profile_helpers import get_available_profiles

logger = logging.getLogger(__name__)

class ProcessingStatus(Enum):
    """Processing status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    STOPPED = "stopped"

@dataclass
class ProcessingStats:
    """Statistics for job processing session."""
    total_jobs: int = 0
    processed_jobs: int = 0
    failed_jobs: int = 0
    processing_time: float = 0.0
    average_job_time: float = 0.0
    jobs_per_second: float = 0.0
    worker_count: int = 2
    batch_size: int = 5
    status: ProcessingStatus = ProcessingStatus.IDLE

class EnhancedJobProcessor:
    """
    Main orchestrator for 2-worker job processing system using multiprocessing.Pool.
    
    This processor replaces the old 6-worker system with an efficient 2-worker
    multiprocessing architecture that uses GPU-accelerated Ollama for AI analysis.
    """
    
    def __init__(self, 
                 profile_name: str,
                 worker_count: int = 2,
                 batch_size: int = 5,
                 timeout: int = 300):
        """
        Initialize the enhanced job processor.
        
        Args:
            profile_name: Profile name for database and processing
            worker_count: Number of worker processes (default: 2)
            batch_size: Jobs per batch for worker processing (default: 5)
            timeout: Timeout for worker processes in seconds (default: 300)
        """
        self.profile_name = profile_name
        self.worker_count = worker_count
        self.batch_size = batch_size
        self.timeout = timeout
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize components
        self.db = get_job_db(profile_name)
        self.stats = ProcessingStats(worker_count=worker_count, batch_size=batch_size)
        
        # Validate setup
        self._validate_setup()
        
        self.logger.info(f"Enhanced job processor initialized for profile '{profile_name}' with {worker_count} workers")
    
    def _validate_setup(self) -> None:
        """Validate that all required components are available."""
        # Check database connectivity
        try:
            self.db.get_job_stats()
            self.logger.debug("Database connectivity verified")
        except Exception as e:
            raise RuntimeError(f"Database connection failed: {e}")
        
        # Check Ollama availability
        try:
            ollama_client = get_gpu_ollama_client()
            if not ollama_client.is_available():
                self.logger.warning("Ollama service not available - will use custom logic only")
            else:
                self.logger.info("GPU Ollama service available for AI analysis")
        except Exception as e:
            self.logger.warning(f"Ollama client initialization failed: {e}")
        
        # Check multiprocessing support
        try:
            mp.set_start_method('spawn', force=True)  # Use spawn method for Windows compatibility
            self.logger.debug("Multiprocessing setup verified")
        except Exception as e:
            self.logger.warning(f"Multiprocessing setup issue: {e}")
    
    def process_jobs_parallel(self, limit: Optional[int] = None) -> ProcessingStats:
        """
        Process jobs using multiprocessing.Pool(processes=2) for parallel execution.
        
        Args:
            limit: Maximum number of jobs to process (None for all available)
            
        Returns:
            ProcessingStats with processing results and metrics
        """
        self.logger.info(f"Starting parallel job processing with {self.worker_count} workers")
        
        start_time = time.time()
        self.stats.status = ProcessingStatus.RUNNING
        
        try:
            # Get jobs ready for processing
            jobs_to_process = self._get_jobs_for_processing(limit)
            
            if not jobs_to_process:
                self.logger.info("No jobs available for processing")
                self.stats.status = ProcessingStatus.COMPLETED
                return self.stats
            
            self.stats.total_jobs = len(jobs_to_process)
            self.logger.info(f"Found {self.stats.total_jobs} jobs ready for processing")
            
            # Batch jobs for worker distribution
            job_batches = batch_jobs_for_processing(jobs_to_process, self.batch_size)
            
            # Process jobs using multiprocessing pool
            processed_results = self._process_with_multiprocessing_pool(job_batches)
            
            # Update database with results
            self._update_database_with_results(processed_results)
            
            # Calculate final statistics
            self._calculate_final_stats(start_time)
            
            self.stats.status = ProcessingStatus.COMPLETED
            self.logger.info(f"Processing completed: {self.stats.processed_jobs}/{self.stats.total_jobs} jobs processed successfully")
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Parallel processing failed: {e}")
            self.stats.status = ProcessingStatus.ERROR
            raise
    
    def _get_jobs_for_processing(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get jobs that are ready for processing (status = 'scraped').
        
        Args:
            limit: Maximum number of jobs to retrieve
            
        Returns:
            List of job dictionaries ready for processing
        """
        try:
            # Get jobs with status 'scraped' (ready for processing)
            jobs = self.db.get_jobs_by_status('scraped', limit=limit)
            
            self.logger.debug(f"Retrieved {len(jobs)} jobs with 'scraped' status")
            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve jobs for processing: {e}")
            return []
    
    def _process_with_multiprocessing_pool(self, job_batches: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Process job batches using multiprocessing.Pool.
        
        Args:
            job_batches: List of job batches for worker processing
            
        Returns:
            List of all processed job results
        """
        self.logger.info(f"Processing {len(job_batches)} batches with {self.worker_count} workers")
        
        all_results = []
        
        try:
            # Create multiprocessing pool with 2 workers
            with Pool(processes=self.worker_count, initializer=init_worker) as pool:
                self.logger.debug(f"Created multiprocessing pool with {self.worker_count} workers")
                
                # Process batches in parallel
                batch_results = pool.map(worker_function, job_batches)
                
                # Flatten results from all batches
                for batch_result in batch_results:
                    all_results.extend(batch_result)
                
                self.logger.info(f"Multiprocessing pool completed processing {len(all_results)} jobs")
                
        except Exception as e:
            self.logger.error(f"Multiprocessing pool execution failed: {e}")
            raise
        
        return all_results
    
    def _update_database_with_results(self, processed_results: List[Dict[str, Any]]) -> None:
        """
        Update database with processed job results.
        
        Args:
            processed_results: List of processed job dictionaries
        """
        self.logger.info(f"Updating database with {len(processed_results)} processed jobs")
        
        successful_updates, failed_updates = update_jobs_in_database(processed_results, self.profile_name)
        
        self.stats.processed_jobs = successful_updates
        self.stats.failed_jobs = failed_updates
        
        self.logger.info(f"Database update completed: {successful_updates} successful, {failed_updates} failed")
    
    def _calculate_final_stats(self, start_time: float) -> None:
        """
        Calculate final processing statistics.
        
        Args:
            start_time: Processing start time
        """
        self.stats.processing_time = time.time() - start_time
        
        if self.stats.processed_jobs > 0:
            self.stats.average_job_time = self.stats.processing_time / self.stats.processed_jobs
            self.stats.jobs_per_second = self.stats.processed_jobs / self.stats.processing_time
        
        self.logger.info(f"Processing statistics: {self.stats.processing_time:.2f}s total, "
                        f"{self.stats.average_job_time:.2f}s per job, "
                        f"{self.stats.jobs_per_second:.2f} jobs/sec")
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        Get current processing status and statistics.
        
        Returns:
            Dictionary with processing status and metrics
        """
        return {
            "status": self.stats.status.value,
            "total_jobs": self.stats.total_jobs,
            "processed_jobs": self.stats.processed_jobs,
            "failed_jobs": self.stats.failed_jobs,
            "processing_time": self.stats.processing_time,
            "average_job_time": self.stats.average_job_time,
            "jobs_per_second": self.stats.jobs_per_second,
            "worker_count": self.stats.worker_count,
            "batch_size": self.stats.batch_size,
            "profile_name": self.profile_name
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health information for monitoring.
        
        Returns:
            Dictionary with system health metrics
        """
        health_info = {
            "processor_status": self.stats.status.value,
            "profile_name": self.profile_name,
            "worker_count": self.worker_count,
            "batch_size": self.batch_size,
            "database_available": False,
            "ollama_available": False,
            "multiprocessing_support": True,
            "jobs_pending": 0
        }
        
        # Check database health
        try:
            db_stats = self.db.get_job_stats()
            health_info["database_available"] = True
            health_info["jobs_pending"] = db_stats.get("scraped", 0)
        except Exception as e:
            self.logger.warning(f"Database health check failed: {e}")
        
        # Check Ollama health
        try:
            ollama_client = get_gpu_ollama_client()
            health_info["ollama_available"] = ollama_client.is_available()
            health_info["ollama_health"] = ollama_client.get_health_info()
        except Exception as e:
            self.logger.warning(f"Ollama health check failed: {e}")
        
        return health_info
    
    def stop_processing(self) -> bool:
        """
        Stop current processing (if running).
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if self.stats.status == ProcessingStatus.RUNNING:
            self.logger.info("Stopping job processing...")
            self.stats.status = ProcessingStatus.STOPPED
            return True
        else:
            self.logger.info("No processing currently running")
            return False
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self.stats = ProcessingStats(worker_count=self.worker_count, batch_size=self.batch_size)
        self.logger.info("Processing statistics reset")
    
    def update_configuration(self, worker_count: Optional[int] = None, batch_size: Optional[int] = None) -> None:
        """
        Update processor configuration.
        
        Args:
            worker_count: New worker count (if provided)
            batch_size: New batch size (if provided)
        """
        if worker_count is not None:
            self.worker_count = worker_count
            self.stats.worker_count = worker_count
            self.logger.info(f"Updated worker count to {worker_count}")
        
        if batch_size is not None:
            self.batch_size = batch_size
            self.stats.batch_size = batch_size
            self.logger.info(f"Updated batch size to {batch_size}")


# Convenience functions for integration
def get_enhanced_job_processor(profile_name: str, **kwargs) -> EnhancedJobProcessor:
    """
    Get a configured enhanced job processor instance.
    
    Args:
        profile_name: Profile name for processing
        **kwargs: Additional configuration options
        
    Returns:
        Configured EnhancedJobProcessor instance
    """
    return EnhancedJobProcessor(profile_name, **kwargs)

def process_jobs_for_profile(profile_name: str, limit: Optional[int] = None) -> ProcessingStats:
    """
    Convenience function to process jobs for a specific profile.
    
    Args:
        profile_name: Profile name for processing
        limit: Maximum number of jobs to process
        
    Returns:
        ProcessingStats with results
    """
    processor = EnhancedJobProcessor(profile_name)
    return processor.process_jobs_parallel(limit=limit)

# CLI integration function
def main():
    """Main function for CLI execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Job Processor")
    parser.add_argument("--profile", required=True, help="Profile name for processing")
    parser.add_argument("--limit", type=int, help="Maximum number of jobs to process")
    parser.add_argument("--workers", type=int, default=2, help="Number of worker processes")
    parser.add_argument("--batch-size", type=int, default=5, help="Jobs per batch")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create and run processor
        processor = EnhancedJobProcessor(
            profile_name=args.profile,
            worker_count=args.workers,
            batch_size=args.batch_size
        )
        
        print(f"🚀 Starting enhanced job processing for profile '{args.profile}'")
        print(f"⚙️ Configuration: {args.workers} workers, batch size {args.batch_size}")
        
        # Process jobs
        stats = processor.process_jobs_parallel(limit=args.limit)
        
        # Display results
        print(f"\n📊 Processing Results:")
        print(f"✅ Total jobs: {stats.total_jobs}")
        print(f"✅ Processed: {stats.processed_jobs}")
        print(f"❌ Failed: {stats.failed_jobs}")
        print(f"⏱️ Processing time: {stats.processing_time:.2f}s")
        print(f"📈 Average time per job: {stats.average_job_time:.2f}s")
        print(f"🚀 Jobs per second: {stats.jobs_per_second:.2f}")
        
        if stats.status == ProcessingStatus.COMPLETED:
            print(f"\n🎉 Processing completed successfully!")
        else:
            print(f"\n⚠️ Processing ended with status: {stats.status.value}")
            
    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()