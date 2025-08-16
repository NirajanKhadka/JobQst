"""
State Management Package

This package provides comprehensive state management capabilities for the dashboard,
including session management, caching, and state synchronization across multiple
instances and browser tabs.

Components:
- session_manager: Persistent user preferences and session data
- cache_manager: Multi-level caching with Automated invalidation
- state_synchronizer: Cross-tab and cross-instance state synchronization
"""

from .session_manager import (
    SessionManager,
    SessionData,
    SessionScope,
    session_manager,
    st_set_session_value,
    st_get_session_value,
    st_set_preference,
    st_get_preference,
    st_clear_session,
    st_get_session_info,
    SessionContext,
    with_session
)

from .cache_manager import (
    CacheManager,
    CacheLevel,
    CacheStrategy,
    MultiLevelCache,
    cache_manager,
    cached,
    get_cached,
    set_cached,
    clear_cache_by_tags,
    get_cache_stats
)

from .state_synchronizer import (
    StateSynchronizer,
    StateScope as SyncStateScope,
    StateChange,
    SyncOperation,
    ConflictResolution,
    state_synchronizer,
    start_state_sync,
    stop_state_sync,
    get_sync_state,
    set_sync_state,
    watch_sync_state,
    get_sync_stats,
    StateContext,
    st_sync_state,
    st_set_sync_state
)

__all__ = [
    # Session Management
    'SessionManager', 'SessionData', 'SessionScope', 'session_manager',
    'st_set_session_value', 'st_get_session_value', 'st_set_preference',
    'st_get_preference', 'st_clear_session', 'st_get_session_info',
    'SessionContext', 'with_session',
    
    # Cache Management
    'CacheManager', 'CacheLevel', 'CacheStrategy', 'MultiLevelCache',
    'cache_manager', 'cached', 'get_cached', 'set_cached',
    'clear_cache_by_tags', 'get_cache_stats',
    
    # State Synchronization
    'StateSynchronizer', 'SyncStateScope', 'StateChange', 'SyncOperation',
    'ConflictResolution', 'state_synchronizer', 'start_state_sync',
    'stop_state_sync', 'get_sync_state', 'set_sync_state', 'watch_sync_state',
    'get_sync_stats', 'StateContext', 'st_sync_state', 'st_set_sync_state'
]

# Initialize state management components
def initialize_state_management():
    """Initialize all state management components."""
    try:
        # Session manager is already initialized as singleton
        logger.info("Session manager initialized")
        
        # Cache manager is already initialized as singleton
        logger.info("Cache manager initialized")
        
        # State synchronizer needs to be started explicitly
        # This is typically done in the main application
        logger.info("State management components ready for initialization")
        
    except Exception as e:
        logger.error(f"Error initializing state management: {e}")


# Cleanup function
def cleanup_state_management():
    """Cleanup state management resources."""
    try:
        # Shutdown cache manager
        cache_manager.shutdown()
        logger.info("Cache manager shutdown")
        
        # Note: State synchronizer and session manager cleanup
        # should be handled by the main application
        logger.info("State management cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during state management cleanup: {e}")


# Set up logging
import logging
logger = logging.getLogger(__name__)
