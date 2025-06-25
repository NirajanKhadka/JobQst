"""
Integration tests for the enhanced click-and-popup job scraping system.
Tests the complete workflow from CLI to scraping to filtering.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestScrapingWorkflowIntegration:
    """Test the complete scraping workflow integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_profile = {
            "profile_name": "test_user",
            "name": "Test User",
            "email": "test@example.com",
            "location": "Toronto, ON",
            "keywords": ["software developer", "data analyst", "junior developer"],
            "experience_level": "entry",
            "batch_default": 10
        }
        
    @patch("src.scrapers.working_eluta_scraper.sync_playwright")
    @patch("src.scrapers.working_eluta_scraper.console")
    def test_eluta_working_scraper_integration(self, mock_console, mock_playwright):
        """Test the enhanced Eluta working scraper integration."""
        from src.scrapers.working_eluta_scraper import WorkingElutaScraper as ElutaWorkingScraper
        
        # Mock browser context
        mock_context = Mock()
        mock_page = Mock()
        mock_context.new_page.return_value = mock_page
        
        # Mock job elements
        mock_job_elem = Mock()
        mock_job_elem.inner_text.return_value = "Software Developer\nTech Corp\nToronto, ON\nEntry level position"
        mock_job_elem.query_selector_all.return_value = [Mock()]  # Mock links
        
        mock_page.query_selector_all.return_value = [mock_job_elem]
        mock_page.url = "https://www.eluta.ca/search"
        
        # Create scraper
        scraper = ElutaWorkingScraper(self.test_profile, browser_context=mock_context)
        
        # Verify initialization
        assert scraper.base_url == "https://www.eluta.ca/search"
        assert scraper.profile == self.test_profile
        
    def test_job_filter_integration(self):
        """Test job filter integration with scraped data."""
        from src.utils.job_filters import UniversalJobFilter
        
        # Create filter
        job_filter = UniversalJobFilter()
        
        # Test job data that should pass filtering
        good_job = {
            "title": "Junior Software Developer",
            "company": "Tech Corp",
            "location": "Toronto, ON",
            "summary": "Entry level position for recent graduates",
            "posted_date": "2 days ago",
            "url": "https://example.com/job/123",
            "site": "eluta"
        }
        
        # Test job data that should fail filtering
        bad_job = {
            "title": "Senior Software Developer",
            "company": "Tech Corp", 
            "location": "Toronto, ON",
            "summary": "5+ years experience required",
            "posted_date": "30 days ago",
            "url": "https://example.com/job/456",
            "site": "eluta"
        }
        
        # Apply filtering
        good_result, good_enhanced = job_filter.filter_job(good_job)
        bad_result, bad_enhanced = job_filter.filter_job(bad_job)
        
        # Verify results
        assert good_result == True
        assert good_enhanced["experience_level"] == "Entry"
        assert good_enhanced["filter_passed"] == True
        
        assert bad_result == False  # Should fail due to being too old for Eluta (14-day limit)
        
    @patch("src.scrapers.human_behavior.console")
    def test_universal_click_popup_framework_integration(self, mock_console):
        """Test universal click-popup framework integration."""
        from src.scrapers.human_behavior import UniversalClickPopupFramework
        
        # Test framework for different sites
        sites = ["eluta", "indeed", "jobbank"]
        
        for site in sites:
            framework = UniversalClickPopupFramework(site)
            
            # Verify site-specific configuration
            assert framework.site_name == site
            assert "job_selector" in framework.current_config
            assert "popup_wait" in framework.current_config
            
            # Verify site-specific popup wait times
            if site == "eluta":
                assert framework.current_config["popup_wait"] == 3.0  # 3 seconds as per memories
            
    def test_human_behavior_integration(self):
        """Test human behavior integration with scrapers."""
        from src.scrapers.human_behavior import HumanBehaviorScraper, HumanBehaviorConfig
        
        # Create test scraper with human behavior
        class TestScraper(HumanBehaviorScraper):
            def __init__(self, profile):
                super().__init__(profile)
                self.site_name = "eluta"
        
        scraper = TestScraper(self.test_profile)
        
        # Verify human behavior configuration
        assert hasattr(scraper, 'human_config')
        assert isinstance(scraper.human_config, HumanBehaviorConfig)
        
        # Verify delay configurations match memories
        assert scraper.human_config.delays["popup_wait"] == 3.0  # 3-second wait
        assert scraper.human_config.delays["between_jobs"] == (1.0, 2.0)  # 1-second delays
        
        # Verify cookie and tab settings
        assert scraper.human_config.cookie_settings["save_cookies"] == True
        assert scraper.human_config.tab_settings["close_tabs_immediately"] == True


class TestCLIIntegration:
    """Test CLI integration with enhanced scrapers."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_profile = {
            "profile_name": "test_user",
            "keywords": ["developer"],
            "location": "Toronto"
        }
        
    @patch("src.app.console")
    def test_scraping_menu_options(self, mock_console):
        """Test that scraping menu shows enhanced options."""
        from src.app import scraping_menu_action
        
        # Mock args
        mock_args = Mock()
        
        # This would normally show the menu - we're testing the structure exists
        # The actual menu interaction would require more complex mocking
        
        # Verify the enhanced options are available in the code
        # (This is more of a smoke test to ensure the functions exist)
        from src.app import eluta_enhanced_click_popup_scrape, eluta_multi_browser_scrape
        
        assert callable(eluta_enhanced_click_popup_scrape)
        assert callable(eluta_multi_browser_scrape)
        
    @patch("src.scrapers.working_eluta_scraper.WorkingElutaScraper")
    @patch("playwright.sync_api.sync_playwright")
    @patch("src.app.console")
    def test_enhanced_click_popup_scrape_function(self, mock_console, mock_playwright, mock_scraper_class):
        """Test the enhanced click-popup scrape function."""
        from src.app import eluta_enhanced_click_popup_scrape
        
        # Mock the scraper
        mock_scraper = Mock()
        mock_scraper.scrape_jobs.return_value = [
            {
                "title": "Junior Developer",
                "company": "Tech Corp",
                "experience_level": "Entry",
                "filter_passed": True
            }
        ]
        mock_scraper_class.return_value = mock_scraper
        
        # Mock playwright
        mock_browser = Mock()
        mock_context = Mock()
        mock_browser.new_context.return_value = mock_context
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        
        # Run the function
        jobs = eluta_enhanced_click_popup_scrape(self.test_profile)
        
        # Verify results
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Junior Developer"
        assert jobs[0]["experience_level"] == "Entry"
        
        # Verify scraper was configured correctly
        mock_scraper_class.assert_called_once()
        assert mock_scraper.max_age_days == 14  # 14-day filter
        assert mock_scraper.max_pages_per_keyword == 5  # 5 pages minimum


class TestErrorHandlingIntegration:
    """Test error handling across the integrated system."""
    
    def test_graceful_failure_handling(self):
        """Test that the system handles failures gracefully."""
        from src.utils.job_filters import UniversalJobFilter
        
        job_filter = UniversalJobFilter()
        
        # Test with malformed job data
        malformed_jobs = [
            {},  # Empty job
            {"title": None},  # None title
            {"posted_date": "invalid date"},  # Invalid date
        ]
        
        for job in malformed_jobs:
            # Should not raise exceptions
            try:
                is_suitable, enhanced_job = job_filter.filter_job(job)
                assert isinstance(is_suitable, bool)
                assert isinstance(enhanced_job, dict)
            except Exception as e:
                pytest.fail(f"Filter should handle malformed data gracefully: {e}")
                
    @patch("src.scrapers.human_behavior.console")
    def test_popup_failure_handling(self, mock_console):
        """Test popup failure handling."""
        from src.scrapers.human_behavior import UniversalClickPopupFramework
        
        framework = UniversalClickPopupFramework("eluta")
        
        # Mock elements that will fail
        mock_link = Mock()
        mock_page = Mock()
        mock_page.expect_popup.side_effect = Exception("Popup failed")
        
        # Should handle failure gracefully
        result = framework.execute_click_popup(mock_link, mock_page, "test-job")
        assert result is None  # Should return None on failure, not raise exception


class TestPerformanceIntegration:
    """Test performance aspects of the integrated system."""
    
    def test_batch_processing_efficiency(self):
        """Test that batch processing is efficient."""
        from src.utils.job_filters import UniversalJobFilter
        
        job_filter = UniversalJobFilter("indeed")  # Use Indeed for 124-day limit
        
        # Create a large batch of test jobs
        jobs = []
        for i in range(100):
            jobs.append({
                "title": f"Developer {i}",
                "company": f"Company {i}",
                "posted_date": "5 days ago",
                "summary": "Entry level position"
            })
        
        # Time the batch processing (should be fast)
        import time
        start_time = time.time()
        
        filtered_jobs = job_filter.filter_jobs_batch(jobs)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 100 jobs quickly (under 1 second)
        assert processing_time < 1.0
        assert len(filtered_jobs) == 100  # All should pass (entry level, recent)


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
