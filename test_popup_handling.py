#!/usr/bin/env python3
"""
Test script for popup handling in Core Eluta Scraper
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scrapers.core_eluta_scraper import CoreElutaScraper

async def test_popup_handling():
    """Test the popup handling functionality"""
    print("🧪 Testing Core Eluta Scraper with popup handling...")
    
    # Create scraper with minimal config for testing
    config = {
        "search_terms": ["python developer"],
        "pages": 1,
        "jobs": 5,
        "headless": False,  # Non-headless to handle popups
        "days": 7,
        "enable_ai": False,
        "entry_level_only": False
    }
    
    scraper = CoreElutaScraper(profile_name="default", config=config)
    
    try:
        # Run scraping with popup handling
        jobs = await scraper.scrape_all_keywords(limit=5)
        
        print(f"\n✅ Successfully scraped {len(jobs)} jobs with popup handling!")
        
        # Display first job as sample
        if jobs:
            job = jobs[0]
            print(f"\n📋 Sample job:")
            print(f"   Title: {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   URL: {job.get('url', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_popup_handling())
    sys.exit(0 if success else 1)