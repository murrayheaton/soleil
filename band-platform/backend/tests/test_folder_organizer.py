"""
Unit tests for the FolderOrganizer service.

Tests the Google Drive folder organization functionality including
role-based file filtering and folder structure creation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.services.folder_organizer import FolderOrganizer, FolderOrganizationError, create_user_folder_if_needed
from app.models.user import User, Band
from app.models.folder_structure import UserFolder


class TestFolderOrganizer:
    """Test cases for the FolderOrganizer service."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock credentials
        self.mock_credentials = Mock()
        
        # Mock database session
        self.mock_db_session = AsyncMock()
        
        # Create organizer instance
        self.organizer = FolderOrganizer(
            credentials=self.mock_credentials,
            db_session=self.mock_db_session
        )
        
        # Create mock user
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.name = "Test User"
        self.mock_user.email = "test@example.com"
        self.mock_user.instruments = ["trumpet"]
        
        # Create mock band
        self.mock_band = Mock(spec=Band)
        self.mock_band.id = 1
        self.mock_band.google_drive_folder_id = "source_folder_123"
        self.mock_user.band = self.mock_band
    
    @pytest.mark.asyncio
    async def test_create_user_folder_structure_success(self):
        """Test successful folder creation for a user."""
        # Mock the Google Drive service responses
        mock_service = AsyncMock()
        mock_create_response = {'id': 'user_folder_123'}
        
        def mock_create():
            return mock_create_response
        
        mock_files = Mock()
        mock_files.create.return_value.execute = mock_create
        mock_service.files.return_value = mock_files
        
        # Mock the context manager
        with patch.object(self.organizer, '_get_service') as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_service
            mock_get_service.return_value.__aexit__.return_value = None
            
            # Mock _make_request to return the create response
            with patch.object(self.organizer, '_make_request', return_value=mock_create_response):
                # Mock _share_folder_with_user
                with patch.object(self.organizer, '_share_folder_with_user') as mock_share:
                    # Mock sync log creation
                    with patch.object(self.organizer, '_create_sync_log', return_value=Mock()):
                        with patch.object(self.organizer, '_complete_sync_log'):
                            
                            folder_id = await self.organizer.create_user_folder_structure(
                                self.mock_user, 
                                "source_folder_123"
                            )
                            
                            assert folder_id == 'user_folder_123'
                            
                            # Verify folder was shared with user
                            mock_share.assert_called_once_with('user_folder_123', 'test@example.com')
    
    @pytest.mark.asyncio 
    async def test_organize_files_by_song_filters_by_instrument(self):
        """Test that files are properly filtered based on user instruments."""
        # Mock files with different keys
        mock_files = [
            {
                'id': 'file1',
                'name': 'Song1 - Bb.pdf',
                'mimeType': 'application/pdf'
            },
            {
                'id': 'file2', 
                'name': 'Song1 - Eb.pdf',
                'mimeType': 'application/pdf'
            },
            {
                'id': 'file3',
                'name': 'Song1 - Reference.mp3',
                'mimeType': 'audio/mpeg'
            }
        ]
        
        # Mock Google Drive service
        mock_service = AsyncMock()
        
        with patch.object(self.organizer, '_get_service') as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_service
            mock_get_service.return_value.__aexit__.return_value = None
            
            # Mock helper methods
            with patch.object(self.organizer, '_create_song_folder', return_value='song_folder_123'):
                with patch.object(self.organizer, '_create_shortcuts_in_folder', return_value=2):
                    with patch.object(self.organizer, '_create_sync_log', return_value=Mock()):
                        with patch.object(self.organizer, '_complete_sync_log'):
                            
                            result = await self.organizer.organize_files_by_song(
                                'user_folder_123',
                                mock_files,
                                ['trumpet'],  # Trumpet uses Bb key
                                1
                            )
                            
                            # Should only have Song1 folder (Bb chart + audio file accessible)
                            assert 'Song1' in result
                            assert result['Song1'] == 'song_folder_123'
    
    @pytest.mark.asyncio
    async def test_organize_files_excludes_inaccessible_charts(self):
        """Test that charts in keys not accessible to user are excluded."""
        # Mock files with Eb charts (not accessible to trumpet player)
        mock_files = [
            {
                'id': 'file1',
                'name': 'Song1 - Eb.pdf',
                'mimeType': 'application/pdf'
            }
        ]
        
        mock_service = AsyncMock()
        
        with patch.object(self.organizer, '_get_service') as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_service
            mock_get_service.return_value.__aexit__.return_value = None
            
            with patch.object(self.organizer, '_create_sync_log', return_value=Mock()):
                with patch.object(self.organizer, '_complete_sync_log'):
                    
                    result = await self.organizer.organize_files_by_song(
                        'user_folder_123',
                        mock_files,
                        ['trumpet'],  # Trumpet uses Bb key, not Eb
                        1
                    )
                    
                    # Should have no song folders since Eb chart is not accessible
                    assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_audio_files_accessible_to_all_users(self):
        """Test that audio files are accessible to all users regardless of instrument."""
        # Mock audio files
        mock_files = [
            {
                'id': 'audio1',
                'name': 'Song1 - Reference.mp3',
                'mimeType': 'audio/mpeg'
            },
            {
                'id': 'audio2',
                'name': 'Song2 - Demo.wav',
                'mimeType': 'audio/wav'
            }
        ]
        
        mock_service = AsyncMock()
        
        with patch.object(self.organizer, '_get_service') as mock_get_service:
            mock_get_service.return_value.__aenter__.return_value = mock_service
            mock_get_service.return_value.__aexit__.return_value = None
            
            # Mock helper methods
            with patch.object(self.organizer, '_create_song_folder', side_effect=['folder1', 'folder2']):
                with patch.object(self.organizer, '_create_shortcuts_in_folder', return_value=1):
                    with patch.object(self.organizer, '_create_sync_log', return_value=Mock()):
                        with patch.object(self.organizer, '_complete_sync_log'):
                            
                            result = await self.organizer.organize_files_by_song(
                                'user_folder_123',
                                mock_files,
                                ['trumpet'],  # Any instrument should access audio files
                                1
                            )
                            
                            # Should have folders for both songs
                            assert 'Song1' in result
                            assert 'Song2' in result
    
    @pytest.mark.asyncio
    async def test_error_handling_rate_limits(self):
        """Test graceful handling of API rate limits."""
        from app.services.google_drive import RateLimitExceeded
        
        with patch.object(self.organizer, '_get_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_get_service.return_value.__aenter__.return_value = mock_service
            mock_get_service.return_value.__aexit__.return_value = None
            
            # Mock _make_request to raise rate limit error
            with patch.object(self.organizer, '_make_request', side_effect=RateLimitExceeded("Rate limit exceeded")):
                with patch.object(self.organizer, '_create_sync_log', return_value=Mock()):
                    with patch.object(self.organizer, '_complete_sync_log'):
                        
                        with pytest.raises(FolderOrganizationError):
                            await self.organizer.create_user_folder_structure(
                                self.mock_user,
                                'source_123'
                            )
    
    @pytest.mark.asyncio
    async def test_batch_shortcut_creation_respects_limits(self):
        """Test that batch operations stay under API limits.""" 
        # Create large number of files to test batching
        mock_files = []
        for i in range(150):
            mock_files.append({
                'file_data': {
                    'id': f'file_{i}',
                    'name': f'Song{i} - Bb.pdf'
                },
                'parsed': Mock(file_type=Mock(value='chart'), key='Bb')
            })
        
        mock_service = AsyncMock()
        
        # Track _make_request calls to ensure proper batching
        with patch.object(self.organizer, '_make_request') as mock_make_request:
            mock_make_request.return_value = {'id': 'shortcut_id'}
            
            shortcuts_created = await self.organizer._create_shortcuts_in_folder(
                mock_service,
                'folder_123',
                mock_files
            )
            
            # Should create all shortcuts
            assert shortcuts_created == 150
            
            # Should make individual requests for each shortcut (within batch limits)
            assert mock_make_request.call_count == 150
    
    def test_generate_shortcut_name_for_charts(self):
        """Test shortcut name generation for chart files."""
        # Mock parsed info for chart
        mock_parsed = Mock()
        mock_parsed.key = 'Bb'
        mock_parsed.file_type.value = 'chart'
        mock_parsed.extension = '.pdf'
        
        name = self.organizer._generate_shortcut_name('Song1 - Bb.pdf', mock_parsed)
        assert name == 'Bb Chart.pdf'
    
    def test_generate_shortcut_name_for_audio(self):
        """Test shortcut name generation for audio files."""
        # Mock parsed info for audio
        mock_parsed = Mock()
        mock_parsed.file_type.value = 'audio'
        
        name = self.organizer._generate_shortcut_name('Song1 - Reference.mp3', mock_parsed)
        assert name == 'Song1 - Reference.mp3'  # Keep original name for audio
    
    @pytest.mark.asyncio
    async def test_create_shortcuts_for_user_integration(self):
        """Test the complete workflow of creating shortcuts for a user."""
        # Setup user with folder structure
        mock_user_folder = Mock(spec=UserFolder)
        mock_user_folder.google_folder_id = 'user_folder_123'
        self.mock_user.user_folder = mock_user_folder
        
        # Mock source files
        source_files = [
            {
                'id': 'file1',
                'name': 'Song1 - Bb.pdf',
                'mimeType': 'application/pdf'
            }
        ]
        
        # Mock organize_files_by_song to return success
        with patch.object(self.organizer, 'organize_files_by_song', return_value={'Song1': 'song_folder_123'}):
            shortcuts_count = await self.organizer.create_shortcuts_for_user(
                self.mock_user,
                source_files
            )
            
            # Should return count from org_stats (mocked by organize_files_by_song)
            assert isinstance(shortcuts_count, int)
    
    @pytest.mark.asyncio 
    async def test_create_shortcuts_for_user_no_folder_structure(self):
        """Test error handling when user has no folder structure."""
        # User with no folder structure
        self.mock_user.user_folder = None
        
        with pytest.raises(FolderOrganizationError, match="has no folder structure"):
            await self.organizer.create_shortcuts_for_user(
                self.mock_user,
                []
            )


class TestCreateUserFolderIfNeeded:
    """Test cases for the create_user_folder_if_needed utility function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.name = "Test User"
        
        self.mock_band = Mock(spec=Band) 
        self.mock_band.google_drive_folder_id = "source_folder_123"
        self.mock_user.band = self.mock_band
        
        self.mock_organizer = AsyncMock(spec=FolderOrganizer)
        self.mock_db_session = AsyncMock()
    
    @pytest.mark.asyncio
    async def test_user_already_has_folder_structure(self):
        """Test when user already has folder structure."""
        # User with existing folder
        mock_user_folder = Mock(spec=UserFolder)
        mock_user_folder.google_folder_id = 'existing_folder_123'
        self.mock_user.user_folder = mock_user_folder
        
        folder_id = await create_user_folder_if_needed(
            self.mock_user,
            self.mock_organizer,
            self.mock_db_session
        )
        
        assert folder_id == 'existing_folder_123'
        
        # Should not call organizer since folder already exists
        self.mock_organizer.create_user_folder_structure.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_new_folder_structure(self):
        """Test creating new folder structure when none exists."""
        # User with no folder structure
        self.mock_user.user_folder = None
        
        # Mock organizer to return new folder ID
        self.mock_organizer.create_user_folder_structure.return_value = 'new_folder_123'
        
        folder_id = await create_user_folder_if_needed(
            self.mock_user,
            self.mock_organizer, 
            self.mock_db_session
        )
        
        assert folder_id == 'new_folder_123'
        
        # Should call organizer to create folder
        self.mock_organizer.create_user_folder_structure.assert_called_once_with(
            self.mock_user,
            "source_folder_123"
        )
        
        # Should add new UserFolder to database
        self.mock_db_session.add.assert_called_once()
        self.mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_when_no_band_drive_folder(self):
        """Test error handling when band has no Google Drive folder."""
        # Band with no Google Drive folder
        self.mock_user.band.google_drive_folder_id = None
        self.mock_user.user_folder = None
        
        with pytest.raises(FolderOrganizationError, match="has no band or band has no Google Drive folder"):
            await create_user_folder_if_needed(
                self.mock_user,
                self.mock_organizer,
                self.mock_db_session
            )
    
    @pytest.mark.asyncio
    async def test_error_when_no_band(self):
        """Test error handling when user has no band."""
        # User with no band
        self.mock_user.band = None
        self.mock_user.user_folder = None
        
        with pytest.raises(FolderOrganizationError, match="has no band or band has no Google Drive folder"):
            await create_user_folder_if_needed(
                self.mock_user,
                self.mock_organizer,
                self.mock_db_session
            )


class TestFolderOrganizerStatistics:
    """Test cases for organizer statistics tracking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.organizer = FolderOrganizer()
    
    def test_initial_statistics(self):
        """Test that initial statistics are zero."""
        stats = self.organizer.get_organization_stats()
        
        assert stats['folders_created'] == 0
        assert stats['shortcuts_created'] == 0
        assert stats['files_organized'] == 0
        assert stats['users_processed'] == 0
        assert stats['errors'] == 0
    
    def test_reset_statistics(self):
        """Test resetting statistics."""
        # Modify stats
        self.organizer.org_stats['folders_created'] = 5
        self.organizer.org_stats['errors'] = 2
        
        # Reset
        self.organizer.reset_organization_stats()
        
        # Should be back to zero
        stats = self.organizer.get_organization_stats()
        assert stats['folders_created'] == 0
        assert stats['errors'] == 0
    
    def test_statistics_are_independent_copies(self):
        """Test that get_organization_stats returns independent copies."""
        stats1 = self.organizer.get_organization_stats()
        stats2 = self.organizer.get_organization_stats()
        
        # Modify one copy
        stats1['folders_created'] = 100
        
        # Other copy should be unchanged
        assert stats2['folders_created'] == 0
        
        # Original should be unchanged
        assert self.organizer.org_stats['folders_created'] == 0