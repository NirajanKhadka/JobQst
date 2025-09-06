"""
Session Manager Module for AutoJobAgent.

This module provides session management functionality for maintaining
browser sessions, cookies, and state across scraping operations.
"""

import json
import logging
import time
import random
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages browser sessions and state for scraping operations."""

    def __init__(self, profile_name: Optional[str] = None):
        if profile_name is None or profile_name == "":
            self.profile_name = "default"
        else:
            self.profile_name = profile_name
        self.session_dir = Path(f"profiles/{self.profile_name}/sessions")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session = {}
        self.session_history = []

    def create_session(self, session_name: str = None) -> str:
        """
        Create a new session.

        Args:
            session_name: Optional name for the session

        Returns:
            Session ID
        """
        if not session_name:
            session_name = f"session_{int(time.time())}"

        session_id = f"{self.profile_name}_{session_name}"

        self.current_session = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "profile_name": self.profile_name,
            "status": "active",
            "data": {},
        }

        # Save session
        self._save_session()

        logger.info(f"✅ Created session: {session_id}")
        return session_id

    def load_session(self, session_id: str) -> bool:
        """
        Load an existing session.

        Args:
            session_id: Session ID to load

        Returns:
            True if session loaded successfully
        """
        try:
            session_file = self.session_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, "r") as f:
                    self.current_session = json.load(f)

                logger.info(f"✅ Loaded session: {session_id}")
                return True
            else:
                logger.warning(f"⚠️ Session not found: {session_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Error loading session: {e}")
            return False

    def save_session_data(self, session_data):
        try:
            with open(self.session_file, "w") as f:
                json.dump(session_data, f)
            return True
        except Exception:
            return False

    def get_session_data(self, key: str, default: Any = None) -> Any:
        """
        Get data from current session.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Session data value
        """
        if self.current_session:
            return self.current_session["data"].get(key, default)
        return default

    def end_session(self) -> None:
        """End the current session."""
        if self.current_session:
            self.current_session["status"] = "ended"
            self.current_session["ended_at"] = datetime.now().isoformat()
            self._save_session()

            # Add to history
            self.session_history.append(self.current_session.copy())

            logger.info(f"✅ Ended session: {self.current_session['session_id']}")

    def _save_session(self) -> None:
        """Save current session to file."""
        try:
            if self.current_session:
                session_id = self.current_session["session_id"]
                session_file = self.session_dir / f"{session_id}.json"

                with open(session_file, "w") as f:
                    json.dump(self.current_session, f, indent=2)

        except Exception as e:
            logger.error(f"❌ Error saving session: {e}")

    def get_session_info(self) -> Dict:
        """Get information about the current session."""
        if self.current_session:
            return {
                "session_id": self.current_session.get("session_id"),
                "status": self.current_session.get("status"),
                "created_at": self.current_session.get("created_at"),
                "updated_at": self.current_session.get("updated_at"),
                "data_keys": list(self.current_session.get("data", {}).keys()),
            }
        return {}

    def list_sessions(self) -> List[Dict]:
        """List all available sessions."""
        sessions = []

        try:
            for session_file in self.session_dir.glob("*.json"):
                try:
                    with open(session_file, "r") as f:
                        session_data = json.load(f)
                        sessions.append(
                            {
                                "session_id": session_data.get("session_id"),
                                "created_at": session_data.get("created_at"),
                                "status": session_data.get("status"),
                                "profile_name": session_data.get("profile_name"),
                            }
                        )
                except Exception as e:
                    logger.warning(f"⚠️ Error reading session file {session_file}: {e}")

        except Exception as e:
            logger.error(f"❌ Error listing sessions: {e}")

        return sessions

    def cleanup_old_sessions(self, max_age_hours=24):
        try:
            with open(self.session_file, "r") as f:
                data = json.load(f)
            timestamp = data.get("timestamp")
            if timestamp:
                ts = datetime.fromisoformat(timestamp)
                if (datetime.now() - ts).total_seconds() > max_age_hours * 3600:
                    with open(self.session_file, "w") as f:
                        json.dump({}, f)
            return True
        except Exception:
            return False


class CookieSessionManager:
    """
    Manages browser cookies and cookie-based sessions for scraping operations.

    Provides cookie storage, retrieval, and management for maintaining
    login states and session persistence across scraping operations.
    """

    def __init__(
        self,
        profile_name: Optional[str] = None,
        cookie_file: str = "",
        session_file: str = "",
        site_name: str = "",
    ):
        """
        Initialize the cookie session manager.

        Args:
            profile_name: Name of the user profile
            cookie_file: Path to the cookie file (optional)
            session_file: Path to the session file (optional)
            site_name: Name of the site (optional)
        """
        self.profile_name = "default" if not profile_name else profile_name
        self.site_name = site_name if site_name else "default_site"
        self.cookie_file = (
            str(cookie_file)
            if cookie_file
            else f"profiles/{self.profile_name}/cookies/cookies.json"
        )
        self.session_file = (
            str(session_file)
            if session_file
            else f"profiles/{self.profile_name}/sessions/session.json"
        )
        self.session_id = "dummy-session-id"
        self.cookie_dir = Path(f"profiles/{self.profile_name}/cookies")
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self.current_cookies = {}
        self.cookie_history = []

    def save_cookies(self, cookies: List[Dict] = None, domain: str = "") -> bool:
        cookies = cookies if cookies is not None else []
        try:
            file_path = self.cookie_file
            if domain:
                safe_domain = domain.replace(".", "_").replace("/", "_")
                file_path = f"profiles/{self.profile_name}/cookies/{safe_domain}_cookies.json"
            with open(file_path, "w") as f:
                json.dump({"cookies": cookies}, f)
            return True
        except Exception as e:
            print(f"❌ Error saving cookies for {cookies}: {e}")
            return False

    def load_cookies(self) -> List[Dict]:
        try:
            with open(self.cookie_file, "r") as f:
                data = json.load(f)
            cookies = data.get("cookies", []) if isinstance(data, dict) else data
            now = datetime.now().timestamp()
            filtered = [c for c in cookies if ("expires" not in c or c["expires"] > now)]
            return filtered
        except Exception as e:
            print(f"❌ Error loading cookies from file: {e}")
            return []

    def _save_cookies_domain(self, domain: str, cookies: List[Dict]) -> bool:
        try:
            cookie_file = self.cookie_dir / f"{domain}_cookies.json"
            cookie_data = {
                "domain": domain,
                "cookies": cookies,
                "saved_at": datetime.now().isoformat(),
                "profile_name": self.profile_name,
            }
            with open(cookie_file, "w") as f:
                json.dump(cookie_data, f, indent=2)
            self.current_cookies[domain] = cookies
            logger.info(f"✅ Saved cookies for domain: {domain}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving cookies for {domain}: {e}")
            return False

    def _load_cookies_domain(self, domain: str) -> List[Dict]:
        try:
            cookie_file = self.cookie_dir / f"{domain}_cookies.json"
            if cookie_file.exists():
                with open(cookie_file, "r") as f:
                    cookie_data = json.load(f)
                cookies = cookie_data.get("cookies", [])
                self.current_cookies[domain] = cookies
                logger.info(f"✅ Loaded cookies for domain: {domain}")
                return cookies
            else:
                logger.warning(f"⚠️ No cookies found for domain: {domain}")
                return []
        except Exception as e:
            logger.error(f"❌ Error loading cookies for {domain}: {e}")
            return []

    def get_cookie(self, domain: str, name: str) -> Optional[Dict]:
        """
        Get a specific cookie by name for a domain.

        Args:
            domain: Domain name
            name: Cookie name

        Returns:
            Cookie dictionary or None if not found
        """
        cookies = self.current_cookies.get(domain, [])

        for cookie in cookies:
            if cookie.get("name") == name:
                return cookie

        return None

    def set_cookie(self, domain: str, name: str, value: str, **kwargs) -> bool:
        """
        Set a cookie for a domain.

        Args:
            domain: Domain name
            name: Cookie name
            value: Cookie value
            **kwargs: Additional cookie attributes

        Returns:
            True if cookie set successfully
        """
        if domain not in self.current_cookies:
            self.current_cookies[domain] = []

        # Remove existing cookie with same name
        self.current_cookies[domain] = [
            c for c in self.current_cookies[domain] if c.get("name") != name
        ]

        # Add new cookie
        cookie = {"name": name, "value": value, "domain": domain, **kwargs}

        self.current_cookies[domain].append(cookie)

        # Save to file
        return self.save_cookies(self.current_cookies[domain], domain)

    def delete_cookie(self, domain: str, name: str) -> bool:
        """
        Delete a cookie by name for a domain.

        Args:
            domain: Domain name
            name: Cookie name

        Returns:
            True if cookie deleted successfully
        """
        if domain in self.current_cookies:
            original_count = len(self.current_cookies[domain])
            self.current_cookies[domain] = [
                c for c in self.current_cookies[domain] if c.get("name") != name
            ]

            if len(self.current_cookies[domain]) < original_count:
                return self.save_cookies(self.current_cookies[domain], domain)

        return False

    def clear_cookies(self, domain: str = "") -> bool:
        """
        Clear all cookies for a domain or all domains.

        Args:
            domain: Domain name (empty string for all domains)
        Returns:
            True if cookies cleared successfully
        """
        try:
            if domain:
                if domain in self.current_cookies:
                    del self.current_cookies[domain]
                    cookie_file = self.cookie_dir / f"{domain}_cookies.json"
                    if cookie_file.exists():
                        cookie_file.unlink()
            else:
                self.current_cookies.clear()
                for cookie_file in self.cookie_dir.glob("*_cookies.json"):
                    cookie_file.unlink()
            logger.info(f"✅ Cleared cookies for domain: {domain or 'all'}")
            return True
        except Exception as e:
            logger.error(f"❌ Error clearing cookies: {e}")
            return False

    def list_cookie_domains(self) -> List[str]:
        """
        List all domains with saved cookies.

        Returns:
            List of domain names
        """
        domains = []

        try:
            for cookie_file in self.cookie_dir.glob("*_cookies.json"):
                domain = cookie_file.stem.replace("_cookies", "")
                domains.append(domain)

        except Exception as e:
            logger.error(f"❌ Error listing cookie domains: {e}")

        return domains

    def get_cookie_count(self, domain: str = "") -> int:
        """
        Get the number of cookies for a domain or total.

        Args:
            domain: Domain name (empty string for total)
        Returns:
            Number of cookies
        """
        if domain:
            return len(self.current_cookies.get(domain, []))
        else:
            return sum(len(cookies) for cookies in self.current_cookies.values())

    def apply_cookies_to_context(self, context) -> bool:
        """Stub: Apply cookies to browser context (not implemented)."""
        logger.info("Stub: apply_cookies_to_context called.")
        return True

    def get_random_user_agent(self):
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        ]
        return random.choice(agents)

    @property
    def cookie_file(self):
        return self._cookie_file if hasattr(self, "_cookie_file") else None

    @cookie_file.setter
    def cookie_file(self, value):
        self._cookie_file = str(value) if value else None

    def load_session_data(self):
        try:
            with open(self.session_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def extract_cookies_from_context(self, context):
        """Stub: Extract cookies from browser context."""
        return True


# Factory functions for backward compatibility
def create_session(profile_name: Optional[str], session_name: str = "") -> str:
    """Create a new session."""
    session_manager = SessionManager(profile_name)
    return session_manager.create_session(session_name)


def load_session(profile_name: Optional[str], session_id: str) -> bool:
    """Load an existing session."""
    session_manager = SessionManager(profile_name)
    return session_manager.load_session(session_id)


def save_session_data(profile_name: Optional[str], key: str, value: Any) -> None:
    """Save data to current session."""
    session_manager = SessionManager(profile_name)
    session_manager.save_session_data(key, value)


def get_session_data(profile_name: Optional[str], key: str, default: Any = None) -> Any:
    """Get data from current session."""
    session_manager = SessionManager(profile_name)
    return session_manager.get_session_data(key, default)

