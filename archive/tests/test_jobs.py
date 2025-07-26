#!/usr/bin/env python3
"""
Test script to check jobs in Nirajan profile database
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.job_database import get_job_db

def test_jobs():
    """Test the jobs in Nirajan profile database."""
    try:
        # Get database
        db = get_job_db('Nirajan')
        print("✅ Database connected successfully")
        
        # Get all jobs
        jobs = db.get_jobs()
        print(f"📊 Total jobs in database: {len(jobs)}")
        
        if not jobs:
            print("❌ No jobs found in database")
            return
        
        # Display job details
        print("\n🔍 Job Details:")
        print("-" * 80)
        
        for i, job in enumerate(jobs, 1):
            print(f"\nJob {i}:")
            print(f"  Title: {job.get('title', 'No title')}")
            print(f"  Company: {job.get('company', 'Unknown')}")
            print(f"  Location: {job.get('location', 'Unknown')}")
            print(f"  Status: {job.get('status', 'Unknown')}")
            print(f"  URL: {job.get('url', 'No URL')[:100]}...")
            print(f"  Applied: {job.get('applied', 0)}")
            print(f"  Application Status: {job.get('application_status', 'Unknown')}")
            print(f"  Match Score: {job.get('match_score', 0)}")
            print("-" * 40)
        
        # Check pending jobs (status = 'scraped')
        pending_jobs = [job for job in jobs if job.get('status') == 'scraped']
        print(f"\n📥 Pending jobs (status='scraped'): {len(pending_jobs)}")
        
        # Check processed jobs
        processed_jobs = [job for job in jobs if job.get('status') == 'processed']
        print(f"⚙️ Processed jobs: {len(processed_jobs)}")
        
        # Check applied jobs
        applied_jobs = [job for job in jobs if job.get('applied') == 1]
        print(f"✅ Applied jobs: {len(applied_jobs)}")
        
        # Get job statistics
        stats = db.get_job_stats()
        print(f"\n📈 Database Statistics:")
        print(f"  Total jobs: {stats.get('total_jobs', 0)}")
        print(f"  Applied jobs: {stats.get('applied_jobs', 0)}")
        print(f"  Unapplied jobs: {stats.get('unapplied_jobs', 0)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jobs() 