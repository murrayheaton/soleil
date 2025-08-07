"""
User profile management endpoints
"""
from fastapi import APIRouter, Request, HTTPException, Response
import json
import os
from datetime import datetime
import jwt

router = APIRouter()

# JWT configuration (should match validate.py)
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"


def get_user_from_session(request: Request) -> dict:
    """Extract user from session token"""
    session_token = request.cookies.get("soleil_session")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(session_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user", {})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session")


@router.post("/api/user/profile")
async def save_user_profile(request: Request, response: Response):
    """Save user profile after OAuth"""
    # Get user from session
    user = get_user_from_session(request)
    
    # Get profile data from request
    profile_data = await request.json()
    
    # Ensure we have required fields
    if not profile_data.get("email") or not profile_data.get("name"):
        raise HTTPException(status_code=400, detail="Email and name are required")
    
    # Load existing profiles
    profiles_file = "user_profiles.json"
    profiles = {}
    
    if os.path.exists(profiles_file):
        try:
            with open(profiles_file, "r") as f:
                profiles = json.load(f)
        except:
            profiles = {}
    
    # Use email as unique identifier
    user_id = profile_data.get("email")
    
    # Merge with existing user data
    profile_data["id"] = user.get("id", user_id)
    profile_data["created_at"] = user.get("created_at", datetime.now().isoformat())
    profile_data["updated_at"] = datetime.now().isoformat()
    profile_data["profile_complete"] = True
    
    # Save profile
    profiles[user_id] = profile_data
    
    with open(profiles_file, "w") as f:
        json.dump(profiles, f, indent=2)
    
    # Set profile complete cookie
    response.set_cookie(
        key="soleil_profile_complete",
        value="true",
        max_age=86400 * 30,  # 30 days
        httponly=False,
        samesite="lax"
    )
    
    # Also ensure auth cookie is set for middleware
    response.set_cookie(
        key="soleil_auth",
        value="true",
        max_age=86400,
        httponly=False,
        samesite="lax"
    )
    
    return {
        "status": "success",
        "profile": profile_data,
        "message": "Profile saved successfully"
    }


@router.get("/api/user/profile")
async def get_user_profile(request: Request):
    """Get current user profile"""
    # Get user from session
    user = get_user_from_session(request)
    
    # Load profiles
    profiles_file = "user_profiles.json"
    if not os.path.exists(profiles_file):
        raise HTTPException(status_code=404, detail="Profile not found")
    
    try:
        with open(profiles_file, "r") as f:
            profiles = json.load(f)
    except:
        raise HTTPException(status_code=500, detail="Error loading profiles")
    
    # Try to find profile by email or ID
    user_email = user.get("email")
    user_id = user.get("id")
    
    profile = profiles.get(user_email) or profiles.get(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "status": "success",
        "profile": profile
    }