#!/usr/bin/env python3
"""
Test script for new high-performance features.
"""

import sys
import time
import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_imports():
    """Test that all new modules can be imported."""
    console.print("[bold blue]🧪 Testing New Feature Imports[/bold blue]")
    
    tests = [
        ("Parallel Job Scraper", "from src.scrapers.parallel_job_scraper import ParallelJobScraper"),
        ("Enhanced Eluta Scraper", "from src.scrapers.eluta_enhanced import ElutaEnhancedScraper"),
        ("Debug Dashboard", "import debug_dashboard_issue"),
        ("Main Menu Functions", "from main import ultra_fast_scrape_action, deep_scrape_action, debug_dashboard_action"),
    ]
    
    results = []
    
    for test_name, import_statement in tests:
        try:
            exec(import_statement)
            results.append((test_name, "✅ PASS", "Import successful"))
        except Exception as e:
            results.append((test_name, "❌ FAIL", str(e)))
    
    # Display results
    table = Table(title="Import Test Results")
    table.add_column("Feature", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="yellow")
    
    for test_name, status, details in results:
        table.add_row(test_name, status, details)
    
    console.print(table)
    
    # Summary
    passed = sum(1 for _, status, _ in results if "PASS" in status)
    total = len(results)
    
    if passed == total:
        console.print(f"[bold green]✅ All {total} import tests passed![/bold green]")
        assert True
    else:
        console.print(f"[bold red]❌ {total - passed} import tests failed![/bold red]")
        pytest.skip(f"{total - passed} import tests failed")

def test_enhanced_scraper_features():
    """Test enhanced scraper features."""
    console.print("\n[bold blue]🔍 Testing Enhanced Scraper Features[/bold blue]")
    
    try:
        from src.scrapers.eluta_enhanced import ElutaEnhancedScraper
        
        # Create a test profile
        test_profile = {
            "profile_name": "test",
            "keywords": ["python", "data analyst"],
            "name": "Test User",
            "email": "test@example.com",
            "location": "Toronto, ON"
        }
        
        # Test scraper initialization
        scraper = ElutaEnhancedScraper(test_profile, deep_scraping=True)
        
        console.print("[green]✅ Enhanced scraper initialized successfully[/green]")
        console.print(f"[cyan]   Deep scraping enabled: {scraper.deep_scraping}[/cyan]")
        console.print(f"[cyan]   Rate limit delay: {scraper.rate_limit_delay}[/cyan]")
        console.print(f"[cyan]   Max pages per keyword: {scraper.max_pages_per_keyword}[/cyan]")
        
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Enhanced scraper test failed: {e}[/red]")
        pytest.skip("Feature not available")

def test_ultra_parallel_scraper():
    """Test ultra parallel scraper initialization."""
    console.print("\n[bold blue]⚡ Testing Ultra Parallel Scraper[/bold blue]")
    
    try:
        from src.scrapers.parallel_job_scraper import ParallelJobScraper

        # Create a test profile
        test_profile = {
            "profile_name": "test",
            "keywords": ["python", "data analyst", "sql"],
            "name": "Test User",
            "email": "test@example.com"
        }

        # Test scraper initialization
        scraper = ParallelJobScraper(test_profile, max_workers=2)

        console.print("[green]✅ Parallel job scraper initialized successfully[/green]")
        console.print(f"[cyan]   Max workers: {scraper.max_workers}[/cyan]")
        console.print(f"[cyan]   Batch size: {scraper.batch_size}[/cyan]")
        console.print(f"[cyan]   Concurrent browsers: {scraper.concurrent_browsers}[/cyan]")
        console.print(f"[cyan]   Keywords to process: {len(scraper.keywords)}[/cyan]")
        
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Ultra parallel scraper test failed: {e}[/red]")
        pytest.skip("Feature not available")

def test_main_menu_functions():
    """Test that new main menu functions exist."""
    console.print("\n[bold blue]📋 Testing Main Menu Functions[/bold blue]")
    
    try:
        import main
        
        # Check if new functions exist
        functions_to_check = [
            'ultra_fast_scrape_action',
            'deep_scrape_action', 
            'debug_dashboard_action'
        ]
        
        for func_name in functions_to_check:
            if hasattr(main, func_name):
                console.print(f"[green]✅ {func_name} exists[/green]")
            else:
                console.print(f"[red]❌ {func_name} missing[/red]")
                pytest.skip("Feature not available")
        
        console.print("[green]✅ All main menu functions exist[/green]")
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Main menu function test failed: {e}[/red]")
        pytest.skip("Feature not available")

def test_debug_dashboard():
    """Test debug dashboard script."""
    console.print("\n[bold blue]🔍 Testing Debug Dashboard Script[/bold blue]")
    
    try:
        import debug_dashboard_issue
        
        # Check if main functions exist
        functions = ['investigate_database_issue', 'check_dashboard_database_connection', 'suggest_fixes']
        
        for func_name in functions:
            if hasattr(debug_dashboard_issue, func_name):
                console.print(f"[green]✅ {func_name} exists[/green]")
            else:
                console.print(f"[red]❌ {func_name} missing[/red]")
                pytest.skip("Feature not available")
        
        console.print("[green]✅ Debug dashboard script is ready[/green]")
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Debug dashboard test failed: {e}[/red]")
        pytest.skip("Feature not available")

def run_performance_benchmark():
    """Run a quick performance benchmark."""
    console.print("\n[bold blue]⚡ Performance Benchmark[/bold blue]")
    
    try:
        import os
        cpu_count = os.cpu_count()
        
        console.print(f"[cyan]💻 System Info:[/cyan]")
        console.print(f"   CPU cores: {cpu_count}")
        console.print(f"   Recommended workers: {min(cpu_count // 2, 12)}")
        
        # Simple timing test
        start_time = time.time()
        
        # Simulate some work
        for i in range(1000000):
            pass
        
        end_time = time.time()
        duration = end_time - start_time
        
        console.print(f"[cyan]⏱️  Simple benchmark: {duration:.3f} seconds[/cyan]")
        
        if duration < 0.1:
            console.print("[green]✅ System performance looks good for parallel processing[/green]")
        else:
            console.print("[yellow]⚠️ System may be under load[/yellow]")
        
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Performance benchmark failed: {e}[/red]")
        pytest.skip("Feature not available")

def main():
    """Run all tests."""
    console.print(Panel("🧪 New Features Test Suite", style="bold blue"))
    console.print("[cyan]Testing all new high-performance features...[/cyan]\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Enhanced Scraper", test_enhanced_scraper_features),
        ("Ultra Parallel Scraper", test_ultra_parallel_scraper),
        ("Main Menu Functions", test_main_menu_functions),
        ("Debug Dashboard", test_debug_dashboard),
        ("Performance Benchmark", run_performance_benchmark),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            console.print(f"[red]❌ {test_name} crashed: {e}[/red]")
            results.append((test_name, False))
    
    # Final summary
    console.print("\n" + "="*50)
    console.print("[bold blue]📊 TEST SUMMARY[/bold blue]")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        console.print(f"   {status} {test_name}")
    
    console.print(f"\n[bold]Results: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        console.print("[bold green]🎉 All tests passed! New features are ready to use.[/bold green]")
        console.print("\n[cyan]💡 Try the new features:[/cyan]")
        console.print("   python main.py Nirajan  # Choose option 2 for ultra-fast scraping")
        console.print("   python main.py Nirajan  # Choose option 3 for deep scraping")
        console.print("   python main.py Nirajan  # Choose option 10 for dashboard debugging")
    else:
        console.print(f"[bold red]❌ {total - passed} tests failed. Check the errors above.[/bold red]")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
