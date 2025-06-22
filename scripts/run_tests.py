"""
Test runner for the enhanced click-and-popup job scraping system.
Runs comprehensive tests for all components including click-and-popup functionality,
popup handling, multi-browser context support, and job filtering.
"""

import sys
import os
import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run_test_suite(test_file: str, description: str) -> bool:
    """Run a specific test suite and return success status."""
    try:
        console.print(f"[cyan]🧪 Running {description}...[/cyan]")
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            console.print(f"[green]✅ {description} - PASSED[/green]")
            return True
        else:
            console.print(f"[red]❌ {description} - FAILED[/red]")
            console.print(f"[red]Error output:[/red]")
            console.print(result.stdout)
            console.print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        console.print(f"[red]⏰ {description} - TIMEOUT[/red]")
        return False
    except Exception as e:
        console.print(f"[red]💥 {description} - ERROR: {e}[/red]")
        return False


def check_test_dependencies() -> bool:
    """Check if required test dependencies are available."""
    console.print("[cyan]🔍 Checking test dependencies...[/cyan]")
    
    required_packages = ["pytest", "playwright", "rich"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            console.print(f"[green]✅ {package} - Available[/green]")
        except ImportError:
            console.print(f"[red]❌ {package} - Missing[/red]")
            missing_packages.append(package)
    
    if missing_packages:
        console.print(f"[red]Missing packages: {', '.join(missing_packages)}[/red]")
        console.print("[yellow]Install with: pip install pytest playwright rich[/yellow]")
        return False
    
    return True


def run_all_tests():
    """Run all test suites for the enhanced click-and-popup system."""
    console.clear()
    console.print(Panel("🧪 Enhanced Click-and-Popup Test Suite", style="bold blue"))
    
    # Check dependencies first
    if not check_test_dependencies():
        console.print("[red]❌ Cannot run tests due to missing dependencies[/red]")
        return False
    
    # Define test suites
    test_suites = [
        {
            "file": "tests/test_click_popup_framework.py",
            "description": "Universal Click-and-Popup Framework Tests",
            "critical": True
        },
        {
            "file": "tests/test_job_filters.py", 
            "description": "Job Filtering and Experience Level Detection Tests",
            "critical": True
        },
        {
            "file": "tests/test_comprehensive_scraping.py",
            "description": "Comprehensive Scraping Integration Tests",
            "critical": True
        }
    ]
    
    # Check if test files exist
    missing_files = []
    for suite in test_suites:
        if not Path(suite["file"]).exists():
            missing_files.append(suite["file"])
    
    if missing_files:
        console.print(f"[red]❌ Missing test files: {', '.join(missing_files)}[/red]")
        return False
    
    # Run tests
    results = []
    total_tests = len(test_suites)
    passed_tests = 0
    
    console.print(f"\n[bold]Running {total_tests} test suites...[/bold]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for i, suite in enumerate(test_suites, 1):
            task = progress.add_task(f"[cyan]Test {i}/{total_tests}: {suite['description']}")
            
            success = run_test_suite(suite["file"], suite["description"])
            results.append({
                "suite": suite["description"],
                "file": suite["file"],
                "success": success,
                "critical": suite["critical"]
            })
            
            if success:
                passed_tests += 1
            
            progress.remove_task(task)
    
    # Display results summary
    console.print("\n" + "="*80)
    console.print(Panel("📊 Test Results Summary", style="bold blue"))
    
    # Create results table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test Suite", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Critical", justify="center")
    
    critical_failures = 0
    
    for result in results:
        status = "[green]✅ PASSED[/green]" if result["success"] else "[red]❌ FAILED[/red]"
        critical = "[red]YES[/red]" if result["critical"] else "[yellow]NO[/yellow]"
        
        if not result["success"] and result["critical"]:
            critical_failures += 1
        
        table.add_row(
            result["suite"],
            status,
            critical
        )
    
    console.print(table)
    
    # Overall status
    console.print(f"\n[bold]Overall Results:[/bold]")
    console.print(f"[green]✅ Passed: {passed_tests}/{total_tests}[/green]")
    console.print(f"[red]❌ Failed: {total_tests - passed_tests}/{total_tests}[/red]")
    
    if critical_failures > 0:
        console.print(f"[red]🚨 Critical failures: {critical_failures}[/red]")
        console.print("[red]❌ OVERALL STATUS: FAILED[/red]")
        return False
    elif passed_tests == total_tests:
        console.print("[green]🎉 OVERALL STATUS: ALL TESTS PASSED[/green]")
        return True
    else:
        console.print("[yellow]⚠️ OVERALL STATUS: SOME NON-CRITICAL TESTS FAILED[/yellow]")
        return True


def run_specific_test(test_name: str):
    """Run a specific test suite."""
    test_mapping = {
        "framework": "tests/test_click_popup_framework.py",
        "filters": "tests/test_job_filters.py", 
        "comprehensive": "tests/test_comprehensive_scraping.py"
    }
    
    if test_name not in test_mapping:
        console.print(f"[red]❌ Unknown test: {test_name}[/red]")
        console.print(f"[yellow]Available tests: {', '.join(test_mapping.keys())}[/yellow]")
        return False
    
    test_file = test_mapping[test_name]
    description = f"{test_name.title()} Tests"
    
    console.print(Panel(f"🧪 Running {description}", style="bold blue"))
    
    if not check_test_dependencies():
        return False
    
    return run_test_suite(test_file, description)


def main():
    """Main test runner entry point."""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1].lower()
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
