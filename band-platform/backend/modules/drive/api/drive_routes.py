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

router = APIRouter(prefix="/drive", tags=["Drive"])


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
