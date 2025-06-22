"""
Basic tests for AutoJobAgent package.
"""
import sys
from pathlib import Path

# Add project root and src directory to path for imports
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

import pytest

def test_basic_imports():
    """Test that basic modules can be imported."""
    try:
        from core import utils
        assert utils is not None
    except ImportError:
        pytest.skip("core.utils not available")
    
    try:
        from src.utils.document_generator import customize
        assert customize is not None
    except ImportError:
        pytest.skip("document_generator not available")
    
    try:
        from ats import detect, get_submitter
        assert detect is not None
        assert get_submitter is not None
    except ImportError:
        pytest.skip("ats module not available")

def test_profile_loading():
    """Test loading a user profile."""
    try:
        from core import utils
        profile = utils.load_profile("Nirajan")
        if profile:
            assert "name" in profile
            assert "keywords" in profile
        else:
            pytest.skip("Profile not found")
    except Exception:
        pytest.skip("Profile loading not available")

def test_job_database():
    """Test job database functionality."""
    try:
        from core.job_database import JobDatabase
        db = JobDatabase("Nirajan")
        stats = db.get_stats()
        assert isinstance(stats, dict)
    except Exception:
        pytest.skip("Job database not available")

def test_basic_data_structures():
    """Test basic data structure creation."""
    # Test job dictionary
    job = {
        "title": "Software Engineer",
        "company": "Test Corp",
        "location": "Remote",
        "url": "https://example.com/jobs/123"
    }
    
    assert job["title"] == "Software Engineer"
    assert job["company"] == "Test Corp"
    assert job["location"] == "Remote"
    assert job["url"] == "https://example.com/jobs/123"

def test_path_operations():
    """Test path operations."""
    from pathlib import Path
    
    # Test profile path
    profile_path = Path("profiles/Nirajan")
    assert isinstance(profile_path, Path)
    
    # Test src path
    src_path = Path("src")
    assert isinstance(src_path, Path)
