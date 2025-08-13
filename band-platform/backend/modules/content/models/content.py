"""
Content models for charts, audio, and other band content.

This module defines the data models used by the content API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Chart(BaseModel):
    """Chart model representing a musical chart file."""
    
    id: str = Field(..., description="Unique chart identifier (Google Drive file ID)")
    filename: str = Field(..., description="Original filename")
    title: str = Field(..., description="Chart title")
    instruments: List[str] = Field(default_factory=list, description="Instruments this chart is for")
    key: Optional[str] = Field(None, description="Musical key of the chart")
    tempo: Optional[str] = Field(None, description="Tempo marking")
    time_signature: Optional[str] = Field(None, description="Time signature")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    mime_type: str = Field(..., description="File MIME type")
    size: int = Field(..., description="File size in bytes")
    created_at: Optional[datetime] = Field(None, description="When the chart was created")
    modified_at: Optional[datetime] = Field(None, description="When the chart was last modified")
    google_drive_id: str = Field(..., description="Google Drive file ID")
    download_url: str = Field(..., description="URL to download the chart")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                "filename": "Take Five - Dave Brubeck - Bb Trumpet.pdf",
                "title": "Take Five",
                "instruments": ["Bb Trumpet", "Alto Sax"],
                "key": "Eb minor",
                "tempo": "Medium swing",
                "time_signature": "5/4",
                "difficulty": "Intermediate",
                "mime_type": "application/pdf",
                "size": 1048576,
                "created_at": "2024-01-15T10:30:00Z",
                "modified_at": "2024-01-20T14:45:00Z",
                "google_drive_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                "download_url": "/charts/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/download"
            }
        }


class ChartListResponse(BaseModel):
    """Response model for chart listing endpoints."""
    
    charts: List[Chart] = Field(..., description="List of charts")
    total: int = Field(..., description="Total number of charts available")
    limit: int = Field(..., description="Maximum number of charts returned")
    offset: int = Field(..., description="Number of charts skipped")
    
    class Config:
        json_schema_extra = {
            "example": {
                "charts": [
                    {
                        "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                        "filename": "Take Five - Dave Brubeck - Bb Trumpet.pdf",
                        "title": "Take Five",
                        "instruments": ["Bb Trumpet"],
                        "key": "Eb minor",
                        "tempo": "Medium swing",
                        "time_signature": "5/4",
                        "difficulty": "Intermediate",
                        "mime_type": "application/pdf",
                        "size": 1048576,
                        "created_at": "2024-01-15T10:30:00Z",
                        "modified_at": "2024-01-20T14:45:00Z",
                        "google_drive_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                        "download_url": "/charts/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/download"
                    }
                ],
                "total": 1,
                "limit": 50,
                "offset": 0
            }
        }


class Audio(BaseModel):
    """Audio file model."""
    
    id: str = Field(..., description="Unique audio identifier")
    filename: str = Field(..., description="Original filename")
    title: str = Field(..., description="Audio title")
    duration: Optional[float] = Field(None, description="Duration in seconds")
    mime_type: str = Field(..., description="File MIME type")
    size: int = Field(..., description="File size in bytes")
    stream_url: str = Field(..., description="URL to stream the audio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "audio_123",
                "filename": "Take Five - Full Band.mp3",
                "title": "Take Five - Full Band",
                "duration": 324.5,
                "mime_type": "audio/mpeg",
                "size": 5242880,
                "stream_url": "/audio/audio_123/stream"
            }
        }


class Setlist(BaseModel):
    """Setlist model for band performances."""
    
    id: str = Field(..., description="Unique setlist identifier")
    title: str = Field(..., description="Setlist title")
    date: Optional[datetime] = Field(None, description="Performance date")
    venue: Optional[str] = Field(None, description="Performance venue")
    charts: List[str] = Field(default_factory=list, description="List of chart IDs in the setlist")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "setlist_456",
                "title": "Jazz Night at The Blue Note",
                "date": "2024-02-15T20:00:00Z",
                "venue": "The Blue Note, NYC",
                "charts": ["chart_1", "chart_2", "chart_3"],
                "notes": "Standard jazz set, 2 sets of 45 minutes each"
            }
        }