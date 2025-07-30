"""
Main API routes for the Band Platform.

This module provides general API endpoints and utilities
following the PRP requirements for the band platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database.connection import get_db_session_dependency
from ..models.user import BandSchema, UserSchema

router = APIRouter()


@router.get("/", tags=["General"])
async def api_root():
    """
    API root endpoint with available routes information.
    
    Returns:
        dict: API information and available endpoints.
    """
    return {
        "message": "Band Platform API",
        "version": "1.0.0",
        "endpoints": {
            "authentication": "/api/auth",
            "content": "/api/content",
            "sync": "/api/sync",
            "users": "/api/users",
            "bands": "/api/bands",
            "health": "/health"
        },
        "documentation": "/docs",
        "websocket": "/ws"
    }


@router.get("/bands", response_model=List[BandSchema], tags=["Bands"])
async def list_bands(
    skip: int = Query(0, ge=0, description="Number of bands to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of bands to return"),
    search: Optional[str] = Query(None, description="Search bands by name"),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    List all bands with pagination and search.
    
    Args:
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        search: Optional search term for band names.
        session: Database session.
        
    Returns:
        List of band information.
    """
    # TODO: Implement after authentication is set up
    # This is a placeholder structure
    return []


@router.get("/bands/{band_id}", response_model=BandSchema, tags=["Bands"])
async def get_band(
    band_id: int,
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get band information by ID.
    
    Args:
        band_id: The band ID.
        session: Database session.
        
    Returns:
        Band information.
        
    Raises:
        HTTPException: If band not found.
    """
    # TODO: Implement after authentication is set up
    raise HTTPException(status_code=404, detail="Band not found")


@router.get("/users", response_model=List[UserSchema], tags=["Users"])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    band_id: Optional[int] = Query(None, description="Filter by band ID"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    List users with pagination and filtering.
    
    Args:
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        band_id: Optional band ID filter.
        role: Optional role filter.
        session: Database session.
        
    Returns:
        List of user information.
    """
    # TODO: Implement after authentication is set up
    return []


@router.get("/users/{user_id}", response_model=UserSchema, tags=["Users"])
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get user information by ID.
    
    Args:
        user_id: The user ID.
        session: Database session.
        
    Returns:
        User information.
        
    Raises:
        HTTPException: If user not found.
    """
    # TODO: Implement after authentication is set up
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/dashboard", tags=["Dashboard"])
async def get_dashboard_data(
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get dashboard data for the current user.
    
    This endpoint provides summary information for the user's dashboard
    including recent charts, upcoming gigs, and sync status.
    
    Args:
        session: Database session.
        
    Returns:
        Dashboard data including charts, setlists, and sync information.
    """
    # TODO: Implement after authentication is set up
    # This would include:
    # - Recent charts accessible to user
    # - Upcoming setlists/gigs
    # - Sync status
    # - Band information
    
    return {
        "user": None,  # Current user info
        "band": None,  # User's band info
        "recent_charts": [],  # Charts accessible to user
        "upcoming_setlists": [],  # Upcoming gigs/rehearsals
        "sync_status": {
            "last_sync": None,
            "status": "unknown",
            "files_synced": 0
        },
        "statistics": {
            "total_charts": 0,
            "total_audio": 0,
            "accessible_charts": 0  # Based on user's instruments
        }
    }


@router.get("/search", tags=["Search"])
async def search_content(
    q: str = Query(..., min_length=1, description="Search query"),
    content_type: Optional[str] = Query(None, description="Filter by content type (chart, audio)"),
    key: Optional[str] = Query(None, description="Filter by musical key"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Search across all content (charts, audio, setlists).
    
    This provides a unified search interface across all content types
    with role-based filtering based on the user's instruments.
    
    Args:
        q: Search query string.
        content_type: Optional content type filter.
        key: Optional musical key filter.
        limit: Maximum number of results.
        session: Database session.
        
    Returns:
        Search results with charts, audio, and setlists.
    """
    # TODO: Implement after authentication is set up
    # This would include:
    # - Full-text search across titles, composers, etc.
    # - Role-based filtering based on user's instruments
    # - Relevance scoring
    
    return {
        "query": q,
        "results": {
            "charts": [],
            "audio": [],
            "setlists": []
        },
        "total_results": 0,
        "filters_applied": {
            "content_type": content_type,
            "key": key,
            "user_instruments": []  # Would come from current user
        }
    }


@router.get("/instruments", tags=["Reference"])
async def list_instruments(
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    List all available instruments with their transposition keys.
    
    This provides reference information for instrument selection
    and key mapping logic.
    
    Returns:
        List of instruments with their properties.
    """
    from ..services.content_parser import INSTRUMENT_KEY_MAPPING
    
    # Group instruments by key
    instruments_by_key = {}
    for instrument, key in INSTRUMENT_KEY_MAPPING.items():
        if key not in instruments_by_key:
            instruments_by_key[key] = []
        
        # Convert to display format
        display_name = instrument.replace("_", " ").title()
        instruments_by_key[key].append({
            "name": instrument,
            "display_name": display_name,
            "key": key
        })
    
    return {
        "instruments_by_key": instruments_by_key,
        "all_keys": sorted(instruments_by_key.keys()),
        "total_instruments": len(INSTRUMENT_KEY_MAPPING)
    }


@router.get("/keys", tags=["Reference"])
async def list_musical_keys():
    """
    List all valid musical keys.
    
    Returns:
        List of valid musical keys for validation and reference.
    """
    from ..services.content_parser import VALID_KEYS
    
    # Separate major and minor keys
    major_keys = [key for key in VALID_KEYS if not key.endswith('m')]
    minor_keys = [key for key in VALID_KEYS if key.endswith('m')]
    
    return {
        "all_keys": sorted(list(VALID_KEYS)),
        "major_keys": sorted(major_keys),
        "minor_keys": sorted(minor_keys),
        "total_keys": len(VALID_KEYS)
    }


@router.get("/stats", tags=["Statistics"])
async def get_platform_statistics(
    session: AsyncSession = Depends(get_db_session_dependency)
):
    """
    Get platform-wide statistics.
    
    Provides overview statistics for monitoring and analytics.
    
    Returns:
        Platform statistics including content counts and sync status.
    """
    # TODO: Implement after authentication is set up
    # This would include:
    # - Total bands, users, charts, audio files
    # - Sync statistics
    # - Content parsing statistics
    # - Usage metrics
    
    return {
        "content": {
            "total_bands": 0,
            "total_users": 0,
            "total_charts": 0,
            "total_audio": 0,
            "total_setlists": 0
        },
        "sync": {
            "total_sync_operations": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "last_sync": None
        },
        "parsing": {
            "files_parsed": 0,
            "parsing_errors": 0,
            "by_file_type": {
                "chart": 0,
                "audio": 0,
                "other": 0
            }
        },
        "activity": {
            "active_users_today": 0,
            "files_accessed_today": 0,
            "searches_today": 0
        }
    }