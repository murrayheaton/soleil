"""
Pytest configuration and fixtures for the Band Platform backend.

This module provides shared test fixtures and configuration for all test modules.
"""

import pytest
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import Mock, AsyncMock, patch
from typing import AsyncGenerator

# Mock database initialization to avoid actual database connections in tests
@pytest.fixture(scope="session", autouse=True)
def mock_database():
    """Mock database initialization for all tests."""
    # Mock the global db_manager instance
    with patch('app.database.connection.db_manager') as mock_db_manager:
        mock_manager = Mock()
        mock_engine = Mock()
        mock_manager.engine = mock_engine
        mock_manager.session_factory = Mock()
        mock_db_manager.return_value = mock_manager

        # Also patch the DatabaseManager class and session helper
        with patch('app.database.connection.DatabaseManager'), patch(
            'app.database.connection.get_db_session'
        ) as mock_get_db_session:
            @asynccontextmanager
            async def _session_ctx() -> AsyncGenerator[AsyncMock, None]:
                yield AsyncMock()

            mock_get_db_session.side_effect = _session_ctx
            yield


@pytest.fixture
def mock_async_session():
    """Provide a mock async database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    """Provide a mock user for testing."""
    user = Mock()
    user.id = 1
    user.name = "Test User"
    user.email = "test@example.com"
    user.instruments = ["trumpet"]
    user.is_admin = False
    return user


@pytest.fixture
def mock_band():
    """Provide a mock band for testing."""
    band = Mock()
    band.id = 1
    band.name = "Test Band"
    band.google_drive_folder_id = "source_folder_123"
    return band


@pytest.fixture
def mock_user_folder():
    """Provide a mock user folder for testing."""
    folder = Mock()
    folder.id = 1
    folder.google_folder_id = "user_folder_123"
    folder.sync_status = "completed"
    folder.file_count = 0
    return folder


@pytest.fixture(scope='session')
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock Google Drive credentials for all tests
@pytest.fixture(autouse=True)
def mock_google_credentials():
    """Mock Google Drive credentials for all tests."""
    with patch('app.services.google_drive.Credentials') as mock_creds:
        mock_credentials = Mock()
        mock_credentials.expired = False
        mock_credentials.refresh_token = "refresh_token"
        mock_creds.return_value = mock_credentials
        yield mock_credentials


# Mock environment variables for tests
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock application settings for tests."""
    with patch('app.config.settings') as mock_settings:
        mock_settings.database_url = "sqlite:///:memory:"
        mock_settings.google_client_id = "test_client_id"
        mock_settings.google_client_secret = "test_client_secret"
        mock_settings.google_drive_scope = "https://www.googleapis.com/auth/drive"
        mock_settings.debug = True
        yield mock_settings