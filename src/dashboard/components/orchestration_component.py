"""
Deprecated orchestration component module.
This module exists for backward compatibility only.
Use `src.dashboard.components.orchestration_ui` instead.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "src.dashboard.components.orchestration_component is deprecated; use orchestration_ui instead",
    DeprecationWarning,
    stacklevel=2,
)

from .orchestration_ui import (
    render_orchestration_control,
    ImprovedOrchestrationComponent,
)

__all__ = [
    "render_orchestration_control",
    "ImprovedOrchestrationComponent",
]
