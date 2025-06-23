"""
Browser utilities for web scraping and automation.
"""

import time
import random
from typing import Optional, List, Dict, Any, Union
from playwright.sync_api import Page, Browser, BrowserContext


class BrowserUtils:
    """Utility functions for browser automation."""
    
    @staticmethod
    def wait_for_page_load(page: Page, timeout: int = 30):
        """Wait for page to fully load."""
        try:
            page.wait_for_load_state('networkidle', timeout=timeout * 1000)
        except Exception:
            # Fallback to basic load state
            page.wait_for_load_state('domcontentloaded', timeout=timeout * 1000)
    
    @staticmethod
    def random_delay(min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay to simulate human behavior."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    @staticmethod
    def scroll_page(page: Page, scroll_pause: float = 1.0):
        """Scroll the page to load dynamic content."""
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(scroll_pause)
        
        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(scroll_pause)
    
    @staticmethod
    def wait_for_element(page: Page, selector: str, timeout: int = 10) -> bool:
        """Wait for an element to appear on the page."""
        try:
            page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except Exception:
            return False
    
    @staticmethod
    def click_element_safely(page: Page, selector: str, timeout: int = 10) -> bool:
        """Safely click an element with error handling."""
        try:
            if page.wait_for_selector(selector, timeout=timeout * 1000):
                page.click(selector)
                return True
        except Exception:
            pass
        return False
    
    @staticmethod
    def fill_input_safely(page: Page, selector: str, value: str, timeout: int = 10) -> bool:
        """Safely fill an input field with error handling."""
        try:
            if page.wait_for_selector(selector, timeout=timeout * 1000):
                page.fill(selector, value)
                return True
        except Exception:
            pass
        return False
    
    @staticmethod
    def get_text_safely(page: Page, selector: str, default: str = "") -> str:
        """Safely get text from an element."""
        try:
            element = page.query_selector(selector)
            if element:
                return element.text_content() or default
        except Exception:
            pass
        return default
    
    @staticmethod
    def get_attribute_safely(page: Page, selector: str, attribute: str, default: str = "") -> str:
        """Safely get attribute value from an element."""
        try:
            element = page.query_selector(selector)
            if element:
                return element.get_attribute(attribute) or default
        except Exception:
            pass
        return default


class TabManager:
    """Manages browser tabs for multi-tab operations."""
    
    def __init__(self, context: BrowserContext):
        self.context = context
        self.pages: List[Page] = []
        self.active_page: Optional[Page] = None
    
    def create_new_tab(self) -> Page:
        """Create a new tab and return the page."""
        page = self.context.new_page()
        self.pages.append(page)
        self.active_page = page
        return page
    
    def switch_to_tab(self, index: int) -> Optional[Page]:
        """Switch to a specific tab by index."""
        if 0 <= index < len(self.pages):
            self.active_page = self.pages[index]
            return self.active_page
        return None
    
    def close_tab(self, index: int) -> bool:
        """Close a specific tab by index."""
        if 0 <= index < len(self.pages):
            try:
                self.pages[index].close()
                self.pages.pop(index)
                if self.pages:
                    self.active_page = self.pages[-1]
                else:
                    self.active_page = None
                return True
            except Exception:
                pass
        return False
    
    def close_all_tabs(self):
        """Close all tabs except the first one."""
        while len(self.pages) > 1:
            self.close_tab(1)
    
    def get_active_page(self) -> Optional[Page]:
        """Get the currently active page."""
        return self.active_page
    
    def get_page_count(self) -> int:
        """Get the number of open pages."""
        return len(self.pages)


class PopupHandler:
    """Handles popup windows and dialogs."""
    
    def __init__(self, context: BrowserContext):
        self.context = context
    
    def wait_for_popup(self, timeout: int = 10) -> Optional[Page]:
        """Wait for a popup window to open."""
        try:
            page = self.context.wait_for_event('page', timeout=timeout * 1000)
            return page
        except Exception:
            return None
    
    def handle_alert(self, page: Page, accept: bool = True):
        """Handle JavaScript alerts."""
        if accept:
            page.on('dialog', lambda dialog: dialog.accept())
        else:
            page.on('dialog', lambda dialog: dialog.dismiss())
    
    def close_popup(self, page: Page):
        """Close a popup window."""
        try:
            page.close()
        except Exception:
            pass


class NavigationUtils:
    """Utilities for page navigation."""
    
    @staticmethod
    def navigate_with_retry(page: Page, url: str, max_retries: int = 3) -> bool:
        """Navigate to URL with retry logic."""
        for attempt in range(max_retries):
            try:
                page.goto(url, wait_until='domcontentloaded')
                return True
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        return False
    
    @staticmethod
    def wait_for_navigation(page: Page, timeout: int = 30):
        """Wait for navigation to complete."""
        try:
            page.wait_for_load_state('networkidle', timeout=timeout * 1000)
        except Exception:
            page.wait_for_load_state('domcontentloaded', timeout=timeout * 1000)
    
    @staticmethod
    def get_current_url(page: Page) -> str:
        """Get the current URL of the page."""
        return page.url
    
    @staticmethod
    def go_back(page: Page):
        """Go back to the previous page."""
        page.go_back()
    
    @staticmethod
    def go_forward(page: Page):
        """Go forward to the next page."""
        page.go_forward()
    
    @staticmethod
    def refresh_page(page: Page):
        """Refresh the current page."""
        page.reload()


class FormUtils:
    """Utilities for form handling."""
    
    @staticmethod
    def fill_form(page: Page, form_data: Dict[str, str]) -> bool:
        """Fill a form with provided data."""
        try:
            for field_name, value in form_data.items():
                selector = f'[name="{field_name}"], [id="{field_name}"], [data-field="{field_name}"]'
                if not BrowserUtils.fill_input_safely(page, selector, value):
                    return False
            return True
        except Exception:
            return False
    
    @staticmethod
    def submit_form(page: Page, submit_selector: str = 'input[type="submit"], button[type="submit"]') -> bool:
        """Submit a form."""
        return BrowserUtils.click_element_safely(page, submit_selector)
    
    @staticmethod
    def clear_form(page: Page, form_selector: str = 'form'):
        """Clear all form fields."""
        try:
            page.evaluate(f"""
                document.querySelector('{form_selector}').reset();
            """)
        except Exception:
            pass


def create_browser_utils() -> BrowserUtils:
    """Create a browser utils instance."""
    return BrowserUtils()


def create_tab_manager(context: BrowserContext) -> TabManager:
    """Create a tab manager for the given context."""
    return TabManager(context)


def create_popup_handler(context: BrowserContext) -> PopupHandler:
    """Create a popup handler for the given context."""
    return PopupHandler(context) 