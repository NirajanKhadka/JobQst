#!/usr/bin/env python3
"""
Simple test to verify dashboard connection to database.
"""

import sys
import sqlite3
from src.utils.profile_helpers import load_profile, get_available_profiles
from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv
from src.utils.document_generator import customize, DocumentGenerator
from rich.console import Console
from src.core.job_database import get_job_db

console = Console()

def test_direct_database():
    """Test direct database access."""
    console.print("[bold blue]🔍 Testing Direct Database Access[/bold blue]")
    
    db_path = "output/Nirajan_jobs.db"
    try:
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
        console.print("Sample jobs:")
        for job_id, title, company, site, applied in jobs:
            status = "Applied" if applied else "Unapplied"
            console.print(f"  {job_id}. {title} at {company} ({site}) - {status}")
        
        conn.close()
        return total > 0
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        return False

def test_job_database_module():
    """Test job database module."""
    console.print("\n[bold blue]🧪 Testing Job Database Module[/bold blue]")
    
    try:
        db = get_job_db('Nirajan')
        console.print(f"✅ Database instance created: {db.db_path}")
        
        # Test stats
        stats = db.get_stats()
        console.print(f"✅ Stats: {stats}")
        
        # Test get_jobs
        jobs = db.get_jobs(limit=10)
        console.print(f"✅ get_jobs() returned {len(jobs)} jobs")
        
        if jobs:
            for i, job in enumerate(jobs[:3]):
                console.print(f"  {i+1}. {job.get('title')} at {job.get('company')}")
        
        return len(jobs) > 0
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard_api_direct():
    """Test dashboard API functions directly."""
    console.print("\n[bold blue]🌐 Testing Dashboard API Functions[/bold blue]")
    
    try:
        # Test get_comprehensive_stats
        from src.dashboard.api import get_comprehensive_stats
        
        stats = get_comprehensive_stats()
        console.print(f"✅ Comprehensive stats retrieved")
        
        job_stats = stats.get('job_stats', {})
        console.print(f"Job stats: {job_stats}")
        
        # Test the jobs endpoint function directly
        import asyncio
        from src.dashboard.api import get_jobs
        
        # Since get_jobs is async, we need to run it properly
        async def test_get_jobs():
            result = await get_jobs()
            return result
        
        # Run the async function
        result = asyncio.run(test_get_jobs())
        console.print(f"✅ Dashboard get_jobs returned {len(result.get('jobs', []))} jobs")
        console.print(f"Total count: {result.get('total', 0)}")
        
        if result.get('jobs'):
            console.print("Sample jobs from dashboard API:")
            for i, job in enumerate(result['jobs'][:3]):
                console.print(f"  {i+1}. {job.get('title')} at {job.get('company')}")
        
        return len(result.get('jobs', [])) > 0
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_profile_loading():
    """Test profile loading."""
    console.print("\n[bold blue]⚙️ Testing Profile Loading[/bold blue]")
    
    try:
        
        
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
        console.print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    console.print("[bold red]🔧 Dashboard Connection Test[/bold red]\n")
    
    tests = [
        ("Direct Database", test_direct_database),
        ("Job Database Module", test_job_database_module),
        ("Profile Loading", test_profile_loading),
        ("Dashboard API Direct", test_dashboard_api_direct),
    ]
    
    results = {}
    for test_name, test_func in tests:
        console.print(f"\n{'='*50}")
        console.print(f"[bold cyan]Running: {test_name}[/bold cyan]")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            console.print(f"[bold]{status}[/bold]")
        except Exception as e:
            console.print(f"[red]❌ CRASHED: {e}[/red]")
            results[test_name] = False
    
    # Summary
    console.print(f"\n{'='*50}")
    console.print("[bold blue]📊 TEST SUMMARY[/bold blue]")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"{status} {test_name}")
    
    console.print(f"\n[bold]Results: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("\n[bold green]🎉 All tests passed![/bold green]")
        console.print("[cyan]The database has jobs and the API should work.[/cyan]")
        console.print("[cyan]The issue might be in the frontend or dashboard startup.[/cyan]")
    else:
        console.print("\n[bold red]❌ Some tests failed[/bold red]")
        console.print("[cyan]Check the failed tests above for the root cause.[/cyan]")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
