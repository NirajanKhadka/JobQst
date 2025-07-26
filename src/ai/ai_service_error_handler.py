#!/usr/bin/env python3
"""
AI Service Error Handler - Enhanced error handling with Mistral client patterns
Implements proper exception handling, retry logic, and circuit breaker patterns
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import requests
from functools import wraps

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types"""
    TRANSIENT = "transient"  # Retry-able errors
    PERMANENT = "permanent"  # Non-retry-able errors
    TIMEOUT = "timeout"      # Timeout errors
    CONNECTION = "connection"  # Connection errors
    VALIDATION = "validation"  # Validation errors
    UNKNOWN = "unknown"      # Unknown errors


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, blocking calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ErrorInfo:
    """Error information"""
    error_type: ErrorType
    message: str
    original_exception: Exception
    retry_after: Optional[float] = None
    is_retryable: bool = True


class CircuitBreaker:
    """Circuit breaker implementation for AI services"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return self.half_open_calls < self.config.half_open_max_calls
        
        return False
    
    def record_success(self):
        """Record successful execution"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.config.half_open_max_calls:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker transitioning to CLOSED")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker transitioning to OPEN from HALF_OPEN")
        elif self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")


class AIServiceErrorHandler:
    """Enhanced error handler for AI services with Mistral client patterns"""
    
    def __init__(self, 
                 retry_config: Optional[RetryConfig] = None,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize error handler.
        
        Args:
            retry_config: Retry configuration
            circuit_breaker_config: Circuit breaker configuration
        """
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config or CircuitBreakerConfig())
        
        # Error statistics
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'retried_calls': 0,
            'circuit_breaker_trips': 0,
            'error_types': {error_type.value: 0 for error_type in ErrorType}
        }
    
    def classify_error(self, exception: Exception) -> ErrorInfo:
        """
        Classify error based on exception type and message.
        
        Args:
            exception: The exception to classify
            
        Returns:
            ErrorInfo with classification details
        """
        error_message = str(exception)
        error_type = ErrorType.UNKNOWN
        is_retryable = True
        retry_after = None
        
        # Classify based on exception type
        if isinstance(exception, requests.exceptions.Timeout):
            error_type = ErrorType.TIMEOUT
            is_retryable = True
        elif isinstance(exception, requests.exceptions.ConnectionError):
            error_type = ErrorType.CONNECTION
            is_retryable = True
        elif isinstance(exception, requests.exceptions.HTTPError):
            status_code = getattr(exception.response, 'status_code', 0)
            if 400 <= status_code < 500:
                error_type = ErrorType.VALIDATION
                is_retryable = status_code in [408, 429, 502, 503, 504]  # Specific retryable 4xx codes
                
                # Check for rate limiting
                if status_code == 429:
                    retry_after_header = getattr(exception.response, 'headers', {}).get('Retry-After')
                    if retry_after_header:
                        try:
                            retry_after = float(retry_after_header)
                        except ValueError:
                            retry_after = 60  # Default retry after 1 minute
            elif 500 <= status_code < 600:
                error_type = ErrorType.TRANSIENT
                is_retryable = True
        
        # Classify based on error message patterns
        error_message_lower = error_message.lower()
        if any(pattern in error_message_lower for pattern in ['timeout', 'timed out']):
            error_type = ErrorType.TIMEOUT
        elif any(pattern in error_message_lower for pattern in ['connection', 'network', 'unreachable']):
            error_type = ErrorType.CONNECTION
        elif any(pattern in error_message_lower for pattern in ['validation', 'invalid', 'bad request']):
            error_type = ErrorType.VALIDATION
            is_retryable = False
        elif any(pattern in error_message_lower for pattern in ['server error', 'internal error', 'service unavailable']):
            error_type = ErrorType.TRANSIENT
        
        # Handle Mistral-specific errors
        try:
            # Try to import Mistral models for specific error handling
            from mistralai import models
            
            if isinstance(exception, models.HTTPValidationError):
                error_type = ErrorType.VALIDATION
                is_retryable = False
            elif isinstance(exception, models.SDKError):
                error_type = ErrorType.TRANSIENT
                is_retryable = True
        except ImportError:
            pass  # Mistral not available
        
        return ErrorInfo(
            error_type=error_type,
            message=error_message,
            original_exception=exception,
            retry_after=retry_after,
            is_retryable=is_retryable
        )
    
    def calculate_delay(self, attempt: int, base_delay: float = None, retry_after: float = None) -> float:
        """
        Calculate delay for retry attempt with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            base_delay: Base delay override
            retry_after: Specific retry-after delay
            
        Returns:
            Delay in seconds
        """
        if retry_after:
            return retry_after
        
        base = base_delay or self.retry_config.initial_delay
        delay = min(base * (self.retry_config.backoff_multiplier ** attempt), self.retry_config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.retry_config.jitter:
            import random
            jitter_range = delay * 0.25  # ±25% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    async def execute_with_retry(self, 
                                func: Callable,
                                *args,
                                **kwargs) -> Any:
        """
        Execute function with retry logic and circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        self.stats['total_calls'] += 1
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            self.stats['circuit_breaker_trips'] += 1
            raise Exception("Circuit breaker is OPEN - service unavailable")
        
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Record success
                self.circuit_breaker.record_success()
                self.stats['successful_calls'] += 1
                
                if attempt > 0:
                    logger.info(f"Function succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_info = self.classify_error(e)
                
                # Update error statistics
                self.stats['error_types'][error_info.error_type.value] += 1
                
                # Check if we should retry
                if not error_info.is_retryable or attempt == self.retry_config.max_attempts - 1:
                    break
                
                # Calculate delay
                delay = self.calculate_delay(attempt, retry_after=error_info.retry_after)
                
                logger.warning(f"Attempt {attempt + 1} failed ({error_info.error_type.value}): {error_info.message}. "
                             f"Retrying in {delay:.1f}s...")
                
                self.stats['retried_calls'] += 1
                
                # Wait before retry
                if delay > 0:
                    await asyncio.sleep(delay)
        
        # All attempts failed
        self.circuit_breaker.record_failure()
        self.stats['failed_calls'] += 1
        
        if last_exception:
            error_info = self.classify_error(last_exception)
            logger.error(f"All {self.retry_config.max_attempts} attempts failed. "
                        f"Final error ({error_info.error_type.value}): {error_info.message}")
            raise last_exception
        else:
            raise Exception("Unknown error occurred during retry attempts")
    
    def execute_with_retry_sync(self, 
                               func: Callable,
                               *args,
                               **kwargs) -> Any:
        """
        Synchronous version of execute_with_retry.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        self.stats['total_calls'] += 1
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            self.stats['circuit_breaker_trips'] += 1
            raise Exception("Circuit breaker is OPEN - service unavailable")
        
        last_exception = None
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                result = func(*args, **kwargs)
                
                # Record success
                self.circuit_breaker.record_success()
                self.stats['successful_calls'] += 1
                
                if attempt > 0:
                    logger.info(f"Function succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_info = self.classify_error(e)
                
                # Update error statistics
                self.stats['error_types'][error_info.error_type.value] += 1
                
                # Check if we should retry
                if not error_info.is_retryable or attempt == self.retry_config.max_attempts - 1:
                    break
                
                # Calculate delay
                delay = self.calculate_delay(attempt, retry_after=error_info.retry_after)
                
                logger.warning(f"Attempt {attempt + 1} failed ({error_info.error_type.value}): {error_info.message}. "
                             f"Retrying in {delay:.1f}s...")
                
                self.stats['retried_calls'] += 1
                
                # Wait before retry
                if delay > 0:
                    time.sleep(delay)
        
        # All attempts failed
        self.circuit_breaker.record_failure()
        self.stats['failed_calls'] += 1
        
        if last_exception:
            error_info = self.classify_error(last_exception)
            logger.error(f"All {self.retry_config.max_attempts} attempts failed. "
                        f"Final error ({error_info.error_type.value}): {error_info.message}")
            raise last_exception
        else:
            raise Exception("Unknown error occurred during retry attempts")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics."""
        total_calls = max(self.stats['total_calls'], 1)
        
        return {
            **self.stats,
            'success_rate': (self.stats['successful_calls'] / total_calls) * 100,
            'retry_rate': (self.stats['retried_calls'] / total_calls) * 100,
            'circuit_breaker_state': self.circuit_breaker.state.value,
            'circuit_breaker_failures': self.circuit_breaker.failure_count
        }
    
    def reset_statistics(self):
        """Reset error handling statistics."""
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'retried_calls': 0,
            'circuit_breaker_trips': 0,
            'error_types': {error_type.value: 0 for error_type in ErrorType}
        }
        
        # Reset circuit breaker
        self.circuit_breaker.state = CircuitBreakerState.CLOSED
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.half_open_calls = 0


def with_retry(retry_config: Optional[RetryConfig] = None,
               circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator for adding retry logic to functions.
    
    Args:
        retry_config: Retry configuration
        circuit_breaker_config: Circuit breaker configuration
    """
    def decorator(func):
        error_handler = AIServiceErrorHandler(retry_config, circuit_breaker_config)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return error_handler.execute_with_retry_sync(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await error_handler.execute_with_retry(func, *args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


# Global error handler instance
_global_error_handler = None

def get_ai_error_handler(retry_config: Optional[RetryConfig] = None,
                        circuit_breaker_config: Optional[CircuitBreakerConfig] = None) -> AIServiceErrorHandler:
    """Get or create global AI service error handler."""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = AIServiceErrorHandler(retry_config, circuit_breaker_config)
    
    return _global_error_handler


if __name__ == "__main__":
    # Test the error handler
    import random
    
    def flaky_function(success_rate: float = 0.3):
        """Test function that fails randomly"""
        if random.random() < success_rate:
            return "Success!"
        else:
            raise requests.exceptions.ConnectionError("Connection failed")
    
    # Test with decorator
    @with_retry(RetryConfig(max_attempts=5, initial_delay=0.1))
    def decorated_flaky_function():
        return flaky_function(0.7)
    
    # Test error handler
    error_handler = AIServiceErrorHandler()
    
    print("Testing AI Service Error Handler...")
    
    try:
        result = error_handler.execute_with_retry_sync(flaky_function, 0.8)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")
    
    print("\nStatistics:")
    stats = error_handler.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nTesting decorator:")
    try:
        result = decorated_flaky_function()
        print(f"Decorated result: {result}")
    except Exception as e:
        print(f"Decorated failed: {e}")