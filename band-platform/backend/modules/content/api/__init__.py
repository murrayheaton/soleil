"""
Content API module.

Provides API routes for content management.
"""
from fastapi import APIRouter
from .content_routes import router as content_router

# Create main content router
router = APIRouter(prefix="/content", tags=["Content"])

# Include sub-routers
router.include_router(content_router)

__all__ = ["router"]