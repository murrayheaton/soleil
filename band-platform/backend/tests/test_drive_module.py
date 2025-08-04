"""
Tests for the Drive module.

This module tests the Google Drive integration functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from modules.drive.services.drive_client import GoogleDriveService, DriveAPIError
from modules.drive.services.drive_auth import GoogleDriveOAuthService as DriveOAuthService
from modules.drive.services.rate_limiter import RateLimiter, DynamicRateLimiter
from modules.drive.services.cache_manager import CacheManager
from modules.drive.models.drive_metadata import DriveMetadata, FileChange


class TestDriveClient:
    """Test GoogleDriveService functionality."""

    @pytest.fixture
    def mock_credentials(self):
        """Mock Google OAuth credentials."""
        mock_creds = Mock()
        mock_creds.expired = False
        mock_creds.valid = True
        return mock_creds

    @pytest.fixture
    def drive_service(self, mock_credentials):
        """Create GoogleDriveService instance with mocked credentials."""
        with patch('modules.drive.services.drive_client.build'):
            service = GoogleDriveService(mock_credentials)
            service.service = Mock()
            return service

    @pytest.mark.asyncio
    async def test_list_files_success(self, drive_service):
        """Test successful file listing."""
        # Mock the API response
        mock_response = {
            'files': [
                {'id': 'file1', 'name': 'Song1.pdf', 'mimeType': 'application/pdf'},
                {'id': 'file2', 'name': 'Song2.pdf', 'mimeType': 'application/pdf'}
            ]
        }
        
        drive_service.service.files().list().execute.return_value = mock_response
        
        # Test listing files
        files = await drive_service.list_files()
        
        assert len(files) == 2
        assert files[0]['name'] == 'Song1.pdf'
        assert files[1]['name'] == 'Song2.pdf'

    @pytest.mark.asyncio
    async def test_list_files_with_folder(self, drive_service):
        """Test listing files in a specific folder."""
        folder_id = 'folder123'
        
        # Mock the API call
        drive_service.service.files().list.return_value.execute.return_value = {
            'files': []
        }
        
        # Test listing files in folder
        await drive_service.list_files(folder_id=folder_id)
        
        # Verify the query includes the folder parent
        call_args = drive_service.service.files().list.call_args
        assert f"'{folder_id}' in parents" in call_args[1]['q']

    @pytest.mark.asyncio
    async def test_get_file_metadata(self, drive_service):
        """Test getting file metadata."""
        file_id = 'file123'
        mock_metadata = {
            'id': file_id,
            'name': 'Test.pdf',
            'mimeType': 'application/pdf',
            'modifiedTime': '2024-01-01T00:00:00Z'
        }
        
        drive_service.service.files().get().execute.return_value = mock_metadata
        
        # Test getting metadata
        metadata = await drive_service.get_file_metadata(file_id)
        
        assert metadata['id'] == file_id
        assert metadata['name'] == 'Test.pdf'

    @pytest.mark.asyncio
    async def test_setup_webhook(self, drive_service):
        """Test setting up a webhook for file changes."""
        folder_id = 'folder123'
        webhook_url = 'https://example.com/webhook'
        
        mock_response = {
            'id': 'channel123',
            'resourceId': 'resource123'
        }
        
        drive_service.service.files().watch().execute.return_value = mock_response
        
        # Test webhook setup
        result = await drive_service.setup_webhook(folder_id, webhook_url)
        
        assert result['channel_id'] == 'channel123'
        assert result['resource_id'] == 'resource123'


class TestDriveAuth:
    """Test DriveOAuthService functionality."""

    @pytest.fixture
    def oauth_service(self):
        """Create DriveOAuthService instance."""
        with patch('modules.drive.services.drive_auth.os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key, default=None: {
                'GOOGLE_CLIENT_ID': 'test_client_id',
                'GOOGLE_CLIENT_SECRET': 'test_secret',
                'GOOGLE_REDIRECT_URI': 'http://localhost/callback'
            }.get(key, default)
            
            return DriveOAuthService()

    @pytest.mark.asyncio
    async def test_get_auth_url(self, oauth_service):
        """Test generating authorization URL."""
        auth_url = await oauth_service.get_auth_url()
        
        assert 'accounts.google.com' in auth_url
        assert 'test_client_id' in auth_url
        assert 'http://localhost/callback' in auth_url

    @pytest.mark.asyncio
    async def test_handle_callback_success(self, oauth_service):
        """Test handling OAuth callback."""
        auth_code = 'test_auth_code'
        
        with patch('modules.drive.services.drive_auth.InstalledAppFlow') as mock_flow:
            mock_flow_instance = Mock()
            mock_flow_instance.fetch_token.return_value = None
            mock_flow_instance.credentials = Mock(valid=True)
            mock_flow.from_client_config.return_value = mock_flow_instance
            
            result = await oauth_service.handle_callback(auth_code)
            
            assert result is True
            assert oauth_service.creds is not None


class TestRateLimiter:
    """Test rate limiting functionality."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(requests_per_second=10, burst_size=20)
        
        assert limiter.requests_per_second == 10
        assert limiter.burst_size == 20
        assert limiter.tokens == 20.0

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test acquiring tokens from rate limiter."""
        limiter = RateLimiter(requests_per_second=10, burst_size=10)
        
        # Should succeed immediately
        await limiter.acquire()
        assert limiter.tokens == 9.0
        
        # Acquire remaining tokens
        for _ in range(9):
            await limiter.acquire()
        
        assert limiter.tokens == 0.0

    def test_dynamic_rate_limiter(self):
        """Test DynamicRateLimiter adjustments."""
        limiter = DynamicRateLimiter(initial_rate=10)
        
        # Test backing off on rate limit error
        limiter.on_rate_limit_error()
        assert limiter.current_rate < 10
        
        # Test increasing rate on success
        for _ in range(10):
            limiter.on_success()
        
        # Rate should increase but not exceed max
        assert limiter.current_rate > limiter.min_rate


class TestCacheManager:
    """Test cache management functionality."""

    @pytest.fixture
    def cache_manager(self):
        """Create CacheManager instance."""
        return CacheManager(max_size=100, ttl_seconds=300)

    def test_cache_set_and_get(self, cache_manager):
        """Test setting and getting cached values."""
        key = 'test_key'
        value = {'data': 'test_value'}
        
        # Set value
        cache_manager.set(key, value)
        
        # Get value
        retrieved = cache_manager.get(key)
        assert retrieved == value

    def test_cache_expiration(self, cache_manager):
        """Test cache TTL expiration."""
        key = 'test_key'
        value = {'data': 'test_value'}
        
        # Set value with short TTL
        cache_manager.set(key, value, ttl_seconds=0.1)
        
        # Value should be available immediately
        assert cache_manager.get(key) == value
        
        # Wait for expiration
        import time
        time.sleep(0.2)
        
        # Value should be None after expiration
        assert cache_manager.get(key) is None

    def test_cache_invalidation_pattern(self, cache_manager):
        """Test invalidating cache entries by pattern."""
        # Set multiple values
        cache_manager.set('file_1', {'name': 'File1.pdf'})
        cache_manager.set('file_2', {'name': 'File2.pdf'})
        cache_manager.set('other_1', {'name': 'Other.pdf'})
        
        # Invalidate by pattern
        invalidated = cache_manager.invalidate_pattern('file_*')
        
        assert invalidated == 2
        assert cache_manager.get('file_1') is None
        assert cache_manager.get('file_2') is None
        assert cache_manager.get('other_1') is not None


class TestDriveMetadata:
    """Test drive metadata models."""

    def test_drive_metadata_creation(self):
        """Test creating DriveMetadata instance."""
        metadata = DriveMetadata(
            file_id='file123',
            folder_id='folder456',
            name='Test.pdf',
            mime_type='application/pdf',
            size=1024,
            modified_time=datetime.utcnow(),
            created_time=datetime.utcnow()
        )
        
        assert metadata.file_id == 'file123'
        assert metadata.name == 'Test.pdf'
        assert metadata.size == 1024

    def test_file_change_creation(self):
        """Test creating FileChange instance."""
        change = FileChange(
            file_id='file123',
            change_type='modified',
            change_time=datetime.utcnow(),
            user_email='user@example.com'
        )
        
        assert change.file_id == 'file123'
        assert change.change_type == 'modified'
        assert change.user_email == 'user@example.com'