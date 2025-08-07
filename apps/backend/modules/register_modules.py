"""
Module Registration for SOLEil Band Platform

This file handles the registration of all modular components with the API gateway.
It ensures proper initialization order based on module dependencies.
"""

import logging
from typing import Optional

from fastapi import FastAPI

from .core.api_gateway import get_api_gateway
from .auth import router as auth_router, MODULE_NAME as AUTH_MODULE, MODULE_VERSION as AUTH_VERSION
from .content import router as content_router, MODULE_NAME as CONTENT_MODULE, MODULE_VERSION as CONTENT_VERSION
from .drive import router as drive_router, MODULE_NAME as DRIVE_MODULE, MODULE_VERSION as DRIVE_VERSION
from .sync import router as sync_router, MODULE_NAME as SYNC_MODULE, MODULE_VERSION as SYNC_VERSION
from .dashboard import router as dashboard_router, MODULE_NAME as DASHBOARD_MODULE, MODULE_VERSION as DASHBOARD_VERSION

logger = logging.getLogger(__name__)


def register_all_modules(app: Optional[FastAPI] = None) -> None:
    """
    Register all modules with the API gateway.
    
    This function ensures modules are registered in the correct order
    based on their dependencies.
    
    Args:
        app: Optional FastAPI application instance
    """
    gateway = get_api_gateway()
    
    if app:
        gateway.set_app(app)
    
    try:
        # Core modules (no dependencies)
        logger.info("Registering core modules...")
        
        # Auth module - foundation for all other modules
        gateway.register_module(
            name=AUTH_MODULE,
            router=auth_router,
            version=AUTH_VERSION,
            description="Authentication and user management",
            dependencies=[],
            metadata={"core": True}
        )
        
        # Content module - manages charts and audio
        gateway.register_module(
            name=CONTENT_MODULE,
            router=content_router,
            version=CONTENT_VERSION,
            description="Content management for charts and audio files",
            dependencies=[AUTH_MODULE],
            metadata={"core": True}
        )
        
        # Drive module - Google Drive integration
        gateway.register_module(
            name=DRIVE_MODULE,
            router=drive_router,
            version=DRIVE_VERSION,
            description="Google Drive integration and file management",
            dependencies=[AUTH_MODULE, CONTENT_MODULE],
            metadata={"external_api": "google_drive"}
        )
        
        # Sync module - synchronization engine
        gateway.register_module(
            name=SYNC_MODULE,
            router=sync_router,
            version=SYNC_VERSION,
            description="Real-time synchronization engine",
            dependencies=[AUTH_MODULE, CONTENT_MODULE, DRIVE_MODULE],
            metadata={"realtime": True, "websocket": True}
        )
        
        # Dashboard module - aggregates data from other modules
        gateway.register_module(
            name=DASHBOARD_MODULE,
            router=dashboard_router,
            version=DASHBOARD_VERSION,
            description="Dashboard and analytics",
            dependencies=[AUTH_MODULE, CONTENT_MODULE, SYNC_MODULE],
            metadata={"frontend_facing": True}
        )
        
        # Validate all dependencies are satisfied
        if gateway.validate_dependencies():
            logger.info("All modules registered successfully")
            
            # Log initialization order
            init_order = gateway.get_initialization_order()
            logger.info(f"Module initialization order: {' -> '.join(init_order)}")
            
            # Log module summary
            modules = gateway.list_modules()
            logger.info(f"Total modules registered: {len(modules)}")
            for module in modules:
                route_count = len(gateway.get_module_routes(module.name))
                logger.info(
                    f"  - {module.name} v{module.version}: "
                    f"{route_count} routes, "
                    f"deps: {module.dependencies or 'none'}"
                )
        else:
            logger.error("Module dependency validation failed!")
            raise RuntimeError("Failed to validate module dependencies")
            
    except Exception as e:
        logger.error(f"Failed to register modules: {e}")
        raise


def get_module_status() -> dict:
    """
    Get status information for all registered modules.
    
    Returns:
        Dictionary with module status information
    """
    gateway = get_api_gateway()
    modules = gateway.list_modules()
    
    status = {
        "total_modules": len(modules),
        "initialization_order": gateway.get_initialization_order(),
        "modules": {}
    }
    
    for module in modules:
        status["modules"][module.name] = {
            "version": module.version,
            "description": module.description,
            "dependencies": module.dependencies,
            "routes": gateway.get_module_routes(module.name),
            "registered_at": module.registered_at.isoformat(),
            "metadata": module.metadata
        }
    
    return status


# For backward compatibility
__all__ = ["register_all_modules", "get_module_status"]