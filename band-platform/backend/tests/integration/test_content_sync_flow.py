"""
Integration tests for content parsing and sync flow
"""

import pytest
from unittest.mock import Mock, AsyncMock
import asyncio
from datetime import datetime

from modules.core import get_event_bus, events


class TestContentSyncFlow:
    """Test content upload → parse → sync flow"""
    
    @pytest.fixture
    def event_bus(self):
        """Get test event bus"""
        from modules.core.event_bus import EventBus
        return EventBus()
    
    @pytest.fixture
    def mock_file(self):
        """Create mock file data"""
        return {
            'id': 'file_123',
            'name': 'Amazing Grace - Bb.pdf',
            'mimeType': 'application/pdf',
            'size': 1024000,
            'createdTime': datetime.utcnow().isoformat()
        }
    
    @pytest.mark.asyncio
    async def test_file_upload_parse_sync_flow(self, event_bus, mock_file):
        """Test complete flow: upload → parse → sync to users"""
        flow_events = []
        
        async def track_event(event):
            flow_events.append({
                'event': event.name,
                'module': event.module,
                'data': event.data
            })
        
        # Subscribe to all relevant events
        for event_type in [
            events.DRIVE_FILE_ADDED,
            events.CONTENT_PARSED,
            events.SYNC_FILE_UPDATED
        ]:
            event_bus.subscribe(event_type, track_event, target_module="test")
        
        # Step 1: Drive detects new file
        await event_bus.publish(
            event_type=events.DRIVE_FILE_ADDED,
            data={
                'file': mock_file,
                'folder_id': 'folder_456'
            },
            source_module='drive'
        )
        
        await asyncio.sleep(0.1)
        
        # Step 2: Content module parses the file
        await event_bus.publish(
            event_type=events.CONTENT_PARSED,
            data={
                'file_id': mock_file['id'],
                'parsed_data': {
                    'title': 'Amazing Grace',
                    'key': 'Bb',
                    'instruments': ['trumpet', 'clarinet'],
                    'tempo': 72,
                    'time_signature': '3/4'
                }
            },
            source_module='content'
        )
        
        await asyncio.sleep(0.1)
        
        # Step 3: Sync module updates all clients
        await event_bus.publish(
            event_type=events.SYNC_FILE_UPDATED,
            data={
                'file_id': mock_file['id'],
                'action': 'added',
                'metadata': {
                    'title': 'Amazing Grace',
                    'key': 'Bb',
                    'instruments': ['trumpet', 'clarinet']
                },
                'synced_users': ['user1', 'user2', 'user3']
            },
            source_module='sync'
        )
        
        await asyncio.sleep(0.1)
        
        # Verify complete flow
        assert len(flow_events) == 3
        assert flow_events[0]['event'] == events.DRIVE_FILE_ADDED
        assert flow_events[1]['event'] == events.CONTENT_PARSED
        assert flow_events[2]['event'] == events.SYNC_FILE_UPDATED
        
        # Verify data flow
        assert flow_events[1]['data']['parsed_data']['title'] == 'Amazing Grace'
        assert 'trumpet' in flow_events[2]['data']['metadata']['instruments']
    
    @pytest.mark.asyncio
    async def test_bulk_content_update_flow(self, event_bus):
        """Test bulk content update → sync flow"""
        sync_events = []
        
        async def sync_handler(event):
            sync_events.append(event.data)
        
        # Sync module subscribes to content updates
        event_bus.subscribe(
            events.CONTENT_UPDATED,
            sync_handler,
            target_module="sync"
        )
        
        # Simulate bulk content updates
        files_to_update = [
            {'id': 'file_1', 'title': 'Song 1', 'key': 'C'},
            {'id': 'file_2', 'title': 'Song 2', 'key': 'G'},
            {'id': 'file_3', 'title': 'Song 3', 'key': 'F'}
        ]
        
        for file_data in files_to_update:
            await event_bus.publish(
                event_type=events.CONTENT_UPDATED,
                data={
                    'file_id': file_data['id'],
                    'action': 'metadata_updated',
                    'updates': file_data
                },
                source_module='content'
            )
        
        await asyncio.sleep(0.2)
        
        # Verify all updates were received by sync
        assert len(sync_events) == 3
        for i, event_data in enumerate(sync_events):
            assert event_data['file_id'] == files_to_update[i]['id']
    
    @pytest.mark.asyncio
    async def test_content_deletion_flow(self, event_bus, mock_file):
        """Test content deletion → cleanup → sync flow"""
        cleanup_actions = []
        
        async def cleanup_handler(event):
            # Simulate cleanup actions
            cleanup_actions.append({
                'module': event.module,
                'file_id': event.data.get('file_id'),
                'action_taken': 'cleaned'
            })
        
        # Multiple modules subscribe to content deletion
        for module in ['drive', 'sync', 'dashboard']:
            event_bus.subscribe(
                events.CONTENT_DELETED,
                cleanup_handler,
                target_module=module
            )
        
        # Trigger content deletion
        await event_bus.publish(
            event_type=events.CONTENT_DELETED,
            data={
                'file_id': mock_file['id'],
                'reason': 'user_requested',
                'timestamp': datetime.utcnow().isoformat()
            },
            source_module='content'
        )
        
        await asyncio.sleep(0.1)
        
        # Verify all modules performed cleanup
        assert len(cleanup_actions) == 3
        modules_cleaned = [action['module'] for action in cleanup_actions]
        assert set(modules_cleaned) == {'content'}  # All handlers see source as content
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast_flow(self, event_bus):
        """Test sync → WebSocket broadcast flow"""
        broadcasts = []
        
        async def websocket_handler(event):
            # Simulate WebSocket broadcast
            broadcasts.append({
                'type': 'broadcast',
                'event': event.name,
                'data': event.data,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Frontend WebSocket subscribes to sync events
        event_bus.subscribe(
            events.SYNC_PROGRESS,
            websocket_handler,
            target_module="frontend"
        )
        
        # Simulate sync progress updates
        for progress in [0, 25, 50, 75, 100]:
            await event_bus.publish(
                event_type=events.SYNC_PROGRESS,
                data={
                    'operation': 'folder_sync',
                    'progress': progress,
                    'current_file': f'file_{progress}.pdf',
                    'total_files': 100
                },
                source_module='sync'
            )
            await asyncio.sleep(0.05)
        
        # Verify all progress updates were broadcast
        assert len(broadcasts) == 5
        progress_values = [b['data']['progress'] for b in broadcasts]
        assert progress_values == [0, 25, 50, 75, 100]