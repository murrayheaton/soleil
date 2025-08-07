"""
Folder structure models for Google Drive role-based organization.

This module defines the database models for tracking user-specific folder
structures and their synchronization with Google Drive.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, ConfigDict

from app.database.connection import Base


class SyncStatus(str, Enum):
    """Synchronization status for user folders."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    ERROR = "error"
    STALE = "stale"


# SQLAlchemy Models

class UserFolder(Base):
    """
    Tracks user-specific folder organization.
    
    Each user gets their own folder structure based on their role and instruments.
    This model tracks the root folder created for each user and its sync status.
    """
    __tablename__ = "user_folders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    google_folder_id = Column(String(255), nullable=False, index=True)  # User's root folder ID
    source_folder_id = Column(String(255), nullable=False, index=True)  # Admin's source folder ID
    
    # Sync tracking
    last_sync = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default=SyncStatus.PENDING, nullable=False, index=True)
    sync_error = Column(Text, nullable=True)  # Error message if sync fails
    file_count = Column(Integer, default=0)  # Number of files/shortcuts in structure
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_folder")
    song_folders = relationship("UserSongFolder", back_populates="user_folder", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<UserFolder(user_id={self.user_id}, status='{self.sync_status}')>"


class UserSongFolder(Base):
    """
    Tracks individual song folders within user's organization.
    
    Each song gets its own folder with appropriate shortcuts to files
    that the user can access based on their instruments.
    """
    __tablename__ = "user_song_folders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_folder_id = Column(Integer, ForeignKey("user_folders.id"), nullable=False, index=True)
    song_title = Column(String(255), nullable=False, index=True)
    google_folder_id = Column(String(255), nullable=False, index=True)  # Song folder ID in Drive
    
    # Content tracking
    shortcut_count = Column(Integer, default=0)  # Number of shortcuts in this folder
    chart_count = Column(Integer, default=0)     # Number of chart files
    audio_count = Column(Integer, default=0)     # Number of audio files
    
    # Sync tracking
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    needs_update = Column(Boolean, default=False, index=True)  # Flag for pending updates
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user_folder = relationship("UserFolder", back_populates="song_folders")
    
    def __repr__(self) -> str:
        return f"<UserSongFolder(song='{self.song_title}', shortcuts={self.shortcut_count})>"


class FolderSyncLog(Base):
    """
    Audit log for folder synchronization operations.
    
    Tracks all sync operations for debugging and monitoring purposes.
    """
    __tablename__ = "folder_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    operation = Column(String(100), nullable=False, index=True)  # 'create', 'update', 'sync'
    status = Column(String(50), nullable=False, index=True)      # 'success', 'error'
    
    # Operation details
    files_processed = Column(Integer, default=0)
    shortcuts_created = Column(Integer, default=0)
    shortcuts_deleted = Column(Integer, default=0)
    folders_created = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self) -> str:
        return f"<FolderSyncLog(user_id={self.user_id}, operation='{self.operation}', status='{self.status}')>"


# Pydantic Schemas for API validation

class UserFolderBase(BaseModel):
    """Base schema for user folder operations."""
    source_folder_id: str = Field(..., description="Google Drive source folder ID")


class UserFolderCreate(UserFolderBase):
    """Schema for creating a user folder structure."""
    user_id: int = Field(..., description="User ID to create folders for")


class UserFolderUpdate(BaseModel):
    """Schema for updating user folder information."""
    sync_status: Optional[SyncStatus] = None
    sync_error: Optional[str] = None
    file_count: Optional[int] = None


class UserFolderSchema(UserFolderBase):
    """Complete user folder schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    google_folder_id: str
    last_sync: Optional[datetime] = None
    sync_status: SyncStatus
    sync_error: Optional[str] = None
    file_count: int
    created_at: datetime
    updated_at: datetime


class UserSongFolderBase(BaseModel):
    """Base schema for user song folder operations."""
    song_title: str = Field(..., min_length=1, max_length=255, description="Song title")


class UserSongFolderSchema(UserSongFolderBase):
    """Complete user song folder schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_folder_id: int
    google_folder_id: str
    shortcut_count: int
    chart_count: int
    audio_count: int
    needs_update: bool
    last_updated: datetime
    created_at: datetime


class FolderSyncLogSchema(BaseModel):
    """Schema for folder sync log entries."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    operation: str
    status: str
    files_processed: int
    shortcuts_created: int
    shortcuts_deleted: int
    folders_created: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    error_count: int
    created_at: datetime


class FolderContentsResponse(BaseModel):
    """Response schema for user folder contents."""
    user_folder: UserFolderSchema
    song_folders: List[UserSongFolderSchema]
    total_files: int
    last_sync: Optional[datetime] = None
    sync_status: SyncStatus


class SyncStatusResponse(BaseModel):
    """Response schema for sync status queries."""
    user_id: int
    sync_status: SyncStatus
    last_sync: Optional[datetime] = None
    file_count: int
    song_count: int
    sync_error: Optional[str] = None
    estimated_sync_time: Optional[int] = None  # Seconds


class SyncTriggerResponse(BaseModel):
    """Response schema for manual sync triggers."""
    status: str = Field(..., description="Sync operation status")
    message: str = Field(..., description="Human-readable status message")
    estimated_duration: Optional[str] = None
    job_id: Optional[str] = None  # For tracking async operations