import pytest
from src.dashboard.unified_dashboard import check_dashboard_backend_connection

def test_dashboard_backend_connection():
    # Test the backend connection without parameters
    result = check_dashboard_backend_connection()
    assert isinstance(result, bool), "Dashboard connection check should return a boolean"

def test_dashboard_backend_connection_missing():
    # Test that the function runs without errors
    result = check_dashboard_backend_connection()
    assert isinstance(result, bool), "Dashboard connection check should return a boolean"
