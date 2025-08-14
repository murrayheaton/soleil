"""
Content Module

Handles file parsing, organization, and instrument-based filtering for the band platform.
"""
from .api import router as content_router
from .services import ChartService
from .services.soleil_content_parser import SOLEILContentParser, parse_filename, get_instrument_key, is_chart_accessible_by_user

# Module metadata
MODULE_NAME = "content"
MODULE_VERSION = "1.0.0"

# Alias for compatibility
router = content_router
from .models import (
    Chart, Audio, Setlist
)

# Create module-level service instances
soleil_parser = SOLEILContentParser()
# chart_service = ChartService()  # Temporarily disabled due to import issues

__all__ = [
    # Router
    "content_router",
    "router",
    # Module metadata
    "MODULE_NAME",
    "MODULE_VERSION",
    # Services
    "SOLEILContentParser",
    "ChartService",
    "soleil_parser",
    "chart_service",
    # Utility functions
    "parse_filename",
    "get_instrument_key",
    "is_chart_accessible_by_user",
    # Models
    "Chart",
    "Audio",
    "Setlist",
]