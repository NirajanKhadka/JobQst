#!/usr/bin/env python3
"""
Test script to debug Eluta scraper and see what's happening with job extraction
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper

async def test_eluta_scraping():
    """Test the Eluta scraper to see what's happening with job extraction."""
    try:
        print("🔍 Testing Eluta Scraper Job Extraction")
        print("=" * 50)
        
        # Create scraper instance
        scraper = ComprehensiveElutaScraper('Nirajan')
        
        # Test with just one keyword and one page to see what's happening
        print(f"📝 Search terms: {scraper.search_terms[:3]}...")  # Show first 3 terms
        
        # Test with a simple keyword
        test_keyword = "Python"
        print(f"\n🧪 Testing with keyword: {test_keyword}")
        
        # Run a minimal scraping test
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            
            try:
                # Go to Eluta search page
                search_url = f"https://www.eluta.ca/search?q={test_keyword}&l=&radius=25&co=CA&type=1&source=&from=&to=&s=3&su=1"
                print(f"🌐 Navigating to: {search_url}")
                
                await page.goto(search_url, wait_until="networkidle")
                await asyncio.sleep(3)
                
                # Find job elements
                job_elements = await page.query_selector_all(".job-result")
                print(f"📊 Found {len(job_elements)} job elements")
                
                if job_elements:
                    # Test extraction on first job
                    print(f"\n🔍 Testing extraction on first job:")
                    first_job = job_elements[0]
                    
                    # Get raw text content
                    job_text = await first_job.inner_text()
                    print(f"📄 Raw job text:")
                    print("-" * 40)
                    print(job_text)
                    print("-" * 40)
                    
                    # Test the extraction method
                    job_data = await scraper._extract_job_data(page, first_job, 1, 1)
                    print(f"\n📋 Extracted job data:")
                    for key, value in job_data.items():
                        print(f"  {key}: {value}")
                    
                    # Test URL extraction specifically
                    print(f"\n🔗 Testing URL extraction:")
                    real_url = await scraper._get_real_job_url(first_job, page, 1)
                    print(f"  Real URL: {real_url}")
                    
                    if real_url:
                        print(f"  Refining URL...")
                        refined_url = await scraper._refine_and_get_final_url(real_url, context)
                        print(f"  Refined URL: {refined_url}")
                
                else:
                    print("❌ No job elements found")
                
            finally:
                await browser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_eluta_scraping()) 