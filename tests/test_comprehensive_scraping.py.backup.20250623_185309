"""
Comprehensive test suite for enhanced click-and-popup job scraping functionality.
Tests click-and-popup behavior, popup handling, multi-browser context support, 
human-like behavior, and job filtering.
"""

import pytest
import sys
import os
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.human_behavior import HumanBehaviorMixin, UniversalClickPopupFramework, HumanBehaviorConfig
from scrapers.job_filters import JobDateFilter, ExperienceLevelFilter, UniversalJobFilter


class TestClickAndPopupIntegration:
    """Test the complete click-and-popup integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.profile = {
            "profile_name": "test_user",
            "keywords": ["developer", "analyst"],
            "location": "Toronto",
            "experience_level": "entry"
        }
        
    @patch('scrapers.human_behavior.console')
    def test_human_behavior_mixin_initialization(self, mock_console):
        """Test that HumanBehaviorMixin initializes correctly."""
        
        class TestScraper(HumanBehaviorMixin):
            def __init__(self, profile, **kwargs):
                self.site_name = "eluta"
                super().__init__(profile, **kwargs)
        
        scraper = TestScraper(self.profile)
        
        # Check that human config is initialized
        assert hasattr(scraper, 'human_config')
        assert isinstance(scraper.human_config, HumanBehaviorConfig)
        
        # Check that click-popup framework is initialized
        assert hasattr(scraper, 'click_popup_framework')
        assert isinstance(scraper.click_popup_framework, UniversalClickPopupFramework)
        
    @patch('scrapers.human_behavior.time')
    @patch('scrapers.human_behavior.console')
    def test_human_delay_functionality(self, mock_console, mock_time):
        """Test human delay functionality with different delay types."""
        
        class TestScraper(HumanBehaviorMixin):
            def __init__(self, profile):
                super().__init__(profile)
        
        scraper = TestScraper(self.profile)
        
        # Test different delay types
        delay_types = ["page_load", "between_jobs", "popup_wait", "pre_click"]
        
        for delay_type in delay_types:
            delay = scraper.human_delay(delay_type)
            assert isinstance(delay, float)
            assert delay > 0
            mock_time.sleep.assert_called()
            
    @patch('scrapers.human_behavior.console')
    def test_universal_click_popup_framework_site_configs(self, mock_console):
        """Test that universal framework has correct site configurations."""
        
        # Test different sites
        sites = ["eluta", "indeed", "jobbank", "linkedin", "monster"]
        
        for site in sites:
            framework = UniversalClickPopupFramework(site)
            assert framework.site_name == site
            assert "job_selector" in framework.current_config
            assert "popup_wait" in framework.current_config
            assert "popup_timeout" in framework.current_config
            
        # Test generic fallback
        generic_framework = UniversalClickPopupFramework("unknown_site")
        assert generic_framework.site_name == "unknown_site"
        assert generic_framework.current_config["job_selector"] == ".job"
        
    @patch('scrapers.human_behavior.console')
    def test_job_link_scoring_algorithm(self, mock_console):
        """Test the job link scoring algorithm."""
        framework = UniversalClickPopupFramework("eluta")
        config = framework.current_config
        
        # Mock good job link
        good_link = Mock()
        good_link.inner_text.return_value = "Software Developer - Entry Level Position"
        good_link.get_attribute.return_value = "/job/12345/software-developer"
        
        score = framework._score_job_link(good_link, config)
        assert score > 30  # Should get high score
        
        # Mock navigation link (should get low score)
        nav_link = Mock()
        nav_link.inner_text.return_value = "Next Page"
        nav_link.get_attribute.return_value = "/search?page=2"
        
        nav_score = framework._score_job_link(nav_link, config)
        assert nav_score < 0  # Should get negative score
        
    @patch('scrapers.human_behavior.time')
    @patch('scrapers.human_behavior.console')
    def test_click_popup_execution(self, mock_console, mock_time):
        """Test click-and-popup execution with site-specific optimizations."""
        framework = UniversalClickPopupFramework("eluta")
        
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
        result_url = framework.execute_click_popup(mock_link, mock_page, "test-job-1")
        
        # Verify click was called
        mock_link.click.assert_called_once()
        
        # Verify popup was closed
        mock_popup.close.assert_called_once()
        
        # Verify URL was returned
        assert result_url == "https://external-ats.com/job/12345"
        
        # Verify site-specific wait time was used (3.0 for Eluta)
        mock_time.sleep.assert_called_with(3.0)


class TestJobFilteringIntegration:
    """Test the complete job filtering integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.eluta_filter = UniversalJobFilter("eluta")
        self.indeed_filter = UniversalJobFilter("indeed")
        
    def test_site_specific_date_filtering(self):
        """Test site-specific date filtering (14 days for Eluta, 124 days for others)."""
        
        # Job posted 20 days ago
        job_20_days = {
            "title": "Software Developer",
            "posted_date": "20 days ago",
            "summary": "Entry level position"
        }
        
        # Should fail Eluta (14-day limit) but pass Indeed (124-day limit)
        eluta_result, _ = self.eluta_filter.filter_job(job_20_days)
        indeed_result, _ = self.indeed_filter.filter_job(job_20_days)
        
        assert eluta_result == False  # Too old for Eluta
        assert indeed_result == True   # Recent enough for Indeed
        
    def test_experience_level_filtering(self):
        """Test experience level filtering (0-2 years only)."""
        
        # Entry level job (should pass)
        entry_job = {
            "title": "Junior Software Developer",
            "summary": "Entry level position for recent graduates",
            "posted_date": "2 days ago"
        }
        
        # Senior level job (should fail)
        senior_job = {
            "title": "Senior Software Developer", 
            "summary": "5+ years experience required",
            "posted_date": "1 day ago"
        }
        
        # Test both filters
        for job_filter in [self.eluta_filter, self.indeed_filter]:
            entry_result, entry_enhanced = job_filter.filter_job(entry_job)
            senior_result, senior_enhanced = job_filter.filter_job(senior_job)
            
            assert entry_result == True
            assert entry_enhanced["experience_level"] == "Entry"
            
            assert senior_result == False
            assert senior_enhanced["experience_level"] == "Senior"
            
    def test_batch_filtering_performance(self):
        """Test batch filtering performance and accuracy."""
        
        # Create test job batch
        jobs = [
            {"title": "Junior Developer", "posted_date": "1 day ago", "summary": "Entry level"},
            {"title": "Senior Developer", "posted_date": "1 day ago", "summary": "5+ years exp"},
            {"title": "Developer", "posted_date": "30 days ago", "summary": "Join our team"},
            {"title": "Entry Level Analyst", "posted_date": "2 days ago", "summary": "No experience required"},
            {"title": "Lead Engineer", "posted_date": "5 days ago", "summary": "Team leadership"},
        ]
        
        # Test Eluta filtering (14-day limit)
        eluta_results = self.eluta_filter.filter_jobs_batch(jobs)
        
        # Should include: Junior Developer, Entry Level Analyst
        # Should exclude: Senior Developer (too senior), Developer (too old), Lead Engineer (too senior)
        assert len(eluta_results) == 2
        
        # Verify correct jobs were included
        included_titles = [job["title"] for job in eluta_results]
        assert "Junior Developer" in included_titles
        assert "Entry Level Analyst" in included_titles
        
        # Test Indeed filtering (124-day limit)
        indeed_results = self.indeed_filter.filter_jobs_batch(jobs)
        
        # Should include: Junior Developer, Developer (now recent enough), Entry Level Analyst
        # Should exclude: Senior Developer, Lead Engineer (too senior)
        assert len(indeed_results) == 3


class TestMultiBrowserContextSupport:
    """Test multi-browser context support and parallel processing."""
    
    @patch('scrapers.eluta_multi_browser.sync_playwright')
    @patch('scrapers.eluta_multi_browser.console')
    def test_multi_browser_initialization(self, mock_console, mock_playwright):
        """Test multi-browser scraper initialization."""
        from scrapers.eluta_multi_browser import ElutaMultiBrowserScraper
        
        profile = {
            "profile_name": "test_user",
            "keywords": ["developer", "analyst"],
            "location": "Toronto"
        }
        
        scraper = ElutaMultiBrowserScraper(profile, max_workers=2)
        
        # Check initialization
        assert scraper.max_workers == 2
        assert scraper.max_pages_per_keyword == 5  # Should be 5 as per memories
        assert hasattr(scraper, 'human_delays')
        assert hasattr(scraper, 'click_popup_framework')
        
    def test_human_delay_configurations(self):
        """Test that human delay configurations are properly set."""
        from scrapers.eluta_multi_browser import ElutaMultiBrowserScraper
        
        profile = {"profile_name": "test_user", "keywords": ["developer"]}
        scraper = ElutaMultiBrowserScraper(profile)
        
        # Check that human delays are configured as per memories
        assert scraper.human_delays["popup_wait"] == 3.0  # 3-second wait as per memories
        assert scraper.human_delays["between_jobs"] == (1.0, 2.0)  # 1-second delays as per memories
        assert scraper.human_delays["between_pages"] == (2.0, 4.0)
        assert scraper.human_delays["keyword_switch"] == (2.0, 4.0)


class TestErrorHandlingAndReliability:
    """Test error handling and reliability of the scraping system."""
    
    @patch('scrapers.human_behavior.console')
    def test_popup_timeout_handling(self, mock_console):
        """Test handling of popup timeouts."""
        framework = UniversalClickPopupFramework("eluta")
        
        # Mock elements that will timeout
        mock_link = Mock()
        mock_page = Mock()
        
        # Mock timeout exception
        mock_page.expect_popup.side_effect = Exception("Timeout")
        
        # Should handle timeout gracefully
        result = framework.execute_click_popup(mock_link, mock_page, "test-job")
        assert result is None
        
    @patch('scrapers.human_behavior.console')
    def test_missing_job_elements_handling(self, mock_console):
        """Test handling of missing job elements."""
        framework = UniversalClickPopupFramework("eluta")
        
        # Mock page with no job elements
        mock_page = Mock()
        mock_page.query_selector_all.return_value = []
        
        # Should handle gracefully
        elements = framework.find_job_elements(mock_page)
        assert len(elements) == 0
        
    def test_invalid_job_data_filtering(self):
        """Test filtering of invalid job data."""
        job_filter = UniversalJobFilter("eluta")
        
        # Test with missing required fields
        invalid_jobs = [
            {},  # Empty job
            {"title": ""},  # Empty title
            {"title": "Developer"},  # Missing other fields
        ]
        
        for invalid_job in invalid_jobs:
            # Should handle gracefully and apply default behavior
            is_suitable, enhanced_job = job_filter.filter_job(invalid_job)
            assert isinstance(is_suitable, bool)
            assert isinstance(enhanced_job, dict)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
