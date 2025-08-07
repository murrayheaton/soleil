"""
Authentication API module.

Provides authentication and authorization endpoints.
"""
from fastapi import APIRouter

from .auth_routes import router as auth_router
from .google_auth_routes import router as google_auth_router

# Create main auth router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Include sub-routers
router.include_router(auth_router)
router.include_router(google_auth_router)

__all__ = ["router"]