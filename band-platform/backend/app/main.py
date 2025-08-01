"""
FastAPI main application for the Band Platform.

This module sets up the FastAPI application with CORS, WebSocket support,
middleware, and all API routes following the PRP requirements.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings
from .database.connection import init_database, close_database
from .api import routes, auth, content, sync, websocket, folder_management, role_management, google_auth


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized successfully")
        
        # TODO: Initialize Google API services
        # TODO: Initialize sync engine
        # TODO: Set up webhook endpoints
        
        logger.info(f"{settings.app_name} startup complete")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")
    
    try:
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
        
        # TODO: Cleanup Google API services
        # TODO: Stop sync engine
        
        logger.info(f"{settings.app_name} shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A Progressive Web App for band management with Google Workspace integration",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# Security Middleware
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["solepower.live", "www.solepower.live"]
    )


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
)


# Compression Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Custom Middleware for Request/Response Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log HTTP requests and responses for monitoring and debugging.
    """
    # Log request
    if settings.debug:
        logger.debug(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time (placeholder)
    process_time = 0
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-API-Version"] = "1.0.0"
    
    # Log response
    if settings.debug:
        logger.debug(
            f"Response: {request.method} {request.url} - "
            f"Status: {response.status_code} - Time: {process_time}ms"
        )
    
    return response


# Custom Exception Handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors with custom response."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors with custom response."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred",
            "path": str(request.url.path)
        }
    )


# Health Check Endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Health status information.
    """
    from .database.connection import db_manager
    
    # Check database connectivity
    db_healthy = await db_manager.health_check()
    
    # TODO: Check Google API connectivity
    # TODO: Check sync engine status
    
    health_status = {
        "status": "healthy" if db_healthy else "unhealthy",
        "version": "1.0.0",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": "2024-07-23T17:00:00Z",  # Use actual timestamp
    }
    
    return health_status


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with component status.
    
    Returns:
        dict: Detailed health information.
    """
    from .database.connection import db_manager
    
    # Database health
    db_healthy = await db_manager.health_check()
    db_info = await db_manager.get_connection_info()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "components": {
            "database": {
                "status": "connected" if db_healthy else "disconnected",
                "connection_pool": db_info,
            },
            "google_apis": {
                "status": "not_implemented",  # TODO: Implement
                "drive": "unknown",
                "sheets": "unknown",
                "calendar": "unknown",
            },
            "sync_engine": {
                "status": "not_implemented",  # TODO: Implement
                "last_sync": None,
            }
        },
        "version": "1.0.0",
        "uptime_seconds": 0,  # TODO: Implement uptime tracking
    }


# API Routes
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    content.router,
    prefix="/api/content",
    tags=["Content"]
)

app.include_router(
    sync.router,
    prefix="/api/sync", 
    tags=["Sync"]
)

app.include_router(
    folder_management.router,
    prefix="/api/folders",
    tags=["Folder Management"]
)

app.include_router(
    role_management.router,
    prefix="/api/roles",
    tags=["Role Management"]
)

app.include_router(
    routes.router,
    prefix="/api",
    tags=["General"]
)

app.include_router(
    google_auth.router,
    prefix="/api/auth",
    tags=["Google OAuth"]
)

# WebSocket routes
app.include_router(
    websocket.router,
    prefix="/ws",
    tags=["WebSocket"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        dict: API information and links.
    """
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": "1.0.0",
        "documentation": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health",
        "endpoints": {
            "authentication": "/api/auth",
            "content": "/api/content", 
            "sync": "/api/sync",
            "folders": "/api/folders",
            "roles": "/api/roles",
            "websocket": "/ws"
        }
    }


# Development server configuration
if __name__ == "__main__":
    # This is only used for development
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.auto_reload,
        log_level=settings.log_level.lower(),
        access_log=settings.debug,
    )