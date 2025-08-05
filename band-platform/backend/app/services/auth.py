"""
Authentication service compatibility layer.

This module provides backward compatibility by importing from the new auth module.
All functionality has been migrated to modules.auth.
"""
import warnings
from typing import Dict, List, Optional, Any, Tuple

# Import everything from the new auth module for backward compatibility
from modules.auth import *
from modules.auth.services import *
from modules.auth.exceptions import *
from modules.auth.models import *

# Show deprecation warning
warnings.warn(
    "Importing from app.services.auth is deprecated. "
    "Please import from modules.auth instead.",
    DeprecationWarning,
    stacklevel=2
)

# Create global auth service instance for backward compatibility
auth_service = AuthService()

# Re-export convenience functions for backward compatibility
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
    required_role: Optional['UserRole'] = None,
    required_instruments: Optional[List[str]] = None
) -> bool:
    """Check permissions using global auth service."""
    return await auth_service.check_permission(user_info, required_role, required_instruments)


def get_auth_stats() -> Dict[str, Any]:
    """Get authentication statistics."""
    return auth_service.get_stats()