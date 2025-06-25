"""
Integration Tests for Simplified Scraping Architecture

Tests the complete workflow of the simplified scraping system:
1. Simple Sequential Method
2. Multi-Worker Method

Uses mocks for fast execution while testing the handler logic.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.cli.handlers.scraping_handler import ScrapingHandler
from src.core.job_processor_queue import JobProcessorQueue


class TestSimplifiedScrapingIntegration:
    """Integration tests for the simplified scraping architecture."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_profile = {
            "profile_name": "test_integration",
            "name": "Test User",
            "email": "test@example.com",
            "location": "Toronto, ON",
            "keywords": ["python developer", "data analyst"],
            "skills": ["Python", "SQL", "JavaScript"],
            "experience_level": "entry",
            "batch_default": 5
        }
        
        # Mock job data for testing
        self.mock_jobs = [
            {
                "title": "Junior Python Developer",
                "company": "Tech Corp",
                "location": "Toronto, ON",
                "url": "https://example.com/job/1",
                "site": "eluta",
                "posted_date": "2025-06-24",
                "experience_level": "entry",
                "confidence_score": 0.85
            },
            {
                "title": "Data Analyst",
                "company": "Data Corp",
                "location": "Toronto, ON", 
                "url": "https://example.com/job/2",
                "site": "eluta",
                "posted_date": "2025-06-23",
                "experience_level": "entry",
                "confidence_score": 0.90
            }
        ]
    
    @patch('src.cli.handlers.scraping_handler.console')
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_simple_sequential_scraping_integration(self, mock_run_scraping, mock_console):
        """Test simple sequential scraping mode integration."""
        # Mock scraping function
        mock_run_scraping.return_value = self.mock_jobs
        
        # Create scraping handler
        handler = ScrapingHandler(self.test_profile)
        
        # Run simple sequential scraping
        result = handler.run_scraping(mode="simple")
        
        # Verify results
        assert result == True
        mock_run_scraping.assert_called()
        
        # Verify console output
        mock_console.print.assert_called()
    
    @patch('src.cli.handlers.scraping_handler.console')
    @patch('src.core.job_processor_queue.create_job_processor_queue')
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_multi_worker_scraping_integration(self, mock_run_scraping, mock_create_queue, mock_console):
        """Test multi-worker scraping mode integration."""
        # Mock scraping function
        mock_run_scraping.return_value = self.mock_jobs
        
        # Mock job processor queue
        mock_queue = Mock()
        mock_queue.start.return_value = None
        mock_queue.add_jobs_from_scraping.return_value = None
        mock_queue.wait_for_completion.return_value = None
        mock_queue.stop.return_value = None
        mock_queue.get_stats.return_value = {
            'total_processed': 2,
            'successful': 2,
            'failed': 0
        }
        mock_create_queue.return_value = mock_queue
        
        # Create scraping handler
        handler = ScrapingHandler(self.test_profile)
        
        # Run multi-worker scraping
        result = handler.run_scraping(mode="multi_worker")
        
        # Verify results
        assert result == True
        mock_create_queue.assert_called()
        mock_queue.start.assert_called()
        mock_queue.add_jobs_from_scraping.assert_called()
        mock_queue.wait_for_completion.assert_called()
        mock_queue.stop.assert_called()
        
        # Verify console output
        mock_console.print.assert_called()
    
    @patch('src.cli.handlers.scraping_handler.console')
    def test_scraping_mode_validation_integration(self, mock_console):
        """Test scraping mode validation integration."""
        handler = ScrapingHandler(self.test_profile)
        
        # Test valid modes
        assert handler._validate_scraping_mode("simple") == "simple"
        assert handler._validate_scraping_mode("multi_worker") == "multi_worker"
        assert handler._validate_scraping_mode("multi-worker") == "multi_worker"
        assert handler._validate_scraping_mode("MULTI_WORKER") == "multi_worker"
        
        # Test invalid mode
        with pytest.raises(ValueError):
            handler._validate_scraping_mode("invalid_mode")
    
    @patch('src.cli.handlers.scraping_handler.console')
    def test_scraping_mode_descriptions_integration(self, mock_console):
        """Test scraping mode description integration."""
        handler = ScrapingHandler(self.test_profile)
        
        # Test descriptions
        simple_desc = handler._get_scraping_mode_description("simple")
        multi_desc = handler._get_scraping_mode_description("multi_worker")
        
        assert "Simple Sequential" in simple_desc
        assert "Multi-Worker" in multi_desc
        assert "reliable" in simple_desc.lower()
        assert "performance" in multi_desc.lower()
    
    @patch('src.cli.handlers.scraping_handler.console')
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_error_handling_integration(self, mock_run_scraping, mock_console):
        """Test error handling integration in scraping."""
        # Mock scraping function that raises an exception
        mock_run_scraping.side_effect = Exception("Scraping failed")
        
        # Create scraping handler
        handler = ScrapingHandler(self.test_profile)
        
        # Run scraping (should handle error gracefully)
        result = handler.run_scraping(mode="simple")
        
        # Verify error handling
        assert result == False
        mock_console.print.assert_called()
        
        # Check that error message was logged
        error_calls = [call for call in mock_console.print.call_args_list 
                      if any('error' in str(call).lower() or 'failed' in str(call).lower() for call in [call])]
        assert len(error_calls) > 0
    
    @patch('src.cli.handlers.scraping_handler.console')
    def test_profile_loading_integration(self, mock_console):
        """Test profile loading integration."""
        handler = ScrapingHandler(self.test_profile)
        
        # Verify profile is loaded correctly
        assert handler.profile == self.test_profile
        assert handler.profile.get("keywords") == ["python developer", "data analyst"]
        assert handler.profile.get("location") == "Toronto, ON"
    
    @patch('src.cli.handlers.scraping_handler.console')
    def test_default_behavior_integration(self, mock_console):
        """Test default behavior integration."""
        handler = ScrapingHandler(self.test_profile)
        
        # Test that handler is initialized correctly
        assert handler.profile == self.test_profile
        assert handler.profile.get("keywords") == ["python developer", "data analyst"]


class TestScrapingHandlerEndToEnd:
    """End-to-end tests for the scraping handler workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_profile = {
            "profile_name": "test_e2e",
            "keywords": ["python developer"],
            "location": "Toronto, ON"
        }
    
    @patch('src.cli.handlers.scraping_handler.console')
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_complete_simple_workflow(self, mock_run_scraping, mock_console):
        """Test complete simple scraping workflow."""
        # Mock scraper with realistic job data
        mock_jobs = [
            {
                "title": "Junior Python Developer",
                "company": "Tech Corp",
                "location": "Toronto, ON",
                "url": "https://example.com/job/1",
                "site": "eluta",
                "posted_date": datetime.now().strftime("%Y-%m-%d"),
                "experience_level": "entry",
                "confidence_score": 0.85
            }
        ]
        
        mock_run_scraping.return_value = mock_jobs
        
        # Create handler and run workflow
        handler = ScrapingHandler(self.test_profile)
        result = handler.run_scraping(mode="simple")
        
        # Verify complete workflow
        assert result == True
        mock_run_scraping.assert_called()
        
        # Verify console output shows progress
        console_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Running simple job scraping" in call for call in console_calls)
        assert any("Simple Sequential" in call for call in console_calls)
    
    @patch('src.cli.handlers.scraping_handler.console')
    @patch('src.core.job_processor_queue.create_job_processor_queue')
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_complete_multi_worker_workflow(self, mock_run_scraping, mock_create_queue, mock_console):
        """Test complete multi-worker scraping workflow."""
        # Mock scraping function
        mock_jobs = [
            {
                "title": "Junior Python Developer",
                "company": "Tech Corp",
                "location": "Toronto, ON",
                "url": "https://example.com/job/1",
                "site": "eluta",
                "posted_date": datetime.now().strftime("%Y-%m-%d"),
                "experience_level": "entry",
                "confidence_score": 0.85
            }
        ]
        mock_run_scraping.return_value = mock_jobs
        
        # Mock queue with realistic stats
        mock_queue = Mock()
        mock_queue.get_stats.return_value = {
            'total_processed': 5,
            'successful': 4,
            'failed': 1,
            'queue_size': 0
        }
        mock_create_queue.return_value = mock_queue
        
        # Create handler and run workflow
        handler = ScrapingHandler(self.test_profile)
        result = handler.run_scraping(mode="multi_worker")
        
        # Verify complete workflow
        assert result == True
        mock_create_queue.assert_called()
        mock_queue.start.assert_called()
        mock_queue.add_jobs_from_scraping.assert_called()
        mock_queue.wait_for_completion.assert_called()
        mock_queue.stop.assert_called()
        
        # Verify console output shows progress
        console_calls = [str(call) for call in mock_console.print.call_args_list]
        assert any("Running multi_worker job scraping" in call for call in console_calls)
        assert any("Multi-Worker" in call for call in console_calls) 