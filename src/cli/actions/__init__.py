"""
CLI Actions module.

Contains action processors for different CLI operations:
- Scraping actions
- Application actions
- Dashboard actions
- System actions
"""

from .scraping_actions import ScrapingActions
from .application_actions import ApplicationActions
from .dashboard_actions import DashboardActions
from .system_actions import SystemActions

__all__ = ["ScrapingActions", "ApplicationActions", "DashboardActions", "SystemActions"]
