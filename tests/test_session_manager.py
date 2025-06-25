"""
Test-Driven Development: Cookie-Based Session Manager Tests
WRITE TESTS FIRST - THEN IMPLEMENT CODE

This test suite defines the expected behavior of a cookie-based session manager
for maintaining scraping sessions across browser contexts and avoiding bot detection.
"""

import pytest
import sys
import os
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCookieSessionManager:
    """Test the cookie-based session manager (TDD - Tests First!)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cookie_file = os.path.join(self.temp_dir, "test_cookies.json")
        self.session_file = os.path.join(self.temp_dir, "test_session.json")
        
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_session_manager_initialization(self):
        """Test that session manager initializes correctly."""
        # This test will fail until we implement the SessionManager class
        from src.scrapers.session_manager import CookieSessionManager
        
        manager = CookieSessionManager(
            cookie_file=self.cookie_file,
            session_file=self.session_file,
            site_name="eluta"
        )
        
        assert manager.cookie_file == self.cookie_file
        assert manager.session_file == self.session_file
        assert manager.site_name == "eluta"
        assert manager.session_id is not None
        assert isinstance(manager.session_data, dict)
        
    def test_save_cookies_to_file(self):
        """Test saving cookies to file."""
        from src.scrapers.session_manager import CookieSessionManager
        
        manager = CookieSessionManager(cookie_file=self.cookie_file, site_name="eluta")
        
        # Mock cookies data
        test_cookies = [
            {
                "name": "session_id",
                "value": "abc123",
                "domain": ".eluta.ca",
                "path": "/",
                "expires": (datetime.now() + timedelta(days=1)).timestamp()
            },
            {
                "name": "csrf_token", 
                "value": "xyz789",
                "domain": ".eluta.ca",
                "path": "/",
                "expires": (datetime.now() + timedelta(hours=2)).timestamp()
            }
        ]
        
        # Should save cookies successfully
        result = manager.save_cookies(test_cookies)
        assert result == True
        
        # File should exist and contain cookies
        assert os.path.exists(self.cookie_file)
        
        with open(self.cookie_file, 'r') as f:
            saved_data = json.load(f)
            
        assert "cookies" in saved_data
        assert "timestamp" in saved_data
        assert "site_name" in saved_data
        assert len(saved_data["cookies"]) == 2
        assert saved_data["site_name"] == "eluta"
        
    def test_load_cookies_from_file(self):
        """Test loading cookies from file."""
        from src.scrapers.session_manager import CookieSessionManager
        
        # Create test cookie file
        test_data = {
            "cookies": [
                {"name": "session_id", "value": "abc123", "domain": ".eluta.ca"},
                {"name": "csrf_token", "value": "xyz789", "domain": ".eluta.ca"}
            ],
            "timestamp": datetime.now().isoformat(),
            "site_name": "eluta"
        }
        
        with open(self.cookie_file, 'w') as f:
            json.dump(test_data, f)
            
        manager = CookieSessionManager(cookie_file=self.cookie_file, site_name="eluta")
        
        # Should load cookies successfully
        cookies = manager.load_cookies()
        assert len(cookies) == 2
        assert cookies[0]["name"] == "session_id"
        assert cookies[1]["name"] == "csrf_token"
        
    def test_load_cookies_file_not_exists(self):
        """Test loading cookies when file doesn't exist."""
        from src.scrapers.session_manager import CookieSessionManager
        
        manager = CookieSessionManager(cookie_file="nonexistent.json", site_name="eluta")
        
        # Should return empty list when file doesn't exist
        cookies = manager.load_cookies()
        assert cookies == []
        
    def test_cookies_expiration_check(self):
        """Test that expired cookies are filtered out."""
        from src.scrapers.session_manager import CookieSessionManager
        
        # Create test data with expired and valid cookies
        expired_time = (datetime.now() - timedelta(hours=1)).timestamp()
        valid_time = (datetime.now() + timedelta(hours=1)).timestamp()
        
        test_data = {
            "cookies": [
                {"name": "expired_cookie", "value": "old", "expires": expired_time},
                {"name": "valid_cookie", "value": "new", "expires": valid_time},
                {"name": "no_expiry_cookie", "value": "permanent"}  # No expires field
            ],
            "timestamp": datetime.now().isoformat(),
            "site_name": "eluta"
        }
        
        with open(self.cookie_file, 'w') as f:
            json.dump(test_data, f)
            
        manager = CookieSessionManager(cookie_file=self.cookie_file, site_name="eluta")
        cookies = manager.load_cookies()
        
        # Should only return valid cookies
        assert len(cookies) == 2  # valid_cookie and no_expiry_cookie
        cookie_names = [c["name"] for c in cookies]
        assert "expired_cookie" not in cookie_names
        assert "valid_cookie" in cookie_names
        assert "no_expiry_cookie" in cookie_names
        
    def test_session_data_management(self):
        """Test session data save/load functionality."""
        from src.scrapers.session_manager import CookieSessionManager
        
        manager = CookieSessionManager(session_file=self.session_file, site_name="eluta")
        
        # Test saving session data
        test_session = {
            "last_search_url": "https://eluta.ca/search?q=developer",
            "keywords_processed": ["developer", "analyst"],
            "jobs_scraped": 25,
            "last_activity": datetime.now().isoformat()
        }
        
        result = manager.save_session_data(test_session)
        assert result == True
        
        # Test loading session data
        loaded_session = manager.load_session_data()
        assert loaded_session["last_search_url"] == test_session["last_search_url"]
        assert loaded_session["keywords_processed"] == test_session["keywords_processed"]
        assert loaded_session["jobs_scraped"] == test_session["jobs_scraped"]
        
    def test_session_cleanup(self):
        """Test cleaning up old session data."""
        from src.scrapers.session_manager import CookieSessionManager
        
        manager = CookieSessionManager(
            cookie_file=self.cookie_file,
            session_file=self.session_file,
            site_name="eluta"
        )
        
        # Create old session data
        old_session = {
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "data": "old_data"
        }
        
        with open(self.session_file, 'w') as f:
            json.dump(old_session, f)
            
        # Should clean up old session
        result = manager.cleanup_old_sessions(max_age_hours=24)
        assert result == True
        
        # Session file should be removed or emptied
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                assert data == {} or "timestamp" not in data
                
    def test_browser_context_integration(self):
        """Test integration with browser context."""
        from src.scrapers.session_manager import CookieSessionManager
        
        manager = CookieSessionManager(cookie_file=self.cookie_file, site_name="eluta")
        
        # Mock browser context
        mock_context = Mock()
        mock_context.cookies.return_value = [
            {"name": "test_cookie", "value": "test_value", "domain": ".eluta.ca"}
        ]
        
        # Test applying cookies to context
        result = manager.apply_cookies_to_context(mock_context)
        assert result == True
        
        # Test extracting cookies from context
        result = manager.extract_cookies_from_context(mock_context)
        assert result == True
        mock_context.cookies.assert_called_once()
        
    def test_anti_detection_features(self):
        """Test anti-detection features."""
        from src.scrapers.session_manager import CookieSessionManager
        
        manager = CookieSessionManager(cookie_file=self.cookie_file, site_name="eluta")
        
        # Test user agent rotation
        user_agent_1 = manager.get_random_user_agent()
        user_agent_2 = manager.get_random_user_agent()
        
        assert isinstance(user_agent_1, str)
        assert len(user_agent_1) > 50  # Realistic user agent length
        assert "Mozilla" in user_agent_1  # Should be a real browser user agent
        
        # Test that user agents can vary (not always the same)
        # Note: This might occasionally fail due to randomness, but should usually pass
        user_agents = [manager.get_random_user_agent() for _ in range(10)]
        unique_agents = set(user_agents)
        assert len(unique_agents) >= 2  # Should have some variety
        
    def test_session_persistence_across_restarts(self):
        """Test that sessions persist across application restarts."""
        from src.scrapers.session_manager import CookieSessionManager
        
        # First session
        manager1 = CookieSessionManager(
            cookie_file=self.cookie_file,
            session_file=self.session_file,
            site_name="eluta"
        )
        
        test_cookies = [{"name": "persistent", "value": "data", "domain": ".eluta.ca"}]
        manager1.save_cookies(test_cookies)
        
        test_session = {"jobs_scraped": 42}
        manager1.save_session_data(test_session)
        
        # Simulate application restart - new manager instance
        manager2 = CookieSessionManager(
            cookie_file=self.cookie_file,
            session_file=self.session_file,
            site_name="eluta"
        )
        
        # Should load previous session data
        loaded_cookies = manager2.load_cookies()
        loaded_session = manager2.load_session_data()
        
        assert len(loaded_cookies) == 1
        assert loaded_cookies[0]["name"] == "persistent"
        assert loaded_session["jobs_scraped"] == 42
        
    def test_error_handling(self):
        """Test error handling for various failure scenarios."""
        from src.scrapers.session_manager import CookieSessionManager
        
        # Test with invalid file paths (use Windows-style invalid path)
        import platform
        if platform.system() == "Windows":
            invalid_path = "Z:\\nonexistent\\invalid\\path\\cookies.json"
        else:
            invalid_path = "/root/nonexistent/invalid/path/cookies.json"

        manager = CookieSessionManager(
            cookie_file=invalid_path,
            session_file=invalid_path.replace("cookies", "session"),
            site_name="eluta"
        )
        
        # Should handle errors gracefully
        result = manager.save_cookies([{"name": "test", "value": "test"}])
        assert result == False  # Should fail gracefully
        
        cookies = manager.load_cookies()
        assert cookies == []  # Should return empty list on error
        
        # Test with corrupted cookie file
        with open(self.cookie_file, 'w') as f:
            f.write("invalid json content")
            
        manager2 = CookieSessionManager(cookie_file=self.cookie_file, site_name="eluta")
        cookies = manager2.load_cookies()
        assert cookies == []  # Should handle corrupted file gracefully


if __name__ == "__main__":
    # Run tests - these will all fail until we implement the code!
    pytest.main([__file__, "-v"])
