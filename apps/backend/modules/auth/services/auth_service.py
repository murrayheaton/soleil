"""
Main authentication service combining Google OAuth and JWT.

Provides complete authentication flow including user creation,
session management, and role-based access control.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google.oauth2.credentials import Credentials

from app.database.connection import get_db_session
from ..models.user import User, UserRole
from ..exceptions import AuthenticationError, TokenError
from .google_auth_service import GoogleAuthService
from .jwt_service import JWTService

logger = logging.getLogger(__name__)


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