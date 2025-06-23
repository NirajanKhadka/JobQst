#!/usr/bin/env python3
"""
Modern Utils - Simple, robust, and easy to debug
Enhanced with better error handling and modern Python patterns.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import hashlib
import shutil
from dataclasses import dataclass, asdict

# Import from new modular structure
from .job_data import JobData
from .text_utils import clean_text, extract_keywords, analyze_text
from .job_filters import JobFilter, FilterCriteria, filter_jobs_by_priority, filter_duplicate_jobs
from .session import SessionManager, RateLimiter, BrowserSession
from .browser_utils import BrowserUtils, TabManager, PopupHandler
from .exceptions import AutoJobAgentError, ScrapingError, DatabaseError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModernUtils:
    """
    Modern utilities with simple, robust operations.
    Enhanced error handling and easy debugging.
    """
    
    def __init__(self):
        self.output_dir = Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Modern utils initialized")
    
    def save_jobs_to_json(self, jobs: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save jobs to JSON file.
        Returns the file path.
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"jobs_{timestamp}.json"
            
            file_path = self.output_dir / filename
            
            # Ensure jobs are serializable
            serializable_jobs = []
            for job in jobs:
                if isinstance(job, JobData):
                    serializable_jobs.append(job.to_dict())
                else:
                    serializable_jobs.append(job)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_jobs, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved {len(jobs)} jobs to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to save jobs to JSON: {e}")
            return ""
    
    def load_jobs_from_json(self, file_path: str) -> List[Dict]:
        """Load jobs from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            
            logger.info(f"✅ Loaded {len(jobs)} jobs from {file_path}")
            return jobs
            
        except Exception as e:
            logger.error(f"❌ Failed to load jobs from JSON: {e}")
            return []
    
    def save_jobs_to_csv(self, jobs: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save jobs to CSV file.
        Returns the file path.
        """
        try:
            import csv
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"jobs_{timestamp}.csv"
            
            file_path = self.output_dir / filename
            
            if not jobs:
                logger.warning("⚠️ No jobs to save")
                return ""
            
            # Get all field names
            fieldnames = set()
            for job in jobs:
                if isinstance(job, JobData):
                    fieldnames.update(job.to_dict().keys())
                else:
                    fieldnames.update(job.keys())
            
            fieldnames = sorted(list(fieldnames))
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for job in jobs:
                    if isinstance(job, JobData):
                        row = job.to_dict()
                    else:
                        row = job.copy()
                    
                    # Convert lists to strings
                    for key, value in row.items():
                        if isinstance(value, list):
                            row[key] = ", ".join(str(v) for v in value)
                    
                    writer.writerow(row)
            
            logger.info(f"✅ Saved {len(jobs)} jobs to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to save jobs to CSV: {e}")
            return ""
    
    def extract_company_from_url(self, url: str) -> str:
        """Extract company name from URL."""
        try:
            from urllib.parse import urlparse
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            domain = re.sub(r'^www\.', '', domain)
            domain = re.sub(r'^careers\.', '', domain)
            domain = re.sub(r'^jobs\.', '', domain)
            
            # Extract company name
            company = domain.split('.')[0]
            
            # Clean up
            company = re.sub(r'[^\w]', '', company)
            company = company.title()
            
            return company if company else "Unknown"
            
        except Exception as e:
            logger.error(f"❌ Failed to extract company from URL: {e}")
            return "Unknown"
    
    def normalize_location(self, location: str) -> str:
        """Normalize location string."""
        if not location:
            return ""
        
        # Convert to title case
        location = location.title()
        
        # Remove extra whitespace
        location = re.sub(r'\s+', ' ', location).strip()
        
        return location
    
    def generate_job_hash(self, job: Dict) -> str:
        """Generate hash for job duplicate detection."""
        try:
            # Create a consistent string for hashing
            content = f"{job.get('title', '').lower()}{job.get('company', '').lower()}{job.get('url', '')}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception as e:
            logger.error(f"❌ Failed to generate job hash: {e}")
            return ""
    
    def is_duplicate_job(self, job1: Dict, job2: Dict) -> bool:
        """Check if two jobs are duplicates."""
        try:
            # Check exact matches first
            if (job1.get('title') == job2.get('title') and 
                job1.get('company') == job2.get('company')):
                return True
            
            # Check URL similarity
            url1 = job1.get('url', '')
            url2 = job2.get('url', '')
            if url1 and url2 and url1 == url2:
                return True
            
            # Check title similarity
            title1 = job1.get('title', '')
            title2 = job2.get('title', '')
            if self._similar_titles(title1, title2):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to check job duplicates: {e}")
            return False
    
    def _similar_titles(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two titles are similar using simple string comparison."""
        if not title1 or not title2:
            return False
        
        # Convert to lowercase and clean
        t1 = re.sub(r'[^\w\s]', '', title1.lower())
        t2 = re.sub(r'[^\w\s]', '', title2.lower())
        
        # Simple similarity check
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def sort_jobs(self, jobs: List[Dict], sort_by: str = "scraped_at", reverse: bool = True) -> List[Dict]:
        """Sort jobs by specified field."""
        try:
            return sorted(jobs, key=lambda x: x.get(sort_by, ""), reverse=reverse)
        except Exception as e:
            logger.error(f"❌ Failed to sort jobs: {e}")
            return jobs
    
    def get_job_stats(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Get statistics about jobs."""
        try:
            if not jobs:
                return {
                    'total_jobs': 0,
                    'unique_companies': 0,
                    'locations': {},
                    'job_types': {},
                    'date_range': None
                }
            
            companies = set()
            locations = {}
            job_types = {}
            dates = []
            
            for job in jobs:
                # Companies
                company = job.get('company', 'Unknown')
                companies.add(company)
                
                # Locations
                location = job.get('location', 'Unknown')
                locations[location] = locations.get(location, 0) + 1
                
                # Job types
                job_type = job.get('job_type', 'Unknown')
                job_types[job_type] = job_types.get(job_type, 0) + 1
                
                # Dates
                scraped_at = job.get('scraped_at', '')
                if scraped_at:
                    try:
                        date_obj = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                        dates.append(date_obj)
                    except:
                        pass
            
            return {
                'total_jobs': len(jobs),
                'unique_companies': len(companies),
                'locations': locations,
                'job_types': job_types,
                'date_range': {
                    'earliest': min(dates).isoformat() if dates else None,
                    'latest': max(dates).isoformat() if dates else None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get job stats: {e}")
            return {}
    
    def backup_file(self, file_path: str, backup_dir: str = "backups") -> bool:
        """Create a backup of a file."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                logger.warning(f"⚠️ Source file does not exist: {file_path}")
                return False
            
            # Create backup directory
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_file_path = backup_path / backup_filename
            
            # Copy file
            shutil.copy2(source_path, backup_file_path)
            
            logger.info(f"✅ Created backup: {backup_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def create_output_directory(self, name: str) -> Path:
        """Create an output directory with the given name."""
        try:
            output_path = Path("output") / name
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created output directory: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"❌ Failed to create output directory: {e}")
            return Path("output")

# Global utils instance
_utils_instance = None

def get_utils() -> ModernUtils:
    """Get global utils instance."""
    global _utils_instance
    if _utils_instance is None:
        _utils_instance = ModernUtils()
    return _utils_instance

# Global convenience functions
def save_jobs_to_json(jobs: List[Dict], filename: Optional[str] = None) -> str:
    """Save jobs to JSON file."""
    return get_utils().save_jobs_to_json(jobs, filename)

def load_jobs_from_json(file_path: str) -> List[Dict]:
    """Load jobs from JSON file."""
    return get_utils().load_jobs_from_json(file_path)

def save_jobs_to_csv(jobs: List[Dict], filename: Optional[str] = None) -> str:
    """Save jobs to CSV file."""
    return get_utils().save_jobs_to_csv(jobs, filename)

def extract_company_from_url(url: str) -> str:
    """Extract company name from URL."""
    return get_utils().extract_company_from_url(url)

def normalize_location(location: str) -> str:
    """Normalize location string."""
    return get_utils().normalize_location(location)

def generate_job_hash(job: Dict) -> str:
    """Generate hash for a job."""
    return get_utils().generate_job_hash(job)

def is_duplicate_job(job1: Dict, job2: Dict) -> bool:
    """Check if two jobs are duplicates."""
    return get_utils().is_duplicate_job(job1, job2)

def sort_jobs(jobs: List[Dict], sort_by: str = "scraped_at", reverse: bool = True) -> List[Dict]:
    """Sort jobs by specified field."""
    return get_utils().sort_jobs(jobs, sort_by, reverse)

def get_job_stats(jobs: List[Dict]) -> Dict[str, Any]:
    """Get statistics about jobs."""
    return get_utils().get_job_stats(jobs)

def get_available_profiles() -> List[str]:
    """Get list of available profile names."""
    try:
        profiles_dir = Path("profiles")
        if not profiles_dir.exists():
            return []
        
        profiles = []
        for item in profiles_dir.iterdir():
            if item.is_dir() and (item / f"{item.name}.json").exists():
                profiles.append(item.name)
        
        return sorted(profiles)
    except Exception as e:
        logger.error(f"❌ Failed to get available profiles: {e}")
        return []

def load_profile(profile_name: str) -> Dict:
    """Load profile configuration."""
    try:
        profile_file = Path(f"profiles/{profile_name}/{profile_name}.json")
        if not profile_file.exists():
            raise FileNotFoundError(f"Profile file not found: {profile_file}")
        
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        # Add profile_name field to the profile data
        profile['profile_name'] = profile_name
        
        logger.info(f"✅ Loaded profile: {profile_name}")
        return profile
        
    except Exception as e:
        logger.error(f"❌ Failed to load profile '{profile_name}': {e}")
        return {}

def convert_doc_to_pdf(docx_path: str, pdf_path: str) -> bool:
    """Convert DOCX to PDF using Word COM."""
    try:
        import win32com.client
        import os
        
        if not os.path.exists(docx_path):
            logger.error(f"❌ DOCX file not found: {docx_path}")
            return False
        
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        
        doc = word.Documents.Open(os.path.abspath(docx_path))
        doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)  # 17 = PDF
        doc.Close()
        word.Quit()
        
        logger.info(f"✅ Converted {docx_path} to {pdf_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to convert DOCX to PDF: {e}")
        return False

def create_temp_file(content: str, extension: str = ".txt") -> str:
    """Create a temporary file with content."""
    try:
        import tempfile
        import uuid
        
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        
        filename = f"temp_{uuid.uuid4().hex[:8]}{extension}"
        filepath = temp_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
        
    except Exception as e:
        logger.error(f"❌ Failed to create temp file: {e}")
        return ""

def get_browser_user_data_dir(profile_name: str, browser: str = "chrome") -> str:
    """Get browser user data directory for a profile."""
    try:
        profile_dir = Path(f"profiles/{profile_name}/{browser}_data")
        profile_dir.mkdir(parents=True, exist_ok=True)
        return str(profile_dir)
    except Exception as e:
        logger.error(f"❌ Failed to get browser data dir: {e}")
        return ""

# Pause signal handling
_pause_signal = False

def check_pause_signal() -> bool:
    """Check if pause signal is set."""
    return _pause_signal

def set_pause_signal(value: bool) -> None:
    """Set pause signal."""
    global _pause_signal
    _pause_signal = value

class NeedsHumanException(Exception):
    """Exception raised when human intervention is needed."""
    pass

def ensure_profile_files(profile: Dict) -> bool:
    """
    Ensure all required profile files exist and are in the correct format.
    May generate PDFs from DOCX files if needed.
    
    Args:
        profile: User profile dictionary
        
    Returns:
        True if all files are ready, False otherwise
    """
    try:
        # Get profile name - use profile_name field or infer from profile data
        profile_name = profile.get('profile_name')
        if not profile_name:
            # Try to infer from name field or other identifiers
            if 'name' in profile:
                # Extract first name from full name
                profile_name = profile['name'].split()[0]
            else:
                # Fallback to 'Unknown' but this should be rare
                profile_name = 'Unknown'
        
        profile_dir = Path(f"profiles/{profile_name}")
        
        if not profile_dir.exists():
            logger.error(f"❌ Profile directory not found: {profile_dir}")
            logger.error(f"💡 Profile data: {profile}")
            return False
        
        # Check for required files
        required_files = {
            'resume': [
                f"{profile_name}_Resume.pdf",
                f"{profile_name}_Resume.docx",
                "resume.pdf",
                "resume.docx"
            ],
            'cover_letter': [
                f"{profile_name}_CoverLetter.pdf", 
                f"{profile_name}_CoverLetter.docx",
                "cover_letter.pdf",
                "cover_letter.docx"
            ]
        }
        
        files_found = {}
        
        # Check for existing files
        for file_type, possible_names in required_files.items():
            for filename in possible_names:
                file_path = profile_dir / filename
                if file_path.exists():
                    files_found[file_type] = str(file_path)
                    logger.info(f"✅ Found {file_type}: {file_path}")
                    break
        
        # Generate PDFs from DOCX if needed
        for file_type, file_path in files_found.items():
            if file_path.endswith('.docx'):
                pdf_path = file_path.replace('.docx', '.pdf')
                if not Path(pdf_path).exists():
                    logger.info(f"🔄 Converting {file_type} to PDF...")
                    if convert_doc_to_pdf(file_path, pdf_path):
                        files_found[file_type] = pdf_path
                        logger.info(f"✅ Generated PDF: {pdf_path}")
                    else:
                        logger.warning(f"⚠️ Failed to convert {file_type} to PDF")
        
        # Check if we have at least a resume
        if 'resume' not in files_found:
            logger.error(f"❌ No resume file found in {profile_dir}")
            logger.info(f"💡 Please add a resume file to {profile_dir}")
            return False
        
        logger.info(f"✅ Profile files ready for {profile_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ensuring profile files: {e}")
        return False

def save_customized_document(profile: Dict, job_hash: str, temp_docx: str, is_resume: bool = True) -> str:
    """
    Save a customized document to the appropriate location.
    
    Args:
        profile: User profile dictionary
        job_hash: Hash of the job for naming
        temp_docx: Path to temporary DOCX file
        is_resume: True if this is a resume, False if cover letter
        
    Returns:
        Path to the saved document
    """
    try:
        profile_name = profile.get('profile_name', 'default')
        doc_type = 'resume' if is_resume else 'cover_letter'
        
        # Create output directory
        output_dir = Path(f"output/{profile_name}/{doc_type}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{profile_name}_{doc_type}_{job_hash[:8]}_{timestamp}.docx"
        output_path = output_dir / filename
        
        # Copy the temporary file to the output location
        import shutil
        shutil.copy2(temp_docx, output_path)
        
        logger.info(f"✅ Saved {doc_type}: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"❌ Failed to save {doc_type}: {e}")
        return temp_docx  # Return original path as fallback
