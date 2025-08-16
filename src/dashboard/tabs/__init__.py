#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Tabs Module
Improved tab modules with Configurable workflows, caching, and auto-healing capabilities.
"""

# Phase 2: Improved Tab Modules
from .optimized_jobs_tab import render_optimized_jobs_tab, render_jobs_tab
from .cached_analytics_tab import render_cached_analytics_tab, render_analytics_tab
from .resilient_system_tab import render_resilient_system_tab, render_system_tab
from .Automated_orchestration_tab import (
    render_Automated_orchestration_tab, 
    render_orchestration_tab
)

# Legacy tab imports for compatibility
try:
    from .jobs_tab import render_jobs_tab as legacy_render_jobs_tab
    from .analytics_tab import render_analytics_tab as legacy_render_analytics_tab
    from .system_tab import render_system_tab as legacy_render_system_tab
except ImportError:
    # Fallback to Improved versions if legacy not available
    legacy_render_jobs_tab = render_jobs_tab
    legacy_render_analytics_tab = render_analytics_tab
    legacy_render_system_tab = render_system_tab

__all__ = [
    # Improved Phase 2 modules
    'render_optimized_jobs_tab',
    'render_cached_analytics_tab', 
    'render_resilient_system_tab',
    'render_Automated_orchestration_tab',
    
    # Compatibility functions
    'render_jobs_tab',
    'render_analytics_tab',
    'render_system_tab',
    'render_orchestration_tab',
    
    # Legacy fallbacks
    'legacy_render_jobs_tab',
    'legacy_render_analytics_tab',
    'legacy_render_system_tab'
]
