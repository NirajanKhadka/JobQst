#!/usr/bin/env python3
"""Check job data in the database."""

from src.core.job_database import get_job_db

def check_jobs():
    db = get_job_db('Nirajan')
    jobs = db.get_all_jobs()
    
    print(f"Found {len(jobs)} jobs in Nirajan profile:")
    print("-" * 60)
    
    for i, job in enumerate(jobs[:5]):
        print(f"Job {i+1}:")
        print(f"  ID: {job.get('job_id', 'N/A')}")
        print(f"  Title: {job.get('title', 'N/A')}")
        print(f"  Company: {job.get('company', 'N/A')}")
        print(f"  Status: {job.get('status', 'N/A')}")
        print(f"  Site: {job.get('site', 'N/A')}")
        print()
    
    # Check status distribution
    statuses = {}
    for job in jobs:
        status = job.get('status', 'no_status')
        statuses[status] = statuses.get(status, 0) + 1
    
    print("Status distribution:")
    for status, count in statuses.items():
        print(f"  {status}: {count}")

if __name__ == "__main__":
    check_jobs()