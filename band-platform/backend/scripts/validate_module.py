#!/usr/bin/env python3
"""
Validate Module Structure and Dependencies

This script validates that a module follows the SOLEil module structure
and conventions.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any
import json
import ast
import re

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))


class ModuleValidator:
    """Validates module structure and dependencies"""
    
    def __init__(self, module_name: str, modules_dir: Path):
        self.module_name = module_name
        self.module_path = modules_dir / module_name
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def validate(self) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate the module.
        
        Returns:
            Tuple of (is_valid, results_dict)
        """
        if not self.module_path.exists():
            self.errors.append(f"Module directory not found: {self.module_path}")
            return False, self._get_results()
        
        # Check required structure
        self._check_directory_structure()
        
        # Check MODULE.md
        self._check_module_documentation()
        
        # Check __init__.py files
        self._check_init_files()
        
        # Check configuration
        self._check_configuration()
        
        # Validate Python code
        self._validate_python_code()
        
        # Check dependencies
        self._check_dependencies()
        
        # Check naming conventions
        self._check_naming_conventions()
        
        # Check test coverage
        self._check_tests()
        
        # Run module-specific tests
        self._run_tests()
        
        return len(self.errors) == 0, self._get_results()
    
    def _get_results(self) -> Dict[str, List[str]]:
        """Get validation results"""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info
        }
    
    def _check_directory_structure(self):
        """Check required directory structure"""
        required_dirs = ["api", "services", "models", "tests"]
        
        for dir_name in required_dirs:
            dir_path = self.module_path / dir_name
            if not dir_path.exists():
                self.warnings.append(f"Missing directory: {dir_name}/")
            elif not dir_path.is_dir():
                self.errors.append(f"{dir_name} exists but is not a directory")
    
    def _check_module_documentation(self):
        """Check MODULE.md exists and has required sections"""
        module_md = self.module_path / "MODULE.md"
        
        if not module_md.exists():
            self.errors.append("Missing MODULE.md documentation")
            return
        
        content = module_md.read_text()
        required_sections = [
            "Purpose",
            "Dependencies",
            "API Endpoints",
            "Key Services",
            "Testing Strategy"
        ]
        
        for section in required_sections:
            if f"## {section}" not in content:
                self.warnings.append(f"MODULE.md missing section: {section}")
    
    def _check_init_files(self):
        """Check __init__.py files exist"""
        dirs_to_check = [self.module_path] + [
            self.module_path / d for d in ["api", "services", "models", "tests"]
            if (self.module_path / d).exists()
        ]
        
        for dir_path in dirs_to_check:
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                self.warnings.append(f"Missing __init__.py in {dir_path.relative_to(self.module_path)}")
    
    def _check_configuration(self):
        """Check module configuration"""
        config_file = self.module_path / "config.py"
        
        if not config_file.exists():
            self.warnings.append("Missing config.py file")
            return
        
        try:
            # Check if config class exists
            content = config_file.read_text()
            tree = ast.parse(content)
            
            has_config_class = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and "Config" in node.name:
                    has_config_class = True
                    break
            
            if not has_config_class:
                self.warnings.append("config.py missing configuration class")
        
        except Exception as e:
            self.errors.append(f"Error parsing config.py: {e}")
    
    def _validate_python_code(self):
        """Validate Python syntax in all files"""
        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text()
                ast.parse(content)
            except SyntaxError as e:
                self.errors.append(f"Syntax error in {py_file.relative_to(self.module_path)}: {e}")
    
    def _check_dependencies(self):
        """Check module dependencies"""
        # Check imports
        internal_imports = set()
        external_imports = set()
        
        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            
            # Find imports
            import_pattern = r'(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))'
            for match in re.finditer(import_pattern, content):
                module = match.group(1) or match.group(2)
                if module:
                    if module.startswith("modules."):
                        internal_imports.add(module.split('.')[1])
                    elif not module.startswith('.'):
                        external_imports.add(module.split('.')[0])
        
        # Check if internal dependencies exist
        for dep in internal_imports:
            if dep != self.module_name:  # Don't check self
                dep_path = self.module_path.parent / dep
                if not dep_path.exists():
                    self.warnings.append(f"Dependency module not found: {dep}")
        
        self.info.append(f"Internal dependencies: {', '.join(sorted(internal_imports))}")
        self.info.append(f"External dependencies: {', '.join(sorted(external_imports))}")
    
    def _check_naming_conventions(self):
        """Check naming conventions"""
        # Check file names
        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            file_name = py_file.stem
            if file_name != "__init__" and not re.match(r'^[a-z_]+$', file_name):
                self.warnings.append(
                    f"File name not in snake_case: {py_file.relative_to(self.module_path)}"
                )
            
            # Check class names in services
            if "services" in str(py_file) and file_name != "__init__":
                content = py_file.read_text()
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if not node.name.endswith("Service"):
                                self.warnings.append(
                                    f"Service class should end with 'Service': {node.name} in {py_file.name}"
                                )
                except:
                    pass
    
    def _check_tests(self):
        """Check test coverage"""
        tests_dir = self.module_path / "tests"
        
        if not tests_dir.exists():
            self.errors.append("No tests directory found")
            return
        
        test_files = list(tests_dir.glob("test_*.py"))
        if not test_files:
            self.errors.append("No test files found")
            return
        
        # Check if main services have tests
        services_dir = self.module_path / "services"
        if services_dir.exists():
            for service_file in services_dir.glob("*.py"):
                if service_file.stem != "__init__":
                    test_file = tests_dir / f"test_{service_file.stem}.py"
                    if not test_file.exists():
                        self.warnings.append(f"No test file for service: {service_file.stem}")
        
        self.info.append(f"Found {len(test_files)} test files")
    
    def _run_tests(self):
        """Run module-specific tests"""
        tests_dir = self.module_path / "tests"
        
        if not tests_dir.exists():
            return
        
        try:
            # Run pytest for this module
            result = subprocess.run(
                ["python", "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=self.module_path.parent.parent  # Backend directory
            )
            
            if result.returncode != 0:
                self.errors.append("Module tests failed")
                # Extract failure summary
                lines = result.stdout.split('\n')
                for line in lines:
                    if "FAILED" in line:
                        self.errors.append(f"Test failure: {line.strip()}")
            else:
                # Count passed tests
                passed_match = re.search(r'(\d+) passed', result.stdout)
                if passed_match:
                    self.info.append(f"All {passed_match.group(1)} tests passed")
        
        except Exception as e:
            self.warnings.append(f"Could not run tests: {e}")


def format_results(results: Dict[str, List[str]], module_name: str) -> str:
    """Format validation results"""
    output = f"\n{'='*60}\n"
    output += f"Module Validation Report: {module_name}\n"
    output += f"{'='*60}\n\n"
    
    if results["errors"]:
        output += "❌ ERRORS (must fix):\n"
        for error in results["errors"]:
            output += f"   - {error}\n"
        output += "\n"
    
    if results["warnings"]:
        output += "⚠️  WARNINGS (should fix):\n"
        for warning in results["warnings"]:
            output += f"   - {warning}\n"
        output += "\n"
    
    if results["info"]:
        output += "ℹ️  INFORMATION:\n"
        for info in results["info"]:
            output += f"   - {info}\n"
        output += "\n"
    
    if not results["errors"]:
        output += "✅ Module structure is valid!\n"
    else:
        output += "❌ Module validation failed!\n"
    
    output += f"{'='*60}\n"
    
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Validate a SOLEil module structure"
    )
    parser.add_argument(
        "module",
        help="Name of the module to validate"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    
    args = parser.parse_args()
    
    # Find modules directory
    modules_dir = Path(__file__).parent.parent / "modules"
    
    # Validate module
    validator = ModuleValidator(args.module, modules_dir)
    is_valid, results = validator.validate()
    
    # In strict mode, warnings are errors
    if args.strict and results["warnings"]:
        is_valid = False
    
    # Output results
    if args.json:
        output = {
            "module": args.module,
            "valid": is_valid,
            "results": results
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_results(results, args.module))
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()