"""
Authentication service with JWT tokens and Google OAuth integration.

This module handles user authentication, JWT token management, and Google OAuth 2.0
integration following the PRP requirements for secure band platform access.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import secrets

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import backoff

from ..config import settings
from ..database.connection import get_db_session
from ..models.user import User, UserRole

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthorizationError(Exception):
    """Custom exception for authorization errors."""
    pass


class TokenError(Exception):
    """Custom exception for token-related errors."""
    pass


class GoogleAuthService:
    """
    Google OAuth 2.0 authentication service.
    
    Handles Google OAuth flow, token management, and user profile retrieval.
    """
    
    def __init__(self):
        """Initialize the Google auth service."""
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        
        # OAuth 2.0 scopes required for the band platform
        self.scopes = [
            'openid',
            'email', 
            'profile',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/calendar'
        ]
        
        # Statistics
        self.stats = {
            "auth_attempts": 0,
            "auth_successes": 0,
            "auth_failures": 0,
            "token_refreshes": 0,
            "token_refresh_failures": 0,
        }
    
    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """
        Get Google OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection.
            
        Returns:
            Tuple of (authorization_url, state) where state is generated if not provided.
        """
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # Generate state if not provided
            if not state:
                state = secrets.token_urlsafe(32)
            
            # Get authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'  # Force consent to get refresh token
            )
            
            logger.debug(f"Generated OAuth authorization URL with state: {state}")
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            raise AuthenticationError(f"Failed to generate authorization URL: {e}")
    
    async def exchange_code_for_tokens(
        self, 
        authorization_code: str, 
        state: str
    ) -> Credentials:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: The authorization code from Google.
            state: The state parameter for CSRF validation.
            
        Returns:
            Google OAuth credentials with tokens.
        """
        try:
            self.stats["auth_attempts"] += 1
            
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri]
                    }
                },
                scopes=self.scopes,
                state=state
            )
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            self.stats["auth_successes"] += 1
            logger.info("Successfully exchanged authorization code for tokens")
            
            return credentials
            
        except Exception as e:
            self.stats["auth_failures"] += 1
            logger.error(f"Error exchanging authorization code: {e}")
            raise AuthenticationError(f"Failed to exchange code for tokens: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=60
    )
    async def get_user_profile(self, credentials: Credentials) -> Dict[str, Any]:
        """
        Get user profile information from Google.
        
        Args:
            credentials: Google OAuth credentials.
            
        Returns:
            User profile information.
        """
        try:
            # Refresh credentials if needed
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                self.stats["token_refreshes"] += 1
            
            # Build People API service
            service = build('people', 'v1', credentials=credentials)
            
            # Get user profile
            profile = service.people().get(
                resourceName='people/me',
                personFields='names,emailAddresses,photos'
            ).execute()
            
            # Extract relevant information
            email = None
            if 'emailAddresses' in profile:
                email = profile['emailAddresses'][0].get('value')
            
            name = None
            if 'names' in profile:
                name = profile['names'][0].get('displayName')
            
            photo_url = None
            if 'photos' in profile:
                photo_url = profile['photos'][0].get('url')
            
            return {
                'email': email,
                'name': name,
                'photo_url': photo_url,
                'google_id': profile.get('resourceName', '').replace('people/', '')
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise AuthenticationError(f"Failed to get user profile: {e}")
    
    async def refresh_credentials(self, credentials: Credentials) -> Credentials:
        """
        Refresh Google OAuth credentials.
        
        Args:
            credentials: Expired credentials to refresh.
            
        Returns:
            Refreshed credentials.
        """
        try:
            if not credentials.refresh_token:
                raise TokenError("No refresh token available")
            
            credentials.refresh(Request())
            self.stats["token_refreshes"] += 1
            
            logger.debug("Successfully refreshed Google credentials")
            return credentials
            
        except Exception as e:
            self.stats["token_refresh_failures"] += 1
            logger.error(f"Error refreshing credentials: {e}")
            raise TokenError(f"Failed to refresh credentials: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get authentication service statistics."""
        return self.stats.copy()


class JWTService:
    """
    JWT token service for local authentication.
    
    Handles creation, validation, and management of JWT tokens for API access.
    """
    
    def __init__(self):
        """Initialize the JWT service."""
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
        
        # Statistics
        self.stats = {
            "tokens_issued": 0,
            "tokens_validated": 0,
            "validation_failures": 0,
            "tokens_refreshed": 0,
        }
    
    def create_access_token(
        self, 
        user_id: int, 
        band_id: Optional[int] = None,
        role: Optional[str] = None,
        instruments: Optional[List[str]] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: The user ID.
            band_id: The user's band ID.
            role: The user's role in the band.
            instruments: List of instruments the user plays.
            
        Returns:
            JWT access token string.
        """
        try:
            # Token expiration
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
            
            # Token payload
            payload = {
                "sub": str(user_id),
                "band_id": band_id,
                "role": role,
                "instruments": instruments or [],
                "type": "access",
                "exp": expire.timestamp(),
                "iat": datetime.now(timezone.utc).timestamp(),
                "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
            }
            
            # Create token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            self.stats["tokens_issued"] += 1
            logger.debug(f"Created access token for user {user_id}")
            
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise TokenError(f"Failed to create access token: {e}")
    
    def create_refresh_token(self, user_id: int) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            user_id: The user ID.
            
        Returns:
            JWT refresh token string.
        """
        try:
            # Token expiration
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )
            
            # Token payload (minimal for refresh tokens)
            payload = {
                "sub": str(user_id),
                "type": "refresh",
                "exp": expire.timestamp(),
                "iat": datetime.now(timezone.utc).timestamp(),
                "jti": secrets.token_urlsafe(16)
            }
            
            # Create token
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            logger.debug(f"Created refresh token for user {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise TokenError(f"Failed to create refresh token: {e}")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate and decode a JWT token.
        
        Args:
            token: The JWT token to validate.
            
        Returns:
            Decoded token payload.
        """
        try:
            # Decode and validate token
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            self.stats["tokens_validated"] += 1
            return payload
            
        except jwt.ExpiredSignatureError:
            self.stats["validation_failures"] += 1
            raise TokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            self.stats["validation_failures"] += 1
            raise TokenError(f"Invalid token: {e}")
        except Exception as e:
            self.stats["validation_failures"] += 1
            raise TokenError(f"Token validation error: {e}")
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Create new access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token.
            
        Returns:
            Tuple of (new_access_token, new_refresh_token).
        """
        try:
            # Validate refresh token
            payload = self.validate_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise TokenError("Invalid token type for refresh")
            
            user_id = int(payload["sub"])
            
            # TODO: Get user details from database to include in new token
            # For now, create basic tokens
            new_access_token = self.create_access_token(user_id)
            new_refresh_token = self.create_refresh_token(user_id)
            
            self.stats["tokens_refreshed"] += 1
            logger.debug(f"Refreshed tokens for user {user_id}")
            
            return new_access_token, new_refresh_token
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise TokenError(f"Failed to refresh token: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get JWT service statistics."""
        return self.stats.copy()


class AuthService:
    """
    Main authentication service combining Google OAuth and JWT.
    
    Provides complete authentication flow including user creation,
    session management, and role-based access control.
    """
    
    def __init__(self):
        """Initialize the authentication service."""
        self.google_auth = GoogleAuthService()
        self.jwt_service = JWTService()
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Statistics
        self.stats = {
            "logins": 0,
            "login_failures": 0,
            "user_registrations": 0,
            "active_sessions": 0,
        }
    
    async def start_google_oauth_flow(
        self, 
        state: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Start Google OAuth flow.
        
        Args:
            state: Optional state parameter.
            
        Returns:
            Tuple of (authorization_url, state).
        """
        return self.google_auth.get_authorization_url(state)
    
    async def complete_google_oauth_flow(
        self,
        authorization_code: str,
        state: str
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Complete Google OAuth flow and create user session.
        
        Args:
            authorization_code: Authorization code from Google.
            state: State parameter for validation.
            
        Returns:
            Tuple of (access_token, refresh_token, user_info).
        """
        try:
            # Exchange code for credentials
            credentials = await self.google_auth.exchange_code_for_tokens(
                authorization_code, state
            )
            
            # Get user profile
            profile = await self.google_auth.get_user_profile(credentials)
            
            # Create or update user in database
            async with get_db_session() as session:
                user = await self._get_or_create_user(session, profile, credentials)
                
                # Create JWT tokens
                access_token = self.jwt_service.create_access_token(
                    user_id=user.id,
                    band_id=user.band_id,
                    role=user.role.value if user.role else None,
                    instruments=user.instruments
                )
                refresh_token = self.jwt_service.create_refresh_token(user.id)
                
                # Update user's last login
                user.last_login = datetime.now(timezone.utc)
                await session.commit()
                
                self.stats["logins"] += 1
                logger.info(f"User {user.email} logged in successfully")
                
                return access_token, refresh_token, {
                    "id": user.id,
                    "email": user.email,
                    "name": user.display_name,
                    "band_id": user.band_id,
                    "role": user.role.value if user.role else None,
                    "instruments": user.instruments
                }
        
        except Exception as e:
            self.stats["login_failures"] += 1
            logger.error(f"OAuth flow completion failed: {e}")
            raise AuthenticationError(f"Failed to complete OAuth flow: {e}")
    
    async def validate_access_token(self, token: str) -> Dict[str, Any]:
        """
        Validate access token and return user information.
        
        Args:
            token: JWT access token.
            
        Returns:
            User information from token.
        """
        try:
            payload = self.jwt_service.validate_token(token)
            
            if payload.get("type") != "access":
                raise TokenError("Invalid token type")
            
            return {
                "user_id": int(payload["sub"]),
                "band_id": payload.get("band_id"),
                "role": payload.get("role"),
                "instruments": payload.get("instruments", []),
                "exp": payload["exp"]
            }
            
        except Exception as e:
            logger.debug(f"Token validation failed: {e}")
            raise AuthenticationError(f"Invalid access token: {e}")
    
    async def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token.
            
        Returns:
            Tuple of (new_access_token, new_refresh_token).
        """
        return self.jwt_service.refresh_access_token(refresh_token)
    
    async def logout_user(self, user_id: int) -> None:
        """
        Logout user and invalidate tokens.
        
        Args:
            user_id: The user ID to logout.
        """
        # TODO: Implement token blacklisting/revocation
        # For now, just log the logout
        logger.info(f"User {user_id} logged out")
    
    async def check_permission(
        self,
        user_info: Dict[str, Any],
        required_role: Optional[UserRole] = None,
        required_instruments: Optional[List[str]] = None
    ) -> bool:
        """
        Check if user has required permissions.
        
        Args:
            user_info: User information from token validation.
            required_role: Required user role.
            required_instruments: Required instruments for access.
            
        Returns:
            True if user has required permissions.
        """
        try:
            # Check role requirement
            if required_role:
                user_role = UserRole(user_info.get("role", "member"))
                if not self._role_has_permission(user_role, required_role):
                    return False
            
            # Check instrument requirement
            if required_instruments:
                user_instruments = user_info.get("instruments", [])
                if not any(inst in user_instruments for inst in required_instruments):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    def _role_has_permission(self, user_role: UserRole, required_role: UserRole) -> bool:
        """Check if user role has required permission level."""
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.LEADER: 2,
            UserRole.MEMBER: 1
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    async def _get_or_create_user(
        self,
        session: AsyncSession,
        profile: Dict[str, Any],
        credentials: Credentials
    ) -> User:
        """Get existing user or create new one from OAuth profile."""
        try:
            # Look for existing user by email
            stmt = select(User).where(User.email == profile["email"])
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                # Update existing user
                user.display_name = profile.get("name") or user.display_name
                user.profile_image_url = profile.get("photo_url") or user.profile_image_url
                user.google_refresh_token = credentials.refresh_token or user.google_refresh_token
                user.is_active = True
                
                logger.debug(f"Updated existing user: {user.email}")
            else:
                # Create new user
                user = User(
                    email=profile["email"],
                    display_name=profile.get("name", ""),
                    profile_image_url=profile.get("photo_url"),
                    google_refresh_token=credentials.refresh_token,
                    role=UserRole.MEMBER,
                    is_active=True,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(user)
                
                self.stats["user_registrations"] += 1
                logger.info(f"Created new user: {user.email}")
            
            await session.flush()
            return user
            
        except Exception as e:
            logger.error(f"Error getting/creating user: {e}")
            raise AuthenticationError(f"Failed to process user: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get authentication service statistics."""
        return {
            **self.stats,
            "google_auth": self.google_auth.get_stats(),
            "jwt_service": self.jwt_service.get_stats()
        }


# Global authentication service instance
auth_service = AuthService()


# Convenience functions for authentication

async def start_oauth_flow(state: Optional[str] = None) -> Tuple[str, str]:
    """Start Google OAuth flow using global auth service."""
    return await auth_service.start_google_oauth_flow(state)


async def complete_oauth_flow(
    authorization_code: str,
    state: str
) -> Tuple[str, str, Dict[str, Any]]:
    """Complete OAuth flow using global auth service."""
    return await auth_service.complete_google_oauth_flow(authorization_code, state)


async def validate_token(token: str) -> Dict[str, Any]:
    """Validate access token using global auth service."""
    return await auth_service.validate_access_token(token)


async def refresh_tokens(refresh_token: str) -> Tuple[str, str]:
    """Refresh tokens using global auth service."""
    return await auth_service.refresh_token(refresh_token)


async def logout(user_id: int) -> None:
    """Logout user using global auth service."""
    await auth_service.logout_user(user_id)


async def check_permissions(
    user_info: Dict[str, Any],
    required_role: Optional[UserRole] = None,
    required_instruments: Optional[List[str]] = None
) -> bool:
    """Check permissions using global auth service."""
    return await auth_service.check_permission(user_info, required_role, required_instruments)


def get_auth_stats() -> Dict[str, Any]:
    """Get authentication statistics."""
    return auth_service.get_stats()