"""Profile Module

Handles user profile management, instrument settings, and preferences.
"""
from .api import router as profile_router

# Module metadata
MODULE_NAME = "profile"
MODULE_VERSION = "1.0.0"

# Alias for compatibility
router = profile_router

__all__ = [
    # Router
    "profile_router",
    "router",
    # Module metadata
    "MODULE_NAME",
    "MODULE_VERSION",
]
