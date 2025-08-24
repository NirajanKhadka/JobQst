#!/usr/bin/env python3
"""
Enhanced Job Processing Pipeline with Real-Time Status Updates
Integrates with the RealTimeJobStatusManager for live dashboard updates
Follows DEVELOPMENT_STANDARDS.md guidelines
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

# Setup logging per standards
logger = logging.getLogger(__name__)


class EnhancedJobProcessor:
    """
    Enhanced job processor with real-time status tracking.
    
    Design Principles:
    - Single responsibility: Process jobs with status updates
    - Thread-safe operations using async/await
    - Real-time status updates for dashboard
    - Error handling with graceful degradation
    """
    
    def __init__(self, profile_name: str, max_workers: int = 3):
        """
        Initialize enhanced job processor.
        
        Args:
            profile_name: Profile identifier
            max_workers: Maximum concurrent workers (per standards)
        """
        self.profile_name = profile_name
        self.max_workers = max_workers
        self.active_workers = 0
        self.processed_count = 0
        self.total_jobs = 0
        self.start_time: Optional[datetime] = None
        
        # Initialize status manager
        try:
            from src.core.realtime_job_status import get_status_manager
            self.status_manager = get_status_manager()
            logger.info(f"✅ Enhanced processor initialized for {profile_name}")
        except ImportError:
            self.status_manager = None
            logger.warning("Real-time status manager not available")
    
    async def process_jobs_batch(
        self, 
        job_ids: List[str], 
        processing_method: str = "two_stage"
    ) -> Dict[str, Any]:
        """
        Process a batch of jobs with real-time status updates.
        
        Args:
            job_ids: List of job IDs to process
            processing_method: Processing method to use
            
        Returns:
            Processing results summary
        """
        self.total_jobs = len(job_ids)
        self.processed_count = 0
        self.start_time = datetime.now()
        
        logger.info(f"🚀 Starting batch processing: {self.total_jobs} jobs")
        
        # Update initial status
        if self.status_manager:
            self.status_manager.update_processing_status(
                self.profile_name,
                is_processing=True,
                current_job_title=f"Processing {self.total_jobs} jobs...",
                progress_percentage=0,
                active_workers=0
            )
        
        try:
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.max_workers)
            
            # Create processing tasks
            tasks = [
                self._process_single_job(job_id, semaphore, processing_method)
                for job_id in job_ids
            ]
            
            # Process all jobs concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Calculate final statistics
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            failed = len(results) - successful
            
            processing_time = (datetime.now() - self.start_time).total_seconds()
            jobs_per_minute = (successful / processing_time) * 60 if processing_time > 0 else 0
            
            summary = {
                "total_jobs": self.total_jobs,
                "successful": successful,
                "failed": failed,
                "processing_time": processing_time,
                "jobs_per_minute": jobs_per_minute,
                "method": processing_method
            }
            
            logger.info(f"✅ Batch processing completed: {successful}/{self.total_jobs} successful")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
            return {
                "total_jobs": self.total_jobs,
                "successful": 0,
                "failed": self.total_jobs,
                "error": str(e),
                "method": processing_method
            }
        
        finally:
            # Update final status
            if self.status_manager:
                self.status_manager.update_processing_status(
                    self.profile_name,
                    is_processing=False,
                    current_job_title="",
                    progress_percentage=100,
                    active_workers=0
                )
    
    async def _process_single_job(
        self, 
        job_id: str, 
        semaphore: asyncio.Semaphore,
        processing_method: str
    ) -> Dict[str, Any]:
        """
        Process a single job with status tracking.
        
        Args:
            job_id: Job identifier
            semaphore: Concurrency control semaphore
            processing_method: Processing method to use
            
        Returns:
            Processing result for this job
        """
        async with semaphore:
            self.active_workers += 1
            start_time = time.time()
            
            try:
                # Get job details for status display
                job_title = await self._get_job_title(job_id)
                
                # Update status with current job
                if self.status_manager:
                    progress = int((self.processed_count / self.total_jobs) * 100)
                    self.status_manager.update_processing_status(
                        self.profile_name,
                        is_processing=True,
                        current_job_title=job_title,
                        progress_percentage=progress,
                        active_workers=self.active_workers
                    )
                
                # Simulate job processing (replace with actual processing logic)
                result = await self._perform_job_analysis(job_id, processing_method)
                
                # Mark job as processed
                if self.status_manager and result.get("success"):
                    self.status_manager.mark_job_processed(
                        self.profile_name, 
                        job_id, 
                        job_title
                    )
                
                self.processed_count += 1
                processing_time = time.time() - start_time
                
                logger.debug(f"✅ Processed job {job_id} in {processing_time:.2f}s")
                
                return {
                    "job_id": job_id,
                    "success": result.get("success", False),
                    "processing_time": processing_time,
                    "method": processing_method
                }
                
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"❌ Failed to process job {job_id}: {e}")
                
                return {
                    "job_id": job_id,
                    "success": False,
                    "error": str(e),
                    "processing_time": processing_time,
                    "method": processing_method
                }
            
            finally:
                self.active_workers -= 1
    
    async def _get_job_title(self, job_id: str) -> str:
        """Get job title for status display."""
        try:
            from src.core.job_database import get_job_db
            
            db = get_job_db(self.profile_name)
            jobs = db.get_jobs(limit=1000)  # Get reasonable batch
            
            for job in jobs:
                if str(job.get("id")) == str(job_id):
                    title = job.get("title", "Unknown Job")
                    return title[:50] + "..." if len(title) > 50 else title
            
            return f"Job #{job_id}"
            
        except Exception as e:
            logger.warning(f"Failed to get job title for {job_id}: {e}")
            return f"Job #{job_id}"
    
    async def _perform_job_analysis(self, job_id: str, method: str) -> Dict[str, Any]:
        """
        Perform actual job analysis (placeholder for actual processing).
        
        Args:
            job_id: Job identifier
            method: Processing method
            
        Returns:
            Analysis result
        """
        # Simulate processing time based on method
        if method == "two_stage":
            await asyncio.sleep(0.5)  # Faster processing
        elif method == "cpu_only":
            await asyncio.sleep(1.0)  # Slower processing
        else:
            await asyncio.sleep(0.3)  # Auto-detect (fast)
        
        # TODO: Replace with actual job processing logic
        # This should integrate with your existing analysis pipeline
        
        try:
            from src.core.job_database import get_job_db
            
            db = get_job_db(self.profile_name)
            
            # Simulate successful processing
            # In real implementation, this would call your analysis functions
            update_data = {
                "status": "processed",
                "processed_at": datetime.now().isoformat(),
                "processing_method": method,
                "match_score": 75.0,  # Placeholder score
                "analysis_data": '{"processed": true, "method": "' + method + '"}'
            }
            
            # Update job in database
            db.update_job(job_id, update_data)
            
            return {
                "success": True,
                "method": method,
                "match_score": 75.0
            }
            
        except Exception as e:
            logger.error(f"Job analysis failed for {job_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": method
            }


class JobProcessingOrchestrator:
    """
    Orchestrates job processing across multiple profiles and methods.
    
    Follows the Application Orchestration Standards from DEVELOPMENT_STANDARDS.md
    """
    
    def __init__(self):
        """Initialize the processing orchestrator."""
        self.active_processors: Dict[str, EnhancedJobProcessor] = {}
        self.processing_queue: List[Dict[str, Any]] = []
        
        logger.info("✅ Job Processing Orchestrator initialized")
    
    async def start_processing(
        self, 
        profile_name: str, 
        job_limit: int = 50,
        processing_method: str = "two_stage"
    ) -> Dict[str, Any]:
        """
        Start processing jobs for a profile.
        
        Args:
            profile_name: Profile identifier
            job_limit: Maximum jobs to process
            processing_method: Processing method to use
            
        Returns:
            Processing summary
        """
        try:
            # Get jobs that need processing
            from src.core.job_database import get_job_db
            
            db = get_job_db(profile_name)
            all_jobs = db.get_jobs(limit=job_limit * 2)  # Get more to filter
            
            # Filter for unprocessed jobs
            unprocessed_jobs = [
                job for job in all_jobs
                if job.get("status", "").lower() in ["scraped", "new"] and
                job.get("application_status", "").lower() == "not_applied"
            ][:job_limit]
            
            if not unprocessed_jobs:
                logger.info(f"No unprocessed jobs found for {profile_name}")
                return {"message": "No jobs to process", "profile": profile_name}
            
            # Create processor
            processor = EnhancedJobProcessor(profile_name)
            self.active_processors[profile_name] = processor
            
            # Extract job IDs
            job_ids = [str(job.get("id")) for job in unprocessed_jobs]
            
            logger.info(f"🚀 Starting processing for {profile_name}: {len(job_ids)} jobs")
            
            # Process jobs
            results = await processor.process_jobs_batch(job_ids, processing_method)
            
            # Clean up processor
            self.active_processors.pop(profile_name, None)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Processing failed for {profile_name}: {e}")
            self.active_processors.pop(profile_name, None)
            return {"error": str(e), "profile": profile_name}
    
    def get_processing_status(self, profile_name: str) -> Dict[str, Any]:
        """Get current processing status for a profile."""
        processor = self.active_processors.get(profile_name)
        if processor:
            return {
                "is_processing": True,
                "total_jobs": processor.total_jobs,
                "processed_count": processor.processed_count,
                "active_workers": processor.active_workers,
                "start_time": processor.start_time.isoformat() if processor.start_time else None
            }
        return {"is_processing": False}
    
    def stop_processing(self, profile_name: str) -> bool:
        """Stop processing for a profile."""
        if profile_name in self.active_processors:
            # TODO: Implement graceful shutdown
            self.active_processors.pop(profile_name, None)
            logger.info(f"⏹️ Stopped processing for {profile_name}")
            return True
        return False


# Global orchestrator instance
_orchestrator: Optional[JobProcessingOrchestrator] = None


def get_job_processing_orchestrator() -> JobProcessingOrchestrator:
    """Get the global job processing orchestrator (singleton pattern)."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = JobProcessingOrchestrator()
    return _orchestrator


async def process_jobs_for_profile(
    profile_name: str, 
    job_limit: int = 50,
    processing_method: str = "two_stage"
) -> Dict[str, Any]:
    """
    Convenience function to process jobs for a profile.
    
    Args:
        profile_name: Profile identifier
        job_limit: Maximum jobs to process
        processing_method: Processing method to use
        
    Returns:
        Processing results summary
    """
    orchestrator = get_job_processing_orchestrator()
    return await orchestrator.start_processing(profile_name, job_limit, processing_method)
