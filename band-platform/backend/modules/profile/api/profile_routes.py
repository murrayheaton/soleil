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
        # Try to get existing profile
        profile = await profile_service.get_or_create_profile(
            user_id=user.get("id", user.get("email")),
            email=user.get("email", ""),
            name=user.get("name", "")
        )
        
        if profile.get("is_new"):
            # Return 404 for new users to trigger onboarding
            raise HTTPException(status_code=404, detail="Profile not found")
        
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
        # Create or update profile
        profile = await profile_service.get_or_create_profile(
            user_id=user.get("id", user.get("email")),
            email=profile_data.get("email"),
            name=profile_data.get("name")
        )
        
        # Update with additional fields
        if profile_data.get("instrument"):
            profile["instrument"] = profile_data.get("instrument")
            profile["transposition"] = profile_data.get("transposition", "")
            profile["display_name"] = profile_data.get("display_name", "")
        
        # Save updated profile
        updated_profile = await profile_service.update_profile(
            user_id=user.get("id", user.get("email")),
            updates=profile
        )
        
        if not updated_profile:
            raise HTTPException(status_code=500, detail="Failed to save profile")
        
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
            "profile": updated_profile,
            "message": "Profile saved successfully"
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
