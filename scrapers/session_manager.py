"""
Cookie-Based Session Manager for Enhanced Click-and-Popup Scraping
Implemented using Test-Driven Development (TDD) - Tests written first!

This module provides session persistence, cookie management, and anti-detection
features for maintaining scraping sessions across browser contexts.

Key Features:
- Cookie persistence across browser sessions
- Session data management with automatic cleanup
- Anti-detection user agent rotation
- Cross-platform file handling with proper error handling
- Integration with Playwright browser contexts
"""

import json
import os
import uuid
import random
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from rich.console import Console

console = Console()


class SessionManagerError(Exception):
    """Custom exception for session manager errors."""
    pass


class CookieSessionManager:
    """
    Cookie-based session manager for maintaining scraping sessions.
    Implements all functionality defined in test_session_manager.py
    """
    
    def __init__(self, cookie_file: str = None, session_file: str = None, site_name: str = "generic"):
        """Initialize the session manager."""
        self.cookie_file = cookie_file or f"scrapers/cookies_{site_name}.json"
        self.session_file = session_file or f"scrapers/session_{site_name}.json"
        self.site_name = site_name
        self.session_id = str(uuid.uuid4())
        self.session_data = {}
        
        # Load existing session data
        self.session_data = self.load_session_data()
        
        console.print(f"[green]✅ Session manager initialized for {site_name}[/green]")
        
    def save_cookies(self, cookies: List[Dict]) -> bool:
        """Save cookies to file."""
        try:
            cookie_data = {
                "cookies": cookies,
                "timestamp": datetime.now().isoformat(),
                "site_name": self.site_name,
                "session_id": self.session_id
            }

            # Ensure directory exists
            self._ensure_directory_exists(self.cookie_file)

            with open(self.cookie_file, 'w') as f:
                json.dump(cookie_data, f, indent=2)

            console.print(f"[green]✅ Saved {len(cookies)} cookies for {self.site_name}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to save cookies: {e}[/red]")
            return False
            
    def load_cookies(self) -> List[Dict]:
        """Load cookies from file, filtering out expired ones."""
        try:
            if not os.path.exists(self.cookie_file):
                return []
                
            with open(self.cookie_file, 'r') as f:
                data = json.load(f)
                
            cookies = data.get("cookies", [])
            
            # Filter out expired cookies using utility method
            valid_cookies = [cookie for cookie in cookies if not self._is_cookie_expired(cookie)]
                    
            console.print(f"[green]✅ Loaded {len(valid_cookies)} valid cookies for {self.site_name}[/green]")
            return valid_cookies
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load cookies: {e}[/red]")
            return []
            
    def save_session_data(self, session_data: Dict) -> bool:
        """Save session data to file."""
        try:
            session_info = {
                **session_data,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "site_name": self.site_name
            }

            # Ensure directory exists
            self._ensure_directory_exists(self.session_file)

            with open(self.session_file, 'w') as f:
                json.dump(session_info, f, indent=2)

            self.session_data = session_info
            console.print(f"[green]✅ Session data saved for {self.site_name}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to save session data: {e}[/red]")
            return False
            
    def load_session_data(self) -> Dict:
        """Load session data from file."""
        try:
            if not os.path.exists(self.session_file):
                return {}
                
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                
            console.print(f"[green]✅ Session data loaded for {self.site_name}[/green]")
            return data
            
        except Exception as e:
            console.print(f"[red]❌ Failed to load session data: {e}[/red]")
            return {}
            
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> bool:
        """Clean up old session data."""
        try:
            if not os.path.exists(self.session_file):
                return True
                
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                
            timestamp_str = data.get("timestamp")
            if not timestamp_str:
                return True
                
            timestamp = datetime.fromisoformat(timestamp_str)
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                # Remove old session file
                os.remove(self.session_file)
                console.print(f"[yellow]🗑️ Cleaned up old session data ({age_hours:.1f} hours old)[/yellow]")
                
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to cleanup sessions: {e}[/red]")
            return False
            
    def apply_cookies_to_context(self, browser_context) -> bool:
        """Apply saved cookies to browser context."""
        try:
            cookies = self.load_cookies()
            if not cookies:
                return True
                
            # Apply cookies to context (mock implementation for testing)
            if hasattr(browser_context, 'add_cookies'):
                browser_context.add_cookies(cookies)
            
            console.print(f"[green]✅ Applied {len(cookies)} cookies to browser context[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to apply cookies: {e}[/red]")
            return False
            
    def extract_cookies_from_context(self, browser_context) -> bool:
        """Extract cookies from browser context and save them."""
        try:
            # Extract cookies from context
            cookies = browser_context.cookies()
            
            # Save extracted cookies
            return self.save_cookies(cookies)
            
        except Exception as e:
            console.print(f"[red]❌ Failed to extract cookies: {e}[/red]")
            return False
            
    def get_random_user_agent(self) -> str:
        """Get a random user agent for anti-detection."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        
        return random.choice(user_agents)

    def _ensure_directory_exists(self, file_path: str) -> bool:
        """Ensure the directory for a file path exists."""
        try:
            directory = os.path.dirname(file_path)
            if not directory:
                return True

            if not os.path.isabs(directory):
                # Relative path - safe to create
                os.makedirs(directory, exist_ok=True)
                return True
            else:
                # Absolute path - check if it's valid
                os.makedirs(directory, exist_ok=True)
                return True

        except (OSError, PermissionError) as e:
            raise SessionManagerError(f"Cannot create directory for {file_path}: {e}")

    def _is_cookie_expired(self, cookie: Dict) -> bool:
        """Check if a cookie is expired."""
        expires = cookie.get("expires")
        if expires is None:
            return False  # No expiry means permanent

        current_time = datetime.now().timestamp()
        return expires <= current_time

    def get_session_stats(self) -> Dict:
        """Get session statistics."""
        cookies = self.load_cookies()
        session_data = self.load_session_data()

        return {
            "session_id": self.session_id,
            "site_name": self.site_name,
            "cookie_count": len(cookies),
            "session_age_hours": self._get_session_age_hours(),
            "last_activity": session_data.get("timestamp", "Never"),
            "has_valid_cookies": len(cookies) > 0
        }

    def _get_session_age_hours(self) -> float:
        """Get the age of the current session in hours."""
        session_data = self.load_session_data()
        timestamp_str = session_data.get("timestamp")

        if not timestamp_str:
            return 0.0

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp
            return age.total_seconds() / 3600
        except ValueError:
            return 0.0
