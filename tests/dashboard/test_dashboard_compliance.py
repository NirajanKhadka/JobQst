#!/usr/bin/env python3
"""
Test suite for dashboard module compliance with development standards.

This test suite verifies that all dashboard components follow the development
standards including type hints, docstrings, error handling, and code quality.
"""

import pytest
import inspect
import ast
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import dashboard modules
from src.dashboard import components
from src.dashboard import api
from src.dashboard import websocket
from src.dashboard.routers import jobs, stats, system
from src.dashboard.services import data_service


class TestDashboardCompliance:
    """Test suite for dashboard module compliance."""

    def test_all_functions_have_docstrings(self):
        """Test that all public functions have docstrings."""
        modules_to_check = [
            components.header,
            components.sidebar,
            components.metrics,
            components.job_table,
            components.charts,
            api,
            websocket,
            jobs,
            stats,
            system,
            data_service,
        ]
        
        missing_docstrings = []
        
        for module in modules_to_check:
            for name, obj in inspect.getmembers(module):
                if (inspect.isfunction(obj) and 
                    not name.startswith('_') and 
                    obj.__module__ == module.__name__):
                    
                    if not obj.__doc__ or obj.__doc__.strip() == "":
                        missing_docstrings.append(f"{module.__name__}.{name}")
        
        assert not missing_docstrings, f"Functions missing docstrings: {missing_docstrings}"

    def test_all_classes_have_docstrings(self):
        """Test that all public classes have docstrings."""
        modules_to_check = [
            components.base,
            websocket,
            data_service,
        ]
        
        missing_docstrings = []
        
        for module in modules_to_check:
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    not name.startswith('_') and 
                    obj.__module__ == module.__name__):
                    
                    if not obj.__doc__ or obj.__doc__.strip() == "":
                        missing_docstrings.append(f"{module.__name__}.{name}")
        
        assert not missing_docstrings, f"Classes missing docstrings: {missing_docstrings}"

    def test_functions_have_type_hints(self):
        """Test that functions have proper type hints."""
        modules_to_check = [
            components.header,
            components.sidebar,
            components.metrics,
            components.job_table,
            jobs,
            stats,
            system,
        ]
        
        missing_type_hints = []
        
        for module in modules_to_check:
            for name, obj in inspect.getmembers(module):
                if (inspect.isfunction(obj) and 
                    not name.startswith('_') and 
                    obj.__module__ == module.__name__):
                    
                    sig = inspect.signature(obj)
                    
                    # Check if function has return type annotation
                    if sig.return_annotation == inspect.Signature.empty:
                        missing_type_hints.append(f"{module.__name__}.{name} (missing return type)")
                    
                    # Check if parameters have type annotations
                    for param_name, param in sig.parameters.items():
                        if (param.annotation == inspect.Parameter.empty and 
                            param_name not in ['self', 'cls']):
                            missing_type_hints.append(f"{module.__name__}.{name}.{param_name} (missing param type)")
        
        assert not missing_type_hints, f"Missing type hints: {missing_type_hints}"

    def test_module_docstrings_exist(self):
        """Test that all modules have docstrings."""
        modules_to_check = [
            components.header,
            components.sidebar,
            components.metrics,
            components.job_table,
            components.charts,
            api,
            websocket,
            jobs,
            stats,
            system,
        ]
        
        missing_module_docstrings = []
        
        for module in modules_to_check:
            if not module.__doc__ or module.__doc__.strip() == "":
                missing_module_docstrings.append(module.__name__)
        
        assert not missing_module_docstrings, f"Modules missing docstrings: {missing_module_docstrings}"

    def test_error_handling_patterns(self):
        """Test that error handling follows proper patterns."""
        # This is a simplified test - in practice, you'd analyze the AST
        # to check for try/except blocks and proper logging
        
        modules_with_error_handling = [
            api,
            jobs,
            stats,
            system,
            websocket,
            data_service,
        ]
        
        for module in modules_with_error_handling:
            # Check if module imports logging
            assert hasattr(module, 'logger') or 'logging' in module.__dict__, \
                f"Module {module.__name__} should have logging configured"

    def test_component_imports_work(self):
        """Test that all component imports work correctly."""
        # Test that we can import all the functions we expect
        from src.dashboard.components import (
            render_header,
            render_sidebar,
            render_metrics,
            render_job_table,
            render_charts,
            BaseComponent,
            ContainerComponent,
            CachedComponent,
        )
        
        # Verify they are callable
        assert callable(render_header)
        assert callable(render_sidebar)
        assert callable(render_metrics)
        assert callable(render_job_table)
        assert callable(render_charts)
        
        # Verify classes exist and are importable (skip instantiation since they're abstract)
        assert BaseComponent is not None
        assert ContainerComponent is not None  
        assert CachedComponent is not None
        
        # Verify they have the expected interface
        assert hasattr(BaseComponent, 'render')
        assert hasattr(BaseComponent, 'initialize')
        assert hasattr(ContainerComponent, 'add_component')  # Fixed method name
        assert hasattr(CachedComponent, 'get_cached_data')

    def test_api_endpoints_documented(self):
        """Test that API endpoints have proper documentation."""
        from src.dashboard.routers import jobs, stats, system
        
        routers = [jobs.router, stats.router, system.router]
        
        for router in routers:
            for route in router.routes:
                if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__doc__'):
                    assert route.endpoint.__doc__, f"API endpoint {route.path} missing docstring"

    def test_websocket_manager_functionality(self):
        """Test that WebSocket manager has proper functionality."""
        from src.dashboard.websocket import ConnectionManager
        
        manager = ConnectionManager()
        
        # Test basic functionality
        assert manager.get_connection_count() == 0
        stats = manager.get_connection_stats()
        assert isinstance(stats, dict)
        assert 'active_connections' in stats

    def test_data_service_functionality(self):
        """Test that data service has proper functionality."""
        from src.dashboard.services.data_service import get_data_service
        
        service = get_data_service()
        
        # Test health check
        health = service.get_health_status()
        assert isinstance(health, dict)
        assert 'status' in health
        
        # Test cache functionality
        assert hasattr(service, 'clear_cache')
        service.clear_cache()  # Should not raise exception

    def test_no_white_font_in_templates(self):
        """Test that HTML templates don't use white font inappropriately."""
        template_dir = Path(__file__).parent.parent.parent / "src" / "dashboard" / "templates"
        
        if template_dir.exists():
            for template_file in template_dir.glob("*.html"):
                content = template_file.read_text(encoding='utf-8')
                
                # Check for problematic white font usage
                # This is a simplified check - you could make it more effective
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'color: white' in line or 'color: #fff' in line:
                        # Check if it's on a dark background (simplified check)
                        context = '\n'.join(lines[max(0, i-3):i+3])
                        if not any(dark_bg in context.lower() for dark_bg in 
                                 ['background-color: #', 'bg-', 'gradient', 'dark']):
                            pytest.fail(f"Potential white font on light background in {template_file}:{i}")


def test_file_size_compliance():
    """Test that files don't exceed size thresholds."""
    dashboard_dir = Path(__file__).parent.parent.parent / "src" / "dashboard"
    
    oversized_files = []
    
    for py_file in dashboard_dir.rglob("*.py"):
        if py_file.is_file():
            # Skip backup files and temporary files
            if '_backup' in py_file.name or '.bak' in py_file.name or py_file.name.startswith('temp_'):
                continue
                
            line_count = len(py_file.read_text(encoding='utf-8').split('\n'))
            
            # Special threshold for main dashboard file (complex UI component)
            critical_threshold = 2500 if py_file.name == 'unified_dashboard.py' else 1000
            warning_threshold = 1000 if py_file.name == 'unified_dashboard.py' else 500
            
            # Critical threshold check
            if line_count > critical_threshold:
                oversized_files.append(f"{py_file.name}: {line_count} lines (CRITICAL)")
            # Warning threshold check
            elif line_count > warning_threshold:
                oversized_files.append(f"{py_file.name}: {line_count} lines (WARNING)")
    
    # Fail only on critical violations
    critical_violations = [f for f in oversized_files if "CRITICAL" in f]
    assert not critical_violations, f"Files exceed critical size limit: {critical_violations}"
    
    # Log warnings for review
    warnings = [f for f in oversized_files if "WARNING" in f]
    if warnings:
        print(f"Files approaching size limit (review recommended): {warnings}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
