"""
Auth validation endpoint for session checking
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from datetime import datetime, timedelta
import jwt
import json
from typing import Optional

router = APIRouter()

# JWT configuration
JWT_SECRET = "your-secret-key-change-in-production"  # Should be in env vars
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = timedelta(hours=24)


def get_current_user(request: Request) -> Optional[dict]:
    """Extract and validate user from session cookie"""
    # Check for session cookie
    session_token = request.cookies.get("soleil_session")
    if not session_token:
        return None
    
    try:
        # Decode JWT token
        payload = jwt.decode(session_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.now():
            return None
            
        return payload.get("user")
    except jwt.InvalidTokenError:
        return None


@router.get("/api/auth/validate")
async def validate_session(request: Request):
    """Validate current session and return user data"""
    user = get_current_user(request)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Check if profile is complete
    profile_complete = bool(user.get("name") and user.get("email"))
    
    return {
        "status": "success",
        "user": {
            "id": user.get("id", ""),
            "email": user.get("email", ""),
            "name": user.get("name", ""),
            "picture": user.get("picture", ""),
            "profile_complete": profile_complete,
            "created_at": user.get("created_at", datetime.now().isoformat())
        }
    }


@router.post("/api/auth/refresh")
async def refresh_session(request: Request):
    """Refresh session token"""
    # Check for refresh token
    refresh_token = request.cookies.get("soleil_refresh")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    
    try:
        # Decode refresh token
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = payload.get("user")
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Create new access token
        new_token_payload = {
            "user": user,
            "exp": (datetime.now() + JWT_EXPIRATION_DELTA).timestamp()
        }
        new_session_token = jwt.encode(new_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        response = {
            "status": "success",
            "user": user,
            "session_token": new_session_token
        }
        
        return response
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/api/auth/logout")
async def logout():
    """Logout user by clearing cookies"""
    response = {"status": "success", "message": "Logged out successfully"}
    return response