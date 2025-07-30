"""
WebSocket API routes for real-time updates.

This module provides WebSocket endpoints for real-time communication
including setlist updates and sync notifications.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    WebSocket connection manager for real-time updates.
    
    Manages active WebSocket connections and handles broadcasting
    of updates to connected clients.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, List[str]] = {}  # user_id -> [connection_ids]
        self.band_connections: Dict[int, List[str]] = {}  # band_id -> [connection_ids]
    
    async def connect(self, websocket: WebSocket, client_id: str, user_id: int, band_id: int):
        """Accept WebSocket connection and register client."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(client_id)
        
        # Track band connections
        if band_id not in self.band_connections:
            self.band_connections[band_id] = []
        self.band_connections[band_id].append(client_id)
        
        logger.info(f"WebSocket client {client_id} connected for user {user_id} in band {band_id}")
    
    def disconnect(self, client_id: str, user_id: int, band_id: int):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from user connections
        if user_id in self.user_connections:
            if client_id in self.user_connections[user_id]:
                self.user_connections[user_id].remove(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove from band connections
        if band_id in self.band_connections:
            if client_id in self.band_connections[band_id]:
                self.band_connections[band_id].remove(client_id)
            if not self.band_connections[band_id]:
                del self.band_connections[band_id]
        
        logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                # Remove broken connection
                if client_id in self.active_connections:
                    del self.active_connections[client_id]
    
    async def send_to_user(self, message: dict, user_id: int):
        """Send message to all connections for a specific user."""
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id].copy():
                await self.send_personal_message(message, client_id)
    
    async def send_to_band(self, message: dict, band_id: int):
        """Send message to all connections for a specific band."""
        if band_id in self.band_connections:
            for client_id in self.band_connections[band_id].copy():
                await self.send_personal_message(message, client_id)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for client_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, client_id)
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "users_connected": len(self.user_connections),
            "bands_with_connections": len(self.band_connections),
            "connections_by_band": {
                band_id: len(connections) 
                for band_id, connections in self.band_connections.items()
            }
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/connect/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Main WebSocket endpoint for real-time updates.
    
    Args:
        websocket: WebSocket connection.
        client_id: Unique client identifier.
    """
    # TODO: In production, extract user_id and band_id from JWT token
    # For now, using placeholder values
    user_id = 1  # Would come from JWT token
    band_id = 1  # Would come from user's band association
    
    await manager.connect(websocket, client_id, user_id, band_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection_established",
            "client_id": client_id,
            "message": "Connected to Band Platform WebSocket",
            "timestamp": "2024-07-23T17:00:00Z"  # Would use actual timestamp
        }, client_id)
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(message, client_id, user_id, band_id)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": "2024-07-23T17:00:00Z"
                }, client_id)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await manager.send_personal_message({
                    "type": "error", 
                    "message": "Error processing message",
                    "timestamp": "2024-07-23T17:00:00Z"
                }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id, user_id, band_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id, user_id, band_id)


async def handle_websocket_message(message: dict, client_id: str, user_id: int, band_id: int):
    """
    Handle incoming WebSocket messages.
    
    Args:
        message: Parsed JSON message from client.
        client_id: Client identifier.
        user_id: User ID.
        band_id: Band ID.
    """
    message_type = message.get("type", "unknown")
    
    if message_type == "ping":
        # Respond to ping with pong
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": "2024-07-23T17:00:00Z"
        }, client_id)
    
    elif message_type == "subscribe":
        # Subscribe to specific updates
        subscription_type = message.get("subscription", "")
        
        if subscription_type == "setlist_updates":
            # TODO: Subscribe to setlist updates
            await manager.send_personal_message({
                "type": "subscription_confirmed",
                "subscription": "setlist_updates",
                "message": "Subscribed to setlist updates",
                "timestamp": "2024-07-23T17:00:00Z"
            }, client_id)
        
        elif subscription_type == "sync_status":
            # TODO: Subscribe to sync status updates
            await manager.send_personal_message({
                "type": "subscription_confirmed",
                "subscription": "sync_status", 
                "message": "Subscribed to sync status updates",
                "timestamp": "2024-07-23T17:00:00Z"
            }, client_id)
    
    elif message_type == "get_stats":
        # Send connection statistics
        stats = manager.get_connection_stats()
        await manager.send_personal_message({
            "type": "stats",
            "data": stats,
            "timestamp": "2024-07-23T17:00:00Z"
        }, client_id)
    
    else:
        # Unknown message type
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": "2024-07-23T17:00:00Z"
        }, client_id)


# Functions for sending updates from other parts of the application

async def notify_setlist_update(band_id: int, setlist_id: int, update_data: dict):
    """
    Notify all band members about setlist updates.
    
    Args:
        band_id: Band ID.
        setlist_id: Setlist ID that was updated.
        update_data: Update information.
    """
    message = {
        "type": "setlist_update",
        "setlist_id": setlist_id,
        "data": update_data,
        "timestamp": "2024-07-23T17:00:00Z"
    }
    
    await manager.send_to_band(message, band_id)
    logger.info(f"Sent setlist update notification to band {band_id}")


async def notify_sync_status(band_id: int, sync_status: dict):
    """
    Notify band members about sync status changes.
    
    Args:
        band_id: Band ID.
        sync_status: Sync status information.
    """
    message = {
        "type": "sync_status_update",
        "data": sync_status,
        "timestamp": "2024-07-23T17:00:00Z"
    }
    
    await manager.send_to_band(message, band_id)
    logger.info(f"Sent sync status notification to band {band_id}")


async def notify_new_content(band_id: int, content_type: str, content_data: dict):
    """
    Notify band members about new content (charts, audio).
    
    Args:
        band_id: Band ID.
        content_type: Type of content (chart, audio).
        content_data: Content information.
    """
    message = {
        "type": "new_content",
        "content_type": content_type,
        "data": content_data,
        "timestamp": "2024-07-23T17:00:00Z"
    }
    
    await manager.send_to_band(message, band_id)
    logger.info(f"Sent new content notification to band {band_id}")


@router.get("/stats", tags=["WebSocket"])
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        Connection statistics for monitoring.
    """
    return manager.get_connection_stats()