#!/usr/bin/env python3
"""
Enhanced Error Tolerance and Robustness System
Provides comprehensive error handling, retry mechanisms, and fallback strategies.
"""

import time
import json
import traceback
import functools
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Union
from rich.console import Console

console = Console()

class RobustOperationManager:
    """
    Manages robust operations with retry logic, fallbacks, and error recovery.
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize the robust operation manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries (exponential backoff)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.error_log = []
        self.recovery_strategies = {}
        
    def with_retry(self, 
                   operation_name: str = "operation",
                   exceptions: tuple = (Exception,),
                   max_retries: Optional[int] = None,
                   backoff_factor: float = 2.0,
                   max_delay: float = 60.0):
        """
        Decorator for adding retry logic to functions.
        
        Args:
            operation_name: Name of the operation for logging
            exceptions: Tuple of exceptions to catch and retry
            max_retries: Override default max retries
            backoff_factor: Exponential backoff factor
            max_delay: Maximum delay between retries
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                retries = max_retries if max_retries is not None else self.max_retries
                last_exception = None
                
                for attempt in range(retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        if attempt > 0:
                            console.print(f"[green]✅ {operation_name} succeeded on attempt {attempt + 1}[/green]")
                        return result
                        
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < retries:
                            delay = min(self.base_delay * (backoff_factor ** attempt), max_delay)
                            console.print(f"[yellow]⚠️ {operation_name} failed (attempt {attempt + 1}/{retries + 1}): {e}[/yellow]")
                            console.print(f"[cyan]🔄 Retrying in {delay:.1f} seconds...[/cyan]")
                            time.sleep(delay)
                        else:
                            console.print(f"[red]❌ {operation_name} failed after {retries + 1} attempts[/red]")
                            self._log_error(operation_name, e, attempt + 1)
                
                # If we get here, all retries failed
                raise last_exception
                
            return wrapper
        return decorator
    
    def with_fallback(self, fallback_func: Callable, operation_name: str = "operation"):
        """
        Decorator for adding fallback functionality to functions.
        
        Args:
            fallback_func: Function to call if primary function fails
            operation_name: Name of the operation for logging
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    console.print(f"[yellow]⚠️ {operation_name} failed, trying fallback: {e}[/yellow]")
                    try:
                        result = fallback_func(*args, **kwargs)
                        console.print(f"[green]✅ {operation_name} fallback succeeded[/green]")
                        return result
                    except Exception as fallback_error:
                        console.print(f"[red]❌ {operation_name} fallback also failed: {fallback_error}[/red]")
                        self._log_error(f"{operation_name}_fallback", fallback_error, 1)
                        raise e  # Raise original exception
                        
            return wrapper
        return decorator
    
    def safe_execute(self, 
                     func: Callable, 
                     *args, 
                     operation_name: str = "operation",
                     default_return: Any = None,
                     log_errors: bool = True,
                     **kwargs) -> Any:
        """
        Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            operation_name: Name of the operation for logging
            default_return: Value to return if function fails
            log_errors: Whether to log errors
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result or default_return if failed
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                console.print(f"[red]❌ {operation_name} failed: {e}[/red]")
                self._log_error(operation_name, e, 1)
            return default_return
    
    def circuit_breaker(self, 
                       failure_threshold: int = 5,
                       recovery_timeout: int = 60,
                       operation_name: str = "operation"):
        """
        Circuit breaker pattern to prevent cascading failures.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            operation_name: Name of the operation for logging
        """
        def decorator(func: Callable) -> Callable:
            state = {"failures": 0, "last_failure": None, "state": "closed"}
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                now = datetime.now()
                
                # Check if circuit is open and recovery timeout has passed
                if state["state"] == "open":
                    if state["last_failure"] and (now - state["last_failure"]).seconds >= recovery_timeout:
                        state["state"] = "half-open"
                        console.print(f"[yellow]🔄 Circuit breaker for {operation_name} moving to half-open[/yellow]")
                    else:
                        raise Exception(f"Circuit breaker open for {operation_name}")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Success - reset circuit breaker
                    if state["failures"] > 0:
                        console.print(f"[green]✅ Circuit breaker for {operation_name} reset[/green]")
                    state["failures"] = 0
                    state["state"] = "closed"
                    return result
                    
                except Exception as e:
                    state["failures"] += 1
                    state["last_failure"] = now
                    
                    if state["failures"] >= failure_threshold:
                        state["state"] = "open"
                        console.print(f"[red]🚫 Circuit breaker opened for {operation_name} after {failure_threshold} failures[/red]")
                    
                    raise e
                    
            return wrapper
        return decorator
    
    def _log_error(self, operation_name: str, error: Exception, attempt: int):
        """Log error details for analysis."""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "attempt": attempt,
            "traceback": traceback.format_exc()
        }
        
        self.error_log.append(error_entry)
        
        # Keep only last 100 errors to prevent memory issues
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
    
    def get_error_summary(self) -> Dict:
        """Get summary of recent errors."""
        if not self.error_log:
            return {"total_errors": 0, "recent_errors": []}
        
        # Group errors by type
        error_counts = {}
        recent_errors = self.error_log[-10:]  # Last 10 errors
        
        for error in self.error_log:
            error_type = error["error_type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "error_counts": error_counts,
            "recent_errors": recent_errors
        }
    
    def register_recovery_strategy(self, error_type: str, recovery_func: Callable):
        """
        Register a recovery strategy for a specific error type.
        
        Args:
            error_type: Type of error to handle
            recovery_func: Function to call for recovery
        """
        self.recovery_strategies[error_type] = recovery_func
        console.print(f"[cyan]📋 Registered recovery strategy for {error_type}[/cyan]")
    
    def attempt_recovery(self, error: Exception, context: Dict = None) -> bool:
        """
        Attempt to recover from an error using registered strategies.
        
        Args:
            error: The error that occurred
            context: Additional context for recovery
            
        Returns:
            True if recovery was successful, False otherwise
        """
        error_type = type(error).__name__
        
        if error_type in self.recovery_strategies:
            try:
                console.print(f"[cyan]🔧 Attempting recovery for {error_type}[/cyan]")
                recovery_func = self.recovery_strategies[error_type]
                recovery_func(error, context or {})
                console.print(f"[green]✅ Recovery successful for {error_type}[/green]")
                return True
            except Exception as recovery_error:
                console.print(f"[red]❌ Recovery failed for {error_type}: {recovery_error}[/red]")
                return False
        else:
            console.print(f"[yellow]⚠️ No recovery strategy for {error_type}[/yellow]")
            return False

# Global instance for easy access
robust_ops = RobustOperationManager()

# Convenience decorators
def with_retry(operation_name: str = "operation", **kwargs):
    """Convenience decorator for retry logic."""
    return robust_ops.with_retry(operation_name=operation_name, **kwargs)

def with_fallback(fallback_func: Callable, operation_name: str = "operation"):
    """Convenience decorator for fallback logic."""
    return robust_ops.with_fallback(fallback_func, operation_name)

def circuit_breaker(operation_name: str = "operation", **kwargs):
    """Convenience decorator for circuit breaker pattern."""
    return robust_ops.circuit_breaker(operation_name=operation_name, **kwargs)

def safe_execute(func: Callable, *args, **kwargs):
    """Convenience function for safe execution."""
    return robust_ops.safe_execute(func, *args, **kwargs)


class SystemHealthMonitor:
    """
    Monitors system health and provides recovery recommendations.
    """

    def __init__(self):
        """Initialize the health monitor."""
        self.health_checks = {}
        self.health_history = []
        self.alerts = []

    def register_health_check(self, name: str, check_func: Callable, critical: bool = False):
        """
        Register a health check function.

        Args:
            name: Name of the health check
            check_func: Function that returns True if healthy, False otherwise
            critical: Whether this check is critical for system operation
        """
        self.health_checks[name] = {
            "func": check_func,
            "critical": critical,
            "last_check": None,
            "last_result": None,
            "failure_count": 0
        }
        console.print(f"[cyan]📋 Registered health check: {name} (critical: {critical})[/cyan]")

    def run_health_checks(self) -> Dict:
        """
        Run all registered health checks.

        Returns:
            Dictionary with health check results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy",
            "checks": {},
            "critical_failures": [],
            "warnings": []
        }

        for name, check_info in self.health_checks.items():
            try:
                is_healthy = check_info["func"]()
                check_info["last_check"] = datetime.now()
                check_info["last_result"] = is_healthy

                if is_healthy:
                    check_info["failure_count"] = 0
                    status = "healthy"
                else:
                    check_info["failure_count"] += 1
                    status = "unhealthy"

                    if check_info["critical"]:
                        results["critical_failures"].append(name)
                        results["overall_health"] = "critical"
                    else:
                        results["warnings"].append(name)
                        if results["overall_health"] == "healthy":
                            results["overall_health"] = "warning"

                results["checks"][name] = {
                    "status": status,
                    "critical": check_info["critical"],
                    "failure_count": check_info["failure_count"]
                }

            except Exception as e:
                console.print(f"[red]❌ Health check {name} failed with error: {e}[/red]")
                check_info["failure_count"] += 1
                results["checks"][name] = {
                    "status": "error",
                    "critical": check_info["critical"],
                    "failure_count": check_info["failure_count"],
                    "error": str(e)
                }

                if check_info["critical"]:
                    results["critical_failures"].append(name)
                    results["overall_health"] = "critical"

        # Store in history
        self.health_history.append(results)
        if len(self.health_history) > 100:  # Keep last 100 checks
            self.health_history = self.health_history[-100:]

        return results

    def get_health_summary(self) -> Dict:
        """Get a summary of system health."""
        if not self.health_history:
            return {"status": "unknown", "message": "No health checks run yet"}

        latest = self.health_history[-1]

        summary = {
            "current_status": latest["overall_health"],
            "last_check": latest["timestamp"],
            "total_checks": len(latest["checks"]),
            "healthy_checks": len([c for c in latest["checks"].values() if c["status"] == "healthy"]),
            "critical_failures": latest["critical_failures"],
            "warnings": latest["warnings"]
        }

        # Calculate uptime percentage over last 24 hours
        recent_checks = [
            h for h in self.health_history
            if (datetime.now() - datetime.fromisoformat(h["timestamp"])).total_seconds() < 86400
        ]

        if recent_checks:
            healthy_count = len([h for h in recent_checks if h["overall_health"] == "healthy"])
            summary["uptime_24h"] = (healthy_count / len(recent_checks)) * 100
        else:
            summary["uptime_24h"] = 0

        return summary


# Global health monitor instance
health_monitor = SystemHealthMonitor()

# Common health check functions
def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        from job_database import get_job_db
        db = get_job_db("health_check")
        # Try a simple query
        _ = db.get_job_stats()  # Just check if it works
        return True
    except Exception:
        return False

def check_disk_space() -> bool:
    """Check if sufficient disk space is available."""
    try:
        import shutil
        _, _, free = shutil.disk_usage(".")
        free_gb = free / (1024**3)
        return free_gb > 1.0  # At least 1GB free
    except Exception:
        return False

def check_memory_usage() -> bool:
    """Check if memory usage is reasonable."""
    try:
        # Try to import psutil, but don't fail if not available
        import psutil
        memory = psutil.virtual_memory()
        return memory.percent < 90  # Less than 90% memory usage
    except ImportError:
        return True  # If psutil not available, assume OK
    except Exception:
        return True  # If any other error, assume OK

# Register default health checks
health_monitor.register_health_check("database_connection", check_database_connection, critical=True)
health_monitor.register_health_check("disk_space", check_disk_space, critical=True)
health_monitor.register_health_check("memory_usage", check_memory_usage, critical=False)

def get_error_tolerance_handler() -> RobustOperationManager:
    """Get an error tolerance handler instance."""
    return RobustOperationManager()

# Backward compatibility alias
ErrorToleranceHandler = RobustOperationManager
