"""
Dashboard components module for the AutoJobAgent Dashboard.

This module exports all dashboard UI components including base classes,
specialized components, and utility functions for building dashboard interfaces.
"""

from .base import BaseComponent, ContainerComponent, CachedComponent, ComponentError
from .header import render_header
from .sidebar import render_sidebar
from .metrics import render_metrics, _calculate_job_metrics
from .job_table import render_job_table, get_available_columns
from .charts import render_charts, get_chart_data_summary

# Conditional imports for optional components
try:
    from .cli_component import CLIComponent
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False

try:
    from .orchestration_component import OrchestrationComponent
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False

try:
    from .metrics_component import MetricsComponent
    METRICS_COMPONENT_AVAILABLE = True
except ImportError:
    METRICS_COMPONENT_AVAILABLE = False

try:
    from .header_component import HeaderComponent
    HEADER_COMPONENT_AVAILABLE = True
except ImportError:
    HEADER_COMPONENT_AVAILABLE = False

# Base exports (always available)
__all__ = [
    # Base classes
    'BaseComponent',
    'ContainerComponent', 
    'CachedComponent',
    'ComponentError',
    
    # Render functions
    'render_header',
    'render_sidebar',
    'render_metrics',
    'render_job_table',
    'render_charts',
    
    # Utility functions
    'get_available_columns',
    'get_chart_data_summary',
]

# Add optional exports if available
if CLI_AVAILABLE:
    __all__.append('CLIComponent')

if ORCHESTRATION_AVAILABLE:
    __all__.append('OrchestrationComponent')

if METRICS_COMPONENT_AVAILABLE:
    __all__.append('MetricsComponent')

if HEADER_COMPONENT_AVAILABLE:
    __all__.append('HeaderComponent')

# Availability flags for feature detection
FEATURE_FLAGS = {
    'cli_component': CLI_AVAILABLE,
    'orchestration_component': ORCHESTRATION_AVAILABLE,
    'metrics_component': METRICS_COMPONENT_AVAILABLE,
    'header_component': HEADER_COMPONENT_AVAILABLE,
}
