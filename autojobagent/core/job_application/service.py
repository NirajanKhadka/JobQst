"""
Job application service for managing the job application pipeline.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from ...shared.config import settings
from ..models import JobPosting, JobApplication, UserProfile, Resume, CoverLetter, JobStatus

logger = logging.getLogger(__name__)

class JobApplicationService:
    """Service for managing job applications."""
    
    def __init__(self, profile: UserProfile):
        """Initialize with user profile."""
        self.profile = profile
        self.applications: Dict[str, JobApplication] = {}
        
    def create_application(self, job: JobPosting, resume_path: str, 
                          cover_letter_path: Optional[str] = None) -> JobApplication:
        """
        Create a new job application.
        
        Args:
            job: The job posting to apply for
            resume_path: Path to the resume file
            cover_letter_path: Optional path to the cover letter file
            
        Returns:
            The created job application
        """
        resume = Resume(file_path=Path(resume_path))
        
        cover_letter = None
        if cover_letter_path:
            cover_letter = CoverLetter(file_path=Path(cover_letter_path))
        
        application = JobApplication(
            job=job,
            resume=resume,
            cover_letter=cover_letter
        )
        
        self.applications[job.id] = application
        return application
    
    def update_application_status(self, job_id: str, status: JobStatus, notes: Optional[str] = None) -> bool:
        """
        Update the status of a job application.
        
        Args:
            job_id: ID of the job application
            status: New status
            notes: Optional notes about the update
            
        Returns:
            True if the update was successful, False otherwise
        """
        if job_id not in self.applications:
            logger.warning(f"Job application {job_id} not found")
            return False
            
        application = self.applications[job_id]
        application.status = status
        
        if status == JobStatus.APPLIED and not application.applied_at:
            from datetime import datetime
            application.applied_at = datetime.utcnow()
            
        if notes:
            application.notes = notes
            
        return True
    
    def get_application(self, job_id: str) -> Optional[JobApplication]:
        """
        Get a job application by ID.
        
        Args:
            job_id: ID of the job application
            
        Returns:
            The job application or None if not found
        """
        return self.applications.get(job_id)
    
    def list_applications(self, status: Optional[JobStatus] = None) -> List[JobApplication]:
        """
        List all job applications, optionally filtered by status.
        
        Args:
            status: Optional status to filter by
            
        Returns:
            List of job applications
        """
        if status is None:
            return list(self.applications.values())
        return [app for app in self.applications.values() if app.status == status]
    
    def delete_application(self, job_id: str) -> bool:
        """
        Delete a job application.
        
        Args:
            job_id: ID of the job application to delete
            
        Returns:
            True if the application was deleted, False otherwise
        """
        if job_id in self.applications:
            del self.applications[job_id]
            return True
        return False
