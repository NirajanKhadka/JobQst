#!/usr/bin/env python3
"""Check all job statuses after processing."""

from src.core.job_database import get_job_db

def check_all_statuses():
    db = get_job_db('default')
    jobs = db.get_all_jobs()
    
    print(f"📊 Total jobs in database: {len(jobs)}")
    print("=" * 60)
    
    # Count statuses
    status_counts = {}
    for job in jobs:
        status = job.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("Status Distribution:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    print("\nJob Details:")
    for i, job in enumerate(jobs):
        print(f"Job {i+1}:")
        print(f"  Title: {job.get('title', 'N/A')}")
        print(f"  Company: {job.get('company', 'N/A')}")
        print(f"  Status: {job.get('status', 'N/A')}")
        if job.get('error_message'):
            print(f"  Error: {job.get('error_message', 'N/A')}")
        if job.get('processing_method'):
            print(f"  Method: {job.get('processing_method', 'N/A')}")
        print()

if __name__ == "__main__":
    check_all_statuses()