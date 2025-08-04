"""
User model compatibility layer.

This module provides backward compatibility by importing from the new auth module.
All functionality has been migrated to modules.auth.models.
"""
import warnings

# Import everything from the new auth module for backward compatibility
from modules.auth.models import *

# Show deprecation warning
warnings.warn(
    "Importing from app.models.user is deprecated. "
    "Please import from modules.auth.models instead.",
    DeprecationWarning,
    stacklevel=2
)