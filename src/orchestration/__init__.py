"""
Orchestration package: centralizes job discovery (JobSpy), processing (Two-Stage),
worker pool control, and dashboard-facing orchestration APIs.

This provides a clean, typed interface that the dashboard and CLI can import
without reaching into component internals.
"""

from .jobspy_controller import run_jobspy_discovery
from .processing_controller import run_processing_batches
from .types import OrchestratorConfig, DiscoveryResult

__all__ = [
    "run_jobspy_discovery",
    "run_processing_batches",
    "OrchestratorConfig",
    "DiscoveryResult",
]
