"""
Base service interface for dashboard services.
Implements clean architecture principles and SOLID design patterns.
Following Development Standards for proper service interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def cache_result(timeout: int = 300):
    """Decorator for caching service method results.

    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Create cache key from method name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"

            # Check if we have cached result
            if hasattr(self, "_cache") and cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if time.time() - timestamp < timeout:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_data

            # Execute function and cache result
            result = func(self, *args, **kwargs)

            # Initialize cache if needed
            if not hasattr(self, "_cache"):
                self._cache = {}

            self._cache[cache_key] = (result, time.time())
            logger.debug(f"Cached result for {func.__name__}")
            return result

        return wrapper

    return decorator


class BaseService(ABC):
    """Base service class implementing common patterns.

    All dashboard services should inherit from this class to ensure
    consistent interfaces and proper error handling.
    """

    def __init__(self):
        """Initialize base service."""
        self._cache = {}
        self._initialized = False

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info(f"{self.__class__.__name__} cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "service_name": self.__class__.__name__,
            "initialized": self._initialized,
        }

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check service health status.

        Returns:
            Dict with health status information
        """
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service.

        Returns:
            True if initialization successful, False otherwise
        """
        pass


class ServiceRegistry:
    """Registry for managing dashboard services.

    Implements singleton pattern for service management.
    """

    _instance = None
    _services = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRegistry, cls).__new__(cls)
        return cls._instance

    def register_service(self, name: str, service: BaseService) -> None:
        """Register a service.

        Args:
            name: Service name
            service: Service instance
        """
        self._services[name] = service
        logger.info(f"Service registered: {name}")

    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a registered service.

        Args:
            name: Service name

        Returns:
            Service instance or None if not found
        """
        return self._services.get(name)

    def get_all_services(self) -> Dict[str, BaseService]:
        """Get all registered services."""
        return self._services.copy()

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Run health check on all services."""
        results = {}
        for name, service in self._services.items():
            try:
                results[name] = service.health_check()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return results


# Global service registry instance
service_registry = ServiceRegistry()
