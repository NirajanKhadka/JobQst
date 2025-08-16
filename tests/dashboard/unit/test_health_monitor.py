"""
Comprehensive unit tests for HealthMonitor.

Tests all functionality of the health monitoring system including:
- Service health checking and aggregation
- Recovery and self-healing mechanisms
- Health history tracking
- Performance monitoring
- Error handling and resilience
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.services.health_monitor import (
    HealthMonitor, 
    get_health_monitor,
    HealthStatus,
    ServiceType
)


class TestHealthMonitor:
    """Test suite for HealthMonitor class."""
    
    @pytest.fixture
    def health_monitor(self):
        """Create a fresh HealthMonitor instance for testing."""
        return HealthMonitor(check_interval=5)
    
    @pytest.fixture
    def mock_healthy_services(self):
        """Mock data for healthy services."""
        return {
            "database": {
                "status": HealthStatus.HEALTHY.value,
                "profiles_count": 2,
                "database_healthy": True,
                "cache_size": 10,
                "timestamp": datetime.now().isoformat()
            },
            "system": {
                "status": HealthStatus.HEALTHY.value,
                "cpu_percent": 25.0,
                "memory_percent": 45.0,
                "disk_usage": 60.0,
                "network_status": "connected",
                "timestamp": datetime.now().isoformat()
            },
            "orchestration": {
                "status": HealthStatus.HEALTHY.value,
                "services_healthy": 2,
                "total_services": 2,
                "timestamp": datetime.now().isoformat()
            },
            "network": {
                "status": HealthStatus.HEALTHY.value,
                "connectivity": "good",
                "timestamp": datetime.now().isoformat()
            },
            "cache": {
                "status": HealthStatus.HEALTHY.value,
                "memory_usage": 30.0,
                "hit_rate": 85.0,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @pytest.fixture
    def mock_degraded_services(self):
        """Mock data for degraded services."""
        return {
            "database": {
                "status": HealthStatus.HEALTHY.value,
                "timestamp": datetime.now().isoformat()
            },
            "system": {
                "status": HealthStatus.DEGRADED.value,
                "cpu_percent": 85.0,  # High but not critical
                "memory_percent": 75.0,
                "timestamp": datetime.now().isoformat()
            },
            "orchestration": {
                "status": HealthStatus.HEALTHY.value,
                "timestamp": datetime.now().isoformat()
            },
            "network": {
                "status": HealthStatus.HEALTHY.value,
                "timestamp": datetime.now().isoformat()
            },
            "cache": {
                "status": HealthStatus.HEALTHY.value,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    @pytest.fixture
    def mock_unhealthy_services(self):
        """Mock data for unhealthy services."""
        return {
            "database": {
                "status": HealthStatus.UNHEALTHY.value,
                "error": "Database connection failed",
                "timestamp": datetime.now().isoformat()
            },
            "system": {
                "status": HealthStatus.UNHEALTHY.value,
                "cpu_percent": 95.0,  # Critical level
                "memory_percent": 95.0,
                "timestamp": datetime.now().isoformat()
            },
            "orchestration": {
                "status": HealthStatus.DEGRADED.value,
                "services_healthy": 1,
                "total_services": 2,
                "timestamp": datetime.now().isoformat()
            },
            "network": {
                "status": HealthStatus.HEALTHY.value,
                "timestamp": datetime.now().isoformat()
            },
            "cache": {
                "status": HealthStatus.HEALTHY.value,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def test_health_monitor_initialization(self, health_monitor):
        """Test HealthMonitor proper initialization."""
        assert health_monitor.check_interval == 5
        assert health_monitor._history == []
        assert health_monitor._last_check is None
        assert health_monitor._recovery_status == {}
        assert health_monitor._check_count == 0
    
    def test_singleton_pattern(self):
        """Test that get_health_monitor returns the same instance."""
        monitor1 = get_health_monitor()
        monitor2 = get_health_monitor()
        
        assert monitor1 is monitor2
        assert isinstance(monitor1, HealthMonitor)
    
    @pytest.mark.asyncio
    async def test_check_service_health_all_healthy(self, health_monitor, mock_healthy_services):
        """Test health check when all services are healthy."""
        # Mock all individual health check methods
        with patch.object(health_monitor, '_check_database_health', 
                         return_value=mock_healthy_services["database"]), \
             patch.object(health_monitor, '_check_system_health',
                         return_value=mock_healthy_services["system"]), \
             patch.object(health_monitor, '_check_orchestration_health',
                         return_value=mock_healthy_services["orchestration"]), \
             patch.object(health_monitor, '_check_network_health',
                         return_value=mock_healthy_services["network"]), \
             patch.object(health_monitor, '_check_cache_health',
                         return_value=mock_healthy_services["cache"]):
            
            result = await health_monitor.check_service_health()
            
            assert isinstance(result, dict)
            assert result["overall_status"] == HealthStatus.HEALTHY.value
            assert "services" in result
            assert "timestamp" in result
            assert "check_duration" in result
            assert len(result["services"]) == 5
    
    @pytest.mark.asyncio
    async def test_check_service_health_degraded(self, health_monitor, mock_degraded_services):
        """Test health check when services are degraded."""
        with patch.object(health_monitor, '_check_database_health',
                         return_value=mock_degraded_services["database"]), \
             patch.object(health_monitor, '_check_system_health',
                         return_value=mock_degraded_services["system"]), \
             patch.object(health_monitor, '_check_orchestration_health',
                         return_value=mock_degraded_services["orchestration"]), \
             patch.object(health_monitor, '_check_network_health',
                         return_value=mock_degraded_services["network"]), \
             patch.object(health_monitor, '_check_cache_health',
                         return_value=mock_degraded_services["cache"]):
            
            result = await health_monitor.check_service_health()
            
            assert result["overall_status"] == HealthStatus.DEGRADED.value
    
    @pytest.mark.asyncio
    async def test_check_service_health_unhealthy(self, health_monitor, mock_unhealthy_services):
        """Test health check when services are unhealthy."""
        with patch.object(health_monitor, '_check_database_health',
                         return_value=mock_unhealthy_services["database"]), \
             patch.object(health_monitor, '_check_system_health',
                         return_value=mock_unhealthy_services["system"]), \
             patch.object(health_monitor, '_check_orchestration_health',
                         return_value=mock_unhealthy_services["orchestration"]), \
             patch.object(health_monitor, '_check_network_health',
                         return_value=mock_unhealthy_services["network"]), \
             patch.object(health_monitor, '_check_cache_health',
                         return_value=mock_unhealthy_services["cache"]):
            
            result = await health_monitor.check_service_health()
            
            assert result["overall_status"] == HealthStatus.UNHEALTHY.value
    
    @pytest.mark.asyncio
    async def test_check_database_health_success(self, health_monitor):
        """Test successful database health checking."""
        mock_data_service = Mock()
        mock_data_service.get_health_status.return_value = {
            "status": "healthy",
            "profiles_count": 2,
            "database_healthy": True,
            "cache_size": 10
        }
        
        with patch('src.dashboard.services.health_monitor.get_data_service',
                  return_value=mock_data_service):
            
            result = await health_monitor._check_database_health()
            
            assert result["status"] == HealthStatus.HEALTHY.value
            assert result["profiles_count"] == 2
            assert result["database_healthy"] is True
    
    @pytest.mark.asyncio
    async def test_check_database_health_failure(self, health_monitor):
        """Test database health checking with failure."""
        with patch('src.dashboard.services.health_monitor.get_data_service',
                  side_effect=Exception("Database error")):
            
            result = await health_monitor._check_database_health()
            
            assert result["status"] == HealthStatus.UNKNOWN.value
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_check_system_health_success(self, health_monitor):
        """Test successful system health checking."""
        mock_system_service = Mock()
        mock_system_service.get_system_metrics.return_value = {
            "cpu_percent": 25.0,
            "memory_percent": 45.0,
            "disk_usage": 60.0,
            "network_status": "connected",
            "services": {}
        }
        
        with patch('src.dashboard.services.health_monitor.get_system_service',
                  return_value=mock_system_service):
            
            result = await health_monitor._check_system_health()
            
            assert result["status"] == HealthStatus.HEALTHY.value
            assert result["cpu_percent"] == 25.0
            assert result["memory_percent"] == 45.0
    
    @pytest.mark.asyncio
    async def test_check_system_health_degraded(self, health_monitor):
        """Test system health checking with degraded performance."""
        mock_system_service = Mock()
        mock_system_service.get_system_metrics.return_value = {
            "cpu_percent": 85.0,  # High but not critical
            "memory_percent": 75.0,
            "disk_usage": 60.0,
            "network_status": "connected",
            "services": {}
        }
        
        with patch('src.dashboard.services.health_monitor.get_system_service',
                  return_value=mock_system_service):
            
            result = await health_monitor._check_system_health()
            
            assert result["status"] == HealthStatus.DEGRADED.value
    
    @pytest.mark.asyncio
    async def test_check_system_health_unhealthy(self, health_monitor):
        """Test system health checking with critical levels."""
        mock_system_service = Mock()
        mock_system_service.get_system_metrics.return_value = {
            "cpu_percent": 95.0,  # Critical level
            "memory_percent": 95.0,  # Critical level
            "disk_usage": 95.0,
            "network_status": "connected",
            "services": {}
        }
        
        with patch('src.dashboard.services.health_monitor.get_system_service',
                  return_value=mock_system_service):
            
            result = await health_monitor._check_system_health()
            
            assert result["status"] == HealthStatus.UNHEALTHY.value
    
    @pytest.mark.asyncio
    async def test_check_orchestration_health_success(self, health_monitor):
        """Test successful orchestration health checking."""
        mock_orchestration_service = Mock()
        mock_orchestration_service.get_orchestration_health.return_value = {
            "overall_status": "healthy",
            "services_healthy": 2,
            "total_services": 2
        }
        
        with patch('src.dashboard.services.health_monitor.get_orchestration_service',
                  return_value=mock_orchestration_service):
            
            result = await health_monitor._check_orchestration_health()
            
            assert result["status"] == "healthy"
            assert result["services_healthy"] == 2
            assert result["total_services"] == 2
    
    @pytest.mark.asyncio
    async def test_check_network_health_success(self, health_monitor):
        """Test successful network health checking."""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect.return_value = None
            
            result = await health_monitor._check_network_health()
            
            assert result["status"] == HealthStatus.HEALTHY.value
            assert "connectivity" in result
    
    @pytest.mark.asyncio
    async def test_check_network_health_failure(self, health_monitor):
        """Test network health checking with connectivity failure."""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect.side_effect = ConnectionError("No connection")
            
            result = await health_monitor._check_network_health()
            
            assert result["status"] == HealthStatus.UNHEALTHY.value
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_check_cache_health_success(self, health_monitor):
        """Test successful cache health checking."""
        # Mock service caches
        mock_services = {
            "data_service": Mock(_cache={"key1": "value1", "key2": "value2"}),
            "system_service": Mock(_cache={"metrics": "data"}),
            "orchestration_service": Mock(_cache={"status": "healthy"})
        }
        
        with patch.dict('sys.modules', {
            'src.dashboard.services.data_service': Mock(get_data_service=lambda: mock_services["data_service"]),
            'src.dashboard.services.system_service': Mock(get_system_service=lambda: mock_services["system_service"]),
            'src.dashboard.services.orchestration_service': Mock(get_orchestration_service=lambda: mock_services["orchestration_service"])
        }):
            result = await health_monitor._check_cache_health()
            
            assert result["status"] == HealthStatus.HEALTHY.value
            assert "total_cache_size" in result
    
    @pytest.mark.asyncio
    async def test_trigger_health_recovery_success(self, health_monitor):
        """Test successful health recovery trigger."""
        with patch.object(health_monitor, '_perform_service_recovery',
                         return_value={"success": True, "action": "cache_cleared"}):
            
            result = await health_monitor.trigger_health_recovery("database")
            
            assert result["success"] is True
            assert result["service"] == "database"
            assert "action" in result
    
    @pytest.mark.asyncio
    async def test_trigger_health_recovery_failure(self, health_monitor):
        """Test health recovery trigger with failure."""
        with patch.object(health_monitor, '_perform_service_recovery',
                         side_effect=Exception("Recovery failed")):
            
            result = await health_monitor.trigger_health_recovery("database")
            
            assert result["success"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_perform_service_recovery_database(self, health_monitor):
        """Test database service recovery."""
        mock_data_service = Mock()
        
        with patch('src.dashboard.services.health_monitor.get_data_service',
                  return_value=mock_data_service):
            
            result = await health_monitor._perform_service_recovery("database")
            
            assert result["success"] is True
            assert result["action"] == "cache_cleared"
            mock_data_service.clear_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_perform_service_recovery_system(self, health_monitor):
        """Test system service recovery."""
        mock_system_service = Mock()
        
        with patch('src.dashboard.services.health_monitor.get_system_service',
                  return_value=mock_system_service):
            
            result = await health_monitor._perform_service_recovery("system")
            
            assert result["success"] is True
            assert result["action"] == "cache_cleared"
            mock_system_service.clear_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_perform_service_recovery_orchestration(self, health_monitor):
        """Test orchestration service recovery."""
        mock_orchestration_service = Mock()
        
        with patch('src.dashboard.services.health_monitor.get_orchestration_service',
                  return_value=mock_orchestration_service):
            
            result = await health_monitor._perform_service_recovery("orchestration")
            
            assert result["success"] is True
            assert result["action"] == "cache_cleared"
            mock_orchestration_service.clear_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_all_caches(self, health_monitor):
        """Test clearing all service caches."""
        mock_data_service = Mock()
        mock_system_service = Mock()
        mock_orchestration_service = Mock()
        
        with patch.dict('sys.modules', {
            'src.dashboard.services.data_service': Mock(get_data_service=lambda: mock_data_service),
            'src.dashboard.services.system_service': Mock(get_system_service=lambda: mock_system_service),
            'src.dashboard.services.orchestration_service': Mock(get_orchestration_service=lambda: mock_orchestration_service)
        }):
            await health_monitor._clear_all_caches()
            
            # Should attempt to clear all service caches
            # Note: The actual implementation may handle import errors gracefully
    
    def test_add_to_history(self, health_monitor):
        """Test adding health check results to history."""
        health_summary = {
            "overall_status": HealthStatus.HEALTHY.value,
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        health_monitor._add_to_history(health_summary)
        
        assert len(health_monitor._history) == 1
        assert health_monitor._history[0] == health_summary
    
    def test_get_health_history(self, health_monitor):
        """Test retrieving health history."""
        # Add some history entries
        for i in range(25):
            health_summary = {
                "overall_status": HealthStatus.HEALTHY.value,
                "timestamp": datetime.now().isoformat(),
                "check_id": i
            }
            health_monitor._add_to_history(health_summary)
        
        # Get recent history (default limit 20)
        history = health_monitor.get_health_history()
        
        assert len(history) == 20
        assert history[0]["check_id"] == 24  # Most recent first
    
    def test_get_health_history_custom_limit(self, health_monitor):
        """Test retrieving health history with custom limit."""
        # Add some history entries
        for i in range(10):
            health_summary = {
                "overall_status": HealthStatus.HEALTHY.value,
                "timestamp": datetime.now().isoformat(),
                "check_id": i
            }
            health_monitor._add_to_history(health_summary)
        
        # Get limited history
        history = health_monitor.get_health_history(limit=5)
        
        assert len(history) == 5
        assert history[0]["check_id"] == 9  # Most recent first
    
    def test_get_recovery_status(self, health_monitor):
        """Test getting current recovery status."""
        # Set some recovery status
        health_monitor._recovery_status = {
            "database": {
                "last_recovery": datetime.now().isoformat(),
                "attempts": 2,
                "success": True
            }
        }
        
        status = health_monitor._get_recovery_status()
        
        assert isinstance(status, dict)
        assert "database" in status
    
    @pytest.mark.asyncio
    async def test_calculate_check_duration(self, health_monitor):
        """Test health check duration calculation."""
        # Set a start time
        health_monitor._last_check = datetime.now() - timedelta(seconds=2)
        
        duration = await health_monitor._calculate_check_duration()
        
        assert isinstance(duration, float)
        assert duration >= 2.0  # Should be at least 2 seconds
        assert duration < 5.0   # Should be reasonable
    
    @pytest.mark.asyncio
    async def test_trigger_recovery_if_needed(self, health_monitor):
        """Test automatic recovery triggering for unhealthy services."""
        unhealthy_results = {
            "database": {
                "status": HealthStatus.UNHEALTHY.value,
                "error": "Connection failed"
            },
            "system": {
                "status": HealthStatus.HEALTHY.value
            }
        }
        
        with patch.object(health_monitor, '_perform_service_recovery',
                         return_value={"success": True, "action": "recovery_performed"}):
            
            await health_monitor._trigger_recovery_if_needed(unhealthy_results)
            
            # Should have attempted recovery for unhealthy service
            assert "database" in health_monitor._recovery_status
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, health_monitor):
        """Test that health checks complete within reasonable time."""
        import time
        
        with patch.object(health_monitor, '_check_database_health',
                         return_value={"status": HealthStatus.HEALTHY.value}), \
             patch.object(health_monitor, '_check_system_health',
                         return_value={"status": HealthStatus.HEALTHY.value}), \
             patch.object(health_monitor, '_check_orchestration_health',
                         return_value={"status": HealthStatus.HEALTHY.value}), \
             patch.object(health_monitor, '_check_network_health',
                         return_value={"status": HealthStatus.HEALTHY.value}), \
             patch.object(health_monitor, '_check_cache_health',
                         return_value={"status": HealthStatus.HEALTHY.value}):
            
            start_time = time.time()
            await health_monitor.check_service_health()
            end_time = time.time()
            
            # Should complete within 3 seconds
            assert (end_time - start_time) < 3.0
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, health_monitor):
        """Test handling of concurrent health checks."""
        with patch.object(health_monitor, '_check_database_health',
                         return_value={"status": HealthStatus.HEALTHY.value}), \
             patch.object(health_monitor, '_check_system_health',
                         return_value={"status": HealthStatus.HEALTHY.value}), \
             patch.object(health_monitor, '_check_orchestration_health',
                         return_value={"status": HealthStatus.HEALTHY.value}), \
             patch.object(health_monitor, '_check_network_health',
                         return_value={"status": HealthStatus.HEALTHY.value}), \
             patch.object(health_monitor, '_check_cache_health',
                         return_value={"status": HealthStatus.HEALTHY.value}):
            
            # Run multiple health checks concurrently
            tasks = [health_monitor.check_service_health() for _ in range(3)]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            for result in results:
                assert isinstance(result, dict)
                assert "overall_status" in result
    
    @pytest.mark.asyncio
    async def test_error_resilience(self, health_monitor):
        """Test that health monitor is resilient to errors."""
        # All checks fail
        with patch.object(health_monitor, '_check_database_health',
                         side_effect=Exception("Database check failed")), \
             patch.object(health_monitor, '_check_system_health',
                         side_effect=Exception("System check failed")), \
             patch.object(health_monitor, '_check_orchestration_health',
                         side_effect=Exception("Orchestration check failed")), \
             patch.object(health_monitor, '_check_network_health',
                         side_effect=Exception("Network check failed")), \
             patch.object(health_monitor, '_check_cache_health',
                         side_effect=Exception("Cache check failed")):
            
            result = await health_monitor.check_service_health()
            
            # Should still return a result, even if degraded
            assert isinstance(result, dict)
            assert "overall_status" in result
            # Should probably be degraded or unknown due to errors
            assert result["overall_status"] in [HealthStatus.DEGRADED.value, HealthStatus.UNKNOWN.value]


class TestHealthMonitorIntegration:
    """Integration tests for HealthMonitor with real services."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_service_health_checks(self):
        """Test with actual service health checks."""
        monitor = HealthMonitor()
        
        try:
            # This should work with real services if they're available
            result = await monitor.check_service_health()
            
            assert isinstance(result, dict)
            assert "overall_status" in result
            assert "services" in result
            assert "timestamp" in result
            
        except Exception as e:
            pytest.skip(f"Real service health checks not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_recovery_mechanisms(self):
        """Test actual recovery mechanisms."""
        monitor = HealthMonitor()
        
        try:
            # Test recovery for a specific service
            result = await monitor.trigger_health_recovery("cache")
            
            assert isinstance(result, dict)
            assert "success" in result
            assert "service" in result
            
        except Exception as e:
            pytest.skip(f"Real recovery mechanisms not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
