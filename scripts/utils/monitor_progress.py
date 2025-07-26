#!/usr/bin/env python3
"""
Monitor scraping and processing progress
"""

import time
from src.core.job_database import get_job_db

def monitor_progress():
    """Monitor scraping and processing progress"""
    print("🔍 Monitoring scraping and processing progress...")
    print("Press Ctrl+C to stop monitoring")
    
    try:
        while True:
            db = get_job_db('Nirajan')
            jobs = db.get_jobs()
            
            print(f"\n📊 Database Status: {len(jobs)} total jobs")
            
            if jobs:
                from collections import Counter
                statuses = Counter(job.get('status', 'unknown') for job in jobs)
                print("Job Statuses:")
                for status, count in statuses.items():
                    print(f"  {status}: {count}")
                
                # Show recent jobs
                recent_jobs = sorted(jobs, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
                print("\nRecent Jobs:")
                for job in recent_jobs:
                    title = job.get('title', 'Unknown')[:50]
                    company = job.get('company', 'Unknown')[:30]
                    status = job.get('status', 'unknown')
                    print(f"  {title} at {company} - {status}")
            else:
                print("No jobs found yet - scraper may still be running...")
            
            print(f"\n⏰ {time.strftime('%H:%M:%S')} - Waiting 30 seconds...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    monitor_progress() 