#!/usr/bin/env python3
"""
End-to-end pipeline test without Redis dependency.
"""

import sys
import os
import asyncio
import uuid
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_job_data_flow():
    """Test complete job data flow through pipeline stages."""
    print("Testing End-to-End Job Data Flow...")
    print("=" * 60)
    
    try:
        # Import required components
        from src.core.job_data import JobData
        from src.orchestration.job_queue_manager import JobStatus as QueueJobStatus
        from src.scrapers.scraping_models import JobStatus as ScrapingJobStatus
        
        # Create test job data
        test_job = JobData(
            title="Senior Python Developer",
            company="Tech Innovations Inc",
            location="Toronto, ON",
            url="https://example.com/job/12345",
            summary="Exciting opportunity for a senior Python developer...",
            salary="$80,000 - $120,000",
            job_type="Full-time",
            site="test_site",
            search_keyword="python developer"
        )
        
        print(f"✅ Created test job: {test_job.title} at {test_job.company}")
        
        # Test job data conversion
        job_dict = test_job.to_dict()
        print(f"✅ Job data serialization: {len(job_dict)} fields")
        
        # Test job hash generation for duplicate detection
        job_hash = test_job.get_hash()
        print(f"✅ Job hash generated: {job_hash[:8]}...")
        
        # Simulate pipeline stages
        correlation_id = str(uuid.uuid4())
        print(f"✅ Correlation ID generated: {correlation_id}")
        
        # Test structured logging
        from src.pipeline.stages.processing import StructuredLogger
        
        with patch('src.pipeline.stages.processing.logger') as mock_logger:
            StructuredLogger.log_job_event(
                correlation_id, "processing", "job_received", test_job,
                {"stage": "end_to_end_test"}
            )
            print("✅ Structured logging works in pipeline")
        
        return True
        
    except Exception as e:
        print(f"❌ Job data flow test failed: {e}")
        return False

async def test_pipeline_stages_simulation():
    """Simulate pipeline stages without Redis."""
    print("\nTesting Pipeline Stages Simulation...")
    print("=" * 60)
    
    try:
        # Create mock queues
        processing_queue = asyncio.Queue()
        analysis_queue = asyncio.Queue()
        storage_queue = asyncio.Queue()
        
        # Create test job
        from src.core.job_data import JobData
        test_job = JobData(
            title="Data Scientist",
            company="AI Corp",
            location="Vancouver, BC",
            url="https://example.com/job/67890",
            site="test_site",
            search_keyword="data science"
        )
        
        # Add correlation ID
        test_job.correlation_id = str(uuid.uuid4())
        
        # Put job in processing queue
        await processing_queue.put(test_job)
        print("✅ Job added to processing queue")
        
        # Simulate processing stage
        job_from_queue = await processing_queue.get()
        assert job_from_queue.title == test_job.title
        print("✅ Job retrieved from processing queue")
        
        # Simulate moving to analysis queue
        await analysis_queue.put(job_from_queue)
        print("✅ Job moved to analysis queue")
        
        # Simulate analysis stage
        job_for_analysis = await analysis_queue.get()
        assert job_for_analysis.title == test_job.title
        print("✅ Job retrieved from analysis queue")
        
        # Simulate moving to storage queue
        await storage_queue.put(job_for_analysis)
        print("✅ Job moved to storage queue")
        
        # Simulate storage stage
        job_for_storage = await storage_queue.get()
        assert job_for_storage.title == test_job.title
        print("✅ Job retrieved from storage queue")
        
        print("✅ Complete pipeline simulation successful")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline stages simulation failed: {e}")
        return False

async def test_dashboard_monitoring_simulation():
    """Test dashboard monitoring during pipeline operation."""
    print("\nTesting Dashboard Monitoring Simulation...")
    print("=" * 60)
    
    try:
        # Test health monitoring
        from src.health_checks.pipeline_health_monitor import pipeline_health_monitor
        
        health_status = await pipeline_health_monitor.perform_comprehensive_health_check()
        print(f"✅ Health check: {health_status['overall_status']}")
        
        # Test real-time monitoring
        from src.dashboard.components.real_time_monitor import real_time_monitor
        
        with patch('psutil.cpu_percent', return_value=30.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value.percent = 50.0
            mock_disk.return_value.percent = 65.0
            
            status = await real_time_monitor._collect_system_status()
            print(f"✅ System monitoring: CPU {status.cpu_percent}%, Memory {status.memory_percent}%")
        
        # Test error visualization
        from src.dashboard.components.error_visualization import error_visualization_manager
        
        error_summary = await error_visualization_manager.get_error_summary()
        print(f"✅ Error monitoring: {error_summary.total_errors} total errors tracked")
        
        # Test queue management
        from src.dashboard.components.queue_manager import queue_manager
        
        stats = await queue_manager.get_queue_stats()
        print(f"✅ Queue monitoring: Main queue length {stats.main_queue_length}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard monitoring simulation failed: {e}")
        return False

async def test_error_handling_simulation():
    """Test error handling throughout the pipeline."""
    print("\nTesting Error Handling Simulation...")
    print("=" * 60)
    
    try:
        # Simulate job processing error
        correlation_id = str(uuid.uuid4())
        
        # Test structured error logging
        from src.pipeline.stages.processing import StructuredLogger
        
        with patch('src.pipeline.stages.processing.logger') as mock_logger:
            StructuredLogger.log_job_event(
                correlation_id, "processing", "job_failed", None,
                {
                    "error": "Test error simulation",
                    "retry_count": 1,
                    "max_retries": 3
                }
            )
            print("✅ Error logging with correlation ID works")
        
        # Test health monitoring with errors
        from src.health_checks.pipeline_health_monitor import pipeline_health_monitor
        
        # This should handle Redis connection errors gracefully
        health_status = await pipeline_health_monitor.perform_comprehensive_health_check()
        
        # Should still return a status even with Redis errors
        assert "overall_status" in health_status
        print("✅ Health monitoring handles Redis errors gracefully")
        
        # Test WebSocket error handling
        from src.dashboard.websocket import manager as websocket_manager
        
        # Test broadcasting with no connections
        test_error_message = {
            "type": "error_alert",
            "data": {
                "correlation_id": correlation_id,
                "error": "Test error simulation",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        result = await websocket_manager.broadcast(test_error_message)
        print("✅ WebSocket error broadcasting works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling simulation failed: {e}")
        return False

async def test_backward_compatibility():
    """Test backward compatibility with existing systems."""
    print("\nTesting Backward Compatibility...")
    print("=" * 60)
    
    try:
        # Test that existing API endpoints still work
        from fastapi.testclient import TestClient
        from src.dashboard.api import app
        
        client = TestClient(app)
        
        # Test basic endpoints
        response = client.get("/health")
        assert response.status_code == 200
        print("✅ Basic health endpoint works")
        
        response = client.get("/api/system-status")
        assert response.status_code == 200
        print("✅ System status endpoint works")
        
        response = client.get("/")
        assert response.status_code == 200
        print("✅ Root endpoint works")
        
        # Test that new endpoints are available
        response = client.get("/api/health/pipeline-health")
        assert response.status_code == 200
        print("✅ New pipeline health endpoint works")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

async def main():
    """Run complete end-to-end pipeline test."""
    print("Phase 3 End-to-End Pipeline Validation")
    print("=" * 80)
    
    tests = [
        ("Job Data Flow", test_job_data_flow),
        ("Pipeline Stages Simulation", test_pipeline_stages_simulation),
        ("Dashboard Monitoring", test_dashboard_monitoring_simulation),
        ("Error Handling", test_error_handling_simulation),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 80)
    print("END-TO-END PIPELINE TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASSED" if results[i] else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ End-to-end pipeline validation PASSED!")
        return True
    else:
        print(f"❌ End-to-end pipeline validation FAILED ({total - passed} failures)")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)