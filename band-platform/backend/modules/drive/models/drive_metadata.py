"""
Google Drive metadata models.

This module defines models for tracking Drive-specific metadata,
file information, and sync state.
"""

from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, ConfigDict

from app.database.connection import Base


class DriveFileType(str, Enum):
    """Types of files in Google Drive."""

    FOLDER = "folder"
    CHART = "chart"
    AUDIO = "audio"
    SETLIST = "setlist"
    SHEET = "sheet"
    DOCUMENT = "document"
    OTHER = "other"


class DrivePermissionRole(str, Enum):
    """Google Drive permission roles."""

    OWNER = "owner"
    ORGANIZER = "organizer"
    FILE_ORGANIZER = "fileOrganizer"
    WRITER = "writer"
    COMMENTER = "commenter"
    READER = "reader"


# SQLAlchemy Models


class DriveFile(Base):
    """
    Track Google Drive files and their metadata.

    This model stores information about files in Google Drive
    to enable efficient syncing and tracking.
    """

    __tablename__ = "drive_files"

    id = Column(Integer, primary_key=True, index=True)

    # Google Drive identifiers
    google_file_id = Column(String(255), unique=True, nullable=False, index=True)
    google_parent_id = Column(String(255), nullable=True, index=True)

    # File information
    filename = Column(String(500), nullable=False)
    mime_type = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # DriveFileType enum
    size_bytes = Column(Integer, nullable=True)

    # Timestamps
    google_created_time = Column(DateTime, nullable=True)
    google_modified_time = Column(DateTime, nullable=True, index=True)
    last_synced_at = Column(DateTime, nullable=True)

    # Band association
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False, index=True)

    # Content association (if file has been processed)
    content_id = Column(Integer, nullable=True, index=True)
    content_type = Column(String(50), nullable=True)  # chart, audio, setlist

    # Parsed metadata
    parsed_title = Column(String(255), nullable=True)
    parsed_key = Column(String(10), nullable=True)
    parsed_metadata = Column(JSON, default=dict)

    # Sync tracking
    is_active = Column(Boolean, default=True, index=True)
    sync_error = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    band = relationship("Band")
    permissions = relationship(
        "DrivePermission", back_populates="file", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_drive_file_band_type", "band_id", "file_type"),
        Index("idx_drive_file_parent", "google_parent_id"),
        Index("idx_drive_file_content", "content_id", "content_type"),
    )

    def __repr__(self) -> str:
        return f"<DriveFile(id={self.id}, filename='{self.filename}', google_id='{self.google_file_id}')>"


class DrivePermission(Base):
    """
    Track permissions for Google Drive files.

    This helps manage access control and sharing settings.
    """

    __tablename__ = "drive_permissions"

    id = Column(Integer, primary_key=True, index=True)

    # File association
    file_id = Column(Integer, ForeignKey("drive_files.id"), nullable=False, index=True)

    # Permission details
    permission_id = Column(String(255), nullable=False)  # Google permission ID
    role = Column(String(50), nullable=False)  # DrivePermissionRole enum
    permission_type = Column(String(50), nullable=False)  # user, group, domain, anyone

    # User/email information
    email_address = Column(String(255), nullable=True, index=True)
    display_name = Column(String(255), nullable=True)

    # Permission settings
    allow_file_discovery = Column(Boolean, default=False)
    expiration_time = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    file = relationship("DriveFile", back_populates="permissions")

    def __repr__(self) -> str:
        return f"<DrivePermission(id={self.id}, role='{self.role}', email='{self.email_address}')>"


class DriveWebhook(Base):
    """
    Track active Google Drive webhooks.

    This helps manage webhook subscriptions and renewals.
    """

    __tablename__ = "drive_webhooks"

    id = Column(Integer, primary_key=True, index=True)

    # Webhook identifiers
    channel_id = Column(String(255), unique=True, nullable=False, index=True)
    resource_id = Column(String(255), nullable=False)
    resource_uri = Column(String(500), nullable=False)

    # Configuration
    folder_id = Column(String(255), nullable=False, index=True)  # Folder being watched
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False, index=True)
    webhook_url = Column(String(500), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    expiration_time = Column(DateTime, nullable=False, index=True)

    # Statistics
    events_received = Column(Integer, default=0)
    last_event_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    band = relationship("Band")

    def __repr__(self) -> str:
        return f"<DriveWebhook(id={self.id}, channel_id='{self.channel_id}', folder='{self.folder_id}')>"


# Pydantic Schemas


class DriveFileBase(BaseModel):
    """Base schema for Drive files."""

    filename: str
    mime_type: str
    file_type: DriveFileType
    size_bytes: Optional[int] = None
    parsed_title: Optional[str] = None
    parsed_key: Optional[str] = None


class DriveFileCreate(DriveFileBase):
    """Schema for creating a Drive file record."""

    google_file_id: str
    google_parent_id: Optional[str] = None
    band_id: int
    google_created_time: Optional[datetime] = None
    google_modified_time: Optional[datetime] = None
    parsed_metadata: Dict[str, Any] = Field(default_factory=dict)


class DriveFileUpdate(BaseModel):
    """Schema for updating a Drive file record."""

    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    google_modified_time: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    content_id: Optional[int] = None
    content_type: Optional[str] = None
    parsed_title: Optional[str] = None
    parsed_key: Optional[str] = None
    parsed_metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    sync_error: Optional[str] = None


class DriveFileSchema(DriveFileBase):
    """Complete Drive file schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    google_file_id: str
    google_parent_id: Optional[str] = None
    band_id: int
    google_created_time: Optional[datetime] = None
    google_modified_time: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    content_id: Optional[int] = None
    content_type: Optional[str] = None
    parsed_metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    sync_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DrivePermissionBase(BaseModel):
    """Base schema for Drive permissions."""

    role: DrivePermissionRole
    permission_type: str
    email_address: Optional[str] = None
    display_name: Optional[str] = None


class DrivePermissionCreate(DrivePermissionBase):
    """Schema for creating a Drive permission."""

    file_id: int
    permission_id: str
    allow_file_discovery: bool = False
    expiration_time: Optional[datetime] = None


class DrivePermissionSchema(DrivePermissionBase):
    """Complete Drive permission schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_id: int
    permission_id: str
    allow_file_discovery: bool
    expiration_time: Optional[datetime] = None
    created_at: datetime


class DriveWebhookBase(BaseModel):
    """Base schema for Drive webhooks."""

    folder_id: str
    band_id: int
    webhook_url: str


class DriveWebhookCreate(DriveWebhookBase):
    """Schema for creating a Drive webhook."""

    channel_id: str
    resource_id: str
    resource_uri: str
    expiration_time: datetime


class DriveWebhookUpdate(BaseModel):
    """Schema for updating a Drive webhook."""

    is_active: Optional[bool] = None
    events_received: Optional[int] = None
    last_event_at: Optional[datetime] = None


class DriveWebhookSchema(DriveWebhookBase):
    """Complete Drive webhook schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_id: str
    resource_id: str
    resource_uri: str
    is_active: bool
    expiration_time: datetime
    events_received: int
    last_event_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class DriveSyncStatus(BaseModel):
    """Drive sync status information."""

    total_files: int
    synced_files: int
    failed_files: int
    last_sync: Optional[datetime] = None
    active_webhooks: int
    next_webhook_expiry: Optional[datetime] = None
