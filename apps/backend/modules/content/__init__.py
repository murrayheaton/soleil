"""
Content Module

Handles file parsing, organization, and instrument-based filtering for the band platform.
"""
from .api import router as content_router
from .services import ContentParser, InstrumentFilter, parse_filename, get_keys_for_instruments
from .models import (
    Chart, Audio, Setlist, UserFolder,
    ContentType, ChartType, SetlistStatus,
    ChartSchema, AudioSchema, SetlistSchema, UserFolderSchema
)

# Create module-level service instances
content_parser = ContentParser()
# TODO: Re-enable when auth module is available
# folder_organizer = FolderOrganizer()
instrument_filter = InstrumentFilter()

__all__ = [
    # Router
    "content_router",
    # Services
    "ContentParser",
    # "FolderOrganizer", 
    "InstrumentFilter",
    "content_parser",
    # "folder_organizer",
    "instrument_filter",
    # Utility functions
    "parse_filename",
    "get_keys_for_instruments",
    # Models
    "Chart",
    "Audio",
    "Setlist",
    "UserFolder",
    # Enums
    "ContentType",
    "ChartType", 
    "SetlistStatus",
    # Schemas
    "ChartSchema",
    "AudioSchema",
    "SetlistSchema",
    "UserFolderSchema",
]