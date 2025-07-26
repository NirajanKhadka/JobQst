#!/usr/bin/env python3
"""Analyze the problematic jobs with bad titles."""

from src.core.job_database import get_job_db
import json

def analyze_problematic_jobs():
    print("🚨 ANALYZING PROBLEMATIC JOBS")
    print("=" * 60)
    
    db = get_job_db('Nirajan')
    jobs = db.get_all_jobs()
    
    # Find jobs with problematic titles
    problematic_titles = ['Job Position', 'Home Office Toronto On', 'Careers']
    
    for job in jobs:
        title = job.get('title', '')
        if any(prob_title in title for prob_title in problematic_titles):
            print(f"\n🚨 PROBLEMATIC JOB: {job.get('job_id', 'N/A')}")
            print("-" * 40)
            print(f"📝 Title: '{title}'")
            print(f"🏢 Company: '{job.get('company', 'N/A')}'")
            print(f"🔗 URL: '{job.get('url', 'N/A')}'")
            print(f"📄 Summary: '{job.get('summary', 'N/A')}'")
            print(f"📋 Description: '{job.get('job_description', 'N/A')}'")
            print(f"🌐 Site: '{job.get('site', 'N/A')}'")
            print(f"📅 Scraped At: '{job.get('scraped_at', 'N/A')}'")
            
            # Analyze what went wrong
            print("\n🔍 ANALYSIS:")
            
            if title == 'Job Position':
                print("  ❌ Generic placeholder title - scraper likely grabbed wrong element")
                print("  🔧 Fix: Update CSS selector to target actual job title")
            
            elif 'Home Office' in title:
                print("  ❌ Location info scraped as title - selector confusion")
                print("  🔧 Fix: Separate title and location selectors")
            
            elif title == 'Careers':
                print("  ❌ Page navigation element scraped as title")
                print("  🔧 Fix: More specific CSS selector for job titles")
            
            # Check if URL gives clues
            url = job.get('url', '')
            if url:
                print(f"  🔗 URL Analysis: {url}")
                if 'ashbyhq.com' in url:
                    print("    - AshbyHQ ATS system")
                elif 'workday.com' in url:
                    print("    - Workday ATS system")
                else:
                    print("    - Unknown ATS system")

if __name__ == "__main__":
    analyze_problematic_jobs()