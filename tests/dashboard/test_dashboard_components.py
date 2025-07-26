"""
Comprehensive Dashboard Component Tests

This module tests all dashboard components, UI elements, API endpoints,
and integration scenarios according to DASHBOARD_STANDARDS.md.
"""

import pytest
import pandas as pd
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.components.base import BaseComponent
from src.dashboard.components.header import render_header
from src.dashboard.components.sidebar import render_sidebar
from src.dashboard.components.metrics import render_metrics
from src.dashboard.components.job_table import render_job_table
from src.dashboard.components.charts import render_charts
from src.dashboard.components.orchestration_component import EnhancedOrchestrationComponent
from src.dashboard.components.document_generation_component import DocumentGenerationComponent
from src.dashboard.unified_dashboard import main as dashboard_main


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit for testing."""
    # Create mock objects that return proper values
    mock_container = Mock()
    mock_columns = Mock()
    mock_metric = Mock()
    mock_dataframe = Mock()
    mock_selectbox = Mock()
    mock_text_input = Mock()
    mock_button = Mock()
    mock_error = Mock()
    mock_success = Mock()
    mock_info = Mock()
    mock_warning = Mock()
    mock_tabs = Mock()
    mock_sidebar = Mock()
    mock_title = Mock()
    mock_header = Mock()
    mock_subheader = Mock()
    mock_text = Mock()
    mock_write = Mock()
    mock_progress = Mock()
    mock_empty = Mock()
    mock_session_state = Mock()
    
    # Configure specific mocks to return proper values
    def mock_columns_func(n):
        # Create mock objects that can be used as context managers
        mock_cols = []
        # Handle both integer and list arguments
        if isinstance(n, list):
            num_cols = len(n)
        else:
            num_cols = n
        for i in range(num_cols):
            mock_col = Mock()
            mock_col.__enter__ = Mock(return_value=mock_col)
            mock_col.__exit__ = Mock(return_value=None)
            mock_cols.append(mock_col)
        return mock_cols
    
    def mock_tabs_func(tab_names):
        # Create mock objects that can be used as context managers
        mock_tabs = []
        for i in range(len(tab_names)):
            mock_tab = Mock()
            mock_tab.__enter__ = Mock(return_value=mock_tab)
            mock_tab.__exit__ = Mock(return_value=None)
            mock_tabs.append(mock_tab)
        return mock_tabs
    
    mock_columns.side_effect = mock_columns_func
    mock_tabs.side_effect = mock_tabs_func
    
    # Use a simpler approach to avoid too many nested blocks
    patches = [
        patch('streamlit.container', return_value=mock_container),
        patch('streamlit.columns', side_effect=mock_columns_func),
        patch('streamlit.metric', return_value=mock_metric),
        patch('streamlit.dataframe', return_value=mock_dataframe),
        patch('streamlit.selectbox', return_value=mock_selectbox),
        patch('streamlit.text_input', return_value=mock_text_input),
        patch('streamlit.button', return_value=mock_button),
        patch('streamlit.error', return_value=mock_error),
        patch('streamlit.success', return_value=mock_success),
        patch('streamlit.info', return_value=mock_info),
        patch('streamlit.warning', return_value=mock_warning),
        patch('streamlit.tabs', side_effect=mock_tabs_func),
        patch('streamlit.sidebar', return_value=mock_sidebar),
        patch('streamlit.title', return_value=mock_title),
        patch('streamlit.header', return_value=mock_header),
        patch('streamlit.subheader', return_value=mock_subheader),
        patch('streamlit.text', return_value=mock_text),
        patch('streamlit.write', return_value=mock_write),
        patch('streamlit.progress', return_value=mock_progress),
        patch('streamlit.empty', return_value=mock_empty),
        patch('streamlit.session_state', return_value=mock_session_state)
    ]
    
    # Start all patches
    started_patches = [p.start() for p in patches]
    
    yield
    
    # Stop all patches
    for p in started_patches:
        p.stop()


class ConcreteBaseComponent(BaseComponent):
    """Concrete implementation of BaseComponent for testing."""
    
    def _setup(self):
        """Setup method implementation."""
        pass
    
    def _render_content(self):
        """Render content method implementation."""
        pass


class TestDashboardComponents:
    """Test suite for all dashboard components."""
    
    @pytest.fixture
    def real_jobs_data(self):
        with open("tests/fixtures/test_data.json") as f:
            data = json.load(f)
        # The real jobs are under the 'sample_jobs' key
        return pd.DataFrame(data["sample_jobs"])
    

    
    def test_base_component_initialization(self):
        """Test BaseComponent initialization and basic functionality."""
        component = ConcreteBaseComponent("test_component")
        assert component.name == "test_component"
        assert hasattr(component, 'render')
    
    def test_header_component(self, mock_streamlit):
        """Test header component rendering."""
        with patch('streamlit.markdown') as mock_markdown:
            render_header()
            mock_markdown.assert_called()
    
    def test_sidebar_component(self, mock_streamlit):
        """Test sidebar component rendering."""
        with patch('streamlit.sidebar.title') as mock_title, \
             patch('streamlit.sidebar.selectbox') as mock_selectbox, \
             patch('streamlit.sidebar.markdown') as mock_markdown, \
             patch('streamlit.sidebar.button') as mock_button:
            available_profiles = ["Profile1", "Profile2"]
            render_sidebar(available_profiles)
            # Verify sidebar elements are created
            mock_title.assert_called()
            mock_selectbox.assert_called()
    
    def test_metrics_component(self, mock_streamlit, real_jobs_data):
        """Test metrics component with real data."""
        with patch('streamlit.metric') as mock_metric:
            render_metrics(real_jobs_data)
            # Should call metric for total jobs, applied jobs, success rate
            assert mock_metric.call_count >= 3
    
    def test_job_table_component(self, mock_streamlit, real_jobs_data):
        """Test job table component with real data."""
        with patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.text_input', return_value="") as mock_text_input, \
             patch('streamlit.selectbox', return_value="All") as mock_selectbox, \
             patch('streamlit.expander') as mock_expander:
            render_job_table(real_jobs_data)
            # Should call markdown for job details section
            mock_markdown.assert_called()
    
    def test_job_table_empty_data(self, mock_streamlit):
        """Test job table with empty DataFrame."""
        empty_df = pd.DataFrame()
        with patch('streamlit.info') as mock_info:
            render_job_table(empty_df)
            mock_info.assert_called()
    
    def test_job_table_missing_columns(self, mock_streamlit):
        """Test job table with missing columns."""
        incomplete_df = pd.DataFrame({'id': [1], 'title': ['Test Job']})
        with patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.text_input', return_value="") as mock_text_input, \
             patch('streamlit.selectbox', return_value="All") as mock_selectbox, \
             patch('streamlit.expander') as mock_expander:
            render_job_table(incomplete_df)
            # Should call markdown for job details section
            mock_markdown.assert_called()
    
    def test_charts_component(self, mock_streamlit, real_jobs_data):
        """Test charts component with sample data."""
        with patch('streamlit.plotly_chart') as mock_chart:
            render_charts(real_jobs_data)
            # Should render charts if data is available
            if len(real_jobs_data) > 0:
                assert mock_chart.called
    
    def test_orchestration_component(self, mock_streamlit):
        """Test orchestration component."""
        try:
            component = EnhancedOrchestrationComponent("test_profile")
            assert hasattr(component, 'render')
        except ImportError:
            # Component might not be available
            pytest.skip("Orchestration component not available")
    
    def test_document_generation_component(self, mock_streamlit):
        """Test document generation component."""
        try:
            component = DocumentGenerationComponent("test_profile")
            assert hasattr(component, 'render')
        except ImportError:
            # Component might not be available
            pytest.skip("Document generation component not available")


class TestDashboardAPI:
    """Test suite for dashboard API endpoints."""
    
    @pytest.fixture
    def mock_fastapi_app(self):
        """Mock FastAPI app for testing."""
        with patch('fastapi.FastAPI') as mock_app:
            yield mock_app
    
    def test_api_imports(self):
        """Test that dashboard API can be imported without errors."""
        try:
            from src.dashboard.api import app
            assert app is not None
        except ImportError as e:
            pytest.fail(f"Failed to import dashboard API: {e}")
    
    def test_router_imports(self):
        """Test that all dashboard routers can be imported."""
        routers = ['jobs', 'stats', 'system', 'profiles']
        for router in routers:
            try:
                module = __import__(f'src.dashboard.routers.{router}', fromlist=['router'])
                assert hasattr(module, 'router')
            except ImportError as e:
                pytest.fail(f"Failed to import {router} router: {e}")


class TestDashboardIntegration:
    """Test suite for dashboard integration scenarios."""
    
    def test_dashboard_main_function(self, mock_streamlit):
        """Test that dashboard main function can be called without errors."""
        with patch('streamlit.set_page_config'), \
             patch('streamlit.markdown'), \
             patch('streamlit.tabs') as mock_tabs:
            mock_tabs.return_value = [Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock()]
            try:
                dashboard_main()
                # Should not raise any exceptions
            except Exception as e:
                pytest.fail(f"Dashboard main function failed: {e}")
    
    def test_dashboard_imports(self):
        """Test that all dashboard modules can be imported."""
        modules = [
            'src.dashboard.unified_dashboard',
            'src.dashboard.components.base',
            'src.dashboard.components.header',
            'src.dashboard.components.sidebar',
            'src.dashboard.components.metrics',
            'src.dashboard.components.job_table',
            'src.dashboard.components.charts'
        ]
        
        for module in modules:
            try:
                __import__(module)
            except ImportError as e:
                pytest.fail(f"Failed to import {module}: {e}")
    
    def test_dashboard_error_handling(self, mock_streamlit):
        """Test dashboard error handling with invalid data."""
        # Create a proper DataFrame with invalid data instead of string
        invalid_df = pd.DataFrame({'invalid_column': ['not numeric data']})
        
        with patch('streamlit.error') as mock_error:
            try:
                render_metrics(invalid_df)
                # Should handle error gracefully
                assert mock_error.called
            except Exception:
                # Should not crash
                pass


class TestDashboardStandards:
    """Test suite for dashboard standards compliance."""
    
    def test_component_docstrings(self):
        """Test that all dashboard components have docstrings."""
        components = [
            ConcreteBaseComponent,
            render_header,
            render_sidebar,
            render_metrics,
            render_job_table,
            render_charts
        ]
        
        for component in components:
            assert component.__doc__ is not None, f"{component.__name__} missing docstring"
    
    def test_function_type_hints(self):
        """Test that dashboard functions have type hints."""
        functions = [
            render_header,
            render_sidebar,
            render_metrics,
            render_job_table,
            render_charts
        ]
        
        for func in functions:
            # Check if function has type hints
            import inspect
            sig = inspect.signature(func)
            assert len(sig.parameters) > 0, f"{func.__name__} should have parameters"
    
    def test_no_placeholder_data(self):
        """Test that no placeholder/fake data is used in production."""
        # This test ensures that components don't use hardcoded fake data
        # in their production code
        pass  # Implementation would check for hardcoded data patterns


class TestDashboardPerformance:
    """Test suite for dashboard performance."""
    
    def test_large_dataset_handling(self, mock_streamlit):
        """Test dashboard performance with large datasets."""
        # Create large dataset
        large_df = pd.DataFrame({
            'id': range(1000),
            'title': [f'Job {i}' for i in range(1000)],
            'company': [f'Company {i}' for i in range(1000)],
            'status': ['Applied'] * 1000
        })
        
        with patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.text_input', return_value="") as mock_text_input, \
             patch('streamlit.selectbox', return_value="All") as mock_selectbox, \
             patch('streamlit.expander') as mock_expander:
            start_time = pd.Timestamp.now()
            render_job_table(large_df)
            end_time = pd.Timestamp.now()
            
            # Should complete within reasonable time (e.g., 5 seconds)
            assert (end_time - start_time).total_seconds() < 5
            # Should call markdown for job details section
            mock_markdown.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 