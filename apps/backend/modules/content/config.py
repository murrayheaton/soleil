"""
Content Module Configuration
"""

from typing import List, Dict
from pydantic import Field
from modules.core.module_config import BaseModuleConfig


class ContentModuleConfig(BaseModuleConfig):
    """Configuration for the Content module"""
    
    # File Processing
    supported_audio_formats: List[str] = Field(
        default_factory=lambda: ['.mp3', '.wav', '.m4a', '.flac'],
        description="Supported audio file formats"
    )
    supported_chart_formats: List[str] = Field(
        default_factory=lambda: ['.pdf', '.jpg', '.jpeg', '.png'],
        description="Supported chart/sheet music formats"
    )
    max_file_size_mb: int = Field(
        default=100,
        description="Maximum file size in MB"
    )
    
    # Parsing Settings
    enable_auto_parsing: bool = Field(
        default=True,
        description="Automatically parse files on upload"
    )
    parse_timeout_seconds: int = Field(
        default=30,
        description="Timeout for parsing operations"
    )
    extract_metadata: bool = Field(
        default=True,
        description="Extract metadata from files"
    )
    
    # Instrument Mapping
    instrument_key_mapping: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "C": ["piano", "guitar", "bass", "violin", "flute", "vocals"],
            "Bb": ["trumpet", "clarinet", "tenor_sax", "soprano_sax"],
            "Eb": ["alto_sax", "baritone_sax"],
            "F": ["french_horn"]
        },
        description="Mapping of keys to instruments"
    )
    
    # Content Organization
    auto_organize: bool = Field(
        default=True,
        description="Automatically organize content by metadata"
    )
    organization_rules: Dict[str, str] = Field(
        default_factory=lambda: {
            "by_instrument": "/{instrument}/{title}",
            "by_genre": "/{genre}/{title}",
            "by_key": "/{key}/{title}"
        },
        description="Organization rule templates"
    )
    
    # Caching
    enable_content_cache: bool = Field(
        default=True,
        description="Enable content caching"
    )
    cache_ttl_hours: int = Field(
        default=24,
        description="Cache time-to-live in hours"
    )
    
    # Module specific
    module_name: str = Field(default="content")
    required_modules: List[str] = Field(
        default_factory=lambda: ["core", "auth"]
    )