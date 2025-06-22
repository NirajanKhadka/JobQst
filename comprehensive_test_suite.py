#!/usr/bin/env python3
"""
Comprehensive Test Suite for AutoJobAgent
Tests all major components and improvements made during the optimization process.
"""

import sys
import time
import json
import traceback
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID
from datetime import datetime

console = Console()

class TestResult:
    """Container for test results."""
    
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration

class ComprehensiveTestSuite:
    """
    Comprehensive test suite for validating all system improvements.
    """
    
    def __init__(self):
        """Initialize the test suite."""
        self.results: List[TestResult] = []
        self.test_profile = "test_profile"
        
    def run_all_tests(self) -> bool:
        """
        Run all tests and return overall success status.
        
        Returns:
            True if all tests pass, False otherwise
        """
        console.print(Panel("🧪 Comprehensive Test Suite", style="bold blue"))
        console.print("[cyan]Testing all system components and improvements...[/cyan]")
        
        test_categories = [
            ("Database Tests", self._test_database_functionality),
            ("Error Tolerance Tests", self._test_error_tolerance),
            ("Scraping Optimization Tests", self._test_scraping_optimization),
            ("Application Flow Tests", self._test_application_flow),
            ("Dashboard Tests", self._test_dashboard_functionality),
            ("Integration Tests", self._test_integration),
            ("Performance Tests", self._test_performance)
        ]
        
        with Progress() as progress:
            main_task = progress.add_task("[cyan]Running Tests", total=len(test_categories))
            
            for category_name, test_func in test_categories:
                console.print(f"\n[bold yellow]🔍 {category_name}[/bold yellow]")
                
                try:
                    test_func()
                    console.print(f"[green]✅ {category_name} completed[/green]")
                except Exception as e:
                    console.print(f"[red]❌ {category_name} failed: {e}[/red]")
                    self.results.append(TestResult(category_name, False, str(e)))
                
                progress.update(main_task, advance=1)
        
        # Display results
        self._display_test_results()
        
        # Return overall success
        passed_tests = sum(1 for r in self.results if r.passed)
        total_tests = len(self.results)
        
        return passed_tests == total_tests
    
    def _test_database_functionality(self):
        """Test database functionality and improvements."""
        console.print("[cyan]  Testing database operations...[/cyan]")
        
        # Test database initialization
        start_time = time.time()
        try:
            from job_database import get_job_db
            db = get_job_db(self.test_profile)
            duration = time.time() - start_time
            self.results.append(TestResult("Database Initialization", True, "Database initialized successfully", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Database Initialization", False, str(e), duration))
            return
        
        # Test job addition with duplicate detection
        start_time = time.time()
        try:
            # Use a unique job with timestamp to avoid conflicts with previous test runs
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            test_job = {
                'title': f'Test Software Developer {timestamp}',
                'company': f'Test Company Inc {timestamp}',
                'location': 'Toronto, ON',
                'url': f'https://test.com/job/{timestamp}',
                'summary': 'Test job description for validation',
                'site': 'test'
            }
            
            # Add job first time
            added1 = db.add_job(test_job)
            # Try to add same job again
            added2 = db.add_job(test_job)
            
            if added1 and not added2:
                duration = time.time() - start_time
                self.results.append(TestResult("Duplicate Detection", True, "Duplicate detection working correctly", duration))
            else:
                duration = time.time() - start_time
                self.results.append(TestResult("Duplicate Detection", False, f"Duplicate detection failed: {added1}, {added2}", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Duplicate Detection", False, str(e), duration))
        
        # Test database statistics
        start_time = time.time()
        try:
            stats = db.get_stats()
            if isinstance(stats, dict) and 'total_jobs' in stats:
                duration = time.time() - start_time
                self.results.append(TestResult("Database Statistics", True, f"Stats retrieved: {stats['total_jobs']} jobs", duration))
            else:
                duration = time.time() - start_time
                self.results.append(TestResult("Database Statistics", False, "Invalid stats format", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Database Statistics", False, str(e), duration))
    
    def _test_error_tolerance(self):
        """Test enhanced error tolerance and robustness."""
        console.print("[cyan]  Testing error tolerance mechanisms...[/cyan]")
        
        # Test enhanced error tolerance import
        start_time = time.time()
        try:
            from src.utils.enhanced_error_tolerance import with_retry, RobustOperations
            # Test the functions exist
            assert callable(with_retry)
            robust_ops = RobustOperations()
            duration = time.time() - start_time
            self.results.append(TestResult("Error Tolerance Import", True, "Error tolerance functions imported successfully", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Error Tolerance Import", False, str(e), duration))
    
    def _test_scraping_optimization(self):
        """Test scraping optimization improvements."""
        console.print("[cyan]  Testing scraping optimization...[/cyan]")
        
        # Test optimized scraping coordinator import
        start_time = time.time()
        try:
            from src.utils.scraping_coordinator import OptimizedScrapingCoordinator
            coordinator = OptimizedScrapingCoordinator("test_profile")
            duration = time.time() - start_time
            self.results.append(TestResult("Scraping Coordinator", True, "Coordinator initialized successfully", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Scraping Coordinator", False, str(e), duration))
            return
        
        # Test job quality calculation
        start_time = time.time()
        try:
            test_job = {
                'title': 'Senior Python Developer',
                'company': 'Tech Corp',
                'location': 'Toronto, ON',
                'url': 'https://example.com/job/123',
                'summary': 'We are looking for an experienced Python developer to join our team.',
                'posted_date': 'today'
            }
            
            quality_score = coordinator._calculate_job_quality(test_job)
            if 0.0 <= quality_score <= 1.0:
                duration = time.time() - start_time
                self.results.append(TestResult("Job Quality Calculation", True, f"Quality score: {quality_score:.2f}", duration))
            else:
                duration = time.time() - start_time
                self.results.append(TestResult("Job Quality Calculation", False, f"Invalid quality score: {quality_score}", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Job Quality Calculation", False, str(e), duration))
    
    def _test_application_flow(self):
        """Test application flow optimization."""
        console.print("[cyan]  Testing application flow optimization...[/cyan]")
        
        # Test application flow optimizer import
        start_time = time.time()
        try:
            from src.ats.application_flow_optimizer import ApplicationFlowOptimizer
            optimizer = ApplicationFlowOptimizer("test_profile")
            duration = time.time() - start_time
            self.results.append(TestResult("Application Flow Optimizer", True, "Optimizer initialized successfully", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Application Flow Optimizer", False, str(e), duration))
            return
        
        # Test ATS pattern loading
        start_time = time.time()
        try:
            patterns = optimizer.ats_patterns
            if isinstance(patterns, dict) and 'workday' in patterns:
                duration = time.time() - start_time
                self.results.append(TestResult("ATS Pattern Loading", True, f"Loaded {len(patterns)} ATS patterns", duration))
            else:
                duration = time.time() - start_time
                self.results.append(TestResult("ATS Pattern Loading", False, "Invalid ATS patterns", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("ATS Pattern Loading", False, str(e), duration))
    
    def _test_dashboard_functionality(self):
        """Test dashboard functionality."""
        console.print("[cyan]  Testing dashboard functionality...[/cyan]")
        
        # Test dashboard API import
        start_time = time.time()
        try:
            from src.dashboard.api import app
            duration = time.time() - start_time
            self.results.append(TestResult("Dashboard API Import", True, "Dashboard API imported successfully", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Dashboard API Import", False, str(e), duration))
            return
        
        # Test dashboard endpoints (basic check)
        start_time = time.time()
        try:
            # Check if the app object exists and has routes
            if hasattr(app, 'routes') and len(app.routes) > 0:
                duration = time.time() - start_time
                self.results.append(TestResult("Dashboard Routes", True, f"Found {len(app.routes)} routes", duration))
            else:
                duration = time.time() - start_time
                self.results.append(TestResult("Dashboard Routes", False, "No routes found", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Dashboard Routes", False, str(e), duration))
    
    def _test_integration(self):
        """Test integration between components."""
        console.print("[cyan]  Testing component integration...[/cyan]")
        
        # Test profile loading
        start_time = time.time()
        try:
            import utils
            profiles = utils.get_available_profiles()
            duration = time.time() - start_time
            self.results.append(TestResult("Profile Integration", True, f"Found {len(profiles)} profiles", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Profile Integration", False, str(e), duration))
        
        # Test utils functionality
        start_time = time.time()
        try:
            from utils import clean_text, generate_job_hash
            # Test clean_text function
            test_text = "  Test   Job   Title  "
            cleaned = clean_text(test_text)
            # Test generate_job_hash function
            test_job = {'title': 'Test Job', 'company': 'Test Company', 'url': 'https://test.com'}
            job_hash = generate_job_hash(test_job)
            
            if cleaned == "Test Job Title" and len(job_hash) > 0:
                duration = time.time() - start_time
                self.results.append(TestResult("Utils Integration", True, "Utility functions working correctly", duration))
            else:
                duration = time.time() - start_time
                self.results.append(TestResult("Utils Integration", False, "Utility functions not working as expected", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Utils Integration", False, str(e), duration))
    
    def _test_performance(self):
        """Test performance improvements."""
        console.print("[cyan]  Testing performance improvements...[/cyan]")
        
        # Test database performance
        start_time = time.time()
        try:
            from job_database import get_job_db
            db = get_job_db(self.test_profile)
            
            # Add multiple jobs and measure time
            test_jobs = []
            for i in range(10):
                test_jobs.append({
                    'title': f'Test Job {i}',
                    'company': f'Company {i}',
                    'location': 'Toronto, ON',
                    'url': f'https://test.com/job/{i}',
                    'summary': f'Test job description {i}',
                    'site': 'test'
                })
            
            add_start = time.time()
            for job in test_jobs:
                db.add_job(job)
            add_duration = time.time() - add_start
            
            duration = time.time() - start_time
            if add_duration < 5.0:  # Should be fast
                self.results.append(TestResult("Database Performance", True, f"Added 10 jobs in {add_duration:.2f}s", duration))
            else:
                self.results.append(TestResult("Database Performance", False, f"Too slow: {add_duration:.2f}s", duration))
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult("Database Performance", False, str(e), duration))
    
    def _display_test_results(self):
        """Display comprehensive test results."""
        console.print(f"\n[bold blue]📊 Test Results Summary[/bold blue]")
        
        # Create results table
        table = Table(title="Test Results")
        table.add_column("Test Name", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Duration", justify="right", style="yellow")
        table.add_column("Message", style="white")
        
        passed_count = 0
        total_duration = 0.0
        
        for result in self.results:
            status = "[green]✅ PASS[/green]" if result.passed else "[red]❌ FAIL[/red]"
            duration_str = f"{result.duration:.3f}s"
            
            table.add_row(
                result.name,
                status,
                duration_str,
                result.message[:80] + "..." if len(result.message) > 80 else result.message
            )
            
            if result.passed:
                passed_count += 1
            total_duration += result.duration
        
        console.print(table)
        
        # Summary statistics
        total_tests = len(self.results)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0
        
        console.print(f"\n[bold]📈 Summary Statistics:[/bold]")
        console.print(f"[green]✅ Passed: {passed_count}/{total_tests} ({success_rate:.1f}%)[/green]")
        console.print(f"[red]❌ Failed: {total_tests - passed_count}/{total_tests}[/red]")
        console.print(f"[yellow]⏱️  Total Duration: {total_duration:.2f}s[/yellow]")
        
        if success_rate == 100:
            console.print(f"\n[bold green]🎉 All tests passed! System is ready for production.[/bold green]")
        elif success_rate >= 80:
            console.print(f"\n[bold yellow]⚠️ Most tests passed. Some issues need attention.[/bold yellow]")
        else:
            console.print(f"\n[bold red]❌ Multiple test failures. System needs significant fixes.[/bold red]")

def main():
    """Run the comprehensive test suite."""
    test_suite = ComprehensiveTestSuite()
    success = test_suite.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
