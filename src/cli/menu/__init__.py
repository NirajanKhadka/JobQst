"""
CLI Menu module.

Contains menu system for interactive CLI operations:
- Main menu
- Scraping menu
- Application menu
- System menu
"""

from .main_menu import MainMenu
from .scraping_menu import ScrapingMenu
from .application_menu import ApplicationMenu
from .system_menu import SystemMenu

__all__ = ["MainMenu", "ScrapingMenu", "ApplicationMenu", "SystemMenu"]
