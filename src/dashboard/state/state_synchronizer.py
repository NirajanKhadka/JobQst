"""
State Synchronizer

This module provides state synchronization capabilities across multiple
dashboard instances, browser tabs, and user sessions. It handles cross-tab
communication, state conflicts, and ensures consistent state across the
application.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union, AsyncIterable
import hashlib
import weakref

# Set up logging
logger = logging.getLogger(__name__)


class StateScope(Enum):
    """Scope of state synchronization."""
    GLOBAL = "global"        # Synchronized across all instances
    USER = "user"           # Synchronized per user
    SESSION = "session"     # Synchronized per session
    TAB = "tab"            # Local to browser tab


class SyncOperation(Enum):
    """Types of synchronization operations."""
    SET = "set"
    DELETE = "delete"
    MERGE = "merge"
    CLEAR = "clear"
    BATCH = "batch"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE_VALUES = "merge_values"
    CUSTOM = "custom"


@dataclass
class StateChange:
    """Represents a state change operation."""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: SyncOperation = SyncOperation.SET
    scope: StateScope = StateScope.GLOBAL
    key: str = ""
    value: Any = None
    old_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    source_id: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'change_id': self.change_id,
            'operation': self.operation.value,
            'scope': self.scope.value,
            'key': self.key,
            'value': self.value,
            'old_value': self.old_value,
            'timestamp': self.timestamp.isoformat(),
            'source_id': self.source_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateChange':
        """Create from dictionary."""
        return cls(
            change_id=data.get('change_id', str(uuid.uuid4())),
            operation=SyncOperation(data.get('operation', 'set')),
            scope=StateScope(data.get('scope', 'global')),
            key=data.get('key', ''),
            value=data.get('value'),
            old_value=data.get('old_value'),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            source_id=data.get('source_id', ''),
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            metadata=data.get('metadata', {})
        )


class StateStore:
    """Thread-safe state storage with versioning."""
    
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._versions: Dict[str, int] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = threading.RLock()
        self._watchers: Dict[str, Set[Callable]] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        with self._lock:
            return self._state.get(key, default)
    
    def set(self, key: str, value: Any, source_id: str = "") -> StateChange:
        """Set state value and return change."""
        with self._lock:
            old_value = self._state.get(key)
            self._state[key] = value
            self._versions[key] = self._versions.get(key, 0) + 1
            self._timestamps[key] = datetime.now()
            
            change = StateChange(
                operation=SyncOperation.SET,
                key=key,
                value=value,
                old_value=old_value,
                source_id=source_id
            )
            
            # Notify watchers
            self._notify_watchers(key, change)
            
            return change
    
    def delete(self, key: str, source_id: str = "") -> Optional[StateChange]:
        """Delete state value."""
        with self._lock:
            if key in self._state:
                old_value = self._state[key]
                del self._state[key]
                del self._versions[key]
                del self._timestamps[key]
                
                change = StateChange(
                    operation=SyncOperation.DELETE,
                    key=key,
                    old_value=old_value,
                    source_id=source_id
                )
                
                # Notify watchers
                self._notify_watchers(key, change)
                
                return change
        
        return None
    
    def merge(self, key: str, value: Dict[str, Any], source_id: str = "") -> StateChange:
        """Merge dictionary value."""
        with self._lock:
            old_value = self._state.get(key, {})
            
            if isinstance(old_value, dict) and isinstance(value, dict):
                new_value = {**old_value, **value}
            else:
                new_value = value
            
            self._state[key] = new_value
            self._versions[key] = self._versions.get(key, 0) + 1
            self._timestamps[key] = datetime.now()
            
            change = StateChange(
                operation=SyncOperation.MERGE,
                key=key,
                value=new_value,
                old_value=old_value,
                source_id=source_id
            )
            
            # Notify watchers
            self._notify_watchers(key, change)
            
            return change
    
    def clear(self, source_id: str = "") -> StateChange:
        """Clear all state."""
        with self._lock:
            old_state = self._state.copy()
            self._state.clear()
            self._versions.clear()
            self._timestamps.clear()
            
            change = StateChange(
                operation=SyncOperation.CLEAR,
                key="*",
                old_value=old_state,
                source_id=source_id
            )
            
            # Notify all watchers
            for key in old_state:
                self._notify_watchers(key, change)
            
            return change
    
    def get_version(self, key: str) -> int:
        """Get version number for key."""
        with self._lock:
            return self._versions.get(key, 0)
    
    def get_timestamp(self, key: str) -> Optional[datetime]:
        """Get last modified timestamp for key."""
        with self._lock:
            return self._timestamps.get(key)
    
    def keys(self) -> List[str]:
        """Get all keys."""
        with self._lock:
            return list(self._state.keys())
    
    def watch(self, key: str, callback: Callable[[StateChange], None]):
        """Watch for changes to a key."""
        with self._lock:
            if key not in self._watchers:
                self._watchers[key] = set()
            self._watchers[key].add(callback)
    
    def unwatch(self, key: str, callback: Callable[[StateChange], None]):
        """Stop watching changes to a key."""
        with self._lock:
            if key in self._watchers:
                self._watchers[key].discard(callback)
                if not self._watchers[key]:
                    del self._watchers[key]
    
    def _notify_watchers(self, key: str, change: StateChange):
        """Notify watchers of state change."""
        watchers = self._watchers.get(key, set()).copy()
        
        for callback in watchers:
            try:
                callback(change)
            except Exception as e:
                logger.error(f"Error in state watcher callback: {e}")
                # Remove problematic callback
                self._watchers[key].discard(callback)


class SyncChannel(ABC):
    """Abstract base class for synchronization channels."""
    
    @abstractmethod
    async def send_change(self, change: StateChange):
        """Send state change to other instances."""
        pass
    
    @abstractmethod
    async def receive_changes(self) -> AsyncIterable[StateChange]:
        """Receive state changes from other instances."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the sync channel."""
        pass


class LocalSyncChannel(SyncChannel):
    """Local synchronization channel for same-process communication."""
    
    def __init__(self):
        self.subscribers: Set[Callable[[StateChange], None]] = set()
        self._queue: asyncio.Queue = asyncio.Queue()
    
    def subscribe(self, callback: Callable[[StateChange], None]):
        """Subscribe to state changes."""
        self.subscribers.add(callback)
    
    def unsubscribe(self, callback: Callable[[StateChange], None]):
        """Unsubscribe from state changes."""
        self.subscribers.discard(callback)
    
    async def send_change(self, change: StateChange):
        """Send state change to subscribers."""
        # Notify local subscribers
        for callback in self.subscribers.copy():
            try:
                callback(change)
            except Exception as e:
                logger.error(f"Error in sync channel callback: {e}")
                self.subscribers.discard(callback)
        
        # Add to queue for async iteration
        await self._queue.put(change)
    
    async def receive_changes(self):
        """Receive state changes as async iterator."""
        while True:
            try:
                change = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                yield change
            except asyncio.TimeoutError:
                continue
    
    async def close(self):
        """Close the channel."""
        self.subscribers.clear()


class StateSynchronizer:
    """Main state synchronization coordinator."""
    
    def __init__(self, instance_id: Optional[str] = None):
        self.instance_id = instance_id or str(uuid.uuid4())
        self.stores: Dict[StateScope, StateStore] = {
            scope: StateStore() for scope in StateScope
        }
        self.channels: Dict[StateScope, SyncChannel] = {}
        self.conflict_resolvers: Dict[str, Callable] = {}
        self.is_running = False
        self._sync_tasks: List[asyncio.Task] = []
        self._change_history: List[StateChange] = []
        self._max_history = 1000
        
        # Default conflict resolution
        self.default_conflict_resolution = ConflictResolution.LAST_WRITE_WINS
        
        # Setup default sync channels
        self._setup_default_channels()
    
    def _setup_default_channels(self):
        """Setup default synchronization channels."""
        # For now, use local channels for all scopes
        # In a real implementation, you'd have different channels for different scopes
        for scope in StateScope:
            self.channels[scope] = LocalSyncChannel()
    
    async def start(self):
        """Start state synchronization."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start sync tasks for each scope
        for scope, channel in self.channels.items():
            task = asyncio.create_task(self._sync_loop(scope, channel))
            self._sync_tasks.append(task)
        
        logger.info(f"State synchronizer started for instance {self.instance_id}")
    
    async def stop(self):
        """Stop state synchronization."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel sync tasks
        for task in self._sync_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._sync_tasks:
            await asyncio.gather(*self._sync_tasks, return_exceptions=True)
        
        # Close channels
        for channel in self.channels.values():
            await channel.close()
        
        logger.info(f"State synchronizer stopped for instance {self.instance_id}")
    
    async def _sync_loop(self, scope: StateScope, channel: SyncChannel):
        """Main synchronization loop for a scope."""
        try:
            async for change in channel.receive_changes():
                if change.source_id != self.instance_id:
                    await self._apply_remote_change(scope, change)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in sync loop for scope {scope.value}: {e}")
    
    async def _apply_remote_change(self, scope: StateScope, change: StateChange):
        """Apply a remote state change."""
        store = self.stores[scope]
        
        # Check for conflicts
        local_version = store.get_version(change.key)
        local_timestamp = store.get_timestamp(change.key)
        
        if local_timestamp and local_timestamp > change.timestamp:
            # Potential conflict
            resolved_change = await self._resolve_conflict(scope, change, store)
            if resolved_change:
                change = resolved_change
            else:
                logger.debug(f"Conflict resolution rejected change for key {change.key}")
                return
        
        # Apply the change
        if change.operation == SyncOperation.SET:
            store.set(change.key, change.value, self.instance_id)
        elif change.operation == SyncOperation.DELETE:
            store.delete(change.key, self.instance_id)
        elif change.operation == SyncOperation.MERGE:
            store.merge(change.key, change.value, self.instance_id)
        elif change.operation == SyncOperation.CLEAR:
            store.clear(self.instance_id)
        
        # Add to history
        self._add_to_history(change)
    
    async def _resolve_conflict(self, 
                               scope: StateScope, 
                               remote_change: StateChange, 
                               store: StateStore) -> Optional[StateChange]:
        """Resolve state conflict between local and remote changes."""
        local_value = store.get(remote_change.key)
        
        # Check for custom resolver
        resolver_key = f"{scope.value}.{remote_change.key}"
        if resolver_key in self.conflict_resolvers:
            try:
                return self.conflict_resolvers[resolver_key](
                    local_value, remote_change.value, remote_change
                )
            except Exception as e:
                logger.error(f"Error in custom conflict resolver: {e}")
        
        # Apply default resolution strategy
        if self.default_conflict_resolution == ConflictResolution.LAST_WRITE_WINS:
            return remote_change
        elif self.default_conflict_resolution == ConflictResolution.FIRST_WRITE_WINS:
            return None  # Reject remote change
        elif self.default_conflict_resolution == ConflictResolution.MERGE_VALUES:
            if isinstance(local_value, dict) and isinstance(remote_change.value, dict):
                merged_value = {**local_value, **remote_change.value}
                remote_change.value = merged_value
                return remote_change
        
        return remote_change
    
    def _add_to_history(self, change: StateChange):
        """Add change to history."""
        self._change_history.append(change)
        
        # Trim history if it gets too long
        if len(self._change_history) > self._max_history:
            self._change_history = self._change_history[-self._max_history//2:]
    
    # Public API methods
    
    def get_state(self, key: str, scope: StateScope = StateScope.GLOBAL, default: Any = None) -> Any:
        """Get state value."""
        return self.stores[scope].get(key, default)
    
    async def set_state(self, 
                       key: str, 
                       value: Any, 
                       scope: StateScope = StateScope.GLOBAL,
                       sync: bool = True) -> StateChange:
        """Set state value."""
        store = self.stores[scope]
        change = store.set(key, value, self.instance_id)
        change.scope = scope
        
        # Broadcast to other instances
        if sync and scope in self.channels:
            await self.channels[scope].send_change(change)
        
        self._add_to_history(change)
        return change
    
    async def delete_state(self, 
                          key: str, 
                          scope: StateScope = StateScope.GLOBAL,
                          sync: bool = True) -> Optional[StateChange]:
        """Delete state value."""
        store = self.stores[scope]
        change = store.delete(key, self.instance_id)
        
        if change:
            change.scope = scope
            
            # Broadcast to other instances
            if sync and scope in self.channels:
                await self.channels[scope].send_change(change)
            
            self._add_to_history(change)
        
        return change
    
    async def merge_state(self, 
                         key: str, 
                         value: Dict[str, Any], 
                         scope: StateScope = StateScope.GLOBAL,
                         sync: bool = True) -> StateChange:
        """Merge dictionary state value."""
        store = self.stores[scope]
        change = store.merge(key, value, self.instance_id)
        change.scope = scope
        
        # Broadcast to other instances
        if sync and scope in self.channels:
            await self.channels[scope].send_change(change)
        
        self._add_to_history(change)
        return change
    
    def watch_state(self, 
                   key: str, 
                   callback: Callable[[StateChange], None],
                   scope: StateScope = StateScope.GLOBAL):
        """Watch for changes to a state key."""
        self.stores[scope].watch(key, callback)
    
    def unwatch_state(self, 
                     key: str, 
                     callback: Callable[[StateChange], None],
                     scope: StateScope = StateScope.GLOBAL):
        """Stop watching changes to a state key."""
        self.stores[scope].unwatch(key, callback)
    
    def register_conflict_resolver(self, 
                                  scope: StateScope, 
                                  key: str, 
                                  resolver: Callable[[Any, Any, StateChange], Optional[StateChange]]):
        """Register custom conflict resolver for a specific key."""
        resolver_key = f"{scope.value}.{key}"
        self.conflict_resolvers[resolver_key] = resolver
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics."""
        stats = {
            'instance_id': self.instance_id,
            'is_running': self.is_running,
            'history_size': len(self._change_history),
            'stores': {}
        }
        
        for scope, store in self.stores.items():
            stats['stores'][scope.value] = {
                'keys': len(store.keys()),
                'watchers': len(store._watchers)
            }
        
        return stats
    
    def get_change_history(self, 
                          limit: int = 100,
                          scope: Optional[StateScope] = None,
                          key: Optional[str] = None) -> List[StateChange]:
        """Get change history with optional filtering."""
        history = self._change_history
        
        if scope:
            history = [c for c in history if c.scope == scope]
        
        if key:
            history = [c for c in history if c.key == key]
        
        return history[-limit:]


# Global state synchronizer instance
state_synchronizer = StateSynchronizer()


# Convenience functions
async def start_state_sync():
    """Start global state synchronization."""
    await state_synchronizer.start()


async def stop_state_sync():
    """Stop global state synchronization."""
    await state_synchronizer.stop()


def get_sync_state(key: str, scope: StateScope = StateScope.GLOBAL, default: Any = None) -> Any:
    """Get synchronized state value."""
    return state_synchronizer.get_state(key, scope, default)


async def set_sync_state(key: str, value: Any, scope: StateScope = StateScope.GLOBAL) -> StateChange:
    """Set synchronized state value."""
    return await state_synchronizer.set_state(key, value, scope)


def watch_sync_state(key: str, callback: Callable[[StateChange], None], scope: StateScope = StateScope.GLOBAL):
    """Watch for synchronized state changes."""
    state_synchronizer.watch_state(key, callback, scope)


def get_sync_stats() -> Dict[str, Any]:
    """Get synchronization statistics."""
    return state_synchronizer.get_sync_stats()


# Context manager for state operations
class StateContext:
    """Context manager for grouped state operations."""
    
    def __init__(self, scope: StateScope = StateScope.GLOBAL):
        self.scope = scope
        self.changes: List[StateChange] = []
    
    def set(self, key: str, value: Any):
        """Set state value in context."""
        # This would batch the operations
        pass
    
    async def __aenter__(self):
        """Enter async context."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and commit changes."""
        if not exc_type:
            # Commit all changes as a batch
            pass


# Streamlit integration
def st_sync_state(key: str, 
                 default: Any = None, 
                 scope: StateScope = StateScope.SESSION) -> Any:
    """Get synchronized state value for Streamlit."""
    import streamlit as st
    
    # Try to get from local session state first
    if hasattr(st, 'session_state') and key in st.session_state:
        return st.session_state[key]
    
    # Get from synchronized state
    value = get_sync_state(key, scope, default)
    
    # Cache in local session state
    if hasattr(st, 'session_state'):
        st.session_state[key] = value
    
    return value


async def st_set_sync_state(key: str, 
                           value: Any, 
                           scope: StateScope = StateScope.SESSION):
    """Set synchronized state value for Streamlit."""
    import streamlit as st
    
    # Set in local session state
    if hasattr(st, 'session_state'):
        st.session_state[key] = value
    
    # Set in synchronized state
    await set_sync_state(key, value, scope)
