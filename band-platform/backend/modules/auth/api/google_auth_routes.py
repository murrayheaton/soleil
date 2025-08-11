"""
Google OAuth2 authentication endpoints.
Allows admin to authenticate once, then all users benefit from the connection.
"""

from fastapi import APIRouter, HTTPException
import logging
import os

from app.services.google_drive_oauth import drive_oauth_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/google/login")
async def google_login():
    """
    Initiate Google OAuth2 login flow for user authentication.
    """
    # For user authentication, redirect to Google OAuth
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'https://solepower.live/api/auth/google/callback')
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline&"
        f"include_granted_scopes=true&"
        f"prompt=consent"
    )
    
    return {
        "auth_url": auth_url,
        "message": "Redirecting to Google OAuth for user authentication"
    }

@router.get("/google/callback")
async def google_callback(code: str):
    """
    Handle Google OAuth2 callback for user authentication.
    """
    from fastapi import Response
    from fastapi.responses import RedirectResponse
    import jwt
    import requests
    from datetime import datetime, timedelta
    
    try:
        # Exchange authorization code for tokens
        token_data = {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'https://solepower.live/api/auth/google/callback')
        }
        
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        tokens = response.json()
        
        if 'access_token' in tokens:
            # Get user info from Google
            user_info_response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f"Bearer {tokens['access_token']}"}
            )
            
            if user_info_response.status_code == 200:
                user_info = user_info_response.json()
                user_email = user_info.get('email', 'unknown')
                user_id = user_info.get('id', user_email)
                user_name = user_info.get('name', user_email.split('@')[0])
                
                # Create session token
                JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
                JWT_ALGORITHM = "HS256"
                
                # Create user info for session
                session_user_info = {
                    "id": user_id,
                    "email": user_email,
                    "name": user_name,
                    "created_at": datetime.now().isoformat()
                }
                
                # Create access token (24 hours)
                access_payload = {
                    "user": session_user_info,
                    "exp": (datetime.now() + timedelta(hours=24)).timestamp()
                }
                access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
                
                # Create refresh token (7 days)
                refresh_payload = {
                    "user": session_user_info,
                    "exp": (datetime.now() + timedelta(days=7)).timestamp()
                }
                refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
                
                # Create redirect response with cookies
                frontend_url = os.getenv('FRONTEND_URL', 'https://solepower.live')
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
                    secure=True  # Set to True in production with HTTPS
                )
                response.set_cookie(
                    key="soleil_refresh",
                    value=refresh_token,
                    max_age=604800,  # 7 days
                    httponly=True,
                    samesite="lax",
                    secure=True  # Set to True in production with HTTPS
                )
                
                return response
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to get user info from Google"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to get access token from Google"
            )
            
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Authentication failed"
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