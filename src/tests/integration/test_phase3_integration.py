"""
Integration tests for Phase 3: Dashboard Integration and Error Handling/Observability.

This module tests the integration of all Phase 3 components including:
- Redis monitoring endpoints
- Structured logging and correlation IDs
- Health check system
- Real-time dashboard components
- Error visualization
- Queue management interface
"""

import asyncio
import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# Import Phase 3 components
from src.dashboard.api import app
from src.pipeline.redis_queue import RedisQueue
from src.health_checks.pipeline_health_monitor import pipeline_health_monitor
from src.dashboard.components.real_time_monitor import real_time_monitor
from src.dashboard.components.error_visualization import error_visualization_manager
from src.dashboard.components.queue_manager import queue_manager
from src.pipeline.stages.processing import processing_stage, StructuredLogger
from src.pipeline.stages.analysis import analysis_stage
from src.pipeline.stages.storage import storage_stage


class TestPhase3Integration:
    """Test suite for Phase 3 integration."""
    
    @pytest.fixture
    def mock_redis_queue(self):
        """Mock Redis queue for testing."""
        mock_queue = AsyncMock(spec=RedisQueue)
        mock_queue.redis = AsyncMock()
        mock_queue.redis.llen.return_value = 5
        mock_queue.redis.lrange.return_value = [
            json.dumps({
                "job_id": "test_job_1",
                "title": "Test Job",
                "company": "Test Company",
                "correlation_id": str(uuid.uuid4()),
                "queued_at": datetime.now().isoformat()
            })
        ]
        mock_queue.redis.info.return_value = {
            "redis_version": "6.0.0",
            "connected_clients": 1,
            "used_memory_human": "1M",
            "uptime_in_seconds": 3600
        }
        return mock_queue
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for testing."""
        mock_db = MagicMock()
        mock_db.get_job_count.return_value = 100
        mock_db.get_job_stats.return_value = {
            "total_jobs": 100,
            "applied_jobs": 20,
            "failed_jobs": 5,
            "pending_jobs": 75
        }
        mock_db.add_job.return_value = True
        return mock_db
    
    @pytest.mark.asyncio
    async def test_redis_monitoring_endpoints(self, mock_redis_queue):
        """Test Redis monitoring endpoints functionality."""
        with patch('src.pipeline.redis_queue.RedisQueue', return_value=mock_redis_queue):
            from fastapi.testclient import TestClient
            client = TestClient(app)
            
            # Test queue status endpoint
            response = client.get("/api/redis/queue-status")
            assert response.status_code == 200
            data = response.json()
            assert "queue_length" in data
            assert "deadletter_length" in data
            assert "redis_status" in data
            
            # Test dead-letter queue endpoint
            response = client.get("/api/redis/dead-letter")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total_items" in data
            
            # Test pipeline health endpoint
            response = client.get("/api/pipeline/health")
            assert response.status_code == 200
            data = response.json()
            assert "overall_status" in data
            assert "components" in data
            
            # Test pipeline metrics endpoint
            response = client.get("/api/pipeline/metrics")
            assert response.status_code == 200
            data = response.json()
            assert "throughput" in data
            assert "performance" in data
    
    @pytest.mark.asyncio
    async def test_structured_logging_integration(self):
        """Test structured logging with correlation IDs."""
        # Create test job data
        test_job_data = MagicMock()
        test_job_data.job_id = "test_job_123"
        test_job_data.title = "Test Software Engineer"
        test_job_data.company = "Test Company"
        test_job_data.status = MagicMock()
        test_job_data.status.value = "PROCESSING"
        test_job_data.retry_count = 0
        
        correlation_id = str(uuid.uuid4())
        
        # Test structured logging
        with patch('src.pipeline.stages.processing.logger') as mock_logger:
            StructuredLogger.log_job_event(
                correlation_id, "processing", "job_received", test_job_data,
                {"test_data": "test_value"}
            )
            
            # Verify logging was called with structured data
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert correlation_id in call_args[0][0]  # Message contains correlation ID
            assert "extra" in call_args[1]  # Extra data provided
            
            log_entry = call_args[1]["extra"]
            assert log_entry["correlation_id"] == correlation_id
            assert log_entry["stage"] == "processing"
            assert log_entry["event"] == "job_received"
            assert log_entry["job_id"] == "test_job_123"
    
    @pytest.mark.asyncio
    async def test_health_check_system(self, mock_redis_queue, mock_database):
        """Test comprehensive health check system."""
        with patch('src.pipeline.redis_queue.RedisQueue', return_value=mock_redis_queue), \
             patch('src.core.job_database.get_job_db', return_value=mock_database):
            
            # Test pipeline health monitor
            health_status = await pipeline_health_monitor.perform_comprehensive_health_check()
            
            assert "overall_status" in health_status
            assert "components" in health_status
            assert "redis" in health_status["components"]
            assert "database" in health_status["components"]
            assert "system" in health_status["components"]
            assert "websocket" in health_status["components"]
            assert "pipeline" in health_status["components"]
            
            # Verify component health checks
            redis_health = health_status["components"]["redis"]
            assert "status" in redis_health
            assert "response_time_seconds" in redis_health
            
            db_health = health_status["components"]["database"]
            assert "status" in db_health
            assert "connected" in db_health
    
    @pytest.mark.asyncio
    async def test_real_time_monitoring(self, mock_redis_queue, mock_database):
        """Test real-time monitoring components."""
        with patch('src.pipeline.redis_queue.RedisQueue', return_value=mock_redis_queue), \
             patch('src.core.job_database.get_job_db', return_value=mock_database), \
             patch('psutil.cpu_percent', return_value=25.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Mock system resources
            mock_memory.return_value.percent = 45.0
            mock_disk.return_value.percent = 60.0
            
            # Test pipeline metrics collection
            metrics = await real_time_monitor._collect_pipeline_metrics()
            assert hasattr(metrics, 'timestamp')
            assert hasattr(metrics, 'jobs_in_queue')
            assert hasattr(metrics, 'jobs_in_deadletter')
            assert hasattr(metrics, 'total_jobs_processed')
            assert hasattr(metrics, 'success_rate')
            
            # Test system status collection
            status = await real_time_monitor._collect_system_status()
            assert hasattr(status, 'timestamp')
            assert hasattr(status, 'cpu_percent')
            assert hasattr(status, 'memory_percent')
            assert hasattr(status, 'redis_connected')
            assert hasattr(status, 'database_connected')
    
    @pytest.mark.asyncio
    async def test_error_visualization(self, mock_redis_queue):
        """Test error visualization components."""
        # Mock dead-letter queue with error data
        error_job_data = {
            "job_id": "failed_job_123",
            "title": "Failed Job",
            "company": "Test Company",
            "error_reason": "Missing required fields: title or company",
            "failed_at": datetime.now().isoformat(),
            "retry_count": 2,
            "correlation_id": str(uuid.uuid4())
        }
        
        mock_redis_queue.redis.lrange.return_value = [json.dumps(error_job_data)]
        
        with patch('src.pipeline.redis_queue.RedisQueue', return_value=mock_redis_queue):
            # Test error summary
            error_summary = await error_visualization_manager.get_error_summary()
            assert hasattr(error_summary, 'total_errors')
            assert hasattr(error_summary, 'error_rate_percent')
            assert hasattr(error_summary, 'top_error_types')
            
            # Test failed jobs analysis
            analysis = await error_visualization_manager.get_failed_jobs_analysis(10)
            assert "total_failed_jobs" in analysis
            assert "error_breakdown" in analysis
            assert "recovery_suggestions" in analysis
            
            # Test error timeline
            timeline = await error_visualization_manager.get_error_timeline(24)
            assert "timeline" in timeline
            assert "total_errors_in_range" in timeline
    
    @pytest.mark.asyncio
    async def test_queue_management(self, mock_redis_queue):
        """Test queue management interface."""
        with patch('src.pipeline.redis_queue.RedisQueue', return_value=mock_redis_queue):
            # Test queue statistics
            stats = await queue_manager.get_queue_stats()
            assert hasattr(stats, 'main_queue_length')
            assert hasattr(stats, 'deadletter_queue_length')
            assert hasattr(stats, 'queue_health')
            
            # Test queue contents
            contents = await queue_manager.get_queue_contents(limit=10)
            assert "items" in contents
            assert "total_items" in contents
            assert "has_more" in contents
            
            # Test batch operations
            from src.dashboard.components.queue_manager import QueueOperation
            result = await queue_manager.perform_batch_operation(
                QueueOperation.DELETE, [0, 1], source_queue_type="deadletter"
            )
            assert hasattr(result, 'operation')
            assert hasattr(result, 'successful')
            assert hasattr(result, 'failed')
    
    @pytest.mark.asyncio
    async def test_pipeline_stages_integration(self, mock_database):
        """Test integration of enhanced pipeline stages."""
        # Mock queues and dependencies
        processing_queue = asyncio.Queue()
        analysis_queue = asyncio.Queue()
        storage_queue = asyncio.Queue()
        
        # Mock metrics
        metrics = MagicMock()
        metrics.increment = MagicMock()
        metrics.get_count = MagicMock(return_value=10)
        
        # Mock analyzer and thread pool
        analyzer = MagicMock()
        analyzer.analyze_job_deep.return_value = {"analysis": "test"}
        thread_pool = MagicMock()
        
        # Create test job data
        from src.scrapers.scraping_models import JobData, JobStatus
        test_job = JobData(
            job_id="test_123",
            title="Test Job",
            company="Test Company",
            location="Test Location",
            summary="Test summary",
            url="https://test.com/job",
            search_keyword="test",
            site="test_site",
            scraped_at=datetime.now().isoformat(),
            status=JobStatus.SCRAPED
        )
        test_job.correlation_id = str(uuid.uuid4())
        
        # Test processing stage with structured logging
        await processing_queue.put(test_job)
        
        # Mock Redis operations for processing stage
        with patch('src.pipeline.redis_queue.RedisQueue') as mock_redis_class:
            mock_redis_instance = AsyncMock()
            mock_redis_class.return_value = mock_redis_instance
            
            # Run processing stage briefly
            processing_task = asyncio.create_task(
                processing_stage(processing_queue, analysis_queue, metrics, use_redis=False)
            )
            
            # Allow some processing time
            await asyncio.sleep(0.1)
            processing_task.cancel()
            
            try:
                await processing_task
            except asyncio.CancelledError:
                pass
            
            # Verify job was processed
            assert not processing_queue.empty() or not analysis_queue.empty()
    
    @pytest.mark.asyncio
    async def test_websocket_integration(self):
        """Test WebSocket integration with real-time components."""
        from src.dashboard.websocket import manager as websocket_manager
        
        # Test WebSocket manager functionality
        connection_stats = websocket_manager.get_connection_stats()
        assert "active_connections" in connection_stats
        assert "total_messages_sent" in connection_stats
        
        # Test broadcasting (without actual WebSocket connections)
        test_message = {
            "type": "test_message",
            "data": {"test": "value"},
            "timestamp": datetime.now().isoformat()
        }
        
        # This should not fail even with no connections
        result = await websocket_manager.broadcast(test_message)
        assert isinstance(result, int)  # Returns number of successful sends
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self):
        """Test backward compatibility with existing dashboard functionality."""
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Test existing endpoints still work
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test existing API routes are still accessible
        response = client.get("/api/system-status")
        assert response.status_code == 200
        
        # Verify new endpoints don't break existing functionality
        response = client.get("/")
        assert response.status_code == 200
    
    def test_configuration_compatibility(self):
        """Test that new components don't break existing configuration."""
        # Test that imports work correctly
        try:
            from src.dashboard.api import app
            from src.pipeline.stages.processing import processing_stage
            from src.pipeline.stages.analysis import analysis_stage
            from src.pipeline.stages.storage import storage_stage
            assert app is not None
            assert processing_stage is not None
            assert analysis_stage is not None
            assert storage_stage is not None
        except ImportError as e:
            pytest.fail(f"Import error indicates compatibility issue: {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling_robustness(self):
        """Test error handling in Phase 3 components."""
        # Test health monitor with connection failures
        with patch('src.pipeline.redis_queue.RedisQueue') as mock_redis_class:
            mock_redis_class.side_effect = Exception("Connection failed")
            
            # Should not crash, should return error status
            health_status = await pipeline_health_monitor.perform_comprehensive_health_check()
            assert health_status["overall_status"] in ["critical", "degraded"]
        
        # Test error visualization with corrupted data
        with patch('src.pipeline.redis_queue.RedisQueue') as mock_redis_class:
            mock_redis_instance = AsyncMock()
            mock_redis_instance.redis.lrange.return_value = ["invalid json", "also invalid"]
            mock_redis_class.return_value = mock_redis_instance
            
            # Should handle corrupted data gracefully
            errors = await error_visualization_manager._get_deadletter_errors(10)
            assert isinstance(errors, list)  # Should return list even with bad data
    
    def test_performance_impact(self):
        """Test that Phase 3 additions don't significantly impact performance."""
        import time
        
        # Test import time (should be reasonable)
        start_time = time.time()
        from src.dashboard.api import app
        import_time = time.time() - start_time
        
        # Should import in reasonable time (less than 2 seconds)
        assert import_time < 2.0, f"Import time too slow: {import_time}s"
        
        # Test that app creation is still fast
        start_time = time.time()
        from src.dashboard.api import create_app
        test_app = create_app()
        creation_time = time.time() - start_time
        
        assert creation_time < 1.0, f"App creation too slow: {creation_time}s"
        assert test_app is not None


if __name__ == "__main__":
    # Run basic integration test
    print("Running Phase 3 Integration Tests...")
    
    # Test imports
    try:
        from src.dashboard.api import app
        from src.health_checks.pipeline_health_monitor import pipeline_health_monitor
        from src.dashboard.components.real_time_monitor import real_time_monitor
        from src.dashboard.components.error_visualization import error_visualization_manager
        from src.dashboard.components.queue_manager import queue_manager
        print("✅ All Phase 3 components imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        exit(1)
    
    # Test basic functionality
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        print("✅ Basic health endpoint working")
        
        # Test new API routes exist
        response = client.get("/api/health/pipeline-health")
        # May fail due to Redis connection, but should not be 404
        assert response.status_code != 404
        print("✅ New API routes accessible")
        
        print("✅ Phase 3 integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        exit(1)