"""
Folder organizer service compatibility layer.

This module provides backward compatibility by importing from the new content module.
All functionality has been migrated to modules.content.services.
"""
import warnings

# Import everything from the new content module for backward compatibility
from modules.content.services.file_organizer import *  # noqa: F403

# Show deprecation warning
warnings.warn(
    "Importing from app.services.folder_organizer is deprecated. "
    "Please import from modules.content.services.file_organizer instead.",
    DeprecationWarning,
    stacklevel=2
)