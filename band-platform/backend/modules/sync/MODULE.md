# Sync Module

## Overview
The Sync module orchestrates real-time synchronization between Google Workspace services (Drive, Sheets, Calendar) and the band platform, providing webhook processing, WebSocket broadcasting, and comprehensive sync management.

## Architecture

### Services
- **SyncEngine**: Core orchestration service managing sync operations and webhook processing
- **FileSynchronizer**: Handles file synchronization between source and user folders
- **WebSocketManager**: Manages real-time WebSocket connections for live updates
- **EventBroadcaster**: Broadcasts sync events to connected clients

### Models
- **SyncOperation**: Tracks sync operations with detailed metrics
- **SyncItem**: Individual items processed during sync
- **WebhookEvent**: Webhook notifications from Google APIs
- **SyncConfiguration**: Per-band sync settings and preferences

### API Routes
- `/sync/status`: Get sync status and health checks
- `/sync/trigger`: Manually trigger sync operations
- `/sync/operations`: View sync operation history
- `/sync/webhook/*`: Webhook endpoints for Google services
- `/ws/connect/*`: WebSocket connection endpoints

## Key Features

### 1. Real-time Synchronization
- Webhook-based instant updates from Google services
- Delta sync for efficient incremental updates
- Full sync for initial setup or recovery
- Automatic retry with exponential backoff

### 2. WebSocket Broadcasting
- Real-time updates to connected clients
- Per-band and per-user message routing
- Connection management with automatic cleanup
- Event subscription system

### 3. Sync Operation Tracking
- Detailed operation logging and metrics
- Item-level tracking for debugging
- Performance statistics and monitoring
- Error tracking and recovery

### 4. Flexible Configuration
- Per-band sync settings
- Configurable sync intervals
- File type filtering
- Rate limiting controls

## Dependencies
- **Drive Module**: For Google Drive operations
- **Content Module**: For content parsing and file processing
- **Auth Module**: For user and band management

## Usage Examples

### Starting the Sync Engine
```python
from modules.sync import start_sync_engine, websocket_manager

await start_sync_engine(websocket_manager)
```

### Triggering Manual Sync
```python
from modules.sync import trigger_full_sync

operation_id = await trigger_full_sync(
    band_id=1,
    credentials=user_credentials
)
```

### Handling Webhooks
```python
from modules.sync import handle_webhook

await handle_webhook(webhook_data)
```

### Broadcasting Events
```python
from modules.sync import broadcast_sync_completed

await broadcast_sync_completed(
    band_id=1,
    operation_id="op_123",
    results={"files_synced": 42}
)
```

## Sync Flow

1. **Webhook Reception**: Google sends notification of changes
2. **Event Queuing**: Events queued for processing
3. **Sync Execution**: Files fetched and processed
4. **Database Update**: Local records updated
5. **Broadcasting**: Updates sent via WebSocket
6. **Completion**: Operation marked complete

## Performance Considerations
- Concurrent sync operations with semaphore control
- Batch processing for efficiency
- Queue-based architecture prevents overload
- Automatic cleanup of stale operations

## Monitoring

### Health Checks
```python
GET /sync/health
{
    "is_healthy": true,
    "google_drive_accessible": true,
    "webhook_endpoint_active": true,
    "pending_operations": 2
}
```

### Statistics
```python
GET /sync/stats
{
    "events_processed": 1234,
    "files_synced": 5678,
    "active_syncs": 2,
    "last_sync": "2024-07-23T12:00:00Z"
}
```

## Error Handling
- Automatic retry for transient failures
- Dead letter queue for persistent failures
- Detailed error logging with context
- Recovery mechanisms for interrupted syncs

## Security
- Webhook signature verification
- Secure credential handling
- Band-level access control
- Rate limiting to prevent abuse

## Future Enhancements
- [ ] Conflict resolution strategies
- [ ] Offline sync capabilities
- [ ] Multi-source aggregation
- [ ] Advanced filtering rules
- [ ] Sync scheduling with cron expressions