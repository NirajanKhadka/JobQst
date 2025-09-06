#!/usr/bin/env python3
"""
Direct JobSpy scraper for 1000 jobs with RCIP tagging
No emojis, just plain text to avoid encoding issues
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

async def scrape_1000_jobs_with_rcip():
    """Scrape 1000 jobs with RCIP tagging for Nirajan profile"""
    print("Starting 1000 jobs scraping with RCIP tagging...")
    
    try:
        from src.scrapers.jobspy_scraper import JobSpyScraper
        from src.core.job_database import get_job_db
        
        # Initialize scraper for Nirajan profile
        print("Initializing Enhanced JobSpy Scraper for Nirajan...")
        scraper = JobSpyScraper('Nirajan')
        
        # Run scraping
        print("Starting scraping process...")
        jobs = await scraper.scrape_enhanced()
        
        print(f"Scraping completed: {len(jobs)} jobs found")
        
        # Analyze RCIP tagging
        if jobs:
            rcip_jobs = [job for job in jobs if job.get('is_rcip_city', 0) == 1]
            non_rcip_jobs = [job for job in jobs if job.get('is_rcip_city', 0) == 0]
            
            print(f"RCIP tagged jobs: {len(rcip_jobs)}")
            print(f"Non-RCIP jobs: {len(non_rcip_jobs)}")
            print(f"RCIP percentage: {len(rcip_jobs)/len(jobs)*100:.1f}%")
            
            # Show location breakdown
            locations = {}
            for job in jobs:
                loc = job.get('location', 'Unknown')
                is_rcip = job.get('is_rcip_city', 0) == 1
                if loc not in locations:
                    locations[loc] = {'total': 0, 'rcip': 0}
                locations[loc]['total'] += 1
                if is_rcip:
                    locations[loc]['rcip'] += 1
            
            print("\nTop 10 locations:")
            sorted_locs = sorted(locations.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
            for loc, stats in sorted_locs:
                rcip_pct = (stats['rcip'] / stats['total'] * 100) if stats['total'] else 0
                print(f"  {loc}: {stats['total']} jobs ({stats['rcip']} RCIP, {rcip_pct:.1f}%)")
            
            # Show sample RCIP jobs
            if rcip_jobs:
                print(f"\nSample RCIP jobs:")
                for i, job in enumerate(rcip_jobs[:5]):
                    title = job.get('title', 'Unknown')[:40]
                    company = job.get('company', 'Unknown')[:20]
                    location = job.get('location', 'Unknown')
                    print(f"  {i+1}. {title} at {company} in {location}")
        
        # Check database
        print("\nChecking database...")
        job_db = get_job_db('Nirajan')
        all_jobs = job_db.get_all_jobs()
        print(f"Total jobs in database: {len(all_jobs)}")
        
        # Check if RCIP column exists in database
        if all_jobs:
            has_rcip_in_db = any('is_rcip_city' in job for job in all_jobs)
            print(f"RCIP column in database: {has_rcip_in_db}")
            
            if has_rcip_in_db:
                db_rcip_count = sum(1 for job in all_jobs if job.get('is_rcip_city', 0) == 1)
                print(f"RCIP jobs in database: {db_rcip_count}")
        
        return len(jobs)
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return 0

def test_dashboard_integration():
    """Test if dashboard can display RCIP data"""
    print("\nTesting dashboard integration...")
    
    try:
        # Try to load data the way dashboard does
        from src.core.job_database import get_job_db
        
        job_db = get_job_db('Nirajan')
        jobs = job_db.get_all_jobs()
        
        if jobs:
            print(f"Dashboard can access {len(jobs)} jobs")
            
            # Check RCIP data availability
            rcip_available = any('is_rcip_city' in job for job in jobs)
            print(f"RCIP data available for dashboard: {rcip_available}")
            
            if rcip_available:
                rcip_count = sum(1 for job in jobs if job.get('is_rcip_city', 0) == 1)
                print(f"Dashboard will show {rcip_count} RCIP jobs")
                print("Dashboard RCIP filtering will work!")
            else:
                print("Dashboard RCIP filtering not available - no RCIP column")
        else:
            print("No jobs available for dashboard")
            
    except Exception as e:
        print(f"Dashboard integration test failed: {e}")

if __name__ == "__main__":
    print("Direct JobSpy Scraper with RCIP Tagging")
    print("=" * 50)
    
    # Run the scraping
    jobs_count = asyncio.run(scrape_1000_jobs_with_rcip())
    
    if jobs_count > 0:
        print(f"\nScraping successful! {jobs_count} jobs scraped with RCIP tagging.")
        
        # Test dashboard integration
        test_dashboard_integration()
        
        print("\nTo view the data in dashboard:")
        print("python main.py Nirajan --action dashboard")
        print("\nLook for RCIP filtering options in the dashboard!")
        print("RCIP cities are immigration-friendly Canadian cities.")
    else:
        print("\nScraping failed. Please check the logs for errors.")
