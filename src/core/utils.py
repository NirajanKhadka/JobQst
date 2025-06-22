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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobData:
    """Simple job data structure."""
    title: str
    company: str
    location: str = ""
    url: str = ""
    summary: str = ""
    salary: str = ""
    job_type: str = ""
    posted_date: str = ""
    site: str = ""
    search_keyword: str = ""
    scraped_at: str = ""
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_hash(self) -> str:
        """Generate hash for duplicate detection."""
        content = f"{self.title.lower()}{self.company.lower()}{self.url}"
        return hashlib.md5(content.encode()).hexdigest()

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
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text more gently."""
        if not isinstance(text, str):
            return ""
        
        # Replace non-breaking spaces and collapse all whitespace
        text = re.sub(r'\s+', ' ', text.replace('\xa0', ' ')).strip()
        
        return text
    
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
        
        # Standardize common abbreviations
        replacements = {
            'On': 'ON',
            'Bc': 'BC',
            'Ab': 'AB',
            'Qc': 'QC',
            'Ns': 'NS',
            'Nb': 'NB',
            'Pe': 'PE',
            'Nl': 'NL',
            'Sk': 'SK',
            'Mb': 'MB',
            'Yt': 'YT',
            'Nt': 'NT',
            'Nu': 'NU'
        }
        
        for old, new in replacements.items():
            location = location.replace(old, new)
        
        return location
    
    def generate_job_hash(self, job: Dict) -> str:
        """Generate unique hash for job."""
        try:
            # Use title, company, and URL for hash
            title = job.get('title', '').lower()
            company = job.get('company', '').lower()
            url = job.get('url', '')
            
            content = f"{title}{company}{url}"
            return hashlib.md5(content.encode()).hexdigest()[:12]
            
        except Exception as e:
            logger.error(f"❌ Failed to generate job hash: {e}")
            return ""
    
    def is_duplicate_job(self, job1: Dict, job2: Dict) -> bool:
        """Check if two jobs are duplicates."""
        try:
            # Method 1: Same URL
            if job1.get('url') and job2.get('url') and job1['url'] == job2['url']:
                return True
            
            # Method 2: Same title and company
            title1 = job1.get('title', '').lower()
            title2 = job2.get('title', '').lower()
            company1 = job1.get('company', '').lower()
            company2 = job2.get('company', '').lower()
            
            if title1 == title2 and company1 == company2:
                return True
            
            # Method 3: Similar title and same company (fuzzy match)
            if company1 == company2 and self._similar_titles(title1, title2):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to check duplicate: {e}")
            return False
    
    def _similar_titles(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two titles are similar using simple similarity."""
        if not title1 or not title2:
            return False
        
        # Simple word overlap similarity
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def filter_jobs(self, jobs: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Filter jobs based on criteria."""
        try:
            filtered_jobs = []
            
            for job in jobs:
                include_job = True
                
                # Filter by keyword in title or company
                if 'keyword' in filters:
                    keyword = filters['keyword'].lower()
                    title = job.get('title', '').lower()
                    company = job.get('company', '').lower()
                    
                    if keyword not in title and keyword not in company:
                        include_job = False
                
                # Filter by location
                if 'location' in filters and include_job:
                    location_filter = filters['location'].lower()
                    job_location = job.get('location', '').lower()
                    
                    if location_filter not in job_location:
                        include_job = False
                
                # Filter by company
                if 'company' in filters and include_job:
                    company_filter = filters['company'].lower()
                    job_company = job.get('company', '').lower()
                    
                    if company_filter not in job_company:
                        include_job = False
                
                # Filter by site
                if 'site' in filters and include_job:
                    site_filter = filters['site'].lower()
                    job_site = job.get('site', '').lower()
                    
                    if site_filter != job_site:
                        include_job = False
                
                if include_job:
                    filtered_jobs.append(job)
            
            logger.info(f"✅ Filtered {len(jobs)} jobs to {len(filtered_jobs)}")
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"❌ Failed to filter jobs: {e}")
            return jobs
    
    def sort_jobs(self, jobs: List[Dict], sort_by: str = "scraped_at", reverse: bool = True) -> List[Dict]:
        """Sort jobs by specified field."""
        try:
            if not jobs:
                return jobs
            
            # Define sort keys
            sort_keys = {
                'title': lambda x: x.get('title', '').lower(),
                'company': lambda x: x.get('company', '').lower(),
                'location': lambda x: x.get('location', '').lower(),
                'scraped_at': lambda x: x.get('scraped_at', ''),
                'posted_date': lambda x: x.get('posted_date', ''),
                'salary': lambda x: x.get('salary', '')
            }
            
            sort_key = sort_keys.get(sort_by, sort_keys['scraped_at'])
            
            sorted_jobs = sorted(jobs, key=sort_key, reverse=reverse)
            
            logger.info(f"✅ Sorted {len(jobs)} jobs by {sort_by}")
            return sorted_jobs
            
        except Exception as e:
            logger.error(f"❌ Failed to sort jobs: {e}")
            return jobs
    
    def get_job_stats(self, jobs: List[Dict]) -> Dict[str, Any]:
        """Get statistics about jobs."""
        try:
            if not jobs:
                return {'total_jobs': 0}
            
            stats = {
                'total_jobs': len(jobs),
                'unique_companies': len(set(j.get('company', '') for j in jobs if j.get('company'))),
                'unique_locations': len(set(j.get('location', '') for j in jobs if j.get('location'))),
                'sites': {},
                'recent_jobs': 0
            }
            
            # Count by site
            for job in jobs:
                site = job.get('site', 'unknown')
                stats['sites'][site] = stats['sites'].get(site, 0) + 1
            
            # Count recent jobs (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            for job in jobs:
                try:
                    scraped_at = datetime.fromisoformat(job.get('scraped_at', ''))
                    if scraped_at > yesterday:
                        stats['recent_jobs'] += 1
                except:
                    pass
            
            logger.info(f"✅ Generated stats for {len(jobs)} jobs")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to generate job stats: {e}")
            return {'total_jobs': 0}
    
    def backup_file(self, file_path: str, backup_dir: str = "backups") -> bool:
        """Create a backup of a file."""
        try:
            source = Path(file_path)
            if not source.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                return False
            
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{source.stem}_backup_{timestamp}{source.suffix}"
            backup_dest = backup_path / backup_name
            
            shutil.copy2(source, backup_dest)
            
            logger.info(f"✅ Created backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to backup file: {e}")
            return False
    
    def create_output_directory(self, name: str) -> Path:
        """Create and return output directory path."""
        try:
            output_path = self.output_dir / name
            output_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"✅ Created output directory: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create output directory: {e}")
            return self.output_dir
    
    def load_session(self, profile_name: str) -> Dict:
        """Load session data for a profile."""
        try:
            session_file = Path(f"profiles/{profile_name}/session.json")
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                logger.info(f"✅ Loaded session for profile: {profile_name}")
                return session_data
            else:
                logger.warning(f"⚠️ No session file found for profile: {profile_name}")
                return {}
        except Exception as e:
            logger.error(f"❌ Failed to load session for profile '{profile_name}': {e}")
            return {}
    
    def save_session(self, profile_name: str, session_data: Dict) -> bool:
        """Save session data for a profile."""
        try:
            session_file = Path(f"profiles/{profile_name}/session.json")
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved session for profile: {profile_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save session for profile '{profile_name}': {e}")
            return False
    
    def detect_available_browsers(self) -> Dict[str, str]:
        """Detect available browsers on the system."""
        try:
            browsers = {}
            
            # Check for Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser"
            ]
            
            for path in chrome_paths:
                if Path(path).exists():
                    browsers["chrome"] = path
                    break
            
            # Check for Firefox
            firefox_paths = [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                "/usr/bin/firefox"
            ]
            
            for path in firefox_paths:
                if Path(path).exists():
                    browsers["firefox"] = path
                    break
            
            # Check for Edge
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
            
            for path in edge_paths:
                if Path(path).exists():
                    browsers["edge"] = path
                    break
            
            logger.info(f"✅ Detected browsers: {list(browsers.keys())}")
            return browsers
            
        except Exception as e:
            logger.error(f"❌ Failed to detect browsers: {e}")
            return {"chrome": "default"}  # Default fallback

# Global utils instance
_utils = None

def get_utils() -> ModernUtils:
    """Get global utils instance."""
    global _utils
    
    if _utils is None:
        _utils = ModernUtils()
    
    return _utils

# Convenience functions for backward compatibility
def save_jobs_to_json(jobs: List[Dict], filename: Optional[str] = None) -> str:
    """Save jobs to JSON file."""
    return get_utils().save_jobs_to_json(jobs, filename)

def load_jobs_from_json(file_path: str) -> List[Dict]:
    """Load jobs from JSON file."""
    return get_utils().load_jobs_from_json(file_path)

def save_jobs_to_csv(jobs: List[Dict], filename: Optional[str] = None) -> str:
    """Save jobs to CSV file."""
    return get_utils().save_jobs_to_csv(jobs, filename)

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    return get_utils().clean_text(text)

def extract_company_from_url(url: str) -> str:
    """Extract company name from URL."""
    return get_utils().extract_company_from_url(url)

def normalize_location(location: str) -> str:
    """Normalize location string."""
    return get_utils().normalize_location(location)

def generate_job_hash(job: Dict) -> str:
    """Generate unique hash for job."""
    return get_utils().generate_job_hash(job)

def is_duplicate_job(job1: Dict, job2: Dict) -> bool:
    """Check if two jobs are duplicates."""
    return get_utils().is_duplicate_job(job1, job2)

def filter_jobs(jobs: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """Filter jobs based on criteria."""
    return get_utils().filter_jobs(jobs, filters)

def sort_jobs(jobs: List[Dict], sort_by: str = "scraped_at", reverse: bool = True) -> List[Dict]:
    """Sort jobs by specified field."""
    return get_utils().sort_jobs(jobs, sort_by, reverse)

def get_job_stats(jobs: List[Dict]) -> Dict[str, Any]:
    """Get statistics about jobs."""
    return get_utils().get_job_stats(jobs)

def load_session(profile_name: str) -> Dict:
    """Load session data for a profile."""
    return get_utils().load_session(profile_name)

def save_session(profile_name: str, session_data: Dict) -> bool:
    """Save session data for a profile."""
    return get_utils().save_session(profile_name, session_data)

def detect_available_browsers() -> Dict[str, str]:
    """Detect available browsers on the system."""
    return get_utils().detect_available_browsers()

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
        
        logger.info(f"✅ Loaded profile: {profile_name}")
        return profile
        
    except Exception as e:
        logger.error(f"❌ Failed to load profile '{profile_name}': {e}")
        return {}

def hash_job(job: Dict) -> str:
    """Generate hash for a job."""
    return get_utils().generate_job_hash(job)

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

def save_document_as_pdf(docx_path: str, pdf_path: str) -> bool:
    """Save document as PDF (alias for convert_doc_to_pdf)."""
    return convert_doc_to_pdf(docx_path, pdf_path)

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
        profile_name = profile.get('profile_name', 'Unknown')
        profile_dir = Path(f"profiles/{profile_name}")
        
        if not profile_dir.exists():
            logger.error(f"❌ Profile directory not found: {profile_dir}")
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
