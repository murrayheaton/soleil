"""
Tests for the Sync module.

This module tests the synchronization functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone
import asyncio

from modules.sync.services.sync_engine import (
    SyncEngine, SyncEvent, SyncEventType, SyncEngineError
)
from modules.sync.services.file_synchronizer import FileSynchronizer, SynchronizationError
from modules.sync.services.websocket_manager import WebSocketManager
from modules.sync.services.event_broadcaster import EventBroadcaster, BroadcastEventType
from modules.sync.models.sync_state import SyncStatus, SyncOperation, GoogleService


class TestSyncEngine:
    """Test SyncEngine functionality."""

    @pytest.fixture
    def websocket_manager(self):
        """Create mock WebSocketManager."""
        return Mock(spec=WebSocketManager)

    @pytest.fixture
    def sync_engine(self, websocket_manager):
        """Create SyncEngine instance."""
        return SyncEngine(
            websocket_manager=websocket_manager,
            max_concurrent_syncs=3,
            batch_size=10
        )

    @pytest.mark.asyncio
    async def test_start_stop_engine(self, sync_engine):
        """Test starting and stopping the sync engine."""
        # Start engine
        await sync_engine.start()
        assert sync_engine._running is True
        
        # Stop engine
        await sync_engine.stop()
        assert sync_engine._running is False

    @pytest.mark.asyncio
    async def test_handle_webhook(self, sync_engine):
        """Test handling webhook data."""
        webhook_data = {
            'resourceId': 'file123',
            'resourceState': 'update'
        }
        
        # Start engine to process events
        await sync_engine.start()
        
        # Handle webhook
        await sync_engine.handle_webhook(webhook_data)
        
        # Check that event was queued
        assert sync_engine._sync_queue.qsize() > 0
        
        # Stop engine
        await sync_engine.stop()

    @pytest.mark.asyncio
    async def test_trigger_full_sync(self, sync_engine):
        """Test triggering a full sync."""
        band_id = 1
        credentials = Mock()
        
        # Start engine
        await sync_engine.start()
        
        # Trigger full sync
        operation_id = await sync_engine.trigger_full_sync(band_id, credentials)
        
        assert operation_id.startswith(f'full_sync_{band_id}_')
        assert sync_engine._sync_queue.qsize() > 0
        
        # Stop engine
        await sync_engine.stop()

    def test_parse_webhook_data_drive(self, sync_engine):
        """Test parsing Google Drive webhook data."""
        webhook_data = {
            'resourceId': 'file123',
            'resourceState': 'update'
        }
        
        event = sync_engine._parse_webhook_data(webhook_data)
        
        assert event is not None
        assert event.event_type == SyncEventType.FILE_UPDATED
        assert event.resource_id == 'file123'
        assert event.resource_type == 'drive_file'

    def test_parse_webhook_data_sheets(self, sync_engine):
        """Test parsing Google Sheets webhook data."""
        webhook_data = {
            'eventType': 'update',
            'spreadsheetId': 'sheet123'
        }
        
        event = sync_engine._parse_webhook_data(webhook_data)
        
        assert event is not None
        assert event.event_type == SyncEventType.SHEET_UPDATED
        assert event.resource_id == 'sheet123'
        assert event.resource_type == 'sheet'

    def test_get_stats(self, sync_engine):
        """Test getting sync engine statistics."""
        stats = sync_engine.get_stats()
        
        assert 'events_processed' in stats
        assert 'events_failed' in stats
        assert 'files_synced' in stats
        assert 'active_syncs' in stats
        assert 'running' in stats


class TestFileSynchronizer:
    """Test FileSynchronizer functionality."""

    @pytest.fixture
    def mock_drive_service(self):
        """Create mock GoogleDriveService."""
        service = Mock()
        service.credentials = Mock()
        return service

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def file_synchronizer(self, mock_drive_service, mock_db_session):
        """Create FileSynchronizer instance."""
        return FileSynchronizer(
            drive_service=mock_drive_service,
            db_session=mock_db_session
        )

    @pytest.mark.asyncio
    async def test_sync_source_to_user_folders(self, file_synchronizer, mock_drive_service):
        """Test syncing files from source to user folders."""
        source_folder_id = 'source123'
        
        # Mock source files
        mock_drive_service.process_files_for_sync = AsyncMock(return_value=[
            {'id': 'file1', 'filename': 'Song1_Bb.pdf'},
            {'id': 'file2', 'filename': 'Song2_Bb.pdf'}
        ])
        
        # Mock users
        mock_users = [Mock(id=1, user_folder=Mock())]
        file_synchronizer._get_users_for_sync = AsyncMock(return_value=mock_users)
        file_synchronizer._sync_user_folder = AsyncMock(return_value={
            'shortcuts_created': 2,
            'shortcuts_deleted': 0
        })
        
        # Execute sync
        result = await file_synchronizer.sync_source_to_user_folders(source_folder_id)
        
        assert result['users_processed'] == 1
        assert result['files_processed'] == 2
        assert result['total_shortcuts_created'] == 2

    @pytest.mark.asyncio
    async def test_sync_single_user(self, file_synchronizer, mock_db_session):
        """Test syncing for a single user."""
        user_id = 1
        source_folder_id = 'source123'
        
        # Mock user
        mock_user = Mock(id=user_id, user_folder=Mock())
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Mock sync operation
        file_synchronizer._sync_user_folder = AsyncMock(return_value={
            'shortcuts_created': 5,
            'shortcuts_deleted': 0,
            'status': 'success'
        })
        
        # Execute sync
        result = await file_synchronizer.sync_single_user(user_id, source_folder_id)
        
        assert result['shortcuts_created'] == 5
        assert result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_detect_file_changes(self, file_synchronizer, mock_db_session):
        """Test detecting and processing file changes from webhook."""
        webhook_data = {
            'resourceId': 'folder123',
            'resourceState': 'update'
        }
        
        # Mock user folders
        mock_user_folders = [Mock(user_id=1), Mock(user_id=2)]
        mock_db_session.execute = AsyncMock()
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = mock_user_folders
        
        # Mock sync operation
        file_synchronizer.sync_source_to_user_folders = AsyncMock(return_value={
            'users_processed': 2
        })
        
        # Process webhook
        result = await file_synchronizer.detect_file_changes(webhook_data)
        
        assert result['status'] == 'sync_triggered'
        assert result['affected_users'] == 2

    def test_get_sync_stats(self, file_synchronizer):
        """Test getting sync statistics."""
        stats = file_synchronizer.get_sync_stats()
        
        assert 'users_synced' in stats
        assert 'files_processed' in stats
        assert 'shortcuts_created' in stats
        assert 'errors' in stats


class TestWebSocketManager:
    """Test WebSocketManager functionality."""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocketManager instance."""
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_connect_disconnect(self, websocket_manager):
        """Test WebSocket connection and disconnection."""
        mock_websocket = Mock()
        band_id = 1
        
        # Connect
        connection_id = await websocket_manager.connect(mock_websocket, band_id)
        assert connection_id is not None
        assert connection_id in websocket_manager._connections
        
        # Disconnect
        await websocket_manager.disconnect(connection_id)
        assert connection_id not in websocket_manager._connections

    @pytest.mark.asyncio
    async def test_broadcast_to_band(self, websocket_manager):
        """Test broadcasting message to band members."""
        # Create mock connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        band_id = 1
        
        # Connect two clients for the same band
        conn_id1 = await websocket_manager.connect(mock_ws1, band_id)
        conn_id2 = await websocket_manager.connect(mock_ws2, band_id)
        
        # Broadcast message
        message = {'type': 'test', 'data': 'hello'}
        await websocket_manager.broadcast_to_band(band_id, message)
        
        # Both connections should receive the message
        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_called_once()

    def test_get_stats(self, websocket_manager):
        """Test getting WebSocket statistics."""
        stats = websocket_manager.get_stats()
        
        assert 'total_connections' in stats
        assert 'connections_by_band' in stats
        assert 'messages_sent' in stats


class TestEventBroadcaster:
    """Test EventBroadcaster functionality."""

    @pytest.fixture
    def websocket_manager(self):
        """Create mock WebSocketManager."""
        return AsyncMock(spec=WebSocketManager)

    @pytest.fixture
    def event_broadcaster(self, websocket_manager):
        """Create EventBroadcaster instance."""
        return EventBroadcaster(websocket_manager=websocket_manager)

    @pytest.mark.asyncio
    async def test_broadcast_sync_started(self, event_broadcaster):
        """Test broadcasting sync started event."""
        band_id = 1
        sync_type = 'full_sync'
        operation_id = 'op123'
        
        await event_broadcaster.broadcast_sync_started(
            band_id, sync_type, operation_id
        )
        
        # Check event was queued
        assert event_broadcaster._event_queue.qsize() > 0

    @pytest.mark.asyncio
    async def test_broadcast_sync_progress(self, event_broadcaster):
        """Test broadcasting sync progress event."""
        band_id = 1
        operation_id = 'op123'
        progress = 50
        total = 100
        
        await event_broadcaster.broadcast_sync_progress(
            band_id, operation_id, progress, total
        )
        
        # Check event was queued
        assert event_broadcaster._event_queue.qsize() > 0

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, event_broadcaster):
        """Test subscribing and unsubscribing from events."""
        callback = Mock()
        event_type = BroadcastEventType.SYNC_COMPLETED
        
        # Subscribe
        event_broadcaster.subscribe(event_type, callback)
        assert event_type in event_broadcaster._subscribers
        assert callback in event_broadcaster._subscribers[event_type]
        
        # Unsubscribe
        event_broadcaster.unsubscribe(event_type, callback)
        assert callback not in event_broadcaster._subscribers[event_type]

    def test_get_stats(self, event_broadcaster):
        """Test getting broadcaster statistics."""
        stats = event_broadcaster.get_stats()
        
        assert 'events_broadcast' in stats
        assert 'events_failed' in stats
        assert 'queue_size' in stats
        assert 'subscriber_count' in stats


class TestSyncModels:
    """Test sync module models."""

    def test_sync_operation_creation(self):
        """Test creating SyncOperation instance."""
        operation = SyncOperation(
            operation_id='op123',
            band_id=1,
            sync_type='full_sync',
            google_service=GoogleService.DRIVE,
            status=SyncStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc)
        )
        
        assert operation.operation_id == 'op123'
        assert operation.band_id == 1
        assert operation.status == SyncStatus.IN_PROGRESS

    def test_sync_status_enum(self):
        """Test SyncStatus enum values."""
        assert SyncStatus.PENDING.value == 'pending'
        assert SyncStatus.IN_PROGRESS.value == 'in_progress'
        assert SyncStatus.COMPLETED.value == 'completed'
        assert SyncStatus.FAILED.value == 'failed'
        assert SyncStatus.STALE.value == 'stale'