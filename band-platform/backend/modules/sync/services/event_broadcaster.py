"""
Event broadcaster for sync module.

This service handles broadcasting sync events to WebSocket connections
and other interested parties.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from .websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class BroadcastEventType(str, Enum):
    """Types of broadcast events."""

    SYNC_STARTED = "sync_started"
    SYNC_PROGRESS = "sync_progress"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    FILE_ADDED = "file_added"
    FILE_UPDATED = "file_updated"
    FILE_REMOVED = "file_removed"
    SETLIST_UPDATED = "setlist_updated"
    CONNECTION_STATUS = "connection_status"


class EventBroadcaster:
    """
    Service for broadcasting sync events to connected clients.

    This service acts as a bridge between the sync engine and WebSocket
    connections, ensuring all clients receive real-time updates.
    """

    def __init__(self, websocket_manager: Optional[WebSocketManager] = None):
        """
        Initialize the event broadcaster.

        Args:
            websocket_manager: WebSocket manager for sending messages.
        """
        self.websocket_manager = websocket_manager
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._subscribers: Dict[str, List[Callable]] = {}

        # Statistics
        self.stats = {
            "events_broadcast": 0,
            "events_failed": 0,
            "total_recipients": 0,
        }

    async def start(self) -> None:
        """Start the event broadcaster."""
        if self._running:
            logger.warning("Event broadcaster already running")
            return

        self._running = True
        logger.info("Starting event broadcaster")

        # Start background task for processing events
        asyncio.create_task(self._process_event_queue())

    async def stop(self) -> None:
        """Stop the event broadcaster."""
        if not self._running:
            return

        logger.info("Stopping event broadcaster")
        self._running = False

    async def broadcast_sync_started(
        self,
        band_id: int,
        sync_type: str,
        operation_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Broadcast that a sync operation has started.

        Args:
            band_id: Band ID for the sync.
            sync_type: Type of sync operation.
            operation_id: Unique operation identifier.
            metadata: Additional metadata about the sync.
        """
        event = {
            "type": BroadcastEventType.SYNC_STARTED,
            "band_id": band_id,
            "sync_type": sync_type,
            "operation_id": operation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        await self._queue_event(event)

    async def broadcast_sync_progress(
        self,
        band_id: int,
        operation_id: str,
        progress: int,
        total: int,
        message: Optional[str] = None,
    ) -> None:
        """
        Broadcast sync progress update.

        Args:
            band_id: Band ID for the sync.
            operation_id: Unique operation identifier.
            progress: Current progress count.
            total: Total items to process.
            message: Optional progress message.
        """
        event = {
            "type": BroadcastEventType.SYNC_PROGRESS,
            "band_id": band_id,
            "operation_id": operation_id,
            "progress": progress,
            "total": total,
            "percentage": round((progress / total * 100) if total > 0 else 0, 1),
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._queue_event(event)

    async def broadcast_sync_completed(
        self, band_id: int, operation_id: str, results: Dict[str, Any]
    ) -> None:
        """
        Broadcast that a sync operation has completed.

        Args:
            band_id: Band ID for the sync.
            operation_id: Unique operation identifier.
            results: Results of the sync operation.
        """
        event = {
            "type": BroadcastEventType.SYNC_COMPLETED,
            "band_id": band_id,
            "operation_id": operation_id,
            "results": results,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._queue_event(event)

    async def broadcast_sync_failed(
        self,
        band_id: int,
        operation_id: str,
        error: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Broadcast that a sync operation has failed.

        Args:
            band_id: Band ID for the sync.
            operation_id: Unique operation identifier.
            error: Error message.
            error_details: Additional error details.
        """
        event = {
            "type": BroadcastEventType.SYNC_FAILED,
            "band_id": band_id,
            "operation_id": operation_id,
            "error": error,
            "error_details": error_details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._queue_event(event)

    async def broadcast_file_change(
        self, band_id: int, change_type: str, file_data: Dict[str, Any]
    ) -> None:
        """
        Broadcast a file change event.

        Args:
            band_id: Band ID.
            change_type: Type of change (added, updated, removed).
            file_data: File information.
        """
        event_type_map = {
            "added": BroadcastEventType.FILE_ADDED,
            "updated": BroadcastEventType.FILE_UPDATED,
            "removed": BroadcastEventType.FILE_REMOVED,
        }

        event = {
            "type": event_type_map.get(change_type, BroadcastEventType.FILE_UPDATED),
            "band_id": band_id,
            "file": file_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._queue_event(event)

    async def broadcast_setlist_update(
        self, band_id: int, setlist_id: int, update_data: Dict[str, Any]
    ) -> None:
        """
        Broadcast a setlist update.

        Args:
            band_id: Band ID.
            setlist_id: Setlist ID.
            update_data: Update information.
        """
        event = {
            "type": BroadcastEventType.SETLIST_UPDATED,
            "band_id": band_id,
            "setlist_id": setlist_id,
            "update": update_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._queue_event(event)

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to specific event types.

        Args:
            event_type: Event type to subscribe to.
            callback: Callback function to call when event occurs.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        Unsubscribe from event types.

        Args:
            event_type: Event type to unsubscribe from.
            callback: Callback function to remove.
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]

    async def _queue_event(self, event: Dict[str, Any]) -> None:
        """Queue an event for broadcasting."""
        await self._event_queue.put(event)

    async def _process_event_queue(self) -> None:
        """Process queued events and broadcast them."""
        while self._running:
            try:
                # Get event with timeout
                try:
                    event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Broadcast event
                await self._broadcast_event(event)

            except Exception as e:
                logger.error(f"Error processing event queue: {e}")
                self.stats["events_failed"] += 1

    async def _broadcast_event(self, event: Dict[str, Any]) -> None:
        """
        Broadcast an event to all relevant recipients.

        Args:
            event: Event to broadcast.
        """
        try:
            event_type = event.get("type")
            band_id = event.get("band_id")

            # Send via WebSocket if available
            if self.websocket_manager and band_id:
                await self.websocket_manager.broadcast_to_band(band_id, event)
                self.stats["events_broadcast"] += 1

            # Call local subscribers
            if event_type in self._subscribers:
                for callback in self._subscribers[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Error in event subscriber: {e}")

            logger.debug(f"Broadcast event: {event_type} to band {band_id}")

        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
            self.stats["events_failed"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get broadcaster statistics."""
        return {
            **self.stats,
            "queue_size": self._event_queue.qsize(),
            "subscriber_count": sum(len(subs) for subs in self._subscribers.values()),
            "running": self._running,
        }

    def reset_stats(self) -> None:
        """Reset broadcaster statistics."""
        self.stats = {
            "events_broadcast": 0,
            "events_failed": 0,
            "total_recipients": 0,
        }


# Global event broadcaster instance
event_broadcaster = EventBroadcaster()


# Convenience functions


async def broadcast_sync_started(
    band_id: int,
    sync_type: str,
    operation_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Broadcast sync started event using global broadcaster."""
    await event_broadcaster.broadcast_sync_started(
        band_id, sync_type, operation_id, metadata
    )


async def broadcast_sync_completed(
    band_id: int, operation_id: str, results: Dict[str, Any]
) -> None:
    """Broadcast sync completed event using global broadcaster."""
    await event_broadcaster.broadcast_sync_completed(band_id, operation_id, results)


async def broadcast_file_change(
    band_id: int, change_type: str, file_data: Dict[str, Any]
) -> None:
    """Broadcast file change event using global broadcaster."""
    await event_broadcaster.broadcast_file_change(band_id, change_type, file_data)
