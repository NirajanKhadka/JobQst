"""
WebSocket Handler

This module provides WebSocket communication capabilities for real-time 
dashboard updates. It handles client connections, message routing, and
connection management.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Set, Optional, Any, Callable
from datetime import datetime
import weakref
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logging.warning("websockets library not available. WebSocket functionality disabled.")

from .real_time_service import DataStreamType, StreamMessage, real_time_service

# Set up logging
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    DATA_UPDATE = "data_update"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    CONNECTION_STATUS = "connection_status"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    message_type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = None
    client_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_json(self) -> str:
        """Convert to JSON string for transmission."""
        return json.dumps({
            'type': self.message_type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'client_id': self.client_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Create message from JSON string."""
        data = json.loads(json_str)
        return cls(
            message_type=MessageType(data['type']),
            data=data['data'],
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            client_id=data.get('client_id')
        )


class WebSocketClient:
    """Represents a connected WebSocket client."""
    
    def __init__(self, websocket: 'WebSocketServerProtocol', client_id: str = None):
        self.websocket = websocket
        self.client_id = client_id or str(uuid.uuid4())
        self.connected_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.subscriptions: Set[DataStreamType] = set()
        self.is_alive = True
        
        # Client metadata
        self.remote_address = getattr(websocket, 'remote_address', ('unknown', 0))
        self.user_agent = getattr(websocket, 'request_headers', {}).get('user-agent', 'unknown')
    
    async def send_message(self, message: WebSocketMessage):
        """Send message to client."""
        if not self.is_alive:
            return False
        
        try:
            message.client_id = self.client_id
            await self.websocket.send(message.to_json())
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to client {self.client_id}: {e}")
            self.is_alive = False
            return False
    
    async def close(self, code: int = 1000, reason: str = "Normal closure"):
        """Close the WebSocket connection."""
        if self.is_alive:
            try:
                await self.websocket.close(code, reason)
            except Exception as e:
                logger.error(f"Error closing connection for client {self.client_id}: {e}")
            finally:
                self.is_alive = False
    
    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = datetime.now()
    
    def is_stale(self, timeout_seconds: int = 60) -> bool:
        """Check if client connection is stale."""
        return (datetime.now() - self.last_heartbeat).total_seconds() > timeout_seconds
    
    def get_info(self) -> Dict[str, Any]:
        """Get client information."""
        return {
            'client_id': self.client_id,
            'connected_at': self.connected_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'subscriptions': [stream.value for stream in self.subscriptions],
            'remote_address': self.remote_address,
            'user_agent': self.user_agent,
            'is_alive': self.is_alive
        }


class WebSocketHandler:
    """Handles WebSocket connections and message routing."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, WebSocketClient] = {}
        self.server = None
        self.is_running = False
        
        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {
            MessageType.SUBSCRIBE: self._handle_subscribe,
            MessageType.UNSUBSCRIBE: self._handle_unsubscribe,
            MessageType.HEARTBEAT: self._handle_heartbeat
        }
        
        # Subscribe to real-time service for data updates
        self._setup_real_time_subscriptions()
    
    def _setup_real_time_subscriptions(self):
        """Subscribe to all real-time data streams."""
        for stream_type in DataStreamType:
            real_time_service.subscribe(stream_type, self._on_stream_message)
    
    def _on_stream_message(self, message: StreamMessage):
        """Handle incoming stream messages from real-time service."""
        # Convert to WebSocket message
        ws_message = WebSocketMessage(
            message_type=MessageType.DATA_UPDATE,
            data={
                'stream_type': message.stream_type.value,
                'payload': message.data,
                'message_id': message.message_id,
                'priority': message.priority
            },
            timestamp=message.timestamp
        )
        
        # Send to subscribed clients
        asyncio.create_task(self._broadcast_to_subscribers(message.stream_type, ws_message))
    
    async def _broadcast_to_subscribers(self, stream_type: DataStreamType, message: WebSocketMessage):
        """Broadcast message to clients subscribed to a stream type."""
        subscribers = [
            client for client in self.clients.values()
            if stream_type in client.subscriptions and client.is_alive
        ]
        
        if subscribers:
            # Send message to all subscribers
            tasks = [client.send_message(message) for client in subscribers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Clean up failed connections
            for client, result in zip(subscribers, results):
                if not result or isinstance(result, Exception):
                    await self._remove_client(client.client_id)
    
    async def _handle_client_connection(self, websocket: 'WebSocketServerProtocol', path: str):
        """Handle new client connection."""
        client = WebSocketClient(websocket)
        self.clients[client.client_id] = client
        
        logger.info(f"New WebSocket client connected: {client.client_id} from {client.remote_address}")
        
        # Send connection confirmation
        welcome_message = WebSocketMessage(
            message_type=MessageType.CONNECTION_STATUS,
            data={
                'status': 'connected',
                'client_id': client.client_id,
                'server_time': datetime.now().isoformat()
            }
        )
        await client.send_message(welcome_message)
        
        try:
            # Listen for messages
            async for message_str in websocket:
                await self._handle_client_message(client, message_str)
                
        except Exception as e:
            logger.error(f"Error handling client {client.client_id}: {e}")
        
        finally:
            await self._remove_client(client.client_id)
    
    async def _handle_client_message(self, client: WebSocketClient, message_str: str):
        """Handle message from client."""
        try:
            message = WebSocketMessage.from_json(message_str)
            handler = self.message_handlers.get(message.message_type)
            
            if handler:
                await handler(client, message)
            else:
                logger.warning(f"Unknown message type from client {client.client_id}: {message.message_type}")
                
        except Exception as e:
            logger.error(f"Error processing message from client {client.client_id}: {e}")
            
            # Send error response
            error_message = WebSocketMessage(
                message_type=MessageType.ERROR,
                data={'error': str(e), 'original_message': message_str}
            )
            await client.send_message(error_message)
    
    async def _handle_subscribe(self, client: WebSocketClient, message: WebSocketMessage):
        """Handle subscription request."""
        stream_types = message.data.get('stream_types', [])
        
        for stream_type_str in stream_types:
            try:
                stream_type = DataStreamType(stream_type_str)
                client.subscriptions.add(stream_type)
                logger.info(f"Client {client.client_id} subscribed to {stream_type.value}")
                
            except ValueError:
                logger.warning(f"Invalid stream type requested: {stream_type_str}")
        
        # Send confirmation
        response = WebSocketMessage(
            message_type=MessageType.CONNECTION_STATUS,
            data={
                'action': 'subscribed',
                'subscriptions': [s.value for s in client.subscriptions]
            }
        )
        await client.send_message(response)
    
    async def _handle_unsubscribe(self, client: WebSocketClient, message: WebSocketMessage):
        """Handle unsubscription request."""
        stream_types = message.data.get('stream_types', [])
        
        for stream_type_str in stream_types:
            try:
                stream_type = DataStreamType(stream_type_str)
                client.subscriptions.discard(stream_type)
                logger.info(f"Client {client.client_id} unsubscribed from {stream_type.value}")
                
            except ValueError:
                logger.warning(f"Invalid stream type for unsubscribe: {stream_type_str}")
        
        # Send confirmation
        response = WebSocketMessage(
            message_type=MessageType.CONNECTION_STATUS,
            data={
                'action': 'unsubscribed',
                'subscriptions': [s.value for s in client.subscriptions]
            }
        )
        await client.send_message(response)
    
    async def _handle_heartbeat(self, client: WebSocketClient, message: WebSocketMessage):
        """Handle heartbeat message."""
        client.update_heartbeat()
        
        # Send heartbeat response
        response = WebSocketMessage(
            message_type=MessageType.HEARTBEAT,
            data={'server_time': datetime.now().isoformat()}
        )
        await client.send_message(response)
    
    async def _remove_client(self, client_id: str):
        """Remove client from connections."""
        if client_id in self.clients:
            client = self.clients[client_id]
            
            # Unsubscribe from all streams
            client.subscriptions.clear()
            
            # Close connection if still alive
            if client.is_alive:
                await client.close()
            
            # Remove from clients dict
            del self.clients[client_id]
            
            logger.info(f"Removed client: {client_id}")
    
    async def _cleanup_stale_connections(self):
        """Periodically clean up stale connections."""
        while self.is_running:
            try:
                stale_clients = [
                    client_id for client_id, client in self.clients.items()
                    if client.is_stale() or not client.is_alive
                ]
                
                for client_id in stale_clients:
                    await self._remove_client(client_id)
                
                if stale_clients:
                    logger.info(f"Cleaned up {len(stale_clients)} stale connections")
                
                # Wait before next cleanup
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error during connection cleanup: {e}")
                await asyncio.sleep(30)
    
    async def start(self):
        """Start the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("WebSocket server cannot start - websockets library not available")
            return False
        
        if self.is_running:
            logger.warning("WebSocket server is already running")
            return True
        
        try:
            # Start WebSocket server
            self.server = await websockets.serve(
                self._handle_client_connection,
                self.host,
                self.port
            )
            
            self.is_running = True
            
            # Start cleanup task
            asyncio.create_task(self._cleanup_stale_connections())
            
            logger.info(f"WebSocket server started on {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            return False
    
    async def stop(self):
        """Stop the WebSocket server."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Close all client connections
        for client_id in list(self.clients.keys()):
            await self._remove_client(client_id)
        
        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("WebSocket server stopped")
    
    def get_client_count(self) -> int:
        """Get number of connected clients."""
        return len([c for c in self.clients.values() if c.is_alive])
    
    def get_subscription_stats(self) -> Dict[str, int]:
        """Get subscription statistics by stream type."""
        stats = {}
        for stream_type in DataStreamType:
            count = len([
                c for c in self.clients.values()
                if c.is_alive and stream_type in c.subscriptions
            ])
            stats[stream_type.value] = count
        return stats
    
    def get_clients_info(self) -> List[Dict[str, Any]]:
        """Get information about all connected clients."""
        return [client.get_info() for client in self.clients.values() if client.is_alive]


# Global WebSocket handler instance
websocket_handler = WebSocketHandler()


# Convenience functions
async def start_websocket_server(host: str = "localhost", port: int = 8765) -> bool:
    """Start the WebSocket server."""
    websocket_handler.host = host
    websocket_handler.port = port
    return await websocket_handler.start()


async def stop_websocket_server():
    """Stop the WebSocket server."""
    await websocket_handler.stop()


def get_websocket_stats() -> Dict[str, Any]:
    """Get WebSocket server statistics."""
    return {
        'is_running': websocket_handler.is_running,
        'client_count': websocket_handler.get_client_count(),
        'subscription_stats': websocket_handler.get_subscription_stats(),
        'clients': websocket_handler.get_clients_info()
    }
