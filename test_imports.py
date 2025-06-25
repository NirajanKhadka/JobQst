#!/usr/bin/env python3
"""
Simple test script to verify core imports work correctly
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test core imports"""
    try:
        print("Testing core imports...")
        
        # Test ProcessManager
        from core.process_manager import ProcessManager
        print("✅ ProcessManager imported successfully")
        
        # Test DashboardManager
        from core.process_manager import DashboardManager
        print("✅ DashboardManager imported successfully")
        
        # Test basic core modules
        from core import session, job_data, job_database
        print("✅ Core modules imported successfully")
        
        # Test app module
        from app import main
        print("✅ App module imported successfully")
        
        print("\n🎉 All core imports successful! System is ready to ignite!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 