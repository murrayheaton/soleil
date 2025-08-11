"""
Authentication API routes.

This module provides authentication endpoints including JWT token management
and Google OAuth integration following the PRP requirements.
"""

from fastapi import APIRouter, HTTPException, Response, Request
from datetime import datetime

router = APIRouter()


@router.post("/login", tags=["Authentication"])
async def login(response: Response):
    """User login endpoint."""
    # TODO: Implement JWT authentication
    # For now, set authentication cookie with secure attributes
    response.set_cookie(
        key="soleil_auth",
        value="true",
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return {"detail": "Authentication not implemented yet"}


@router.post("/register", tags=["Authentication"])
async def register():
    """User registration endpoint."""
    # TODO: Implement user registration
    raise HTTPException(status_code=501, detail="Registration not implemented yet")


@router.post("/google/auth", tags=["Authentication"])
async def google_oauth():
    """Google OAuth authentication endpoint."""
    # TODO: Implement Google OAuth flow
    raise HTTPException(status_code=501, detail="Google OAuth not implemented yet")


@router.post("/refresh", tags=["Authentication"])  
async def refresh_token():
    """Refresh JWT token endpoint."""
    # TODO: Implement token refresh
    raise HTTPException(status_code=501, detail="Token refresh not implemented yet")


@router.post("/logout", tags=["Authentication"])
async def logout(response: Response):
    """User logout endpoint."""
    try:
        # Clear all authentication cookies
        response.delete_cookie(
            key="soleil_session",
            path="/",
            httponly=True,
            samesite="lax",
            secure=True
        )
        
        response.delete_cookie(
            key="soleil_refresh",
            path="/",
            httponly=True,
            samesite="lax",
            secure=True
        )
        
        response.delete_cookie(
            key="soleil_auth",
            path="/",
            httponly=False,
            samesite="lax",
            secure=True
        )
        
        response.delete_cookie(
            key="soleil_profile_complete",
            path="/",
            httponly=False,
            samesite="lax",
            secure=True
        )
        
        return {
            "status": "success",
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        # Even if there's an error, try to clear cookies
        response.delete_cookie("soleil_session", path="/")
        response.delete_cookie("soleil_refresh", path="/")
        response.delete_cookie("soleil_auth", path="/")
        response.delete_cookie("soleil_profile_complete", path="/")
        
        return {
            "status": "success",
            "message": "Logged out successfully"
        }


@router.get("/validate", tags=["Authentication"])
async def validate_auth(request: Request):
    """Validate user authentication status."""
    try:
        # Check for session token
        session_token = request.cookies.get("soleil_session")
        if not session_token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Import JWT handling
        import jwt
        import os
        
        JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        JWT_ALGORITHM = "HS256"
        
        try:
            # Decode and validate token
            payload = jwt.decode(session_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_info = payload.get("user", {})
            
            # Check if token is expired
            exp_timestamp = payload.get("exp")
            if exp_timestamp and datetime.now().timestamp() > exp_timestamp:
                raise HTTPException(status_code=401, detail="Token expired")
            
            return {
                "status": "success",
                "authenticated": True,
                "user": user_info
            }
            
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.get("/session", tags=["Authentication"])
async def get_session(request: Request):
    """Get current user session information."""
    try:
        # Check for session token
        session_token = request.cookies.get("soleil_session")
        if not session_token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Import JWT handling
        import jwt
        import os
        
        JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        JWT_ALGORITHM = "HS256"
        
        try:
            # Decode and validate token
            payload = jwt.decode(session_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_info = payload.get("user", {})
            
            # Check if token is expired
            exp_timestamp = payload.get("exp")
            if exp_timestamp and datetime.now().timestamp() > exp_timestamp:
                raise HTTPException(status_code=401, detail="Token expired")
            
            return {
                "status": "success",
                "authenticated": True,
                "name": user_info.get("name", ""),
                "email": user_info.get("email", ""),
                "picture": user_info.get("picture", ""),
                "id": user_info.get("id", "")
            }
            
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session error: {str(e)}")


@router.post("/profile/complete", tags=["Authentication"])
async def profile_complete(response: Response):
    """Mark user profile as complete and set tracking cookie."""
    response.set_cookie(
        key="soleil_profile_complete",
        value="true",
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return {"status": "profile marked complete"}

