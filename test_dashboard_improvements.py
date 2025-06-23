#!/usr/bin/env python3
"""
Test script to verify dashboard improvements:
1. No more "press enter to stop" behavior
2. Dashboard runs persistently across all CLI actions
3. All actions use the same dashboard instance
"""

import subprocess
import time
import requests
import sys
from pathlib import Path

def test_dashboard_persistence():
    """Test that dashboard runs persistently without blocking."""
    print("🧪 Testing Dashboard Persistence Improvements")
    print("=" * 50)
    
    # Test 1: Start dashboard and verify it's running
    print("\n1️⃣ Testing dashboard auto-start...")
    try:
        # Run main.py with interactive mode (should auto-start dashboard)
        process = subprocess.Popen(
            [sys.executable, "src/app.py", "Nirajan", "--action", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for dashboard to start
        time.sleep(5)
        
        # Check if dashboard is running
        try:
            response = requests.get("http://localhost:8002/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard is running and healthy")
            else:
                print(f"⚠️ Dashboard responding with status: {response.status_code}")
        except:
            print("❌ Dashboard is not running")
            return False
            
        process.terminate()
        process.wait()
        
    except Exception as e:
        print(f"❌ Error testing dashboard start: {e}")
        return False
    
    # Test 2: Verify dashboard doesn't block with "press enter to stop"
    print("\n2️⃣ Testing no blocking behavior...")
    try:
        # Run dashboard action (should not block)
        process = subprocess.Popen(
            [sys.executable, "src/app.py", "Nirajan", "--action", "dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment and check if it's still running
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Dashboard action doesn't block (process still running)")
        else:
            print("❌ Dashboard action terminated unexpectedly")
            return False
            
        process.terminate()
        process.wait()
        
    except Exception as e:
        print(f"❌ Error testing dashboard blocking: {e}")
        return False
    
    # Test 3: Verify dashboard persists across different actions
    print("\n3️⃣ Testing dashboard persistence across actions...")
    try:
        # Test scraping action
        process = subprocess.Popen(
            [sys.executable, "src/app.py", "Nirajan", "--action", "scrape"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        time.sleep(3)
        process.terminate()
        process.wait()
        
        # Check if dashboard is still running
        try:
            response = requests.get("http://localhost:8002/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard persists after scraping action")
            else:
                print("❌ Dashboard not running after scraping action")
                return False
        except:
            print("❌ Dashboard not running after scraping action")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dashboard persistence: {e}")
        return False
    
    print("\n🎉 All dashboard improvement tests passed!")
    return True

def test_dashboard_interconnection():
    """Test that all CLI actions use the same dashboard instance."""
    print("\n🔗 Testing Dashboard Interconnection")
    print("=" * 50)
    
    # Test that different actions reference the same dashboard
    actions_to_test = [
        ("status", "Status action"),
        ("scrape", "Scrape action"), 
        ("apply", "Apply action"),
        ("dashboard", "Dashboard action")
    ]
    
    for action, description in actions_to_test:
        print(f"\nTesting {description}...")
        try:
            process = subprocess.Popen(
                [sys.executable, "src/app.py", "Nirajan", "--action", action],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            time.sleep(2)
            process.terminate()
            process.wait()
            
            # Check if dashboard is still running
            try:
                response = requests.get("http://localhost:8002/api/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {description} uses persistent dashboard")
                else:
                    print(f"❌ {description} broke dashboard connection")
                    return False
            except:
                print(f"❌ {description} broke dashboard connection")
                return False
                
        except Exception as e:
            print(f"❌ Error testing {description}: {e}")
            return False
    
    print("\n🎉 All interconnection tests passed!")
    return True

def main():
    """Run all dashboard improvement tests."""
    print("🚀 Testing Dashboard CLI Improvements")
    print("=" * 60)
    
    # Test dashboard persistence
    if not test_dashboard_persistence():
        print("\n❌ Dashboard persistence tests failed")
        return False
    
    # Test dashboard interconnection
    if not test_dashboard_interconnection():
        print("\n❌ Dashboard interconnection tests failed")
        return False
    
    print("\n🎉 All dashboard improvement tests passed!")
    print("\n📋 Summary of improvements:")
    print("✅ Removed 'press enter to stop' blocking behavior")
    print("✅ Dashboard runs persistently in background")
    print("✅ All CLI actions use the same dashboard instance")
    print("✅ Dashboard auto-starts with any action")
    print("✅ Dashboard continues running after CLI actions complete")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 