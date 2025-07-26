#!/usr/bin/env python3
"""
Cleaned-up Test Suite for AutoJobAgent
Removed redundant tests and fixed pytest patterns
Following DEVELOPMENT_STANDARDS.md principles
"""

import pytest
import time
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

console = Console()

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


# =================================================================
# FIXTURES
# =================================================================

@pytest.fixture
def test_profile():
    """Provide a test profile for testing."""
    return {
        'profile_name': 'test',
        'keywords': ['python', 'data analyst'],
        'skills': ['sql', 'machine learning'],
        'experience_years': 3,
        'location': 'Toronto, ON'
    }


# =================================================================
# MAIN APPLICATION TESTS
# =================================================================

class TestMainApplication:
    """Test suite for main application functionality."""
    
    def test_main_app_imports(self):
        """Test that main app can be imported and basic functions work."""
        import main
        assert hasattr(main, 'main'), "main() function not found"
        assert hasattr(main, 'parse_arguments'), "parse_arguments() function not found"
        assert callable(main.main)
    
    def test_main_app_argument_parsing(self):
        """Test main app argument parsing functionality."""
        import main
        
        # Test default arguments
        with patch('sys.argv', ['main.py']):
            args = main.parse_arguments()
            assert hasattr(args, 'action')
    
    def test_main_app_profile_loading(self):
        """Test profile loading functionality."""
        from src.utils.profile_helpers import get_available_profiles
        
        # Test that function exists and is callable
        assert callable(get_available_profiles)
        
        # Test basic functionality
        profiles = get_available_profiles()
        assert isinstance(profiles, list)
    
    def test_main_app_health_check(self):
        """Test main app health check functionality."""
        from src.core.job_database import get_job_db
        
        # Test database connection
        assert callable(get_job_db)
        
        # Test with mock profile
        with patch('src.utils.profile_helpers.load_profile') as mock_load:
            mock_load.return_value = {'profile_name': 'test'}
            db = get_job_db('test')
            assert db is not None


# =================================================================
# DASHBOARD TESTS
# =================================================================

class TestDashboard:
    """Test suite for dashboard functionality."""
    
    def test_dashboard_imports(self):
        """Test that dashboard components can be imported."""
        from src.dashboard.unified_dashboard import main as dashboard_main
        assert callable(dashboard_main)
    
    def test_dashboard_data_loading(self):
        """Test dashboard data loading functionality."""
        from src.dashboard.components.data_loader import load_job_data
        assert callable(load_job_data)
    
    def test_dashboard_system_metrics(self):
        """Test dashboard system metrics functionality."""
        from src.dashboard.components.metrics import render_metrics
        assert callable(render_metrics)
    
    def test_dashboard_css_constants(self):
        """Test that dashboard CSS constants are properly defined."""
        from src.dashboard.unified_dashboard import UNIFIED_CSS
        assert isinstance(UNIFIED_CSS, str)
        assert len(UNIFIED_CSS) > 0
    
    @pytest.mark.skipif(not HAS_STREAMLIT, reason="Streamlit not available")
    def test_dashboard_streamlit_compatibility(self):
        """Test dashboard compatibility with Streamlit (if available)."""
        import streamlit as st
        assert hasattr(st, 'title')
        assert hasattr(st, 'write')


# =================================================================
# SCRAPER TESTS
# =================================================================

class TestScrapers:
    """Test suite for scraper functionality."""
    
    def test_scraper_imports(self):
        """Test that scraper modules can be imported."""
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        from src.scrapers.enhanced_job_description_scraper import EnhancedJobDescriptionScraper
        
        assert ComprehensiveElutaScraper is not None
        assert ModernJobPipeline is not None
        assert EnhancedJobDescriptionScraper is not None
    
    def test_eluta_scraper_initialization(self, test_profile):
        """Test Eluta scraper initialization."""
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        
        with patch('src.utils.profile_helpers.load_profile') as mock_load:
            mock_load.return_value = test_profile
            
            with patch('src.core.job_database.get_job_db') as mock_db:
                mock_db.return_value = Mock()
                
                scraper = ComprehensiveElutaScraper("test")
                assert scraper.profile_name == "test"
                assert hasattr(scraper, 'search_terms')
    
    def test_modern_pipeline_initialization(self, test_profile):
        """Test Modern Job Pipeline initialization."""
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        
        mock_config = {
            'max_workers': 2,
            'enable_ai_analysis': False,
            'timeout': 10
        }
        
        with patch('src.core.job_database.get_job_db') as mock_db:
            mock_db.return_value = Mock()
            
            pipeline = ModernJobPipeline(test_profile, mock_config)
            assert hasattr(pipeline, 'profile')
            assert hasattr(pipeline, 'config')
    
    def test_scraper_models_and_utilities(self):
        """Test scraper supporting modules."""
        from src.scrapers.scraping_models import JobData, ScrapingTask, JobStatus
        from src.scrapers.session_manager import SessionManager
        from src.scrapers.human_behavior import HumanBehaviorMixin
        
        # Test basic instantiation
        job_data = JobData(basic_info={'title': 'Test Job'})
        assert job_data.basic_info['title'] == 'Test Job'
        
        task = ScrapingTask(task_id='test', task_type='basic_scrape', keyword='python', page_number=1)
        assert task.task_id == 'test'
    
    @pytest.mark.asyncio
    async def test_async_scraper_functionality(self, test_profile):
        """Test async functionality in scrapers."""
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        
        mock_config = {'max_workers': 1, 'enable_ai_analysis': False}
        
        with patch('src.core.job_database.get_job_db') as mock_db:
            mock_db.return_value = Mock()
            
            pipeline = ModernJobPipeline(test_profile, mock_config)
            assert hasattr(pipeline, 'run_optimized')


# =================================================================
# INTEGRATION TESTS
# =================================================================

class TestIntegration:
    """Test suite for integration functionality."""
    
    def test_database_integration(self, test_profile):
        """Test database integration across components."""
        from src.core.job_database import get_job_db
        
        with patch('src.utils.profile_helpers.load_profile') as mock_load:
            mock_load.return_value = test_profile
            
            db = get_job_db('test')
            assert db is not None
            assert hasattr(db, 'add_job')
    
    def test_profile_integration(self, test_profile):
        """Test profile integration across components."""
        from src.utils.profile_helpers import load_profile, get_available_profiles
        
        with patch('src.utils.profile_helpers.load_profile') as mock_load:
            mock_load.return_value = test_profile
            
            profile = load_profile('test')
            assert profile is not None
            assert profile['profile_name'] == 'test'
    
    def test_pipeline_integration(self, test_profile):
        """Test pipeline integration between scrapers and processors."""
        from src.scrapers.modern_job_pipeline import ModernJobPipeline
        
        mock_config = {'max_workers': 1, 'enable_ai_analysis': False}
        
        with patch('src.core.job_database.get_job_db') as mock_db:
            mock_db.return_value = Mock()
            
            pipeline = ModernJobPipeline(test_profile, mock_config)
            assert hasattr(pipeline, 'profile')
            assert hasattr(pipeline, 'config')


# =================================================================
# PERFORMANCE TESTS
# =================================================================

class TestPerformance:
    """Test suite for performance monitoring."""
    
    def test_import_performance(self):
        """Test import performance of key modules."""
        import_times = {}
        
        # Test main imports
        start_time = time.time()
        import main
        import_times['main'] = time.time() - start_time
        
        # Test dashboard imports
        start_time = time.time()
        from src.dashboard.unified_dashboard import main as dashboard_main
        import_times['dashboard'] = time.time() - start_time
        
        # Test scraper imports
        start_time = time.time()
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        import_times['scrapers'] = time.time() - start_time
        
        # Assert reasonable import times (< 2 seconds each)
        for module, import_time in import_times.items():
            assert import_time < 2.0, f"{module} import took too long: {import_time:.2f}s"
    
    def test_memory_usage(self):
        """Test memory usage of key components."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Import heavy modules
        from src.scrapers.comprehensive_eluta_scraper import ComprehensiveElutaScraper
        from src.dashboard.unified_dashboard import main as dashboard_main
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Assert reasonable memory usage (< 100MB increase)
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase:.1f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])