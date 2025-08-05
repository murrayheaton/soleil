"""
API Gateway for Module Registration

This module provides a gateway for registering and managing module routes
in the SOLEil application.
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from fastapi import FastAPI, APIRouter
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class ModuleInfo:
    """Information about a registered module"""
    name: str
    version: str
    description: str
    router: APIRouter
    dependencies: List[str]
    registered_at: datetime
    metadata: Dict[str, Any]
    health_check: Optional[Callable] = None
    services: Dict[str, Any] = None


class APIGateway:
    """
    Gateway for managing module registration and API routes.
    
    Features:
    - Dynamic module registration
    - Dependency validation
    - Route conflict detection
    - Module lifecycle management
    """
    
    def __init__(self, app: Optional[FastAPI] = None):
        self._app = app
        self._modules: Dict[str, ModuleInfo] = {}
        self._initialization_order: List[str] = []
        self._services: Dict[str, Dict[str, Any]] = {}
        
    def set_app(self, app: FastAPI) -> None:
        """Set the FastAPI application instance"""
        self._app = app
        # Re-register all modules with the new app
        for module_name in self._initialization_order:
            module = self._modules[module_name]
            self._register_routes(module)
    
    def register_module(
        self,
        name: str,
        router: APIRouter,
        version: str = "1.0.0",
        description: str = "",
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        health_check: Optional[Callable] = None,
        services: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a module with the gateway.
        
        Args:
            name: Module name
            router: FastAPI router with module endpoints
            version: Module version
            description: Module description
            dependencies: List of module names this module depends on
            metadata: Additional module metadata
        """
        if name in self._modules:
            raise ValueError(f"Module {name} is already registered")
        
        dependencies = dependencies or []
        metadata = metadata or {}
        
        # Validate dependencies
        for dep in dependencies:
            if dep not in self._modules:
                raise ValueError(
                    f"Module {name} depends on {dep}, which is not registered"
                )
        
        # Create module info
        module_info = ModuleInfo(
            name=name,
            version=version,
            description=description,
            router=router,
            dependencies=dependencies,
            registered_at=datetime.now(timezone.utc),
            metadata=metadata,
            health_check=health_check,
            services=services or {}
        )
        
        # Register services
        if services:
            self._services[name] = services
        
        # Register module
        self._modules[name] = module_info
        self._initialization_order.append(name)
        
        # Register routes if app is available
        if self._app:
            self._register_routes(module_info)
            
        logger.info(f"Registered module: {name} v{version}")
    
    def _register_routes(self, module: ModuleInfo) -> None:
        """Register module routes with the FastAPI app"""
        if not self._app:
            return
            
        # Add module prefix to avoid conflicts
        prefix = f"/api/modules/{module.name}"
        self._app.include_router(
            module.router,
            prefix=prefix,
            tags=[module.name]
        )
        logger.debug(f"Registered routes for module {module.name} at {prefix}")
    
    def unregister_module(self, name: str) -> None:
        """
        Unregister a module.
        
        Args:
            name: Module name to unregister
        """
        if name not in self._modules:
            raise ValueError(f"Module {name} is not registered")
        
        # Check if other modules depend on this one
        dependents = self.get_dependent_modules(name)
        if dependents:
            raise ValueError(
                f"Cannot unregister {name}, required by: {', '.join(dependents)}"
            )
        
        # Remove module
        del self._modules[name]
        self._initialization_order.remove(name)
        logger.info(f"Unregistered module: {name}")
    
    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """Get module information"""
        return self._modules.get(name)
    
    def list_modules(self) -> List[ModuleInfo]:
        """List all registered modules"""
        return list(self._modules.values())
    
    def get_dependent_modules(self, name: str) -> List[str]:
        """Get list of modules that depend on the given module"""
        dependents = []
        for module_name, module_info in self._modules.items():
            if name in module_info.dependencies:
                dependents.append(module_name)
        return dependents
    
    def get_initialization_order(self) -> List[str]:
        """Get module initialization order"""
        return self._initialization_order.copy()
    
    def validate_dependencies(self) -> bool:
        """
        Validate all module dependencies are satisfied.
        
        Returns:
            True if all dependencies are satisfied
        """
        for module_name, module_info in self._modules.items():
            for dep in module_info.dependencies:
                if dep not in self._modules:
                    logger.error(
                        f"Module {module_name} has unsatisfied dependency: {dep}"
                    )
                    return False
        return True
    
    def get_module_routes(self, name: str) -> List[str]:
        """Get list of routes registered by a module"""
        module = self.get_module(name)
        if not module:
            return []
            
        routes = []
        for route in module.router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        return routes
    
    def get_module_service(self, module_name: str, service_name: str) -> Any:
        """
        Get a service from another module.
        
        Args:
            module_name: Name of the module
            service_name: Name of the service
            
        Returns:
            The requested service instance
            
        Raises:
            ValueError: If module or service not found
        """
        if module_name not in self._services:
            raise ValueError(f"Module {module_name} not found or has no services")
        
        if service_name not in self._services[module_name]:
            raise ValueError(f"Service {service_name} not found in module {module_name}")
        
        return self._services[module_name][service_name]
    
    async def check_module_health(self, name: str) -> Dict[str, Any]:
        """
        Check health of a specific module.
        
        Args:
            name: Module name
            
        Returns:
            Health check result
        """
        module = self.get_module(name)
        if not module:
            return {"status": "error", "message": "Module not found"}
        
        if not module.health_check:
            return {"status": "ok", "message": "No health check defined"}
        
        try:
            # Support both sync and async health checks
            import asyncio
            if asyncio.iscoroutinefunction(module.health_check):
                result = await module.health_check()
            else:
                result = module.health_check()
            
            return {
                "status": "ok",
                "module": name,
                "version": module.version,
                "details": result
            }
        except Exception as e:
            logger.error(f"Health check failed for module {name}: {e}")
            return {
                "status": "error",
                "module": name,
                "message": str(e)
            }
    
    async def check_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all registered modules"""
        results = {}
        for name in self._modules:
            results[name] = await self.check_module_health(name)
        return results
    
    def validate_module_dependencies(self, name: str) -> Dict[str, bool]:
        """
        Validate a module's dependencies are available and healthy.
        
        Args:
            name: Module name
            
        Returns:
            Dict mapping dependency names to availability status
        """
        module = self.get_module(name)
        if not module:
            return {}
        
        results = {}
        for dep in module.dependencies:
            results[dep] = dep in self._modules
        
        return results


# Global API gateway instance
_api_gateway: Optional[APIGateway] = None


def get_api_gateway() -> APIGateway:
    """Get the global API gateway instance"""
    global _api_gateway
    if _api_gateway is None:
        _api_gateway = APIGateway()
    return _api_gateway


def reset_api_gateway() -> None:
    """Reset the global API gateway (mainly for testing)"""
    global _api_gateway
    _api_gateway = None