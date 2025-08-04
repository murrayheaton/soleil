"""
Content model compatibility layer.

This module provides backward compatibility by importing from the new content module.
All functionality has been migrated to modules.content.models.
"""
import warnings

# Import everything from the new content module for backward compatibility  
from modules.content.models.content import *  # noqa: F403

# Show deprecation warning
warnings.warn(
    "Importing from app.models.content is deprecated. "
    "Please import from modules.content.models instead.",
    DeprecationWarning,
    stacklevel=2
)