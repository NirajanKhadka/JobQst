#!/usr/bin/env python3
"""
Simple script to check database statistics
"""

from src.core.job_database import ModernJobDatabase

def check_database_stats():
    """Check database statistics for all profiles."""
    try:
        # Check default database
        print("🔍 Checking default database...")
        db = ModernJobDatabase('data/jobs.db')
        stats = db.get_stats()
        
        print(f"📊 Database Statistics:")
        print(f"  Total jobs: {stats.get('total_jobs', 0)}")
        print(f"  Jobs by site: {stats.get('jobs_by_site', {})}")
        print(f"  Recent jobs: {stats.get('recent_jobs', 0)}")
        print(f"  Database size: {stats.get('database_size', 0)} bytes")
        
        # Get some sample jobs
        jobs = db.get_jobs(limit=5, offset=0)
        print(f"\n📋 Sample jobs ({len(jobs)} found):")
        for i, job in enumerate(jobs, 1):
            title = job.get('title', 'Unknown')[:50]
            company = job.get('company', 'Unknown')
            site = job.get('site', 'Unknown')
            print(f"  {i}. {title} at {company} ({site})")
        
        # Check Nirajan profile database if it exists
        try:
            print("\n🔍 Checking Nirajan profile database...")
            db_nirajan = ModernJobDatabase('profiles/Nirajan/jobs.db')
            stats_nirajan = db_nirajan.get_stats()
            print(f"📊 Nirajan Database Statistics:")
            print(f"  Total jobs: {stats_nirajan.get('total_jobs', 0)}")
            print(f"  Jobs by site: {stats_nirajan.get('jobs_by_site', {})}")
        except Exception as e:
            print(f"⚠️ Nirajan database not found or empty: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

if __name__ == "__main__":
    check_database_stats() 