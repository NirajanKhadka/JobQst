"""
Document Generator Module for AutoJobAgent.

This module provides functionality to generate and customize documents
like resumes and cover letters based on job requirements.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Fix import path to use correct module structure
from src.core.job_database import ModernJobDatabase

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """Generates and customizes documents for job applications."""
    
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.db = ModernJobDatabase(profile_name=profile_name)
        self.profile_dir = Path(f"profiles/{profile_name}")
        self.profile_dir.mkdir(parents=True, exist_ok=True)
    
    def customize_documents(self, job_data: Dict) -> Dict:
        """
        Customize documents for a specific job.
        
        Args:
            job_data: Job information to customize documents for
            
        Returns:
            Dictionary with customized document paths
        """
        try:
            company_name = job_data.get('company', 'Unknown Company')
            job_title = job_data.get('title', 'Unknown Position')
            
            # Customize resume
            resume_path = self._customize_resume(company_name, job_title)
            
            # Customize cover letter
            cover_letter_path = self._customize_cover_letter(company_name, job_title)
            
            return {
                'resume': resume_path,
                'cover_letter': cover_letter_path,
                'company': company_name,
                'job_title': job_title
            }
            
        except Exception as e:
            logger.error(f"Error customizing documents: {e}")
            return {}
    
    def _customize_resume(self, company_name: str, job_title: str) -> str:
        """Customize resume for specific company and job."""
        try:
            # Create customized resume content
            resume_content = {
                'profile_name': self.profile_name,
                'target_company': company_name,
                'target_position': job_title,
                'customization_date': str(Path().cwd()),
                'content': f"Customized resume for {job_title} position at {company_name}"
            }
            
            # Save to file
            resume_file = self.profile_dir / "customized_resume.json"
            with open(resume_file, 'w') as f:
                json.dump(resume_content, f, indent=2)
            
            logger.info(f"✅ Customized resume created: {resume_file}")
            return str(resume_file)
            
        except Exception as e:
            logger.error(f"Error generating resume: {e}")
            return ""
    
    def _customize_cover_letter(self, company_name: str, job_title: str) -> str:
        """Customize cover letter for specific company and job."""
        try:
            # Create customized cover letter content
            cover_letter_content = {
                'profile_name': self.profile_name,
                'target_company': company_name,
                'target_position': job_title,
                'customization_date': str(Path().cwd()),
                'content': f"Customized cover letter for {job_title} position at {company_name}"
            }
            
            # Save to file
            cover_letter_file = self.profile_dir / "customized_cover_letter.json"
            with open(cover_letter_file, 'w') as f:
                json.dump(cover_letter_content, f, indent=2)
            
            logger.info(f"✅ Customized cover letter created: {cover_letter_file}")
            return str(cover_letter_file)
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return ""

    def get_available_templates(self) -> list:
        """Return a list of available document templates (stub)."""
        return ["default_resume", "default_cover_letter"]

    def format_document(self, content: str, doc_type: str) -> str:
        """Format document content for the given type (stub)."""
        return f"[{doc_type.upper()}]\n{content}"

    def generate_cover_letter(self, job, profile):
        """Generate a cover letter for the given job and profile (stub)."""
        company = job.get('company', 'Company')
        title = job.get('title', 'Job Title')
        profile_name = profile.get('name', 'Profile') if isinstance(profile, dict) else str(profile)
        return f"Cover letter for {title} at {company} for profile {profile_name}"

    def use_custom_template(self, template: str, context: dict) -> str:
        """Apply a custom template with context (stub)."""
        return template.format(**context)

    def generate_resume(self, job, profile):
        """Generate a resume for the given job and profile (stub)."""
        company = job.get('company', 'Company')
        title = job.get('title', 'Job Title')
        profile_name = profile.get('name', 'Profile') if isinstance(profile, dict) else str(profile)
        return f"Resume for {title} at {company} for profile {profile_name}"


# Convenience function
def customize(job_data: Dict, profile_name: str = "default") -> Dict:
    """
    Convenience function to customize documents for a job.
    
    Args:
        job_data: Job information
        profile_name: Profile name
        
    Returns:
        Dictionary with customized document paths
    """
    generator = DocumentGenerator(profile_name)
    return generator.customize_documents(job_data)
