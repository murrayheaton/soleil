"""
User, Band, and Instrument data models for the Band Platform.

This module defines the core user management models with SQLAlchemy ORM
and Pydantic schemas for API validation following the PRP requirements.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from ..database.connection import Base


class UserRole(str, Enum):
    """User roles in the band platform."""
    MEMBER = "musician"
    MUSICIAN = MEMBER
    LEADER = "band_leader"
    BAND_LEADER = LEADER
    ADMIN = "admin"


class InstrumentFamily(str, Enum):
    """Instrument families for organization and filtering."""
    BRASS = "brass"
    WOODWIND = "woodwind"
    STRING = "string"
    PERCUSSION = "percussion"
    KEYBOARD = "keyboard"
    VOCAL = "vocal"
    OTHER = "other"


# SQLAlchemy Models

class Band(Base):
    """
    Band model representing a musical group or organization.
    
    Each band has its own Google Workspace integration and members.
    """
    __tablename__ = "bands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Google Workspace Integration
    google_drive_folder_id = Column(String(255), nullable=True, index=True)
    google_sheets_id = Column(String(255), nullable=True, index=True)
    google_calendar_id = Column(String(255), nullable=True, index=True)
    
    # Settings
    default_timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = relationship("User", back_populates="band", cascade="all, delete-orphan")
    charts = relationship("Chart", back_populates="band", cascade="all, delete-orphan")
    setlists = relationship("Setlist", back_populates="band", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Band(id={self.id}, name='{self.name}')>"


class User(Base):
    """
    User model representing musicians and administrators.
    
    Each user belongs to a band and has instrument assignments that determine
    which charts they can access based on the key mapping logic.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Optional for OAuth users
    name = Column(String(255), nullable=False)
    
    # Authentication
    google_id = Column(String(255), nullable=True, unique=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Band Association
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False, index=True)
    role = Column(String(50), default=UserRole.MEMBER, nullable=False, index=True)
    
    # Musical Information
    instruments = Column(JSON, nullable=False, default=list)  # List of instrument names
    primary_instrument = Column(String(100), nullable=True)  # Main instrument
    
    # Preferences
    preferred_key = Column(String(10), nullable=True)  # e.g., "Bb", "Eb", "C"
    notification_preferences = Column(JSON, default=dict)
    
    # Metadata
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    band = relationship("Band", back_populates="members")
    user_folder = relationship("UserFolder", back_populates="user", uselist=False)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in [UserRole.ADMIN, UserRole.BAND_LEADER]
    
    def get_preferred_keys(self) -> List[str]:
        """
        Get the preferred keys for this user based on their instruments.
        
        Returns:
            List of keys (e.g., ["Bb", "C"]) that match the user's instruments.
        """
        from ..services.content_parser import get_keys_for_instruments
        return get_keys_for_instruments(self.instruments)
    
    def get_user_folder_path(self) -> Optional[str]:
        """
        Get the Google Drive folder path for this user's organized files.
        
        Returns:
            Google Drive folder ID if user has a folder structure, None otherwise.
        """
        if self.user_folder and self.user_folder.google_folder_id:
            return self.user_folder.google_folder_id
        return None
    
    def needs_folder_reorganization(self) -> bool:
        """
        Check if user's folder structure needs reorganization.
        
        This could be due to instrument changes or sync errors.
        
        Returns:
            True if folders need reorganization.
        """
        if not self.user_folder:
            return True  # No folder structure exists
            
        # Check for sync errors
        if self.user_folder.sync_status == "error":
            return True
            
        # Check if folder structure is stale (>1 hour since last sync)
        if self.user_folder.last_sync:
            from datetime import datetime, timedelta
            if datetime.utcnow() - self.user_folder.last_sync > timedelta(hours=1):
                return True
                
        return False


class Instrument(Base):
    """
    Instrument model defining available instruments and their properties.
    
    This is used for validation and key mapping logic.
    """
    __tablename__ = "instruments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    family = Column(String(50), nullable=False, index=True)
    transposition_key = Column(String(10), nullable=False)  # e.g., "Bb", "Eb", "C"
    
    # Display properties
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Instrument(name='{self.name}', key='{self.transposition_key}')>"


# Pydantic Schemas for API validation

class BandBase(BaseModel):
    """Base band schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Band name")
    description: Optional[str] = Field(None, description="Band description")
    default_timezone: str = Field(default="UTC", description="Default timezone for the band")


class BandCreate(BandBase):
    """Schema for creating a new band."""
    google_drive_folder_id: Optional[str] = Field(None, description="Google Drive folder ID")
    google_sheets_id: Optional[str] = Field(None, description="Google Sheets ID")
    google_calendar_id: Optional[str] = Field(None, description="Google Calendar ID")


class BandUpdate(BaseModel):
    """Schema for updating a band."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    default_timezone: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    google_sheets_id: Optional[str] = None
    google_calendar_id: Optional[str] = None
    is_active: Optional[bool] = None


class BandSchema(BandBase):
    """Complete band schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    google_drive_folder_id: Optional[str] = None
    google_sheets_id: Optional[str] = None
    google_calendar_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Optional: include member count
    member_count: Optional[int] = None


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    instruments: List[str] = Field(default=[], description="List of instruments the user plays")
    primary_instrument: Optional[str] = Field(None, description="Primary instrument")
    role: UserRole = Field(default=UserRole.MEMBER, description="User role in the band")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: Optional[str] = Field(None, min_length=8, description="User password (optional for OAuth)")
    band_id: int = Field(..., description="ID of the band this user belongs to")


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    instruments: Optional[List[str]] = None
    primary_instrument: Optional[str] = None
    role: Optional[UserRole] = None
    preferred_key: Optional[str] = None
    notification_preferences: Optional[dict] = None
    is_active: Optional[bool] = None


class UserSchema(UserBase):
    """Complete user schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    google_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    band_id: int
    preferred_key: Optional[str] = None
    notification_preferences: dict
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    band: Optional[BandSchema] = None


class UserWithBand(UserSchema):
    """User schema with band information included."""
    band: BandSchema


class InstrumentBase(BaseModel):
    """Base instrument schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Instrument name")
    family: InstrumentFamily = Field(..., description="Instrument family")
    transposition_key: str = Field(..., description="Transposition key (e.g., Bb, Eb, C)")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Instrument description")


class InstrumentCreate(InstrumentBase):
    """Schema for creating a new instrument."""
    pass


class InstrumentUpdate(BaseModel):
    """Schema for updating an instrument."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    family: Optional[InstrumentFamily] = None
    transposition_key: Optional[str] = None
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class InstrumentSchema(InstrumentBase):
    """Complete instrument schema for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Authentication Schemas

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class GoogleAuthCallback(BaseModel):
    """Schema for Google OAuth callback."""
    code: str
    state: Optional[str] = None


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfile(BaseModel):
    """Schema for user profile information."""
    id: int
    email: str
    name: str
    role: UserRole
    band: BandSchema
    instruments: List[str]
    primary_instrument: Optional[str] = None
    preferred_key: Optional[str] = None
    last_login: Optional[datetime] = None