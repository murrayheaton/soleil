"""
Sync Module

Manages real-time synchronization and WebSocket connections for the band platform.
"""

# Core services
from .services.sync_engine import (
    SyncEngine,
    SyncEvent,
    SyncEventType,
    sync_engine,
    start_sync_engine,
    stop_sync_engine,
    handle_webhook,
    trigger_full_sync,
    trigger_delta_sync,
    get_sync_stats,
)
from .services.websocket_manager import WebSocketManager
from .services.file_synchronizer import FileSynchronizer
from .services.event_broadcaster import (
    EventBroadcaster,
    BroadcastEventType,
    event_broadcaster,
    broadcast_sync_started,
    broadcast_sync_completed,
    broadcast_file_change,
)

# Models
from .models.sync_state import (
    SyncStatus,
    SyncType,
    GoogleService,
    SyncOperation,
    SyncOperationSchema,
    SyncItem,
    SyncItemSchema,
    WebhookEvent,
    WebhookEventSchema,
    SyncConfiguration,
    SyncConfigurationSchema,
)

# API routes
from .api.sync_routes import router as sync_routes
from .api.websocket import router as websocket_routes, manager as websocket_manager

__all__ = [
    # Services
    "SyncEngine",
    "SyncEvent",
    "SyncEventType",
    "sync_engine",
    "start_sync_engine",
    "stop_sync_engine",
    "handle_webhook",
    "trigger_full_sync",
    "trigger_delta_sync",
    "get_sync_stats",
    "WebSocketManager",
    "FileSynchronizer",
    "EventBroadcaster",
    "BroadcastEventType",
    "event_broadcaster",
    "broadcast_sync_started",
    "broadcast_sync_completed",
    "broadcast_file_change",
    # Models
    "SyncStatus",
    "SyncType",
    "GoogleService",
    "SyncOperation",
    "SyncOperationSchema",
    "SyncItem",
    "SyncItemSchema",
    "WebhookEvent",
    "WebhookEventSchema",
    "SyncConfiguration",
    "SyncConfigurationSchema",
    # API
    "sync_routes",
    "websocket_routes",
    "websocket_manager",
]
