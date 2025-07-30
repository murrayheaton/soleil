"""
Google OAuth2 authentication endpoints.
Allows admin to authenticate once, then all users benefit from the connection.
"""

from fastapi import APIRouter, HTTPException
import logging

from ..services.google_drive_oauth import drive_oauth_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth2 login flow.
    Only admin needs to do this once.
    """
    auth_url = await drive_oauth_service.get_auth_url()
    return {
        "auth_url": auth_url,
        "message": "Visit the auth_url to authenticate with Google Drive"
    }

@router.get("/google/callback")
async def google_callback(code: str):
    """
    Handle Google OAuth2 callback.
    """
    success = await drive_oauth_service.handle_callback(code)
    
    if success:
        # Redirect to success page or return success message
        return {
            "status": "success",
            "message": "Google Drive authentication successful! The band platform can now access your Drive."
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Failed to authenticate with Google Drive"
        )

@router.get("/google/status")
async def google_auth_status():
    """
    Check if Google Drive is authenticated.
    """
    is_authenticated = await drive_oauth_service.authenticate()
    
    return {
        "authenticated": is_authenticated,
        "message": "Google Drive is connected" if is_authenticated else "Google Drive authentication required"
    }