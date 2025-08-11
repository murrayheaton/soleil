"""
Drive Module

Manages Google Drive integration for the band platform.
"""

# Module metadata
MODULE_NAME = "drive"
MODULE_VERSION = "1.0.0"

# Core services
from .services.drive_client import GoogleDriveService, DriveAPIError
from .services.drive_auth import GoogleDriveOAuthService, drive_oauth_service
from .services.rate_limiter import RateLimiter, DynamicRateLimiter
from .services.cache_manager import CacheManager, cached

# Utilities
from .utils.drive_helpers import GoogleDriveAuth, test_drive_connection

# API routes
from .api import drive_routes

# Router alias for API gateway registration
router = drive_routes

# Models
from .models import (
    DriveFileType,
    DriveFile,
    DriveFileSchema,
    DriveWebhook,
    DriveWebhookSchema,
)

__all__ = [
    # Module metadata
    "MODULE_NAME",
    "MODULE_VERSION",
    # API gateway
    "router",
    # Services
    "GoogleDriveService",
    "GoogleDriveOAuthService",
    "drive_oauth_service",
    "RateLimiter",
    "DynamicRateLimiter",
    "CacheManager",
    "cached",
    # Errors
    "DriveAPIError",
    # Utilities
    "GoogleDriveAuth",
    "test_drive_connection",
    # API
    "drive_routes",
    # Models
    "DriveFileType",
    "DriveFile",
    "DriveFileSchema",
    "DriveWebhook",
    "DriveWebhookSchema",
]
