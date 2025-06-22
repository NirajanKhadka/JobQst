#!/usr/bin/env python3
"""
Real scraping test for the Producer-Consumer system.
This will actually scrape jobs from Eluta to verify the system works.
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

def test_real_scraping():
    """Test the producer-consumer system with real job scraping."""
    print("🧪 Testing Real Job Scraping with Producer-Consumer System...")
    
    try:
        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Load profile
        print("👤 Loading profile...")
        with open("profiles/Nirajan/Nirajan.json", "r") as f:
            profile = json.load(f)
        
        # Limit keywords for testing (use only first 2)
        test_keywords = profile.get("keywords", [])[:2]
        profile["keywords"] = test_keywords
        print(f"✅ Profile loaded: {len(test_keywords)} keywords for testing")
        print(f"🔍 Keywords: {', '.join(test_keywords)}")
        
        # Import and test producer-consumer system
        print("\n🚀 Initializing Producer-Consumer System...")
        from src.scrapers.producer_consumer_orchestrator import ProducerConsumerOrchestrator
        
        # Create orchestrator with test settings
        orchestrator = ProducerConsumerOrchestrator(profile, "temp/test_real")
        
        print("\n🎯 Starting Real Scraping Test...")
        print("📋 This will:")
        print("  • Scrape real jobs from Eluta.ca")
        print("  • Process them with AI analysis")
        print("  • Save to database")
        print("  • Show real-time performance")
        print("\n⏱️  Test will run for ~2-3 minutes...")
        print("🛑 Press Ctrl+C to stop early")
        
        # Start the system
        orchestrator.start()
        
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_real_scraping()
    if success:
        print("\n🎉 Real scraping test completed successfully!")
        print("📁 Check temp/test_real/ for scraped data")
    else:
        print("\n🔧 Test failed - check error messages above") 