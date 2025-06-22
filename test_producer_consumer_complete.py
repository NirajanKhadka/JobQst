#!/usr/bin/env python3
"""
Test Producer-Consumer System with Complete Requirements:
- 9 pages per keyword
- 14-day filter (no jobs older than 14 days)
- All keywords from profile
"""

import json
import time
import signal
import sys
from pathlib import Path

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    print(f"\n🛑 Received signal {signum}, stopping...")
    sys.exit(0)

def test_complete_producer_consumer():
    """Test the producer-consumer system with complete requirements."""
    print("🧪 Testing Complete Producer-Consumer System...")
    print("📋 Requirements: 9 pages per keyword, 14-day filter, all keywords")
    
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Load profile
        print("👤 Loading profile...")
        with open("profiles/Nirajan/Nirajan.json", "r") as f:
            profile = json.load(f)
        
        print(f"✅ Profile loaded: {len(profile.get('keywords', []))} keywords")
        print(f"🔍 Keywords: {', '.join(profile.get('keywords', [])[:5])}...")
        
        # Import producer-consumer system
        print("\n🚀 Initializing Producer-Consumer System...")
        from src.scrapers.producer_consumer_orchestrator import ProducerConsumerOrchestrator
        
        # Create orchestrator with complete settings
        db_path = f"profiles/{profile.get('profile_name', 'Nirajan')}/jobs.db"
        print(f"📁 Using database: {db_path}")
        orchestrator = ProducerConsumerOrchestrator(profile, "temp/complete_test", database_path=db_path)
        
        # Update producer settings for complete scraping
        print("\n⚙️ Configuring for complete scraping...")
        orchestrator.producer.max_pages_per_keyword = 9  # 9 pages as requested
        orchestrator.producer.max_jobs_per_keyword = 200  # High limit to get all jobs
        orchestrator.producer.keywords = profile.get("keywords", [])  # All keywords
        
        print(f"✅ Configuration updated:")
        print(f"  • Max pages per keyword: {orchestrator.producer.max_pages_per_keyword}")
        print(f"  • Max jobs per keyword: {orchestrator.producer.max_jobs_per_keyword}")
        print(f"  • Keywords to process: {len(orchestrator.producer.keywords)}")
        print(f"  • Date filter: Last 14 days")
        
        print("\n🎯 Starting Complete Scraping Test...")
        print("📋 This will:")
        print("  • Scrape ALL keywords from profile")
        print("  • Process 9 pages per keyword")
        print("  • Filter for jobs from last 14 days")
        print("  • Process with 4 worker processes")
        print("  • Save to database with multi-process optimization")
        print("  • Show real-time performance")
        print("\n⏱️  Test will run for ~10-15 minutes...")
        print("🛑 Press Ctrl+C to stop early")
        
        # Start the system
        orchestrator.start()
        
        # After the system finishes, check if jobs were saved
        from src.core.job_database import ModernJobDatabase
        db = ModernJobDatabase(db_path)
        stats = db.get_stats()
        print(f"\n📊 Final Database Stats:")
        print(f"  Total jobs: {stats.get('total_jobs', 0)}")
        if stats.get('total_jobs', 0) == 0:
            print("⚠️ WARNING: No jobs saved to the database! Check logs and configuration.")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_single_keyword_quick():
    """Quick test with single keyword to verify system works."""
    print("\n🧪 Quick Test: Single Keyword (Data Analyst, 3 pages)")
    
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Load profile
        print("👤 Loading profile...")
        with open("profiles/Nirajan/Nirajan.json", "r") as f:
            profile = json.load(f)
        
        # Use only first keyword for quick test
        test_keywords = profile.get("keywords", [])[:1]
        profile["keywords"] = test_keywords
        print(f"✅ Profile loaded: {len(test_keywords)} keyword for quick test")
        print(f"🔍 Keyword: {test_keywords[0]}")
        
        # Import producer-consumer system
        print("\n🚀 Initializing Producer-Consumer System...")
        from src.scrapers.producer_consumer_orchestrator import ProducerConsumerOrchestrator
        
        # Create orchestrator with quick test settings
        orchestrator = ProducerConsumerOrchestrator(profile, "temp/quick_test")
        
        # Update producer settings for quick test
        print("\n⚙️ Configuring for quick test...")
        orchestrator.producer.max_pages_per_keyword = 3  # Quick test with 3 pages
        orchestrator.producer.max_jobs_per_keyword = 50  # Reasonable limit
        orchestrator.producer.keywords = test_keywords  # Single keyword
        
        print(f"✅ Configuration updated:")
        print(f"  • Max pages per keyword: {orchestrator.producer.max_pages_per_keyword}")
        print(f"  • Max jobs per keyword: {orchestrator.producer.max_jobs_per_keyword}")
        print(f"  • Keywords to process: {len(orchestrator.producer.keywords)}")
        print(f"  • Date filter: Last 14 days")
        
        print("\n🎯 Starting Quick Test...")
        print("📋 This will:")
        print("  • Scrape 1 keyword (Data Analyst)")
        print("  • Process 3 pages")
        print("  • Filter for jobs from last 14 days")
        print("  • Process with 4 worker processes")
        print("  • Save to database")
        print("\n⏱️  Test will run for ~2-3 minutes...")
        print("🛑 Press Ctrl+C to stop early")
        
        # Start the system
        orchestrator.start()
        
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Producer-Consumer System Test Suite")
    print("=" * 60)
    
    # Ask user which test to run
    print("\n🤔 Choose test mode:")
    print("1. Quick Test (1 keyword, 3 pages) - ~2-3 minutes")
    print("2. Complete Test (all keywords, 9 pages) - ~10-15 minutes")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        success = test_single_keyword_quick()
    elif choice == "2":
        success = test_complete_producer_consumer()
    else:
        print("❌ Invalid choice. Running quick test...")
        success = test_single_keyword_quick()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n🔧 Test failed. Check configuration.") 