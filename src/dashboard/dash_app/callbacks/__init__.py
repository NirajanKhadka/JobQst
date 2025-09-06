# Callbacks package for Dash dashboard

# Import all callback modules
from . import jobs_callbacks
from . import analytics_callbacks
from . import processing_callbacks
from . import system_callbacks
from . import settings_callbacks

__all__ = ['jobs_callbacks', 'analytics_callbacks', 'processing_callbacks', 'system_callbacks', 'settings_callbacks']
