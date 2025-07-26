"""
CLI Menu module.

Contains menu system for interactive CLI operations:
- Main menu
- Scraping menu
- Application menu
- System menu
"""

from .application_menu import ApplicationMenu
from .system_menu import SystemMenu

__all__ = ["ApplicationMenu", "SystemMenu"]
