"""
Content models for charts, audio files, and setlists in the Band Platform.

This module defines the content management models with SQLAlchemy ORM
and Pydantic schemas following the PRP requirements for band content management.
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, 
    Text, Float, Date, Index
)
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, ConfigDict, validator

from app.database.connection import Base


class ContentType(str, Enum):
    """Types of content in the platform."""
    CHART = "chart"
    AUDIO = "audio"
    OTHER = "other"


class ChartType(str, Enum):
    """Types of charts/sheet music."""
    LEAD_SHEET = "lead_sheet"
    FULL_ARRANGEMENT = "full_arrangement"
    CHORD_CHART = "chord_chart"
    RHYTHM_CHART = "rhythm_chart"
    OTHER = "other"


class SetlistStatus(str, Enum):
    """Status of setlists."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# SQLAlchemy Models

class Chart(Base):
    """
    Chart model representing sheet music and musical arrangements.
    
    Charts are parsed from Google Drive based on naming conventions
    and filtered by instrument/key for role-based access.
    """
    __tablename__ = "charts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    title = Column(String(255), nullable=False, index=True)
    composer = Column(String(255), nullable=True)
    arranger = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    
    # Musical Information
    key = Column(String(10), nullable=False, index=True)  # e.g., "Bb", "Eb", "C"
    tempo = Column(String(50), nullable=True)  # e.g., "120 BPM", "Medium Swing"
    time_signature = Column(String(10), nullable=True)  # e.g., "4/4", "3/4"
    chart_type = Column(String(50), default=ChartType.LEAD_SHEET, index=True)
    
    # File Information
    google_drive_file_id = Column(String(255), nullable=False, unique=True, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    
    # Parsed Content
    parsed_metadata = Column(JSON, default=dict)  # Additional metadata from filename parsing
    tags = Column(JSON, default=list)  # Tags for filtering and search
    
    # Band Association
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False, index=True)
    
    # Status and Visibility
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False)  # Whether visible to all band members
    
    # Sync Information
    last_synced = Column(DateTime, nullable=True)
    google_modified_time = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="synced")  # synced, pending, error
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    band = relationship("Band", back_populates="charts")
    setlist_items = relationship("SetlistItem", back_populates="chart")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_chart_band_key', 'band_id', 'key'),
        Index('idx_chart_title_band', 'title', 'band_id'),
        Index('idx_chart_sync_status', 'sync_status', 'last_synced'),
    )
    
    def __repr__(self) -> str:
        return f"<Chart(id={self.id}, title='{self.title}', key='{self.key}')>"
    
    def is_accessible_by_user(self, user_instruments: List[str]) -> bool:
        """
        Check if this chart is accessible by a user based on their instruments.
        
        Args:
            user_instruments: List of instruments the user plays.
            
        Returns:
            True if the user can access this chart.
        """
        from ..services.content_parser import get_keys_for_instruments
        user_keys = get_keys_for_instruments(user_instruments)
        return self.key in user_keys


class Audio(Base):
    """
    Audio model representing reference recordings and backing tracks.
    
    Audio files are linked to charts and provide reference material for musicians.
    """
    __tablename__ = "audio"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    audio_type = Column(String(50), default="reference")  # reference, backing_track, demo
    
    # File Information
    google_drive_file_id = Column(String(255), nullable=False, unique=True, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Musical Information
    key = Column(String(10), nullable=True, index=True)
    tempo = Column(String(50), nullable=True)
    
    # Band Association
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False, index=True)
    
    # Chart Association (optional)
    related_chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True, index=True)
    
    # Status and Visibility
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False)
    
    # Sync Information
    last_synced = Column(DateTime, nullable=True)
    google_modified_time = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="synced")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    band = relationship("Band")
    related_chart = relationship("Chart")
    
    def __repr__(self) -> str:
        return f"<Audio(id={self.id}, title='{self.title}')>"


class Setlist(Base):
    """
    Setlist model representing ordered lists of songs for performances.
    
    Setlists are created and managed through Google Sheets integration
    and provide real-time updates to musicians.
    """
    __tablename__ = "setlists"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Performance Information
    performance_date = Column(Date, nullable=True, index=True)
    venue = Column(String(255), nullable=True)
    event_type = Column(String(100), nullable=True)  # concert, rehearsal, gig, etc.
    
    # Status
    status = Column(String(50), default=SetlistStatus.DRAFT, index=True)
    
    # Google Sheets Integration
    google_sheets_range = Column(String(100), nullable=True)  # e.g., "Sheet1!A1:F20"
    
    # Band Association
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False, index=True)
    
    # Timing Information
    estimated_duration_minutes = Column(Integer, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    
    # Sync Information
    last_synced = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="synced")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    band = relationship("Band", back_populates="setlists")
    items = relationship("SetlistItem", back_populates="setlist", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Setlist(id={self.id}, name='{self.name}')>"


class SetlistItem(Base):
    """
    Individual items within a setlist with ordering and timing information.
    """
    __tablename__ = "setlist_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Setlist Association
    setlist_id = Column(Integer, ForeignKey("setlists.id"), nullable=False, index=True)
    
    # Chart Association (optional - can have items without charts)
    chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True, index=True)
    
    # Ordering
    order_index = Column(Integer, nullable=False, index=True)
    
    # Item Information
    title = Column(String(255), nullable=False)  # Can override chart title
    key = Column(String(10), nullable=True)  # Can override chart key
    notes = Column(Text, nullable=True)
    
    # Timing
    estimated_duration_minutes = Column(Float, nullable=True)
    actual_duration_minutes = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    completed = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    setlist = relationship("Setlist", back_populates="items")
    chart = relationship("Chart", back_populates="setlist_items")
    
    # Indexes
    __table_args__ = (
        Index('idx_setlist_order', 'setlist_id', 'order_index'),
    )
    
    def __repr__(self) -> str:
        return f"<SetlistItem(id={self.id}, title='{self.title}', order={self.order_index})>"


# Pydantic Schemas

class ChartBase(BaseModel):
    """Base chart schema."""
    title: str = Field(..., min_length=1, max_length=255)
    composer: Optional[str] = Field(None, max_length=255)
    arranger: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    key: str = Field(..., description="Musical key (e.g., Bb, Eb, C)")
    tempo: Optional[str] = Field(None, max_length=50)
    time_signature: Optional[str] = Field(None, max_length=10)
    chart_type: ChartType = Field(default=ChartType.LEAD_SHEET)


class ChartCreate(ChartBase):
    """Schema for creating a chart."""
    google_drive_file_id: str = Field(..., description="Google Drive file ID")
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    band_id: int


class ChartUpdate(BaseModel):
    """Schema for updating a chart."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    composer: Optional[str] = Field(None, max_length=255)
    arranger: Optional[str] = Field(None, max_length=255)
    genre: Optional[str] = Field(None, max_length=100)
    key: Optional[str] = None
    tempo: Optional[str] = Field(None, max_length=50)
    time_signature: Optional[str] = Field(None, max_length=10)
    chart_type: Optional[ChartType] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class ChartSchema(ChartBase):
    """Complete chart schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    google_drive_file_id: str
    filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    parsed_metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    band_id: int
    is_active: bool
    is_public: bool
    last_synced: Optional[datetime] = None
    google_modified_time: Optional[datetime] = None
    sync_status: str
    created_at: datetime
    updated_at: datetime


class AudioBase(BaseModel):
    """Base audio schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    audio_type: str = Field(default="reference")
    key: Optional[str] = None
    tempo: Optional[str] = None


class AudioCreate(AudioBase):
    """Schema for creating audio."""
    google_drive_file_id: str = Field(..., description="Google Drive file ID")
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    duration_seconds: Optional[float] = None
    band_id: int
    related_chart_id: Optional[int] = None


class AudioUpdate(BaseModel):
    """Schema for updating audio."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    audio_type: Optional[str] = None
    key: Optional[str] = None
    tempo: Optional[str] = None
    related_chart_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class AudioSchema(AudioBase):
    """Complete audio schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    google_drive_file_id: str
    filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    duration_seconds: Optional[float] = None
    band_id: int
    related_chart_id: Optional[int] = None
    is_active: bool
    is_public: bool
    last_synced: Optional[datetime] = None
    google_modified_time: Optional[datetime] = None
    sync_status: str
    created_at: datetime
    updated_at: datetime


class SetlistItemBase(BaseModel):
    """Base setlist item schema."""
    title: str = Field(..., min_length=1, max_length=255)
    key: Optional[str] = None
    notes: Optional[str] = None
    estimated_duration_minutes: Optional[float] = Field(None, ge=0)
    order_index: int = Field(..., ge=0)


class SetlistItemCreate(SetlistItemBase):
    """Schema for creating a setlist item."""
    chart_id: Optional[int] = None


class SetlistItemUpdate(BaseModel):
    """Schema for updating a setlist item."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    key: Optional[str] = None
    notes: Optional[str] = None
    estimated_duration_minutes: Optional[float] = Field(None, ge=0)
    order_index: Optional[int] = Field(None, ge=0)
    chart_id: Optional[int] = None
    is_active: Optional[bool] = None
    completed: Optional[bool] = None


class SetlistItemSchema(SetlistItemBase):
    """Complete setlist item schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    setlist_id: int
    chart_id: Optional[int] = None
    actual_duration_minutes: Optional[float] = None
    is_active: bool
    completed: bool
    created_at: datetime
    updated_at: datetime
    
    # Optional chart information
    chart: Optional[ChartSchema] = None


class SetlistBase(BaseModel):
    """Base setlist schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    performance_date: Optional[date] = None
    venue: Optional[str] = Field(None, max_length=255)
    event_type: Optional[str] = Field(None, max_length=100)
    status: SetlistStatus = Field(default=SetlistStatus.DRAFT)


class SetlistCreate(SetlistBase):
    """Schema for creating a setlist."""
    band_id: int
    items: List[SetlistItemCreate] = Field(default_factory=list)


class SetlistUpdate(BaseModel):
    """Schema for updating a setlist."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    performance_date: Optional[date] = None
    venue: Optional[str] = Field(None, max_length=255)
    event_type: Optional[str] = Field(None, max_length=100)
    status: Optional[SetlistStatus] = None
    estimated_duration_minutes: Optional[int] = None


class SetlistSchema(SetlistBase):
    """Complete setlist schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    google_sheets_range: Optional[str] = None
    band_id: int
    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    last_synced: Optional[datetime] = None
    sync_status: str
    created_at: datetime
    updated_at: datetime
    
    # Items included by default
    items: List[SetlistItemSchema] = Field(default_factory=list)


class SetlistWithCharts(SetlistSchema):
    """Setlist schema with full chart information included."""
    items: List[SetlistItemSchema] = Field(default_factory=list)
    
    @validator('items', pre=True)
    def load_chart_info(cls, items):
        """Ensure chart information is loaded for each item."""
        # This would be handled by the API layer with proper joins
        return items


# Search and Filter Schemas

class ContentFilter(BaseModel):
    """Schema for filtering content."""
    search: Optional[str] = Field(None, description="Search in title, composer, or tags")
    key: Optional[str] = Field(None, description="Filter by musical key")
    genre: Optional[str] = Field(None, description="Filter by genre")
    chart_type: Optional[ChartType] = Field(None, description="Filter by chart type")
    is_public: Optional[bool] = Field(None, description="Filter by public/private status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    has_audio: Optional[bool] = Field(None, description="Filter charts that have related audio")


class ContentSearchResult(BaseModel):
    """Schema for content search results."""
    charts: List[ChartSchema] = Field(default_factory=list)
    audio: List[AudioSchema] = Field(default_factory=list)
    total_charts: int = 0
    total_audio: int = 0
    page: int = 1
    per_page: int = 20
    total_pages: int = 0