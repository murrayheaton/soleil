"""
Sync models for tracking synchronization status and metadata with Google APIs.

This module defines the sync tracking models with SQLAlchemy ORM
and Pydantic schemas following the PRP requirements for real-time sync monitoring.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, 
    Text, Index
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, ConfigDict

from ..database.connection import Base


class SyncStatus(str, Enum):
    """Status of sync operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SyncType(str, Enum):
    """Types of sync operations."""
    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"
    WEBHOOK_SYNC = "webhook_sync"
    MANUAL_SYNC = "manual_sync"


class GoogleService(str, Enum):
    """Google services that can be synced."""
    DRIVE = "drive"
    SHEETS = "sheets"
    CALENDAR = "calendar"


# SQLAlchemy Models

class SyncOperation(Base):
    """
    Track sync operations between the band platform and Google APIs.
    
    This model provides detailed logging and monitoring of all sync activities
    for debugging and performance monitoring.
    """
    __tablename__ = "sync_operations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Operation Details
    operation_id = Column(String(255), unique=True, nullable=False, index=True)  # UUID for tracking
    sync_type = Column(String(50), nullable=False, index=True)
    google_service = Column(String(50), nullable=False, index=True)
    
    # Band Association
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False, index=True)
    
    # Status Tracking
    status = Column(String(50), default=SyncStatus.PENDING, nullable=False, index=True)
    
    # Timing Information
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Calculated field
    
    # Results
    items_processed = Column(Integer, default=0)
    items_created = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_deleted = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Error Information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, default=dict)  # Structured error information
    
    # Sync Parameters
    sync_parameters = Column(JSON, default=dict)  # Parameters used for the sync
    
    # Google API Information
    google_page_token = Column(String(255), nullable=True)  # For pagination
    google_start_token = Column(String(255), nullable=True)  # For delta sync
    google_webhook_id = Column(String(255), nullable=True)  # For webhook-triggered syncs
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    band = relationship("Band")
    sync_items = relationship("SyncItem", back_populates="sync_operation", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_sync_status_started', 'status', 'started_at'),
        Index('idx_sync_band_service', 'band_id', 'google_service'),
        Index('idx_sync_operation_date', 'started_at'),
    )
    
    def __repr__(self) -> str:
        return f"<SyncOperation(id={self.id}, operation_id='{self.operation_id}', status='{self.status}')>"
    
    def calculate_duration(self) -> None:
        """Calculate and update the duration of the sync operation."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())


class SyncItem(Base):
    """
    Track individual items processed during sync operations.
    
    This provides detailed logging of each file/item that was processed
    during a sync operation for debugging and audit purposes.
    """
    __tablename__ = "sync_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sync Operation Association
    sync_operation_id = Column(Integer, ForeignKey("sync_operations.id"), nullable=False, index=True)
    
    # Item Information
    google_file_id = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    item_type = Column(String(50), nullable=False)  # chart, audio, setlist, etc.
    
    # Processing Status
    status = Column(String(50), nullable=False, index=True)  # processed, failed, skipped
    action_taken = Column(String(50), nullable=False)  # created, updated, deleted, skipped
    
    # Content Information
    parsed_title = Column(String(255), nullable=True)
    parsed_key = Column(String(10), nullable=True)
    parsed_metadata = Column(JSON, default=dict)
    
    # Google API Information
    google_modified_time = Column(DateTime, nullable=True)
    google_size = Column(Integer, nullable=True)
    google_mime_type = Column(String(100), nullable=True)
    
    # Local Content Association
    content_id = Column(Integer, nullable=True, index=True)  # ID of created/updated content
    content_type = Column(String(50), nullable=True)  # chart, audio, setlist
    
    # Error Information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, default=dict)
    
    # Processing Time
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    sync_operation = relationship("SyncOperation", back_populates="sync_items")
    
    # Indexes
    __table_args__ = (
        Index('idx_sync_item_file_id', 'google_file_id'),
        Index('idx_sync_item_status', 'status', 'action_taken'),
    )
    
    def __repr__(self) -> str:
        return f"<SyncItem(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class WebhookEvent(Base):
    """
    Track webhook events received from Google APIs.
    
    This provides logging and tracking of all webhook notifications
    for debugging and ensuring no events are missed.
    """
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Webhook Information
    webhook_id = Column(String(255), nullable=False, index=True)  # Google channel ID
    resource_id = Column(String(255), nullable=False, index=True)  # Google resource ID
    resource_uri = Column(String(500), nullable=False)  # Google resource URI
    
    # Event Details
    event_type = Column(String(50), nullable=False, index=True)  # sync, add, remove, update
    google_service = Column(String(50), nullable=False, index=True)
    
    # Headers and Data
    headers = Column(JSON, default=dict)  # HTTP headers from webhook
    payload = Column(JSON, default=dict)  # Webhook payload
    
    # Processing Status
    processed = Column(Boolean, default=False, index=True)
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Associated Sync Operation
    sync_operation_id = Column(Integer, ForeignKey("sync_operations.id"), nullable=True, index=True)
    
    # Metadata
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    sync_operation = relationship("SyncOperation")
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_processed', 'processed', 'received_at'),
        Index('idx_webhook_resource', 'resource_id', 'event_type'),
    )
    
    def __repr__(self) -> str:
        return f"<WebhookEvent(id={self.id}, webhook_id='{self.webhook_id}', event_type='{self.event_type}')>"


class SyncConfiguration(Base):
    """
    Store sync configuration settings for each band.
    
    This allows customization of sync behavior per band.
    """
    __tablename__ = "sync_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Band Association
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False, unique=True, index=True)
    
    # Sync Settings
    auto_sync_enabled = Column(Boolean, default=True)
    sync_interval_minutes = Column(Integer, default=15)  # How often to sync
    
    # Google Service Configuration
    drive_sync_enabled = Column(Boolean, default=True)
    sheets_sync_enabled = Column(Boolean, default=True)
    calendar_sync_enabled = Column(Boolean, default=True)
    
    # Webhook Configuration
    webhook_enabled = Column(Boolean, default=True)
    webhook_secret = Column(String(255), nullable=True)
    
    # File Filtering
    file_extensions_allowed = Column(JSON, default=lambda: [".pdf", ".mp3", ".wav", ".m4a"])
    ignore_patterns = Column(JSON, default=list)  # Patterns to ignore during sync
    
    # Performance Settings
    batch_size = Column(Integer, default=100)  # Number of items to process per batch
    rate_limit_delay_ms = Column(Integer, default=100)  # Delay between API calls
    
    # Last Sync Information
    last_full_sync = Column(DateTime, nullable=True)
    last_incremental_sync = Column(DateTime, nullable=True)
    next_sync_token = Column(String(255), nullable=True)  # Google API sync token
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    band = relationship("Band")
    
    def __repr__(self) -> str:
        return f"<SyncConfiguration(id={self.id}, band_id={self.band_id})>"


# Pydantic Schemas

class SyncOperationBase(BaseModel):
    """Base sync operation schema."""
    sync_type: SyncType
    google_service: GoogleService
    sync_parameters: Dict[str, Any] = Field(default_factory=dict)


class SyncOperationCreate(SyncOperationBase):
    """Schema for creating a sync operation."""
    band_id: int


class SyncOperationUpdate(BaseModel):
    """Schema for updating a sync operation."""
    status: Optional[SyncStatus] = None
    completed_at: Optional[datetime] = None
    items_processed: Optional[int] = None
    items_created: Optional[int] = None
    items_updated: Optional[int] = None
    items_deleted: Optional[int] = None
    items_failed: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    google_page_token: Optional[str] = None
    google_start_token: Optional[str] = None


class SyncOperationSchema(SyncOperationBase):
    """Complete sync operation schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    operation_id: str
    band_id: int
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    items_processed: int
    items_created: int
    items_updated: int
    items_deleted: int
    items_failed: int
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)
    google_page_token: Optional[str] = None
    google_start_token: Optional[str] = None
    google_webhook_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SyncItemBase(BaseModel):
    """Base sync item schema."""
    google_file_id: str
    filename: str
    item_type: str
    status: str
    action_taken: str
    parsed_title: Optional[str] = None
    parsed_key: Optional[str] = None


class SyncItemCreate(SyncItemBase):
    """Schema for creating a sync item."""
    sync_operation_id: int
    parsed_metadata: Dict[str, Any] = Field(default_factory=dict)
    google_modified_time: Optional[datetime] = None
    google_size: Optional[int] = None
    google_mime_type: Optional[str] = None


class SyncItemSchema(SyncItemBase):
    """Complete sync item schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    sync_operation_id: int
    parsed_metadata: Dict[str, Any] = Field(default_factory=dict)
    google_modified_time: Optional[datetime] = None
    google_size: Optional[int] = None
    google_mime_type: Optional[str] = None
    content_id: Optional[int] = None
    content_type: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)
    processed_at: datetime


class WebhookEventBase(BaseModel):
    """Base webhook event schema."""
    webhook_id: str
    resource_id: str
    resource_uri: str
    event_type: str
    google_service: GoogleService


class WebhookEventCreate(WebhookEventBase):
    """Schema for creating a webhook event."""
    headers: Dict[str, str] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)


class WebhookEventUpdate(BaseModel):
    """Schema for updating a webhook event."""
    processed: Optional[bool] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    sync_operation_id: Optional[int] = None


class WebhookEventSchema(WebhookEventBase):
    """Complete webhook event schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    headers: Dict[str, str] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    processed: bool
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    sync_operation_id: Optional[int] = None
    received_at: datetime


class SyncConfigurationBase(BaseModel):
    """Base sync configuration schema."""
    auto_sync_enabled: bool = True
    sync_interval_minutes: int = Field(default=15, ge=1, le=1440)  # 1 minute to 24 hours
    drive_sync_enabled: bool = True
    sheets_sync_enabled: bool = True
    calendar_sync_enabled: bool = True
    webhook_enabled: bool = True


class SyncConfigurationCreate(SyncConfigurationBase):
    """Schema for creating sync configuration."""
    band_id: int
    webhook_secret: Optional[str] = None
    file_extensions_allowed: List[str] = Field(default=[".pdf", ".mp3", ".wav", ".m4a"])
    ignore_patterns: List[str] = Field(default_factory=list)
    batch_size: int = Field(default=100, ge=1, le=1000)
    rate_limit_delay_ms: int = Field(default=100, ge=0, le=5000)


class SyncConfigurationUpdate(BaseModel):
    """Schema for updating sync configuration."""
    auto_sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    drive_sync_enabled: Optional[bool] = None
    sheets_sync_enabled: Optional[bool] = None
    calendar_sync_enabled: Optional[bool] = None
    webhook_enabled: Optional[bool] = None
    webhook_secret: Optional[str] = None
    file_extensions_allowed: Optional[List[str]] = None
    ignore_patterns: Optional[List[str]] = None
    batch_size: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_delay_ms: Optional[int] = Field(None, ge=0, le=5000)


class SyncConfigurationSchema(SyncConfigurationBase):
    """Complete sync configuration schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    band_id: int
    webhook_secret: Optional[str] = None
    file_extensions_allowed: List[str]
    ignore_patterns: List[str]
    batch_size: int
    rate_limit_delay_ms: int
    last_full_sync: Optional[datetime] = None
    last_incremental_sync: Optional[datetime] = None
    next_sync_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Sync Status and Statistics Schemas

class SyncStatistics(BaseModel):
    """Sync statistics for monitoring and dashboard."""
    total_operations: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    in_progress_operations: int = 0
    total_items_processed: int = 0
    total_items_created: int = 0
    total_items_updated: int = 0
    total_items_deleted: int = 0
    total_items_failed: int = 0
    average_duration_seconds: Optional[float] = None
    last_successful_sync: Optional[datetime] = None
    last_failed_sync: Optional[datetime] = None


class SyncHealthCheck(BaseModel):
    """Sync health check response."""
    is_healthy: bool
    google_drive_accessible: bool
    google_sheets_accessible: bool
    google_calendar_accessible: bool
    webhook_endpoint_active: bool
    last_sync_age_minutes: Optional[int] = None
    pending_webhook_events: int = 0
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)