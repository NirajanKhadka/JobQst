"""
Event Manager

This module provides event management capabilities for the dashboard.
It handles event registration, publishing, and subscription management
for system-wide events.
"""

import asyncio
import logging
import threading
import uuid
from typing import Dict, List, Set, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import weakref
import json

# Set up logging
logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class EventCategory(Enum):
    """Event categories."""
    SYSTEM = "system"
    JOB_PROCESSING = "job_processing"
    USER_ACTION = "user_action"
    APPLICATION = "application"
    HEALTH = "health"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class Event:
    """Represents a system event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    category: EventCategory = EventCategory.SYSTEM
    priority: EventPriority = EventPriority.MEDIUM
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'category': self.category.value,
            'priority': self.priority.value,
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'tags': list(self.tags)
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            event_id=data.get('event_id', str(uuid.uuid4())),
            event_type=data.get('event_type', ''),
            category=EventCategory(data.get('category', 'system')),
            priority=EventPriority(data.get('priority', 2)),
            data=data.get('data', {}),
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            source=data.get('source', 'unknown'),
            tags=set(data.get('tags', []))
        )


class EventSubscription:
    """Represents an event subscription."""
    
    def __init__(self,
                 callback: Callable[[Event], None],
                 event_types: Optional[List[str]] = None,
                 categories: Optional[List[EventCategory]] = None,
                 priorities: Optional[List[EventPriority]] = None,
                 tags: Optional[List[str]] = None,
                 filter_func: Optional[Callable[[Event], bool]] = None):
        """
        Initialize event subscription.
        
        Args:
            callback: Function to call when matching event occurs
            event_types: List of event types to match (None = all)
            categories: List of categories to match (None = all)
            priorities: List of priorities to match (None = all)
            tags: List of tags to match (None = all)
            filter_func: Custom filter function
        """
        self.subscription_id = str(uuid.uuid4())
        self.callback = callback
        self.event_types = set(event_types) if event_types else None
        self.categories = set(categories) if categories else None
        self.priorities = set(priorities) if priorities else None
        self.tags = set(tags) if tags else None
        self.filter_func = filter_func
        self.created_at = datetime.now()
        self.call_count = 0
        self.last_called = None
    
    def matches(self, event: Event) -> bool:
        """Check if event matches subscription criteria."""
        # Check event types
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check categories
        if self.categories and event.category not in self.categories:
            return False
        
        # Check priorities
        if self.priorities and event.priority not in self.priorities:
            return False
        
        # Check tags (event must have at least one matching tag)
        if self.tags and not self.tags.intersection(event.tags):
            return False
        
        # Check custom filter
        if self.filter_func and not self.filter_func(event):
            return False
        
        return True
    
    def notify(self, event: Event) -> bool:
        """Notify subscriber about event."""
        try:
            self.callback(event)
            self.call_count += 1
            self.last_called = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error in event callback {self.subscription_id}: {e}")
            return False


class EventHistory:
    """Manages event history storage and retrieval."""
    
    def __init__(self, max_events: int = 10000, retention_hours: int = 24):
        self.max_events = max_events
        self.retention_hours = retention_hours
        self.events: deque = deque(maxlen=max_events)
        self.events_by_type: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.events_by_category: Dict[EventCategory, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.Lock()
    
    def add_event(self, event: Event):
        """Add event to history."""
        with self._lock:
            self.events.append(event)
            self.events_by_type[event.event_type].append(event)
            self.events_by_category[event.category].append(event)
    
    def get_events(self,
                   limit: int = 100,
                   event_type: Optional[str] = None,
                   category: Optional[EventCategory] = None,
                   since: Optional[datetime] = None) -> List[Event]:
        """Get events from history with filtering."""
        with self._lock:
            # Choose source collection
            if event_type:
                source = self.events_by_type.get(event_type, deque())
            elif category:
                source = self.events_by_category.get(category, deque())
            else:
                source = self.events
            
            # Filter by time if specified
            events = list(source)
            if since:
                events = [e for e in events if e.timestamp >= since]
            
            # Sort by timestamp (newest first) and limit
            events.sort(key=lambda e: e.timestamp, reverse=True)
            return events[:limit]
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics."""
        with self._lock:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            
            recent_events = [e for e in self.events if e.timestamp >= last_hour]
            
            stats = {
                'total_events': len(self.events),
                'events_last_hour': len(recent_events),
                'events_by_category': {},
                'events_by_priority': {},
                'events_by_type': {}
            }
            
            # Category breakdown
            for category in EventCategory:
                count = len(self.events_by_category.get(category, []))
                stats['events_by_category'][category.value] = count
            
            # Priority breakdown
            for priority in EventPriority:
                count = len([e for e in self.events if e.priority == priority])
                stats['events_by_priority'][priority.name] = count
            
            # Type breakdown (top 10)
            type_counts = {}
            for event_type, events in self.events_by_type.items():
                type_counts[event_type] = len(events)
            
            top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            stats['events_by_type'] = dict(top_types)
            
            return stats
    
    def cleanup_old_events(self):
        """Remove events older than retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self._lock:
            # Clean main events
            while self.events and self.events[0].timestamp < cutoff_time:
                self.events.popleft()
            
            # Clean categorized events
            for event_deque in self.events_by_type.values():
                while event_deque and event_deque[0].timestamp < cutoff_time:
                    event_deque.popleft()
            
            for event_deque in self.events_by_category.values():
                while event_deque and event_deque[0].timestamp < cutoff_time:
                    event_deque.popleft()


class EventManager:
    """Central event management system."""
    
    _instance: Optional['EventManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'EventManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.history = EventHistory()
        self.is_running = False
        self._processing_queue = asyncio.Queue()
        self._processor_task: Optional[asyncio.Task] = None
        
        # Event handlers for common patterns
        self.pattern_handlers: Dict[str, Callable[[Event], None]] = {}
        
        # Metrics
        self.events_published = 0
        self.events_processed = 0
        self.subscription_calls = 0
        
        # Setup default patterns
        self._setup_default_patterns()
    
    def _setup_default_patterns(self):
        """Setup default event patterns and handlers."""
        # Critical error pattern
        def handle_critical_errors(event: Event):
            if event.priority == EventPriority.CRITICAL:
                logger.critical(f"Critical event: {event.event_type} - {event.data}")
        
        # Performance monitoring pattern
        def handle_performance_events(event: Event):
            if event.category == EventCategory.PERFORMANCE:
                if 'response_time' in event.data:
                    response_time = event.data['response_time']
                    if response_time > 5.0:  # Slow response threshold
                        self.publish_event(Event(
                            event_type="slow_response_detected",
                            category=EventCategory.PERFORMANCE,
                            priority=EventPriority.HIGH,
                            data={'original_event': event.event_id, 'response_time': response_time}
                        ))
        
        self.pattern_handlers['critical_errors'] = handle_critical_errors
        self.pattern_handlers['performance_monitoring'] = handle_performance_events
    
    async def start(self):
        """Start the event manager."""
        if self.is_running:
            return
        
        self.is_running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Event manager started")
    
    async def stop(self):
        """Stop the event manager."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event manager stopped")
    
    async def _process_events(self):
        """Process events from the queue."""
        while self.is_running:
            try:
                event = await asyncio.wait_for(self._processing_queue.get(), timeout=1.0)
                await self._handle_event(event)
                self.events_processed += 1
                
            except asyncio.TimeoutError:
                # Periodic cleanup
                self.history.cleanup_old_events()
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: Event):
        """Handle a single event."""
        # Add to history
        self.history.add_event(event)
        
        # Apply pattern handlers
        for handler in self.pattern_handlers.values():
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in pattern handler: {e}")
        
        # Notify subscribers
        failed_subscriptions = []
        
        for subscription in self.subscriptions.values():
            if subscription.matches(event):
                success = subscription.notify(event)
                if success:
                    self.subscription_calls += 1
                else:
                    failed_subscriptions.append(subscription.subscription_id)
        
        # Remove failed subscriptions
        for sub_id in failed_subscriptions:
            self.unsubscribe(sub_id)
            logger.warning(f"Removed failed subscription: {sub_id}")
    
    def publish_event(self, event: Event):
        """Publish an event."""
        if not self.is_running:
            logger.warning("Event manager not running, event dropped")
            return
        
        self.events_published += 1
        
        # Add to processing queue
        try:
            self._processing_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event")
    
    def subscribe(self,
                  callback: Callable[[Event], None],
                  event_types: Optional[List[str]] = None,
                  categories: Optional[List[EventCategory]] = None,
                  priorities: Optional[List[EventPriority]] = None,
                  tags: Optional[List[str]] = None,
                  filter_func: Optional[Callable[[Event], bool]] = None) -> str:
        """
        Subscribe to events.
        
        Returns:
            Subscription ID for unsubscribing
        """
        subscription = EventSubscription(
            callback=callback,
            event_types=event_types,
            categories=categories,
            priorities=priorities,
            tags=tags,
            filter_func=filter_func
        )
        
        self.subscriptions[subscription.subscription_id] = subscription
        logger.info(f"New event subscription: {subscription.subscription_id}")
        
        return subscription.subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Removed subscription: {subscription_id}")
            return True
        return False
    
    def get_events(self, **kwargs) -> List[Event]:
        """Get events from history."""
        return self.history.get_events(**kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event manager statistics."""
        stats = {
            'is_running': self.is_running,
            'events_published': self.events_published,
            'events_processed': self.events_processed,
            'subscription_calls': self.subscription_calls,
            'active_subscriptions': len(self.subscriptions),
            'queue_size': self._processing_queue.qsize() if self._processing_queue else 0
        }
        
        stats.update(self.history.get_event_stats())
        return stats


# Global event manager instance
event_manager = EventManager()


# Convenience functions
async def start_event_manager():
    """Start the global event manager."""
    await event_manager.start()


async def stop_event_manager():
    """Stop the global event manager."""
    await event_manager.stop()


def publish_event(event_type: str,
                  data: Dict[str, Any],
                  category: EventCategory = EventCategory.SYSTEM,
                  priority: EventPriority = EventPriority.MEDIUM,
                  source: str = "unknown",
                  tags: Optional[Set[str]] = None):
    """Publish a new event."""
    event = Event(
        event_type=event_type,
        category=category,
        priority=priority,
        data=data,
        source=source,
        tags=tags or set()
    )
    event_manager.publish_event(event)


def subscribe_to_events(callback: Callable[[Event], None], **kwargs) -> str:
    """Subscribe to events."""
    return event_manager.subscribe(callback, **kwargs)


def unsubscribe_from_events(subscription_id: str) -> bool:
    """Unsubscribe from events."""
    return event_manager.unsubscribe(subscription_id)


def get_recent_events(limit: int = 50) -> List[Event]:
    """Get recent events."""
    return event_manager.get_events(limit=limit)


def get_event_stats() -> Dict[str, Any]:
    """Get event statistics."""
    return event_manager.get_stats()
