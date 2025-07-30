"""
Unit tests for the authentication service.

This module tests Google OAuth integration, JWT token management,
and role-based access control following the PRP requirements.
"""

import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
from google.oauth2.credentials import Credentials

from app.services.auth import (
    AuthService,
    GoogleAuthService,
    JWTService,
    AuthenticationError,
    AuthorizationError,
    TokenError,
    auth_service,
    start_oauth_flow,
    complete_oauth_flow,
    validate_token,
    refresh_tokens,
    logout,
    check_permissions,
    get_auth_stats
)
from app.models.user import UserRole


class TestGoogleAuthService:
    """Test cases for the GoogleAuthService class."""
    
    @pytest.fixture
    def google_auth_service(self):
        """Create a test Google auth service instance."""
        return GoogleAuthService()
    
    def test_google_auth_service_initialization(self, google_auth_service):
        """Test Google auth service initialization."""
        service = google_auth_service
        
        assert service.client_id is not None
        assert service.client_secret is not None
        assert len(service.scopes) > 0
        assert 'openid' in service.scopes
        assert 'email' in service.scopes
        assert 'profile' in service.scopes
        assert isinstance(service.stats, dict)
    
    def test_get_authorization_url(self, google_auth_service):
        """Test generating OAuth authorization URL."""
        service = google_auth_service
        
        # Test without state
        auth_url, state = service.get_authorization_url()
        
        assert auth_url.startswith('https://accounts.google.com/o/oauth2/auth')
        assert 'client_id=' in auth_url
        assert 'scope=' in auth_url
        assert 'response_type=code' in auth_url
        assert len(state) > 10  # State should be a random string
    
    def test_get_authorization_url_with_state(self, google_auth_service):
        """Test generating OAuth authorization URL with provided state."""
        service = google_auth_service
        custom_state = "test_state_123"
        
        auth_url, returned_state = service.get_authorization_url(custom_state)
        
        assert returned_state == custom_state
        assert f'state={custom_state}' in auth_url
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self, google_auth_service):
        """Test getting user profile from Google."""
        service = google_auth_service
        
        # Mock credentials
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.expired = False
        
        # Mock Google People API response
        mock_profile = {
            'resourceName': 'people/123456789',
            'emailAddresses': [{'value': 'test@example.com'}],
            'names': [{'displayName': 'Test User'}],
            'photos': [{'url': 'https://example.com/photo.jpg'}]
        }
        
        with patch('app.services.auth.build') as mock_build:
            mock_service = Mock()
            mock_people = Mock()
            mock_get = Mock()
            mock_get.execute.return_value = mock_profile
            mock_people.get.return_value = mock_get
            mock_service.people.return_value = mock_people
            mock_build.return_value = mock_service
            
            profile = await service.get_user_profile(mock_credentials)
            
            assert profile['email'] == 'test@example.com'
            assert profile['name'] == 'Test User'
            assert profile['photo_url'] == 'https://example.com/photo.jpg'
            assert profile['google_id'] == '123456789'
    
    @pytest.mark.asyncio
    async def test_refresh_credentials(self, google_auth_service):
        """Test refreshing Google OAuth credentials."""
        service = google_auth_service
        
        # Mock credentials with refresh token
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.refresh_token = "refresh_token_123"
        mock_credentials.refresh = Mock()
        
        refreshed = await service.refresh_credentials(mock_credentials)
        
        assert refreshed == mock_credentials
        mock_credentials.refresh.assert_called_once()
        assert service.stats["token_refreshes"] == 1
    
    @pytest.mark.asyncio
    async def test_refresh_credentials_no_refresh_token(self, google_auth_service):
        """Test refreshing credentials without refresh token."""
        service = google_auth_service
        
        # Mock credentials without refresh token
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.refresh_token = None
        
        with pytest.raises(TokenError, match="No refresh token available"):
            await service.refresh_credentials(mock_credentials)
    
    def test_stats_tracking(self, google_auth_service):
        """Test statistics tracking."""
        service = google_auth_service
        
        # Initial stats
        stats = service.get_stats()
        assert stats["auth_attempts"] == 0
        assert stats["auth_successes"] == 0
        assert stats["auth_failures"] == 0


class TestJWTService:
    """Test cases for the JWTService class."""
    
    @pytest.fixture
    def jwt_service(self):
        """Create a test JWT service instance."""
        return JWTService()
    
    def test_jwt_service_initialization(self, jwt_service):
        """Test JWT service initialization."""
        service = jwt_service
        
        assert service.secret_key is not None
        assert service.algorithm == "HS256"
        assert service.access_token_expire_minutes > 0
        assert service.refresh_token_expire_days > 0
        assert isinstance(service.stats, dict)
    
    def test_create_access_token(self, jwt_service):
        """Test creating JWT access token."""
        service = jwt_service
        
        user_id = 123
        band_id = 456
        role = "admin"
        instruments = ["trumpet", "piano"]
        
        token = service.create_access_token(
            user_id=user_id,
            band_id=band_id,
            role=role,
            instruments=instruments
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode token to verify contents
        payload = jwt.decode(token, service.secret_key, algorithms=[service.algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["band_id"] == band_id
        assert payload["role"] == role
        assert payload["instruments"] == instruments
        assert payload["type"] == "access"
    
    def test_create_refresh_token(self, jwt_service):
        """Test creating JWT refresh token."""
        service = jwt_service
        
        user_id = 123
        token = service.create_refresh_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode token to verify contents
        payload = jwt.decode(token, service.secret_key, algorithms=[service.algorithm])
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
    
    def test_validate_token_valid(self, jwt_service):
        """Test validating a valid JWT token."""
        service = jwt_service
        
        # Create token
        user_id = 123
        token = service.create_access_token(user_id)
        
        # Validate token
        payload = service.validate_token(token)
        
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert service.stats["tokens_validated"] == 1
    
    def test_validate_token_expired(self, jwt_service):
        """Test validating an expired JWT token."""
        service = jwt_service
        
        # Create expired token
        expire = datetime.now(timezone.utc) - timedelta(minutes=1)
        payload = {
            "sub": "123",
            "type": "access",
            "exp": expire.timestamp(),
            "iat": datetime.now(timezone.utc).timestamp()
        }
        
        expired_token = jwt.encode(payload, service.secret_key, algorithm=service.algorithm)
        
        # Validate expired token
        with pytest.raises(TokenError, match="Token has expired"):
            service.validate_token(expired_token)
        
        assert service.stats["validation_failures"] == 1
    
    def test_validate_token_invalid(self, jwt_service):
        """Test validating an invalid JWT token."""
        service = jwt_service
        
        invalid_token = "invalid.token.here"
        
        with pytest.raises(TokenError, match="Invalid token"):
            service.validate_token(invalid_token)
        
        assert service.stats["validation_failures"] == 1
    
    def test_refresh_access_token(self, jwt_service):
        """Test refreshing access token using refresh token."""
        service = jwt_service
        
        user_id = 123
        
        # Create refresh token
        refresh_token = service.create_refresh_token(user_id)
        
        # Refresh access token
        new_access_token, new_refresh_token = service.refresh_access_token(refresh_token)
        
        assert isinstance(new_access_token, str)
        assert isinstance(new_refresh_token, str)
        assert new_access_token != refresh_token
        assert new_refresh_token != refresh_token
        
        # Verify new tokens are valid
        access_payload = service.validate_token(new_access_token)
        refresh_payload = service.validate_token(new_refresh_token)
        
        assert access_payload["sub"] == str(user_id)
        assert access_payload["type"] == "access"
        assert refresh_payload["sub"] == str(user_id)
        assert refresh_payload["type"] == "refresh"
        
        assert service.stats["tokens_refreshed"] == 1
    
    def test_refresh_with_access_token(self, jwt_service):
        """Test attempting to refresh using access token (should fail)."""
        service = jwt_service
        
        # Create access token
        access_token = service.create_access_token(123)
        
        # Try to refresh with access token
        with pytest.raises(TokenError, match="Invalid token type for refresh"):
            service.refresh_access_token(access_token)


class TestAuthService:
    """Test cases for the AuthService class."""
    
    @pytest.fixture
    def auth_service_instance(self):
        """Create a test auth service instance."""
        return AuthService()
    
    @pytest.fixture
    def mock_user_profile(self):
        """Mock user profile from Google."""
        return {
            'email': 'test@example.com',
            'name': 'Test User',
            'photo_url': 'https://example.com/photo.jpg',
            'google_id': '123456789'
        }
    
    def test_auth_service_initialization(self, auth_service_instance):
        """Test auth service initialization."""
        service = auth_service_instance
        
        assert isinstance(service.google_auth, GoogleAuthService)
        assert isinstance(service.jwt_service, JWTService)
        assert service.password_context is not None
        assert isinstance(service.stats, dict)
    
    @pytest.mark.asyncio
    async def test_start_google_oauth_flow(self, auth_service_instance):
        """Test starting Google OAuth flow."""
        service = auth_service_instance
        
        auth_url, state = await service.start_google_oauth_flow()
        
        assert auth_url.startswith('https://accounts.google.com/o/oauth2/auth')
        assert len(state) > 10
    
    @pytest.mark.asyncio
    async def test_validate_access_token(self, auth_service_instance):
        """Test validating access token."""
        service = auth_service_instance
        
        user_id = 123
        band_id = 456
        role = "admin"
        instruments = ["trumpet"]
        
        # Create token
        token = service.jwt_service.create_access_token(
            user_id=user_id,
            band_id=band_id,
            role=role,
            instruments=instruments
        )
        
        # Validate token
        user_info = await service.validate_access_token(token)
        
        assert user_info["user_id"] == user_id
        assert user_info["band_id"] == band_id
        assert user_info["role"] == role
        assert user_info["instruments"] == instruments
    
    @pytest.mark.asyncio
    async def test_validate_invalid_token_type(self, auth_service_instance):
        """Test validating token with wrong type."""
        service = auth_service_instance
        
        # Create refresh token
        refresh_token = service.jwt_service.create_refresh_token(123)
        
        # Try to validate as access token
        with pytest.raises(AuthenticationError, match="Invalid token type"):
            await service.validate_access_token(refresh_token)
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, auth_service_instance):
        """Test refreshing tokens."""
        service = auth_service_instance
        
        # Create refresh token
        refresh_token = service.jwt_service.create_refresh_token(123)
        
        # Refresh tokens
        new_access_token, new_refresh_token = await service.refresh_token(refresh_token)
        
        assert isinstance(new_access_token, str)
        assert isinstance(new_refresh_token, str)
        assert new_access_token != refresh_token
        assert new_refresh_token != refresh_token
    
    @pytest.mark.asyncio
    async def test_check_permission_role(self, auth_service_instance):
        """Test role-based permission checking."""
        service = auth_service_instance
        
        # Admin user
        admin_info = {"role": "admin", "instruments": []}
        
        # Check admin can access admin endpoints
        assert await service.check_permission(admin_info, UserRole.ADMIN)
        assert await service.check_permission(admin_info, UserRole.LEADER)
        assert await service.check_permission(admin_info, UserRole.MEMBER)
        
        # Member user
        member_info = {"role": "member", "instruments": []}
        
        # Check member cannot access admin/leader endpoints
        assert not await service.check_permission(member_info, UserRole.ADMIN)
        assert not await service.check_permission(member_info, UserRole.LEADER)
        assert await service.check_permission(member_info, UserRole.MEMBER)
    
    @pytest.mark.asyncio
    async def test_check_permission_instruments(self, auth_service_instance):
        """Test instrument-based permission checking."""
        service = auth_service_instance
        
        user_info = {"role": "member", "instruments": ["trumpet", "piano"]}
        
        # Check user can access content for their instruments
        assert await service.check_permission(user_info, required_instruments=["trumpet"])
        assert await service.check_permission(user_info, required_instruments=["piano"])
        assert await service.check_permission(user_info, required_instruments=["trumpet", "guitar"])
        
        # Check user cannot access content for other instruments
        assert not await service.check_permission(user_info, required_instruments=["saxophone"])
        assert not await service.check_permission(user_info, required_instruments=["violin", "cello"])
    
    @pytest.mark.asyncio
    async def test_logout_user(self, auth_service_instance):
        """Test user logout."""
        service = auth_service_instance
        
        user_id = 123
        
        # Should not raise an exception
        await service.logout_user(user_id)
    
    def test_role_hierarchy(self, auth_service_instance):
        """Test role hierarchy logic."""
        service = auth_service_instance
        
        # Admin has all permissions
        assert service._role_has_permission(UserRole.ADMIN, UserRole.ADMIN)
        assert service._role_has_permission(UserRole.ADMIN, UserRole.LEADER)
        assert service._role_has_permission(UserRole.ADMIN, UserRole.MEMBER)
        
        # Leader has leader and member permissions
        assert not service._role_has_permission(UserRole.LEADER, UserRole.ADMIN)
        assert service._role_has_permission(UserRole.LEADER, UserRole.LEADER)
        assert service._role_has_permission(UserRole.LEADER, UserRole.MEMBER)
        
        # Member has only member permissions
        assert not service._role_has_permission(UserRole.MEMBER, UserRole.ADMIN)
        assert not service._role_has_permission(UserRole.MEMBER, UserRole.LEADER)
        assert service._role_has_permission(UserRole.MEMBER, UserRole.MEMBER)
    
    def test_stats_aggregation(self, auth_service_instance):
        """Test that stats are properly aggregated."""
        service = auth_service_instance
        
        stats = service.get_stats()
        
        assert "logins" in stats
        assert "google_auth" in stats
        assert "jwt_service" in stats
        assert isinstance(stats["google_auth"], dict)
        assert isinstance(stats["jwt_service"], dict)


class TestGlobalAuthFunctions:
    """Test global authentication convenience functions."""
    
    @pytest.mark.asyncio
    async def test_global_start_oauth_flow(self):
        """Test global OAuth flow start function."""
        auth_url, state = await start_oauth_flow()
        
        assert auth_url.startswith('https://accounts.google.com/o/oauth2/auth')
        assert len(state) > 10
    
    @pytest.mark.asyncio
    async def test_global_validate_token(self):
        """Test global token validation function."""
        # Create token using global service
        token = auth_service.jwt_service.create_access_token(123, role="member")
        
        user_info = await validate_token(token)
        
        assert user_info["user_id"] == 123
        assert user_info["role"] == "member"
    
    @pytest.mark.asyncio
    async def test_global_refresh_tokens(self):
        """Test global token refresh function."""
        # Create refresh token
        refresh_token = auth_service.jwt_service.create_refresh_token(123)
        
        new_access_token, new_refresh_token = await refresh_tokens(refresh_token)
        
        assert isinstance(new_access_token, str)
        assert isinstance(new_refresh_token, str)
    
    @pytest.mark.asyncio
    async def test_global_logout(self):
        """Test global logout function."""
        # Should not raise an exception
        await logout(123)
    
    @pytest.mark.asyncio
    async def test_global_check_permissions(self):
        """Test global permission checking function."""
        user_info = {"role": "admin", "instruments": ["trumpet"]}
        
        # Should have admin permissions
        assert await check_permissions(user_info, UserRole.ADMIN)
        assert await check_permissions(user_info, required_instruments=["trumpet"])
    
    def test_global_get_auth_stats(self):
        """Test global auth stats function."""
        stats = get_auth_stats()
        
        assert isinstance(stats, dict)
        assert "logins" in stats


class TestErrorHandling:
    """Test error handling in authentication service."""
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Test auth error")
    
    def test_authorization_error(self):
        """Test AuthorizationError exception."""
        with pytest.raises(AuthorizationError):
            raise AuthorizationError("Test auth error")
    
    def test_token_error(self):
        """Test TokenError exception."""
        with pytest.raises(TokenError):
            raise TokenError("Test token error")
    
    @pytest.mark.asyncio
    async def test_permission_check_error_handling(self):
        """Test that permission checks handle errors gracefully."""
        service = AuthService()
        
        # Malformed user info should return False, not raise exception
        malformed_info = {"invalid": "data"}
        
        result = await service.check_permission(malformed_info, UserRole.ADMIN)
        assert result is False


class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""
    
    @pytest.mark.asyncio
    @patch('app.services.auth.get_db_session')
    async def test_complete_oauth_flow_new_user(self, mock_get_session):
        """Test completing OAuth flow with new user."""
        # Mock database session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock no existing user
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        service = AuthService()
        
        # Mock Google auth methods
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.refresh_token = "refresh_token_123"
        
        profile = {
            'email': 'newuser@example.com',
            'name': 'New User',
            'photo_url': 'https://example.com/photo.jpg',
            'google_id': '123456789'
        }
        
        with patch.object(service.google_auth, 'exchange_code_for_tokens', return_value=mock_credentials), \
             patch.object(service.google_auth, 'get_user_profile', return_value=profile):
            
            access_token, refresh_token, user_info = await service.complete_google_oauth_flow(
                "auth_code_123", "state_123"
            )
            
            assert isinstance(access_token, str)
            assert isinstance(refresh_token, str)
            assert user_info["email"] == "newuser@example.com"
            assert user_info["name"] == "New User"
            
            # Verify user was added to session
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called()


# Test fixtures for integration testing
@pytest.fixture
def mock_google_credentials():
    """Mock Google OAuth credentials."""
    mock_creds = Mock(spec=Credentials)
    mock_creds.token = "access_token_123"
    mock_creds.refresh_token = "refresh_token_123"
    mock_creds.expired = False
    return mock_creds


@pytest.fixture
def sample_user_profile():
    """Sample user profile data."""
    return {
        'email': 'testuser@example.com',
        'name': 'Test User',
        'photo_url': 'https://example.com/photo.jpg',
        'google_id': '123456789012345'
    }


def test_jwt_token_lifecycle():
    """Test complete JWT token lifecycle."""
    service = JWTService()
    
    # Create tokens
    user_id = 123
    access_token = service.create_access_token(user_id, role="member")
    refresh_token = service.create_refresh_token(user_id)
    
    # Validate access token
    payload = service.validate_token(access_token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    
    # Use refresh token to get new tokens
    new_access_token, new_refresh_token = service.refresh_access_token(refresh_token)
    
    # Validate new tokens
    new_payload = service.validate_token(new_access_token)
    assert new_payload["sub"] == str(user_id)
    assert new_payload["type"] == "access"
    
    # Tokens should be different
    assert access_token != new_access_token
    assert refresh_token != new_refresh_token