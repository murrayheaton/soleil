"""
Sync Module Configuration
"""

from typing import List
from pydantic import Field
from modules.core.module_config import BaseModuleConfig


class SyncModuleConfig(BaseModuleConfig):
    """Configuration for the Sync module"""
    
    # WebSocket Settings
    websocket_heartbeat_interval: int = Field(
        default=30,
        description="WebSocket heartbeat interval in seconds"
    )
    websocket_timeout: int = Field(
        default=60,
        description="WebSocket connection timeout in seconds"
    )
    max_connections_per_user: int = Field(
        default=3,
        description="Maximum WebSocket connections per user"
    )
    
    # Sync Engine
    sync_batch_size: int = Field(
        default=100,
        description="Number of items to sync in one batch"
    )
    sync_interval_seconds: int = Field(
        default=300,  # 5 minutes
        description="Default sync interval in seconds"
    )
    enable_real_time_sync: bool = Field(
        default=True,
        description="Enable real-time synchronization"
    )
    
    # Event Broadcasting
    broadcast_buffer_size: int = Field(
        default=1000,
        description="Size of the broadcast event buffer"
    )
    event_ttl_seconds: int = Field(
        default=300,
        description="Time-to-live for broadcast events"
    )
    enable_event_compression: bool = Field(
        default=True,
        description="Enable compression for large events"
    )
    
    # Conflict Resolution
    conflict_resolution_strategy: str = Field(
        default="last_write_wins",
        description="Strategy for resolving sync conflicts"
    )
    track_sync_history: bool = Field(
        default=True,
        description="Track sync operation history"
    )
    history_retention_days: int = Field(
        default=30,
        description="Days to retain sync history"
    )
    
    # Performance
    worker_pool_size: int = Field(
        default=4,
        description="Size of the sync worker pool"
    )
    queue_size: int = Field(
        default=1000,
        description="Maximum sync queue size"
    )
    
    # Error Handling
    max_retry_attempts: int = Field(
        default=3,
        description="Maximum retry attempts for failed syncs"
    )
    retry_backoff_factor: float = Field(
        default=2.0,
        description="Backoff factor for retries"
    )
    
    # Module specific
    module_name: str = Field(default="sync")
    required_modules: List[str] = Field(
        default_factory=lambda: ["core", "auth", "content", "drive"]
    )