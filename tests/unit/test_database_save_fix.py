#!/usr/bin/env python3
"""
Test script to verify that the database save fix is working.
This script simulates the scraping process and tests database saving.
"""

from src.core.job_database import get_job_db
from rich.console import Console

console = Console()

def test_database_save():
    """Test that jobs can be saved to the database."""
    console.print("[bold blue]🧪 Testing Database Save Fix[/bold blue]")
    
    # Get database
    db = get_job_db("Nirajan Khadka")
    
    # Check initial state
    initial_jobs = db.get_all_jobs()
    console.print(f"[cyan]Initial jobs in database: {len(initial_jobs)}[/cyan]")
    
    # Create test job data (similar to what scrapers return)
    test_job = {
        'title': 'Test Data Analyst Position',
        'company': 'Test Company Inc.',
        'location': 'Toronto, ON',
        'url': 'https://test-company.com/careers/data-analyst',
        'summary': 'Test job description for data analyst position',
        'posted_date': '2025-06-18',
        'source': 'eluta',
        'found_by_keyword': 'data analyst'
    }
    
    # Test adding job to database
    console.print("[cyan]💾 Testing job save to database...[/cyan]")
    success = db.add_job(test_job)
    
    if success:
        console.print("[green]✅ Job saved successfully![/green]")
    else:
        console.print("[yellow]⚠️ Job not saved (might be duplicate)[/yellow]")
    
    # Check final state
    final_jobs = db.get_all_jobs()
    console.print(f"[cyan]Final jobs in database: {len(final_jobs)}[/cyan]")
    
    # Show the difference
    if len(final_jobs) > len(initial_jobs):
        console.print(f"[bold green]✅ SUCCESS: {len(final_jobs) - len(initial_jobs)} new job(s) added![/bold green]")
        
        # Show the new job
        for job in final_jobs[-1:]:  # Show last job
            console.print(f"[green]📋 New job: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}[/green]")
    else:
        console.print("[yellow]⚠️ No new jobs added (might be duplicate or error)[/yellow]")
    
    # Test database stats
    stats = db.get_stats()
    console.print(f"\n[bold]📊 Database Stats:[/bold]")
    console.print(f"[blue]Total jobs: {stats.get('total_jobs', 0)}[/blue]")
    console.print(f"[blue]Unapplied jobs: {stats.get('unapplied_jobs', 0)}[/blue]")
    console.print(f"[blue]Applied jobs: {stats.get('applied_jobs', 0)}[/blue]")
    
    return len(final_jobs) > len(initial_jobs)

def test_multiple_jobs():
    """Test saving multiple jobs like scrapers do."""
    console.print("\n[bold blue]🧪 Testing Multiple Job Save (Scraper Simulation)[/bold blue]")
    
    # Get database
    db = get_job_db("Nirajan Khadka")
    
    # Create multiple test jobs (like scrapers return)
    test_jobs = [
        {
            'title': 'Senior Data Analyst',
            'company': 'Tech Corp',
            'location': 'Vancouver, BC',
            'url': 'https://techcorp.com/careers/senior-data-analyst',
            'summary': 'Senior data analyst position',
            'posted_date': '2025-06-18',
            'source': 'eluta',
            'found_by_keyword': 'data analyst'
        },
        {
            'title': 'Business Intelligence Analyst',
            'company': 'Finance Inc',
            'location': 'Calgary, AB',
            'url': 'https://finance-inc.com/careers/bi-analyst',
            'summary': 'BI analyst position',
            'posted_date': '2025-06-18',
            'source': 'eluta',
            'found_by_keyword': 'business intelligence'
        },
        {
            'title': 'Data Scientist',
            'company': 'AI Startup',
            'location': 'Montreal, QC',
            'url': 'https://ai-startup.com/careers/data-scientist',
            'summary': 'Data scientist position',
            'posted_date': '2025-06-18',
            'source': 'eluta',
            'found_by_keyword': 'data scientist'
        }
    ]
    
    # Check initial state
    initial_count = len(db.get_all_jobs())
    console.print(f"[cyan]Initial jobs: {initial_count}[/cyan]")
    
    # Simulate what the fixed scraping functions do
    console.print(f"[cyan]💾 Saving {len(test_jobs)} jobs to database...[/cyan]")
    saved_count = 0
    duplicate_count = 0
    
    for job in test_jobs:
        if db.add_job(job):
            saved_count += 1
        else:
            duplicate_count += 1
    
    # Check final state
    final_count = len(db.get_all_jobs())
    console.print(f"[cyan]Final jobs: {final_count}[/cyan]")
    
    # Report results (like the fixed functions do)
    console.print(f"[bold green]✅ Scraping simulation found {len(test_jobs)} jobs![/bold green]")
    console.print(f"[green]💾 Saved {saved_count} new jobs to database ({duplicate_count} duplicates skipped)[/green]")
    console.print("[cyan]💡 Check the dashboard to see your scraped jobs[/cyan]")
    
    return saved_count > 0

def main():
    """Run all tests."""
    console.print("[bold green]🚀 Database Save Fix Test Suite[/bold green]")
    console.print("[cyan]This tests the fix for scraped jobs not being saved to database[/cyan]\n")
    
    try:
        # Test 1: Single job save
        test1_success = test_database_save()
        
        # Test 2: Multiple job save (scraper simulation)
        test2_success = test_multiple_jobs()
        
        # Summary
        console.print(f"\n[bold]🎯 Test Results Summary:[/bold]")
        console.print(f"[{'green' if test1_success else 'red'}]Test 1 (Single Job): {'✅ PASS' if test1_success else '❌ FAIL'}[/{'green' if test1_success else 'red'}]")
        console.print(f"[{'green' if test2_success else 'red'}]Test 2 (Multiple Jobs): {'✅ PASS' if test2_success else '❌ FAIL'}[/{'green' if test2_success else 'red'}]")
        
        if test1_success and test2_success:
            console.print("\n[bold green]🎉 ALL TESTS PASSED! Database save fix is working![/bold green]")
            console.print("[cyan]💡 The scraped jobs should now appear in the dashboard[/cyan]")
            console.print("[cyan]🌐 Visit http://localhost:8002 to see the jobs[/cyan]")
        else:
            console.print("\n[bold red]❌ Some tests failed. Database save fix needs more work.[/bold red]")
    
    except Exception as e:
        console.print(f"[red]❌ Test error: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
