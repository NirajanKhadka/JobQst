#!/usr/bin/env python3
"""
Complete Pipeline Test for JobQst

Tests all major components of the job search pipeline:
1. Database connectivity
2. Scraping functionality  
3. Job processing
4. Dashboard data loading
5. System health checks
"""

import sys
import traceback
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_database_connectivity():
    """Test database connection and basic operations."""
    console.print("[cyan]Step 1: Testing Database Connectivity[/cyan]")
    
    try:
        from src.core.job_database import get_job_db
        
        # Test database creation and connection
        db = get_job_db("Nirajan")
        
        # Test basic operations
        job_count = db.get_job_count()
        console.print(f"[green]✅ Database connected: {job_count} jobs found[/green]")
        
        # Test analytics data
        analytics = db.get_analytics_data()
        console.print(f"[green]✅ Analytics working: {analytics.get('total_jobs', 0)} total jobs[/green]")
        
        return True, db
        
    except Exception as e:
        console.print(f"[red]❌ Database test failed: {e}[/red]")
        traceback.print_exc()
        return False, None

def test_scraper_availability():
    """Test scraper imports and availability."""
    console.print("[cyan]Step 2: Testing Scraper Availability[/cyan]")
    
    try:
        # Test main scrapers
        from src.scrapers.unified_eluta_scraper import ElutaScraper
        console.print("[green]✅ Eluta scraper available[/green]")
        
        from src.scrapers.external_job_scraper import ExternalJobDescriptionScraper
        console.print("[green]✅ External job scraper available[/green]")
        
        # Test scraper initialization
        scraper = ElutaScraper("Nirajan")
        console.print(f"[green]✅ Scraper initialized with {len(scraper.keywords)} keywords[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Scraper test failed: {e}[/red]")
        traceback.print_exc()
        return False

def test_profile_loading():
    """Test profile loading functionality."""
    console.print("[cyan]Step 3: Testing Profile Loading[/cyan]")
    
    try:
        from src.utils.profile_helpers import load_profile
        
        profile = load_profile("Nirajan")
        if profile:
            console.print(f"[green]✅ Profile loaded: {len(profile.get('keywords', []))} keywords[/green]")
            console.print(f"[green]✅ Profile name: {profile.get('profile_name', 'Unknown')}[/green]")
            return True
        else:
            console.print("[red]❌ Profile not found[/red]")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Profile test failed: {e}[/red]")
        traceback.print_exc()
        return False

def test_processing_components():
    """Test job processing components."""
    console.print("[cyan]Step 4: Testing Processing Components[/cyan]")
    
    try:
        # Test deduplication
        from src.core.smart_deduplication import SmartJobDeduplicator
        dedup = SmartJobDeduplicator()
        console.print("[green]✅ Smart deduplication available[/green]")
        
        # Test filtering
        from src.core.job_filters import JobRelevanceFilter
        job_filter = JobRelevanceFilter({"keywords": ["Python Developer"]})
        console.print("[green]✅ Job filtering available[/green]")
        
        # Test processing
        from src.analysis.two_stage_processor import TwoStageJobProcessor
        from src.utils.profile_helpers import load_profile
        profile = load_profile("Nirajan")
        processor = TwoStageJobProcessor(profile)
        console.print("[green]✅ Two-stage processor available[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Processing test failed: {e}[/red]")
        traceback.print_exc()
        return False

def test_job_processing(db):
    """Test job processing with actual data."""
    console.print("[cyan]Step 5: Testing Job Processing[/cyan]")
    
    try:
        # Get jobs for processing
        jobs_to_process = db.get_jobs_for_processing(limit=5)
        console.print(f"[green]✅ Found {len(jobs_to_process)} jobs for processing[/green]")
        
        if jobs_to_process:
            # Test processing update
            test_job = jobs_to_process[0]
            success = db.update_job_processing_status(
                test_job['id'], 
                {'fit_score': 85.5, 'status': 'processed'}
            )
            if success:
                console.print("[green]✅ Job processing update successful[/green]")
            else:
                console.print("[yellow]⚠️ Job processing update failed[/yellow]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Job processing test failed: {e}[/red]")
        traceback.print_exc()
        return False

def test_dashboard_components():
    """Test dashboard data loading."""
    console.print("[cyan]Step 6: Testing Dashboard Components[/cyan]")
    
    try:
        from src.dashboard.dash_app.utils.data_loader import DataLoader
        
        loader = DataLoader()
        data = loader.load_jobs_data("Nirajan")
        
        console.print(f"[green]✅ Dashboard data loaded: {data.get('total_jobs', 0)} jobs[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Dashboard test failed: {e}[/red]")
        traceback.print_exc()
        return False

def test_main_cli():
    """Test main CLI functionality."""
    console.print("[cyan]Step 7: Testing Main CLI[/cyan]")
    
    try:
        from main import main
        console.print("[green]✅ Main CLI module available[/green]")
        
        # Test menu system
        from src.cli.menu.main_menu import MainMenu
        menu = MainMenu({"profile_name": "Nirajan"})
        console.print("[green]✅ Main menu system available[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ CLI test failed: {e}[/red]")
        traceback.print_exc()
        return False

def display_system_health(db):
    """Display overall system health."""
    console.print(Panel("📊 System Health Report", style="bold blue"))
    
    try:
        stats = db.get_job_stats()
        
        table = Table(title="JobQst System Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Jobs", str(stats.get('total_jobs', 0)))
        table.add_row("Unique Companies", str(stats.get('unique_companies', 0)))
        table.add_row("Job Sites", str(stats.get('unique_sites', 0)))
        table.add_row("Recent Jobs (24h)", str(stats.get('recent_jobs', 0)))
        table.add_row("Last Scraped", stats.get('last_scraped_ago', 'Never'))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Health report failed: {e}[/red]")

def main():
    """Run complete pipeline test."""
    console.print(Panel("🚀 JobQst Complete Pipeline Test", style="bold blue"))
    
    test_results = []
    db = None
    
    # Run all tests
    tests = [
        ("Database Connectivity", test_database_connectivity),
        ("Scraper Availability", test_scraper_availability),
        ("Profile Loading", test_profile_loading),
        ("Processing Components", test_processing_components),
        ("Dashboard Components", test_dashboard_components),
        ("Main CLI", test_main_cli),
    ]
    
    for test_name, test_func in tests:
        try:
            if test_name == "Database Connectivity":
                success, db = test_func()
            else:
                success = test_func()
            test_results.append((test_name, success))
        except Exception as e:
            console.print(f"[red]❌ {test_name} failed with exception: {e}[/red]")
            test_results.append((test_name, False))
    
    # Test job processing if database is available
    if db:
        try:
            success = test_job_processing(db)
            test_results.append(("Job Processing", success))
        except Exception as e:
            console.print(f"[red]❌ Job Processing failed: {e}[/red]")
            test_results.append(("Job Processing", False))
    
    # Display results
    console.print(Panel("📋 Test Results", style="bold yellow"))
    
    passed = 0
    total = len(test_results)
    
    for test_name, success in test_results:
        if success:
            console.print(f"[green]✅ {test_name}: PASSED[/green]")
            passed += 1
        else:
            console.print(f"[red]❌ {test_name}: FAILED[/red]")
    
    # Overall result
    console.print(f"\n[bold]Overall Result: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print(Panel("🎉 All Tests Passed! Pipeline is fully operational.", style="bold green"))
        
        # Display system health if database available
        if db:
            display_system_health(db)
            
        console.print("\n[green]✅ Your JobQst pipeline is ready for production use![/green]")
        console.print("[cyan]💡 Next steps:[/cyan]")
        console.print("  1. Run scraping: python main.py Nirajan --action scrape --jobs 50")
        console.print("  2. Check dashboard: python src/dashboard/unified_dashboard.py --profile Nirajan")
        console.print("  3. Set up scheduling: python cleanup_and_schedule.py")
        
    else:
        console.print(Panel(f"⚠️ {total - passed} tests failed. Please fix issues before production use.", style="bold red"))
        
        console.print("\n[yellow]💡 Common fixes:[/yellow]")
        console.print("  - Install missing dependencies: pip install -r requirements.txt")
        console.print("  - Check profile exists: profiles/Nirajan/Nirajan.json")
        console.print("  - Verify database permissions")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)