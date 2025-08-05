"""
Base Module Configuration

This module provides base configuration classes and utilities for all SOLEil modules.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum
import os
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class BaseModuleConfig(BaseModel):
    """Base configuration for all modules"""
    
    # Module metadata
    module_name: str = Field(..., description="Name of the module")
    module_version: str = Field("1.0.0", description="Module version")
    enabled: bool = Field(True, description="Whether the module is enabled")
    
    # Environment
    environment: Environment = Field(
        default_factory=lambda: Environment(
            os.getenv("ENVIRONMENT", "development").lower()
        )
    )
    
    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Performance
    max_workers: int = Field(4, description="Maximum number of worker threads")
    timeout: int = Field(30, description="Default timeout in seconds")
    
    # Dependencies
    required_modules: List[str] = Field(
        default_factory=list,
        description="List of required module dependencies"
    )
    
    class Config:
        """Pydantic config"""
        use_enum_values = True
        extra = "allow"  # Allow extra fields for module-specific config
    
    @validator('module_version')
    def validate_version(cls, v):
        """Validate version format"""
        parts = v.split('.')
        if len(parts) != 3:
            raise ValueError("Version must be in format X.Y.Z")
        try:
            for part in parts:
                int(part)
        except ValueError:
            raise ValueError("Version parts must be integers")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return self.dict()
    
    @classmethod
    def from_file(cls, file_path: Path) -> "BaseModuleConfig":
        """Load config from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to load config from {file_path}: {e}")
            raise
    
    def save_to_file(self, file_path: Path) -> None:
        """Save config to JSON file"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config to {file_path}: {e}")
            raise
    
    def get_module_setting(self, key: str, default: Any = None) -> Any:
        """Get a module-specific setting"""
        return getattr(self, key, default)
    
    def update_setting(self, key: str, value: Any) -> None:
        """Update a setting value"""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            # For extra fields
            self.__dict__[key] = value
    
    def validate_dependencies(self, available_modules: List[str]) -> bool:
        """Check if all required modules are available"""
        missing = set(self.required_modules) - set(available_modules)
        if missing:
            logger.error(f"Missing required modules: {missing}")
            return False
        return True


class ModuleConfigManager:
    """Manages module configurations"""
    
    def __init__(self, base_config_dir: Optional[Path] = None):
        self.base_config_dir = base_config_dir or Path("configs/modules")
        self.configs: Dict[str, BaseModuleConfig] = {}
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        self.base_config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_module_config(
        self,
        module_name: str,
        config_class: type[BaseModuleConfig] = BaseModuleConfig
    ) -> BaseModuleConfig:
        """Load configuration for a module"""
        config_file = self.base_config_dir / f"{module_name}.json"
        
        if config_file.exists():
            try:
                config = config_class.from_file(config_file)
                logger.info(f"Loaded config for module: {module_name}")
            except Exception as e:
                logger.warning(f"Failed to load config file, using defaults: {e}")
                config = config_class(module_name=module_name)
        else:
            logger.info(f"No config file found for {module_name}, using defaults")
            config = config_class(module_name=module_name)
        
        self.configs[module_name] = config
        return config
    
    def save_module_config(self, module_name: str) -> None:
        """Save configuration for a module"""
        if module_name not in self.configs:
            raise ValueError(f"No config loaded for module: {module_name}")
        
        config_file = self.base_config_dir / f"{module_name}.json"
        self.configs[module_name].save_to_file(config_file)
        logger.info(f"Saved config for module: {module_name}")
    
    def get_config(self, module_name: str) -> Optional[BaseModuleConfig]:
        """Get configuration for a module"""
        return self.configs.get(module_name)
    
    def update_config(
        self,
        module_name: str,
        updates: Dict[str, Any]
    ) -> BaseModuleConfig:
        """Update configuration for a module"""
        if module_name not in self.configs:
            raise ValueError(f"No config loaded for module: {module_name}")
        
        config = self.configs[module_name]
        for key, value in updates.items():
            config.update_setting(key, value)
        
        return config
    
    def get_all_configs(self) -> Dict[str, BaseModuleConfig]:
        """Get all loaded configurations"""
        return self.configs.copy()
    
    def validate_all_dependencies(self) -> Dict[str, bool]:
        """Validate dependencies for all modules"""
        available_modules = list(self.configs.keys())
        results = {}
        
        for module_name, config in self.configs.items():
            results[module_name] = config.validate_dependencies(available_modules)
        
        return results


# Global config manager instance
_config_manager: Optional[ModuleConfigManager] = None


def get_config_manager() -> ModuleConfigManager:
    """Get the global config manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ModuleConfigManager()
    return _config_manager


def reset_config_manager() -> None:
    """Reset the global config manager (mainly for testing)"""
    global _config_manager
    _config_manager = None