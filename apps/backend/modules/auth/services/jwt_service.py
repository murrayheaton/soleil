"""
JWT token service for local authentication.

Handles creation, validation, and management of JWT tokens for API access.
"""
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple

import jwt

from app.config import settings
from ..exceptions import TokenError

logger = logging.getLogger(__name__)


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