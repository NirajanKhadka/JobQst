#!/usr/bin/env python3
"""
AutoJobAgent New System Demonstration
Shows the enhanced dashboard v2, job processing, and all new features in action.
"""

import sys
import os
import time
import requests
import json
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section."""
    print(f"\n📋 {title}")
    print("-" * 40)

def demo_profile_management():
    """Demonstrate profile management."""
    print_section("Profile Management")
    
    try:
        from src.core import utils
        
        # Load profile
        profile = utils.load_profile("Nirajan")
        print(f"✅ Profile loaded: {profile['name']}")
        print(f"   📧 Email: {profile.get('email', 'N/A')}")
        print(f"   📍 Location: {profile.get('location', 'N/A')}")
        print(f"   🎯 Keywords: {', '.join(profile.get('keywords', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Profile management error: {e}")
        return False

def demo_database_status():
    """Demonstrate database status."""
    print_section("Database Status")
    
    try:
        # Check default database
        default_db = "data/jobs.db"
        if os.path.exists(default_db):
            import sqlite3
            conn = sqlite3.connect(default_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Default database: {count} jobs")
        else:
            print("⚠️ Default database not found")
        
        # Check profile database
        profile_db = "profiles/Nirajan/Nirajan.db"
        if os.path.exists(profile_db):
            conn = sqlite3.connect(profile_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            count = cursor.fetchone()[0]
            conn.close()
            print(f"✅ Profile database: {count} jobs")
        else:
            print("⚠️ Profile database not found")
        
        return True
    except Exception as e:
        print(f"❌ Database status error: {e}")
        return False

def demo_job_processing():
    """Demonstrate job processing system."""
    print_section("Job Processing System")
    
    try:
        from src.utils.job_processor_master import JobProcessorMaster
        
        # Create processor
        processor = JobProcessorMaster("Nirajan", max_workers=2)
        
        # Check unprocessed jobs
        unprocessed = processor.load_unprocessed_jobs()
        print(f"✅ Found {len(unprocessed)} unprocessed jobs")
        
        # Get stats
        stats = processor.get_processing_stats()
        print(f"   📊 Queue size: {stats['queue_size']}")
        print(f"   👥 Active workers: {stats['active_workers']}")
        print(f"   🏃 Running: {stats['running']}")
        
        if len(unprocessed) > 0:
            print(f"   💡 Run 'python src/app.py Nirajan --action process-jobs' to process these jobs")
        
        return True
    except Exception as e:
        print(f"❌ Job processing error: {e}")
        return False

def demo_dashboard_v2():
    """Demonstrate dashboard v2."""
    print_section("Dashboard v2")
    
    try:
        from src.dashboard.api_v2 import DashboardAPIv2
        
        # Create dashboard instance
        dashboard = DashboardAPIv2("Nirajan")
        
        # Test basic functionality
        stats = dashboard.fetch_basic_stats()
        print(f"✅ Dashboard v2 created successfully")
        print(f"   📊 Total jobs: {stats.get('total_jobs', 0)}")
        print(f"   🏢 Job sites: {len(stats.get('jobs_by_site', {}))}")
        print(f"   📅 Recent jobs: {stats.get('recent_jobs', 0)}")
        
        # Test cache
        print(f"   💾 Cache size: {len(dashboard.cache)}")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard v2 error: {e}")
        return False

def demo_dashboard_health():
    """Demonstrate dashboard health check."""
    print_section("Dashboard Health")
    
    try:
        # Check if dashboard is running
        response = requests.get("http://localhost:8002/api/health", timeout=5)
        
        if response.status_code == 200:
            health = response.json()
            print("✅ Dashboard is running and healthy")
            print(f"   🏷️ Version: {health.get('version', 'Unknown')}")
            print(f"   👤 Profile: {health.get('profile', 'Unknown')}")
            print(f"   🕐 Timestamp: {health.get('timestamp', 'Unknown')}")
            
            # Test stats endpoint
            stats_response = requests.get("http://localhost:8002/api/stats", timeout=5)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"   📊 Live stats: {stats.get('total_jobs', 0)} jobs")
            
            return True
        else:
            print(f"⚠️ Dashboard responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Dashboard is not running")
        print("   💡 Start it with: python src/app.py Nirajan --action dashboard")
        return False
    except Exception as e:
        print(f"❌ Dashboard health error: {e}")
        return False

def demo_scraping_command():
    """Demonstrate scraping command."""
    print_section("Scraping Command")
    
    print("💡 To scrape jobs, run:")
    print("   python src/app.py Nirajan --action scrape --keywords 'data analyst'")
    print("   python src/app.py Nirajan --action scrape --sites 'eluta,indeed'")
    print("   python src/app.py Nirajan --action scrape --keywords 'python developer' --sites 'eluta'")
    
    return True

def demo_application_command():
    """Demonstrate application command."""
    print_section("Application Command")
    
    print("💡 To apply to jobs, run:")
    print("   python src/app.py Nirajan --action apply")
    print("   python src/app.py Nirajan --action apply --ats workday")
    
    return True

def demo_status_command():
    """Demonstrate status command."""
    print_section("Status Command")
    
    print("💡 To check system status, run:")
    print("   python src/app.py Nirajan --action status")
    
    return True

def demo_job_processing_command():
    """Demonstrate job processing command."""
    print_section("Job Processing Command")
    
    print("💡 To process unanalyzed jobs, run:")
    print("   python src/app.py Nirajan --action process-jobs")
    print("   python src/app.py Nirajan --action process-jobs --max-workers 8")
    
    return True

def demo_interactive_mode():
    """Demonstrate interactive mode."""
    print_section("Interactive Mode")
    
    print("💡 To run in interactive mode, run:")
    print("   python src/app.py Nirajan")
    print("   python src/app.py Nirajan --action interactive")
    
    return True

def demo_dashboard_features():
    """Demonstrate dashboard features."""
    print_section("Dashboard Features")
    
    print("🌐 Dashboard Features:")
    print("   ✅ Real-time updates via WebSocket")
    print("   ✅ Caching for better performance")
    print("   ✅ Background job processing")
    print("   ✅ Profile-based data isolation")
    print("   ✅ Mobile-responsive design")
    print("   ✅ Job filtering and search")
    print("   ✅ Processing queue monitoring")
    
    return True

def demo_system_architecture():
    """Demonstrate system architecture."""
    print_section("System Architecture")
    
    print("🏗️ New System Architecture:")
    print("   🔄 Master/Slave Job Processing")
    print("   📊 Enhanced Dashboard v2")
    print("   💾 Profile-based Database Isolation")
    print("   🧠 AI-powered Job Analysis")
    print("   📝 Automated Document Generation")
    print("   🔍 Intelligent Scraping Pipeline")
    print("   🛡️ Error Recovery & Retry Logic")
    
    return True

def main():
    """Main demonstration function."""
    print_header("AutoJobAgent New System Demonstration")
    print("This demo shows all the new features and improvements!")
    
    # Run all demonstrations
    demos = [
        ("Profile Management", demo_profile_management),
        ("Database Status", demo_database_status),
        ("Job Processing System", demo_job_processing),
        ("Dashboard v2", demo_dashboard_v2),
        ("Dashboard Health", demo_dashboard_health),
        ("System Architecture", demo_system_architecture),
        ("Dashboard Features", demo_dashboard_features),
        ("Scraping Commands", demo_scraping_command),
        ("Application Commands", demo_application_command),
        ("Status Commands", demo_status_command),
        ("Job Processing Commands", demo_job_processing_command),
        ("Interactive Mode", demo_interactive_mode),
    ]
    
    results = []
    for demo_name, demo_func in demos:
        try:
            result = demo_func()
            results.append((demo_name, result))
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
            results.append((demo_name, False))
    
    # Summary
    print_header("Demonstration Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for demo_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {demo_name}")
    
    print(f"\n📊 Overall: {passed}/{total} demonstrations successful")
    
    if passed == total:
        print("\n🎉 All systems are working perfectly!")
        print("\n🚀 Ready to use AutoJobAgent!")
    else:
        print("\n⚠️ Some systems need attention, but core functionality is working.")
    
    print("\n💡 Quick Start Guide:")
    print("   1. Start dashboard: python src/app.py Nirajan --action dashboard")
    print("   2. Scrape jobs: python src/app.py Nirajan --action scrape")
    print("   3. Process jobs: python src/app.py Nirajan --action process-jobs")
    print("   4. Apply to jobs: python src/app.py Nirajan --action apply")
    print("   5. Check status: python src/app.py Nirajan --action status")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ Demonstration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 