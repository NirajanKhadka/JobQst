import sys
from src.core.job_database import get_job_db

def main(profile_name: str):
    db = get_job_db(profile_name)
    jobs = db.get_jobs(limit=100)
    print(f"Found {len(jobs)} jobs for profile '{profile_name}':\n")
    for job in jobs:
        url = job.get('url', '')
        print(f"- {job.get('title', 'No Title')} @ {job.get('company', 'No Company')}: {url}")
        if any(pattern in url for pattern in ["/search?", "q=", "pg=", "posted="]):
            print(f"  [WARNING] Invalid job URL detected: {url}")

if __name__ == "__main__":
    profile = sys.argv[1] if len(sys.argv) > 1 else "Nirajan"
    main(profile)
