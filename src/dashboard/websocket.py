"""
WebSocket connection manager for the AutoJobAgent Dashboard.

This module handles WebSocket connections for real-time dashboard updates,
including connection management and message broadcasting functionality.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

# Set up logging
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time dashboard updates.
    
    Provides functionality for connecting, disconnecting, and broadcasting
    messages to all connected clients.
    """
    
    def __init__(self):
        """Initialize the connection manager with empty connection list."""
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, client_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to accept
            client_info: Optional metadata about the client
            
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            # Store client metadata
            metadata = {
                "connected_at": datetime.now().isoformat(),
                "client_info": client_info or {},
                "messages_sent": 0
            }
            self.connection_metadata[websocket] = metadata
            
            logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")
            
            # Send welcome message
            await self._send_to_connection(websocket, {
                "type": "connection_established",
                "timestamp": datetime.now().isoformat(),
                "connection_id": id(websocket)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection: {e}")
            return False

    def disconnect(self, websocket: WebSocket) -> bool:
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            
        Returns:
            True if connection was removed, False if not found
        """
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                
                # Clean up metadata
                if websocket in self.connection_metadata:
                    del self.connection_metadata[websocket]
                
                logger.info(f"WebSocket connection removed. Total connections: {len(self.active_connections)}")
                return True
            else:
                logger.warning("Attempted to remove non-existent WebSocket connection")
                return False
                
        except Exception as e:
            logger.error(f"Error removing WebSocket connection: {e}")
            return False

    async def broadcast(self, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Dictionary containing message data
            
        Returns:
            Number of clients that successfully received the message
        """
        if not self.active_connections:
            logger.debug("No active connections for broadcast")
            return 0
        
        successful_sends = 0
        failed_connections = []
        
        # Add timestamp to message
        message_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            **message
        }
        
        for connection in self.active_connections:
            try:
                await self._send_to_connection(connection, message_with_timestamp)
                successful_sends += 1
                
                # Update metadata
                if connection in self.connection_metadata:
                    self.connection_metadata[connection]["messages_sent"] += 1
                    
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket connection: {e}")
                failed_connections.append(connection)
        
        # Clean up failed connections
        for failed_connection in failed_connections:
            self.disconnect(failed_connection)
        
        if successful_sends > 0:
            logger.debug(f"Broadcast message sent to {successful_sends} clients")
        
        return successful_sends

    async def send_to_client(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            websocket: Target WebSocket connection
            message: Dictionary containing message data
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if websocket not in self.active_connections:
            logger.warning("Attempted to send message to inactive connection")
            return False
        
        try:
            message_with_timestamp = {
                "timestamp": datetime.now().isoformat(),
                **message
            }
            
            await self._send_to_connection(websocket, message_with_timestamp)
            
            # Update metadata
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["messages_sent"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to specific client: {e}")
            self.disconnect(websocket)
            return False

    async def _send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            websocket: Target WebSocket connection
            message: Message to send
            
        Raises:
            Exception: If sending fails
        """
        await websocket.send_json(message)

    def get_connection_count(self) -> int:
        """
        Get the number of active connections.
        
        Returns:
            Number of active WebSocket connections
        """
        return len(self.active_connections)

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about WebSocket connections.
        
        Returns:
            Dictionary containing connection statistics
        """
        total_messages = sum(
            meta.get("messages_sent", 0) 
            for meta in self.connection_metadata.values()
        )
        
        return {
            "active_connections": len(self.active_connections),
            "total_messages_sent": total_messages,
            "average_messages_per_connection": (
                total_messages / len(self.active_connections) 
                if self.active_connections else 0
            ),
            "connection_metadata": {
                str(id(ws)): meta 
                for ws, meta in self.connection_metadata.items()
            }
        }


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint handler for dashboard connections.
    
    Args:
        websocket: WebSocket connection to handle
        
    Note:
        Handles connection lifecycle and basic message processing.
        Currently implements one-way broadcasting from server to client.
    """
    connection_id = id(websocket)
    logger.info(f"New WebSocket connection attempt: {connection_id}")
    
    # Accept the connection
    success = await manager.connect(websocket, {"connection_id": connection_id})
    
    if not success:
        logger.error(f"Failed to establish WebSocket connection: {connection_id}")
        return
    
    try:
        while True:
            # Wait for incoming messages
            data = await websocket.receive_text()
            
            try:
                # Parse incoming message
                message = json.loads(data)
                logger.debug(f"Received WebSocket message: {message}")
                
                # Process different message types
                message_type = message.get("type", "unknown")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_to_client(websocket, {
                        "type": "pong",
                        "original_timestamp": message.get("timestamp")
                    })
                    
                elif message_type == "subscribe":
                    # Handle subscription requests (future enhancement)
                    await manager.send_to_client(websocket, {
                        "type": "subscription_ack",
                        "subscribed_to": message.get("topics", [])
                    })
                    
                else:
                    # Log unknown message types
                    logger.warning(f"Unknown WebSocket message type: {message_type}")
                    
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from WebSocket: {data}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection {connection_id}: {e}")
    finally:
        # Clean up connection
        manager.disconnect(websocket)
        logger.info(f"WebSocket connection cleanup completed: {connection_id}")
