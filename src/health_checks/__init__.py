"""
Health Checks Package
Provides system health monitoring and diagnostics for AutoJobAgent.
"""

from typing import Dict

# Import shared utilities
from .health_utils import (
    HealthCheckResult,
    HEALTH_STATUS,
    DEFAULT_THRESHOLDS,
    check_memory_usage,
    check_disk_space,
    check_cpu_usage,
    check_network_connectivity,
    check_dependencies,
    check_browser_processes,
    check_file_permissions,
    check_ollama_service,
    display_health_results,
    save_health_report,
)

# Import individual health check modules
from .memory import check_memory, check_memory_usage
from .disk import check_disk, check_disk_space
from .network import check_network, check_network_connectivity
from .browser import check_browser, check_browser_processes
from .permissions import check_permissions, check_file_permissions
from .ollama import check_ollama, check_ollama_service
from .dependencies import check_dependencies

# Export main functions
__all__ = [
    # Shared utilities
    "HealthCheckResult",
    "HEALTH_STATUS",
    "DEFAULT_THRESHOLDS",
    "check_memory_usage",
    "check_disk_space",
    "check_cpu_usage",
    "check_network_connectivity",
    "check_dependencies",
    "check_browser_processes",
    "check_file_permissions",
    "check_ollama_service",
    "display_health_results",
    "save_health_report",
    # Individual health checks (backward compatibility)
    "check_memory",
    "check_disk",
    "check_network",
    "check_browser",
    "check_permissions",
    "check_ollama",
]

