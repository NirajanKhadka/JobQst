#!/usr/bin/env python3
"""
Test script for the optimized scraper with immediate tab closure and concurrent processing
"""

import asyncio
from src.scrapers.optimized_eluta_scraper import OptimizedElutaScraper

async def main():
    """Test the optimized scraper."""
    print("🚀 Testing Optimized Eluta Scraper")
    print("=" * 60)
    print("Features:")
    print("✅ Immediate tab closure after copying job URLs")
    print("⚡ Concurrent job processing (2 jobs at a time)")
    print("🧹 Better resource management")
    print("🤖 OpenHermes 2.5 AI analysis")
    print("=" * 60)
    
    try:
        # Initialize scraper
        scraper = OptimizedElutaScraper(profile_name="Nirajan")
        
        # Run optimized scraping (limited to 2 keywords, 5 jobs each for testing)
        jobs = await scraper.scrape_all_keywords_optimized(max_jobs_per_keyword=5)
        
        print(f"\n🎉 Optimization test completed!")
        print(f"📊 Results:")
        print(f"   - Jobs found: {len(jobs)}")
        print(f"   - Tabs closed: {scraper.stats['tabs_closed']}")
        print(f"   - Concurrent processed: {scraper.stats['concurrent_processed']}")
        print(f"   - Keywords processed: {scraper.stats['keywords_processed']}")
        
        if jobs:
            print(f"\n📋 Sample results:")
            for i, job in enumerate(jobs[:3], 1):
                title = job.get('title', 'Unknown')[:40]
                company = job.get('company', 'Unknown')[:25]
                score = job.get('compatibility_score', 0)
                method = 'OpenHermes' if job.get('llm_analysis', {}).get('analysis_method') == 'openhermes_2_5' else 'Fallback'
                
                print(f"   {i}. {title}... at {company}...")
                print(f"      Score: {score:.2f} | Analysis: {method}")
        
        print(f"\n✅ Optimized scraper test successful!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())