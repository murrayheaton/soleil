"""
Content API routes for charts, audio, and setlists.

This module provides CRUD operations for band content with role-based
filtering and file streaming following the PRP requirements.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging

from ..models.content import Chart, ChartListResponse
from ..services.chart_service import ChartService

# Import app services with proper path handling
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.services.google_drive import GoogleDriveService, DriveAPIError, AuthenticationError
# Remove the broken import - we'll handle this differently
# from app.services.google_drive_oauth import drive_oauth_service
# from ..utils.auth import get_current_user  # TODO: Implement auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/charts", tags=["Content"], response_model=ChartListResponse)
async def list_charts(
    folder_id: Optional[str] = Query(None, description="Google Drive folder ID to list charts from"),
    instrument: Optional[str] = Query(None, description="Filter charts by instrument"),
    limit: int = Query(50, description="Maximum number of charts to return"),
    offset: int = Query(0, description="Number of charts to skip")
):
    """List charts with role-based filtering and Google Drive integration."""
    try:
        chart_service = ChartService()
        charts = await chart_service.list_charts(
            folder_id=folder_id,
            instrument=instrument,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"Successfully listed {len(charts)} charts")
        return ChartListResponse(
            charts=charts,
            total=len(charts),
            limit=limit,
            offset=offset
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Google Drive authentication required: {str(e)}")
    except DriveAPIError as e:
        logger.error(f"Google Drive API error: {e}")
        raise HTTPException(status_code=503, detail=f"Google Drive service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to list charts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list charts: {str(e)}")


@router.get("/charts/{chart_id}", tags=["Content"], response_model=Chart)
async def get_chart(chart_id: str):
    """Get chart metadata by ID with access control."""
    try:
        chart_service = ChartService()
        chart = await chart_service.get_chart(chart_id)
        
        if not chart:
            raise HTTPException(status_code=404, detail="Chart not found")
        
        logger.info(f"Successfully retrieved chart {chart_id}")
        return chart
        
    except HTTPException:
        raise
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Google Drive authentication required: {str(e)}")
    except DriveAPIError as e:
        logger.error(f"Google Drive API error: {e}")
        raise HTTPException(status_code=503, detail=f"Google Drive service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to get chart {chart_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chart: {str(e)}")


@router.get("/charts/{chart_id}/download", tags=["Content"])
async def download_chart(chart_id: str):
    """Download chart file with streaming from Google Drive."""
    try:
        chart_service = ChartService()
        file_stream = await chart_service.download_chart(chart_id)
        
        if not file_stream:
            raise HTTPException(status_code=404, detail="Chart file not found")
        
        # Get chart metadata for filename and content type
        chart = await chart_service.get_chart(chart_id)
        filename = chart.filename if chart else f"chart_{chart_id}.pdf"
        mime_type = chart.mime_type if chart and chart.mime_type else "application/pdf"
        
        logger.info(f"Successfully streaming chart {chart_id}")
        
        return StreamingResponse(
            file_stream,
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Google Drive authentication required: {str(e)}")
    except DriveAPIError as e:
        logger.error(f"Google Drive API error: {e}")
        raise HTTPException(status_code=503, detail=f"Google Drive service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to download chart {chart_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download chart: {str(e)}")


@router.get("/charts/search", tags=["Content"], response_model=ChartListResponse)
async def search_charts(
    query: str = Query(..., description="Search query for chart names or content"),
    folder_id: Optional[str] = Query(None, description="Google Drive folder ID to search in"),
    instrument: Optional[str] = Query(None, description="Filter by instrument"),
    limit: int = Query(20, description="Maximum number of results")
):
    """Search charts by name or content with Google Drive integration."""
    try:
        chart_service = ChartService()
        charts = await chart_service.search_charts(
            query=query,
            folder_id=folder_id,
            instrument=instrument,
            limit=limit
        )
        
        logger.info(f"Successfully searched charts with query '{query}', found {len(charts)} results")
        return ChartListResponse(
            charts=charts,
            total=len(charts),
            limit=limit,
            offset=0
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Google Drive authentication required: {str(e)}")
    except DriveAPIError as e:
        logger.error(f"Google Drive API error: {e}")
        raise HTTPException(status_code=503, detail=f"Google Drive service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to search charts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search charts: {str(e)}")


# Google Drive folder management endpoint
@router.get("/folders", tags=["Content"], summary="List chart folders")
async def list_chart_folders():
    """List available chart folders from Google Drive."""
    try:
        chart_service = ChartService()
        folders = await chart_service.get_chart_folders()
        return {"folders": folders}
    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Google Drive authentication required: {str(e)}")
    except DriveAPIError as e:
        logger.error(f"Google Drive API error: {e}")
        raise HTTPException(status_code=503, detail=f"Google Drive service unavailable: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to list chart folders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list folders: {str(e)}")


# Keep existing audio and setlist endpoints as-is for now
@router.get("/audio", tags=["Content"])
async def list_audio():
    """List audio files."""
    # TODO: Implement audio listing
    raise HTTPException(status_code=501, detail="Audio listing not implemented yet")


@router.get("/audio/{audio_id}/stream", tags=["Content"])
async def stream_audio(audio_id: int):
    """Stream audio file."""
    # TODO: Implement audio streaming
    raise HTTPException(status_code=501, detail="Audio streaming not implemented yet")


@router.get("/setlists", tags=["Content"])
async def list_setlists():
    """List setlists with real-time data."""
    # TODO: Implement setlist listing with Google Sheets integration
    raise HTTPException(status_code=501, detail="Setlist listing not implemented yet")


@router.get("/setlists/{setlist_id}", tags=["Content"])
async def get_setlist(setlist_id: int):
    """Get setlist with real-time updates."""
    # TODO: Implement setlist retrieval with real-time sync
    raise HTTPException(status_code=501, detail="Setlist listing not implemented yet")


# Google Drive Authentication Endpoints
@router.get("/auth/google/url", tags=["Content"], summary="Get Google OAuth URL")
async def get_google_auth_url():
    """Get Google OAuth authorization URL for Drive access."""
    try:
        auth_url = await GoogleDriveService.get_auth_url()
        return {"auth_url": auth_url, "message": "Visit this URL to authorize Google Drive access"}
    except Exception as e:
        logger.error(f"Failed to get Google auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get authentication URL: {str(e)}")


@router.post("/auth/google/callback", tags=["Content"], summary="Handle Google OAuth callback")
async def handle_google_callback(authorization_code: str):
    """Handle Google OAuth callback with authorization code."""
    try:
        success = await GoogleDriveService.handle_callback(authorization_code)
        if success:
            return {"message": "Google Drive authentication successful"}
        else:
            raise HTTPException(status_code=400, detail="Failed to authenticate with Google Drive")
    except Exception as e:
        logger.error(f"Failed to handle Google callback: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.get("/auth/google/status", tags=["Content"], summary="Check Google Drive auth status")
async def check_google_auth_status():
    """Check if Google Drive is authenticated and accessible."""
    try:
        authenticated = await GoogleDriveService.authenticate()
        if authenticated:
            return {
                "authenticated": True, 
                "message": "Google Drive access is configured and ready"
            }
        else:
            return {
                "authenticated": False, 
                "message": "Google Drive authentication required",
                "auth_url": await GoogleDriveService.get_auth_url()
            }
    except Exception as e:
        logger.error(f"Failed to check Google auth status: {e}")
        return {
            "authenticated": False, 
            "message": f"Authentication check failed: {str(e)}"
        }