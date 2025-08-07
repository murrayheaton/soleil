"""
Integration tests for module boundary enforcement
"""

import pytest
from pathlib import Path
import ast
import re
from typing import Set, List, Dict


class TestModuleBoundaries:
    """Test that modules respect boundaries and don't have direct dependencies"""
    
    @pytest.fixture
    def modules_path(self):
        """Get modules directory path"""
        return Path(__file__).parent.parent.parent / "modules"
    
    def get_module_imports(self, module_path: Path) -> Set[str]:
        """Extract all imports from a module"""
        imports = set()
        
        for py_file in module_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "tests" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module)
            except:
                pass
        
        return imports
    
    def test_no_cross_module_imports(self, modules_path):
        """Test that modules don't import from each other directly"""
        modules = ['auth', 'content', 'drive', 'sync', 'dashboard']
        
        for module_name in modules:
            module_path = modules_path / module_name
            if not module_path.exists():
                continue
            
            imports = self.get_module_imports(module_path)
            
            # Check for direct imports from other modules
            for other_module in modules:
                if other_module == module_name:
                    continue
                
                # Direct imports like "from modules.auth.services import X" are not allowed
                forbidden_patterns = [
                    f"modules.{other_module}.services",
                    f"modules.{other_module}.models",
                    f"modules.{other_module}.api"
                ]
                
                for pattern in forbidden_patterns:
                    assert pattern not in imports, \
                        f"Module {module_name} has forbidden import: {pattern}"
    
    def test_core_module_imports_allowed(self, modules_path):
        """Test that all modules can import from core"""
        modules = ['auth', 'content', 'drive', 'sync', 'dashboard']
        
        for module_name in modules:
            module_path = modules_path / module_name
            if not module_path.exists():
                continue
            
            imports = self.get_module_imports(module_path)
            
            # Core imports should be allowed
            core_imports = [imp for imp in imports if imp.startswith("modules.core")]
            
            # Verify at least some core usage (event bus, etc)
            has_eventbus = any("event_bus" in imp for imp in core_imports)
            has_events = any("events" in imp for imp in core_imports)
            
            assert has_eventbus or has_events or module_name == 'dashboard', \
                f"Module {module_name} should use core infrastructure"
    
    def test_module_public_interfaces(self, modules_path):
        """Test that modules expose public interfaces in __init__.py"""
        modules = ['auth', 'content', 'drive', 'sync', 'dashboard']
        
        for module_name in modules:
            module_path = modules_path / module_name
            init_file = module_path / "__init__.py"
            
            if not init_file.exists():
                continue
            
            content = init_file.read_text()
            
            # Should have __all__ defined
            assert "__all__" in content or "# No public API" in content, \
                f"Module {module_name} should define __all__ in __init__.py"
    
    def test_event_based_communication(self, modules_path):
        """Test that modules use events for communication"""
        modules = ['auth', 'content', 'drive', 'sync']
        event_usage = {}
        
        for module_name in modules:
            module_path = modules_path / module_name
            if not module_path.exists():
                continue
            
            publishes = []
            subscribes = []
            
            for py_file in module_path.rglob("*.py"):
                if "__pycache__" in str(py_file) or "tests" in str(py_file):
                    continue
                
                try:
                    content = py_file.read_text()
                    
                    # Find event publications
                    pub_pattern = r'event_bus\.publish\s*\(\s*event_type\s*=\s*events\.(\w+)'
                    for match in re.finditer(pub_pattern, content):
                        publishes.append(match.group(1))
                    
                    # Find event subscriptions
                    sub_pattern = r'event_bus\.subscribe\s*\(\s*events\.(\w+)'
                    for match in re.finditer(sub_pattern, content):
                        subscribes.append(match.group(1))
                except:
                    pass
            
            event_usage[module_name] = {
                'publishes': publishes,
                'subscribes': subscribes
            }
        
        # Verify modules use events
        for module_name, usage in event_usage.items():
            if module_name in ['auth', 'content', 'drive', 'sync']:
                assert usage['publishes'] or usage['subscribes'], \
                    f"Module {module_name} should use event-based communication"
    
    def test_configuration_isolation(self, modules_path):
        """Test that each module has its own configuration"""
        modules = ['auth', 'content', 'drive', 'sync', 'dashboard']
        
        for module_name in modules:
            config_file = modules_path / module_name / "config.py"
            
            assert config_file.exists(), \
                f"Module {module_name} should have config.py"
            
            content = config_file.read_text()
            
            # Should have module-specific config class
            assert f"{module_name.capitalize()}ModuleConfig" in content, \
                f"Module {module_name} should have its own config class"
            
            # Should inherit from BaseModuleConfig
            assert "BaseModuleConfig" in content, \
                f"Module {module_name} config should inherit from BaseModuleConfig"
    
    def test_module_tests_isolation(self, modules_path):
        """Test that each module has isolated tests"""
        modules = ['auth', 'content', 'drive', 'sync', 'dashboard']
        
        for module_name in modules:
            tests_dir = modules_path / module_name / "tests"
            
            if not tests_dir.exists():
                continue
            
            # Check that tests only import from their own module
            for test_file in tests_dir.glob("test_*.py"):
                content = test_file.read_text()
                
                # Check for imports from other modules
                for other_module in modules:
                    if other_module == module_name:
                        continue
                    
                    assert f"modules.{other_module}" not in content, \
                        f"Test {test_file.name} in {module_name} imports from {other_module}"