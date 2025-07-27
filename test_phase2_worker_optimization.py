#!/usr/bin/env python3
"""
Test script for Phase 2 Worker Optimization components.

This script tests the new OptimizedConnectionPool and OptimizedJobBatcher
components that were implemented as part of Phase 2 of the scraper pipeline overhaul.

Tests:
- OptimizedConnectionPool functionality
- OptimizedJobBatcher functionality
- Integration with DescriptionFetcherOrchestrator
- Performance metrics and monitoring
- Error handling and recovery
"""

import asyncio
import time
import logging
import sys
import os
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestration.optimized_connection_pool import (
    OptimizedConnectionPool, ConnectionConfig, RateLimitConfig
)
from src.orchestration.optimized_job_batcher import (
    OptimizedJobBatcher, BatchConfig
)
from src.orchestration.description_fetcher_orchestrator import (
    DescriptionFetcherOrchestrator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase2Tester:
    """Test suite for Phase 2 Worker Optimization components."""
    
    def __init__(self):
        self.test_results = {}
        
    async def test_optimized_connection_pool(self) -> Dict[str, Any]:
        """Test OptimizedConnectionPool functionality."""
        logger.info("🧪 Testing OptimizedConnectionPool...")
        
        try:
            # Initialize connection pool
            config = ConnectionConfig(
                pool_size=5,
                max_connections=20,
                retry_attempts=2
            )
            rate_config = RateLimitConfig(
                requests_per_second=10,
                burst_limit=5
            )
            
            pool = OptimizedConnectionPool(config, rate_config)
            
            # Start pool
            await pool.start()
            
            # Test basic functionality
            test_urls = [
                "https://httpbin.org/get",
                "https://httpbin.org/status/200",
                "https://httpbin.org/delay/1"
            ]
            
            start_time = time.time()
            successful_requests = 0
            
            for url in test_urls * 3:  # Test rate limiting
                try:
                    response = await pool.make_request(url)
                    if response and response.status == 200:
                        successful_requests += 1
                except Exception as e:
                    logger.warning(f"Request failed: {e}")
                    
            test_duration = time.time() - start_time
            
            # Get metrics
            metrics = pool.get_metrics()
            health_status = pool.get_health_status()
            
            # Stop pool
            await pool.stop()
            
            # Evaluate results
            success_rate = successful_requests / (len(test_urls) * 3)
            is_successful = success_rate > 0.8 and health_status["status"] == "healthy"
            
            result = {
                "success": is_successful,
                "success_rate": success_rate,
                "test_duration": test_duration,
                "metrics": metrics,
                "health_status": health_status,
                "successful_requests": successful_requests
            }
            
            logger.info(f"✅ OptimizedConnectionPool test completed: {success_rate:.1%} success rate")
            return result
            
        except Exception as e:
            logger.error(f"❌ OptimizedConnectionPool test failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def test_optimized_job_batcher(self) -> Dict[str, Any]:
        """Test OptimizedJobBatcher functionality."""
        logger.info("🧪 Testing OptimizedJobBatcher...")
        
        try:
            # Initialize job batcher
            config = BatchConfig(
                initial_batch_size=10,
                min_batch_size=3,
                max_batch_size=20,
                memory_threshold_mb=512.0,
                enable_auto_optimization=True
            )
            
            batcher = OptimizedJobBatcher(config)
            
            # Start batcher
            await batcher.start()
            
            # Create test jobs
            test_jobs = [
                {"id": f"job_{i}", "title": f"Test Job {i}", "url": f"https://example.com/job_{i}"}
                for i in range(25)
            ]
            
            # Test batching
            batches = []
            async for batch in batcher.batch_generator(test_jobs):
                batches.append(batch)
                
            # Get metrics
            metrics = batcher.get_metrics()
            health_status = batcher.get_health_status()
            
            # Stop batcher
            await batcher.stop()
            
            # Evaluate results
            total_jobs_batched = sum(len(batch) for batch in batches)
            avg_batch_size = total_jobs_batched / len(batches) if batches else 0
            is_successful = (
                total_jobs_batched == len(test_jobs) and 
                len(batches) > 0 and 
                health_status["status"] in ["healthy", "degraded"]
            )
            
            result = {
                "success": is_successful,
                "total_jobs": len(test_jobs),
                "total_jobs_batched": total_jobs_batched,
                "num_batches": len(batches),
                "avg_batch_size": avg_batch_size,
                "metrics": metrics,
                "health_status": health_status,
                "batches": [len(batch) for batch in batches]
            }
            
            logger.info(f"✅ OptimizedJobBatcher test completed: {len(batches)} batches created")
            return result
            
        except Exception as e:
            logger.error(f"❌ OptimizedJobBatcher test failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def test_integration(self) -> Dict[str, Any]:
        """Test integration of Phase 2 components with DescriptionFetcherOrchestrator."""
        logger.info("🧪 Testing Phase 2 Integration...")
        
        try:
            # Initialize orchestrator with Phase 2 components
            orchestrator = DescriptionFetcherOrchestrator(
                profile_name="test_profile",
                num_workers=3,
                batch_size=5,
                rate_limit=20
            )
            
            # Start orchestrator
            await orchestrator.start()
            
            # Get initial stats
            initial_stats = await orchestrator.get_orchestrator_stats()
            
            # Wait a bit for components to initialize
            await asyncio.sleep(2)
            
            # Get updated stats
            updated_stats = await orchestrator.get_orchestrator_stats()
            
            # Stop orchestrator
            await orchestrator.stop()
            
            # Evaluate results
            has_connection_pool = "connection_pool_metrics" in updated_stats
            has_job_batcher = "job_batcher_metrics" in updated_stats
            has_health_status = "connection_pool_health" in updated_stats
            
            is_successful = has_connection_pool and has_job_batcher and has_health_status
            
            result = {
                "success": is_successful,
                "has_connection_pool": has_connection_pool,
                "has_job_batcher": has_job_batcher,
                "has_health_status": has_health_status,
                "initial_stats": initial_stats,
                "updated_stats": updated_stats
            }
            
            logger.info(f"✅ Phase 2 Integration test completed: {is_successful}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Phase 2 Integration test failed: {e}")
            return {"success": False, "error": str(e)}
            
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 2 tests."""
        logger.info("🚀 Starting Phase 2 Worker Optimization Tests...")
        
        start_time = time.time()
        
        # Run individual tests
        self.test_results["connection_pool"] = await self.test_optimized_connection_pool()
        self.test_results["job_batcher"] = await self.test_optimized_job_batcher()
        self.test_results["integration"] = await self.test_integration()
        
        # Calculate overall results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        
        overall_success = passed_tests == total_tests
        test_duration = time.time() - start_time
        
        # Compile final results
        final_results = {
            "overall_success": overall_success,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "test_duration": test_duration,
            "test_results": self.test_results
        }
        
        # Display results
        self._display_results(final_results)
        
        return final_results
        
    def _display_results(self, results: Dict[str, Any]):
        """Display test results."""
        print("\n" + "="*60)
        print("📊 PHASE 2 WORKER OPTIMIZATION TEST RESULTS")
        print("="*60)
        
        print(f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")
        print(f"Tests Passed: {results['passed_tests']}/{results['total_tests']}")
        print(f"Test Duration: {results['test_duration']:.2f}s")
        
        print("\n📋 Individual Test Results:")
        for test_name, test_result in results['test_results'].items():
            status = "✅ PASSED" if test_result.get("success", False) else "❌ FAILED"
            print(f"  {test_name}: {status}")
            
            if not test_result.get("success", False) and "error" in test_result:
                print(f"    Error: {test_result['error']}")
                
        print("="*60)


async def main():
    """Main test function."""
    tester = Phase2Tester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)


if __name__ == "__main__":
    asyncio.run(main()) 