#!/usr/bin/env python3
"""
Test script to verify database saving functionality.
"""

import json
import time
import threading
from pathlib import Path
from src.core.job_database import ModernJobDatabase

def test_database_saving():
    """Test if the database can save jobs correctly."""
    print("🧪 Testing Database Saving Functionality...")
    
    # Create a test database
    test_db_path = "temp/test_database.db"
    db = ModernJobDatabase(test_db_path)
    
    # Create test job data
    test_job = {
        "title": "Test Software Engineer",
        "company": "TestCorp",
        "location": "Testville, CA",
        "summary": "This is a test job for database testing.",
        "url": "http://example.com/job/test123",
        "job_id": "test123",
        "site": "eluta",
        "scraped_at": "2025-01-22T11:00:00",
        "search_keyword": "software",
        "session_id": "test-session"
    }
    
    print(f"📝 Test job data: {test_job['title']} at {test_job['company']}")
    
    # Try to add the job
    success = db.add_job(test_job)
    print(f"✅ Job save result: {success}")
    
    # Check if job was actually saved
    jobs = db.get_jobs(limit=10)
    print(f"📊 Total jobs in database: {len(jobs)}")
    
    if jobs:
        print(f"📋 Latest job: {jobs[0]['title']} at {jobs[0]['company']}")
    
    # Try to add the same job again (should be detected as duplicate)
    success2 = db.add_job(test_job)
    print(f"🔄 Duplicate job save result: {success2}")
    
    # Check job count again
    jobs2 = db.get_jobs(limit=10)
    print(f"📊 Total jobs after duplicate attempt: {len(jobs2)}")
    
    # Test with different job
    test_job2 = {
        "title": "Test Data Analyst",
        "company": "TestCorp2",
        "location": "Testville2, CA",
        "summary": "This is another test job.",
        "url": "http://example.com/job/test456",
        "job_id": "test456",
        "site": "eluta",
        "scraped_at": "2025-01-22T11:01:00",
        "search_keyword": "data",
        "session_id": "test-session"
    }
    
    success3 = db.add_job(test_job2)
    print(f"✅ Second job save result: {success3}")
    
    # Final count
    jobs3 = db.get_jobs(limit=10)
    print(f"📊 Final total jobs: {len(jobs3)}")
    
    return len(jobs3) == 2

def test_worker_database_connection():
    """Test database connection in worker process context."""
    print("\n🧪 Testing Worker Database Connection...")
    
    from src.utils.job_data_consumer import JobDataConsumer
    
    # Create test directories
    temp_dir = Path("temp/worker_test")
    input_dir = temp_dir / "raw_jobs"
    processed_dir = temp_dir / "processed"
    db_path = temp_dir / "worker_test.db"
    
    # Cleanup
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
    
    input_dir.mkdir(parents=True)
    
    # Create test batch file
    test_job = {
        "title": "Worker Test Job",
        "company": "WorkerTestCorp",
        "location": "WorkerTestville",
        "summary": "Testing worker database connection.",
        "url": "http://example.com/job/worker123",
        "job_id": "worker123",
        "scraped_at": "2025-01-22T11:00:00",
        "search_keyword": "worker",
        "session_id": "worker-test"
    }
    
    batch_data = {
        "batch_id": "worker_test_001",
        "jobs": [test_job]
    }
    
    with open(input_dir / "jobs_batch_worker_test.json", "w") as f:
        json.dump(batch_data, f)
    
    print(f"📦 Created test batch file: {input_dir / 'jobs_batch_worker_test.json'}")
    
    # Test consumer with single worker
    consumer = JobDataConsumer(str(input_dir), str(processed_dir), str(db_path), num_workers=1)
    
    try:
        # Start processing
        processing_thread = threading.Thread(target=consumer.start_processing)
        processing_thread.daemon = True
        processing_thread.start()
        
        # Wait for processing
        time.sleep(5)
        
        # Check results
        db = ModernJobDatabase(str(db_path))
        jobs = db.get_jobs(limit=10)
        print(f"📊 Jobs saved by worker: {len(jobs)}")
        
        if jobs:
            print(f"📋 Worker saved job: {jobs[0]['title']} at {jobs[0]['company']}")
        
        return len(jobs) == 1
        
    finally:
        consumer.stop_processing()

if __name__ == "__main__":
    print("🚀 Database Save Test Suite")
    print("=" * 50)
    
    # Test 1: Basic database saving
    success1 = test_database_saving()
    
    # Test 2: Worker database connection
    success2 = test_worker_database_connection()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 All database tests passed!")
    else:
        print("🔧 Some database tests failed. Check configuration.") 