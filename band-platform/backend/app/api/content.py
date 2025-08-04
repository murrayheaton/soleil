"""
Content API compatibility layer.

This module provides backward compatibility by importing from the new content module.
All functionality has been migrated to modules.content.api.
"""
import warnings

# Import router from the new content module for backward compatibility
from modules.content.api.content_routes import router

# Show deprecation warning
warnings.warn(
    "Importing from app.api.content is deprecated. "
    "Please import from modules.content.api instead.",
    DeprecationWarning, 
    stacklevel=2
)