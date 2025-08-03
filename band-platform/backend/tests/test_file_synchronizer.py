"""
Unit tests for the FileSynchronizer service.

Tests the file synchronization functionality including webhook processing,
user folder synchronization, and sync status management.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.services.file_synchronizer import (
    FileSynchronizer, 
    SynchronizationError,
    schedule_sync_for_users,
    cleanup_stale_folders
)
from app.services.google_drive import GoogleDriveService
from app.services.folder_organizer import FolderOrganizer
from app.models.user import User, Band
from app.models.folder_structure import UserFolder, SyncStatus


class TestFileSynchronizer:
    """Test cases for the FileSynchronizer service."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock services
        self.mock_drive_service = Mock(spec=GoogleDriveService)
        self.mock_db_session = AsyncMock()
        self.mock_organizer = Mock(spec=FolderOrganizer)
        
        # Create synchronizer instance
        self.synchronizer = FileSynchronizer(
            drive_service=self.mock_drive_service,
            db_session=self.mock_db_session,
            organizer=self.mock_organizer
        )
        
        # Mock user with folder structure
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.name = "Test User"
        self.mock_user.instruments = ["trumpet"]
        
        # Mock band
        self.mock_band = Mock(spec=Band)
        self.mock_band.google_drive_folder_id = "source_folder_123"
        self.mock_user.band = self.mock_band
        
        # Mock user folder
        self.mock_user_folder = Mock(spec=UserFolder)
        self.mock_user_folder.id = 1
        self.mock_user_folder.google_folder_id = "user_folder_123"
        self.mock_user_folder.sync_status = SyncStatus.PENDING
        self.mock_user.user_folder = self.mock_user_folder
    
    @pytest.mark.asyncio
    async def test_sync_source_to_user_folders_success(self):
        """Test successful synchronization from source to user folders."""
        # Mock source files
        mock_source_files = [
            {
                'filename': 'Song1 - Bb.pdf',
                'google_file_id': 'file1',
                'key': 'Bb'
            },
            {
                'filename': 'Song1 - Reference.mp3', 
                'google_file_id': 'file2',
                'key': None
            }
        ]
        
        # Mock drive service methods
        self.mock_drive_service.process_files_for_sync.return_value = mock_source_files
        
        # Mock database query for users
        with patch.object(self.synchronizer, '_get_users_for_sync', return_value=[self.mock_user]):
            # Mock user sync method
            with patch.object(self.synchronizer, '_sync_user_folder') as mock_sync_user:
                mock_sync_user.return_value = {
                    'user_id': 1,
                    'shortcuts_created': 2,
                    'shortcuts_deleted': 0,
                    'status': 'success'
                }
                
                result = await self.synchronizer.sync_source_to_user_folders(
                    "source_folder_123"
                )
                
                # Verify results
                assert result['users_processed'] == 1
                assert result['files_processed'] == 2
                assert result['total_shortcuts_created'] == 2
                assert result['total_shortcuts_deleted'] == 0
                assert len(result['errors']) == 0
                
                # Verify user sync was called
                mock_sync_user.assert_called_once_with(
                    self.mock_user, 
                    mock_source_files,
                    "source_folder_123"
                )
    
    @pytest.mark.asyncio
    async def test_sync_source_to_user_folders_handles_user_errors(self):
        """Test that individual user sync errors don't stop the entire operation."""
        # Mock users
        mock_user2 = Mock(spec=User)
        mock_user2.id = 2
        mock_user2.name = "User 2"
        
        mock_source_files = [{'filename': 'test.pdf'}]
        self.mock_drive_service.process_files_for_sync.return_value = mock_source_files
        
        with patch.object(self.synchronizer, '_get_users_for_sync', return_value=[self.mock_user, mock_user2]):
            with patch.object(self.synchronizer, '_sync_user_folder') as mock_sync_user:
                # First user succeeds, second fails
                mock_sync_user.side_effect = [
                    {'user_id': 1, 'shortcuts_created': 1, 'shortcuts_deleted': 0, 'status': 'success'},
                    Exception("User 2 sync failed")
                ]
                
                result = await self.synchronizer.sync_source_to_user_folders(
                    "source_folder_123"
                )
                
                # Should process first user successfully
                assert result['users_processed'] == 1
                assert result['total_shortcuts_created'] == 1
                
                # Should record the error
                assert len(result['errors']) == 1
                assert "User 2 sync failed" in result['errors'][0]
    
    @pytest.mark.asyncio
    async def test_sync_single_user_success(self):
        """Test synchronizing a single user's folder."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = self.mock_user
        self.mock_db_session.execute.return_value = mock_result
        
        # Mock source files
        mock_source_files = [{'filename': 'test.pdf'}]
        self.mock_drive_service.process_files_for_sync.return_value = mock_source_files
        
        # Mock user sync
        with patch.object(self.synchronizer, '_sync_user_folder') as mock_sync_user:
            mock_sync_user.return_value = {
                'user_id': 1,
                'folder_id': 'user_folder_123',
                'shortcuts_created': 1,
                'shortcuts_deleted': 0,
                'status': 'success'
            }
            
            result = await self.synchronizer.sync_single_user(
                1,
                "source_folder_123"
            )
            
            assert result['user_id'] == 1
            assert result['status'] == 'success'
            assert result['shortcuts_created'] == 1
    
    @pytest.mark.asyncio
    async def test_sync_single_user_not_found(self):
        """Test error handling when user is not found."""
        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_db_session.execute.return_value = mock_result
        
        with pytest.raises(SynchronizationError, match="User 999 not found"):
            await self.synchronizer.sync_single_user(999, "source_folder_123")
    
    @pytest.mark.asyncio
    async def test_detect_file_changes_processes_webhook(self):
        """Test processing of Google Drive webhook notifications."""
        # Mock webhook data
        webhook_data = {
            'resourceId': 'source_folder_123',
            'resourceState': 'update'
        }
        
        # Mock database query for user folders
        mock_user_folder = Mock(spec=UserFolder)
        mock_user_folder.user_id = 1
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_user_folder]
        self.mock_db_session.execute.return_value = mock_result
        
        # Mock sync operation
        with patch.object(self.synchronizer, 'sync_source_to_user_folders') as mock_sync:
            mock_sync.return_value = {
                'users_processed': 1,
                'files_processed': 5
            }
            
            result = await self.synchronizer.detect_file_changes(webhook_data)
            
            assert result['status'] == 'sync_triggered'
            assert result['resource_id'] == 'source_folder_123'
            assert result['affected_users'] == 1
            
            # Verify sync was triggered
            mock_sync.assert_called_once_with(
                'source_folder_123',
                user_ids=[1]
            )
    
    @pytest.mark.asyncio
    async def test_detect_file_changes_ignores_unsupported_states(self):
        """Test that unsupported webhook states are ignored."""
        webhook_data = {
            'resourceId': 'source_folder_123',
            'resourceState': 'exists'  # Not update/add/remove
        }
        
        result = await self.synchronizer.detect_file_changes(webhook_data)
        
        assert result['status'] == 'ignored'
        assert 'Unsupported state' in result['reason']
    
    @pytest.mark.asyncio
    async def test_update_user_shortcuts_filters_by_instruments(self):
        """Test that shortcut updates filter files by user instruments."""
        # Mock new files with different keys
        new_files = [
            {
                'filename': 'Song1 - Bb.pdf',  # Accessible to trumpet
                'google_file_id': 'file1'
            },
            {
                'filename': 'Song1 - Eb.pdf',  # Not accessible to trumpet
                'google_file_id': 'file2'
            },
            {
                'filename': 'Song1 - Reference.mp3',  # Accessible to all
                'google_file_id': 'file3'
            }
        ]
        
        # Mock organizer
        self.mock_organizer.create_shortcuts_for_user.return_value = 2
        
        result = await self.synchronizer.update_user_shortcuts(
            self.mock_user,
            new_files
        )
        
        assert result['shortcuts_created'] == 2
        assert result['status'] == 'updated'
        
        # Verify organizer was called (it handles the filtering internally)
        self.mock_organizer.create_shortcuts_for_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_user_shortcuts_no_folder_structure(self):
        """Test handling when user has no folder structure."""
        # User with no folder structure
        self.mock_user.user_folder = None
        
        result = await self.synchronizer.update_user_shortcuts(
            self.mock_user,
            []
        )
        
        assert result['status'] == 'no_folder'
        assert result['shortcuts_created'] == 0
        assert result['shortcuts_deleted'] == 0
    
    @pytest.mark.asyncio
    async def test_sync_user_folder_creates_folder_if_needed(self):
        """Test that user folder is created if it doesn't exist."""
        # User with no folder structure
        self.mock_user.user_folder = None
        
        mock_source_files = [{'filename': 'test.pdf'}]
        
        # Mock create_user_folder_if_needed
        with patch('app.services.file_synchronizer.create_user_folder_if_needed') as mock_create:
            mock_create.return_value = 'new_folder_123'
            
            # Mock organizer
            self.mock_organizer.create_shortcuts_for_user.return_value = 1
            
            # Create mock user folder for the test
            mock_new_folder = Mock(spec=UserFolder)
            mock_new_folder.sync_status = SyncStatus.PENDING
            self.mock_user.user_folder = mock_new_folder
            
            result = await self.synchronizer._sync_user_folder(
                self.mock_user,
                mock_source_files,
                "source_folder_123"
            )
            
            assert result['folder_id'] == 'new_folder_123'
            assert result['status'] == 'success'
            
            # Verify folder creation was called
            mock_create.assert_called_once_with(
                self.mock_user,
                self.synchronizer.organizer,
                self.synchronizer.db_session
            )
    
    @pytest.mark.asyncio
    async def test_sync_user_folder_updates_status(self):
        """Test that sync operation updates user folder status."""
        mock_source_files = [{'filename': 'test.pdf'}]
        
        # Mock organizer
        self.mock_organizer.create_shortcuts_for_user.return_value = 5
        
        await self.synchronizer._sync_user_folder(
            self.mock_user,
            mock_source_files,
            "source_folder_123"
        )
        
        # Verify folder status was updated
        assert self.mock_user_folder.sync_status == SyncStatus.COMPLETED
        assert self.mock_user_folder.sync_error is None
        assert self.mock_user_folder.file_count == 5
        
        # Verify database commit
        self.mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_sync_user_folder_handles_errors(self):
        """Test error handling in user folder sync."""
        mock_source_files = [{'filename': 'test.pdf'}]
        
        # Mock organizer to raise error
        self.mock_organizer.create_shortcuts_for_user.side_effect = Exception("Organizer error")
        
        with pytest.raises(SynchronizationError):
            await self.synchronizer._sync_user_folder(
                self.mock_user,
                mock_source_files,
                "source_folder_123"
            )
        
        # Verify error status was set
        assert self.mock_user_folder.sync_status == SyncStatus.ERROR
        assert "Organizer error" in self.mock_user_folder.sync_error
    
    @pytest.mark.asyncio
    async def test_get_sync_status_for_user(self):
        """Test getting sync status for a specific user."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = self.mock_user
        self.mock_db_session.execute.return_value = mock_result
        
        # Set up user folder with status
        self.mock_user_folder.sync_status = SyncStatus.COMPLETED
        self.mock_user_folder.last_sync = datetime.utcnow()
        self.mock_user_folder.file_count = 10
        self.mock_user_folder.sync_error = None
        
        status = await self.synchronizer.get_sync_status(1)
        
        assert status['user_id'] == 1
        assert status['sync_status'] == SyncStatus.COMPLETED
        assert status['file_count'] == 10
        assert status['sync_error'] is None
        assert 'last_sync' in status
    
    @pytest.mark.asyncio
    async def test_get_sync_status_user_not_found(self):
        """Test sync status when user is not found."""
        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        self.mock_db_session.execute.return_value = mock_result
        
        status = await self.synchronizer.get_sync_status(999)
        
        assert 'error' in status
        assert 'User 999 not found' in status['error']
    
    @pytest.mark.asyncio
    async def test_get_sync_status_no_folder_structure(self):
        """Test sync status when user has no folder structure."""
        # User with no folder structure
        self.mock_user.user_folder = None
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = self.mock_user
        self.mock_db_session.execute.return_value = mock_result
        
        status = await self.synchronizer.get_sync_status(1)
        
        assert status['user_id'] == 1
        assert status['sync_status'] == 'not_initialized'
        assert 'no folder structure' in status['message']
    
    @pytest.mark.asyncio
    async def test_get_sync_status_global(self):
        """Test getting global sync statistics."""
        # Set some stats
        self.synchronizer.sync_stats['users_synced'] = 5
        self.synchronizer.sync_stats['files_processed'] = 100
        self.synchronizer.sync_stats['last_sync'] = datetime.utcnow()
        
        status = await self.synchronizer.get_sync_status()
        
        assert 'global_stats' in status
        assert status['global_stats']['users_synced'] == 5
        assert status['global_stats']['files_processed'] == 100
        assert status['status'] == 'active'
    
    def test_get_sync_stats(self):
        """Test getting sync statistics."""
        # Modify some stats
        self.synchronizer.sync_stats['users_synced'] = 3
        self.synchronizer.sync_stats['errors'] = 1
        
        stats = self.synchronizer.get_sync_stats()
        
        assert stats['users_synced'] == 3
        assert stats['errors'] == 1
        
        # Should be a copy, not the original
        stats['users_synced'] = 999
        assert self.synchronizer.sync_stats['users_synced'] == 3
    
    def test_reset_sync_stats(self):
        """Test resetting sync statistics."""
        # Set some values
        self.synchronizer.sync_stats['users_synced'] = 10
        self.synchronizer.sync_stats['errors'] = 5
        
        # Reset
        self.synchronizer.reset_sync_stats()
        
        # Should be back to defaults
        stats = self.synchronizer.get_sync_stats()
        assert stats['users_synced'] == 0
        assert stats['errors'] == 0
        assert stats['last_sync'] is None


class TestScheduleSyncForUsers:
    """Test cases for the schedule_sync_for_users utility function."""
    
    @pytest.mark.asyncio
    async def test_schedule_sync_returns_job_id(self):
        """Test that scheduling returns a job ID."""
        mock_synchronizer = Mock(spec=FileSynchronizer)
        mock_synchronizer.sync_source_to_user_folders = AsyncMock()
        
        job_id = await schedule_sync_for_users(
            user_ids=[1, 2],
            source_folder_id="source_123",
            synchronizer=mock_synchronizer,
            delay_seconds=0
        )
        
        # Should return a UUID string
        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID format
        
        # Give the async task a moment to start
        await asyncio.sleep(0.1)
        
        # Should call sync method
        mock_synchronizer.sync_source_to_user_folders.assert_called_once_with(
            "source_123",
            user_ids=[1, 2]
        )
    
    @pytest.mark.asyncio 
    async def test_schedule_sync_with_delay(self):
        """Test scheduling with delay."""
        mock_synchronizer = Mock(spec=FileSynchronizer)
        mock_synchronizer.sync_source_to_user_folders = AsyncMock()
        
        start_time = datetime.now()
        
        await schedule_sync_for_users(
            user_ids=[1],
            source_folder_id="source_123", 
            synchronizer=mock_synchronizer,
            delay_seconds=0.1  # Small delay for testing
        )
        
        # Give time for delay and execution
        await asyncio.sleep(0.2)
        
        # Should have been delayed
        elapsed = (datetime.now() - start_time).total_seconds()
        assert elapsed >= 0.1
        
        # Should still call sync method
        mock_synchronizer.sync_source_to_user_folders.assert_called_once()


class TestCleanupStaleFolders:
    """Test cases for the cleanup_stale_folders utility function."""
    
    @pytest.mark.asyncio
    async def test_cleanup_resets_stale_folders(self):
        """Test that stale folders are reset to appropriate status."""
        mock_synchronizer = Mock(spec=FileSynchronizer)
        mock_db_session = AsyncMock()
        mock_synchronizer.db_session = mock_db_session
        
        # Mock stale folders
        mock_stale_folder1 = Mock(spec=UserFolder)
        mock_stale_folder1.sync_status = SyncStatus.IN_PROGRESS
        mock_stale_folder1.updated_at = datetime.utcnow() - timedelta(hours=25)
        
        mock_stale_folder2 = Mock(spec=UserFolder)
        mock_stale_folder2.sync_status = SyncStatus.IN_PROGRESS
        mock_stale_folder2.updated_at = datetime.utcnow() - timedelta(hours=30)
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_stale_folder1, mock_stale_folder2]
        mock_db_session.execute.return_value = mock_result
        
        result = await cleanup_stale_folders(mock_synchronizer, max_age_hours=24)
        
        assert result['folders_reset'] == 2
        assert result['status'] == 'completed'
        
        # Check that folders were updated
        assert mock_stale_folder1.sync_status == SyncStatus.STALE
        assert mock_stale_folder2.sync_status == SyncStatus.STALE
        assert "timed out" in mock_stale_folder1.sync_error
        assert "timed out" in mock_stale_folder2.sync_error
        
        # Should commit changes
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_handles_no_stale_folders(self):
        """Test cleanup when there are no stale folders."""
        mock_synchronizer = Mock(spec=FileSynchronizer)
        mock_db_session = AsyncMock()
        mock_synchronizer.db_session = mock_db_session
        
        # Mock empty result
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        result = await cleanup_stale_folders(mock_synchronizer)
        
        assert result['folders_reset'] == 0
        assert result['status'] == 'completed'
        
        # Should still commit (empty operation)
        mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_handles_errors(self):
        """Test error handling in cleanup operation."""
        mock_synchronizer = Mock(spec=FileSynchronizer)
        mock_db_session = AsyncMock()
        mock_synchronizer.db_session = mock_db_session
        
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        
        result = await cleanup_stale_folders(mock_synchronizer)
        
        assert result['status'] == 'failed'
        assert 'error' in result
        assert 'Database error' in result['error']