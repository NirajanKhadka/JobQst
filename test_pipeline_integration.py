#!/usr/bin/env python3
"""
Test pipeline integration without Redis dependency.
"""

import asyncio
import sys
import os
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_pipeline_stages():
    """Test pipeline stages integration."""
    print("Testing Pipeline Stages Integration...")
    print("=" * 50)
    
    try:
        # Test imports
        from src.pipeline.stages.processing import processing_stage, StructuredLogger
        from src.pipeline.stages.analysis import analysis_stage
        from src.pipeline.stages.storage import storage_stage
        from src.core.job_data import JobData
        print("✅ Pipeline stage imports successful")
        
        # Test structured logging
        correlation_id = "test-correlation-123"
        test_job = MagicMock()
        test_job.job_id = "test_job_456"
        test_job.title = "Test Software Engineer"
        test_job.company = "Test Company"
        
        # This should work without Redis
        print("✅ Structured logging components available")
        
        # Test job data creation
        job_data = JobData(
            title="Test Job",
            company="Test Company",
            location="Test Location",
            url="https://test.com/job",
            site="test_site",
            search_keyword="test"
        )
        print(f"✅ JobData created: {job_data.title}")
        
        # Test job data conversion
        job_dict = job_data.to_dict()
        print(f"✅ JobData to_dict works: {len(job_dict)} fields")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline integration test failed: {e}")
        return False

async def test_dashboard_components():
    """Test dashboard components without Redis."""
    print("\nTesting Dashboard Components...")
    print("=" * 50)
    
    try:
        # Test dashboard API imports
        from src.dashboard.api import app
        print("✅ Dashboard API import successful")
        
        # Test health monitor (should handle Redis gracefully)
        from src.health_checks.pipeline_health_monitor import pipeline_health_monitor
        print("✅ Health monitor import successful")
        
        # Test real-time monitor
        from src.dashboard.components.real_time_monitor import real_time_monitor
        print("✅ Real-time monitor import successful")
        
        # Test error visualization
        from src.dashboard.components.error_visualization import error_visualization_manager
        print("✅ Error visualization import successful")
        
        # Test queue manager
        from src.dashboard.components.queue_manager import queue_manager
        print("✅ Queue manager import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard components test failed: {e}")
        return False

async def test_websocket_integration():
    """Test WebSocket integration."""
    print("\nTesting WebSocket Integration...")
    print("=" * 50)
    
    try:
        from src.dashboard.websocket import manager as websocket_manager
        print("✅ WebSocket manager import successful")
        
        # Test connection stats (should work without active connections)
        stats = websocket_manager.get_connection_stats()
        print(f"✅ WebSocket stats available: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket integration test failed: {e}")
        return False

async def test_job_status_compatibility():
    """Test JobStatus enum compatibility."""
    print("\nTesting JobStatus Compatibility...")
    print("=" * 50)
    
    try:
        from src.scrapers.scraping_models import JobStatus as ScrapingJobStatus
        from src.orchestration.job_queue_manager import JobStatus as QueueJobStatus
        
        print(f"✅ Scraping JobStatus: {list(ScrapingJobStatus)}")
        print(f"✅ Queue JobStatus: {list(QueueJobStatus)}")
        
        # Check if SCRAPED exists in either
        scraped_available = hasattr(ScrapingJobStatus, 'SCRAPED') or hasattr(QueueJobStatus, 'SCRAPED')
        if scraped_available:
            print("✅ SCRAPED status available")
        else:
            print("❌ SCRAPED status not available in either enum")
            
        return scraped_available
        
    except Exception as e:
        print(f"❌ JobStatus compatibility test failed: {e}")
        return False

async def main():
    """Run all integration tests."""
    print("Phase 3 Pipeline Integration Validation")
    print("=" * 60)
    
    results = []
    
    # Test pipeline stages
    results.append(await test_pipeline_stages())
    
    # Test dashboard components
    results.append(await test_dashboard_components())
    
    # Test WebSocket integration
    results.append(await test_websocket_integration())
    
    # Test JobStatus compatibility
    results.append(await test_job_status_compatibility())
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All integration tests passed!")
        return True
    else:
        print(f"❌ {total - passed} integration tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)