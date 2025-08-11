"""
Application initialization with modular architecture.

This module provides functions to initialize the FastAPI application
with all registered modules.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .register_modules import register_all_modules

logger = logging.getLogger(__name__)


def init_modules(app: FastAPI) -> None:
    """
    Initialize all modules with the FastAPI application.
    
    This function registers all modules and their routes with the application.
    
    Args:
        app: FastAPI application instance
    """
    logger.info("Initializing modules...")
    
    try:
        # Register all modules through the API gateway
        register_all_modules(app)
        
        # Remove duplicate route registrations - now handled by API gateway
        # from .drive.api import drive_routes
        # from .sync.api import sync_routes
        
        # Include module routes directly (in addition to gateway routes)
        # This allows both /api/modules/drive/* and /api/drive/* patterns
        # app.include_router(drive_routes.router, prefix="/api", tags=["drive"])
        # app.include_router(sync_routes.router, prefix="/api", tags=["sync"])
        
        logger.info("Module initialization complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize modules: {e}")
        raise


def create_modular_app(
    title: str = "Band Platform API",
    description: str = "A Progressive Web App for band management",
    version: str = "1.0.0",
    cors_origins: list = None
) -> FastAPI:
    """
    Create a FastAPI application with modular architecture.
    
    Args:
        title: Application title
        description: Application description
        version: Application version
        cors_origins: List of allowed CORS origins
        
    Returns:
        Configured FastAPI application
    """
    # Create base application
    app = FastAPI(
        title=title,
        description=description,
        version=version
    )
    
    # Configure CORS
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Initialize modules
    init_modules(app)
    
    return app


# Module status endpoint for debugging
def add_module_status_endpoint(app: FastAPI) -> None:
    """
    Add a module status endpoint for debugging and monitoring.
    
    Args:
        app: FastAPI application instance
    """
    from .register_modules import get_module_status
    
    @app.get("/api/modules/status", tags=["modules"])
    async def module_status():
        """Get status of all registered modules."""
        return get_module_status()