"""
Browser management for AutoJobAgent.
Handles browser automation with Playwright.
"""
import logging
import os
import time
from pathlib import Path
from typing import Dict, Optional, Union, Literal

from playwright.sync_api import sync_playwright, Browser, BrowserContext, BrowserType

from ...shared.config import settings

logger = logging.getLogger(__name__)

BrowserName = Literal["chromium", "firefox", "webkit", "chrome", "chrome-beta", "msedge"]

class BrowserManager:
    """
    Manages browser instances and contexts for web automation.
    
    This class handles the creation and management of browser instances and contexts
    using Playwright. It supports multiple browsers and provides methods for creating
    persistent and incognito contexts.
    """
    
    def __init__(self, profile_name: str, headless: bool = None):
        """
        Initialize the BrowserManager.
        
        Args:
            profile_name: Name of the user profile
            headless: Whether to run in headless mode (default: from settings)
        """
        self.profile_name = profile_name
        self.headless = headless if headless is not None else settings.HEADLESS
        self._playwright = None
        self._browser = None
        self._browser_type = None
        self._contexts: Dict[str, BrowserContext] = {}
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self):
        """Start the Playwright instance and browser."""
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            
        if self._browser is None:
            self._launch_browser()
    
    def close(self):
        """Close all browser contexts and the browser instance."""
        for context in self._contexts.values():
            try:
                context.close()
            except Exception as e:
                logger.warning(f"Error closing browser context: {e}")
        
        self._contexts.clear()
        
        if self._browser:
            try:
                self._browser.close()
                self._browser = None
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        
        if self._playwright:
            try:
                self._playwright.stop()
                self._playwright = None
            except Exception as e:
                logger.warning(f"Error stopping Playwright: {e}")
    
    def _launch_browser(self):
        """Launch the browser with the specified configuration."""
        browser_name = settings.DEFAULT_BROWSER.lower()
        
        # Map browser names to their respective Playwright launchers
        browser_launchers = {
            "chromium": self._playwright.chromium.launch,
            "firefox": self._playwright.firefox.launch,
            "webkit": self._playwright.webkit.launch,
            "chrome": self._playwright.chromium.launch,
            "chrome-beta": self._playwright.chromium.launch,
            "msedge": self._playwright.chromium.launch,
        }
        
        if browser_name not in browser_launchers:
            logger.warning(f"Unsupported browser: {browser_name}. Defaulting to chromium.")
            browser_name = "chromium"
        
        launch_options = {
            "headless": self.headless,
            "timeout": settings.BROWSER_TIMEOUT,
        }
        
        # Add browser-specific options
        if browser_name in ["chrome", "chrome-beta", "msedge"]:
            channel = {
                "chrome": "chrome",
                "chrome-beta": "chrome-beta",
                "msedge": "msedge"
            }[browser_name]
            launch_options["channel"] = channel
        
        try:
            self._browser = browser_launchers[browser_name](**launch_options)
            self._browser_type = browser_name
            logger.info(f"Launched {browser_name} browser (headless={self.headless})")
        except Exception as e:
            logger.error(f"Failed to launch {browser_name}: {e}")
            raise
    
    def create_context(
        self,
        name: str = "default",
        persistent: bool = True,
        **kwargs
    ) -> BrowserContext:
        """
        Create a new browser context.
        
        Args:
            name: Name for the context (used for persistence)
            persistent: Whether to persist the context (cookies, storage, etc.)
            **kwargs: Additional options for the browser context
            
        Returns:
            The created BrowserContext
        """
        if name in self._contexts:
            logger.warning(f"Context '{name}' already exists. Closing existing context.")
            self._contexts[name].close()
        
        context_options = {
            "viewport": {"width": 1366, "height": 768},
            "ignore_https_errors": True,
            "accept_downloads": True,
            **kwargs
        }
        
        if persistent:
            # Create a persistent context with user data directory
            user_data_dir = settings.PROFILES_DIR / self.profile_name / "browser_data"
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            context_options.update({
                "user_data_dir": str(user_data_dir),
                "no_viewport": True,
                "bypass_csp": True,
            })
            
            # Add browser-specific arguments
            if self._browser_type in ["chrome", "chromium", "msedge"]:
                context_options.setdefault("args", []).extend([
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--disable-notifications",
                    "--disable-popup-blocking",
                    "--disable-web-security",
                    "--disable-extensions",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-software-rasterizer",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-setuid-sandbox",
                    f"--user-data-dir={user_data_dir}",
                ])
        
        context = self._browser.new_context(**context_options)
        
        # Add stealth mode to avoid bot detection
        self._apply_stealth_mode(context)
        
        # Store the context
        self._contexts[name] = context
        logger.debug(f"Created browser context: {name}")
        
        return context
    
    def _apply_stealth_mode(self, context: BrowserContext):
        """
        Apply stealth mode to make the browser appear more like a regular user.
        
        Args:
            context: The browser context to apply stealth mode to
        """
        stealth_js = """
        // Override the `plugins` property to mimic Chrome
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Override the `languages` property
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Override the `webdriver` property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Override the `chrome` property
        window.chrome = {
            runtime: {},
            // Add other Chrome-specific properties as needed
        };
        
        // Mock the `permissions` API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: 'denied' }) :
                originalQuery(parameters)
        );
        
        // Mock the `Notification` API
        window.Notification = {};
        """
        
        context.add_init_script(stealth_js)
    
    def get_context(self, name: str = "default") -> Optional[BrowserContext]:
        """
        Get an existing browser context by name.
        
        Args:
            name: Name of the context to retrieve
            
        Returns:
            The BrowserContext or None if not found
        """
        return self._contexts.get(name)
    
    def close_context(self, name: str):
        """
        Close a browser context by name.
        
        Args:
            name: Name of the context to close
        """
        if name in self._contexts:
            self._contexts[name].close()
            del self._contexts[name]
            logger.debug(f"Closed browser context: {name}")
