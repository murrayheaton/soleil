"""
Authentication Module

Handles user authentication, authorization, and session management.
"""
from .api import router as auth_router
from .services import AuthService, GoogleAuthService, JWTService
from .models import User, UserRole, UserCreate, UserUpdate, UserSchema
from .exceptions import AuthenticationError, AuthorizationError, TokenError

# Create module-level service instance
auth_service = AuthService()

__all__ = [
    # Router
    "auth_router",
    # Services
    "AuthService",
    "GoogleAuthService", 
    "JWTService",
    "auth_service",
    # Models
    "User",
    "UserRole",
    "UserCreate",
    "UserUpdate",
    "UserSchema",
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    "TokenError",
]