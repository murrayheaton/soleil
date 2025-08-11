"""Profile API module.

Provides profile management endpoints.
"""
from fastapi import APIRouter

from .profile_routes import router as profile_router

# Create main profile router (no prefix - handled by API gateway)
router = APIRouter(tags=["Profile"])

# Include sub-routers
router.include_router(profile_router)

__all__ = ["router"]
