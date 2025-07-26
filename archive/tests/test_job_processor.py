#!/usr/bin/env python3
"""
Test Job Processor with Llama3 7B
Process the scraped URLs using the enhanced job processor with Llama3 7B only
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dashboard.enhanced_job_processor import get_enhanced_job_processor
from src.core.job_database import get_job_db

def test_job_processor():
    """Test the enhanced job processor with scraped URLs."""
    print("🚀 Testing Enhanced Job Processor with Llama3 7B")
    print("=" * 60)
    
    # Initialize processor
    processor = get_enhanced_job_processor("Nirajan")
    db = get_job_db("Nirajan")
    
    # Check current database status
    all_jobs = db.get_all_jobs()
    scraped_jobs = [job for job in all_jobs if job.get('status') == 'scraped' and job.get('title') == 'Pending Processing']
    
    print(f"📊 Database Status:")
    print(f"  Total jobs: {len(all_jobs)}")
    print(f"  Scraped jobs (pending processing): {len(scraped_jobs)}")
    
    if not scraped_jobs:
        print("❌ No scraped jobs found to process")
        print("Run the test scraper first to get some URLs")
        return
    
    # Show sample scraped jobs
    print(f"\n📋 Sample scraped jobs:")
    for i, job in enumerate(scraped_jobs[:3]):
        url = job.get('url', 'No URL')
        search_keyword = job.get('search_keyword', 'No keyword')
        print(f"  {i+1}. {search_keyword} - {url[:60]}...")
    
    # Start processing
    print(f"\n🔄 Starting job processor...")
    success = processor.start_processing()
    
    if not success:
        print("❌ Failed to start job processor")
        return
    
    print("✅ Job processor started successfully")
    
    # Add scraped jobs to processing queue
    print(f"\n📥 Adding {len(scraped_jobs)} jobs to processing queue...")
    added_count = processor.process_scraped_jobs()
    
    if added_count == 0:
        print("❌ No jobs were added to the processing queue")
        processor.stop_processing()
        return
    
    print(f"✅ Added {added_count} jobs to processing queue")
    
    # Monitor processing
    print(f"\n⏱️  Processing {added_count} jobs with Llama3 7B...")
    
    try:
        start_time = time.time()
        last_processed = 0
        
        while True:
            status = processor.get_status()
            processed_count = status['processed_count']
            queue_size = status['queue_size']
            error_count = status['error_count']
            ai_analyzed_count = status['ai_analyzed_count']
            
            # Show progress only when it changes
            if processed_count != last_processed:
                elapsed = time.time() - start_time
                print(f"  Progress: {processed_count}/{added_count} | AI: {ai_analyzed_count} | Errors: {error_count} | Time: {elapsed:.1f}s")
                last_processed = processed_count
            
            # Check if processing is complete
            if queue_size == 0 and processed_count >= added_count:
                print("✅ Processing complete!")
                break
            
            time.sleep(3)  # Check every 3 seconds
            
    except KeyboardInterrupt:
        print("\n⚠️ Monitoring interrupted by user")
    
    # Get final status
    final_status = processor.get_status()
    stats = final_status['stats']
    
    print(f"\n📈 Final Processing Results:")
    print(f"  Total processed: {final_status['processed_count']}")
    print(f"  AI analyzed: {final_status['ai_analyzed_count']}")
    print(f"  Errors: {final_status['error_count']}")
    print(f"  Average AI score: {stats['average_ai_score']:.2f}")
    print(f"  High matches (≥0.8): {stats['high_matches_found']}")
    print(f"  Processing errors: {stats['processing_errors']}")
    
    # Show AI service health
    ai_health = stats['ai_service_health']
    print(f"\n🤖 AI Service Health:")
    print(f"  Connection status: {ai_health['connection_status']}")
    print(f"  Consecutive failures: {ai_health['consecutive_failures']}")
    print(f"  Last successful AI: {ai_health['last_successful_ai']}")
    
    # Stop processor
    print(f"\n⏹️ Stopping job processor...")
    processor.stop_processing()
    
    # Check database after processing
    processed_jobs = db.get_all_jobs()
    processed_count = len([job for job in processed_jobs if job.get('status') == 'processed'])
    
    print(f"\n📊 Database After Processing:")
    print(f"  Total jobs: {len(processed_jobs)}")
    print(f"  Processed jobs: {processed_count}")
    
    # Show sample processed jobs
    processed_sample = [job for job in processed_jobs if job.get('status') == 'processed'][:3]
    if processed_sample:
        print(f"\n📋 Sample processed jobs:")
        for i, job in enumerate(processed_sample):
            title = job.get('title', 'No title')
            company = job.get('company', 'No company')
            score = job.get('compatibility_score', 0)
            print(f"  {i+1}. {title} at {company} (Score: {score:.2f})")
    
    print(f"\n✅ Job processor test completed!")
    print("Next step: Check the dashboard to see the processed jobs")

if __name__ == "__main__":
    test_job_processor()