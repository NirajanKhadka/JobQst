#!/usr/bin/env python3
"""
Simple script to check database contents.
"""

from src.core.job_database import ModernJobDatabase

def main():
    db = ModernJobDatabase('profiles/Nirajan/jobs.db')
    jobs = db.get_jobs(limit=10)
    print(f"Total jobs in database: {len(jobs)}")
    
    if jobs:
        print("\nLatest jobs:")
        for i, job in enumerate(jobs[:5]):
            print(f"{i+1}. {job['title']} at {job['company']} ({job['site']})")
    else:
        print("No jobs found in database.")

if __name__ == "__main__":
    main() 