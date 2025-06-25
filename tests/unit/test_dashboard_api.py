#!/usr/bin/env python3
"""
Test the dashboard API endpoints to verify they're working correctly.
"""

import requests
import json
import sys
from src.utils.profile_helpers import load_profile, get_available_profiles
from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv
from src.utils.document_generator import customize, DocumentGenerator
from rich.console import Console

console = Console()

def test_dashboard_api():
    """Test all dashboard API endpoints."""
    
    base_url = "http://localhost:8002"
    
    console.print("[bold blue]🧪 Testing Dashboard API Endpoints[/bold blue]\n")
    
    # Test 1: Main dashboard page
    console.print("[cyan]1. Testing main dashboard page...[/cyan]")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            console.print("✅ Main dashboard page accessible")
        else:
            console.print(f"❌ Main dashboard page failed: {response.status_code}")
    except Exception as e:
        console.print(f"❌ Main dashboard page error: {e}")
        return False
    
    # Test 2: Comprehensive stats
    console.print("\n[cyan]2. Testing comprehensive stats API...[/cyan]")
    try:
        response = requests.get(f"{base_url}/api/comprehensive-stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            console.print("✅ Comprehensive stats API working")
            console.print(f"   Job stats: {stats.get('job_stats', {})}")
            console.print(f"   Profile stats: {list(stats.get('profile_stats', {}).keys())}")
        else:
            console.print(f"❌ Comprehensive stats API failed: {response.status_code}")
            console.print(f"   Response: {response.text}")
    except Exception as e:
        console.print(f"❌ Comprehensive stats API error: {e}")
    
    # Test 3: Jobs API
    console.print("\n[cyan]3. Testing jobs API...[/cyan]")
    try:
        response = requests.get(f"{base_url}/api/jobs", timeout=10)
        if response.status_code == 200:
            jobs_data = response.json()
            console.print("✅ Jobs API working")
            console.print(f"   Total jobs: {jobs_data.get('total', 0)}")
            console.print(f"   Jobs returned: {len(jobs_data.get('jobs', []))}")
            console.print(f"   Profile: {jobs_data.get('profile', 'Unknown')}")
            
            if jobs_data.get('jobs'):
                console.print("   Sample jobs:")
                for i, job in enumerate(jobs_data['jobs'][:3]):
                    console.print(f"     {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
            else:
                console.print("   ⚠️ No jobs returned")
                if 'error' in jobs_data:
                    console.print(f"   Error: {jobs_data['error']}")
        else:
            console.print(f"❌ Jobs API failed: {response.status_code}")
            console.print(f"   Response: {response.text}")
    except Exception as e:
        console.print(f"❌ Jobs API error: {e}")
    
    # Test 4: Sites API
    console.print("\n[cyan]4. Testing sites API...[/cyan]")
    try:
        response = requests.get(f"{base_url}/api/sites", timeout=5)
        if response.status_code == 200:
            sites_data = response.json()
            console.print("✅ Sites API working")
            console.print(f"   Available sites: {len(sites_data.get('sites', []))}")
            for site in sites_data.get('sites', []):
                console.print(f"     - {site.get('label', 'Unknown')} ({site.get('value', 'Unknown')})")
        else:
            console.print(f"❌ Sites API failed: {response.status_code}")
    except Exception as e:
        console.print(f"❌ Sites API error: {e}")
    
    # Test 5: Job stats API
    console.print("\n[cyan]5. Testing job stats API...[/cyan]")
    try:
        response = requests.get(f"{base_url}/api/job-stats", timeout=5)
        if response.status_code == 200:
            job_stats = response.json()
            console.print("✅ Job stats API working")
            console.print(f"   Stats: {job_stats}")
        else:
            console.print(f"❌ Job stats API failed: {response.status_code}")
    except Exception as e:
        console.print(f"❌ Job stats API error: {e}")
    
    console.print("\n[bold green]🎯 Dashboard API Test Complete[/bold green]")
    return True

def test_database_direct():
    """Test database access directly."""
    console.print("\n[bold blue]🗄️ Testing Database Direct Access[/bold blue]\n")
    
    try:
        import sqlite3
        import os
        
        db_path = "output/Nirajan_jobs.db"
        if not os.path.exists(db_path):
            console.print(f"❌ Database file not found: {db_path}")
            return False
        
        console.print(f"✅ Database file exists: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total jobs
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total = cursor.fetchone()[0]
        console.print(f"✅ Total jobs in database: {total}")
        
        # Get unapplied jobs
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE applied = 0 OR applied IS NULL')
        unapplied = cursor.fetchone()[0]
        console.print(f"✅ Unapplied jobs: {unapplied}")
        
        # Get sample jobs
        cursor.execute('SELECT id, title, company, site, applied FROM jobs LIMIT 5')
        jobs = cursor.fetchall()
        console.print("✅ Sample jobs:")
        for job_id, title, company, site, applied in jobs:
            status = "Applied" if applied else "Unapplied"
            console.print(f"   {job_id}. {title[:40]}... at {company} ({site}) - {status}")
        
        conn.close()
        return True
        
    except Exception as e:
        console.print(f"❌ Database direct access error: {e}")
        return False

def test_profile_loading():
    """Test profile loading."""
    console.print("\n[bold blue]👤 Testing Profile Loading[/bold blue]\n")
    
    try:
        import sys
        sys.path.append('.')
        
        from src.utils.profile_helpers import load_profile, get_available_profiles
        from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
        from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv
        from src.utils.document_generator import customize, DocumentGenerator
        
        profiles = get_available_profiles()
        console.print(f"✅ Available profiles: {profiles}")
        
        if 'Nirajan' in profiles:
            profile = load_profile('Nirajan')
            console.print(f"✅ Nirajan profile loaded: {profile.get('name')}")
            return True
        else:
            console.print("❌ Nirajan profile not found")
            return False
        
    except Exception as e:
        console.print(f"❌ Profile loading error: {e}")
        return False

def main():
    """Run all tests."""
    console.print("[bold red]🔧 Dashboard API Test Suite[/bold red]\n")
    
    # Test database first
    db_ok = test_database_direct()
    
    # Test profile loading
    profile_ok = test_profile_loading()
    
    # Test API endpoints
    api_ok = test_dashboard_api()
    
    # Summary
    console.print("\n" + "="*60)
    console.print("[bold blue]📊 TEST SUMMARY[/bold blue]")
    
    tests = [
        ("Database Access", db_ok),
        ("Profile Loading", profile_ok),
        ("Dashboard API", api_ok)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"{status} {test_name}")
        if result:
            passed += 1
    
    console.print(f"\n[bold]Results: {passed}/{len(tests)} tests passed[/bold]")
    
    if passed == len(tests):
        console.print("\n[bold green]🎉 All tests passed! Dashboard should be working.[/bold green]")
        console.print("[cyan]If dashboard still shows no jobs, try refreshing the browser.[/cyan]")
    else:
        console.print("\n[bold red]❌ Some tests failed. Check the errors above.[/bold red]")
    
    return 0 if passed == len(tests) else 1

if __name__ == "__main__":
    sys.exit(main())
