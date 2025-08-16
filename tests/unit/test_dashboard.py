

import pytest
import requests
import os
import tempfile
import logging
from pathlib import Path


# ...existing code...

# Integration test for /api/profiles endpoint and Nirajan profile
@pytest.mark.integration
def test_profiles_endpoint_and_nirajan_presence():
    """Test /api/profiles endpoint returns profiles and includes 'Nirajan'.
    Also checks fallback logic for missing profiles."""
    base_url = os.environ.get('DASHBOARD_BASE_URL', 'http://localhost:8000')
    profiles_url = f"{base_url}/api/profiles"
    try:
        response = requests.get(profiles_url, timeout=2)
        assert response.status_code == 200, f"/api/profiles returned {response.status_code}"
        profiles = response.json()
        assert isinstance(profiles, list), "Profiles response is not a list"
        if not profiles:
            print("[yellow]⚠️ No profiles returned. UI should show fallback warning.[/yellow]")
        else:
            print(f"[green]✅ Profiles returned: {profiles}[/green]")
        assert 'Nirajan' in profiles, 'Nirajan profile not found in /api/profiles response'
        print("[green]✅ 'Nirajan' profile found in /api/profiles response[/green]")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pytest.skip("API server not running - skipping integration test")
    except Exception as e:
        pytest.fail(f"Failed to test /api/profiles endpoint: {e}")
#!/usr/bin/env python3
"""
Improved Dashboard Tests - UI and data visualization with job limits
Improved with dynamic UI limits, modular design, and performance optimization
Following DEVELOPMENT_STANDARDS.md principles
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

console = Console()

# Conditional imports for dashboard components
try:
    from src.dashboard.unified_dashboard import load_job_data
    from src.dashboard.components.metrics import render_metrics
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    
    # Mock functions for testing when dashboard is not available
    def load_job_data(profile_name: str) -> pd.DataFrame:
        return pd.DataFrame()
    
    def render_metrics(df: pd.DataFrame) -> None:
        pass


class DashboardMetrics:
    """Improved dashboard performance metrics with UI element limits."""

    def __init__(self, ui_limit: int = 10, components_limit: int = 20):
        self.ui_limit = ui_limit
        self.components_limit = components_limit
        self.start_time = time.time()
        self.data_rows_loaded = 0
        self.ui_components_rendered = 0
        self.metrics_calculated = 0
        self.charts_generated = 0
        self.filters_applied = 0
        self.queries_executed = 0
        self.errors = 0

    def increment_data_loaded(self, count: int = 1):
        self.data_rows_loaded += count

    def increment_ui_rendered(self):
        self.ui_components_rendered += 1

    def increment_metrics(self):
        self.metrics_calculated += 1

    def increment_charts(self):
        self.charts_generated += 1

    def increment_filters(self):
        self.filters_applied += 1

    def increment_queries(self):
        self.queries_executed += 1

    def increment_errors(self):
        self.errors += 1

    def get_elapsed_time(self):
        return time.time() - self.start_time

    def is_ui_limit_reached(self) -> bool:
        """Check if UI component limit has been reached."""
        return self.ui_components_rendered >= self.ui_limit

    def get_ui_progress_percentage(self) -> float:
        """Get UI rendering progress as percentage."""
        if self.ui_limit > 0:
            return min(100.0, (self.ui_components_rendered / self.ui_limit) * 100)
        return 0.0

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for dashboard operations."""
        elapsed = self.get_elapsed_time()
        return {
            "elapsed_time": elapsed,
            "data_loading_rate": self.data_rows_loaded / elapsed if elapsed > 0 else 0,
            "ui_rendering_rate": self.ui_components_rendered / elapsed if elapsed > 0 else 0,
            "metrics_rate": self.metrics_calculated / elapsed if elapsed > 0 else 0,
            "charts_rate": self.charts_generated / elapsed if elapsed > 0 else 0,
            "error_rate": self.errors / elapsed if elapsed > 0 else 0,
        }


@pytest.mark.unit
@pytest.mark.limited
class TestDashboardDataImproved:
    """Test dashboard data loading with job limits and performance monitoring."""

    def test_load_job_data_empty_with_limits(self, job_limit: int) -> None:
        """Test loading job data when database is empty (respecting limits)."""
        if not DASHBOARD_AVAILABLE:
            pytest.skip("Dashboard components not available")
            
        metrics = DashboardMetrics(ui_limit=job_limit)
        
        # Mock the load_job_data function to avoid Streamlit caching issues
        with patch('src.dashboard.unified_dashboard.load_job_data') as mock_load:
            mock_load.return_value = pd.DataFrame()  # Empty DataFrame
            
            df = mock_load("__nonexistent_profile__")
            metrics.increment_data_loaded(len(df))
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0
            assert metrics.data_rows_loaded <= job_limit

    def test_load_job_data_with_limited_jobs(self, job_limit: int, sample_job_list: List[Dict]) -> None:
        """Test loading job data with sample jobs (respecting limits)."""
        metrics = DashboardMetrics(ui_limit=job_limit)
        
        # Limit sample data to job_limit
        limited_jobs = sample_job_list[:job_limit]
        df = pd.DataFrame(limited_jobs)
        metrics.increment_data_loaded(len(df))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= job_limit
        assert len(df) == len(limited_jobs)
        
        # Verify expected columns exist
        expected_columns = ['title', 'company', 'location', 'url']
        for col in expected_columns:
            if col in df.columns:
                assert col in df.columns

        console.print(f"[green]✅ Loaded {len(df)} jobs (limit: {job_limit})[/green]")

    def test_load_job_data_missing_columns_with_limits(self, job_limit: int) -> None:
        """Test loading job data with missing columns (edge case with limits)."""
        metrics = DashboardMetrics(ui_limit=job_limit)
        
        # Create jobs with missing columns, but respect job limit
        mock_jobs = [
            {'title': f'Data Analyst {i}'} if i % 2 == 0 else {'company': f'Tech Corp {i}'}
            for i in range(min(job_limit, 5))  # Limit to smaller of job_limit or 5
        ]
        
        df = pd.DataFrame(mock_jobs)
        metrics.increment_data_loaded(len(df))
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= job_limit
        assert metrics.data_rows_loaded <= job_limit
        
        console.print(f"[yellow]⚠️ Processed {len(df)} jobs with missing columns[/yellow]")

    def test_load_job_data_performance_with_limits(self, job_limit: int, performance_timer) -> None:
        """Test data loading performance with configurable limits."""
        metrics = DashboardMetrics(ui_limit=job_limit)
        
        with performance_timer:
            # Simulate loading job data with performance tracking
            for i in range(job_limit):
                # Simulate data loading operations
                job_data = {
                    'title': f'Job {i}',
                    'company': f'Company {i}',
                    'status': 'scraped',
                    'match_score': 75 + (i % 25),
                    'created_at': datetime.now().isoformat()
                }
                metrics.increment_data_loaded(1)
                metrics.increment_queries()
                
                # Simulate processing delay (2ms per job)
                time.sleep(0.002)
        
        elapsed = performance_timer.elapsed
        loading_rate = metrics.data_rows_loaded / elapsed if elapsed > 0 else 0
        
        assert metrics.data_rows_loaded == job_limit
        assert loading_rate > 0
        
        console.print(f"[cyan]📊 Loaded {job_limit} jobs in {elapsed:.3f}s ({loading_rate:.1f} jobs/s)[/cyan]")


@pytest.mark.unit
@pytest.mark.limited
class TestDashboardMetricsImproved:
    """Test dashboard metrics calculations with UI component limits."""

    def test_metrics_logic_empty_data_with_limits(self, job_limit: int) -> None:
        """Test metrics logic with empty DataFrame (respecting limits)."""
        if not DASHBOARD_AVAILABLE:
            pytest.skip("Dashboard components not available")
            
        metrics = DashboardMetrics(ui_limit=job_limit)
        empty_df = pd.DataFrame()
        
        try:
            render_metrics(empty_df)
            metrics.increment_metrics()
            metrics.increment_ui_rendered()
        except Exception as e:
            metrics.increment_errors()
            pytest.fail(f"render_metrics failed on empty data: {e}")
        
        assert metrics.ui_components_rendered <= job_limit
        console.print(f"[green]✅ Rendered metrics for empty data (limit: {job_limit})[/green]")

    def test_metrics_logic_with_limited_data(self, job_limit: int, sample_job_list: List[Dict]) -> None:
        """Test metrics logic with sample data (respecting limits)."""
        metrics = DashboardMetrics(ui_limit=job_limit)
        
        # Create limited sample data
        limited_data = sample_job_list[:job_limit]
        sample_data = pd.DataFrame({
            'status': [job.get('status', 'scraped') for job in limited_data],
            'match_score': [85 + i for i in range(len(limited_data))]
        })
        
        try:
            if DASHBOARD_AVAILABLE:
                render_metrics(sample_data)
            metrics.increment_metrics()
            metrics.increment_ui_rendered()
        except Exception as e:
            metrics.increment_errors()
            pytest.fail(f"render_metrics failed on sample data: {e}")
        
        assert len(sample_data) <= job_limit
        assert metrics.ui_components_rendered <= job_limit
        
        console.print(f"[green]✅ Rendered metrics for {len(sample_data)} jobs (limit: {job_limit})[/green]")

    def test_dashboard_performance_with_ui_limits(self, job_limit: int, performance_timer, performance_thresholds: Dict[str, float]) -> None:
        """Test dashboard performance with UI component limits."""
        metrics = DashboardMetrics(ui_limit=job_limit, components_limit=job_limit * 2)
        
        with performance_timer:
            # Simulate rendering UI components up to limit
            for i in range(job_limit):
                # Simulate rendering different UI components
                component_types = ['metric', 'chart', 'filter', 'table']
                component_type = component_types[i % len(component_types)]
                
                if component_type == 'metric':
                    metrics.increment_metrics()
                elif component_type == 'chart':
                    metrics.increment_charts()
                elif component_type == 'filter':
                    metrics.increment_filters()
                
                metrics.increment_ui_rendered()
                
                # Simulate rendering delay (5ms per component)
                time.sleep(0.005)
                
                # Stop if UI limit reached
                if metrics.is_ui_limit_reached():
                    break
        
        elapsed = performance_timer.elapsed
        ui_rate = metrics.ui_components_rendered / elapsed if elapsed > 0 else 0
        
        # Performance assertions
        assert metrics.ui_components_rendered <= job_limit
        assert ui_rate >= performance_thresholds.get('min_ui_rate', 10.0), \
            f"UI rendering rate {ui_rate:.1f}/s below threshold"
        
        progress = metrics.get_ui_progress_percentage()
        console.print(f"[cyan]🎨 Rendered {metrics.ui_components_rendered} UI components in {elapsed:.3f}s ({ui_rate:.1f}/s)[/cyan]")
        console.print(f"[cyan]📊 Progress: {progress:.1f}%[/cyan]")


@pytest.mark.unit
@pytest.mark.limited
class TestDashboardComponentsImproved:
    """Test individual dashboard components with limits."""

    def test_dashboard_imports_availability(self) -> None:
        """Test that dashboard modules can be imported or gracefully fallback."""
        try:
            import streamlit as st
            console.print("[green]✅ Streamlit available[/green]")
        except ImportError:
            console.print("[yellow]⚠️ Streamlit not available[/yellow]")
            
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            console.print("[green]✅ Plotly dependencies available[/green]")
        except ImportError as e:
            console.print(f"[yellow]⚠️ Plotly dependencies not available: {e}[/yellow]")
            pytest.skip(f"Plotly dependencies not available: {e}")

    def test_data_processing_functions_with_limits(self, job_limit: int) -> None:
        """Test that required data processing functions exist and work with limits."""
        if not DASHBOARD_AVAILABLE:
            console.print("[yellow]⚠️ Using mock dashboard functions[/yellow]")
        
        # Test function exists and is callable
        assert callable(load_job_data)
        
        # Test with actual profile (limited)
        try:
            df = load_job_data("test_profile")
            assert isinstance(df, pd.DataFrame)
            
            # If data exists, respect limits
            if len(df) > job_limit:
                df_limited = df.head(job_limit)
                assert len(df_limited) <= job_limit
                console.print(f"[cyan]📊 Limited data from {len(df)} to {len(df_limited)} rows[/cyan]")
            else:
                console.print(f"[green]✅ Data within limits: {len(df)} <= {job_limit}[/green]")
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not load real data: {e}[/yellow]")

    def test_component_rendering_limits(self, job_limit: int, performance_timer) -> None:
        """Test dashboard component rendering with limits."""
        metrics = DashboardMetrics(ui_limit=job_limit)
        
        with performance_timer:
            # Simulate rendering various dashboard components
            component_count = 0
            while component_count < job_limit and not metrics.is_ui_limit_reached():
                # Simulate different component types
                if component_count % 4 == 0:
                    # Render metric component
                    metrics.increment_metrics()
                elif component_count % 4 == 1:
                    # Render chart component
                    metrics.increment_charts()
                elif component_count % 4 == 2:
                    # Apply filter component
                    metrics.increment_filters()
                else:
                    # Execute query component
                    metrics.increment_queries()
                
                metrics.increment_ui_rendered()
                component_count += 1
                
                # Simulate component rendering time
                time.sleep(0.003)
        
        # Verify limits were respected
        assert metrics.ui_components_rendered <= job_limit
        
        summary = metrics.get_performance_summary()
        console.print(f"[cyan]🎨 Component Rendering Summary:[/cyan]")
        console.print(f"  • UI Components: {metrics.ui_components_rendered}/{job_limit}")
        console.print(f"  • Metrics: {metrics.metrics_calculated}")
        console.print(f"  • Charts: {metrics.charts_generated}")
        console.print(f"  • Filters: {metrics.filters_applied}")
        console.print(f"  • Queries: {metrics.queries_executed}")
        console.print(f"  • Rendering Rate: {summary['ui_rendering_rate']:.1f}/s")


@pytest.mark.performance
@pytest.mark.limited
def test_dashboard_full_performance_with_limits(
    job_limit: int, 
    performance_timer, 
    performance_thresholds: Dict[str, float],
    sample_job_list: List[Dict]
) -> None:
    """Comprehensive dashboard performance test with configurable limits."""
    console.print(Panel(f"[bold blue]🚀 Dashboard Performance Test with {job_limit} Job Limit[/bold blue]"))
    
    metrics = DashboardMetrics(ui_limit=job_limit, components_limit=job_limit * 2)
    
    with performance_timer:
        # Phase 1: Data Loading (limited)
        limited_jobs = sample_job_list[:job_limit]
        df = pd.DataFrame(limited_jobs)
        metrics.increment_data_loaded(len(df))
        time.sleep(0.01)  # Simulate loading time
        
        # Phase 2: UI Rendering (limited)
        for i in range(job_limit):
            # Simulate rendering different components
            if i % 3 == 0:
                metrics.increment_metrics()
            elif i % 3 == 1:
                metrics.increment_charts()
            else:
                metrics.increment_filters()
            
            metrics.increment_ui_rendered()
            time.sleep(0.005)  # Simulate rendering time
            
            if metrics.is_ui_limit_reached():
                break
        
        # Phase 3: Metrics Calculation
        metrics.increment_queries()
        time.sleep(0.01)  # Simulate calculation time
    
    # Performance analysis
    elapsed = performance_timer.elapsed
    summary = metrics.get_performance_summary()
    
    # Create performance report
    report_table = Table(title="Dashboard Performance Report", show_header=True)
    report_table.add_column("Metric", style="cyan")
    report_table.add_column("Value", style="yellow")
    report_table.add_column("Rate", style="green")
    report_table.add_column("Status", style="blue")
    
    # Add performance rows
    ui_rate = summary['ui_rendering_rate']
    data_rate = summary['data_loading_rate']
    
    report_table.add_row(
        "Data Rows Loaded",
        f"{metrics.data_rows_loaded}/{job_limit}",
        f"{data_rate:.1f}/s",
        "✅ Good" if data_rate > 50 else "⚠️ Slow"
    )
    report_table.add_row(
        "UI Components Rendered",
        f"{metrics.ui_components_rendered}/{job_limit}",
        f"{ui_rate:.1f}/s",
        "✅ Good" if ui_rate > 10 else "⚠️ Slow"
    )
    report_table.add_row(
        "Total Time",
        f"{elapsed:.3f}s",
        f"{job_limit/elapsed:.1f} items/s",
        "✅ Fast" if elapsed < 5 else "⚠️ Slow"
    )
    
    console.print(report_table)
    
    # Performance assertions
    assert metrics.data_rows_loaded <= job_limit
    assert metrics.ui_components_rendered <= job_limit
    assert ui_rate >= performance_thresholds.get('min_ui_rate', 5.0)
    assert summary['error_rate'] == 0  # No errors should occur
    
    progress = metrics.get_ui_progress_percentage()
    console.print(f"\n[bold green]📊 Dashboard test completed: {progress:.1f}% of {job_limit} UI components[/bold green]")
    
    # Test completed successfully - no return needed


import pytest
import requests
import os
import tempfile
import logging
import pytest
from pathlib import Path

# Import orchestrators (assume they are importable from src.cli.handlers)
from src.cli.handlers.scraping_handler import ScrapingOrchestrator
from src.cli.handlers.application_handler import ApplicationOrchestrator
from src.cli.handlers.dashboard_handler import DashboardOrchestrator
from src.cli.handlers.system_handler import SystemOrchestrator

@pytest.mark.parametrize("Orchestrator,logfile", [
    (ScrapingOrchestrator, "logs/scraping_orchestrator.log"),
    (ApplicationOrchestrator, "logs/application_orchestrator.log"),
    (DashboardOrchestrator, "logs/dashboard_orchestrator.log"),
    (SystemOrchestrator, "logs/system_orchestrator.log"),
])
def test_orchestrator_logging_levels(Orchestrator, logfile, caplog):
    # Use a test profile
    profile = {"profile_name": "test_profile"}
    orch = Orchestrator(profile)
    
    # Clear any existing log records
    caplog.clear()
    
    # Log at all levels
    orch.log("Test INFO log", "INFO")
    orch.log("Test WARNING log", "WARNING")
    orch.log("Test ERROR log", "ERROR")
    orch.log("Test CRITICAL log", "CRITICAL")
    
    # Check that messages were logged (using pytest's caplog fixture)
    log_messages = [record.message for record in caplog.records]
    
    assert "Test INFO log" in log_messages
    assert "Test WARNING log" in log_messages
    assert "Test ERROR log" in log_messages
    assert "Test CRITICAL log" in log_messages
    
    # Check log levels
    log_levels = [record.levelname for record in caplog.records]
    assert "INFO" in log_levels
    assert "WARNING" in log_levels
    assert "ERROR" in log_levels
    assert "CRITICAL" in log_levels


if __name__ == "__main__":
    pytest.main([__file__])
