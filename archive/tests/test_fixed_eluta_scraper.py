#!/usr/bin/env python3
"""
Test the fixed Eluta scraper with correct selectors
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper

async def test_fixed_eluta_scraper():
    """Test the fixed Eluta scraper."""
    try:
        print("🧪 Testing Fixed Eluta Scraper")
        print("=" * 50)
        
        # Create scraper instance
        scraper = ComprehensiveElutaScraper('Nirajan')
        
        # Test with SQL keyword (which we know has results)
        test_keyword = "SQL"
        print(f"🔍 Testing with keyword: {test_keyword}")
        
        # Run a minimal scraping test
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            
            try:
                # Test the scraping method
                from rich.progress import Progress
                with Progress() as progress:
                    jobs = await scraper._scrape_keyword(page, test_keyword, max_jobs=3, progress=progress)
                
                print(f"\n📊 Results:")
                print(f"  Jobs found: {len(jobs)}")
                
                if jobs:
                    print(f"\n🔍 Job Details:")
                    for i, job in enumerate(jobs, 1):
                        print(f"\nJob {i}:")
                        print(f"  Title: {job.get('title', 'No title')}")
                        print(f"  Company: {job.get('company', 'Unknown')}")
                        print(f"  Location: {job.get('location', 'Unknown')}")
                        print(f"  Salary: {job.get('salary', 'Unknown')}")
                        print(f"  URL: {job.get('url', 'No URL')}")
                        print(f"  ATS: {job.get('ats_system', 'Unknown')}")
                        print("-" * 40)
                else:
                    print("❌ No jobs found")
                
            finally:
                await browser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_eluta_scraper()) 