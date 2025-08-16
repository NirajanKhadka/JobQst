"""
Real-time Service

This module provides real-time data streaming capabilities for the dashboard.
It handles live data updates, metrics streaming, and notification delivery.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import queue

# Set up logging
logger = logging.getLogger(__name__)


class DataStreamType(Enum):
    """Types of data streams."""
    JOB_METRICS = "job_metrics"
    SYSTEM_HEALTH = "system_health"
    APPLICATION_STATUS = "application_status"
    SCRAPING_PROGRESS = "scraping_progress"
    ERROR_ALERTS = "error_alerts"
    USER_ACTIVITY = "user_activity"


@dataclass
class StreamMessage:
    """Data structure for stream messages."""
    stream_type: DataStreamType
    data: Dict[str, Any]
    timestamp: datetime
    message_id: str
    priority: int = 1  # 1=low, 2=medium, 3=high
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'stream_type': self.stream_type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id,
            'priority': self.priority
        }


class DataCollector:
    """Collects data from various sources for streaming."""
    
    def __init__(self):
        self.collectors: Dict[DataStreamType, Callable] = {}
        self.collection_intervals: Dict[DataStreamType, int] = {}
        self.last_collection: Dict[DataStreamType, datetime] = {}
    
    def register_collector(self, 
                          stream_type: DataStreamType,
                          collector_func: Callable[[], Dict[str, Any]],
                          interval_seconds: int = 5):
        """
        Register a data collector function.
        
        Args:
            stream_type: Type of data stream
            collector_func: Function that returns data dictionary
            interval_seconds: Collection interval in seconds
        """
        self.collectors[stream_type] = collector_func
        self.collection_intervals[stream_type] = interval_seconds
        self.last_collection[stream_type] = datetime.min
        
        logger.info(f"Registered collector for {stream_type.value} with {interval_seconds}s interval")
    
    def should_collect(self, stream_type: DataStreamType) -> bool:
        """Check if data should be collected for given stream type."""
        if stream_type not in self.collectors:
            return False
        
        now = datetime.now()
        last_time = self.last_collection.get(stream_type, datetime.min)
        interval = self.collection_intervals.get(stream_type, 5)
        
        return (now - last_time).total_seconds() >= interval
    
    def collect_data(self, stream_type: DataStreamType) -> Optional[Dict[str, Any]]:
        """Collect data for specific stream type."""
        if not self.should_collect(stream_type):
            return None
        
        try:
            collector = self.collectors[stream_type]
            data = collector()
            self.last_collection[stream_type] = datetime.now()
            
            logger.debug(f"Collected data for {stream_type.value}: {len(str(data))} chars")
            return data
            
        except Exception as e:
            logger.error(f"Error collecting data for {stream_type.value}: {e}")
            return None
    
    def collect_all_due(self) -> List[StreamMessage]:
        """Collect all data that is due for collection."""
        messages = []
        
        for stream_type in self.collectors:
            data = self.collect_data(stream_type)
            if data:
                message = StreamMessage(
                    stream_type=stream_type,
                    data=data,
                    timestamp=datetime.now(),
                    message_id=f"{stream_type.value}_{int(time.time())}"
                )
                messages.append(message)
        
        return messages


class StreamManager:
    """Manages real-time data streams and subscribers."""
    
    def __init__(self, max_queue_size: int = 1000):
        self.subscribers: Dict[DataStreamType, Set[Callable]] = {}
        self.message_queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_queue_size)
        self.is_running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.data_collector = DataCollector()
        
        # Initialize subscriber sets
        for stream_type in DataStreamType:
            self.subscribers[stream_type] = set()
    
    def subscribe(self, stream_type: DataStreamType, callback: Callable[[StreamMessage], None]):
        """
        Subscribe to a data stream.
        
        Args:
            stream_type: Type of stream to subscribe to
            callback: Function to call when new data arrives
        """
        self.subscribers[stream_type].add(callback)
        logger.info(f"New subscriber for {stream_type.value} stream")
    
    def unsubscribe(self, stream_type: DataStreamType, callback: Callable[[StreamMessage], None]):
        """
        Unsubscribe from a data stream.
        
        Args:
            stream_type: Type of stream to unsubscribe from
            callback: Callback function to remove
        """
        if callback in self.subscribers[stream_type]:
            self.subscribers[stream_type].remove(callback)
            logger.info(f"Removed subscriber from {stream_type.value} stream")
    
    def publish(self, message: StreamMessage):
        """
        Publish a message to subscribers.
        
        Args:
            message: Stream message to publish
        """
        try:
            # Add to queue with priority (lower number = higher priority)
            priority = -message.priority  # Invert for priority queue
            self.message_queue.put((priority, message), timeout=1)
            
        except queue.Full:
            logger.warning("Message queue is full, dropping message")
    
    def _process_messages(self):
        """Process messages from the queue (runs in separate thread)."""
        while self.is_running:
            try:
                # Get message with timeout
                priority, message = self.message_queue.get(timeout=1)
                
                # Notify subscribers
                subscribers = self.subscribers.get(message.stream_type, set())
                for callback in subscribers.copy():  # Copy to avoid modification during iteration
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"Error in subscriber callback: {e}")
                        # Remove problematic callback
                        self.subscribers[message.stream_type].discard(callback)
                
                self.message_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    def _collect_and_publish(self):
        """Collect data and publish messages (runs in separate thread)."""
        while self.is_running:
            try:
                # Collect all due data
                messages = self.data_collector.collect_all_due()
                
                # Publish messages
                for message in messages:
                    self.publish(message)
                
                # Sleep briefly to avoid excessive CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in data collection: {e}")
                time.sleep(1)
    
    def start(self):
        """Start the stream manager."""
        if self.is_running:
            logger.warning("Stream manager is already running")
            return
        
        self.is_running = True
        
        # Start message processing thread
        self.worker_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.worker_thread.start()
        
        # Start data collection thread
        self.collection_thread = threading.Thread(target=self._collect_and_publish, daemon=True)
        self.collection_thread.start()
        
        logger.info("Real-time stream manager started")
    
    def stop(self):
        """Stop the stream manager."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for threads to finish
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        if hasattr(self, 'collection_thread') and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=5)
        
        logger.info("Real-time stream manager stopped")
    
    def get_subscriber_count(self, stream_type: DataStreamType) -> int:
        """Get number of subscribers for a stream type."""
        return len(self.subscribers.get(stream_type, set()))
    
    def get_queue_size(self) -> int:
        """Get current message queue size."""
        return self.message_queue.qsize()


class RealTimeService:
    """Main real-time service orchestrator."""
    
    _instance: Optional['RealTimeService'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'RealTimeService':
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
        self.stream_manager = StreamManager()
        self.is_started = False
        
        # Register default data collectors
        self._register_default_collectors()
    
    def _register_default_collectors(self):
        """Register default data collectors."""
        # Job metrics collector
        def collect_job_metrics():
            return {
                'active_jobs': 42,
                'completed_today': 128,
                'success_rate': 94.5,
                'avg_processing_time': 3.2
            }
        
        # System health collector
        def collect_system_health():
            return {
                'cpu_usage': 45.2,
                'memory_usage': 67.8,
                'disk_usage': 23.1,
                'active_services': ['scraper', 'processor', 'api'],
                'uptime_hours': 72.5
            }
        
        # Application status collector
        def collect_application_status():
            return {
                'total_applications': 234,
                'pending_applications': 45,
                'responses_received': 12,
                'interviews_scheduled': 3
            }
        
        self.stream_manager.data_collector.register_collector(
            DataStreamType.JOB_METRICS, collect_job_metrics, 5
        )
        self.stream_manager.data_collector.register_collector(
            DataStreamType.SYSTEM_HEALTH, collect_system_health, 10
        )
        self.stream_manager.data_collector.register_collector(
            DataStreamType.APPLICATION_STATUS, collect_application_status, 15
        )
    
    def start(self):
        """Start the real-time service."""
        if self.is_started:
            return
        
        self.stream_manager.start()
        self.is_started = True
        logger.info("Real-time service started")
    
    def stop(self):
        """Stop the real-time service."""
        if not self.is_started:
            return
        
        self.stream_manager.stop()
        self.is_started = False
        logger.info("Real-time service stopped")
    
    def subscribe(self, stream_type: DataStreamType, callback: Callable[[StreamMessage], None]):
        """Subscribe to a data stream."""
        self.stream_manager.subscribe(stream_type, callback)
    
    def unsubscribe(self, stream_type: DataStreamType, callback: Callable[[StreamMessage], None]):
        """Unsubscribe from a data stream."""
        self.stream_manager.unsubscribe(stream_type, callback)
    
    def publish_custom_message(self, stream_type: DataStreamType, data: Dict[str, Any], priority: int = 1):
        """Publish a custom message to the stream."""
        message = StreamMessage(
            stream_type=stream_type,
            data=data,
            timestamp=datetime.now(),
            message_id=f"custom_{stream_type.value}_{int(time.time())}",
            priority=priority
        )
        self.stream_manager.publish(message)
    
    def register_data_collector(self, 
                               stream_type: DataStreamType,
                               collector_func: Callable[[], Dict[str, Any]],
                               interval_seconds: int = 5):
        """Register a custom data collector."""
        self.stream_manager.data_collector.register_collector(
            stream_type, collector_func, interval_seconds
        )
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        stats = {
            'is_running': self.is_started,
            'queue_size': self.stream_manager.get_queue_size(),
            'subscriber_counts': {}
        }
        
        for stream_type in DataStreamType:
            stats['subscriber_counts'][stream_type.value] = \
                self.stream_manager.get_subscriber_count(stream_type)
        
        return stats


# Global service instance
real_time_service = RealTimeService()


# Convenience functions
def start_real_time_service():
    """Start the global real-time service."""
    real_time_service.start()


def stop_real_time_service():
    """Stop the global real-time service."""
    real_time_service.stop()


def subscribe_to_stream(stream_type: DataStreamType, callback: Callable[[StreamMessage], None]):
    """Subscribe to a data stream."""
    real_time_service.subscribe(stream_type, callback)


def publish_message(stream_type: DataStreamType, data: Dict[str, Any], priority: int = 1):
    """Publish a message to a stream."""
    real_time_service.publish_custom_message(stream_type, data, priority)


def get_service_stats() -> Dict[str, Any]:
    """Get real-time service statistics."""
    return real_time_service.get_service_stats()
