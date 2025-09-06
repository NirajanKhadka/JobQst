"""
Session management utilities for web scraping and browser automation.
"""

import time
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class SessionConfig:
    """Configuration for session management."""

    max_retries: int = 3
    retry_delay: float = 2.0
    max_delay: float = 10.0
    user_agent_rotation: bool = True
    proxy_rotation: bool = False
    session_timeout: int = 300  # 5 minutes
    request_timeout: int = 30


class SessionManager:
    """Manages web scraping sessions with retry logic and rate limiting."""

    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()
        self.session_start = datetime.now()
        self.request_count = 0
        self.last_request_time = None

        # User agent rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]

    def get_user_agent(self) -> str:
        """Get a random user agent for rotation."""
        if self.config.user_agent_rotation:
            return random.choice(self.user_agents)
        return self.user_agents[0]

    def should_rotate_session(self) -> bool:
        """Check if session should be rotated due to timeout."""
        elapsed = datetime.now() - self.session_start
        return elapsed.total_seconds() > self.config.session_timeout

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempts with exponential backoff."""
        delay = self.config.retry_delay * (2**attempt)
        return min(delay, self.config.max_delay)

    def wait_between_requests(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Wait between requests to avoid rate limiting."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < min_delay:
                sleep_time = random.uniform(min_delay, max_delay)
                time.sleep(sleep_time)

        self.last_request_time = datetime.now()

    def reset_session(self):
        """Reset session state."""
        self.session_start = datetime.now()
        self.request_count = 0
        self.last_request_time = None


class RateLimiter:
    """Rate limiting utility for web scraping."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[datetime] = []

    def can_make_request(self) -> bool:
        """Check if a request can be made without exceeding rate limit."""
        now = datetime.now()

        # Remove old requests outside the window
        window_start = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > window_start]

        return len(self.request_times) < self.requests_per_minute

    def record_request(self):
        """Record a request for rate limiting."""
        self.request_times.append(datetime.now())

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        while not self.can_make_request():
            time.sleep(1)


class ProxyManager:
    """Manages proxy rotation for web scraping."""

    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []
        self.current_index = 0
        self.failed_proxies = set()

    def get_next_proxy(self) -> Optional[str]:
        """Get the next proxy in rotation."""
        if not self.proxies:
            return None

        # Skip failed proxies
        available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
        if not available_proxies:
            # Reset failed proxies if all are marked as failed
            self.failed_proxies.clear()
            available_proxies = self.proxies

        if not available_proxies:
            return None

        proxy = available_proxies[self.current_index % len(available_proxies)]
        self.current_index += 1
        return proxy

    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed."""
        self.failed_proxies.add(proxy)

    def reset_failed_proxies(self):
        """Reset the list of failed proxies."""
        self.failed_proxies.clear()


class BrowserSession:
    """Manages browser session state and configuration."""

    def __init__(self, headless: bool = True, user_data_dir: Optional[str] = None):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.browser_args = []
        self.session_data = {}

    def add_browser_argument(self, arg: str):
        """Add a browser argument."""
        self.browser_args.append(arg)

    def set_session_data(self, key: str, value: Any):
        """Set session data."""
        self.session_data[key] = value

    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Get session data."""
        return self.session_data.get(key, default)

    def clear_session_data(self):
        """Clear all session data."""
        self.session_data.clear()

    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration."""
        config = {"headless": self.headless, "args": self.browser_args.copy()}

        if self.user_data_dir:
            config["user_data_dir"] = self.user_data_dir

        return config


def create_session_manager(
    max_retries: int = 3, retry_delay: float = 2.0, user_agent_rotation: bool = True
) -> SessionManager:
    """Create a session manager with default configuration."""
    config = SessionConfig(
        max_retries=max_retries, retry_delay=retry_delay, user_agent_rotation=user_agent_rotation
    )
    return SessionManager(config)


def create_rate_limiter(requests_per_minute: int = 60) -> RateLimiter:
    """Create a rate limiter with specified requests per minute."""
    return RateLimiter(requests_per_minute)


def create_browser_session(headless: bool = True) -> BrowserSession:
    """Create a browser session with default configuration."""
    return BrowserSession(headless=headless)

