#!/usr/bin/env python3
"""
Core Metrics Module
Handles system metrics and performance monitoring.
"""

import psutil
import logging
from datetime import datetime
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

# Import services if available
try:
    from src.dashboard.services.system_service import get_system_service
    HAS_SYSTEM_SERVICE = True
except ImportError:
    HAS_SYSTEM_SERVICE = False
    get_system_service = None


def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics using SystemService or fallback."""
    try:
        if HAS_SYSTEM_SERVICE and get_system_service:
            system_service = get_system_service()
            return system_service.get_service_health()
        else:
            return get_basic_system_metrics()
            
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return get_basic_system_metrics()


def get_basic_system_metrics() -> Dict[str, Any]:
    """Basic system metrics fallback."""
    try:
        disk_path = '/' if os.name != 'nt' else 'C:\\'
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage(disk_path).percent,
            "timestamp": datetime.now().isoformat(),
            "network_status": "unknown",
            "services": {},
            "orchestration": {}
        }
        return metrics
    except Exception as e:
        logger.error(f"Failed to get basic system metrics: {e}")
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_usage": 0,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
