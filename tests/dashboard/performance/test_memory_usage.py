"""
Memory usage and optimization tests for dashboard services.

Tests memory efficiency, garbage collection, and resource management including:
- Memory leak detection
- Cache memory optimization
- Garbage collection effectiveness
- Resource cleanup verification
- Memory usage profiling
"""

import pytest
import gc
import psutil
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.services.data_service import get_data_service
from src.dashboard.services.system_service import get_system_service
from src.dashboard.services.config_service import get_config_service
from src.dashboard.services.orchestration_service import get_orchestration_service
from src.dashboard.services.health_monitor import get_health_monitor


class TestMemoryUsage:
    """Test memory usage patterns and optimization."""
    
    @pytest.fixture
    def memory_baseline(self):
        """Establish memory baseline for testing."""
        # Force garbage collection before establishing baseline
        for _ in range(3):
            gc.collect()
        
        initial_memory = psutil.Process().memory_info().rss
        yield initial_memory
        
        # Cleanup after test
        for _ in range(3):
            gc.collect()
    
    @pytest.fixture
    def large_test_data(self):
        """Generate large test data for memory testing."""
        return {
            "jobs": [
                {
                    "id": i,
                    "title": f"Software Engineer Position {i}",
                    "company": f"Technology Company {i % 50}",
                    "description": "This is a comprehensive job description that contains multiple paragraphs of text describing the role, responsibilities, requirements, and benefits. " * 10,  # ~2KB per job
                    "requirements": [f"Requirement {j}" for j in range(20)],
                    "benefits": [f"Benefit {j}" for j in range(15)],
                    "location": f"City {i % 25}, Province {i % 10}",
                    "salary_range": f"{50000 + (i * 1000)}-{70000 + (i * 1000)}",
                    "application_status": ["pending", "applied", "interview", "rejected"][i % 4],
                    "date_posted": f"2025-08-{(i % 28) + 1:02d}",
                    "application_date": f"2025-08-{(i % 28) + 1:02d}" if i % 3 == 0 else None
                }
                for i in range(1000)  # 1000 jobs * ~2KB = ~2MB
            ],
            "profiles": {
                f"User{i}": {
                    "name": f"User {i} Full Name",
                    "email": f"user{i}@example.com",
                    "database_path": f"profiles/User{i}/jobs.db",
                    "resume_path": f"profiles/User{i}/resume.pdf",
                    "cover_letter_template": f"profiles/User{i}/cover_letter.txt",
                    "preferences": {
                        "locations": [f"City {j}" for j in range(5)],
                        "companies": [f"Company {j}" for j in range(10)],
                        "salary_min": 50000 + (i * 1000),
                        "job_types": ["full-time", "contract", "remote"]
                    },
                    "search_history": [
                        {
                            "query": f"Search query {j}",
                            "timestamp": f"2025-08-{j % 28 + 1:02d}",
                            "results_count": j * 10
                        }
                        for j in range(20)
                    ]
                }
                for i in range(100)  # 100 profiles
            },
            "metrics": {
                "cpu_history": [float(i % 100) for i in range(1000)],
                "memory_history": [float((i * 2) % 100) for i in range(1000)],
                "disk_history": [float((i * 3) % 100) for i in range(1000)],
                "network_history": [
                    {
                        "timestamp": f"2025-08-01T{i % 24:02d}:00:00",
                        "bytes_sent": i * 1000,
                        "bytes_received": i * 2000,
                        "connections": i % 50
                    }
                    for i in range(500)
                ]
            }
        }
    
    @pytest.mark.performance
    def test_data_service_memory_efficiency(self, memory_baseline, large_test_data):
        """Test data service memory efficiency with large datasets."""
        data_service = get_data_service()
        
        # Setup mock database with large dataset
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = large_test_data["jobs"]
        mock_db.get_job_count.return_value = len(large_test_data["jobs"])
        
        profiles = {"TestUser": {"name": "Test User"}}
        
        # Measure memory usage during operations
        memory_snapshots = []
        
        with patch.object(data_service._config_service, 'get_profiles', return_value=profiles), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            # Initial memory
            gc.collect()
            memory_snapshots.append(("initial", psutil.Process().memory_info().rss))
            
            # Load job data (should cache large dataset)
            jobs = data_service.get_job_data("TestUser")
            gc.collect()
            memory_snapshots.append(("after_job_load", psutil.Process().memory_info().rss))
            
            # Generate statistics (additional processing)
            stats = data_service.get_job_statistics("TestUser")
            gc.collect()
            memory_snapshots.append(("after_statistics", psutil.Process().memory_info().rss))
            
            # Convert to DataFrame (memory-intensive operation)
            df = data_service.get_job_data_as_dataframe("TestUser")
            gc.collect()
            memory_snapshots.append(("after_dataframe", psutil.Process().memory_info().rss))
            
            # Clear cache (should free memory)
            data_service.clear_cache()
            gc.collect()
            memory_snapshots.append(("after_cache_clear", psutil.Process().memory_info().rss))
        
        # Analyze memory usage
        memory_deltas = []
        for i in range(1, len(memory_snapshots)):
            prev_memory = memory_snapshots[i-1][1]
            curr_memory = memory_snapshots[i][1]
            delta_mb = (curr_memory - prev_memory) / (1024 * 1024)
            memory_deltas.append((memory_snapshots[i][0], delta_mb))
        
        # Assertions
        assert len(jobs) == 1000
        assert stats["total_jobs"] == 1000
        assert len(df) == 1000
        
        # Memory usage should be reasonable
        job_load_delta = next(delta for name, delta in memory_deltas if name == "after_job_load")
        assert job_load_delta < 50, f"Job loading used too much memory: {job_load_delta:.2f}MB"
        
        # Cache clearing should free significant memory
        cache_clear_delta = next(delta for name, delta in memory_deltas if name == "after_cache_clear")
        assert cache_clear_delta < -5, f"Cache clearing didn't free enough memory: {cache_clear_delta:.2f}MB"
        
        # Final memory should be close to initial
        final_memory = memory_snapshots[-1][1]
        total_increase = (final_memory - memory_baseline) / (1024 * 1024)
        assert total_increase < 10, f"Memory leak detected: {total_increase:.2f}MB increase"
    
    @pytest.mark.performance
    def test_system_service_memory_patterns(self, memory_baseline, large_test_data):
        """Test system service memory usage patterns."""
        system_service = get_system_service()
        
        # Simulate multiple metrics collection cycles
        memory_progression = []
        
        for cycle in range(10):
            gc.collect()
            memory_before = psutil.Process().memory_info().rss
            
            # Collect metrics with large mock data
            with patch('psutil.cpu_percent', return_value=30.0), \
                 patch('psutil.virtual_memory', return_value=Mock(percent=45.0)), \
                 patch('psutil.disk_usage', return_value=Mock(percent=60.0)), \
                 patch('psutil.net_io_counters', return_value=Mock(bytes_sent=1000000, bytes_recv=2000000)), \
                 patch('psutil.process_iter', return_value=[
                     Mock(info={'pid': i, 'name': f'process_{i}', 'cmdline': [f'cmd_{i}']})
                     for i in range(50)  # Many processes
                 ]):
                
                # Multiple calls to trigger caching
                for _ in range(5):
                    metrics = system_service.get_system_metrics()
                
                gc.collect()
                memory_after = psutil.Process().memory_info().rss
                
                memory_delta = (memory_after - memory_before) / (1024 * 1024)
                memory_progression.append(memory_delta)
                
                # Clear cache periodically
                if cycle % 3 == 2:
                    system_service.clear_cache()
        
        # Memory usage should stabilize (not grow indefinitely)
        early_average = sum(memory_progression[:3]) / 3
        late_average = sum(memory_progression[-3:]) / 3
        
        # Later cycles shouldn't use significantly more memory
        assert late_average < early_average + 5, "Memory usage growing over time"
        
        # Individual cycle memory usage should be reasonable
        max_cycle_usage = max(memory_progression)
        assert max_cycle_usage < 20, f"Single cycle used too much memory: {max_cycle_usage:.2f}MB"
    
    @pytest.mark.performance
    def test_cache_memory_efficiency(self, memory_baseline, large_test_data):
        """Test cache memory efficiency across all services."""
        services = [
            get_data_service(),
            get_system_service(),
            get_orchestration_service(),
            get_config_service()
        ]
        
        # Fill caches with large data
        cache_sizes = []
        
        for service in services:
            gc.collect()
            memory_before = psutil.Process().memory_info().rss
            
            # Add substantial data to cache
            for i in range(50):
                cache_key = f"large_data_{i}"
                
                if hasattr(service, '_cache'):
                    service._cache[cache_key] = {
                        "jobs": large_test_data["jobs"][:20],  # 20 jobs per cache entry
                        "metadata": large_test_data["metrics"],
                        "timestamp": datetime.now().isoformat(),
                        "additional_data": ["item"] * 100
                    }
                    service._cache_timestamps[cache_key] = datetime.now()
            
            gc.collect()
            memory_after = psutil.Process().memory_info().rss
            
            cache_size = (memory_after - memory_before) / (1024 * 1024)
            cache_sizes.append(cache_size)
        
        total_cache_memory = sum(cache_sizes)
        
        # Clear all caches
        gc.collect()
        memory_before_clear = psutil.Process().memory_info().rss
        
        for service in services:
            if hasattr(service, 'clear_cache'):
                service.clear_cache()
        
        gc.collect()
        memory_after_clear = psutil.Process().memory_info().rss
        
        memory_freed = (memory_before_clear - memory_after_clear) / (1024 * 1024)
        
        # Assertions
        assert total_cache_memory > 10, "Caches should use significant memory when filled"
        assert memory_freed > total_cache_memory * 0.7, "Cache clearing should free most memory"
        
        # Final memory should be reasonable
        final_increase = (memory_after_clear - memory_baseline) / (1024 * 1024)
        assert final_increase < 15, f"Too much memory retained after clearing: {final_increase:.2f}MB"
    
    @pytest.mark.performance
    def test_memory_leak_detection_extended(self, memory_baseline):
        """Extended memory leak detection across multiple service operations."""
        data_service = get_data_service()
        system_service = get_system_service()
        health_monitor = get_health_monitor()
        
        # Track memory over many iterations
        memory_samples = []
        
        for iteration in range(50):
            gc.collect()
            memory_before = psutil.Process().memory_info().rss
            
            # Perform various operations that could leak memory
            mock_db = Mock()
            mock_db.get_all_jobs.return_value = [
                {
                    "id": i,
                    "title": f"Job {i}",
                    "description": "Long description " * 20,
                    "data": list(range(100))  # Some additional data
                }
                for i in range(25)
            ]
            mock_db.get_job_count.return_value = 25
            
            with patch.object(data_service._config_service, 'get_profiles',
                             return_value={"User1": {"name": "Test"}}), \
                 patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db), \
                 patch('psutil.cpu_percent', return_value=30.0 + iteration), \
                 patch('psutil.virtual_memory', return_value=Mock(percent=40.0)), \
                 patch('psutil.process_iter', return_value=[]):
                
                # Data service operations
                data_service.get_job_data("User1")
                data_service.get_job_statistics("User1")
                data_service.get_health_status()
                
                # System service operations
                system_service.get_system_metrics()
                system_service.get_service_health()
                
                # Health monitor operations (async mocked as sync for simplicity)
                health_monitor._recovery_status = {"test": f"iteration_{iteration}"}
                health_monitor._history.append({"test": f"data_{iteration}"})
                
                # Cleanup operations
                if iteration % 5 == 4:  # Clear caches every 5 iterations
                    data_service.clear_cache()
                    system_service.clear_cache()
                
                # Limit history size
                if len(health_monitor._history) > 20:
                    health_monitor._history = health_monitor._history[-10:]
            
            gc.collect()
            memory_after = psutil.Process().memory_info().rss
            
            memory_delta = (memory_after - memory_baseline) / (1024 * 1024)
            memory_samples.append(memory_delta)
        
        # Analyze memory trend
        early_samples = memory_samples[:10]
        late_samples = memory_samples[-10:]
        
        early_average = sum(early_samples) / len(early_samples)
        late_average = sum(late_samples) / len(late_samples)
        
        memory_growth = late_average - early_average
        max_memory_usage = max(memory_samples)
        
        # Assertions
        assert memory_growth < 10, f"Potential memory leak: {memory_growth:.2f}MB growth over iterations"
        assert max_memory_usage < 50, f"Peak memory usage too high: {max_memory_usage:.2f}MB"
        
        # Memory should stabilize, not grow linearly
        # Check that memory doesn't consistently increase
        increasing_trend = sum(1 for i in range(1, len(memory_samples)) 
                              if memory_samples[i] > memory_samples[i-1])
        
        # Less than 70% of samples should show increase (allowing for normal fluctuation)
        assert increasing_trend < len(memory_samples) * 0.7, "Memory consistently increasing"
    
    @pytest.mark.performance
    def test_garbage_collection_effectiveness(self, memory_baseline, large_test_data):
        """Test effectiveness of garbage collection in memory cleanup."""
        data_service = get_data_service()
        
        # Create objects that should be garbage collected
        temp_objects = []
        
        # Phase 1: Create many temporary objects
        gc.collect()
        memory_before_objects = psutil.Process().memory_info().rss
        
        for i in range(100):
            # Create large temporary objects
            temp_obj = {
                "id": i,
                "data": large_test_data["jobs"][:10],  # 10 jobs per object
                "metadata": large_test_data["metrics"],
                "references": [j for j in range(1000)]
            }
            temp_objects.append(temp_obj)
        
        memory_after_objects = psutil.Process().memory_info().rss
        objects_memory = (memory_after_objects - memory_before_objects) / (1024 * 1024)
        
        # Phase 2: Remove references and force garbage collection
        del temp_objects
        
        # Multiple garbage collection passes
        for _ in range(5):
            gc.collect()
        
        memory_after_gc = psutil.Process().memory_info().rss
        
        # Phase 3: Test service operations don't interfere with GC
        mock_db = Mock()
        mock_db.get_all_jobs.return_value = large_test_data["jobs"][:50]
        
        with patch.object(data_service._config_service, 'get_profiles',
                         return_value={"User1": {"name": "Test"}}), \
             patch('src.dashboard.services.data_service.get_job_db', return_value=mock_db):
            
            # Perform operations after GC
            jobs = data_service.get_job_data("User1")
            data_service.clear_cache()
        
        # Final garbage collection
        for _ in range(3):
            gc.collect()
        
        memory_final = psutil.Process().memory_info().rss
        
        # Analyze garbage collection effectiveness
        memory_freed_by_gc = (memory_after_objects - memory_after_gc) / (1024 * 1024)
        final_increase = (memory_final - memory_baseline) / (1024 * 1024)
        
        # Assertions
        assert objects_memory > 5, "Test objects should use significant memory"
        assert memory_freed_by_gc > objects_memory * 0.8, f"GC should free most object memory. Created: {objects_memory:.2f}MB, Freed: {memory_freed_by_gc:.2f}MB"
        assert final_increase < 10, f"Final memory increase should be minimal: {final_increase:.2f}MB"
        
        # Verify service operations completed successfully
        assert len(jobs) == 50
    
    @pytest.mark.performance
    def test_concurrent_memory_usage(self, memory_baseline, large_test_data):
        """Test memory usage under concurrent access patterns."""
        services = [get_data_service(), get_system_service()]
        
        # Track memory usage across threads
        thread_memory_data = []
        memory_lock = threading.Lock()
        
        def worker_thread(thread_id, iterations):
            """Worker thread that performs memory-intensive operations."""
            thread_data = []
            
            for i in range(iterations):
                # Get memory before operation
                gc.collect()
                memory_before = psutil.Process().memory_info().rss
                
                # Perform operations
                for service in services:
                    # Fill cache with data
                    if hasattr(service, '_cache'):
                        cache_key = f"thread_{thread_id}_iter_{i}"
                        service._cache[cache_key] = {
                            "data": large_test_data["jobs"][:5],  # 5 jobs
                            "thread_id": thread_id,
                            "iteration": i
                        }
                        service._cache_timestamps[cache_key] = datetime.now()
                
                # Measure memory after
                memory_after = psutil.Process().memory_info().rss
                memory_delta = (memory_after - memory_before) / (1024 * 1024)
                
                thread_data.append({
                    "thread_id": thread_id,
                    "iteration": i,
                    "memory_delta": memory_delta,
                    "timestamp": time.time()
                })
                
                # Periodic cleanup
                if i % 3 == 2:
                    for service in services:
                        if hasattr(service, 'clear_cache'):
                            service.clear_cache()
            
            with memory_lock:
                thread_memory_data.extend(thread_data)
        
        # Start multiple threads
        num_threads = 4
        iterations_per_thread = 10
        threads = []
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i, iterations_per_thread))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # Final cleanup
        for service in services:
            if hasattr(service, 'clear_cache'):
                service.clear_cache()
        
        for _ in range(3):
            gc.collect()
        
        final_memory = psutil.Process().memory_info().rss
        
        # Analyze results
        total_operations = len(thread_memory_data)
        avg_memory_per_op = sum(data["memory_delta"] for data in thread_memory_data) / total_operations
        max_memory_per_op = max(data["memory_delta"] for data in thread_memory_data)
        
        final_increase = (final_memory - memory_baseline) / (1024 * 1024)
        total_time = end_time - start_time
        
        # Assertions
        assert total_operations == num_threads * iterations_per_thread
        assert total_time < 10, "Concurrent operations should complete reasonably quickly"
        assert avg_memory_per_op < 5, f"Average memory per operation too high: {avg_memory_per_op:.2f}MB"
        assert max_memory_per_op < 15, f"Peak memory per operation too high: {max_memory_per_op:.2f}MB"
        assert final_increase < 20, f"Final memory increase too high: {final_increase:.2f}MB"
        
        # Memory usage should be consistent across threads
        thread_averages = {}
        for thread_id in range(num_threads):
            thread_ops = [data for data in thread_memory_data if data["thread_id"] == thread_id]
            thread_averages[thread_id] = sum(op["memory_delta"] for op in thread_ops) / len(thread_ops)
        
        # Thread memory usage should be similar (no single thread using excessive memory)
        min_avg = min(thread_averages.values())
        max_avg = max(thread_averages.values())
        assert max_avg < min_avg * 2, "Memory usage inconsistent across threads"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
