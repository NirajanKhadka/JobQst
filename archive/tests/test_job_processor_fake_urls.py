#!/usr/bin/env python3
"""
Test job processor with the 3 fake URLs in the database
"""

import sys
import os
import time
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.job_processor_queue import JobProcessorQueue
from src.core.job_database import get_job_db

async def test_job_processor_fake_urls():
    """Test the job processor with the fake URLs in database."""
    try:
        print("🚀 Testing Job Processor with Fake URLs")
        print("=" * 50)
        
        # Get database
        db = get_job_db('Nirajan')
        print("✅ Database connected successfully")
        
        # Get current jobs
        jobs = db.get_jobs()
        print(f"📊 Found {len(jobs)} jobs in database")
        
        # Show the fake URLs
        print("\n🔍 Fake URLs in database:")
        for i, job in enumerate(jobs, 1):
            print(f"  Job {i}: {job.get('url', 'No URL')}")
        
        # Create job processor queue
        processor = JobProcessorQueue('Nirajan', num_workers=1)  # Use 1 worker for testing
        
        # Start the processor
        print("\n🔄 Starting job processor...")
        processor.start()
        
        # Wait for processing
        print("⏳ Waiting for job processing (30 seconds)...")
        time.sleep(30)  # Wait 30 seconds for processing
        
        # Get updated jobs
        updated_jobs = db.get_jobs()
        print(f"\n📊 Updated jobs: {len(updated_jobs)}")
        
        # Check processing results
        processed_jobs = [job for job in updated_jobs if job.get('status') == 'processed']
        failed_jobs = [job for job in updated_jobs if job.get('status') == 'failed']
        
        print(f"✅ Successfully processed: {len(processed_jobs)}")
        print(f"❌ Failed to process: {len(failed_jobs)}")
        
        # Show detailed results
        print("\n🔍 Processing Results:")
        print("-" * 60)
        
        for i, job in enumerate(updated_jobs, 1):
            print(f"\nJob {i}:")
            print(f"  Title: {job.get('title', 'No title')}")
            print(f"  Company: {job.get('company', 'Unknown')}")
            print(f"  Status: {job.get('status', 'Unknown')}")
            print(f"  URL: {job.get('url', 'No URL')}")
            print(f"  Processing Notes: {job.get('processing_notes', 'None')}")
            print(f"  Error Message: {job.get('error_message', 'None')}")
            print("-" * 30)
        
        # Get processor statistics
        stats = processor.get_stats()
        print(f"\n📈 Processor Statistics:")
        print(f"  Total Processed: {stats.get('total_processed', 0)}")
        print(f"  Successful: {stats.get('successful', 0)}")
        print(f"  Failed: {stats.get('failed', 0)}")
        print(f"  Cached: {stats.get('cached', 0)}")
        print(f"  Queue Size: {stats.get('queue_size', 0)}")
        
        # Stop the processor
        print("\n🛑 Stopping job processor...")
        processor.stop()
        
        print("✅ Test completed!")
        
        # Conclusion
        if len(failed_jobs) == 3:
            print("\n🎯 CONCLUSION:")
            print("✅ The job processor correctly failed to process the fake URLs")
            print("✅ This confirms the issue is in the Eluta scraper, not the job processor")
            print("✅ The scraper needs to be fixed to extract real job URLs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_job_processor_fake_urls()) 