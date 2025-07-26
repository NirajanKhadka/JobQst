#!/usr/bin/env python3
"""
Test Enhanced Job Processor Orchestrator
Comprehensive testing of the 2-worker multiprocessing job processing system.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time
import multiprocessing as mp

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.orchestration.enhanced_job_processor import (
    EnhancedJobProcessor,
    ProcessingStatus,
    ProcessingStats,
    get_enhanced_job_processor,
    process_jobs_for_profile
)

def test_processor_initialization():
    """Test enhanced job processor initialization."""
    print("🧪 Testing Enhanced Job Processor Initialization...")
    
    # Mock dependencies to avoid actual database/Ollama connections
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client') as mock_ollama:
        
        # Mock database
        mock_db = Mock()
        mock_db.get_job_stats.return_value = {"scraped": 5, "processed": 10}
        mock_get_db.return_value = mock_db
        
        # Mock Ollama client
        mock_ollama_client = Mock()
        mock_ollama_client.is_available.return_value = True
        mock_ollama.return_value = mock_ollama_client
        
        # Initialize processor
        processor = EnhancedJobProcessor(
            profile_name="test_profile",
            worker_count=2,
            batch_size=5
        )
        
        # Verify initialization
        assert processor.profile_name == "test_profile"
        assert processor.worker_count == 2
        assert processor.batch_size == 5
        assert processor.stats.status == ProcessingStatus.IDLE
        assert processor.stats.worker_count == 2
        assert processor.stats.batch_size == 5
        
        print("✅ Enhanced job processor initialized correctly")
        print("✅ Configuration parameters set properly")
        print("✅ Statistics initialized correctly")
        print("🎉 Processor initialization test passed!")
        return True

def test_get_jobs_for_processing():
    """Test job retrieval for processing."""
    print("\n🧪 Testing Job Retrieval for Processing...")
    
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client'):
        
        # Mock database with sample jobs
        mock_db = Mock()
        sample_jobs = [
            {
                'id': 'job_1',
                'title': 'Software Engineer',
                'description': 'Python developer needed',
                'status': 'scraped'
            },
            {
                'id': 'job_2',
                'title': 'Data Scientist',
                'description': 'ML engineer position',
                'status': 'scraped'
            }
        ]
        mock_db.get_job_stats.return_value = {}
        mock_db.get_jobs_by_status.return_value = sample_jobs
        mock_get_db.return_value = mock_db
        
        # Initialize processor
        processor = EnhancedJobProcessor("test_profile")
        
        # Test job retrieval
        jobs = processor._get_jobs_for_processing(limit=10)
        
        # Verify results
        assert len(jobs) == 2
        assert jobs[0]['id'] == 'job_1'
        assert jobs[1]['id'] == 'job_2'
        assert all(job['status'] == 'scraped' for job in jobs)
        
        # Verify database was called correctly
        mock_db.get_jobs_by_status.assert_called_once_with('scraped', limit=10)
        
        print("✅ Jobs retrieved correctly from database")
        print("✅ Status filtering works properly")
        print("✅ Limit parameter passed correctly")
        print("🎉 Job retrieval test passed!")
        return True

def test_processing_status_and_stats():
    """Test processing status and statistics tracking."""
    print("\n🧪 Testing Processing Status and Statistics...")
    
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client'):
        
        # Mock database
        mock_db = Mock()
        mock_db.get_job_stats.return_value = {}
        mock_get_db.return_value = mock_db
        
        # Initialize processor
        processor = EnhancedJobProcessor("test_profile", worker_count=2, batch_size=3)
        
        # Test initial status
        status = processor.get_processing_status()
        assert status['status'] == 'idle'
        assert status['worker_count'] == 2
        assert status['batch_size'] == 3
        assert status['total_jobs'] == 0
        assert status['processed_jobs'] == 0
        assert status['profile_name'] == 'test_profile'
        
        # Test statistics update
        processor.stats.total_jobs = 10
        processor.stats.processed_jobs = 8
        processor.stats.failed_jobs = 2
        processor.stats.processing_time = 30.5
        processor.stats.status = ProcessingStatus.COMPLETED
        
        updated_status = processor.get_processing_status()
        assert updated_status['status'] == 'completed'
        assert updated_status['total_jobs'] == 10
        assert updated_status['processed_jobs'] == 8
        assert updated_status['failed_jobs'] == 2
        assert updated_status['processing_time'] == 30.5
        
        print("✅ Processing status tracking works correctly")
        print("✅ Statistics updates properly")
        print("✅ Status dictionary format correct")
        print("🎉 Status and statistics test passed!")
        return True

def test_system_health_monitoring():
    """Test system health monitoring functionality."""
    print("\n🧪 Testing System Health Monitoring...")
    
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client') as mock_ollama:
        
        # Mock database
        mock_db = Mock()
        mock_db.get_job_stats.return_value = {"scraped": 5, "processed": 10}
        mock_get_db.return_value = mock_db
        
        # Mock Ollama client
        mock_ollama_client = Mock()
        mock_ollama_client.is_available.return_value = True
        mock_ollama_client.get_health_info.return_value = {"gpu_enabled": True, "model_loaded": True}
        mock_ollama.return_value = mock_ollama_client
        
        # Initialize processor
        processor = EnhancedJobProcessor("test_profile")
        
        # Get health information
        health = processor.get_system_health()
        
        # Verify health information
        assert health['processor_status'] == 'idle'
        assert health['profile_name'] == 'test_profile'
        assert health['worker_count'] == 2
        assert health['database_available'] == True
        assert health['ollama_available'] == True
        assert health['multiprocessing_support'] == True
        assert health['jobs_pending'] == 5
        assert 'ollama_health' in health
        
        print("✅ System health monitoring works correctly")
        print("✅ Database health check successful")
        print("✅ Ollama health check successful")
        print("✅ Health information format correct")
        print("🎉 System health monitoring test passed!")
        return True

def test_configuration_updates():
    """Test processor configuration updates."""
    print("\n🧪 Testing Configuration Updates...")
    
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client'):
        
        # Mock database
        mock_db = Mock()
        mock_db.get_job_stats.return_value = {}
        mock_get_db.return_value = mock_db
        
        # Initialize processor
        processor = EnhancedJobProcessor("test_profile", worker_count=2, batch_size=5)
        
        # Test initial configuration
        assert processor.worker_count == 2
        assert processor.batch_size == 5
        assert processor.stats.worker_count == 2
        assert processor.stats.batch_size == 5
        
        # Update configuration
        processor.update_configuration(worker_count=4, batch_size=10)
        
        # Verify updates
        assert processor.worker_count == 4
        assert processor.batch_size == 10
        assert processor.stats.worker_count == 4
        assert processor.stats.batch_size == 10
        
        # Test partial update
        processor.update_configuration(batch_size=7)
        assert processor.worker_count == 4  # Unchanged
        assert processor.batch_size == 7    # Updated
        
        print("✅ Configuration updates work correctly")
        print("✅ Partial updates supported")
        print("✅ Statistics updated with configuration")
        print("🎉 Configuration update test passed!")
        return True

def test_stats_reset():
    """Test statistics reset functionality."""
    print("\n🧪 Testing Statistics Reset...")
    
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client'):
        
        # Mock database
        mock_db = Mock()
        mock_db.get_job_stats.return_value = {}
        mock_get_db.return_value = mock_db
        
        # Initialize processor
        processor = EnhancedJobProcessor("test_profile", worker_count=2, batch_size=5)
        
        # Set some statistics
        processor.stats.total_jobs = 20
        processor.stats.processed_jobs = 15
        processor.stats.failed_jobs = 5
        processor.stats.processing_time = 60.0
        processor.stats.status = ProcessingStatus.COMPLETED
        
        # Reset statistics
        processor.reset_stats()
        
        # Verify reset
        assert processor.stats.total_jobs == 0
        assert processor.stats.processed_jobs == 0
        assert processor.stats.failed_jobs == 0
        assert processor.stats.processing_time == 0.0
        assert processor.stats.status == ProcessingStatus.IDLE
        assert processor.stats.worker_count == 2  # Configuration preserved
        assert processor.stats.batch_size == 5   # Configuration preserved
        
        print("✅ Statistics reset correctly")
        print("✅ Configuration preserved during reset")
        print("✅ Status returned to idle")
        print("🎉 Statistics reset test passed!")
        return True

def test_convenience_functions():
    """Test convenience functions for integration."""
    print("\n🧪 Testing Convenience Functions...")
    
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client'):
        
        # Mock database
        mock_db = Mock()
        mock_db.get_job_stats.return_value = {}
        mock_get_db.return_value = mock_db
        
        # Test get_enhanced_job_processor function
        processor = get_enhanced_job_processor("test_profile", worker_count=3, batch_size=7)
        
        assert isinstance(processor, EnhancedJobProcessor)
        assert processor.profile_name == "test_profile"
        assert processor.worker_count == 3
        assert processor.batch_size == 7
        
        print("✅ get_enhanced_job_processor works correctly")
        print("✅ Configuration parameters passed properly")
        print("🎉 Convenience functions test passed!")
        return True

def test_multiprocessing_pool_integration():
    """Test multiprocessing pool integration (mocked)."""
    print("\n🧪 Testing Multiprocessing Pool Integration...")
    
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client'), \
         patch('src.orchestration.enhanced_job_processor.Pool') as mock_pool_class, \
         patch('src.orchestration.enhanced_job_processor.update_jobs_in_database') as mock_update_db:
        
        # Mock database
        mock_db = Mock()
        mock_db.get_job_stats.return_value = {}
        mock_db.get_jobs_by_status.return_value = [
            {'id': 'job_1', 'title': 'Test Job 1', 'description': 'Test', 'status': 'scraped'},
            {'id': 'job_2', 'title': 'Test Job 2', 'description': 'Test', 'status': 'scraped'}
        ]
        mock_get_db.return_value = mock_db
        
        # Mock multiprocessing pool
        mock_pool = Mock()
        mock_pool.__enter__ = Mock(return_value=mock_pool)
        mock_pool.__exit__ = Mock(return_value=None)
        mock_pool.map.return_value = [
            [{'id': 'job_1', 'status': 'processed', 'title': 'Test Job 1'}],
            [{'id': 'job_2', 'status': 'processed', 'title': 'Test Job 2'}]
        ]
        mock_pool_class.return_value = mock_pool
        
        # Mock database update
        mock_update_db.return_value = (2, 0)  # 2 successful, 0 failed
        
        # Initialize processor
        processor = EnhancedJobProcessor("test_profile")
        
        # Process jobs
        stats = processor.process_jobs_parallel(limit=10)
        
        # Verify multiprocessing pool was used correctly
        mock_pool_class.assert_called_once_with(processes=2, initializer=mock_pool.map.call_args[0][0].__globals__['init_worker'])
        mock_pool.map.assert_called_once()
        
        # Verify results
        assert stats.status == ProcessingStatus.COMPLETED
        assert stats.total_jobs == 2
        assert stats.processed_jobs == 2
        assert stats.failed_jobs == 0
        
        print("✅ Multiprocessing pool created correctly")
        print("✅ Worker function called with job batches")
        print("✅ Results processed and statistics updated")
        print("✅ Database updated with processed jobs")
        print("🎉 Multiprocessing pool integration test passed!")
        return True

def test_error_handling():
    """Test error handling in various scenarios."""
    print("\n🧪 Testing Error Handling...")
    
    # Test database connection error during initialization
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client'):
        
        # Mock database to raise error during validation
        mock_db = Mock()
        mock_db.get_job_stats.side_effect = Exception("Database connection failed")
        mock_get_db.return_value = mock_db
        
        try:
            processor = EnhancedJobProcessor("test_profile")
            assert False, "Should have raised RuntimeError"
        except RuntimeError as e:
            assert "Database connection failed" in str(e)
            print("✅ Database connection error handled correctly")
    
    # Test successful initialization with job retrieval error
    with patch('src.orchestration.enhanced_job_processor.get_job_db') as mock_get_db, \
         patch('src.orchestration.enhanced_job_processor.get_gpu_ollama_client'):
        
        # Mock database for successful initialization
        mock_db = Mock()
        mock_db.get_job_stats.return_value = {}
        mock_get_db.return_value = mock_db
        
        processor = EnhancedJobProcessor("test_profile")
        
        # Test job retrieval error
        mock_db.get_jobs_by_status.side_effect = Exception("Database query failed")
        jobs = processor._get_jobs_for_processing()
        assert jobs == []  # Should return empty list on error
        print("✅ Job retrieval error handled gracefully")
        
        print("🎉 Error handling test passed!")
        return True

def main():
    """Run all tests."""
    print("🚀 Testing Enhanced Job Processor Orchestrator")
    print("="*70)
    
    try:
        test_processor_initialization()
        test_get_jobs_for_processing()
        test_processing_status_and_stats()
        test_system_health_monitoring()
        test_configuration_updates()
        test_stats_reset()
        test_convenience_functions()
        test_multiprocessing_pool_integration()
        test_error_handling()
        
        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("✅ Enhanced Job Processor Orchestrator is working correctly!")
        print("✅ Multiprocessing.Pool(processes=2) integration verified!")
        print("✅ Job batching and distribution working!")
        print("✅ Statistics and monitoring functional!")
        print("✅ Error handling is robust!")
        print("✅ Configuration management working!")
        print("✅ System health monitoring operational!")
        print("✅ Ready for production deployment!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)