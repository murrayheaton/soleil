"""
Unit tests for the sync engine service.

This module tests the synchronization engine, webhook processing, 
and real-time update functionality following the PRP requirements.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from google.oauth2.credentials import Credentials

from app.services.sync_engine import (
    SyncEngine,
    SyncEvent,
    SyncEventType,
    SyncEngineError,
    sync_engine,
    start_sync_engine,
    stop_sync_engine,
    handle_webhook,
    trigger_full_sync,
    trigger_delta_sync,
    get_sync_stats
)
from app.services.websocket_manager import WebSocketManager


class TestSyncEvent:
    """Test cases for the SyncEvent dataclass."""
    
    def test_sync_event_creation(self):
        """Test basic sync event creation."""
        event = SyncEvent(
            event_type=SyncEventType.FILE_CREATED,
            resource_id="test_file_123",
            resource_type="drive_file",
            band_id=1
        )
        
        assert event.event_type == SyncEventType.FILE_CREATED
        assert event.resource_id == "test_file_123"
        assert event.resource_type == "drive_file"
        assert event.band_id == 1
        assert event.timestamp is not None
        assert isinstance(event.metadata, dict)
    
    def test_sync_event_with_metadata(self):
        """Test sync event creation with metadata."""
        metadata = {"file_size": 1024, "mime_type": "application/pdf"}
        event = SyncEvent(
            event_type=SyncEventType.FILE_UPDATED,
            resource_id="test_file_456",
            resource_type="drive_file",
            metadata=metadata
        )
        
        assert event.metadata == metadata
    
    def test_sync_event_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated."""
        before = datetime.now(timezone.utc)
        event = SyncEvent(
            event_type=SyncEventType.SHEET_UPDATED,
            resource_id="sheet_123",
            resource_type="sheet"
        )
        after = datetime.now(timezone.utc)
        
        assert before <= event.timestamp <= after


class TestSyncEngine:
    """Test cases for the SyncEngine class."""
    
    @pytest.fixture
    def sync_engine_instance(self):
        """Create a test sync engine instance."""
        return SyncEngine(max_concurrent_syncs=2, batch_size=10)
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Create a mock WebSocket manager."""
        manager = Mock(spec=WebSocketManager)
        manager.broadcast_to_band = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_credentials(self):
        """Create mock Google credentials."""
        return Mock(spec=Credentials)
    
    def test_sync_engine_initialization(self, sync_engine_instance):
        """Test sync engine initialization."""
        engine = sync_engine_instance
        
        assert engine.max_concurrent_syncs == 2
        assert engine.batch_size == 10
        assert not engine._running
        assert len(engine._active_syncs) == 0
        assert engine._sync_queue.qsize() == 0
        assert isinstance(engine.stats, dict)
    
    @pytest.mark.asyncio
    async def test_sync_engine_start_stop(self, sync_engine_instance):
        """Test starting and stopping the sync engine."""
        engine = sync_engine_instance
        
        # Test start
        await engine.start()
        assert engine._running
        
        # Test stop
        await engine.stop()
        assert not engine._running
    
    @pytest.mark.asyncio
    async def test_sync_engine_double_start(self, sync_engine_instance):
        """Test that starting an already running engine doesn't cause issues."""
        engine = sync_engine_instance
        
        await engine.start()
        assert engine._running
        
        # Should not raise an exception
        await engine.start()
        assert engine._running
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_webhook_handling(self, sync_engine_instance):
        """Test webhook data handling."""
        engine = sync_engine_instance
        await engine.start()
        
        # Test Google Drive webhook
        webhook_data = {
            "resourceId": "file_123",
            "resourceState": "sync",
            "eventTime": "2024-07-23T17:00:00Z"
        }
        
        await engine.handle_webhook(webhook_data)
        
        # Event should be queued
        assert engine._sync_queue.qsize() == 1
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_full_sync_trigger(self, sync_engine_instance, mock_credentials):
        """Test triggering a full sync."""
        engine = sync_engine_instance
        await engine.start()
        
        operation_id = await engine.trigger_full_sync(1, mock_credentials)
        
        assert operation_id.startswith("full_sync_1_")
        assert engine._sync_queue.qsize() == 1
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_delta_sync_trigger(self, sync_engine_instance, mock_credentials):
        """Test triggering a delta sync."""
        engine = sync_engine_instance
        await engine.start()
        
        operation_id = await engine.trigger_delta_sync(1, mock_credentials)
        
        assert operation_id.startswith("delta_sync_1_")
        assert engine._sync_queue.qsize() == 1
        
        await engine.stop()
    
    def test_event_handler_registration(self, sync_engine_instance):
        """Test registering event handlers."""
        engine = sync_engine_instance
        
        # Mock handler function
        handler = Mock()
        
        # Register handler
        engine.register_event_handler(SyncEventType.FILE_CREATED, handler)
        
        # Check that handler was registered
        assert SyncEventType.FILE_CREATED in engine._event_handlers
        assert handler in engine._event_handlers[SyncEventType.FILE_CREATED]
    
    @pytest.mark.asyncio
    async def test_event_handler_calling(self, sync_engine_instance):
        """Test that event handlers are called during processing."""
        engine = sync_engine_instance
        
        # Mock handler
        handler = AsyncMock()
        engine.register_event_handler(SyncEventType.FILE_CREATED, handler)
        
        # Create test event
        event = SyncEvent(
            event_type=SyncEventType.FILE_CREATED,
            resource_id="test_file",
            resource_type="drive_file"
        )
        
        # Call event handlers
        await engine._call_event_handlers(event)
        
        # Verify handler was called
        handler.assert_called_once_with(event)
    
    def test_webhook_data_parsing_drive(self, sync_engine_instance):
        """Test parsing Google Drive webhook data."""
        engine = sync_engine_instance
        
        webhook_data = {
            "resourceId": "file_123",
            "resourceState": "sync",
            "eventTime": "2024-07-23T17:00:00Z"
        }
        
        event = engine._parse_webhook_data(webhook_data)
        
        assert event is not None
        assert event.event_type == SyncEventType.FILE_UPDATED
        assert event.resource_id == "file_123"
        assert event.resource_type == "drive_file"
    
    def test_webhook_data_parsing_sheets(self, sync_engine_instance):
        """Test parsing Google Sheets webhook data."""
        engine = sync_engine_instance
        
        webhook_data = {
            "eventType": "google.apps.spreadsheet.document.updated",
            "spreadsheetId": "sheet_123",
            "eventTime": "2024-07-23T17:00:00Z"
        }
        
        event = engine._parse_webhook_data(webhook_data)
        
        assert event is not None
        assert event.event_type == SyncEventType.SHEET_UPDATED
        assert event.resource_id == "sheet_123"
        assert event.resource_type == "sheet"
    
    def test_webhook_data_parsing_invalid(self, sync_engine_instance):
        """Test parsing invalid webhook data."""
        engine = sync_engine_instance
        
        # Invalid webhook data
        webhook_data = {"invalid": "data"}
        
        event = engine._parse_webhook_data(webhook_data)
        assert event is None
    
    def test_stats_tracking(self, sync_engine_instance):
        """Test statistics tracking."""
        engine = sync_engine_instance
        
        # Initial stats
        stats = engine.get_stats()
        assert stats["events_processed"] == 0
        assert stats["events_failed"] == 0
        assert stats["active_syncs"] == 0
        assert stats["running"] == False
        
        # Reset stats
        engine.reset_stats()
        stats = engine.get_stats()
        assert stats["events_processed"] == 0


class TestSyncEngineIntegration:
    """Integration tests for sync engine functionality."""
    
    @pytest.mark.asyncio
    async def test_sync_engine_with_websocket_manager(self):
        """Test sync engine integration with WebSocket manager."""
        websocket_manager = Mock(spec=WebSocketManager)
        websocket_manager.broadcast_to_band = AsyncMock()
        
        engine = SyncEngine(websocket_manager=websocket_manager)
        await engine.start()
        
        # Verify WebSocket manager is set
        assert engine.websocket_manager == websocket_manager
        
        await engine.stop()
    
    @pytest.mark.asyncio
    @patch('app.services.sync_engine.get_db_session')
    async def test_sync_event_processing(self, mock_get_session):
        """Test processing of sync events with database operations."""
        # Mock database session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        engine = SyncEngine()
        
        # Create test event
        event = SyncEvent(
            event_type=SyncEventType.FILE_CREATED,
            resource_id="test_file",
            resource_type="drive_file",
            band_id=1
        )
        
        # Process event (this would normally be called by the queue processor)
        await engine._process_sync_event(event)
        
        # Verify database operations were attempted
        assert mock_session.add.called
        assert mock_session.commit.called


class TestGlobalSyncEngineFunctions:
    """Test global sync engine convenience functions."""
    
    @pytest.mark.asyncio
    async def test_global_start_stop(self):
        """Test global sync engine start/stop functions."""
        # Start global engine
        await start_sync_engine()
        assert sync_engine._running
        
        # Stop global engine
        await stop_sync_engine()
        assert not sync_engine._running
    
    @pytest.mark.asyncio
    async def test_global_webhook_handling(self):
        """Test global webhook handling function."""
        await start_sync_engine()
        
        webhook_data = {
            "resourceId": "file_123",
            "resourceState": "sync"
        }
        
        initial_queue_size = sync_engine._sync_queue.qsize()
        await handle_webhook(webhook_data)
        
        assert sync_engine._sync_queue.qsize() == initial_queue_size + 1
        
        await stop_sync_engine()
    
    @pytest.mark.asyncio
    async def test_global_sync_triggers(self):
        """Test global sync trigger functions."""
        await start_sync_engine()
        
        mock_credentials = Mock(spec=Credentials)
        
        # Test full sync
        operation_id = await trigger_full_sync(1, mock_credentials)
        assert operation_id.startswith("full_sync_1_")
        
        # Test delta sync
        operation_id = await trigger_delta_sync(1, mock_credentials)
        assert operation_id.startswith("delta_sync_1_")
        
        await stop_sync_engine()
    
    def test_global_stats(self):
        """Test global stats function."""
        stats = get_sync_stats()
        assert isinstance(stats, dict)
        assert "events_processed" in stats
        assert "running" in stats


class TestErrorHandling:
    """Test error handling in sync engine."""
    
    @pytest.mark.asyncio
    async def test_sync_engine_error_exception(self):
        """Test SyncEngineError exception."""
        with pytest.raises(SyncEngineError):
            raise SyncEngineError("Test error")
    
    @pytest.mark.asyncio
    async def test_webhook_handling_error(self):
        """Test webhook handling with malformed data."""
        engine = SyncEngine()
        await engine.start()
        
        # This should not raise an exception
        await engine.handle_webhook(None)
        await engine.handle_webhook({"malformed": "data"})
        
        await engine.stop()
    
    @pytest.mark.asyncio
    async def test_event_handler_error_handling(self):
        """Test that errors in event handlers don't crash the engine."""
        engine = SyncEngine()
        
        # Handler that raises an exception
        def error_handler(event):
            raise Exception("Handler error")
        
        engine.register_event_handler(SyncEventType.FILE_CREATED, error_handler)
        
        event = SyncEvent(
            event_type=SyncEventType.FILE_CREATED,
            resource_id="test",
            resource_type="drive_file"
        )
        
        # Should not raise an exception
        await engine._call_event_handlers(event)


class TestSyncEnginePerformance:
    """Test sync engine performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_concurrent_sync_limit(self):
        """Test that concurrent sync operations are limited."""
        engine = SyncEngine(max_concurrent_syncs=2)
        
        # Verify semaphore is created with correct limit
        assert engine._sync_semaphore._value == 2
    
    @pytest.mark.asyncio
    async def test_queue_processing(self):
        """Test that events are properly queued and processed."""
        engine = SyncEngine()
        await engine.start()
        
        # Add multiple events
        for i in range(5):
            event = SyncEvent(
                event_type=SyncEventType.FILE_CREATED,
                resource_id=f"file_{i}",
                resource_type="drive_file"
            )
            await engine._sync_queue.put(event)
        
        assert engine._sync_queue.qsize() == 5
        
        await engine.stop()


# Fixtures for integration testing
@pytest.fixture
def sample_webhook_events():
    """Sample webhook events for testing."""
    return [
        {
            "resourceId": "file_123",
            "resourceState": "sync",
            "eventTime": "2024-07-23T17:00:00Z"
        },
        {
            "resourceId": "file_456",
            "resourceState": "add",
            "eventTime": "2024-07-23T17:01:00Z"
        },
        {
            "eventType": "google.apps.spreadsheet.document.updated",
            "spreadsheetId": "sheet_789",
            "eventTime": "2024-07-23T17:02:00Z"
        }
    ]


@pytest.mark.asyncio
async def test_batch_webhook_processing(sample_webhook_events):
    """Integration test for processing multiple webhook events."""
    engine = SyncEngine()
    await engine.start()
    
    # Process all webhook events
    for webhook_data in sample_webhook_events:
        await engine.handle_webhook(webhook_data)
    
    # All events should be queued
    assert engine._sync_queue.qsize() == len(sample_webhook_events)
    
    await engine.stop()


@pytest.mark.asyncio 
async def test_sync_engine_lifecycle():
    """Test complete sync engine lifecycle."""
    engine = SyncEngine()
    
    # Start engine
    await engine.start()
    assert engine._running
    
    # Add some work
    event = SyncEvent(
        event_type=SyncEventType.FILE_CREATED,
        resource_id="test_file",
        resource_type="drive_file"
    )
    await engine._sync_queue.put(event)
    
    # Stop engine (should wait for work to complete)
    await engine.stop()
    assert not engine._running