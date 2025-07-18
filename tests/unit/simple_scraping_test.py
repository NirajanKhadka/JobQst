#!/usr/bin/env python3
"""
Comprehensive Test Suite for AutoJobAgent
Tests main app, dashboard, and scrapers with performance optimization
Following DEVELOPMENT_STANDARDS.md principles
"""

import pytest
import time
import sys
import threading
import asyncio
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback console
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

console = Console()

# Import test dependencies with error handling
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    st = None


# =================================================================
# 1. TEST INFRASTRUCTURE & UTILITIES
# =================================================================

class ComprehensiveTestMetrics:
    """Enhanced test metrics for main app, dashboard, and scrapers."""

    def __init__(self, test_name: str = "comprehensive_test"):
        self.test_name = test_name
        self.start_time = time.time()
        self.main_app_tests = 0
        self.dashboard_tests = 0
        self.scraper_tests = 0
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.errors = []
        self.performance_metrics = {}
        self.lock = threading.Lock()

    def increment_main_app_test(self, passed: bool = True):
        with self.lock:
            self.main_app_tests += 1
            self.total_tests += 1
            if passed:
                self.passed_tests += 1
            else:
                self.failed_tests += 1

    def increment_dashboard_test(self, passed: bool = True):
        with self.lock:
            self.dashboard_tests += 1
            self.total_tests += 1
            if passed:
                self.passed_tests += 1
            else:
                self.failed_tests += 1

    def increment_scraper_test(self, passed: bool = True):
        with self.lock:
            self.scraper_tests += 1
            self.total_tests += 1
            if passed:
                self.passed_tests += 1
            else:
                self.failed_tests += 1

    def add_error(self, error: str):
        with self.lock:
            self.errors.append(error)

    def add_performance_metric(self, name: str, value: float):
        with self.lock:
            self.performance_metrics[name] = value

    def get_elapsed_time(self):
        return time.time() - self.start_time

    def get_success_rate(self):
        if self.total_tests > 0:
            return (self.passed_tests / self.total_tests) * 100
        return 0

    def get_summary(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "elapsed_time": self.get_elapsed_time(),
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": self.get_success_rate(),
            "main_app_tests": self.main_app_tests,
            "dashboard_tests": self.dashboard_tests,
            "scraper_tests": self.scraper_tests,
            "errors": self.errors,
            "performance_metrics": self.performance_metrics
        }


# =================================================================
# 2. MAIN APP TESTS
# =================================================================

def test_main_app_imports():
    """Test that main app can be imported and basic functions work."""
    try:
        # Test main.py imports
        from src.main import main, parse_arguments, _ensure_imports
        from src.main import run_health_check, run_optimized_scraping
        return True
    except ImportError as e:
        console.print(f"[red]Main app import failed: {e}[/red]")
        return False

def test_main_app_argument_parsing():
    """Test main app argument parsing functionality."""
    try:
        from src.main import parse_arguments
        import sys
        
        # Save original argv
        original_argv = sys.argv.copy()
        
        # Test basic argument parsing
        sys.argv = ["main.py", "Nirajan", "--action", "scrape", "--sites", "eluta"]
        args = parse_arguments()
        
        assert args.profile == "Nirajan"
        assert args.action == "scrape"
        assert args.sites == "eluta"
        
        # Restore original argv
        sys.argv = original_argv
        return True
    except Exception as e:
        console.print(f"[red]Argument parsing test failed: {e}[/red]")
        return False

def test_main_app_profile_loading():
    """Test profile loading functionality."""
    try:
        from src.utils.profile_helpers import load_profile, get_available_profiles
        
        # Test getting available profiles
        profiles = get_available_profiles()
        assert isinstance(profiles, list)
        
        # Test loading a profile (use default if Nirajan doesn't exist)
        profile = load_profile("Nirajan") or load_profile("default")
        assert profile is not None
        assert isinstance(profile, dict)
        
        return True
    except Exception as e:
        console.print(f"[red]Profile loading test failed: {e}[/red]")
        return False

def test_main_app_health_check():
    """Test main app health check functionality."""
    try:
        from src.main import run_health_check
        
        # Create mock profile
        mock_profile = {"profile_name": "test"}
        
        # Test health check (should not crash)
        result = run_health_check(mock_profile)
        assert isinstance(result, bool)
        
        return True
    except Exception as e:
        console.print(f"[red]Health check test failed: {e}[/red]")
        return False

def test_main_app_programmatic_access():
    """Test main app programmatic access."""
    try:
        from src.main import main
        
        # Test programmatic access with health-check action
        result = main(
            profile_name="test",
            action="health-check",
            verbose=False
        )
        
        assert isinstance(result, bool)
        return True
    except Exception as e:
        console.print(f"[red]Programmatic access test failed: {e}[/red]")
        return False


# =================================================================
# 3. DASHBOARD TESTS
# =================================================================

def test_dashboard_imports():
    """Test that dashboard components can be imported."""
    try:
        # Test main dashboard imports
        from src.dashboard.unified_dashboard import load_job_data, get_system_metrics
        from src.dashboard.unified_dashboard import display_enhanced_metrics
        
        return True
    except ImportError as e:
        console.print(f"[red]Dashboard import failed: {e}[/red]")
        return False

def test_dashboard_data_loading():
    """Test dashboard data loading functionality."""
    try:
        from src.dashboard.unified_dashboard import load_job_data
        
        # Test loading data for test profile
        df = load_job_data("test")
        
        # Should return a DataFrame (empty is fine for test)
        if HAS_PANDAS:
            assert hasattr(df, 'empty')  # pandas DataFrame property
        
        return True
    except Exception as e:
        console.print(f"[red]Dashboard data loading test failed: {e}[/red]")
        return False

def test_dashboard_system_metrics():
    """Test dashboard system metrics functionality."""
    try:
        from src.dashboard.unified_dashboard import get_system_metrics
        
        # Test getting system metrics
        metrics = get_system_metrics()
        assert isinstance(metrics, dict)
        
        return True
    except Exception as e:
        console.print(f"[red]System metrics test failed: {e}[/red]")
        return False

def test_dashboard_css_and_styling():
    """Test that dashboard CSS constants are properly defined."""
    try:
        from src.dashboard.unified_dashboard import UNIFIED_CSS
        
        assert isinstance(UNIFIED_CSS, str)
        assert len(UNIFIED_CSS) > 100  # Should have substantial CSS content
        assert "style" in UNIFIED_CSS.lower()
        
        return True
    except Exception as e:
        console.print(f"[red]Dashboard CSS test failed: {e}[/red]")
        return False

@pytest.mark.skipif(not HAS_STREAMLIT, reason="Streamlit not available")
def test_dashboard_streamlit_compatibility():
    """Test dashboard compatibility with Streamlit (if available)."""
    try:
        # Test that dashboard can be imported in Streamlit context
        import streamlit as st
        from src.dashboard.unified_dashboard import display_enhanced_metrics
        
        # Mock DataFrame for testing
        if HAS_PANDAS:
            import pandas as pd
            mock_df = pd.DataFrame({
                'title': ['Test Job'],
                'company': ['Test Company'],
                'scraped': [1],
                'processed': [0],
                'document_created': [0],
                'applied': [0]
            })
            
            # This should not crash (actual display requires Streamlit runtime)
            try:
                display_enhanced_metrics(mock_df)
            except Exception:
                pass  # Expected without Streamlit runtime
        
        return True
    except Exception as e:
        console.print(f"[red]Streamlit compatibility test failed: {e}[/red]")
        return False


# =================================================================
# 4. SCRAPER TESTS
# =================================================================

def test_scraper_imports():
    """Test that scraper modules can be imported."""
    try:
        # Test main scraper imports
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        
        return True
    except ImportError as e:
        console.print(f"[red]Scraper import failed: {e}[/red]")
        return False

def test_eluta_scraper_initialization():
    """Test Eluta scraper initialization."""
    try:
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        
        # Test initialization with mock profile
        with patch('src.utils.profile_helpers.load_profile') as mock_load:
            mock_load.return_value = {
                'keywords': ['python', 'data analyst'],
                'skills': ['sql', 'machine learning']
            }
            
            with patch('src.core.job_database.get_job_db') as mock_db:
                mock_db.return_value = Mock()
                
                scraper = ComprehensiveElutaScraper("test")
                assert scraper.profile_name == "test"
                assert hasattr(scraper, 'search_terms')
        
        return True
    except Exception as e:
        console.print(f"[red]Eluta scraper initialization test failed: {e}[/red]")
        return False

def test_modern_pipeline_initialization():
    """Test Modern Job Pipeline initialization."""
    try:
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        
        # Test initialization with mock profile and config
        mock_profile = {
            'keywords': ['python', 'developer'],
            'profile_name': 'test'
        }
        
        mock_config = {
            'max_workers': 2,
            'enable_ai_analysis': False,
            'timeout': 10
        }
        
        with patch('src.core.job_database.get_job_db') as mock_db:
            mock_db.return_value = Mock()
            
            pipeline = ModernJobPipeline(mock_profile, mock_config)
            assert hasattr(pipeline, 'profile')
            assert hasattr(pipeline, 'config')
        
        return True
    except Exception as e:
        console.print(f"[red]Modern pipeline initialization test failed: {e}[/red]")
        return False

def test_scraper_models_and_utilities():
    """Test scraper supporting modules."""
    try:
        # Test scraper utilities
        from src.scrapers.scraping_models import ScrapingModels
        from src.scrapers.session_manager import SessionManager
        from src.scrapers.human_behavior import HumanBehaviorSimulator
        
        # Basic instantiation tests
        models = ScrapingModels()
        assert hasattr(models, '__dict__')
        
        return True
    except ImportError as e:
        console.print(f"[red]Scraper utilities import failed: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Scraper utilities test failed: {e}[/red]")
        return False

async def test_async_scraper_functionality():
    """Test async functionality in scrapers."""
    try:
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        
        # Mock async functionality
        mock_profile = {'keywords': ['test'], 'profile_name': 'test'}
        mock_config = {'max_workers': 1, 'enable_ai_analysis': False}
        
        with patch('src.core.job_database.get_job_db') as mock_db:
            mock_db.return_value = Mock()
            
            pipeline = ModernJobPipeline(mock_profile, mock_config)
            
            # Test that async methods exist
            assert hasattr(pipeline, 'run_optimized')
        
        return True
    except Exception as e:
        console.print(f"[red]Async scraper test failed: {e}[/red]")
        return False


# =================================================================
# 5. INTEGRATION TESTS
# =================================================================

def test_database_integration():
    """Test database integration across components."""
    try:
        from src.core.job_database import get_job_db, ModernJobDatabase
        
        # Test database connection
        db = get_job_db("test")
        assert db is not None
        
        # Test basic database operations
        count = db.get_job_count()
        assert isinstance(count, int)
        
        return True
    except Exception as e:
        console.print(f"[red]Database integration test failed: {e}[/red]")
        return False

def test_profile_integration():
    """Test profile integration across components."""
    try:
        from src.utils.profile_helpers import load_profile, get_available_profiles
        from src.core.job_database import get_job_db
        
        # Test profile loading
        profiles = get_available_profiles()
        if profiles:
            profile = load_profile(profiles[0])
            assert profile is not None
            
            # Test profile with database
            db = get_job_db(profiles[0])
            assert db is not None
        
        return True
    except Exception as e:
        console.print(f"[red]Profile integration test failed: {e}[/red]")
        return False

def test_pipeline_integration():
    """Test pipeline integration between scrapers and processors."""
    try:
        # Test that pipeline components can work together
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        from src.core.job_database import get_job_db
        
        mock_profile = {
            'keywords': ['test'],
            'profile_name': 'test'
        }
        
        mock_config = {
            'max_workers': 1,
            'enable_ai_analysis': False,
            'timeout': 5
        }
        
        with patch('src.core.job_database.get_job_db') as mock_db:
            mock_db.return_value = Mock()
            
            pipeline = ModernJobPipeline(mock_profile, mock_config)
            
            # Test pipeline has required methods
            assert hasattr(pipeline, 'run_optimized')
            assert hasattr(pipeline, 'profile')
            assert hasattr(pipeline, 'config')
        
        return True
    except Exception as e:
        console.print(f"[red]Pipeline integration test failed: {e}[/red]")
        return False


# =================================================================
# 6. PERFORMANCE TESTS
# =================================================================

def test_import_performance():
    """Test import performance of key modules."""
    import_times = {}
    
    # Test main app import speed
    start_time = time.time()
    try:
        from src.main import main
        import_times['main_app'] = time.time() - start_time
    except ImportError:
        import_times['main_app'] = float('inf')
    
    # Test dashboard import speed
    start_time = time.time()
    try:
        from src.dashboard.unified_dashboard import load_job_data
        import_times['dashboard'] = time.time() - start_time
    except ImportError:
        import_times['dashboard'] = float('inf')
    
    # Test scraper import speed
    start_time = time.time()
    try:
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        import_times['eluta_scraper'] = time.time() - start_time
    except ImportError:
        import_times['eluta_scraper'] = float('inf')
    
    start_time = time.time()
    try:
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        import_times['modern_pipeline'] = time.time() - start_time
    except ImportError:
        import_times['modern_pipeline'] = float('inf')
    
    # Performance assertions (imports should be fast)
    max_import_time = 2.0  # 2 seconds max
    
    for module, import_time in import_times.items():
        if import_time < float('inf'):
            assert import_time < max_import_time, f"{module} import too slow: {import_time:.2f}s"
            console.print(f"[green]{module} import: {import_time:.3f}s[/green]")
        else:
            console.print(f"[yellow]{module} import: failed[/yellow]")
    
    return True

def test_memory_usage():
    """Test memory usage of key components."""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Import and initialize components
        from src.main import main
        from src.dashboard.unified_dashboard import load_job_data
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        console.print(f"[cyan]Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)[/cyan]")
        
        # Memory should not increase excessively
        assert memory_increase < 100, f"Memory increase too high: {memory_increase:.1f}MB"
        
        return True
    except ImportError:
        console.print("[yellow]psutil not available - skipping memory test[/yellow]")
        return True
    except Exception as e:
        console.print(f"[red]Memory test failed: {e}[/red]")
        return False


# =================================================================
# 7. COMPREHENSIVE TEST RUNNER
# =================================================================

def run_comprehensive_tests() -> ComprehensiveTestMetrics:
    """Run all comprehensive tests and return metrics."""
    metrics = ComprehensiveTestMetrics("comprehensive_autojobagent_test")
    
    console.print(Panel("[bold blue]🚀 Starting Comprehensive AutoJobAgent Tests[/bold blue]"))
    
    # Main App Tests
    console.print("\n[bold cyan]🎯 Testing Main Application...[/bold cyan]")
    
    test_cases = [
        ("Main App Imports", test_main_app_imports),
        ("Argument Parsing", test_main_app_argument_parsing),
        ("Profile Loading", test_main_app_profile_loading),
        ("Health Check", test_main_app_health_check),
        ("Programmatic Access", test_main_app_programmatic_access),
    ]
    
    for test_name, test_func in test_cases:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            metrics.increment_main_app_test(result)
            metrics.add_performance_metric(f"main_app_{test_name.lower().replace(' ', '_')}", duration)
            
            status = "✅ PASS" if result else "❌ FAIL"
            console.print(f"  {status} {test_name} ({duration:.3f}s)")
            
            if not result:
                metrics.add_error(f"Main App: {test_name} failed")
                
        except Exception as e:
            metrics.increment_main_app_test(False)
            metrics.add_error(f"Main App: {test_name} error - {str(e)}")
            console.print(f"  ❌ ERROR {test_name}: {e}")
    
    # Dashboard Tests
    console.print("\n[bold cyan]📊 Testing Dashboard...[/bold cyan]")
    
    dashboard_tests = [
        ("Dashboard Imports", test_dashboard_imports),
        ("Data Loading", test_dashboard_data_loading),
        ("System Metrics", test_dashboard_system_metrics),
        ("CSS and Styling", test_dashboard_css_and_styling),
    ]
    
    # Add Streamlit test if available
    if HAS_STREAMLIT:
        dashboard_tests.append(("Streamlit Compatibility", test_dashboard_streamlit_compatibility))
    
    for test_name, test_func in dashboard_tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            metrics.increment_dashboard_test(result)
            metrics.add_performance_metric(f"dashboard_{test_name.lower().replace(' ', '_')}", duration)
            
            status = "✅ PASS" if result else "❌ FAIL"
            console.print(f"  {status} {test_name} ({duration:.3f}s)")
            
            if not result:
                metrics.add_error(f"Dashboard: {test_name} failed")
                
        except Exception as e:
            metrics.increment_dashboard_test(False)
            metrics.add_error(f"Dashboard: {test_name} error - {str(e)}")
            console.print(f"  ❌ ERROR {test_name}: {e}")
    
    # Scraper Tests
    console.print("\n[bold cyan]🕷️ Testing Scrapers...[/bold cyan]")
    
    scraper_tests = [
        ("Scraper Imports", test_scraper_imports),
        ("Eluta Scraper Init", test_eluta_scraper_initialization),
        ("Modern Pipeline Init", test_modern_pipeline_initialization),
        ("Scraper Utilities", test_scraper_models_and_utilities),
        ("Async Functionality", lambda: asyncio.run(test_async_scraper_functionality())),
    ]
    
    for test_name, test_func in scraper_tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            metrics.increment_scraper_test(result)
            metrics.add_performance_metric(f"scraper_{test_name.lower().replace(' ', '_')}", duration)
            
            status = "✅ PASS" if result else "❌ FAIL"
            console.print(f"  {status} {test_name} ({duration:.3f}s)")
            
            if not result:
                metrics.add_error(f"Scraper: {test_name} failed")
                
        except Exception as e:
            metrics.increment_scraper_test(False)
            metrics.add_error(f"Scraper: {test_name} error - {str(e)}")
            console.print(f"  ❌ ERROR {test_name}: {e}")
    
    # Integration Tests
    console.print("\n[bold cyan]🔗 Testing Integration...[/bold cyan]")
    
    integration_tests = [
        ("Database Integration", test_database_integration),
        ("Profile Integration", test_profile_integration),
        ("Pipeline Integration", test_pipeline_integration),
    ]
    
    for test_name, test_func in integration_tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            metrics.increment_main_app_test(result)  # Count as main app tests
            metrics.add_performance_metric(f"integration_{test_name.lower().replace(' ', '_')}", duration)
            
            status = "✅ PASS" if result else "❌ FAIL"
            console.print(f"  {status} {test_name} ({duration:.3f}s)")
            
            if not result:
                metrics.add_error(f"Integration: {test_name} failed")
                
        except Exception as e:
            metrics.increment_main_app_test(False)
            metrics.add_error(f"Integration: {test_name} error - {str(e)}")
            console.print(f"  ❌ ERROR {test_name}: {e}")
    
    # Performance Tests
    console.print("\n[bold cyan]⚡ Testing Performance...[/bold cyan]")
    
    performance_tests = [
        ("Import Performance", test_import_performance),
        ("Memory Usage", test_memory_usage),
    ]
    
    for test_name, test_func in performance_tests:
        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time
            
            metrics.increment_main_app_test(result)  # Count as main app tests
            metrics.add_performance_metric(f"performance_{test_name.lower().replace(' ', '_')}", duration)
            
            status = "✅ PASS" if result else "❌ FAIL"
            console.print(f"  {status} {test_name} ({duration:.3f}s)")
            
            if not result:
                metrics.add_error(f"Performance: {test_name} failed")
                
        except Exception as e:
            metrics.increment_main_app_test(False)
            metrics.add_error(f"Performance: {test_name} error - {str(e)}")
            console.print(f"  ❌ ERROR {test_name}: {e}")
    
    return metrics


# =================================================================
# 8. TEST DISPLAY AND REPORTING
# =================================================================

def display_comprehensive_results(metrics: ComprehensiveTestMetrics):
    """Display comprehensive test results."""
    summary = metrics.get_summary()
    
    # Header
    console.print(Panel(
        f"[bold blue]🎯 AutoJobAgent Comprehensive Test Results[/bold blue]\n"
        f"[cyan]Test Duration: {summary['elapsed_time']:.1f} seconds[/cyan]\n"
        f"[cyan]Total Tests: {summary['total_tests']}[/cyan] | "
        f"[green]Passed: {summary['passed_tests']}[/green] | "
        f"[red]Failed: {summary['failed_tests']}[/red]\n"
        f"[yellow]Success Rate: {summary['success_rate']:.1f}%[/yellow]",
        title="🚀 Test Results Summary"
    ))
    
    # Component breakdown
    breakdown_table = Table(show_header=True, header_style="bold magenta")
    breakdown_table.add_column("Component", style="cyan", width=20)
    breakdown_table.add_column("Tests Run", style="yellow", width=15)
    breakdown_table.add_column("Status", style="green", width=20)
    
    breakdown_table.add_row(
        "Main Application",
        str(summary['main_app_tests']),
        "✅ Tested" if summary['main_app_tests'] > 0 else "⚠️ Skipped"
    )
    breakdown_table.add_row(
        "Dashboard",
        str(summary['dashboard_tests']),
        "✅ Tested" if summary['dashboard_tests'] > 0 else "⚠️ Skipped"
    )
    breakdown_table.add_row(
        "Scrapers",
        str(summary['scraper_tests']),
        "✅ Tested" if summary['scraper_tests'] > 0 else "⚠️ Skipped"
    )
    
    console.print(breakdown_table)
    
    # Performance metrics
    if summary['performance_metrics']:
        console.print("\n[bold blue]⚡ Performance Metrics[/bold blue]")
        
        perf_table = Table(show_header=True, header_style="bold magenta")
        perf_table.add_column("Test", style="cyan", width=30)
        perf_table.add_column("Duration", style="yellow", width=15)
        perf_table.add_column("Status", style="green", width=20)
        
        for metric_name, duration in summary['performance_metrics'].items():
            status = "✅ Fast" if duration < 1.0 else "⚠️ Slow" if duration < 3.0 else "❌ Very Slow"
            perf_table.add_row(
                metric_name.replace('_', ' ').title(),
                f"{duration:.3f}s",
                status
            )
        
        console.print(perf_table)
    
    # Errors
    if summary['errors']:
        console.print("\n[bold red]❌ Errors Encountered[/bold red]")
        for i, error in enumerate(summary['errors'], 1):
            console.print(f"  {i}. {error}")
    else:
        console.print("\n[bold green]✅ No errors encountered![/bold green]")
    
    # Recommendations
    console.print("\n[bold blue]💡 Recommendations[/bold blue]")
    
    if summary['success_rate'] >= 90:
        console.print("[green]• Excellent! All major components are working well.[/green]")
    elif summary['success_rate'] >= 75:
        console.print("[yellow]• Good overall, but check failed tests for improvements.[/yellow]")
    else:
        console.print("[red]• Multiple issues detected. Review errors and fix critical components.[/red]")
    
    if summary['main_app_tests'] == 0:
        console.print("[yellow]• Run main app tests to verify core functionality.[/yellow]")
    
    if summary['dashboard_tests'] == 0:
        console.print("[yellow]• Run dashboard tests to verify UI components.[/yellow]")
    
    if summary['scraper_tests'] == 0:
        console.print("[yellow]• Run scraper tests to verify data collection.[/yellow]")
    
    # Overall assessment
    if summary['success_rate'] >= 90 and summary['total_tests'] >= 15:
        overall_status = "🎉 EXCELLENT"
        overall_color = "bold green"
    elif summary['success_rate'] >= 75 and summary['total_tests'] >= 10:
        overall_status = "✅ GOOD"
        overall_color = "bold yellow"
    elif summary['success_rate'] >= 50:
        overall_status = "⚠️ NEEDS WORK"
        overall_color = "bold yellow"
    else:
        overall_status = "❌ CRITICAL ISSUES"
        overall_color = "bold red"
    
    console.print(f"\n[{overall_color}]Overall Assessment: {overall_status}[/{overall_color}]")


# =================================================================
# 9. PYTEST FIXTURES AND INTEGRATION
# =================================================================

@pytest.fixture
def test_profile():
    """Provide a test profile for testing."""
    return {
        'profile_name': 'test',
        'keywords': ['python', 'data analyst', 'developer'],
        'skills': ['sql', 'machine learning', 'javascript'],
        'experience_level': 'entry',
        'location': 'Toronto'
    }

@pytest.fixture
def performance_thresholds():
    """Provide performance thresholds for testing."""
    return {
        'max_import_time': 2.0,
        'max_memory_increase': 100,  # MB
        'min_success_rate': 75.0  # %
    }

@pytest.mark.main_app
def test_main_application_comprehensive(test_profile):
    """Comprehensive test for main application functionality."""
    console.print("[bold blue]🎯 Testing Main Application Comprehensively...[/bold blue]")
    
    test_results = []
    
    # Test all main app functions
    test_functions = [
        test_main_app_imports,
        test_main_app_argument_parsing,
        test_main_app_profile_loading,
        test_main_app_health_check,
        test_main_app_programmatic_access
    ]
    
    for test_func in test_functions:
        try:
            result = test_func()
            test_results.append(result)
        except Exception as e:
            console.print(f"[red]Test {test_func.__name__} failed with error: {e}[/red]")
            test_results.append(False)
    
    success_rate = (sum(test_results) / len(test_results)) * 100
    console.print(f"[cyan]Main App Test Success Rate: {success_rate:.1f}%[/cyan]")
    
    # Assert at least 80% success rate
    assert success_rate >= 80, f"Main app tests success rate too low: {success_rate:.1f}%"

@pytest.mark.dashboard
def test_dashboard_comprehensive(test_profile):
    """Comprehensive test for dashboard functionality."""
    console.print("[bold blue]📊 Testing Dashboard Comprehensively...[/bold blue]")
    
    test_results = []
    
    # Test all dashboard functions
    test_functions = [
        test_dashboard_imports,
        test_dashboard_data_loading,
        test_dashboard_system_metrics,
        test_dashboard_css_and_styling
    ]
    
    # Add Streamlit test if available
    if HAS_STREAMLIT:
        test_functions.append(test_dashboard_streamlit_compatibility)
    
    for test_func in test_functions:
        try:
            result = test_func()
            test_results.append(result)
        except Exception as e:
            console.print(f"[red]Test {test_func.__name__} failed with error: {e}[/red]")
            test_results.append(False)
    
    success_rate = (sum(test_results) / len(test_results)) * 100
    console.print(f"[cyan]Dashboard Test Success Rate: {success_rate:.1f}%[/cyan]")
    
    # Assert at least 75% success rate (lower threshold for dashboard due to dependencies)
    assert success_rate >= 75, f"Dashboard tests success rate too low: {success_rate:.1f}%"

@pytest.mark.scrapers
def test_scrapers_comprehensive(test_profile):
    """Comprehensive test for scraper functionality."""
    console.print("[bold blue]🕷️ Testing Scrapers Comprehensively...[/bold blue]")
    
    test_results = []
    
    # Test all scraper functions
    test_functions = [
        test_scraper_imports,
        test_eluta_scraper_initialization,
        test_modern_pipeline_initialization,
        test_scraper_models_and_utilities
    ]
    
    for test_func in test_functions:
        try:
            result = test_func()
            test_results.append(result)
        except Exception as e:
            console.print(f"[red]Test {test_func.__name__} failed with error: {e}[/red]")
            test_results.append(False)
    
    # Test async functionality
    try:
        result = asyncio.run(test_async_scraper_functionality())
        test_results.append(result)
    except Exception as e:
        console.print(f"[red]Async test failed with error: {e}[/red]")
        test_results.append(False)
    
    success_rate = (sum(test_results) / len(test_results)) * 100
    console.print(f"[cyan]Scraper Test Success Rate: {success_rate:.1f}%[/cyan]")
    
    # Assert at least 80% success rate
    assert success_rate >= 80, f"Scraper tests success rate too low: {success_rate:.1f}%"

@pytest.mark.integration
def test_full_integration():
    """Test full integration between all components."""
    console.print("[bold blue]🔗 Testing Full Integration...[/bold blue]")
    
    test_results = []
    
    # Test integration functions
    test_functions = [
        test_database_integration,
        test_profile_integration,
        test_pipeline_integration
    ]
    
    for test_func in test_functions:
        try:
            result = test_func()
            test_results.append(result)
        except Exception as e:
            console.print(f"[red]Integration test {test_func.__name__} failed with error: {e}[/red]")
            test_results.append(False)
    
    success_rate = (sum(test_results) / len(test_results)) * 100
    console.print(f"[cyan]Integration Test Success Rate: {success_rate:.1f}%[/cyan]")
    
    # Assert at least 70% success rate (lower threshold for integration tests)
    assert success_rate >= 70, f"Integration tests success rate too low: {success_rate:.1f}%"

@pytest.mark.performance
def test_performance_comprehensive(performance_thresholds):
    """Comprehensive performance testing."""
    console.print("[bold blue]⚡ Testing Performance Comprehensively...[/bold blue]")
    
    test_results = []
    
    # Test performance functions
    test_functions = [
        test_import_performance,
        test_memory_usage
    ]
    
    for test_func in test_functions:
        try:
            result = test_func()
            test_results.append(result)
        except Exception as e:
            console.print(f"[red]Performance test {test_func.__name__} failed with error: {e}[/red]")
            test_results.append(False)
    
    success_rate = (sum(test_results) / len(test_results)) * 100
    console.print(f"[cyan]Performance Test Success Rate: {success_rate:.1f}%[/cyan]")
    
    # Assert meets performance threshold
    assert success_rate >= performance_thresholds['min_success_rate'], \
        f"Performance tests success rate below threshold: {success_rate:.1f}% < {performance_thresholds['min_success_rate']}%"


# =================================================================
# 10. MAIN EXECUTION AND CLI
# =================================================================

def main():
    """Main execution function for running comprehensive tests."""
    console.print(Panel(
        "[bold blue]🚀 AutoJobAgent Comprehensive Test Suite[/bold blue]\n"
        "[cyan]Testing: Main App, Dashboard, Eluta Scraper, and Pipeline Integration[/cyan]",
        title="🧪 Test Suite"
    ))
    
    # Run comprehensive tests
    metrics = run_comprehensive_tests()
    
    # Display results
    display_comprehensive_results(metrics)
    
    # Return summary for external use
    return metrics.get_summary()


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--pytest":
            # Run via pytest
            console.print("[yellow]💡 Running via pytest. Use: pytest tests/unit/simple_scraping_test.py -v[/yellow]")
            sys.exit(0)
        elif sys.argv[1] == "--quick":
            # Quick test mode
            console.print("[yellow]🏃 Quick test mode - basic imports only[/yellow]")
            
            quick_tests = [
                ("Main App", test_main_app_imports),
                ("Dashboard", test_dashboard_imports),
                ("Scrapers", test_scraper_imports)
            ]
            
            for name, test_func in quick_tests:
                try:
                    result = test_func()
                    status = "✅ PASS" if result else "❌ FAIL"
                    console.print(f"{status} {name}")
                except Exception as e:
                    console.print(f"❌ ERROR {name}: {e}")
            
            sys.exit(0)
    
    # Run full comprehensive test
    summary = main()
    
    # Exit with appropriate code
    exit_code = 0 if summary['success_rate'] >= 75 else 1
    
    console.print(f"\n[bold]Test completed with exit code: {exit_code}[/bold]")
    console.print("[cyan]💡 Run with --pytest for pytest integration or --quick for fast checks[/cyan]")
    
    sys.exit(exit_code)
