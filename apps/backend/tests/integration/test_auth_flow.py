"""
Integration tests for authentication flow across modules
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import asyncio

from modules.core import get_event_bus, events, get_api_gateway
from modules.auth.services import AuthService, JWTService
from modules.auth.models import User


class TestAuthenticationFlow:
    """Test complete authentication flow across modules"""
    
    @pytest.fixture
    def event_bus(self):
        """Get test event bus"""
        from modules.core.event_bus import EventBus
        return EventBus()
    
    @pytest.fixture
    def api_gateway(self):
        """Get test API gateway"""
        from modules.core.api_gateway import APIGateway
        return APIGateway()
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user"""
        return User(
            id=1,
            email="test@example.com",
            name="Test User",
            picture="https://example.com/picture.jpg",
            instruments=["piano", "guitar"],
            role="user"
        )
    
    @pytest.mark.asyncio
    async def test_login_flow_with_events(self, event_bus, mock_user):
        """Test login → token creation → event publishing flow"""
        # Track events
        received_events = []
        
        async def capture_event(event):
            received_events.append(event)
        
        # Subscribe to auth events
        event_bus.subscribe(
            events.AUTH_USER_LOGGED_IN,
            capture_event,
            target_module="test"
        )
        
        # Simulate login
        await event_bus.publish(
            event_type=events.AUTH_USER_LOGGED_IN,
            data={
                'user_id': mock_user.id,
                'email': mock_user.email,
                'timestamp': datetime.utcnow().isoformat()
            },
            source_module='auth'
        )
        
        # Give event time to process
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0].name == events.AUTH_USER_LOGGED_IN
        assert received_events[0].data['user_id'] == mock_user.id
    
    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, event_bus, mock_user):
        """Test token refresh → event → drive module update flow"""
        # Track events
        drive_events = []
        
        async def drive_handler(event):
            # Simulate drive module updating credentials
            drive_events.append({
                'event': event.name,
                'user_id': event.data.get('user_id'),
                'new_token': event.data.get('access_token')
            })
        
        # Drive module subscribes to token refresh
        event_bus.subscribe(
            events.AUTH_TOKEN_REFRESHED,
            drive_handler,
            target_module="drive"
        )
        
        # Simulate token refresh
        await event_bus.publish(
            event_type=events.AUTH_TOKEN_REFRESHED,
            data={
                'user_id': mock_user.id,
                'access_token': 'new_access_token_123',
                'refresh_token': 'new_refresh_token_456',
                'expires_in': 3600
            },
            source_module='auth'
        )
        
        # Give event time to process
        await asyncio.sleep(0.1)
        
        # Verify drive module received the event
        assert len(drive_events) == 1
        assert drive_events[0]['user_id'] == mock_user.id
        assert drive_events[0]['new_token'] == 'new_access_token_123'
    
    def test_service_discovery(self, api_gateway):
        """Test auth service registration and discovery"""
        # Create mock services
        mock_jwt_service = Mock(spec=JWTService)
        mock_auth_service = Mock(spec=AuthService)
        
        # Register auth module with services
        api_gateway.register_module(
            name='auth',
            router=Mock(),  # Mock router
            version='1.0.0',
            services={
                'jwt': mock_jwt_service,
                'auth': mock_auth_service
            }
        )
        
        # Other modules can discover auth services
        jwt_service = api_gateway.get_module_service('auth', 'jwt')
        auth_service = api_gateway.get_module_service('auth', 'auth')
        
        assert jwt_service == mock_jwt_service
        assert auth_service == mock_auth_service
    
    @pytest.mark.asyncio
    async def test_logout_flow(self, event_bus, mock_user):
        """Test logout → event → cleanup flow"""
        cleanup_performed = []
        
        async def cleanup_handler(event):
            # Simulate modules cleaning up user data
            cleanup_performed.append({
                'module': 'content',
                'user_id': event.data.get('user_id'),
                'action': 'cleared_cache'
            })
        
        # Content module subscribes to logout
        event_bus.subscribe(
            events.AUTH_USER_LOGGED_OUT,
            cleanup_handler,
            target_module="content"
        )
        
        # Simulate logout
        await event_bus.publish(
            event_type=events.AUTH_USER_LOGGED_OUT,
            data={
                'user_id': mock_user.id,
                'timestamp': datetime.utcnow().isoformat()
            },
            source_module='auth'
        )
        
        # Give event time to process
        await asyncio.sleep(0.1)
        
        # Verify cleanup was performed
        assert len(cleanup_performed) == 1
        assert cleanup_performed[0]['user_id'] == mock_user.id
        assert cleanup_performed[0]['action'] == 'cleared_cache'
    
    @pytest.mark.asyncio
    async def test_permission_update_flow(self, event_bus, mock_user):
        """Test permission update → event → access control update"""
        access_updates = []
        
        async def access_handler(event):
            # Simulate updating access controls
            access_updates.append({
                'user_id': event.data.get('user_id'),
                'new_role': event.data.get('new_role'),
                'new_instruments': event.data.get('new_instruments')
            })
        
        # Multiple modules subscribe to permission updates
        event_bus.subscribe(
            events.AUTH_PERMISSION_UPDATED,
            access_handler,
            target_module="content"
        )
        event_bus.subscribe(
            events.AUTH_PERMISSION_UPDATED,
            access_handler,
            target_module="drive"
        )
        
        # Update permissions
        await event_bus.publish(
            event_type=events.AUTH_PERMISSION_UPDATED,
            data={
                'user_id': mock_user.id,
                'new_role': 'admin',
                'new_instruments': ['piano', 'guitar', 'drums'],
                'timestamp': datetime.utcnow().isoformat()
            },
            source_module='auth'
        )
        
        # Give events time to process
        await asyncio.sleep(0.1)
        
        # Verify both modules received the update
        assert len(access_updates) == 2
        for update in access_updates:
            assert update['user_id'] == mock_user.id
            assert update['new_role'] == 'admin'
            assert 'drums' in update['new_instruments']