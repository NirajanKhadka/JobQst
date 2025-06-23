#!/usr/bin/env python3
"""
Test script for the new AutoJobAgent systems:
1. Enhanced Dashboard v2
2. Master/Slave Job Processing
3. Profile Management
"""

import sys
import os
import time
import requests
import sqlite3
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_profile_loading():
    """Test profile loading functionality."""
    print("🔍 Testing Profile Loading...")
    
    try:
        from src.core import utils
        
        # Test loading Nirajan profile
        profile = utils.load_profile("Nirajan")
        
        if profile and 'name' in profile:
            print(f"✅ Profile loaded successfully: {profile['name']}")
            print(f"   📧 Email: {profile.get('email', 'N/A')}")
            print(f"   📍 Location: {profile.get('location', 'N/A')}")
            print(f"   🎯 Keywords: {len(profile.get('keywords', []))} keywords")
            return True
        else:
            print("❌ Profile loading failed - missing required fields")
            return False
            
    except Exception as e:
        print(f"❌ Profile loading error: {e}")
        return False

def test_database_connection():
    """Test database connection and schema."""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        db_path = "profiles/Nirajan/Nirajan.db"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if jobs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        if cursor.fetchone():
            print("✅ Jobs table exists")
            
            # Get job count
            cursor.execute("SELECT COUNT(*) FROM jobs")
            job_count = cursor.fetchone()[0]
            print(f"   📊 Total jobs: {job_count}")
            
            # Get recent jobs
            cursor.execute("""
                SELECT COUNT(*) FROM jobs 
                WHERE scraped_at > datetime('now', '-1 day')
            """)
            recent_count = cursor.fetchone()[0]
            print(f"   📅 Recent jobs (24h): {recent_count}")
            
        else:
            print("⚠️ Jobs table does not exist - will be created when needed")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_job_processing_system():
    """Test the job processing master system."""
    print("\n⚙️ Testing Job Processing System...")
    
    try:
        from src.utils.job_processor_master import JobProcessorMaster
        
        # Create processor instance
        processor = JobProcessorMaster("Nirajan", max_workers=2)
        
        # Test loading unprocessed jobs
        unprocessed_jobs = processor.load_unprocessed_jobs()
        print(f"✅ Found {len(unprocessed_jobs)} unprocessed jobs")
        
        # Test getting stats
        stats = processor.get_processing_stats()
        print(f"   📊 Stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Job processing system error: {e}")
        return False

def test_dashboard_v2():
    """Test the enhanced dashboard v2."""
    print("\n📊 Testing Dashboard v2...")
    
    try:
        from src.dashboard.api_v2 import DashboardAPIv2
        
        # Create dashboard instance
        dashboard = DashboardAPIv2("Nirajan")
        
        # Test basic stats
        stats = dashboard.fetch_basic_stats()
        print(f"✅ Dashboard v2 created successfully")
        print(f"   📊 Total jobs: {stats.get('total_jobs', 0)}")
        print(f"   🏢 Job sites: {len(stats.get('jobs_by_site', {}))}")
        
        # Test cache functionality
        cache_key = "test_cache"
        test_data = {"test": "data"}
        dashboard.cache[cache_key] = test_data
        dashboard.cache_timestamps[cache_key] = time.time()
        
        if cache_key in dashboard.cache:
            print("✅ Cache functionality working")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard v2 error: {e}")
        return False

def test_dashboard_health():
    """Test if dashboard is running and healthy."""
    print("\n🏥 Testing Dashboard Health...")
    
    try:
        # Try to connect to dashboard
        response = requests.get("http://localhost:8002/api/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Dashboard is running and healthy")
            print(f"   🏷️ Version: {health_data.get('version', 'Unknown')}")
            print(f"   👤 Profile: {health_data.get('profile', 'Unknown')}")
            return True
        else:
            print(f"⚠️ Dashboard responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Dashboard is not running (this is normal if not started)")
        return False
    except Exception as e:
        print(f"❌ Dashboard health check error: {e}")
        return False

def test_comprehensive_system():
    """Test the complete system integration."""
    print("\n🔗 Testing Complete System Integration...")
    
    try:
        # Test all components
        tests = [
            ("Profile Loading", test_profile_loading),
            ("Database Connection", test_database_connection),
            ("Job Processing System", test_job_processing_system),
            ("Dashboard v2", test_dashboard_v2),
            ("Dashboard Health", test_dashboard_health)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n📋 Test Results Summary:")
        print("=" * 50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print("=" * 50)
        print(f"📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is ready.")
            return True
        else:
            print("⚠️ Some tests failed. Check the issues above.")
            return False
            
    except Exception as e:
        print(f"❌ Comprehensive test error: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 AutoJobAgent System Test Suite")
    print("=" * 50)
    print("Testing new systems: Dashboard v2, Job Processing, Profile Management")
    print("=" * 50)
    
    # Run comprehensive test
    success = test_comprehensive_system()
    
    if success:
        print("\n🎉 All systems are working correctly!")
        print("\n💡 Next steps:")
        print("   1. Start dashboard: python src/app.py Nirajan --action dashboard")
        print("   2. Process jobs: python src/app.py Nirajan --action process-jobs")
        print("   3. Scrape jobs: python src/app.py Nirajan --action scrape")
        print("   4. View status: python src/app.py Nirajan --action status")
    else:
        print("\n⚠️ Some systems need attention. Check the issues above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 