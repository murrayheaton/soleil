"""
Google Drive API routes.

This module provides endpoints for Google Drive operations including
authentication, file listing, and folder management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.api.role_helpers import get_current_user
from app.models.user import User
from ..services.drive_client import GoogleDriveService, DriveAPIError
from ..services.drive_auth import drive_oauth_service
from modules.content.services.soleil_content_parser import SOLEILContentParser, get_instrument_key

router = APIRouter(prefix="/drive", tags=["Drive"])

# Initialize content parser for instrument filtering
content_parser = SOLEILContentParser()


@router.get("/auth/url")
async def get_auth_url(
    redirect_uri: str = Query(..., description="OAuth redirect URI"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Get Google Drive OAuth authorization URL.

    Args:
        redirect_uri: URI to redirect to after authorization.
        current_user: Currently authenticated user.

    Returns:
        Dictionary containing the authorization URL.
    """
    try:
        auth_url = await drive_oauth_service.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate auth URL: {str(e)}"
        )


@router.post("/auth/callback")
async def handle_auth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Handle OAuth callback from Google.

    Args:
        code: Authorization code from Google OAuth.
        current_user: Currently authenticated user.

    Returns:
        Success message.
    """
    try:
        success = await drive_oauth_service.handle_callback(code)
        if success:
            return {"message": "Successfully authenticated with Google Drive"}
        else:
            raise HTTPException(status_code=400, detail="Failed to authenticate")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


@router.get("/folders/{folder_id}/files")
async def list_folder_files(
    folder_id: str,
    page_size: int = Query(100, ge=1, le=1000),
    query: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    List files in a Google Drive folder.

    Args:
        folder_id: Google Drive folder ID.
        page_size: Number of files per page.
        query: Optional search query.
        current_user: Currently authenticated user.

    Returns:
        List of file metadata.
    """
    try:
        # TODO: Get credentials for the user's band
        # For now, using the OAuth service credentials
        if not await drive_oauth_service.authenticate():
            raise HTTPException(
                status_code=401, detail="Not authenticated with Google Drive"
            )

        drive_service = GoogleDriveService(drive_oauth_service.creds)
        files = await drive_service.list_files(
            folder_id=folder_id, query=query, page_size=page_size
        )
        return files
    except DriveAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/files/{file_id}")
async def get_file_metadata(
    file_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get metadata for a specific file.

    Args:
        file_id: Google Drive file ID.
        current_user: Currently authenticated user.

    Returns:
        File metadata.
    """
    try:
        if not await drive_oauth_service.authenticate():
            raise HTTPException(
                status_code=401, detail="Not authenticated with Google Drive"
            )

        drive_service = GoogleDriveService(drive_oauth_service.creds)
        metadata = await drive_service.get_file_metadata(file_id)
        return metadata
    except DriveAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get file metadata: {str(e)}"
        )


@router.post("/folders/{folder_id}/sync")
async def sync_folder(
    folder_id: str,
    since: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Sync files from a Google Drive folder.

    Args:
        folder_id: Google Drive folder ID.
        since: Optional datetime to sync files modified since.
        current_user: Currently authenticated user.

    Returns:
        Sync results.
    """
    try:
        if not await drive_oauth_service.authenticate():
            raise HTTPException(
                status_code=401, detail="Not authenticated with Google Drive"
            )

        drive_service = GoogleDriveService(drive_oauth_service.creds)
        processed_files = await drive_service.process_files_for_sync(
            folder_id=folder_id, since=since
        )

        return {"files_processed": len(processed_files), "files": processed_files}
    except DriveAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync folder: {str(e)}")


@router.post("/webhook")
async def setup_webhook(
    folder_id: str = Query(..., description="Folder ID to watch"),
    webhook_url: str = Query(..., description="Webhook URL"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Set up a webhook for Google Drive changes.

    Args:
        folder_id: Google Drive folder ID to watch.
        webhook_url: URL to receive webhook notifications.
        current_user: Currently authenticated user.

    Returns:
        Webhook information.
    """
    try:
        if not await drive_oauth_service.authenticate():
            raise HTTPException(
                status_code=401, detail="Not authenticated with Google Drive"
            )

        drive_service = GoogleDriveService(drive_oauth_service.creds)
        webhook_info = await drive_service.setup_webhook(folder_id, webhook_url)
        return webhook_info
    except DriveAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to setup webhook: {str(e)}"
        )


@router.delete("/webhook/{channel_id}")
async def stop_webhook(
    channel_id: str,
    resource_id: str = Query(..., description="Resource ID from webhook setup"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Stop a webhook channel.

    Args:
        channel_id: Webhook channel ID.
        resource_id: Resource ID from webhook setup.
        current_user: Currently authenticated user.

    Returns:
        Success message.
    """
    try:
        if not await drive_oauth_service.authenticate():
            raise HTTPException(
                status_code=401, detail="Not authenticated with Google Drive"
            )

        drive_service = GoogleDriveService(drive_oauth_service.creds)
        await drive_service.stop_webhook(channel_id, resource_id)
        return {"message": "Webhook stopped successfully"}
    except DriveAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop webhook: {str(e)}")


@router.get("/stats")
async def get_drive_stats(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get Google Drive service statistics.

    Args:
        current_user: Currently authenticated user.

    Returns:
        Service statistics.
    """
    try:
        if not await drive_oauth_service.authenticate():
            raise HTTPException(
                status_code=401, detail="Not authenticated with Google Drive"
            )

        drive_service = GoogleDriveService(drive_oauth_service.creds)
        return drive_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/{instrument}-view")
async def get_instrument_view(
    instrument: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get files filtered by instrument for the current user.
    
    This endpoint implements the instrument-based filtering that the frontend expects.
    It returns only the charts and audio files relevant to the user's instrument.
    
    Supported instrument views:
    - Bb: Trumpet, Tenor Sax
    - Eb: Alto Sax, Bari Sax
    - Concert: Violin
    - BassClef: Trombone
    - Chords: Guitar, Piano, Bass, Drums (harmony section)
    - Lyrics: Singers
    
    Args:
        instrument: Instrument type (e.g., "Bb", "Eb", "Concert", "BassClef", "Chords", "Lyrics")
        current_user: Currently authenticated user.
        
    Returns:
        Dictionary containing filtered files organized by song.
    """
    try:
        # Authenticate with Google Drive
        if not await drive_oauth_service.authenticate():
            raise HTTPException(
                status_code=401, detail="Not authenticated with Google Drive"
            )
        
        # Get the user's instrument and transposition
        user_instrument = current_user.instrument.lower() if current_user.instrument else None
        user_transposition = get_instrument_key(user_instrument) if user_instrument else None
        
        # Validate that the requested instrument view matches the user's instrument
        if user_transposition and user_transposition != instrument:
            raise HTTPException(
                status_code=403, 
                detail=f"User instrument ({user_transposition}) doesn't match requested view ({instrument})"
            )
        
        # Get the band folder ID from environment (you'll need to set this)
        import os
        band_folder_id = os.getenv('GOOGLE_DRIVE_SOURCE_FOLDER_ID')
        if not band_folder_id:
            raise HTTPException(
                status_code=500, 
                detail="Band folder ID not configured. Please set GOOGLE_DRIVE_SOURCE_FOLDER_ID in environment."
            )
        
        # Create drive service and get files
        drive_service = GoogleDriveService(drive_oauth_service.creds)
        
        # Get all files in the band folder
        all_files = await drive_service.list_files(folder_id=band_folder_id)
        
        # Filter files by instrument and organize by song
        songs = {}
        
        for file_data in all_files:
            try:
                # Parse filename for musical information
                parsed = content_parser.parse_filename(file_data["name"])
                
                # Skip files that don't parse correctly
                if not parsed.song_title:
                    continue
                
                # Initialize song if not exists
                if parsed.song_title not in songs:
                    songs[parsed.song_title] = {
                        "song_title": parsed.song_title,
                        "charts": [],
                        "audio": [],
                        "total_files": 0
                    }
                
                # Add file to appropriate category
                file_info = {
                    "id": file_data["id"],
                    "name": file_data["name"],
                    "type": parsed.file_type.value,
                    "link": f"https://drive.google.com/file/d/{file_data['id']}/view",
                    "is_placeholder": "_X" in file_data["name"]  # Check for placeholder suffix
                }
                
                if parsed.file_type.value == "chart":
                    # Only add charts that match the instrument's transposition
                    if parsed.key == instrument:
                        songs[parsed.song_title]["charts"].append(file_info)
                        songs[parsed.song_title]["total_files"] += 1
                elif parsed.file_type.value == "audio":
                    # Add all audio files for the song
                    songs[parsed.song_title]["audio"].append(file_info)
                    songs[parsed.song_title]["total_files"] += 1
                    
            except Exception as e:
                # Log parsing errors but continue processing other files
                print(f"Error parsing file {file_data['name']}: {e}")
                continue
        
        # Convert to list and sort by song title
        songs_list = list(songs.values())
        songs_list.sort(key=lambda x: x["song_title"])
        
        return {
            "status": "success",
            "instrument": user_instrument or "unknown",
            "transposition": instrument,
            "songs": songs_list,
            "total_songs": len(songs_list),
            "message": f"Successfully loaded {len(songs_list)} songs for {instrument} instruments"
        }
        
    except DriveAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get instrument view: {str(e)}"
        )
