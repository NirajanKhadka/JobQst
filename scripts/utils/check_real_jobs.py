#!/usr/bin/env python3
"""Check real job data available for proper demonstration."""

from src.core.job_database import get_job_db

def check_real_jobs():
    # Check Nirajan profile which has real scraped jobs
    db = get_job_db('Nirajan')
    jobs = db.get_all_jobs()
    
    print(f"Real jobs available in Nirajan profile: {len(jobs)}")
    print("=" * 60)
    
    for i, job in enumerate(jobs[:5]):
        print(f"Real Job {i+1}:")
        print(f"  Title: {job.get('title', 'N/A')}")
        print(f"  Company: {job.get('company', 'N/A')}")
        print(f"  Status: {job.get('status', 'N/A')}")
        print(f"  Site: {job.get('site', 'N/A')}")
        print()
    
    # Check if any are ready for processing
    scraped_jobs = [j for j in jobs if j.get('status') == 'scraped']
    print(f"Jobs ready for processing (status='scraped'): {len(scraped_jobs)}")

if __name__ == "__main__":
    check_real_jobs()