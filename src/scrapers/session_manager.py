"""
Session Manager Module for AutoJobAgent.

This module provides session management functionality for maintaining
browser sessions, cookies, and state across scraping operations.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages browser sessions and state for scraping operations."""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.session_dir = Path(f"profiles/{profile_name}/sessions")
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
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'profile_name': self.profile_name,
            'status': 'active',
            'data': {}
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
                with open(session_file, 'r') as f:
                    self.current_session = json.load(f)
                
                logger.info(f"✅ Loaded session: {session_id}")
                return True
            else:
                logger.warning(f"⚠️ Session not found: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error loading session: {e}")
            return False
    
    def save_session_data(self, key: str, value: Any) -> None:
        """
        Save data to current session.
        
        Args:
            key: Data key
            value: Data value
        """
        if self.current_session:
            self.current_session['data'][key] = value
            self.current_session['updated_at'] = datetime.now().isoformat()
            self._save_session()
    
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
            return self.current_session['data'].get(key, default)
        return default
    
    def end_session(self) -> None:
        """End the current session."""
        if self.current_session:
            self.current_session['status'] = 'ended'
            self.current_session['ended_at'] = datetime.now().isoformat()
            self._save_session()
            
            # Add to history
            self.session_history.append(self.current_session.copy())
            
            logger.info(f"✅ Ended session: {self.current_session['session_id']}")
    
    def _save_session(self) -> None:
        """Save current session to file."""
        try:
            if self.current_session:
                session_id = self.current_session['session_id']
                session_file = self.session_dir / f"{session_id}.json"
                
                with open(session_file, 'w') as f:
                    json.dump(self.current_session, f, indent=2)
                    
        except Exception as e:
            logger.error(f"❌ Error saving session: {e}")
    
    def get_session_info(self) -> Dict:
        """Get information about the current session."""
        if self.current_session:
            return {
                'session_id': self.current_session.get('session_id'),
                'status': self.current_session.get('status'),
                'created_at': self.current_session.get('created_at'),
                'updated_at': self.current_session.get('updated_at'),
                'data_keys': list(self.current_session.get('data', {}).keys())
            }
        return {}
    
    def list_sessions(self) -> List[Dict]:
        """List all available sessions."""
        sessions = []
        
        try:
            for session_file in self.session_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                        sessions.append({
                            'session_id': session_data.get('session_id'),
                            'created_at': session_data.get('created_at'),
                            'status': session_data.get('status'),
                            'profile_name': session_data.get('profile_name')
                        })
                except Exception as e:
                    logger.warning(f"⚠️ Error reading session file {session_file}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error listing sessions: {e}")
        
        return sessions
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up old sessions.
        
        Args:
            days: Number of days to keep sessions
            
        Returns:
            Number of sessions cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_count = 0
        
        try:
            for session_file in self.session_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    created_at = datetime.fromisoformat(session_data.get('created_at', '1970-01-01'))
                    
                    if created_at < cutoff_date:
                        session_file.unlink()
                        cleaned_count += 1
                        logger.info(f"🗑️ Cleaned up old session: {session_file.name}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error processing session file {session_file}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error cleaning up sessions: {e}")
        
        return cleaned_count


class CookieSessionManager:
    """
    Manages browser cookies and cookie-based sessions for scraping operations.
    
    Provides cookie storage, retrieval, and management for maintaining
    login states and session persistence across scraping operations.
    """
    
    def __init__(self, profile_name: str):
        """
        Initialize the cookie session manager.
        
        Args:
            profile_name: Name of the user profile
        """
        self.profile_name = profile_name
        self.cookie_dir = Path(f"profiles/{profile_name}/cookies")
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self.current_cookies = {}
        self.cookie_history = []
        
    def save_cookies(self, domain: str, cookies: List[Dict]) -> bool:
        """
        Save cookies for a specific domain.
        
        Args:
            domain: Domain name (e.g., 'www.eluta.ca')
            cookies: List of cookie dictionaries
            
        Returns:
            True if cookies saved successfully
        """
        try:
            cookie_file = self.cookie_dir / f"{domain}_cookies.json"
            
            cookie_data = {
                'domain': domain,
                'cookies': cookies,
                'saved_at': datetime.now().isoformat(),
                'profile_name': self.profile_name
            }
            
            with open(cookie_file, 'w') as f:
                json.dump(cookie_data, f, indent=2)
                
            self.current_cookies[domain] = cookies
            logger.info(f"✅ Saved cookies for domain: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving cookies for {domain}: {e}")
            return False
            
    def load_cookies(self, domain: str) -> List[Dict]:
        """
        Load cookies for a specific domain.
        
        Args:
            domain: Domain name
            
        Returns:
            List of cookie dictionaries
        """
        try:
            cookie_file = self.cookie_dir / f"{domain}_cookies.json"
            
            if cookie_file.exists():
                with open(cookie_file, 'r') as f:
                    cookie_data = json.load(f)
                    
                cookies = cookie_data.get('cookies', [])
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
            if cookie.get('name') == name:
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
            c for c in self.current_cookies[domain] 
            if c.get('name') != name
        ]
        
        # Add new cookie
        cookie = {
            'name': name,
            'value': value,
            'domain': domain,
            **kwargs
        }
        
        self.current_cookies[domain].append(cookie)
        
        # Save to file
        return self.save_cookies(domain, self.current_cookies[domain])
        
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
                c for c in self.current_cookies[domain] 
                if c.get('name') != name
            ]
            
            if len(self.current_cookies[domain]) < original_count:
                return self.save_cookies(domain, self.current_cookies[domain])
                
        return False
        
    def clear_cookies(self, domain: str = None) -> bool:
        """
        Clear all cookies for a domain or all domains.
        
        Args:
            domain: Domain name (None for all domains)
            
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
                domain = cookie_file.stem.replace('_cookies', '')
                domains.append(domain)
                
        except Exception as e:
            logger.error(f"❌ Error listing cookie domains: {e}")
            
        return domains
        
    def get_cookie_count(self, domain: str = None) -> int:
        """
        Get the number of cookies for a domain or total.
        
        Args:
            domain: Domain name (None for total)
            
        Returns:
            Number of cookies
        """
        if domain:
            return len(self.current_cookies.get(domain, []))
        else:
            return sum(len(cookies) for cookies in self.current_cookies.values())


# Factory functions for backward compatibility
def create_session(profile_name: str, session_name: str = None) -> str:
    """Create a new session."""
    session_manager = SessionManager(profile_name)
    return session_manager.create_session(session_name)

def load_session(profile_name: str, session_id: str) -> bool:
    """Load an existing session."""
    session_manager = SessionManager(profile_name)
    return session_manager.load_session(session_id)

def save_session_data(profile_name: str, key: str, value: Any) -> None:
    """Save data to current session."""
    session_manager = SessionManager(profile_name)
    session_manager.save_session_data(key, value)

def get_session_data(profile_name: str, key: str, default: Any = None) -> Any:
    """Get data from current session."""
    session_manager = SessionManager(profile_name)
    return session_manager.get_session_data(key, default)