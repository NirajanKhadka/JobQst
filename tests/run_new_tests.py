#!/usr/bin/env python3
"""
Test runner for improved JobLens test suite
Runs the new tests that align with current architecture.
"""

import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def run_test_category(test_path: str, description: str):
    """Run a specific test category and return results."""
    console.print(f"\n[bold blue]🧪 Running: {description}[/bold blue]")
    
    try:
        # Run pytest for the specific test
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Parse results
        lines = result.stdout.split('\n')
        passed = sum(1 for line in lines if " PASSED" in line)
        failed = sum(1 for line in lines if " FAILED" in line)
        errors = sum(1 for line in lines if " ERROR" in line)
        
        status = "✅ PASS" if result.returncode == 0 else "❌ FAIL"
        
        return {
            "name": description,
            "status": status,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "output": result.stdout,
            "error_output": result.stderr
        }
        
    except Exception as e:
        return {
            "name": description,
            "status": "❌ ERROR",
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "output": "",
            "error_output": str(e)
        }

def main():
    """Main test runner."""
    console.print(Panel.fit(
        "[bold green]JobLens Test Suite Runner[/bold green]\n"
        "Running tests for current architecture",
        title="🧪 Test Suite"
    ))
    
    # Define test categories
    test_categories = [
        ("tests/unit/test_duckdb_core.py", "DuckDB Core Database"),
        ("tests/unit/test_profile_management.py", "Profile Management"),
        ("tests/integration/test_jobspy_integration.py", "JobSpy Integration"),
        ("tests/unit/test_get_job_db.py", "Database Factory"),
        ("tests/unit/test_main.py", "Basic Imports"),
        ("tests/integration/test_jobspy_standalone.py", "JobSpy Standalone"),
    ]
    
    results = []
    
    # Run each test category
    for test_path, description in test_categories:
        if Path(test_path).exists():
            result = run_test_category(test_path, description)
            results.append(result)
        else:
            console.print(f"[yellow]⚠️ Skipping {description} - file not found: {test_path}[/yellow]")
    
    # Display results table
    table = Table(title="Test Results Summary")
    table.add_column("Test Category", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Passed", style="green")
    table.add_column("Failed", style="red")
    table.add_column("Errors", style="red")
    
    total_passed = 0
    total_failed = 0
    total_errors = 0
    
    for result in results:
        table.add_row(
            result["name"],
            result["status"],
            str(result["passed"]),
            str(result["failed"]),
            str(result["errors"])
        )
        total_passed += result["passed"]
        total_failed += result["failed"]
        total_errors += result["errors"]
    
    console.print(table)
    
    # Summary
    console.print(f"\n[bold]Total Results:[/bold]")
    console.print(f"✅ Passed: {total_passed}")
    console.print(f"❌ Failed: {total_failed}")
    console.print(f"🔥 Errors: {total_errors}")
    
    # Show detailed output for failed tests
    for result in results:
        if result["status"] != "✅ PASS":
            console.print(f"\n[red]❌ Failed Test Details: {result['name']}[/red]")
            if result["error_output"]:
                console.print(f"[red]Error Output:[/red]")
                console.print(result["error_output"][:500] + "..." if len(result["error_output"]) > 500 else result["error_output"])
    
    # Overall status
    if total_failed == 0 and total_errors == 0:
        console.print("\n[bold green]🎉 All tests passed![/bold green]")
        return 0
    else:
        console.print(f"\n[bold red]❌ {total_failed + total_errors} tests failed or had errors[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())