# Callbacks package for Dash dashboard

# Import all callback modules
from src.dashboard.dash_app.callbacks import jobs_callbacks
from src.dashboard.dash_app.callbacks import analytics_callbacks
from src.dashboard.dash_app.callbacks import processing_callbacks
from src.dashboard.dash_app.callbacks import system_callbacks
from src.dashboard.dash_app.callbacks import settings_callbacks

__all__ = [
    "jobs_callbacks",
    "analytics_callbacks",
    "processing_callbacks",
    "system_callbacks",
    "settings_callbacks",
]
