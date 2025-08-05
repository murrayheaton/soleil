# Socket.IO Documentation for SOLEil

## Overview
SOLEil uses Socket.IO for real-time communication between the frontend and backend, enabling live updates for collaborative features.

## Current Implementation

### Backend Setup
- **Location**: `/band-platform/backend/modules/sync/`
- **Framework**: python-socketio with FastAPI
- **Transport**: WebSocket with HTTP long-polling fallback

### Frontend Setup
- **Location**: `/band-platform/frontend/src/lib/websocket.ts`
- **Client Version**: socket.io-client v4.8.1
- **Auto-reconnect**: Enabled with exponential backoff

## Connection Management

### Backend Configuration
```python
# In sync module initialization
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["https://solepower.live"],
    logger=True,
    engineio_logger=True
)

# Mount to FastAPI
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
```

### Frontend Connection
```typescript
import { io } from 'socket.io-client';

const socket = io(process.env.NEXT_PUBLIC_WS_URL || 'https://solepower.live', {
    path: '/socket.io/',
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000
});
```

## Event System

### Core Events

#### Authentication
```python
@sio.event
async def authenticate(sid, data):
    """Authenticate WebSocket connection with JWT token"""
    token = data.get('token')
    # Validate token and store user session
```

#### Room Management
```python
@sio.event
async def join_room(sid, room):
    """Join a specific room for targeted broadcasts"""
    await sio.enter_room(sid, room)
    
@sio.event
async def leave_room(sid, room):
    """Leave a room"""
    await sio.leave_room(sid, room)
```

### Custom Events for SOLEil

#### Content Updates
```python
# Backend emission
await sio.emit('content_updated', {
    'type': 'repertoire',
    'action': 'add',
    'data': song_data
}, room=user_id)

# Frontend listener
socket.on('content_updated', (data) => {
    // Update local state
    updateRepertoire(data);
});
```

#### Sync Status
```python
# Backend
await sio.emit('sync_status', {
    'status': 'syncing' | 'completed' | 'error',
    'progress': 0-100,
    'message': 'Syncing files...'
})

# Frontend
socket.on('sync_status', (status) => {
    updateSyncUI(status);
});
```

## Error Handling

### Connection Errors
```typescript
socket.on('connect_error', (error) => {
    console.error('Connection failed:', error.message);
    // Implement retry logic or user notification
});

socket.on('disconnect', (reason) => {
    if (reason === 'io server disconnect') {
        // Server initiated disconnect, try reconnect
        socket.connect();
    }
});
```

### Backend Error Handling
```python
@sio.event
async def connect(sid, environ):
    """Handle new connections"""
    try:
        # Validate connection
        await validate_connection(environ)
    except Exception as e:
        await sio.disconnect(sid)
        return False
```

## Performance Optimization

### 1. Message Batching
```python
# Batch multiple updates
updates = []
async def batch_emit():
    if updates:
        await sio.emit('batch_update', updates)
        updates.clear()
```

### 2. Room-based Broadcasting
```python
# Only send to relevant users
await sio.emit('event', data, room=f'band_{band_id}')
```

### 3. Compression
```python
# Enable compression for large payloads
sio = socketio.AsyncServer(
    compression_threshold=1024  # Compress messages > 1KB
)
```

## Security Considerations

### Authentication Flow
1. Client connects with JWT token
2. Server validates token on connection
3. Server associates socket ID with user session
4. All subsequent events are authenticated

### Implementation
```python
connected_users = {}

@sio.event
async def connect(sid, environ, auth):
    """Authenticate on connection"""
    token = auth.get('token') if auth else None
    user = await validate_jwt(token)
    
    if not user:
        await sio.disconnect(sid)
        return False
        
    connected_users[sid] = user
    return True
```

## Testing Socket.IO

### Unit Testing
```python
import pytest
from socketio import AsyncClient

@pytest.mark.asyncio
async def test_websocket_connection():
    client = AsyncClient()
    await client.connect('http://localhost:8000')
    
    # Test authentication
    await client.emit('authenticate', {'token': 'test_token'})
    
    # Test event emission
    received = []
    @client.on('content_updated')
    def on_update(data):
        received.append(data)
    
    # Trigger update
    await client.emit('request_update')
    await client.sleep(1)
    
    assert len(received) > 0
```

### Load Testing
```python
# Using locust for load testing
from locust import HttpUser, task, between
import socketio

class WebSocketUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        self.client = socketio.Client()
        self.client.connect(self.host)
    
    @task
    def send_message(self):
        self.client.emit('test_event', {'data': 'test'})
```

## Common Patterns

### 1. Presence System
```python
# Track online users
@sio.event
async def connect(sid, environ):
    await sio.emit('user_joined', {'user_id': user_id}, skip_sid=sid)

@sio.event
async def disconnect(sid):
    await sio.emit('user_left', {'user_id': user_id})
```

### 2. Real-time Collaboration
```python
# Collaborative editing
@sio.event
async def edit_content(sid, data):
    # Validate and process edit
    result = await process_edit(data)
    
    # Broadcast to all in room except sender
    await sio.emit('content_edited', result, 
                   room=data['room_id'], 
                   skip_sid=sid)
```

### 3. Progress Updates
```python
# Long-running task updates
async def long_task(sid, task_data):
    for i in range(100):
        await sio.emit('progress', {'percent': i}, to=sid)
        await process_chunk(i)
    await sio.emit('complete', {'result': 'success'}, to=sid)
```

## Debugging

### Enable Debug Logging
```python
# Backend
import logging
logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)
```

### Frontend Debugging
```typescript
// Enable debug mode
localStorage.debug = 'socket.io-client:*';

// Monitor all events
socket.onAny((eventName, ...args) => {
    console.log(`Event: ${eventName}`, args);
});
```

## Resources

- [Socket.IO Documentation](https://socket.io/docs/v4/)
- [Python-SocketIO Documentation](https://python-socketio.readthedocs.io/)
- [Socket.IO Client Documentation](https://socket.io/docs/v4/client-api/)
- [Socket.IO Emit Cheatsheet](https://socket.io/docs/v4/emit-cheatsheet/)