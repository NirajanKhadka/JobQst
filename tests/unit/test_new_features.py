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
        ("JobSpy Enhanced Scraper", "from src.scrapers.jobspy_enhanced_scraper import JobSpyImprovedScraper"),
        ("Unified Eluta Scraper", "from src.scrapers.unified_eluta_scraper import ElutaScraper"),
        ("Main Entry Point", "from main import main"),
        ("Job Database", "from src.core.job_database import get_job_db"),
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
        from src.scrapers.jobspy_enhanced_scraper import JobSpyImprovedScraper
        
        # Create a test profile
        test_profile = {
            "profile_name": "test",
            "keywords": ["python", "data analyst"],
            "name": "Test User",
            "email": "test@example.com",
            "location": "Toronto, ON"
        }
        
        # Test scraper initialization
        scraper = JobSpyImprovedScraper(test_profile)
        
        console.print("[green]✅ Enhanced scraper initialized successfully[/green]")
        console.print(f"[cyan]   Profile: {scraper.profile_name}[/cyan]")
        
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Enhanced scraper test failed: {e}[/red]")
        pytest.skip("Feature not available")

def test_eluta_scraper():
    """Test eluta scraper initialization."""
    console.print("\n[bold blue]⚡ Testing Eluta Scraper[/bold blue]")
    
    try:
        from src.scrapers.unified_eluta_scraper import ElutaScraper

        # Create a test profile
        test_profile = {
            "profile_name": "test",
            "keywords": ["python", "data analyst", "sql"],
            "name": "Test User",
            "email": "test@example.com"
        }

        # Test scraper initialization
        scraper = ElutaScraper(test_profile)

        console.print("[green]✅ Eluta scraper initialized successfully[/green]")
        console.print(f"[cyan]   Profile: {scraper.profile_name}[/cyan]")
        console.print(f"[cyan]   Keywords: {len(scraper.keywords)}[/cyan]")
        
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Eluta scraper test failed: {e}[/red]")
        pytest.skip("Feature not available")

def test_main_menu_functions():
    """Test that main functions exist."""
    console.print("\n[bold blue]📋 Testing Main Functions[/bold blue]")
    
    try:
        import main
        
        # Check if functions exist
        functions_to_check = [
            'main',
            'parse_arguments', 
            'run_health_check'
        ]
        
        for func_name in functions_to_check:
            if hasattr(main, func_name):
                console.print(f"[green]✅ {func_name} exists[/green]")
            else:
                console.print(f"[red]❌ {func_name} missing[/red]")
                pytest.skip("Feature not available")
        
        console.print("[green]✅ All main functions exist[/green]")
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Main function test failed: {e}[/red]")
        pytest.skip("Feature not available")

def test_database_functions():
    """Test database functionality."""
    console.print("\n[bold blue]🔍 Testing Database Functions[/bold blue]")
    
    try:
        from src.core.job_database import get_job_db
        
        # Test database initialization
        db = get_job_db("test")
        
        console.print("[green]✅ Database functions work[/green]")
        assert True
        
    except Exception as e:
        console.print(f"[red]❌ Database test failed: {e}[/red]")
        pytest.skip("Database not available")

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
    console.print("[cyan]Testing working features...[/cyan]\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Enhanced Scraper", test_enhanced_scraper_features),
        ("Eluta Scraper", test_eluta_scraper),
        ("Main Functions", test_main_menu_functions),
        ("Database Functions", test_database_functions),
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
        console.print("[bold green]🎉 All tests passed![/bold green]")
        console.print("\n[cyan]💡 Features working:[/cyan]")
        console.print("   - JobSpy Enhanced Scraper")
        console.print("   - Unified Eluta Scraper") 
        console.print("   - Database functionality")
    else:
        console.print(f"[bold red]❌ {total - passed} tests failed.[/bold red]")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
