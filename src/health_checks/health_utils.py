"""
Health Check Utilities
Shared utilities for system health monitoring and diagnostics.
"""

import os
import sys
import json
import psutil
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Health status constants
HEALTH_STATUS = {
    "HEALTHY": "healthy",
    "WARNING": "warning",
    "CRITICAL": "critical",
    "ERROR": "error",
}

# Default thresholds
DEFAULT_THRESHOLDS = {
    "critical_memory_usage_percent": 85,
    "warning_memory_usage_percent": 75,
    "critical_disk_usage_percent": 90,
    "warning_disk_usage_percent": 80,
    "critical_cpu_usage_percent": 90,
    "warning_cpu_usage_percent": 80,
    "browser_process_limit": 20,
    "network_timeout_seconds": 5,
}

# Critical Python dependencies
CRITICAL_DEPENDENCIES = [
    "playwright",
    "requests",
    "rich",
    "beautifulsoup4",
    "python-docx",
    "pandas",
    "psutil",
    "asyncio",
]

# Network test URLs
NETWORK_TEST_URLS = ["https://www.google.com", "https://github.com", "https://www.cloudflare.com"]


class HealthCheckResult:
    """Standardized health check result container."""

    def __init__(self, status: str, message: str, details: Optional[Dict] = None):
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }

    def is_healthy(self) -> bool:
        """Check if result indicates healthy status."""
        return self.status == HEALTH_STATUS["HEALTHY"]

    def is_critical(self) -> bool:
        """Check if result indicates critical status."""
        return self.status == HEALTH_STATUS["CRITICAL"]


def check_memory_usage(config: Dict) -> HealthCheckResult:
    """
    Check system memory usage.

    Args:
        config: Configuration dictionary with thresholds

    Returns:
        HealthCheckResult with memory status
    """
    try:
        memory = psutil.virtual_memory()
        used_percent = memory.percent
        available_gb = memory.available / (1024**3)
        total_gb = memory.total / (1024**3)

        critical_threshold = config.get(
            "critical_memory_usage_percent", DEFAULT_THRESHOLDS["critical_memory_usage_percent"]
        )
        warning_threshold = config.get(
            "warning_memory_usage_percent", DEFAULT_THRESHOLDS["warning_memory_usage_percent"]
        )

        details = {
            "used_percent": used_percent,
            "available_gb": round(available_gb, 2),
            "total_gb": round(total_gb, 2),
            "critical_threshold": critical_threshold,
            "warning_threshold": warning_threshold,
        }

        if used_percent > critical_threshold:
            return HealthCheckResult(
                HEALTH_STATUS["CRITICAL"],
                f"Memory usage critical: {used_percent:.1f}% used, {available_gb:.1f}GB available",
                details,
            )
        elif used_percent > warning_threshold:
            return HealthCheckResult(
                HEALTH_STATUS["WARNING"],
                f"Memory usage high: {used_percent:.1f}% used, {available_gb:.1f}GB available",
                details,
            )
        else:
            return HealthCheckResult(
                HEALTH_STATUS["HEALTHY"],
                f"Memory usage normal: {used_percent:.1f}% used, {available_gb:.1f}GB available",
                details,
            )

    except Exception as e:
        return HealthCheckResult(HEALTH_STATUS["ERROR"], f"Memory check failed: {str(e)}")


def check_disk_space(config: Dict) -> HealthCheckResult:
    """
    Check available disk space.

    Args:
        config: Configuration dictionary with thresholds

    Returns:
        HealthCheckResult with disk status
    """
    try:
        disk_usage = psutil.disk_usage(".")
        used_percent = (disk_usage.used / disk_usage.total) * 100
        free_gb = disk_usage.free / (1024**3)
        total_gb = disk_usage.total / (1024**3)

        critical_threshold = config.get(
            "critical_disk_usage_percent", DEFAULT_THRESHOLDS["critical_disk_usage_percent"]
        )
        warning_threshold = config.get(
            "warning_disk_usage_percent", DEFAULT_THRESHOLDS["warning_disk_usage_percent"]
        )

        details = {
            "used_percent": used_percent,
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "critical_threshold": critical_threshold,
            "warning_threshold": warning_threshold,
        }

        if used_percent > critical_threshold:
            return HealthCheckResult(
                HEALTH_STATUS["CRITICAL"],
                f"Disk usage critical: {used_percent:.1f}% used, {free_gb:.1f}GB free",
                details,
            )
        elif used_percent > warning_threshold:
            return HealthCheckResult(
                HEALTH_STATUS["WARNING"],
                f"Disk usage high: {used_percent:.1f}% used, {free_gb:.1f}GB free",
                details,
            )
        else:
            return HealthCheckResult(
                HEALTH_STATUS["HEALTHY"],
                f"Disk usage normal: {used_percent:.1f}% used, {free_gb:.1f}GB free",
                details,
            )

    except Exception as e:
        return HealthCheckResult(HEALTH_STATUS["ERROR"], f"Disk check failed: {str(e)}")


def check_cpu_usage(config: Dict) -> HealthCheckResult:
    """
    Check CPU usage.

    Args:
        config: Configuration dictionary with thresholds

    Returns:
        HealthCheckResult with CPU status
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()

        critical_threshold = config.get(
            "critical_cpu_usage_percent", DEFAULT_THRESHOLDS["critical_cpu_usage_percent"]
        )
        warning_threshold = config.get(
            "warning_cpu_usage_percent", DEFAULT_THRESHOLDS["warning_cpu_usage_percent"]
        )

        details = {
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count,
            "critical_threshold": critical_threshold,
            "warning_threshold": warning_threshold,
        }

        if cpu_percent > critical_threshold:
            return HealthCheckResult(
                HEALTH_STATUS["CRITICAL"], f"CPU usage critical: {cpu_percent:.1f}%", details
            )
        elif cpu_percent > warning_threshold:
            return HealthCheckResult(
                HEALTH_STATUS["WARNING"], f"CPU usage high: {cpu_percent:.1f}%", details
            )
        else:
            return HealthCheckResult(
                HEALTH_STATUS["HEALTHY"], f"CPU usage normal: {cpu_percent:.1f}%", details
            )

    except Exception as e:
        return HealthCheckResult(HEALTH_STATUS["ERROR"], f"CPU check failed: {str(e)}")


def check_network_connectivity(config: Dict) -> HealthCheckResult:
    """
    Check network connectivity.

    Args:
        config: Configuration dictionary with test URLs and timeout

    Returns:
        HealthCheckResult with network status
    """
    try:
        test_urls = config.get("test_urls", NETWORK_TEST_URLS)
        timeout = config.get(
            "network_timeout_seconds", DEFAULT_THRESHOLDS["network_timeout_seconds"]
        )
        successful_connections = 0
        failed_urls = []

        for url in test_urls:
            try:
                response = requests.head(url, timeout=timeout)
                if response.status_code < 400:
                    successful_connections += 1
                else:
                    failed_urls.append(f"{url} (HTTP {response.status_code})")
            except Exception as e:
                failed_urls.append(f"{url} ({str(e)})")

        details = {
            "tested_urls": len(test_urls),
            "successful_connections": successful_connections,
            "failed_urls": failed_urls,
            "timeout_seconds": timeout,
        }

        if successful_connections == 0:
            return HealthCheckResult(HEALTH_STATUS["CRITICAL"], "No network connectivity", details)
        elif successful_connections < len(test_urls):
            return HealthCheckResult(
                HEALTH_STATUS["WARNING"],
                f"Limited network connectivity: {successful_connections}/{len(test_urls)} URLs reachable",
                details,
            )
        else:
            return HealthCheckResult(
                HEALTH_STATUS["HEALTHY"], "Network connectivity normal", details
            )

    except Exception as e:
        return HealthCheckResult(HEALTH_STATUS["ERROR"], f"Network check failed: {str(e)}")


def check_dependencies(config: Dict) -> HealthCheckResult:
    """
    Check critical Python dependencies.

    Args:
        config: Configuration dictionary with dependency list

    Returns:
        HealthCheckResult with dependency status
    """
    try:
        critical_modules = config.get("critical_modules", CRITICAL_DEPENDENCIES)
        missing_modules = []
        available_modules = []

        for module in critical_modules:
            try:
                __import__(module.replace("-", "_"))
                available_modules.append(module)
            except ImportError:
                missing_modules.append(module)

        details = {
            "total_modules": len(critical_modules),
            "available_modules": available_modules,
            "missing_modules": missing_modules,
        }

        if missing_modules:
            return HealthCheckResult(
                HEALTH_STATUS["CRITICAL"],
                f"Missing dependencies: {', '.join(missing_modules)}",
                details,
            )
        else:
            return HealthCheckResult(
                HEALTH_STATUS["HEALTHY"], "All dependencies available", details
            )

    except Exception as e:
        return HealthCheckResult(HEALTH_STATUS["ERROR"], f"Dependency check failed: {str(e)}")


def check_browser_processes(config: Dict) -> HealthCheckResult:
    """
    Check for zombie browser processes.

    Args:
        config: Configuration dictionary with process limits

    Returns:
        HealthCheckResult with browser process status
    """
    try:
        browser_processes = []
        browser_names = ["chrome", "firefox", "edge", "opera", "chromium"]

        for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
            try:
                proc_name = proc.info["name"].lower()
                if any(browser in proc_name for browser in browser_names):
                    browser_processes.append(
                        {
                            "pid": proc.info["pid"],
                            "name": proc.info["name"],
                            "memory_mb": round(proc.info["memory_info"].rss / (1024**2), 2),
                            "cpu_percent": proc.info["cpu_percent"],
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        process_limit = config.get(
            "browser_process_limit", DEFAULT_THRESHOLDS["browser_process_limit"]
        )

        details = {
            "browser_processes": browser_processes,
            "process_count": len(browser_processes),
            "process_limit": process_limit,
        }

        if len(browser_processes) > process_limit:
            return HealthCheckResult(
                HEALTH_STATUS["WARNING"],
                f"Many browser processes running: {len(browser_processes)} (limit: {process_limit})",
                details,
            )
        else:
            return HealthCheckResult(
                HEALTH_STATUS["HEALTHY"],
                f"Browser processes normal: {len(browser_processes)} running",
                details,
            )

    except Exception as e:
        return HealthCheckResult(HEALTH_STATUS["ERROR"], f"Browser process check failed: {str(e)}")


def check_file_permissions(config: Dict) -> HealthCheckResult:
    """
    Check file permissions for critical directories and files.

    Args:
        config: Configuration dictionary with paths to check

    Returns:
        HealthCheckResult with permission status
    """
    try:
        paths_to_check = config.get(
            "paths_to_check", [".", "src", "data", "output", "logs"]  # Current directory
        )

        permission_issues = []
        accessible_paths = []

        for path_str in paths_to_check:
            path = Path(path_str)
            try:
                # Check if path exists and is accessible
                if path.exists():
                    # Check read permission
                    if os.access(path, os.R_OK):
                        accessible_paths.append(f"{path_str} (readable)")
                    else:
                        permission_issues.append(f"{path_str} (not readable)")

                    # Check write permission for directories
                    if path.is_dir() and os.access(path, os.W_OK):
                        accessible_paths.append(f"{path_str} (writable)")
                    elif path.is_dir():
                        permission_issues.append(f"{path_str} (not writable)")
                else:
                    permission_issues.append(f"{path_str} (does not exist)")

            except Exception as e:
                permission_issues.append(f"{path_str} (error: {str(e)})")

        details = {
            "paths_checked": len(paths_to_check),
            "accessible_paths": accessible_paths,
            "permission_issues": permission_issues,
        }

        if permission_issues:
            return HealthCheckResult(
                HEALTH_STATUS["WARNING"],
                f"Permission issues found: {len(permission_issues)} problems",
                details,
            )
        else:
            return HealthCheckResult(
                HEALTH_STATUS["HEALTHY"],
                f"All paths accessible: {len(accessible_paths)} paths checked",
                details,
            )

    except Exception as e:
        return HealthCheckResult(HEALTH_STATUS["ERROR"], f"Permission check failed: {str(e)}")


def check_ollama_service(config: Dict) -> HealthCheckResult:
    """
    Check if Ollama service is running and accessible.

    Args:
        config: Configuration dictionary with Ollama settings

    Returns:
        HealthCheckResult with Ollama status
    """
    try:
        ollama_url = config.get("ollama_url", "http://localhost:11434")
        timeout = config.get("ollama_timeout", 5)

        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=timeout)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return HealthCheckResult(
                    HEALTH_STATUS["HEALTHY"],
                    f"Ollama service running with {len(models)} models",
                    {"models": [m.get("name", "unknown") for m in models]},
                )
            else:
                return HealthCheckResult(
                    HEALTH_STATUS["WARNING"],
                    f"Ollama service responding but with status {response.status_code}",
                    {"status_code": response.status_code},
                )
        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                HEALTH_STATUS["CRITICAL"],
                "Ollama service not accessible",
                {"ollama_url": ollama_url},
            )
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                HEALTH_STATUS["WARNING"],
                "Ollama service timeout",
                {"ollama_url": ollama_url, "timeout": timeout},
            )

    except Exception as e:
        return HealthCheckResult(HEALTH_STATUS["ERROR"], f"Ollama check failed: {str(e)}")


def display_health_results(results: Dict[str, HealthCheckResult]) -> None:
    """
    Display health check results in a formatted table.

    Args:
        results: Dictionary of health check results
    """
    table = Table(title="System Health Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Message", style="white")
    table.add_column("Details", style="dim")

    for component, result in results.items():
        status = result.status
        message = result.message
        details = str(result.details) if result.details else ""

        status_colors = {
            HEALTH_STATUS["HEALTHY"]: "green",
            HEALTH_STATUS["WARNING"]: "yellow",
            HEALTH_STATUS["CRITICAL"]: "red",
            HEALTH_STATUS["ERROR"]: "red",
        }
        status_display = f"[{status_colors.get(status, 'gray')}]{status.upper()}[/]"

        table.add_row(
            component.title(),
            status_display,
            message,
            details[:50] + "..." if len(details) > 50 else details,
        )

    console.print(table)


def save_health_report(
    results: Dict[str, HealthCheckResult], output_path: Optional[str] = None
) -> str:
    """
    Save health check results to a JSON file.

    Args:
        results: Dictionary of health check results
        output_path: Path to save the report (optional)

    Returns:
        Path to the saved report
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"health_logs/health_report_{timestamp}.json"

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert results to dictionary format
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "results": {component: result.to_dict() for component, result in results.items()},
        "summary": {
            "total_checks": len(results),
            "healthy": len([r for r in results.values() if r.is_healthy()]),
            "warnings": len([r for r in results.values() if r.status == HEALTH_STATUS["WARNING"]]),
            "critical": len([r for r in results.values() if r.is_critical()]),
            "errors": len([r for r in results.values() if r.status == HEALTH_STATUS["ERROR"]]),
        },
    }

    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=2)

    console.print(f"[green]Health report saved to: {output_path}[/green]")
    return output_path
