#!/usr/bin/env python3
"""
Check full URLs and details of jobs in database
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.job_database import get_job_db

def check_full_urls():
    """Check the full URLs and details of jobs in database."""
    try:
        # Get database
        db = get_job_db('Nirajan')
        print("✅ Database connected successfully")
        
        # Get all jobs with full details
        jobs = db.get_jobs()
        print(f"📊 Total jobs in database: {len(jobs)}")
        
        if not jobs:
            print("❌ No jobs found in database")
            return
        
        # Display full job details
        print("\n🔍 Full Job Details:")
        print("=" * 80)
        
        for i, job in enumerate(jobs, 1):
            print(f"\nJob {i}:")
            print(f"  ID: {job.get('id', 'Unknown')}")
            print(f"  Job ID: {job.get('job_id', 'Unknown')}")
            print(f"  Title: {job.get('title', 'No title')}")
            print(f"  Company: {job.get('company', 'Unknown')}")
            print(f"  Location: {job.get('location', 'Unknown')}")
            print(f"  Status: {job.get('status', 'Unknown')}")
            print(f"  Full URL: {job.get('url', 'No URL')}")
            print(f"  Apply URL: {job.get('apply_url', 'No apply URL')}")
            print(f"  Search Keyword: {job.get('search_keyword', 'Unknown')}")
            print(f"  Site: {job.get('site', 'Unknown')}")
            print(f"  Scraped At: {job.get('scraped_at', 'Unknown')}")
            print(f"  Posted Date: {job.get('posted_date', 'Unknown')}")
            print(f"  Applied: {job.get('applied', 0)}")
            print(f"  Application Status: {job.get('application_status', 'Unknown')}")
            print(f"  Match Score: {job.get('match_score', 0)}")
            print(f"  Raw Data: {job.get('raw_data', 'None')}")
            print(f"  Analysis Data: {job.get('analysis_data', 'None')}")
            print("-" * 60)
        
        # Check if these are actually Eluta URLs
        eluta_jobs = [job for job in jobs if 'eluta.ca' in job.get('url', '')]
        print(f"\n🔗 Eluta jobs: {len(eluta_jobs)}")
        
        # Check if these are search result URLs (the problem)
        search_urls = [job for job in jobs if any(pattern in job.get('url', '') for pattern in ['/search?', 'q=', 'pg='])]
        print(f"🔍 Search result URLs (problematic): {len(search_urls)}")
        
        if search_urls:
            print("\n❌ PROBLEM FOUND: These jobs have search result URLs instead of actual job URLs!")
            for job in search_urls:
                print(f"  - {job.get('url', '')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_full_urls() 