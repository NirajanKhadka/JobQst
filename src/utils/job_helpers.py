import re
import hashlib
from typing import List, Dict
from urllib.parse import urlparse
# Removed self-import: from src.utils.job_helpers import generate_job_hash


def extract_company_from_url(url: str) -> str:
    """Extracts a clean company name from a URL."""
    try:
        domain = urlparse(url).netloc
        # Remove www. and common job board subdomains
        domain = re.sub(r"^(www|jobs|careers)\.", "", domain)
        # Get the first part of the domain
        company = domain.split(".")[0]
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
    if job1.get("url") and job1.get("url") == job2.get("url"):
        return True
    if generate_job_hash(job1) == generate_job_hash(job2):
        return True
    return False


def sort_jobs(jobs: List[Dict], sort_by: str = "scraped_at", reverse: bool = True) -> List[Dict]:
    """Sorts a list of jobs by a given key."""
    return sorted(jobs, key=lambda x: x.get(sort_by, ""), reverse=reverse)


def get_job_stats(jobs: List[Dict]) -> Dict:
    """Get statistics about a list of jobs."""
    if not jobs:
        return {
            "total_jobs": 0,
            "unique_companies": 0,
            "locations": {},
            "job_types": {},
            "avg_salary": 0,
        }

    companies = set()
    locations = {}
    job_types = {}
    total_salary = 0
    salary_count = 0

    for job in jobs:
        # Count companies
        if job.get("company"):
            companies.add(job["company"])

        # Count locations
        location = job.get("location", "Unknown")
        locations[location] = locations.get(location, 0) + 1

        # Count job types (based on title keywords)
        title = job.get("title", "").lower()
        if any(keyword in title for keyword in ["analyst", "analysis"]):
            job_types["Analyst"] = job_types.get("Analyst", 0) + 1
        elif any(keyword in title for keyword in ["developer", "engineer", "programmer"]):
            job_types["Developer"] = job_types.get("Developer", 0) + 1
        elif any(keyword in title for keyword in ["manager", "lead", "supervisor"]):
            job_types["Manager"] = job_types.get("Manager", 0) + 1
        else:
            job_types["Other"] = job_types.get("Other", 0) + 1

        # Calculate average salary (if available)
        salary = job.get("salary")
        if salary:
            # Extract numeric value from salary string
            salary_match = re.search(r"\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", str(salary))
            if salary_match:
                try:
                    salary_value = float(salary_match.group(1).replace(",", ""))
                    total_salary += salary_value
                    salary_count += 1
                except ValueError:
                    pass

    return {
        "total_jobs": len(jobs),
        "unique_companies": len(companies),
        "locations": locations,
        "job_types": job_types,
        "avg_salary": total_salary / salary_count if salary_count > 0 else 0,
    }
