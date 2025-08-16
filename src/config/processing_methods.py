#!/usr/bin/env python3
"""Standardized Processing Method Definitions."""

from enum import Enum
from typing import Dict, Any


class ProcessingMethod(Enum):
    """Standardized processing method enumeration."""
    CPU_ONLY = "cpu_only"
    GPU_ACCELERATED = "gpu_accelerated"
    TWO_STAGE = "two_stage"  # CPU Stage 1 + GPU Stage 2 (recommended)
    AUTO = "auto"  # Auto-detect best method
    
    @classmethod
    def get_display_name(cls, method: 'ProcessingMethod') -> str:
        """Get user-friendly display name."""
        display_names = {
            cls.CPU_ONLY: "CPU Only",
            cls.GPU_ACCELERATED: "GPU Accelerated", 
            cls.TWO_STAGE: "Two-Stage (CPU + GPU)",
            cls.AUTO: "Auto-Detect"
        }
        return display_names.get(method, method.value)
    
    @classmethod
    def from_legacy_name(cls, legacy_name: str) -> 'ProcessingMethod':
        """Convert legacy processing method names."""
        legacy_mapping = {
            "cpu": cls.CPU_ONLY,
            "cpu_only": cls.CPU_ONLY,
            "gpu": cls.GPU_ACCELERATED,
            "gpu_accelerated": cls.GPU_ACCELERATED,
            "hybrid": cls.TWO_STAGE,
            "two_stage": cls.TWO_STAGE,
            "auto": cls.AUTO,
            "rule_based": cls.CPU_ONLY,
        }
        return legacy_mapping.get(legacy_name.lower(), cls.AUTO)


def get_processing_config(method: ProcessingMethod) -> Dict[str, Any]:
    """Get configuration for a processing method."""
    configs = {
        ProcessingMethod.CPU_ONLY: {
            "enable_gpu": False,
            "cpu_workers": 10,
            "stage2_enabled": False,
            "description": "Fast CPU-only processing"
        },
        ProcessingMethod.GPU_ACCELERATED: {
            "enable_gpu": True,
            "cpu_workers": 4,
            "stage2_enabled": True,
            "max_concurrent_stage2": 4,
            "description": "GPU-accelerated processing"
        },
        ProcessingMethod.TWO_STAGE: {
            "enable_gpu": True,
            "cpu_workers": 10,
            "stage2_enabled": True, 
            "max_concurrent_stage2": 2,
            "description": "Two-stage: CPU filtering + GPU analysis"
        },
        ProcessingMethod.AUTO: {
            "enable_gpu": "auto_detect",
            "cpu_workers": 10,
            "stage2_enabled": "auto_detect",
            "max_concurrent_stage2": 2,
            "description": "Auto-select best method"
        }
    }
    return configs.get(method, configs[ProcessingMethod.AUTO])
