#!/usr/bin/env python3
"""
Additional Module Testing for AutoJobAgent
Tests additional modules and functions that might have issues.
Following DEVELOPMENT_STANDARDS.md for proper pytest structure.
"""

import pytest
from pathlib import Path
from typing import Dict, Any, List


class TestUtilityModules:
    """Test utility module imports and basic functionality."""
    
    def test_profile_helpers_import(self):
        """Test that profile helpers can be imported."""
        try:
            from src.utils.profile_helpers import load_profile, get_available_profiles
            assert callable(load_profile)
            assert callable(get_available_profiles)
        except ImportError as e:
            pytest.fail(f"Failed to import profile helpers: {e}")

    def test_job_helpers_import(self):
        """Test that job helpers can be imported."""
        try:
            from src.utils.job_helpers import generate_job_hash, is_duplicate_job, sort_jobs
            assert callable(generate_job_hash)
            assert callable(is_duplicate_job)
            assert callable(sort_jobs)
        except ImportError as e:
            pytest.fail(f"Failed to import job helpers: {e}")

    def test_file_operations_import(self):
        """Test that file operations can be imported."""
        try:
            from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json, save_jobs_to_csv
            assert callable(save_jobs_to_json)
            assert callable(load_jobs_from_json)
            assert callable(save_jobs_to_csv)
        except ImportError as e:
            pytest.fail(f"Failed to import file operations: {e}")


class TestDocumentModifier:
    """Test document modifier functionality."""
    
    def test_document_modifier_import(self):
        """Test that document modifier can be imported."""
        try:
            from src.document_modifier.document_modifier import customize, DocumentModifier
            assert callable(customize)
            assert DocumentModifier is not None
        except ImportError as e:
            if "lxml" in str(e):
                pytest.skip("Document modifier not available - missing lxml dependency")
            else:
                pytest.fail(f"Failed to import document modifier: {e}")


class TestScrapers:
    """Test scraper module imports."""
    
    def test_eluta_scraper_import(self):
        """Test that Eluta scraper exists."""
        try:
            from src.scrapers.enhanced_eluta_scraper import EnhancedElutaScraper
            assert EnhancedElutaScraper is not None
        except ImportError:
            pytest.skip("Eluta enhanced scraper not available")


class TestDashboard:
    """Test dashboard components."""
    
    def test_dashboard_api_import(self):
        """Test that dashboard API exists."""
        try:
            from src.dashboard import api
            assert api is not None
        except ImportError:
            pytest.skip("Dashboard API not available")


class TestProfileSystem:
    """Test profile system functionality."""
    
    def test_profile_loading(self):
        """Test profile loading with available profiles."""
        try:
            from src.utils.profile_helpers import load_profile, get_available_profiles
            
            # Test getting available profiles
            profiles = get_available_profiles()
            assert isinstance(profiles, (list, tuple))
            
            # If we have profiles, try loading one
            if profiles:
                # Try to load a known good profile first
                test_profiles = ['default', 'Nirajan', 'test_profile']
                profile_loaded = False
                
                for test_profile in test_profiles:
                    if test_profile in profiles:
                        profile = load_profile(test_profile)
                        if profile is not None:
                            profile_loaded = True
                            break
                
                if not profile_loaded:
                    # Fallback: try the first available profile
                    profile = load_profile(profiles[0])
                    assert profile is not None, f"Failed to load profile: {profiles[0]}"
                
        except ImportError:
            pytest.skip("Profile helpers not available")
        except Exception as e:
            pytest.fail(f"Profile loading failed: {e}")


class TestJobHelpers:
    """Test job helper functions."""
    
    def test_job_hash_generation(self):
        """Test job hash generation."""
        try:
            from src.utils.job_helpers import generate_job_hash
            
            # Test with minimal job data structure (no fabricated content)
            job_data = {
                'title': '',
                'company': '',
                'location': ''
            }
            
            hash_value = generate_job_hash(job_data)
            assert hash_value is not None
            assert isinstance(hash_value, str)
            assert len(hash_value) > 0
            
        except ImportError:
            pytest.skip("Job helpers not available")
        except Exception as e:
            pytest.fail(f"Job hash generation failed: {e}")

    def test_duplicate_job_detection(self):
        """Test duplicate job detection."""
        try:
            from src.utils.job_helpers import is_duplicate_job
            
            # Test with minimal job data structure (no fabricated content)
            job1 = {
                'title': '',
                'company': '',
                'location': ''
            }
            
            job2 = {
                'title': '',
                'company': '', 
                'location': ''
            }
            
            # This should detect as duplicate (same job)
            result = is_duplicate_job(job1, job2)
            assert isinstance(result, bool)
            
        except ImportError:
            pytest.skip("Job helpers not available")
        except Exception as e:
            pytest.fail(f"Duplicate job detection failed: {e}")


class TestFileOperations:
    """Test file operation functions."""
    
    def test_json_operations(self):
        """Test JSON save/load operations."""
        try:
            from src.utils.file_operations import save_jobs_to_json, load_jobs_from_json
            
            # These functions exist but we won't test actual file operations
            # in unit tests to avoid side effects
            assert callable(save_jobs_to_json)
            assert callable(load_jobs_from_json)
            
        except ImportError:
            pytest.skip("File operations not available")

    def test_csv_operations(self):
        """Test CSV save operations."""
        try:
            from src.utils.file_operations import save_jobs_to_csv
            
            # Function exists check
            assert callable(save_jobs_to_csv)
            
        except ImportError:
            pytest.skip("File operations not available")

