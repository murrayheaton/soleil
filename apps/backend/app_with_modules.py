#!/usr/bin/env python3
"""
Band Platform Backend with Modular Architecture

This is the main application entry point that integrates all modules
using the modular architecture pattern.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from modules.init_app import create_modular_app, add_module_status_endpoint
from modules.sync.services.sync_engine import start_sync_engine, stop_sync_engine
from modules.sync.services.websocket_manager import WebSocketManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# WebSocket manager instance
websocket_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info("Starting Band Platform with modular architecture...")
    
    # Start sync engine with WebSocket support
    await start_sync_engine(websocket_manager)
    logger.info("Sync engine started")
    
    # TODO: Initialize other background services
    
    yield
    
    # Shutdown
    logger.info("Shutting down Band Platform...")
    
    # Stop sync engine
    await stop_sync_engine()
    logger.info("Sync engine stopped")
    
    # TODO: Cleanup other resources


# Create application with modules
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # CORS configuration
    cors_origins = os.getenv(
        'CORS_ORIGINS',
        '["https://solepower.live", "https://www.solepower.live", "http://localhost:3000", "http://localhost:8000"]'
    )
    if isinstance(cors_origins, str):
        import json
        cors_origins = json.loads(cors_origins)
    
    # Create modular application
    app = create_modular_app(
        title="Band Platform API",
        description="A Progressive Web App for band management with modular architecture",
        version="2.0.0",
        cors_origins=cors_origins
    )
    
    # Add lifespan manager
    app.router.lifespan_context = lifespan
    
    # Session configuration
    SESSION_SECRET = os.getenv('SESSION_SECRET', 'your-secret-key-here')
    SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days
    
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        session_cookie="soleil_session",
        max_age=SESSION_MAX_AGE,
        same_site="lax",
        https_only=os.getenv('ENVIRONMENT', 'development') == 'production',
    )
    
    # Add module status endpoint
    add_module_status_endpoint(app)
    
    # Add WebSocket endpoint
    from modules.sync.api.websocket import router as websocket_router
    app.include_router(websocket_router, prefix="/ws", tags=["websocket"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Band Platform API with Modular Architecture",
            "version": "2.0.0",
            "modules": "/api/modules/status",
            "documentation": "/docs"
        }
    
    # Health check
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "modules": "active",
            "sync_engine": "running"
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    # Run with uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    
    uvicorn.run(
        "app_with_modules:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )