#!/usr/bin/env python3
"""Check the processed jobs results."""

from src.core.job_database import get_job_db

def check_processed_jobs():
    db = get_job_db('default')
    jobs = db.get_all_jobs()
    
    processed_jobs = [j for j in jobs if j.get('status') == 'processed']
    
    print(f"🎉 Successfully processed {len(processed_jobs)} jobs!")
    print("=" * 60)
    
    for i, job in enumerate(processed_jobs):
        print(f"Job {i+1}:")
        print(f"  ✅ Title: {job.get('title', 'N/A')}")
        print(f"  🏢 Company: {job.get('company', 'N/A')}")
        print(f"  📍 Location: {job.get('location', 'N/A')}")
        print(f"  📊 Status: {job.get('status', 'N/A')}")
        print(f"  🔧 Processing Method: {job.get('processing_method', 'N/A')}")
        print(f"  ⚠️ Fallback Used: {job.get('fallback_used', 'N/A')}")
        print(f"  ⏱️ Processing Time: {job.get('processing_time', 'N/A')}s")
        print(f"  👷 Worker ID: {job.get('processing_worker_id', 'N/A')}")
        print()

if __name__ == "__main__":
    check_processed_jobs()