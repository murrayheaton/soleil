# # Synchronization Module

**Version:** 1.0.0  
**Last Updated:** 2025-08-05  
**Status:** Active

## Purpose and Scope
The Sync module manages real-time synchronization between the backend and frontend clients using WebSocket connections. It handles file change detection, sync state management, and event broadcasting.

## Module Context
This module is responsible for:
- WebSocket connection management
- Real-time event broadcasting
- Sync state tracking
- File change detection
- Conflict resolution
- Offline sync queue management

## Dependencies
- Core module (for EventBus)
- Drive module (for file operations)
- Content module (for content updates)
- External: python-socketio, redis (for scaling)

## API Endpoints (To Be Migrated)
- `WS /ws` - WebSocket connection endpoint
- `POST /api/sync/trigger` - Manually trigger sync
- `GET /api/sync/status` - Get sync status
- `GET /api/sync/history` - Get sync history

## Key Services (To Be Migrated)
- `SyncEngine` - Core synchronization logic
- `WebSocketManager` - WebSocket connection handling
- `ChangeDetector` - File change detection
- `ConflictResolver` - Handle sync conflicts
- `SyncQueue` - Offline sync queue

## Events Published
- `sync.started` - Sync operation started
- `sync.progress` - Sync progress update
- `sync.completed` - Sync finished
- `sync.error` - Sync error occurred
- `client.connected` - Client connected
- `client.disconnected` - Client disconnected

## Events Subscribed
- `drive.file.created` - Broadcast to clients
- `drive.file.updated` - Broadcast to clients
- `drive.file.deleted` - Broadcast to clients
- `content.setlist.updated` - Broadcast to clients

## Testing Strategy
- Mock WebSocket connections
- Test event broadcasting
- Test sync state management
- Test conflict resolution
- Integration tests with multiple clients

## Module-Specific Rules
1. WebSocket connections must be authenticated
2. Events must be delivered in order
3. Sync state must be persistent
4. Conflicts must be resolved deterministically
5. Offline changes must be queued properly