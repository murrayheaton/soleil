"""
Profile management API routes.

This module provides profile CRUD operations and instrument management.
"""

from fastapi import APIRouter, HTTPException, Response, Request
import jwt
import os
from datetime import datetime
from typing import Dict, Any

router = APIRouter()

# JWT configuration (should match auth module)
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
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


@router.get("/profile")
async def get_user_profile(request: Request):
    """Get current user profile"""
    # Get user from session
    user = get_user_from_session(request)
    
    # Import profile service
    from app.services.profile_service import profile_service
    
    try:
        # Check if user is new first
        is_new = await profile_service.is_new_user(user.get("id", user.get("email")))
        
        if is_new:
            # Return 404 for new users to trigger onboarding
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get existing profile (don't create new one)
        profiles = await profile_service._load_profiles()
        user_id = user.get("id", user.get("email"))
        
        if user_id not in profiles:
            # User has no profile - return 404
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = profiles[user_id]
        
        return {
            "status": "success",
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading profile: {str(e)}")


@router.post("/profile")
async def save_user_profile(request: Request, response: Response):
    """Save user profile after OAuth or updates"""
    # Get user from session
    user = get_user_from_session(request)
    
    # Get profile data from request
    profile_data = await request.json()
    
    # Ensure we have required fields
    if not profile_data.get("email") or not profile_data.get("name"):
        raise HTTPException(status_code=400, detail="Email and name are required")
    
    # Import profile service
    from app.services.profile_service import profile_service
    
    try:
        user_id = user.get("id", user.get("email"))
        
        # Check if profile already exists
        profiles = await profile_service._load_profiles()
        
        if user_id in profiles:
            # Update existing profile
            profile = profiles[user_id]
            
            # Update with additional fields
            if profile_data.get("instrument"):
                profile["instrument"] = profile_data.get("instrument")
                profile["transposition"] = profile_data.get("transposition", "")
                profile["display_name"] = profile_data.get("display_name", "")
            
            # Save updated profile
            updated_profile = await profile_service.update_profile(
                user_id=user_id,
                updates=profile
            )
            
            return {
                "status": "success",
                "profile": updated_profile
            }
        else:
            # Create new profile (this is the welcome screen flow)
            new_profile = {
                "id": user_id,
                "email": profile_data.get("email"),
                "name": profile_data.get("name"),
                "instrument": profile_data.get("instrument", ""),
                "transposition": profile_data.get("transposition", ""),
                "display_name": profile_data.get("display_name", ""),
                "instruments": [profile_data.get("instrument")] if profile_data.get("instrument") else [],
                "ui_scale": "small",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "last_accessed": datetime.utcnow().isoformat(),
                "is_new": False
            }
            
            # Save new profile
            profiles[user_id] = new_profile
            await profile_service._save_profiles(profiles)
            
            return {
                "status": "success",
                "profile": new_profile
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving profile: {str(e)}")


@router.get("/profile/status")
async def get_profile_status(request: Request):
    """Check if user profile is complete"""
    try:
        # Get user from session
        user = get_user_from_session(request)
        
        # Import profile service
        from app.services.profile_service import profile_service
        
        profile = await profile_service.get_or_create_profile(
            user_id=user.get("id", user.get("email")),
            email=user.get("email", ""),
            name=user.get("name", "")
        )
        
        return {
            "status": "success",
            "profile_complete": not profile.get("is_new", True),
            "has_instrument": bool(profile.get("instrument")),
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking profile status: {str(e)}")
