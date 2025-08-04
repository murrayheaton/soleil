"""
Content parser service compatibility layer.

This module provides backward compatibility by importing from the new content module.
All functionality has been migrated to modules.content.services.
"""
import warnings

# Import everything from the new content module for backward compatibility
from modules.content.services.content_parser import *

# Show deprecation warning
warnings.warn(
    "Importing from app.services.content_parser is deprecated. "
    "Please import from modules.content.services instead.",
    DeprecationWarning,
    stacklevel=2
)