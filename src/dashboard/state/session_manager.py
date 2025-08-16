"""
Session Manager

This module provides session state management capabilities for the dashboard.
It handles persistent user preferences, selections, and session data across
browser refreshes and multiple tabs.
"""

import streamlit as st
import json
import pickle
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
import uuid
import os
from pathlib import Path

# Set up logging
import logging
logger = logging.getLogger(__name__)


class SessionScope(Enum):
    """Scope of session data persistence."""
    BROWSER = "browser"      # Per browser instance
    USER = "user"           # Per user (requires user ID)
    GLOBAL = "global"       # Shared across all users
    TEMPORARY = "temporary" # Current session only


@dataclass
class SessionData:
    """Session data container."""
    session_id: str
    user_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    scope: SessionScope = SessionScope.BROWSER
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def update_access(self):
        """Update last accessed timestamp."""
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'data': self.data,
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'scope': self.scope.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary."""
        return cls(
            session_id=data['session_id'],
            user_id=data.get('user_id'),
            data=data.get('data', {}),
            preferences=data.get('preferences', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            scope=SessionScope(data.get('scope', 'browser'))
        )


class SessionStorage:
    """Handles session data persistence."""
    
    def __init__(self, storage_dir: str = "sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
    
    def _get_session_file(self, session_id: str, scope: SessionScope) -> Path:
        """Get file path for session data."""
        scope_dir = self.storage_dir / scope.value
        scope_dir.mkdir(exist_ok=True)
        return scope_dir / f"{session_id}.json"
    
    def save_session(self, session_data: SessionData) -> bool:
        """Save session data to storage."""
        try:
            with self._lock:
                file_path = self._get_session_file(session_data.session_id, session_data.scope)
                
                with open(file_path, 'w') as f:
                    json.dump(session_data.to_dict(), f, indent=2)
                
                logger.debug(f"Saved session {session_data.session_id} to {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving session {session_data.session_id}: {e}")
            return False
    
    def load_session(self, session_id: str, scope: SessionScope) -> Optional[SessionData]:
        """Load session data from storage."""
        try:
            with self._lock:
                file_path = self._get_session_file(session_id, scope)
                
                if not file_path.exists():
                    return None
                
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                session_data = SessionData.from_dict(data)
                
                # Check if expired
                if session_data.is_expired():
                    self.delete_session(session_id, scope)
                    return None
                
                logger.debug(f"Loaded session {session_id} from {file_path}")
                return session_data
                
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str, scope: SessionScope) -> bool:
        """Delete session data from storage."""
        try:
            with self._lock:
                file_path = self._get_session_file(session_id, scope)
                
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Deleted session {session_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self, scope: SessionScope) -> List[str]:
        """List all session IDs for a scope."""
        try:
            scope_dir = self.storage_dir / scope.value
            if not scope_dir.exists():
                return []
            
            sessions = []
            for file_path in scope_dir.glob("*.json"):
                session_id = file_path.stem
                sessions.append(session_id)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions for scope {scope.value}: {e}")
            return []
    
    def cleanup_expired_sessions(self):
        """Remove expired session files."""
        try:
            with self._lock:
                for scope in SessionScope:
                    scope_dir = self.storage_dir / scope.value
                    if not scope_dir.exists():
                        continue
                    
                    for file_path in scope_dir.glob("*.json"):
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                            
                            session_data = SessionData.from_dict(data)
                            if session_data.is_expired():
                                file_path.unlink()
                                logger.debug(f"Cleaned up expired session {session_data.session_id}")
                                
                        except Exception as e:
                            logger.warning(f"Error checking session file {file_path}: {e}")
                            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")


class SessionManager:
    """Main session management class."""
    
    def __init__(self, storage_dir: str = "sessions", default_expiry_hours: int = 24):
        self.storage = SessionStorage(storage_dir)
        self.default_expiry_hours = default_expiry_hours
        self._active_sessions: Dict[str, SessionData] = {}
        self._lock = threading.Lock()
        
        # Default session settings
        self.default_preferences = {
            'theme': 'light',
            'language': 'en',
            'timezone': 'UTC',
            'notifications_enabled': True,
            'auto_refresh': True,
            'items_per_page': 20
        }
    
    def _generate_session_id(self, scope: SessionScope, user_id: Optional[str] = None) -> str:
        """Generate unique session ID."""
        if scope == SessionScope.USER and user_id:
            # User-specific session
            return f"user_{hashlib.md5(user_id.encode()).hexdigest()}"
        elif scope == SessionScope.GLOBAL:
            # Global session
            return "global_session"
        else:
            # Browser-specific session (use Streamlit's session state)
            if hasattr(st, 'session_state') and hasattr(st.session_state, '_session_id'):
                return st.session_state._session_id
            else:
                # Generate new browser session ID
                session_id = str(uuid.uuid4())
                if hasattr(st, 'session_state'):
                    st.session_state._session_id = session_id
                return session_id
    
    def get_session(self, 
                   scope: SessionScope = SessionScope.BROWSER,
                   user_id: Optional[str] = None,
                   create_if_missing: bool = True) -> Optional[SessionData]:
        """
        Get or create session data.
        
        Args:
            scope: Session scope
            user_id: User ID for user-scoped sessions
            create_if_missing: Create new session if not found
        
        Returns:
            SessionData or None
        """
        session_id = self._generate_session_id(scope, user_id)
        
        with self._lock:
            # Check active sessions first
            if session_id in self._active_sessions:
                session = self._active_sessions[session_id]
                session.update_access()
                return session
            
            # Try to load from storage
            session = self.storage.load_session(session_id, scope)
            
            if session is None and create_if_missing:
                # Create new session
                expires_at = datetime.now() + timedelta(hours=self.default_expiry_hours)
                
                session = SessionData(
                    session_id=session_id,
                    user_id=user_id,
                    scope=scope,
                    expires_at=expires_at,
                    preferences=self.default_preferences.copy()
                )
                
                logger.info(f"Created new session {session_id} with scope {scope.value}")
            
            if session:
                session.update_access()
                self._active_sessions[session_id] = session
            
            return session
    
    def save_session(self, session_data: SessionData) -> bool:
        """Save session data."""
        session_data.update_access()
        
        with self._lock:
            # Update active session
            self._active_sessions[session_data.session_id] = session_data
            
            # Save to storage
            return self.storage.save_session(session_data)
    
    def set_session_value(self, 
                         key: str, 
                         value: Any,
                         scope: SessionScope = SessionScope.BROWSER,
                         user_id: Optional[str] = None):
        """Set a value in session data."""
        session = self.get_session(scope, user_id)
        if session:
            session.data[key] = value
            self.save_session(session)
    
    def get_session_value(self, 
                         key: str, 
                         default: Any = None,
                         scope: SessionScope = SessionScope.BROWSER,
                         user_id: Optional[str] = None) -> Any:
        """Get a value from session data."""
        session = self.get_session(scope, user_id, create_if_missing=False)
        if session:
            return session.data.get(key, default)
        return default
    
    def set_preference(self, 
                      key: str, 
                      value: Any,
                      scope: SessionScope = SessionScope.BROWSER,
                      user_id: Optional[str] = None):
        """Set a user preference."""
        session = self.get_session(scope, user_id)
        if session:
            session.preferences[key] = value
            self.save_session(session)
    
    def get_preference(self, 
                      key: str, 
                      default: Any = None,
                      scope: SessionScope = SessionScope.BROWSER,
                      user_id: Optional[str] = None) -> Any:
        """Get a user preference."""
        session = self.get_session(scope, user_id, create_if_missing=False)
        if session:
            return session.preferences.get(key, default)
        return default
    
    def clear_session(self, 
                     scope: SessionScope = SessionScope.BROWSER,
                     user_id: Optional[str] = None):
        """Clear session data."""
        session_id = self._generate_session_id(scope, user_id)
        
        with self._lock:
            # Remove from active sessions
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
            
            # Delete from storage
            self.storage.delete_session(session_id, scope)
    
    def get_session_info(self, 
                        scope: SessionScope = SessionScope.BROWSER,
                        user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get session information."""
        session = self.get_session(scope, user_id, create_if_missing=False)
        if session:
            return {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'created_at': session.created_at.isoformat(),
                'last_accessed': session.last_accessed.isoformat(),
                'expires_at': session.expires_at.isoformat() if session.expires_at else None,
                'scope': session.scope.value,
                'data_keys': list(session.data.keys()),
                'preferences': session.preferences
            }
        return None
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        # Clean storage
        self.storage.cleanup_expired_sessions()
        
        # Clean active sessions
        with self._lock:
            expired_sessions = [
                session_id for session_id, session in self._active_sessions.items()
                if session.is_expired()
            ]
            
            for session_id in expired_sessions:
                del self._active_sessions[session_id]
                logger.debug(f"Removed expired active session {session_id}")


# Global session manager instance
session_manager = SessionManager()


# Streamlit integration functions
def st_set_session_value(key: str, value: Any, persistent: bool = False):
    """Set value in Streamlit session state with optional persistence."""
    # Set in current session state
    if hasattr(st, 'session_state'):
        st.session_state[key] = value
    
    # Also save persistently if requested
    if persistent:
        session_manager.set_session_value(key, value)


def st_get_session_value(key: str, default: Any = None, persistent: bool = False) -> Any:
    """Get value from Streamlit session state with fallback to persistent storage."""
    # Try current session state first
    if hasattr(st, 'session_state') and key in st.session_state:
        return st.session_state[key]
    
    # Try persistent storage if enabled
    if persistent:
        value = session_manager.get_session_value(key, default)
        # Cache in current session state
        if hasattr(st, 'session_state'):
            st.session_state[key] = value
        return value
    
    return default


def st_set_preference(key: str, value: Any):
    """Set user preference with persistence."""
    session_manager.set_preference(key, value)


def st_get_preference(key: str, default: Any = None) -> Any:
    """Get user preference."""
    return session_manager.get_preference(key, default)


def st_clear_session():
    """Clear current session data."""
    # Clear Streamlit session state
    if hasattr(st, 'session_state'):
        for key in list(st.session_state.keys()):
            if not key.startswith('_'):  # Don't clear internal keys
                del st.session_state[key]
    
    # Clear persistent session
    session_manager.clear_session()


def st_get_session_info() -> Optional[Dict[str, Any]]:
    """Get current session information."""
    return session_manager.get_session_info()


# Context manager for session state
class SessionContext:
    """Context manager for session operations."""
    
    def __init__(self, scope: SessionScope = SessionScope.BROWSER, user_id: Optional[str] = None):
        self.scope = scope
        self.user_id = user_id
        self.session_data = None
    
    def __enter__(self) -> SessionData:
        """Enter session context."""
        self.session_data = session_manager.get_session(self.scope, self.user_id)
        return self.session_data
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit session context and save data."""
        if self.session_data:
            session_manager.save_session(self.session_data)


# Convenience functions
def with_session(scope: SessionScope = SessionScope.BROWSER, user_id: Optional[str] = None):
    """Decorator for functions that need session access."""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            with SessionContext(scope, user_id) as session:
                return func(session, *args, **kwargs)
        return wrapper
    return decorator
