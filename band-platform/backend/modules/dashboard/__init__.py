"""
Dashboard Module

Provides dashboard and analytics functionality.
"""

# Module metadata
MODULE_NAME = "dashboard"
MODULE_VERSION = "1.0.0"

# API routes
from .api import dashboard_routes

# Router alias for API gateway registration
router = dashboard_routes

__all__ = [
    # Module metadata
    "MODULE_NAME",
    "MODULE_VERSION",
    # API gateway
    "router",
    # API
    "dashboard_routes",
]