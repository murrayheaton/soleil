"""
Standard Event Types for SOLEil Modules

This module defines standard event types used for communication between modules.
All modules should use these constants for consistency.
"""

# Authentication Events
AUTH_STATE_CHANGED = "auth.state_changed"
AUTH_TOKEN_REFRESHED = "auth.token_refreshed"
AUTH_USER_LOGGED_IN = "auth.user_logged_in"
AUTH_USER_LOGGED_OUT = "auth.user_logged_out"
AUTH_PERMISSION_UPDATED = "auth.permission_updated"

# Content Events
CONTENT_UPDATED = "content.updated"
CONTENT_PARSED = "content.parsed"
CONTENT_DELETED = "content.deleted"
CONTENT_METADATA_CHANGED = "content.metadata_changed"

# Drive Events
DRIVE_FILE_CHANGED = "drive.file_changed"
DRIVE_FILE_ADDED = "drive.file_added"
DRIVE_FILE_REMOVED = "drive.file_removed"
DRIVE_FOLDER_CREATED = "drive.folder_created"
DRIVE_SYNC_STARTED = "drive.sync_started"
DRIVE_SYNC_COMPLETED = "drive.sync_completed"

# Sync Events
SYNC_STARTED = "sync.started"
SYNC_COMPLETED = "sync.completed"
SYNC_FAILED = "sync.failed"
SYNC_PROGRESS = "sync.progress"
SYNC_FILE_UPDATED = "sync.file_updated"

# Dashboard Events
DASHBOARD_MODULE_UPDATED = "dashboard.module_updated"
DASHBOARD_PREFERENCE_CHANGED = "dashboard.preference_changed"

# System Events
SYSTEM_ERROR = "system.error"
SYSTEM_WARNING = "system.warning"
SYSTEM_HEALTH_CHECK = "system.health_check"
MODULE_REGISTERED = "system.module_registered"
MODULE_UNREGISTERED = "system.module_unregistered"