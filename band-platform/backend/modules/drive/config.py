"""
Drive Module Configuration
"""

from typing import List, Optional
from pydantic import Field
from modules.core.module_config import BaseModuleConfig


class DriveModuleConfig(BaseModuleConfig):
    """Configuration for the Drive module"""
    
    # Google Drive API
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google API key"
    )
    service_account_file: Optional[str] = Field(
        default=None,
        description="Path to service account JSON file"
    )
    scopes: List[str] = Field(
        default_factory=lambda: [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file'
        ],
        description="Google Drive API scopes"
    )
    
    # Rate Limiting
    requests_per_second: int = Field(
        default=10,
        description="Maximum requests per second"
    )
    burst_size: int = Field(
        default=20,
        description="Burst size for rate limiting"
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed requests"
    )
    retry_delay_seconds: int = Field(
        default=1,
        description="Delay between retry attempts"
    )
    
    # Caching
    enable_drive_cache: bool = Field(
        default=True,
        description="Enable Drive metadata caching"
    )
    cache_size_mb: int = Field(
        default=100,
        description="Maximum cache size in MB"
    )
    cache_ttl_minutes: int = Field(
        default=60,
        description="Cache time-to-live in minutes"
    )
    
    # Folder Structure
    root_folder_name: str = Field(
        default="SOLEil Music Library",
        description="Name of the root folder in Drive"
    )
    user_folder_prefix: str = Field(
        default="User_",
        description="Prefix for user-specific folders"
    )
    shared_folder_name: str = Field(
        default="Shared Resources",
        description="Name of the shared resources folder"
    )
    
    # File Handling
    chunk_size_bytes: int = Field(
        default=1048576,  # 1MB
        description="Chunk size for file downloads"
    )
    stream_buffer_size: int = Field(
        default=8192,
        description="Buffer size for streaming"
    )
    
    # Sync Settings
    sync_interval_minutes: int = Field(
        default=5,
        description="Interval for sync operations"
    )
    batch_size: int = Field(
        default=50,
        description="Batch size for bulk operations"
    )
    
    # Module specific
    module_name: str = Field(default="drive")
    required_modules: List[str] = Field(
        default_factory=lambda: ["core", "auth"]
    )