"""
Module Management API Routes

Provides endpoints for module health checks, status, and management.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from pydantic import BaseModel

from .api_gateway import get_api_gateway
from .module_config import get_config_manager
from .event_bus import get_event_bus

router = APIRouter(prefix="/api/modules", tags=["modules"])


class ModuleStatus(BaseModel):
    """Module status response"""
    name: str
    version: str
    status: str
    health: Dict[str, Any]
    dependencies: List[str]
    config: Dict[str, Any]


class ModulesOverview(BaseModel):
    """Overview of all modules"""
    total_modules: int
    healthy_modules: int
    modules: List[ModuleStatus]
    event_stats: Dict[str, int]


@router.get("/", response_model=ModulesOverview)
async def get_modules_overview():
    """Get overview of all registered modules"""
    gateway = get_api_gateway()
    config_manager = get_config_manager()
    event_bus = get_event_bus()
    
    # Get all modules
    modules = gateway.list_modules()
    
    # Check health for all modules
    health_results = await gateway.check_all_health()
    
    # Build module status list
    module_statuses = []
    healthy_count = 0
    
    for module in modules:
        health = health_results.get(module.name, {"status": "unknown"})
        is_healthy = health.get("status") == "ok"
        if is_healthy:
            healthy_count += 1
        
        # Get module config
        config = config_manager.get_config(module.name)
        config_dict = config.to_dict() if config else {}
        
        module_statuses.append(ModuleStatus(
            name=module.name,
            version=module.version,
            status="healthy" if is_healthy else "unhealthy",
            health=health,
            dependencies=module.dependencies,
            config={
                "enabled": config_dict.get("enabled", True),
                "environment": config_dict.get("environment", "unknown")
            }
        ))
    
    # Get event statistics
    event_stats = event_bus.get_subscribers_count()
    
    return ModulesOverview(
        total_modules=len(modules),
        healthy_modules=healthy_count,
        modules=module_statuses,
        event_stats=event_stats
    )


@router.get("/{module_name}", response_model=ModuleStatus)
async def get_module_status(module_name: str):
    """Get detailed status for a specific module"""
    gateway = get_api_gateway()
    config_manager = get_config_manager()
    
    # Get module info
    module = gateway.get_module(module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    # Check module health
    health = await gateway.check_module_health(module_name)
    
    # Get module config
    config = config_manager.get_config(module_name)
    config_dict = config.to_dict() if config else {}
    
    return ModuleStatus(
        name=module.name,
        version=module.version,
        status="healthy" if health.get("status") == "ok" else "unhealthy",
        health=health,
        dependencies=module.dependencies,
        config={
            "enabled": config_dict.get("enabled", True),
            "environment": config_dict.get("environment", "unknown"),
            "log_level": config_dict.get("log_level", "INFO"),
            "timeout": config_dict.get("timeout", 30)
        }
    )


@router.get("/{module_name}/health")
async def check_module_health(module_name: str):
    """Check health of a specific module"""
    gateway = get_api_gateway()
    
    # Check if module exists
    module = gateway.get_module(module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    # Perform health check
    health = await gateway.check_module_health(module_name)
    
    # Return appropriate status code
    if health.get("status") == "error":
        raise HTTPException(status_code=503, detail=health)
    
    return health


@router.get("/{module_name}/routes")
async def get_module_routes(module_name: str):
    """Get all routes registered by a module"""
    gateway = get_api_gateway()
    
    # Check if module exists
    module = gateway.get_module(module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    # Get routes
    routes = gateway.get_module_routes(module_name)
    
    return {
        "module": module_name,
        "routes": routes,
        "total": len(routes)
    }


@router.get("/{module_name}/dependencies")
async def check_module_dependencies(module_name: str):
    """Check if module dependencies are satisfied"""
    gateway = get_api_gateway()
    
    # Check if module exists
    module = gateway.get_module(module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    # Validate dependencies
    dependency_status = gateway.validate_module_dependencies(module_name)
    
    return {
        "module": module_name,
        "dependencies": module.dependencies,
        "status": dependency_status,
        "all_satisfied": all(dependency_status.values()) if dependency_status else True
    }


@router.post("/{module_name}/reload")
async def reload_module_config(module_name: str):
    """Reload configuration for a module"""
    config_manager = get_config_manager()
    
    try:
        # Reload config from file
        config = config_manager.load_module_config(module_name)
        
        return {
            "module": module_name,
            "status": "reloaded",
            "config": {
                "version": config.module_version,
                "enabled": config.enabled,
                "environment": config.environment
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload config: {str(e)}")


@router.get("/events/history")
async def get_event_history(event_name: str = None, limit: int = 100):
    """Get event history"""
    event_bus = get_event_bus()
    
    # Get history
    history = event_bus.get_history(event_name)
    
    # Limit results
    if len(history) > limit:
        history = history[-limit:]
    
    # Format for response
    formatted_history = []
    for event in history:
        formatted_history.append({
            "name": event.name,
            "module": event.module,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data
        })
    
    return {
        "total": len(formatted_history),
        "events": formatted_history
    }


@router.get("/events/subscribers")
async def get_event_subscribers():
    """Get current event subscribers"""
    event_bus = get_event_bus()
    
    subscribers = event_bus.get_subscribers_count()
    
    return {
        "total_event_types": len(subscribers),
        "subscribers": subscribers
    }