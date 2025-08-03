"""
Module Loader Utility

Provides utilities for dynamically loading and initializing SOLEil modules.
"""
import importlib
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..api_gateway import get_api_gateway
from ..event_bus import get_event_bus

logger = logging.getLogger(__name__)


class ModuleLoader:
    """
    Handles dynamic loading and initialization of SOLEil modules.
    """
    
    def __init__(self, modules_path: Path):
        self.modules_path = modules_path
        self.loaded_modules: Dict[str, Any] = {}
        self.api_gateway = get_api_gateway()
        self.event_bus = get_event_bus()
        
    def discover_modules(self) -> List[str]:
        """
        Discover available modules in the modules directory.
        
        Returns:
            List of module names
        """
        modules = []
        
        for path in self.modules_path.iterdir():
            if path.is_dir() and not path.name.startswith('_'):
                # Check if it's a valid module (has __init__.py)
                init_file = path / '__init__.py'
                if init_file.exists():
                    modules.append(path.name)
                    
        logger.info(f"Discovered modules: {modules}")
        return modules
    
    def load_module(self, module_name: str) -> bool:
        """
        Load a single module.
        
        Args:
            module_name: Name of the module to load
            
        Returns:
            True if loaded successfully
        """
        if module_name in self.loaded_modules:
            logger.warning(f"Module {module_name} is already loaded")
            return True
            
        try:
            # Import the module
            module_path = f"modules.{module_name}"
            module = importlib.import_module(module_path)
            
            # Look for module initialization function
            if hasattr(module, 'initialize_module'):
                # Call module initialization
                module.initialize_module(self.api_gateway, self.event_bus)
                logger.info(f"Initialized module: {module_name}")
            else:
                logger.warning(
                    f"Module {module_name} has no initialize_module function"
                )
            
            self.loaded_modules[module_name] = module
            return True
            
        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}", exc_info=True)
            return False
    
    def load_all_modules(self, module_order: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        Load all discovered modules.
        
        Args:
            module_order: Optional list specifying load order
            
        Returns:
            Dict mapping module names to load success status
        """
        if module_order is None:
            # Default load order
            module_order = ['core', 'auth', 'drive', 'content', 'sync', 'dashboard']
            
        available_modules = self.discover_modules()
        results = {}
        
        # Load modules in specified order first
        for module_name in module_order:
            if module_name in available_modules and module_name != 'core':
                results[module_name] = self.load_module(module_name)
                
        # Load any remaining modules
        for module_name in available_modules:
            if module_name not in results and module_name != 'core':
                results[module_name] = self.load_module(module_name)
                
        return results
    
    def unload_module(self, module_name: str) -> bool:
        """
        Unload a module.
        
        Args:
            module_name: Name of the module to unload
            
        Returns:
            True if unloaded successfully
        """
        if module_name not in self.loaded_modules:
            logger.warning(f"Module {module_name} is not loaded")
            return False
            
        try:
            module = self.loaded_modules[module_name]
            
            # Call module cleanup if available
            if hasattr(module, 'cleanup_module'):
                module.cleanup_module()
                
            # Unregister from API gateway
            self.api_gateway.unregister_module(module_name)
            
            del self.loaded_modules[module_name]
            logger.info(f"Unloaded module: {module_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload module {module_name}: {e}", exc_info=True)
            return False
    
    def get_loaded_modules(self) -> List[str]:
        """Get list of currently loaded modules"""
        return list(self.loaded_modules.keys())
    
    def is_module_loaded(self, module_name: str) -> bool:
        """Check if a module is loaded"""
        return module_name in self.loaded_modules