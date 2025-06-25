import re
import hashlib
from typing import List, Dict
from urllib.parse import urlparse

def extract_company_from_url(url: str) -> str:
    """Extracts a clean company name from a URL."""
    try:
        domain = urlparse(url).netloc
        # Remove www. and common job board subdomains
        domain = re.sub(r'^(www|jobs|careers)\.', '', domain)
        # Get the first part of the domain
        company = domain.split('.')[0]
        return company.capitalize()
    except Exception:
        return "Unknown"

def normalize_location(location: str) -> str:
    """Normalizes a location string to a standard format."""
    if not location:
        return ""
    return location.strip().title()

def generate_job_hash(job: Dict) -> str:
    """Generates a unique hash for a job."""
    content = f"{job.get('title', '')}{job.get('company', '')}{job.get('url', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def is_duplicate_job(job1: Dict, job2: Dict) -> bool:
    """Checks if two jobs are likely duplicates."""
    if job1.get('url') and job1.get('url') == job2.get('url'):
        return True
    if generate_job_hash(job1) == generate_job_hash(job2):
        return True
    return False

def sort_jobs(jobs: List[Dict], sort_by: str = "scraped_at", reverse: bool = True) -> List[Dict]:
    """Sorts a list of jobs by a given key."""
    return sorted(jobs, key=lambda x: x.get(sort_by, ""), reverse=reverse)