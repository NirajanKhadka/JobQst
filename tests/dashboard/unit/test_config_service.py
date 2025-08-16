"""
Comprehensive unit tests for ConfigService.

Tests all functionality of the configuration service including:
- Profile management and validation
- Settings management and persistence
- Configuration validation and sanitization
- Error handling and recovery
- Security and data integrity
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.services.config_service import ConfigService, get_config_service


class TestConfigService:
    """Test suite for ConfigService class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for config testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config_service(self, temp_config_dir):
        """Create a fresh ConfigService instance for testing."""
        return ConfigService(config_dir=temp_config_dir)
    
    @pytest.fixture
    def sample_profiles(self):
        """Sample profile data for testing."""
        return {
            "Nirajan": {
                "name": "Nirajan Khadka",
                "email": "nirajan@example.com",
                "database_path": "profiles/Nirajan/jobs.db",
                "resume_path": "profiles/Nirajan/resume.pdf",
                "cover_letter_template": "profiles/Nirajan/cover_letter.txt"
            },
            "TestUser": {
                "name": "Test User",
                "email": "test@example.com", 
                "database_path": "profiles/TestUser/jobs.db",
                "resume_path": "profiles/TestUser/resume.pdf",
                "cover_letter_template": "profiles/TestUser/cover_letter.txt"
            }
        }
    
    @pytest.fixture
    def sample_settings(self):
        """Sample settings data for testing."""
        return {
            "dashboard": {
                "auto_refresh": True,
                "refresh_interval": 10,
                "theme": "light",
                "show_metrics": True,
                "items_per_page": 25
            },
            "notifications": {
                "email_enabled": True,
                "desktop_enabled": False,
                "sound_enabled": True
            },
            "security": {
                "session_timeout": 3600,
                "require_auth": False,
                "encrypt_data": True
            }
        }
    
    def test_config_service_initialization(self, config_service):
        """Test ConfigService proper initialization."""
        assert config_service.config_dir.exists()
        assert isinstance(config_service._cache, dict)
        assert config_service.cache_ttl == 300  # Default value
    
    def test_singleton_pattern(self):
        """Test that get_config_service returns the same instance."""
        service1 = get_config_service()
        service2 = get_config_service()
        
        assert service1 is service2
        assert isinstance(service1, ConfigService)
    
    def test_get_profiles_success(self, config_service, sample_profiles, temp_config_dir):
        """Test successful profile loading."""
        # Create profiles.json file
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        profiles = config_service.get_profiles()
        
        assert isinstance(profiles, dict)
        assert "Nirajan" in profiles
        assert "TestUser" in profiles
        assert profiles["Nirajan"]["name"] == "Nirajan Khadka"
    
    def test_get_profiles_file_not_found(self, config_service):
        """Test profile loading when file doesn't exist."""
        profiles = config_service.get_profiles()
        
        # Should return empty dict when file doesn't exist
        assert isinstance(profiles, dict)
        assert len(profiles) == 0
    
    def test_get_profiles_invalid_json(self, config_service, temp_config_dir):
        """Test profile loading with invalid JSON."""
        # Create invalid JSON file
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            f.write("invalid json content")
        
        profiles = config_service.get_profiles()
        
        # Should return empty dict on invalid JSON
        assert isinstance(profiles, dict)
        assert len(profiles) == 0
    
    def test_save_profiles_success(self, config_service, sample_profiles):
        """Test successful profile saving."""
        result = config_service.save_profiles(sample_profiles)
        
        assert result is True
        
        # Verify profiles were saved
        saved_profiles = config_service.get_profiles()
        assert saved_profiles == sample_profiles
    
    def test_save_profiles_validation_error(self, config_service):
        """Test profile saving with validation errors."""
        invalid_profiles = {
            "InvalidUser": {
                "name": "",  # Empty name should fail validation
                "email": "invalid-email"  # Invalid email format
            }
        }
        
        result = config_service.save_profiles(invalid_profiles)
        
        # Should fail validation
        assert result is False
    
    def test_validate_profile_success(self, config_service):
        """Test successful profile validation."""
        valid_profile = {
            "name": "Test User",
            "email": "test@example.com",
            "database_path": "profiles/test/jobs.db",
            "resume_path": "profiles/test/resume.pdf"
        }
        
        is_valid, errors = config_service.validate_profile(valid_profile)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_profile_missing_required_fields(self, config_service):
        """Test profile validation with missing required fields."""
        invalid_profile = {
            "email": "test@example.com"
            # Missing name field
        }
        
        is_valid, errors = config_service.validate_profile(invalid_profile)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)
    
    def test_validate_profile_invalid_email(self, config_service):
        """Test profile validation with invalid email."""
        invalid_profile = {
            "name": "Test User",
            "email": "invalid-email-format",
            "database_path": "profiles/test/jobs.db"
        }
        
        is_valid, errors = config_service.validate_profile(invalid_profile)
        
        assert is_valid is False
        assert any("email" in error.lower() for error in errors)
    
    def test_get_settings_success(self, config_service, sample_settings, temp_config_dir):
        """Test successful settings loading."""
        # Create settings.json file
        settings_file = temp_config_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(sample_settings, f)
        
        settings = config_service.get_settings()
        
        assert isinstance(settings, dict)
        assert "dashboard" in settings
        assert settings["dashboard"]["auto_refresh"] is True
    
    def test_get_settings_file_not_found(self, config_service):
        """Test settings loading when file doesn't exist."""
        settings = config_service.get_settings()
        
        # Should return default settings
        assert isinstance(settings, dict)
        assert "dashboard" in settings
        assert "auto_refresh" in settings["dashboard"]
    
    def test_save_settings_success(self, config_service, sample_settings):
        """Test successful settings saving."""
        result = config_service.save_settings(sample_settings)
        
        assert result is True
        
        # Verify settings were saved
        saved_settings = config_service.get_settings()
        assert saved_settings["dashboard"]["auto_refresh"] == sample_settings["dashboard"]["auto_refresh"]
    
    def test_get_dashboard_settings(self, config_service, sample_settings, temp_config_dir):
        """Test getting dashboard-specific settings."""
        # Create settings file with dashboard section
        settings_file = temp_config_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(sample_settings, f)
        
        dashboard_settings = config_service.get_dashboard_settings()
        
        assert isinstance(dashboard_settings, dict)
        assert dashboard_settings["auto_refresh"] is True
        assert dashboard_settings["refresh_interval"] == 10
        assert dashboard_settings["theme"] == "light"
    
    def test_save_dashboard_settings(self, config_service):
        """Test saving dashboard-specific settings."""
        new_dashboard_settings = {
            "auto_refresh": False,
            "refresh_interval": 30,
            "theme": "dark",
            "show_metrics": False
        }
        
        result = config_service.save_dashboard_settings(new_dashboard_settings)
        
        assert result is True
        
        # Verify dashboard settings were saved
        saved_settings = config_service.get_dashboard_settings()
        assert saved_settings["auto_refresh"] is False
        assert saved_settings["theme"] == "dark"
    
    def test_get_default_profile_configured(self, config_service, sample_profiles, temp_config_dir):
        """Test getting default profile when configured."""
        # Create profiles and settings
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        settings = {
            "default_profile": "Nirajan",
            "dashboard": {}
        }
        settings_file = temp_config_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(settings, f)
        
        default_profile = config_service.get_default_profile()
        
        assert default_profile == "Nirajan"
    
    def test_get_default_profile_fallback(self, config_service, sample_profiles, temp_config_dir):
        """Test getting default profile with fallback logic."""
        # Create profiles but no default setting
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        default_profile = config_service.get_default_profile()
        
        # Should return first available profile
        assert default_profile in sample_profiles.keys()
    
    def test_set_default_profile_success(self, config_service, sample_profiles, temp_config_dir):
        """Test setting default profile successfully."""
        # Create profiles
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        result = config_service.set_default_profile("TestUser")
        
        assert result is True
        assert config_service.get_default_profile() == "TestUser"
    
    def test_set_default_profile_invalid(self, config_service, sample_profiles, temp_config_dir):
        """Test setting invalid default profile."""
        # Create profiles
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        result = config_service.set_default_profile("NonExistentUser")
        
        assert result is False
    
    def test_validate_settings_success(self, config_service, sample_settings):
        """Test successful settings validation."""
        is_valid, errors = config_service.validate_settings(sample_settings)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_settings_invalid_types(self, config_service):
        """Test settings validation with invalid types."""
        invalid_settings = {
            "dashboard": {
                "auto_refresh": "not_a_boolean",  # Should be boolean
                "refresh_interval": "not_a_number"  # Should be number
            }
        }
        
        is_valid, errors = config_service.validate_settings(invalid_settings)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_get_database_path_absolute(self, config_service, sample_profiles, temp_config_dir):
        """Test getting absolute database path."""
        # Create profiles
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        db_path = config_service.get_database_path("Nirajan")
        
        assert isinstance(db_path, Path)
        assert db_path.is_absolute()
        assert "Nirajan" in str(db_path)
    
    def test_get_database_path_nonexistent_profile(self, config_service):
        """Test getting database path for nonexistent profile."""
        db_path = config_service.get_database_path("NonExistentUser")
        
        assert db_path is None
    
    def test_caching_mechanism(self, config_service, sample_profiles, temp_config_dir):
        """Test that configuration data is properly cached."""
        # Create profiles file
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        # First call should read from file
        profiles1 = config_service.get_profiles()
        
        # Modify file directly
        with open(profiles_file, 'w') as f:
            json.dump({}, f)
        
        # Second call should return cached data
        profiles2 = config_service.get_profiles()
        
        assert profiles1 == profiles2
        assert len(profiles2) > 0  # Should still have cached profiles
    
    def test_clear_cache(self, config_service, sample_profiles, temp_config_dir):
        """Test cache clearing functionality."""
        # Create and load profiles (should be cached)
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        config_service.get_profiles()
        
        # Clear cache
        config_service.clear_cache()
        
        # Modify file
        with open(profiles_file, 'w') as f:
            json.dump({}, f)
        
        # Should reload from file
        profiles = config_service.get_profiles()
        assert len(profiles) == 0
    
    def test_file_permissions_error(self, config_service, temp_config_dir):
        """Test handling of file permission errors."""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            profiles = config_service.get_profiles()
            
            # Should handle gracefully
            assert isinstance(profiles, dict)
    
    def test_concurrent_access(self, config_service, sample_profiles, temp_config_dir):
        """Test handling of concurrent configuration access."""
        import threading
        
        # Create profiles file
        profiles_file = temp_config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(sample_profiles, f)
        
        results = []
        
        def load_profiles():
            results.append(config_service.get_profiles())
        
        # Start multiple threads
        threads = [threading.Thread(target=load_profiles) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(results) == 5
        for result in results:
            assert isinstance(result, dict)
    
    def test_security_validation(self, config_service):
        """Test security-related validation."""
        malicious_profile = {
            "name": "../../../etc/passwd",  # Path traversal attempt
            "email": "test@example.com",
            "database_path": "/etc/shadow",  # Sensitive file access
            "resume_path": "<script>alert('xss')</script>"  # XSS attempt
        }
        
        is_valid, errors = config_service.validate_profile(malicious_profile)
        
        # Should detect and reject malicious content
        assert is_valid is False
        assert len(errors) > 0
    
    def test_data_integrity_validation(self, config_service):
        """Test data integrity validation."""
        # Test with corrupted data structure
        corrupted_profiles = {
            "User1": "this should be a dict, not a string",
            "User2": {
                "name": ["this", "should", "be", "string"],  # Wrong type
                "email": {"nested": "object"}  # Wrong type
            }
        }
        
        result = config_service.save_profiles(corrupted_profiles)
        assert result is False


class TestConfigServiceIntegration:
    """Integration tests for ConfigService with actual file system."""
    
    @pytest.mark.integration
    def test_real_config_directory_access(self):
        """Test accessing real configuration directory."""
        # Test with actual config directory
        service = ConfigService()
        
        try:
            profiles = service.get_profiles()
            settings = service.get_settings()
            
            assert isinstance(profiles, dict)
            assert isinstance(settings, dict)
        except Exception as e:
            pytest.skip(f"Real config directory not accessible: {e}")
    
    @pytest.mark.integration
    def test_real_file_operations(self):
        """Test actual file read/write operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ConfigService(config_dir=Path(temp_dir))
            
            # Test saving and loading real files
            test_profiles = {
                "TestUser": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "database_path": "test.db"
                }
            }
            
            assert service.save_profiles(test_profiles) is True
            loaded_profiles = service.get_profiles()
            assert loaded_profiles == test_profiles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
