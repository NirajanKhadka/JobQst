"""
Test suite for the Universal Click-and-Popup Framework.
Tests the framework across different job sites with site-specific optimizations.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.human_behavior import UniversalClickPopupFramework, HumanBehaviorConfig


class TestUniversalClickPopupFramework:
    """Test the universal click-and-popup framework."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.framework_eluta = UniversalClickPopupFramework("eluta")
        self.framework_indeed = UniversalClickPopupFramework("indeed")
        self.framework_generic = UniversalClickPopupFramework("unknown_site")
        
    def test_site_config_loading(self):
        """Test that site-specific configurations are loaded correctly."""
        # Test Eluta config
        assert self.framework_eluta.site_name == "eluta"
        assert self.framework_eluta.current_config["job_selector"] == ".organic-job"
        assert self.framework_eluta.current_config["popup_wait"] == 3.0
        
        # Test Indeed config
        assert self.framework_indeed.site_name == "indeed"
        assert self.framework_indeed.current_config["job_selector"] == "[data-jk]"
        assert self.framework_indeed.current_config["popup_wait"] == 2.0
        
        # Test generic fallback
        assert self.framework_generic.site_name == "unknown_site"
        assert self.framework_generic.current_config["job_selector"] == ".job"
        assert self.framework_generic.current_config["popup_wait"] == 3.0
        
    def test_job_link_scoring(self):
        """Test the job link scoring algorithm."""
        # Mock link element
        mock_link = Mock()
        mock_link.inner_text.return_value = "Senior Software Developer - Full Time"
        mock_link.get_attribute.return_value = "/job/12345/senior-software-developer"
        
        config = self.framework_eluta.current_config
        score = self.framework_eluta._score_job_link(mock_link, config)
        
        # Should get points for: text length (10), href validation (20), job keyword (5), longer text (5)
        assert score >= 35
        
        # Test navigation link (should get negative score)
        mock_nav_link = Mock()
        mock_nav_link.inner_text.return_value = "Next Page"
        mock_nav_link.get_attribute.return_value = "/search?page=2"
        
        nav_score = self.framework_eluta._score_job_link(mock_nav_link, config)
        assert nav_score < 0
        
    @patch('scrapers.human_behavior.console')
    def test_find_job_elements(self, mock_console):
        """Test finding job elements with site-specific selectors."""
        # Mock page
        mock_page = Mock()
        mock_elements = [Mock(), Mock(), Mock()]
        mock_page.query_selector_all.return_value = mock_elements
        
        # Test Eluta
        elements = self.framework_eluta.find_job_elements(mock_page)
        mock_page.query_selector_all.assert_called_with(".organic-job")
        assert len(elements) == 3
        
        # Test Indeed
        elements = self.framework_indeed.find_job_elements(mock_page)
        mock_page.query_selector_all.assert_called_with("[data-jk]")
        assert len(elements) == 3
        
    @patch('scrapers.human_behavior.console')
    def test_find_best_job_link(self, mock_console):
        """Test finding the best job link within a job element."""
        # Mock job element with multiple links
        mock_job_element = Mock()
        
        # Create mock links with different scores
        good_link = Mock()
        good_link.inner_text.return_value = "Data Analyst Position - Entry Level"
        good_link.get_attribute.return_value = "/job/123/data-analyst"
        
        bad_link = Mock()
        bad_link.inner_text.return_value = "Next"
        bad_link.get_attribute.return_value = "/search?page=2"
        
        mock_job_element.query_selector_all.return_value = [bad_link, good_link]
        
        best_link = self.framework_eluta.find_best_job_link(mock_job_element)
        assert best_link == good_link
        
    @patch('scrapers.human_behavior.time')
    @patch('scrapers.human_behavior.console')
    def test_execute_click_popup(self, mock_console, mock_time):
        """Test executing click-and-popup with site-specific optimizations."""
        # Mock elements
        mock_link = Mock()
        mock_page = Mock()
        mock_popup = Mock()
        mock_popup.url = "https://external-ats.com/job/12345"
        
        # Mock popup context manager
        mock_popup_info = Mock()
        mock_popup_info.value = mock_popup
        mock_page.expect_popup.return_value.__enter__ = Mock(return_value=mock_popup_info)
        mock_page.expect_popup.return_value.__exit__ = Mock(return_value=None)
        
        # Test execution
        result_url = self.framework_eluta.execute_click_popup(mock_link, mock_page, "test-job-1")
        
        # Verify click was called
        mock_link.click.assert_called_once()
        
        # Verify popup was closed
        mock_popup.close.assert_called_once()
        
        # Verify URL was returned
        assert result_url == "https://external-ats.com/job/12345"
        
        # Verify site-specific wait time was used
        mock_time.sleep.assert_called_with(3.0)  # Eluta's popup_wait


class TestHumanBehaviorConfig:
    """Test the human behavior configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = HumanBehaviorConfig()
        
        # Test delay ranges
        assert config.delays["popup_wait"] == 3.0
        assert config.delays["between_jobs"] == (1.0, 2.0)
        assert config.delays["page_load"] == (2.0, 4.0)
        
        # Test cookie settings
        assert config.cookie_settings["save_cookies"] == True
        assert "cookies.json" in config.cookie_settings["cookie_file"]
        
        # Test tab settings
        assert config.tab_settings["close_tabs_immediately"] == True
        assert config.tab_settings["max_open_tabs"] == 3
        
    def test_custom_config(self):
        """Test custom configuration values."""
        config = HumanBehaviorConfig(
            popup_wait=5.0,
            between_jobs=(0.5, 1.0),
            save_cookies=False,
            max_open_tabs=5
        )
        
        assert config.delays["popup_wait"] == 5.0
        assert config.delays["between_jobs"] == (0.5, 1.0)
        assert config.cookie_settings["save_cookies"] == False
        assert config.tab_settings["max_open_tabs"] == 5


class TestIntegration:
    """Integration tests for the complete framework."""
    
    @patch('scrapers.human_behavior.console')
    def test_framework_integration_with_human_behavior(self, mock_console):
        """Test integration between framework and human behavior."""
        framework = UniversalClickPopupFramework("eluta")
        
        # Mock page and elements
        mock_page = Mock()
        mock_job_elements = [Mock(), Mock()]
        mock_page.query_selector_all.return_value = mock_job_elements
        
        # Mock job link
        mock_link = Mock()
        mock_link.inner_text.return_value = "Software Developer - Junior Level"
        mock_link.get_attribute.return_value = "/job/123/software-developer"
        mock_job_elements[0].query_selector_all.return_value = [mock_link]
        
        # Test finding elements
        elements = framework.find_job_elements(mock_page)
        assert len(elements) == 2
        
        # Test finding best link
        best_link = framework.find_best_job_link(mock_job_elements[0])
        assert best_link == mock_link


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
