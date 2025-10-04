"""
Error Tolerance Handler for AutoJobAgent
Provides reliable error handling, retry mechanisms, and system health monitoring.
"""

import asyncio
import functools
import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from threading import Lock

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
    RetryError,
)

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry operations."""

    max_attempts: int = 3
    min_wait: float = 1.0
    max_wait: float = 60.0
    multiplier: float = 2.0
    exceptions: tuple = (Exception,)


@dataclass
class SystemMetrics:
    """System health metrics."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    active_connections: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "unknown"


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
    multiplier: float = 2.0,
    exceptions: tuple = (Exception,),
    reraise: bool = True,
):
    """
    Decorator to add retry functionality to a function.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        multiplier: Exponential backoff multiplier
        exceptions: Tuple of exceptions to retry on
        reraise: Whether to reraise the original exception on final failure

    Returns:
        Decorated function with retry capability
    """

    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO),
            reraise=reraise,
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Function {func.__name__} failed: {e}")
                raise

        return wrapper

    return decorator


def with_fallback(fallback_value: Any = None, fallback_func: Optional[Callable] = None):
    """
    Decorator to provide fallback behavior when a function fails.

    Args:
        fallback_value: Value to return if function fails
        fallback_func: Function to call if main function fails

    Returns:
        Decorated function with fallback capability
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Function {func.__name__} failed, using fallback: {e}")

                if fallback_func:
                    try:
                        return fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        logger.error(f"Fallback function also failed: {fallback_error}")
                        return fallback_value

                return fallback_value

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    *args,
    fallback_value: Any = None,
    max_attempts: int = 1,
    log_errors: bool = True,
    **kwargs,
) -> Any:
    """
    Safely execute a function with error handling and optional retry.

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        fallback_value: Value to return if function fails
        max_attempts: Number of attempts to make
        log_errors: Whether to log errors
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or fallback_value on failure
    """
    last_exception = None

    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if log_errors:
                logger.warning(
                    f"safe_execute attempt {attempt + 1}/{max_attempts} failed "
                    f"for {func.__name__}: {e}"
                )

            if attempt < max_attempts - 1:
                # Wait before retry with exponential backoff
                wait_time = min(2**attempt, 30)  # Cap at 30 seconds
                time.sleep(wait_time)

    if log_errors:
        logger.error(f"safe_execute failed after {max_attempts} attempts: {last_exception}")

    return fallback_value


class reliableOperationManager:
    """
    Manages reliable operations with circuit breaker pattern and health monitoring.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initialize the reliableOperationManager.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery (seconds)
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        self._lock = Lock()

        logger.info(f"reliableOperationManager initialized with threshold={failure_threshold}")

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        with self._lock:
            # Check if circuit should be closed (recovery attempt)
            if self.circuit_open and self._should_attempt_reset():
                logger.info("Attempting to close circuit breaker")
                self.circuit_open = False
                self.failure_count = 0

            # If circuit is still open, fail fast
            if self.circuit_open:
                raise Exception(
                    f"Circuit breaker is open. Too many failures "
                    f"(threshold: {self.failure_threshold})"
                )

        try:
            result = func(*args, **kwargs)
            # Reset failure count on success
            with self._lock:
                self.failure_count = 0
            return result

        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = datetime.now()

                if self.failure_count >= self.failure_threshold:
                    self.circuit_open = True
                    logger.error(f"Circuit breaker opened after {self.failure_count} failures")

            logger.error(f"Operation failed (count: {self.failure_count}): {e}")
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if not self.last_failure_time:
            return True

        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "circuit_open": self.circuit_open,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": (
                self.last_failure_time.isoformat() if self.last_failure_time else None
            ),
            "recovery_timeout": self.recovery_timeout,
        }


class SystemHealthMonitor:
    """
    Monitors system health and provides metrics.
    """

    def __init__(self, check_interval: int = 30):
        """
        Initialize the SystemHealthMonitor.

        Args:
            check_interval: How often to update metrics (seconds)
        """
        self.check_interval = check_interval
        self.last_check = None
        self.current_metrics = SystemMetrics()
        self._lock = Lock()

        logger.info(f"SystemHealthMonitor initialized with interval={check_interval}s")

    def get_metrics(self, force_update: bool = False) -> SystemMetrics:
        """
        Get current system metrics.

        Args:
            force_update: Force immediate update regardless of interval

        Returns:
            Current system metrics
        """
        with self._lock:
            now = datetime.now()

            # Update if forced or enough time has passed
            if (
                force_update
                or not self.last_check
                or (now - self.last_check).seconds >= self.check_interval
            ):

                self._update_metrics()
                self.last_check = now

        return self.current_metrics

    def _update_metrics(self) -> None:
        """Update system metrics."""
        try:
            # CPU and memory metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Network connections
            connections = len(psutil.net_connections())

            # Determine status based on thresholds
            status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = "critical"
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = "warning"

            self.current_metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                active_connections=connections,
                timestamp=datetime.now(),
                status=status,
            )

            logger.debug(f"Updated system metrics: {status}")

        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
            self.current_metrics.status = "error"

    def is_healthy(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0) -> bool:
        """
        Check if system is healthy based on thresholds.

        Args:
            cpu_threshold: CPU usage threshold (%)
            memory_threshold: Memory usage threshold (%)

        Returns:
            True if system is healthy
        """
        metrics = self.get_metrics()
        return (
            metrics.cpu_percent < cpu_threshold
            and metrics.memory_percent < memory_threshold
            and metrics.status in ["healthy", "warning"]
        )


# Global instances for convenience
_reliable_manager = None
_health_monitor = None


def get_error_tolerance_handler() -> reliableOperationManager:
    """
    Get the global reliableOperationManager instance.

    Returns:
        Global reliableOperationManager instance
    """
    global _reliable_manager
    if _reliable_manager is None:
        _reliable_manager = reliableOperationManager()
    return _reliable_manager


def get_system_health_monitor() -> SystemHealthMonitor:
    """
    Get the global SystemHealthMonitor instance.

    Returns:
        Global SystemHealthMonitor instance
    """
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = SystemHealthMonitor()
    return _health_monitor
