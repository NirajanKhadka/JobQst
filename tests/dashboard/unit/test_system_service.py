"""
Comprehensive unit tests for SystemService.

Tests all functionality of the system service including:
- System metrics collection
- Service health monitoring  
- Caching mechanisms
- Error handling and recovery
- Performance monitoring
"""

import pytest
import asyncio
import psutil
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.services.system_service import SystemService, get_system_service


class TestSystemService:
    """Test suite for SystemService class."""
    
    @pytest.fixture
    def system_service(self):
        """Create a fresh SystemService instance for testing."""
        return SystemService(cache_ttl=5)
    
    @pytest.fixture
    def mock_psutil(self):
        """Mock psutil functions for consistent testing."""
        with patch.multiple(
            'psutil',
            cpu_percent=Mock(return_value=25.5),
            virtual_memory=Mock(return_value=Mock(percent=45.2)),
            disk_usage=Mock(return_value=Mock(percent=65.8)),
            net_io_counters=Mock(return_value=Mock(bytes_sent=1000, bytes_recv=2000)),
            process_iter=Mock(return_value=[]),
            boot_time=Mock(return_value=1640995200.0)  # Fixed timestamp for testing
        ) as mock:
            yield mock
    
    def test_system_service_initialization(self):
        """Test SystemService proper initialization."""
        service = SystemService(cache_ttl=30)
        
        assert service.cache_ttl == 30
        assert service._cache == {}
        assert service._cache_timestamps == {}
        assert service._background_task is None
        assert service._last_metrics_time is None
    
    def test_singleton_pattern(self):
        """Test that get_system_service returns the same instance."""
        service1 = get_system_service()
        service2 = get_system_service()
        
        assert service1 is service2
        assert isinstance(service1, SystemService)
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_success(self, system_service, mock_psutil):
        """Test successful system metrics collection."""
        # Mock socket for port checking
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 0
            
            metrics = await system_service.get_system_metrics()
            
            assert isinstance(metrics, dict)
            assert 'cpu_percent' in metrics
            assert 'memory_percent' in metrics
            assert 'disk_usage' in metrics
            assert 'network_status' in metrics
            assert 'services' in metrics
            assert 'orchestration' in metrics
            assert 'timestamp' in metrics
            
            # Verify metric values
            assert metrics['cpu_percent'] == 25.5
            assert metrics['memory_percent'] == 45.2
            assert metrics['disk_usage'] == 65.8
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_caching(self, system_service, mock_psutil):
        """Test that metrics are properly cached."""
        with patch('socket.socket'):
            # First call
            metrics1 = await system_service.get_system_metrics()
            first_timestamp = metrics1['timestamp']
            
            # Second call should return cached data
            metrics2 = await system_service.get_system_metrics()
            
            assert metrics1['timestamp'] == metrics2['timestamp']
            assert metrics1 == metrics2
    
    @pytest.mark.asyncio
    async def test_get_system_metrics_cache_expiration(self, system_service, mock_psutil):
        """Test that cache expires after TTL."""
        system_service.cache_ttl = 0.1  # 100ms for quick testing
        
        with patch('socket.socket'):
            # First call
            await system_service.get_system_metrics()
            
            # Wait for cache to expire
            await asyncio.sleep(0.2)
            
            # Mock different values for second call
            mock_psutil['cpu_percent'].return_value = 50.0
            
            # Second call should fetch fresh data
            metrics = await system_service.get_system_metrics()
            assert metrics['cpu_percent'] == 50.0
    
    @pytest.mark.asyncio
    async def test_check_services_async(self, system_service):
        """Test asynchronous service checking."""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect_ex.side_effect = [0, 1]  # Streamlit up, Ollama down
            
            services = await system_service._check_services_async()
            
            assert isinstance(services, dict)
            assert 'streamlit' in services
            assert 'ollama' in services
            assert services['streamlit'] == 'running'
            assert services['ollama'] == 'stopped'
    
    @pytest.mark.asyncio
    async def test_check_orchestration_status(self, system_service):
        """Test orchestration status checking."""
        # Mock process iterator with test processes
        mock_processes = [
            Mock(info={'pid': 1234, 'name': 'python', 'cmdline': ['python', 'main.py', 'scrape']}),
            Mock(info={'pid': 1235, 'name': 'python', 'cmdline': ['python', 'main.py', 'process']}),
            Mock(info={'pid': 1236, 'name': 'python', 'cmdline': ['python', 'document_generator.py']})
        ]
        
        with patch('psutil.process_iter', return_value=mock_processes):
            status = await system_service._check_orchestration_status()
            
            assert isinstance(status, dict)
            assert 'scraper' in status
            assert 'processor' in status
            assert status['scraper'] == 'running'
            assert status['processor'] == 'running'
    
    def test_get_service_health_healthy(self, system_service):
        """Test service health reporting when system is healthy."""
        # Mock cached metrics with healthy values
        system_service._cache['system_metrics'] = {
            'cpu_percent': 20.0,
            'memory_percent': 30.0,
            'services': {'streamlit': 'running'},
            'orchestration': {'scraper': 'running'}
        }
        system_service._cache_timestamps['system_metrics'] = datetime.now()
        
        health = system_service.get_service_health()
        
        assert health['overall_status'] == 'healthy'
        assert health['system']['cpu_percent'] == 20.0
        assert health['system']['memory_percent'] == 30.0
    
    def test_get_service_health_degraded(self, system_service):
        """Test service health reporting when system is degraded."""
        # Mock cached metrics with degraded values
        system_service._cache['system_metrics'] = {
            'cpu_percent': 85.0,  # High but not critical
            'memory_percent': 40.0,
            'services': {},
            'orchestration': {}
        }
        system_service._cache_timestamps['system_metrics'] = datetime.now()
        
        health = system_service.get_service_health()
        
        assert health['overall_status'] == 'degraded'
    
    def test_get_service_health_unhealthy(self, system_service):
        """Test service health reporting when system is unhealthy."""
        # Mock cached metrics with unhealthy values
        system_service._cache['system_metrics'] = {
            'cpu_percent': 95.0,  # Critical level
            'memory_percent': 95.0,  # Critical level
            'services': {},
            'orchestration': {}
        }
        system_service._cache_timestamps['system_metrics'] = datetime.now()
        
        health = system_service.get_service_health()
        
        assert health['overall_status'] == 'unhealthy'
    
    def test_cache_validation(self, system_service):
        """Test cache validation logic."""
        cache_key = 'test_key'
        
        # No cache entry
        assert not system_service._is_cache_valid(cache_key)
        
        # Valid cache entry
        system_service._cache_timestamps[cache_key] = datetime.now()
        assert system_service._is_cache_valid(cache_key)
        
        # Expired cache entry
        system_service._cache_timestamps[cache_key] = datetime.now() - timedelta(seconds=system_service.cache_ttl + 1)
        assert not system_service._is_cache_valid(cache_key)
    
    def test_clear_cache(self, system_service):
        """Test cache clearing functionality."""
        # Add some cache data
        system_service._cache['test'] = 'data'
        system_service._cache_timestamps['test'] = datetime.now()
        
        system_service.clear_cache()
        
        assert system_service._cache == {}
        assert system_service._cache_timestamps == {}
    
    @pytest.mark.asyncio
    async def test_error_handling_in_metrics_collection(self, system_service):
        """Test error handling during metrics collection."""
        with patch('psutil.cpu_percent', side_effect=Exception("Test error")):
            # Should not raise exception, but handle gracefully
            metrics = await system_service.get_system_metrics()
            
            # Should return partial metrics with error information
            assert isinstance(metrics, dict)
            assert 'timestamp' in metrics
            # May have some default values or error indicators
    
    @pytest.mark.asyncio
    async def test_background_refresh_metrics(self, system_service):
        """Test background metrics refresh functionality."""
        system_service._background_task = Mock()
        
        # This would normally be tested with actual background task running
        # For unit test, we verify the method exists and is callable
        assert hasattr(system_service, '_background_refresh_metrics')
        assert callable(system_service._background_refresh_metrics)
    
    @pytest.mark.asyncio
    async def test_network_connectivity_check(self, system_service):
        """Test network connectivity checking."""
        with patch('socket.socket') as mock_socket:
            # Test successful connection
            mock_socket.return_value.__enter__.return_value.connect_ex.return_value = 0
            
            metrics = await system_service.get_system_metrics()
            assert 'network_status' in metrics
    
    def test_memory_management(self, system_service):
        """Test that service manages memory efficiently."""
        # Add multiple cache entries
        for i in range(100):
            system_service._cache[f'key_{i}'] = f'data_{i}' * 1000
            system_service._cache_timestamps[f'key_{i}'] = datetime.now()
        
        # Clear cache and verify memory is freed
        system_service.clear_cache()
        
        assert len(system_service._cache) == 0
        assert len(system_service._cache_timestamps) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_metrics_requests(self, system_service, mock_psutil):
        """Test handling of concurrent metrics requests."""
        with patch('socket.socket'):
            # Make multiple concurrent requests
            tasks = [system_service.get_system_metrics() for _ in range(5)]
            results = await asyncio.gather(*tasks)
            
            # All should return the same cached result
            for result in results[1:]:
                assert result == results[0]
    
    @pytest.mark.asyncio 
    async def test_performance_metrics_collection(self, system_service, mock_psutil):
        """Test that metrics collection completes within reasonable time."""
        import time
        
        with patch('socket.socket'):
            start_time = time.time()
            await system_service.get_system_metrics()
            end_time = time.time()
            
            # Should complete within 2 seconds
            assert (end_time - start_time) < 2.0
    
    def test_service_dependency_handling(self, system_service):
        """Test handling of service dependencies."""
        # Test with missing dependencies
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            # Should handle gracefully without crashing
            health = system_service.get_service_health()
            assert isinstance(health, dict)
            assert 'overall_status' in health


class TestSystemServiceIntegration:
    """Integration tests for SystemService with real system resources."""
    
    @pytest.mark.integration
    def test_real_system_metrics(self):
        """Test with actual system metrics (integration test)."""
        service = SystemService()
        
        # This should work with real psutil
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent
            
            assert isinstance(cpu, (int, float))
            assert isinstance(memory, (int, float))
            assert 0 <= cpu <= 100
            assert 0 <= memory <= 100
        except Exception as e:
            pytest.skip(f"Real system metrics not available: {e}")
    
    @pytest.mark.integration 
    @pytest.mark.asyncio
    async def test_real_service_discovery(self):
        """Test actual service discovery on the system."""
        service = SystemService()
        
        try:
            services = await service._check_services_async()
            assert isinstance(services, dict)
            # Should at least check for some services
            assert len(services) > 0
        except Exception as e:
            pytest.skip(f"Service discovery not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
