#!/usr/bin/env python3
"""
Generate Module Context for AI Agents

This script generates comprehensive context for a specific module,
making it easy for AI agents to understand and work with the module.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import ast
import re

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))


class ModuleContextGenerator:
    """Generates context documentation for modules"""
    
    def __init__(self, module_name: str, modules_dir: Path):
        self.module_name = module_name
        self.module_path = modules_dir / module_name
        self.context = {
            "module_name": module_name,
            "files": {},
            "dependencies": [],
            "api_endpoints": [],
            "services": [],
            "models": [],
            "tests": [],
            "configuration": {},
            "public_interfaces": [],
            "event_subscriptions": [],
            "event_publications": []
        }
    
    def generate(self) -> Dict[str, Any]:
        """Generate complete module context"""
        if not self.module_path.exists():
            raise ValueError(f"Module {self.module_name} not found at {self.module_path}")
        
        # Read MODULE.md
        self._read_module_documentation()
        
        # Analyze Python files
        self._analyze_python_files()
        
        # Extract API endpoints
        self._extract_api_endpoints()
        
        # Extract services
        self._extract_services()
        
        # Extract models
        self._extract_models()
        
        # Find tests
        self._find_tests()
        
        # Extract configuration
        self._extract_configuration()
        
        # Extract event interactions
        self._extract_event_interactions()
        
        return self.context
    
    def _read_module_documentation(self):
        """Read and parse MODULE.md"""
        module_md = self.module_path / "MODULE.md"
        if module_md.exists():
            self.context["documentation"] = module_md.read_text()
    
    def _analyze_python_files(self):
        """Analyze all Python files in the module"""
        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            relative_path = py_file.relative_to(self.module_path)
            content = py_file.read_text()
            
            # Extract imports to find dependencies
            imports = self._extract_imports(content)
            self.context["dependencies"].extend(imports)
            
            # Store file info
            self.context["files"][str(relative_path)] = {
                "path": str(relative_path),
                "size": len(content),
                "lines": content.count('\n'),
                "classes": self._extract_classes(content),
                "functions": self._extract_functions(content)
            }
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        imports = []
        import_pattern = r'(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))'
        
        for match in re.finditer(import_pattern, content):
            module = match.group(1) or match.group(2)
            if module and not module.startswith('.'):
                imports.append(module)
        
        return list(set(imports))
    
    def _extract_classes(self, content: str) -> List[Dict[str, str]]:
        """Extract class definitions"""
        classes = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node) or "No documentation"
                    classes.append({
                        "name": node.name,
                        "docstring": docstring.split('\n')[0]  # First line only
                    })
        except:
            pass
        return classes
    
    def _extract_functions(self, content: str) -> List[Dict[str, str]]:
        """Extract function definitions"""
        functions = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Public functions only
                        docstring = ast.get_docstring(node) or "No documentation"
                        functions.append({
                            "name": node.name,
                            "docstring": docstring.split('\n')[0]
                        })
        except:
            pass
        return functions
    
    def _extract_api_endpoints(self):
        """Extract API endpoints from the module"""
        api_dir = self.module_path / "api"
        if not api_dir.exists():
            return
        
        for py_file in api_dir.glob("*.py"):
            content = py_file.read_text()
            
            # Find route decorators
            route_pattern = r'@.*\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
            for match in re.finditer(route_pattern, content):
                method = match.group(1).upper()
                path = match.group(2)
                self.context["api_endpoints"].append({
                    "method": method,
                    "path": path,
                    "file": py_file.name
                })
    
    def _extract_services(self):
        """Extract service classes"""
        services_dir = self.module_path / "services"
        if not services_dir.exists():
            return
        
        for py_file in services_dir.glob("*.py"):
            content = py_file.read_text()
            file_info = self.context["files"].get(f"services/{py_file.name}", {})
            
            for class_info in file_info.get("classes", []):
                if class_info["name"].endswith("Service"):
                    self.context["services"].append({
                        "name": class_info["name"],
                        "file": py_file.name,
                        "description": class_info["docstring"]
                    })
    
    def _extract_models(self):
        """Extract model classes"""
        models_dir = self.module_path / "models"
        if not models_dir.exists():
            return
        
        for py_file in models_dir.glob("*.py"):
            file_info = self.context["files"].get(f"models/{py_file.name}", {})
            
            for class_info in file_info.get("classes", []):
                self.context["models"].append({
                    "name": class_info["name"],
                    "file": py_file.name,
                    "description": class_info["docstring"]
                })
    
    def _find_tests(self):
        """Find test files"""
        tests_dir = self.module_path / "tests"
        if not tests_dir.exists():
            return
        
        for test_file in tests_dir.glob("test_*.py"):
            self.context["tests"].append({
                "file": test_file.name,
                "path": f"tests/{test_file.name}"
            })
    
    def _extract_configuration(self):
        """Extract module configuration"""
        config_file = self.module_path / "config.py"
        if config_file.exists():
            content = config_file.read_text()
            
            # Extract config class fields
            config_fields = []
            field_pattern = r'(\w+):\s*[\w\[\]]+\s*=\s*Field\([^)]+\)'
            for match in re.finditer(field_pattern, content):
                config_fields.append(match.group(1))
            
            self.context["configuration"] = {
                "file": "config.py",
                "fields": config_fields
            }
    
    def _extract_event_interactions(self):
        """Extract event subscriptions and publications"""
        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            
            content = py_file.read_text()
            
            # Find event subscriptions
            sub_pattern = r'event_bus\.subscribe\s*\(\s*["\']([^"\']+)["\']'
            for match in re.finditer(sub_pattern, content):
                self.context["event_subscriptions"].append({
                    "event": match.group(1),
                    "file": str(py_file.relative_to(self.module_path))
                })
            
            # Find event publications
            pub_pattern = r'event_bus\.publish\s*\(\s*event_type\s*=\s*["\']([^"\']+)["\']'
            for match in re.finditer(pub_pattern, content):
                self.context["event_publications"].append({
                    "event": match.group(1),
                    "file": str(py_file.relative_to(self.module_path))
                })
    
    def format_as_markdown(self) -> str:
        """Format context as markdown for AI agents"""
        md = f"# Module Context: {self.module_name}\n\n"
        
        # Documentation
        if "documentation" in self.context:
            md += "## Module Documentation\n\n"
            md += self.context["documentation"] + "\n\n"
        
        # Files Overview
        md += "## Files Structure\n\n"
        for file_path, info in self.context["files"].items():
            md += f"- **{file_path}** ({info['lines']} lines)\n"
            if info["classes"]:
                md += "  - Classes: " + ", ".join(c["name"] for c in info["classes"]) + "\n"
            if info["functions"]:
                md += "  - Functions: " + ", ".join(f["name"] for f in info["functions"]) + "\n"
        
        # API Endpoints
        if self.context["api_endpoints"]:
            md += "\n## API Endpoints\n\n"
            for endpoint in self.context["api_endpoints"]:
                md += f"- `{endpoint['method']} {endpoint['path']}` (in {endpoint['file']})\n"
        
        # Services
        if self.context["services"]:
            md += "\n## Services\n\n"
            for service in self.context["services"]:
                md += f"- **{service['name']}**: {service['description']}\n"
        
        # Models
        if self.context["models"]:
            md += "\n## Models\n\n"
            for model in self.context["models"]:
                md += f"- **{model['name']}**: {model['description']}\n"
        
        # Event Interactions
        if self.context["event_subscriptions"]:
            md += "\n## Event Subscriptions\n\n"
            for sub in self.context["event_subscriptions"]:
                md += f"- Subscribes to `{sub['event']}` in {sub['file']}\n"
        
        if self.context["event_publications"]:
            md += "\n## Event Publications\n\n"
            for pub in self.context["event_publications"]:
                md += f"- Publishes `{pub['event']}` in {pub['file']}\n"
        
        # Tests
        if self.context["tests"]:
            md += "\n## Tests\n\n"
            md += "Run tests with: `pytest modules/{}/tests/`\n\n".format(self.module_name)
            for test in self.context["tests"]:
                md += f"- {test['file']}\n"
        
        # Dependencies
        unique_deps = list(set(self.context["dependencies"]))
        internal_deps = [d for d in unique_deps if d.startswith("modules.")]
        external_deps = [d for d in unique_deps if not d.startswith("modules.")]
        
        if internal_deps or external_deps:
            md += "\n## Dependencies\n\n"
            if internal_deps:
                md += "### Internal Modules\n"
                for dep in sorted(internal_deps):
                    md += f"- {dep}\n"
            if external_deps:
                md += "\n### External Libraries\n"
                for dep in sorted(external_deps):
                    md += f"- {dep}\n"
        
        return md


def main():
    parser = argparse.ArgumentParser(
        description="Generate context for a SOLEil module"
    )
    parser.add_argument(
        "module",
        help="Name of the module to generate context for"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--output",
        help="Output file (default: stdout)"
    )
    
    args = parser.parse_args()
    
    # Find modules directory
    modules_dir = Path(__file__).parent.parent / "modules"
    
    # Generate context
    generator = ModuleContextGenerator(args.module, modules_dir)
    try:
        context = generator.generate()
        
        # Format output
        if args.format == "json":
            output = json.dumps(context, indent=2)
        else:
            output = generator.format_as_markdown()
        
        # Write output
        if args.output:
            Path(args.output).write_text(output)
            print(f"Context written to {args.output}")
        else:
            print(output)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()