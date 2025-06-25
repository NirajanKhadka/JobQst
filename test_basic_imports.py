#!/usr/bin/env python3
"""
Basic import test to verify core functionality works.
"""

def test_basic_imports():
    """Test that basic modules can be imported."""
    try:
        print("Testing basic imports...")
        
        # Test core modules
        from src.core.job_database import ModernJobDatabase, get_job_db
        print("✅ Core job database imports work")
        
        from src import utils
        print("✅ Core utils imports work")
        
        # Test ATS modules
        from src.ats import detect, get_submitter
        print("✅ ATS imports work")
        
        # Test dashboard
        from src.dashboard import api as dashboard_api
        print("✅ Dashboard imports work")
        
        # Test utils
        from src.utils.document_generator import customize
        print("✅ Document generator imports work")
        
        print("\n🎉 All basic imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_profile_loading():
    """Test that we can load a profile."""
    try:
        print("\nTesting profile loading...")
        
        from src.utils.profile_helpers import load_profile
        profile = load_profile("Nirajan")
        
        if profile:
            print(f"✅ Profile loaded: {profile.get('name', 'Unknown')}")
            print(f"   Keywords: {profile.get('keywords', [])}")
            return True
        else:
            print("❌ Profile not found")
            return False
            
    except Exception as e:
        print(f"❌ Profile loading error: {e}")
        return False

def test_database_connection():
    """Test that we can connect to the database."""
    try:
        print("\nTesting database connection...")
        
        from src.core.job_database import get_job_db
        db = get_job_db("Nirajan")
        
        if db:
            stats = db.get_stats()
            print(f"✅ Database connected: {stats.get('total_jobs', 0)} jobs")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running basic functionality tests...\n")
    
    tests = [
        test_basic_imports,
        test_profile_loading,
        test_database_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Basic functionality is working.")
    else:
        print("⚠️ Some tests failed. Check the errors above.") 