"""
Test Simplified Scraping Architecture

Tests the simplified scraping methods:
1. Simple Sequential Method
2. Multi-Worker Method
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.cli.handlers.scraping_handler import ScrapingHandler


class TestSimplifiedScraping:
    """Test the simplified scraping architecture."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.profile = {
            'profile_name': 'test_profile',
            'keywords': ['python', 'developer'],
            'location': 'Toronto, ON'
        }
        self.scraping_handler = ScrapingHandler(self.profile)
    
    def test_validate_scraping_mode_simple(self):
        """Test validation of simple scraping mode."""
        mode = self.scraping_handler._validate_scraping_mode("simple")
        assert mode == "simple"
    
    def test_validate_scraping_mode_multi_worker(self):
        """Test validation of multi-worker scraping mode."""
        mode = self.scraping_handler._validate_scraping_mode("multi_worker")
        assert mode == "multi_worker"
    
    def test_validate_scraping_mode_aliases(self):
        """Test validation of scraping mode aliases."""
        assert self.scraping_handler._validate_scraping_mode("multi-worker") == "multi_worker"
        assert self.scraping_handler._validate_scraping_mode("multiworker") == "multi_worker"
    
    def test_validate_scraping_mode_invalid(self):
        """Test validation of invalid scraping mode."""
        with pytest.raises(ValueError, match="Invalid scraping mode"):
            self.scraping_handler._validate_scraping_mode("invalid_mode")
    
    def test_get_scraping_mode_description(self):
        """Test getting scraping mode descriptions."""
        simple_desc = self.scraping_handler._get_scraping_mode_description("simple")
        assert "Simple Sequential" in simple_desc
        assert "Reliable" in simple_desc
        
        multi_desc = self.scraping_handler._get_scraping_mode_description("multi_worker")
        assert "Multi-Worker" in multi_desc
        assert "High-performance" in multi_desc
    
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_run_simple_scraping_success(self, mock_run_scraping):
        """Test successful simple sequential scraping."""
        # Mock successful scraping
        mock_jobs = [
            {'title': 'Python Developer', 'company': 'Tech Corp', 'url': 'https://example.com/job1'},
            {'title': 'Software Engineer', 'company': 'Startup Inc', 'url': 'https://example.com/job2'}
        ]
        mock_run_scraping.return_value = mock_jobs
        
        # Mock session save
        with patch.object(self.scraping_handler, '_save_session') as mock_save:
            success = self.scraping_handler._run_simple_scraping(['eluta'], ['python'])
            
            assert success is True
            mock_run_scraping.assert_called_once()
            mock_save.assert_called_once()
    
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_run_simple_scraping_no_jobs(self, mock_run_scraping):
        """Test simple sequential scraping with no jobs found."""
        # Mock no jobs found
        mock_run_scraping.return_value = []
        
        success = self.scraping_handler._run_simple_scraping(['eluta'], ['python'])
        
        assert success is False
        mock_run_scraping.assert_called_once()
    
    @patch('src.core.job_processor_queue.create_job_processor_queue')
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_run_multi_worker_scraping_success(self, mock_run_scraping, mock_create_queue):
        """Test successful multi-worker scraping."""
        # Mock successful scraping
        mock_jobs = [
            {'title': 'Python Developer', 'company': 'Tech Corp', 'url': 'https://example.com/job1'},
            {'title': 'Software Engineer', 'company': 'Startup Inc', 'url': 'https://example.com/job2'}
        ]
        mock_run_scraping.return_value = mock_jobs
        
        # Mock queue
        mock_queue = Mock()
        mock_queue.get_stats.return_value = {'total_processed': 2, 'successful': 2}
        mock_create_queue.return_value = mock_queue
        
        success = self.scraping_handler._run_multi_worker_scraping(['eluta'], ['python'])
        
        assert success is True
        mock_run_scraping.assert_called_once()
        mock_create_queue.assert_called_once()
        mock_queue.start.assert_called_once()
        mock_queue.add_jobs_from_scraping.assert_called_once_with(mock_jobs)
        mock_queue.wait_for_completion.assert_called_once()
        mock_queue.stop.assert_called_once()
    
    @patch('src.scrapers.comprehensive_eluta_scraper.run_comprehensive_scraping')
    def test_run_multi_worker_scraping_no_jobs(self, mock_run_scraping):
        """Test multi-worker scraping with no jobs found."""
        # Mock no jobs found
        mock_run_scraping.return_value = []
        
        success = self.scraping_handler._run_multi_worker_scraping(['eluta'], ['python'])
        
        assert success is False
        mock_run_scraping.assert_called_once()
    
    def test_run_scraping_default_mode(self):
        """Test run_scraping with default mode."""
        with patch.object(self.scraping_handler, '_run_simple_scraping') as mock_simple:
            mock_simple.return_value = True
            
            success = self.scraping_handler.run_scraping()
            
            assert success is True
            mock_simple.assert_called_once_with(['eluta'], ['python', 'developer'])
    
    def test_run_scraping_simple_mode(self):
        """Test run_scraping with simple mode."""
        with patch.object(self.scraping_handler, '_run_simple_scraping') as mock_simple:
            mock_simple.return_value = True
            
            success = self.scraping_handler.run_scraping(mode="simple")
            
            assert success is True
            mock_simple.assert_called_once_with(['eluta'], ['python', 'developer'])
    
    def test_run_scraping_multi_worker_mode(self):
        """Test run_scraping with multi_worker mode."""
        with patch.object(self.scraping_handler, '_run_multi_worker_scraping') as mock_multi:
            mock_multi.return_value = True
            
            success = self.scraping_handler.run_scraping(mode="multi_worker")
            
            assert success is True
            mock_multi.assert_called_once_with(['eluta'], ['python', 'developer'])
    
    def test_run_scraping_invalid_mode(self):
        """Test run_scraping with invalid mode."""
        success = self.scraping_handler.run_scraping(mode="invalid_mode")
        
        assert success is False
    
    def test_run_scraping_custom_sites_and_keywords(self):
        """Test run_scraping with custom sites and keywords."""
        with patch.object(self.scraping_handler, '_run_simple_scraping') as mock_simple:
            mock_simple.return_value = True
            
            success = self.scraping_handler.run_scraping(
                sites=['indeed', 'linkedin'],
                keywords=['javascript', 'react']
            )
            
            assert success is True
            mock_simple.assert_called_once_with(['indeed', 'linkedin'], ['javascript', 'react']) 