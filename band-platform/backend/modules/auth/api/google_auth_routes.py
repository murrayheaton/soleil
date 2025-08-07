"""
Google OAuth2 authentication endpoints.
Allows admin to authenticate once, then all users benefit from the connection.
"""

from fastapi import APIRouter, HTTPException
import logging

from app.services.google_drive_oauth import drive_oauth_service

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
    Handle Google OAuth2 callback and set session cookies.
    """
    from fastapi import Response
    from fastapi.responses import RedirectResponse
    import jwt
    from datetime import datetime, timedelta
    
    success = await drive_oauth_service.handle_callback(code)
    
    if success:
        # Create session token
        JWT_SECRET = "your-secret-key-change-in-production"  # Should be in env vars
        JWT_ALGORITHM = "HS256"
        
        # Get user info from OAuth service (mock for now, should get from Google)
        user_info = {
            "id": "temp_user_id",
            "email": "",  # Will be filled by user in profile setup
            "name": "",   # Will be filled by user in profile setup
            "created_at": datetime.now().isoformat()
        }
        
        # Create access token (24 hours)
        access_payload = {
            "user": user_info,
            "exp": (datetime.now() + timedelta(hours=24)).timestamp()
        }
        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Create refresh token (7 days)
        refresh_payload = {
            "user": user_info,
            "exp": (datetime.now() + timedelta(days=7)).timestamp()
        }
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Create redirect response with cookies
        frontend_url = "http://localhost:3000"  # Should be from env
        response = RedirectResponse(
            url=f"{frontend_url}/profile?auth=success&new_user=true",
            status_code=302
        )
        
        # Set cookies with proper security settings
        response.set_cookie(
            key="soleil_session",
            value=access_token,
            max_age=86400,  # 24 hours
            httponly=True,
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )
        response.set_cookie(
            key="soleil_refresh",
            value=refresh_token,
            max_age=604800,  # 7 days
            httponly=True,
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )
        
        return response
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