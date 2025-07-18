"""
Human Behavior Scraper for AutoJobAgent.

This module provides scraping functionality that mimics human behavior
to avoid detection and improve success rates.
"""

import time
import random
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from rich.console import Console

from src.utils import profile_helpers
from src.core.job_database import get_job_db

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class HumanBehaviorConfig:
    """Configuration for human behavior simulation."""

    min_delay: float = 1.0
    max_delay: float = 3.0
    scroll_delay: float = 0.5
    typing_delay: float = 0.1
    mouse_movement: bool = True
    random_viewport: bool = True
    user_agent_rotation: bool = True

    def __init__(self):
        self.delays = {"popup_wait": 3.0}


class HumanBehaviorMixin:
    """
    Mixin class that provides human behavior simulation methods.

    This mixin can be added to any scraper class to provide
    human-like behavior simulation capabilities.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the human behavior mixin."""
        super().__init__(*args, **kwargs)
        self.human_config = HumanBehaviorConfig()
        self._setup_human_behavior()

    def _setup_human_behavior(self):
        """Setup human behavior configuration."""
        self.min_delay = getattr(self, "min_delay", 1.0)
        self.max_delay = getattr(self, "max_delay", 3.0)
        self.scroll_delay = getattr(self, "scroll_delay", 0.5)
        self.typing_delay = getattr(self, "typing_delay", 0.1)

    def human_delay(
        self, min_delay: Optional[float] = None, max_delay: Optional[float] = None
    ) -> None:
        """
        Add a human-like delay.

        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        min_d = min_delay or self.min_delay
        max_d = max_delay or self.max_delay
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)

    def human_scroll(self, page, distance: Optional[int] = None) -> None:
        """
        Simulate human-like scrolling.

        Args:
            page: Playwright page object
            distance: Scroll distance (random if None)
        """
        try:
            if distance is None:
                distance = random.randint(300, 800)

            page.mouse.wheel(0, distance)
            time.sleep(random.uniform(0.5, 1.5))

            # Sometimes scroll back up
            if random.random() < 0.3:
                page.mouse.wheel(0, -distance // 2)
                time.sleep(random.uniform(0.3, 0.8))

        except Exception as e:
            logger.warning(f"⚠️ Error in human scroll: {e}")

    def human_click(self, page, element, move_mouse: bool = True) -> None:
        """
        Simulate human-like clicking.

        Args:
            page: Playwright page object
            element: Element to click
            move_mouse: Whether to move mouse to element first
        """
        try:
            if move_mouse:
                self._move_mouse_to_element(page, element)

            # Random delay before click
            time.sleep(random.uniform(0.2, 0.8))

            # Click with slight randomness
            element.click()

            # Random delay after click
            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            logger.warning(f"⚠️ Error in human click: {e}")

    def human_type(self, page, selector: str, text: str, clear_first: bool = True) -> None:
        """
        Simulate human-like typing.

        Args:
            page: Playwright page object
            selector: Element selector
            text: Text to type
            clear_first: Whether to clear field first
        """
        try:
            element = page.query_selector(selector)
            if element:
                if clear_first:
                    element.click()
                    element.fill("")

                # Type with random delays between characters
                for char in text:
                    element.type(char)
                    time.sleep(random.uniform(0.05, 0.15))

        except Exception as e:
            logger.warning(f"⚠️ Error in human typing: {e}")

    def human_navigate(self, page, url: str) -> None:
        """
        Simulate human-like navigation.

        Args:
            page: Playwright page object
            url: URL to navigate to
        """
        try:
            # Random delay before navigation
            time.sleep(random.uniform(0.5, 2.0))

            # Navigate to URL
            page.goto(url)

            # Wait for page load with human-like patience
            page.wait_for_load_state("networkidle")
            time.sleep(random.uniform(1.0, 3.0))

        except Exception as e:
            logger.warning(f"⚠️ Error in human navigation: {e}")

    def _move_mouse_to_element(self, page, element) -> None:
        """
        Move mouse to element with human-like movement.

        Args:
            page: Playwright page object
            element: Target element
        """
        try:
            box = element.bounding_box()
            if box:
                # Add slight randomness to target position
                x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
                y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)

                # Move mouse to element
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))

        except Exception as e:
            logger.warning(f"⚠️ Error moving mouse to element: {e}")

    def random_viewport_size(self, page) -> None:
        """
        Set random viewport size to simulate different devices.

        Args:
            page: Playwright page object
        """
        try:
            viewports = [
                (1920, 1080),  # Desktop
                (1366, 768),  # Laptop
                (1440, 900),  # MacBook
                (1536, 864),  # Large laptop
                (1280, 720),  # Small laptop
            ]

            width, height = random.choice(viewports)
            page.set_viewport_size({"width": width, "height": height})

        except Exception as e:
            logger.warning(f"⚠️ Error setting viewport size: {e}")

    def get_random_user_agent(self) -> str:
        """
        Get a random user agent string.

        Returns:
            Random user agent string
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]

        return random.choice(user_agents)


class UniversalClickPopupFramework:
    """Universal framework for handling click popup scenarios."""

    def __init__(self, site_name: str, config: Optional[HumanBehaviorConfig] = None):
        self.config = config or HumanBehaviorConfig()
        self.human_scraper = HumanBehaviorScraper()
        self.site_name = site_name
        self._load_site_config()

    def _load_site_config(self):
        """Loads site-specific configuration."""
        # This is a placeholder for site-specific configs.
        # In a real scenario, this would load from a file or a config object.
        site_configs = {
            "eluta": {
                "job_selector": ".organic-job",
                "popup_wait": 3.0,
            },
            "indeed": {
                "job_selector": ".jobsearch-SerpJobCard",
                "popup_wait": 2.0,
            },
            "jobbank": {
                "job_selector": ".job-listing",
                "popup_wait": 2.5,
            },
        }
        self.current_config = site_configs.get(self.site_name, {})

    async def expect_popup(self, page, selector: str, timeout: int = 5000) -> bool:
        """Expect and handle a popup after clicking an element."""
        try:
            # Click the element
            element = page.query_selector(selector)
            if element:
                self.human_scraper.simulate_human_click(page, element)

                # Wait for popup
                try:
                    await page.wait_for_event("popup", timeout=timeout)
                    logger.info(f"✅ Popup detected after clicking {selector}")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ No popup detected: {e}")
                    return False
            else:
                logger.error(f"❌ Element not found: {selector}")
                return False

        except Exception as e:
            logger.error(f"❌ Error in expect_popup: {e}")
            return False

    async def handle_popup(self, page, popup_selector: Optional[str] = None) -> Optional[Any]:
        """Handle popup window and return content."""
        try:
            # Get popup page
            popup_pages = page.context.pages
            if len(popup_pages) > 1:
                popup_page = popup_pages[-1]  # Latest popup

                # Wait for popup to load
                await popup_page.wait_for_load_state("networkidle")

                # Extract content if selector provided
                if popup_selector:
                    content = await popup_page.query_selector(popup_selector)
                    if content:
                        return await content.inner_text()

                return popup_page
            else:
                logger.warning("⚠️ No popup detected")
                return None

        except Exception as e:
            logger.error(f"❌ Error handling popup: {e}")
            return None


class HumanBehaviorScraper:
    """Scraper that mimics human behavior to avoid detection."""

    def __init__(self, profile: Optional[Dict] = None, **kwargs):
        self.profile = profile or {}
        self.profile_name = profile.get("profile_name", "default") if profile else "default"
        self.db = get_job_db(self.profile_name)

        # Configuration
        self.max_pages = kwargs.get("max_pages", 5)
        self.max_jobs = kwargs.get("max_jobs", 10)
        self.min_delay = kwargs.get("min_delay", 1.0)
        self.max_delay = kwargs.get("max_delay", 3.0)

        # Statistics
        self.jobs_scraped = 0
        self.jobs_saved = 0
        self.errors = []

        self.human_config = HumanBehaviorConfig()

    def simulate_human_delay(self) -> None:
        """Simulate human-like delays between actions."""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def simulate_human_scroll(self, page) -> None:
        """Simulate human-like scrolling behavior."""
        try:
            # Random scroll patterns
            scroll_distance = random.randint(300, 800)
            page.mouse.wheel(0, scroll_distance)
            time.sleep(random.uniform(0.5, 1.5))

            # Sometimes scroll back up
            if random.random() < 0.3:
                page.mouse.wheel(0, -scroll_distance // 2)
                time.sleep(random.uniform(0.3, 0.8))

        except Exception as e:
            logger.warning(f"⚠️ Error simulating scroll: {e}")

    def simulate_human_mouse_movement(self, page, element) -> None:
        """Simulate human-like mouse movement to element."""
        try:
            # Get element position
            box = element.bounding_box()
            if box:
                # Move mouse to element with slight randomness
                x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
                y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)

                # Move mouse in a natural curve
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))

        except Exception as e:
            logger.warning(f"⚠️ Error simulating mouse movement: {e}")

    def simulate_human_typing(self, page, selector: str, text: str) -> None:
        """Simulate human-like typing behavior."""
        try:
            element = page.query_selector(selector)
            if element:
                # Clear field first
                element.click()
                element.fill("")

                # Type with random delays between characters
                for char in text:
                    element.type(char)
                    time.sleep(random.uniform(0.05, 0.15))

        except Exception as e:
            logger.warning(f"⚠️ Error simulating typing: {e}")

    def simulate_human_click(self, page, element) -> None:
        """Simulate human-like clicking behavior."""
        try:
            # Move mouse to element first
            self.simulate_human_mouse_movement(page, element)

            # Random delay before click
            time.sleep(random.uniform(0.2, 0.8))

            # Click with slight randomness
            element.click()

            # Random delay after click
            time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            logger.warning(f"⚠️ Error simulating click: {e}")

    def simulate_page_load_wait(self, page) -> None:
        """Simulate human-like waiting for page to load."""
        try:
            # Wait for network to be idle
            page.wait_for_load_state("networkidle")

            # Additional random wait
            time.sleep(random.uniform(1.0, 2.5))

        except Exception as e:
            logger.warning(f"⚠️ Error waiting for page load: {e}")

    def simulate_human_navigation(self, page, url: str) -> None:
        """Simulate human-like navigation to a URL."""
        try:
            # Random delay before navigation
            time.sleep(random.uniform(0.5, 1.5))

            # Navigate to URL
            page.goto(url)

            # Wait for page to load
            self.simulate_page_load_wait(page)

        except Exception as e:
            logger.warning(f"⚠️ Error simulating navigation: {e}")

    def get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        ]
        return random.choice(user_agents)

    def simulate_human_session(self, page) -> None:
        """Simulate a human-like browsing session."""
        try:
            # Set random viewport size
            viewport_width = random.choice([1366, 1440, 1536, 1920])
            viewport_height = random.choice([768, 900, 864, 1080])
            page.set_viewport_size({"width": viewport_width, "height": viewport_height})

            # Set random user agent
            user_agent = self.get_random_user_agent()
            page.set_extra_http_headers({"User-Agent": user_agent})

            # Random session delay
            time.sleep(random.uniform(2.0, 5.0))

        except Exception as e:
            logger.warning(f"⚠️ Error simulating session: {e}")

    def get_statistics(self) -> Dict:
        """Get scraping statistics."""
        return {
            "jobs_scraped": self.jobs_scraped,
            "jobs_saved": self.jobs_saved,
            "errors": len(self.errors),
            "error_details": self.errors,
            "human_behavior_simulated": True,
        }


# Utility functions for human behavior simulation
def add_human_delays(min_delay: float = 1.0, max_delay: float = 3.0) -> None:
    """Add random human-like delays."""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)


def simulate_human_scroll_pattern(page) -> None:
    """Simulate a human-like scrolling pattern."""
    try:
        # Scroll down in chunks
        for _ in range(random.randint(2, 5)):
            scroll_distance = random.randint(200, 600)
            page.mouse.wheel(0, scroll_distance)
            time.sleep(random.uniform(0.8, 2.0))

        # Sometimes scroll back up
        if random.random() < 0.4:
            page.mouse.wheel(0, -random.randint(100, 300))
            time.sleep(random.uniform(0.5, 1.0))

    except Exception as e:
        logger.warning(f"⚠️ Error in scroll pattern: {e}")


def simulate_human_reading_time(page, content_length: int) -> None:
    """Simulate human reading time based on content length."""
    # Average reading speed: 200-300 words per minute
    words_per_minute = random.uniform(200, 300)
    estimated_words = content_length // 5  # Rough estimate
    reading_time = (estimated_words / words_per_minute) * 60

    # Add some randomness
    reading_time *= random.uniform(0.5, 1.5)

    # Cap at reasonable limits
    reading_time = max(1.0, min(reading_time, 30.0))

    time.sleep(reading_time)
