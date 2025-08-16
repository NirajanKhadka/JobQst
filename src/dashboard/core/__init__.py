#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Dashboard Module
Contains foundational classes for the modularized dashboard architecture.
"""

# Core module exports
from .dashboard_controller import DashboardController
from .auto_healing_service_factory import AutoHealingServiceFactory
from .smart_cache_manager import ConfigurableCacheManager

__all__ = [
    'DashboardController',
    'AutoHealingServiceFactory', 
    'ConfigurableCacheManager'
]
