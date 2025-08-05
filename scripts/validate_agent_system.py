#!/usr/bin/env python3
"""
Agent Assignment System Validation Script
Validates all components of PRP 09 implementation
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json
import importlib.util

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class AgentSystemValidator:
    """Validates the agent assignment system implementation."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.validation_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print(f"\n{BLUE}SOLEil Agent Assignment System Validation{RESET}")
        print("=" * 60)
        
        # Run validation checks
        self._validate_directory_structure()
        self._validate_agent_contexts()
        self._validate_core_implementations()
        self._validate_api_endpoints()
        self._validate_tools_and_scripts()
        self._validate_documentation()
        
        # Print summary
        self._print_summary()
        
        return len(self.validation_results["failed"]) == 0
    
    def _validate_directory_structure(self):
        """Validate required directories exist."""
        print(f"\n{YELLOW}1. Validating Directory Structure{RESET}")
        
        required_dirs = [
            "agent_contexts",
            "band-platform/backend/modules/core",
            "band-platform/backend/modules/core/api",
            "band-platform/backend/tests/agent_tests",
            "scripts/agent_tools"
        ]
        
        for dir_path in required_dirs:
            full_path = self.base_path / dir_path
            if full_path.exists() and full_path.is_dir():
                self._pass(f"Directory exists: {dir_path}")
            else:
                self._fail(f"Directory missing: {dir_path}")
    
    def _validate_agent_contexts(self):
        """Validate agent context files."""
        print(f"\n{YELLOW}2. Validating Agent Context Files{RESET}")
        
        required_contexts = [
            "AGENT_TEMPLATE.md",
            "auth_agent.md",
            "content_agent.md",
            "drive_agent.md",
            "sync_agent.md",
            "dashboard_agent.md",
            "integration_agent.md",
            "AGENT_COMMUNICATION_PROTOCOL.md",
            "AGENT_ONBOARDING_GUIDE.md"
        ]
        
        context_dir = self.base_path / "agent_contexts"
        
        for context_file in required_contexts:
            file_path = context_dir / context_file
            if file_path.exists():
                # Check file size
                size = file_path.stat().st_size
                if size > 1000:  # At least 1KB
                    self._pass(f"Context file valid: {context_file} ({size} bytes)")
                else:
                    self._warn(f"Context file too small: {context_file} ({size} bytes)")
            else:
                self._fail(f"Context file missing: {context_file}")
        
        # Validate context content structure
        self._validate_context_content()
    
    def _validate_context_content(self):
        """Validate agent context file contents."""
        context_dir = self.base_path / "agent_contexts"
        agent_files = ["auth_agent.md", "content_agent.md", "drive_agent.md", 
                      "sync_agent.md", "dashboard_agent.md", "integration_agent.md"]
        
        required_sections = [
            "## Your Identity",
            "## Your Scope",
            "## Your Capabilities",
            "## Your Restrictions"
        ]
        
        for agent_file in agent_files:
            file_path = context_dir / agent_file
            if file_path.exists():
                content = file_path.read_text()
                missing_sections = []
                
                for section in required_sections:
                    if section not in content:
                        missing_sections.append(section)
                
                if missing_sections:
                    self._warn(f"{agent_file} missing sections: {', '.join(missing_sections)}")
                else:
                    self._pass(f"{agent_file} has all required sections")
    
    def _validate_core_implementations(self):
        """Validate core module implementations."""
        print(f"\n{YELLOW}3. Validating Core Module Implementations{RESET}")
        
        core_files = {
            "agent_coordinator.py": ["AgentCoordinator", "Agent", "ChangeRequest"],
            "agent_handoff_system.py": ["HandoffManager", "HandoffRequest", "TaskContext"],
            "agent_performance_tracker.py": ["PerformanceTracker", "PerformanceMetric"],
            "api/agent_dashboard_routes.py": ["router", "register_agent", "get_dashboard_overview"]
        }
        
        core_path = self.base_path / "band-platform/backend/modules/core"
        
        for file_name, required_items in core_files.items():
            file_path = core_path / file_name
            if file_path.exists():
                content = file_path.read_text()
                missing_items = []
                
                for item in required_items:
                    if f"class {item}" not in content and f"def {item}" not in content and item not in content:
                        missing_items.append(item)
                
                if missing_items:
                    self._fail(f"{file_name} missing: {', '.join(missing_items)}")
                else:
                    self._pass(f"{file_name} contains all required components")
            else:
                self._fail(f"Core file missing: {file_name}")
    
    def _validate_api_endpoints(self):
        """Validate API endpoints are properly defined."""
        print(f"\n{YELLOW}4. Validating API Endpoints{RESET}")
        
        api_file = self.base_path / "band-platform/backend/modules/core/api/agent_dashboard_routes.py"
        
        if not api_file.exists():
            self._fail("API routes file not found")
            return
        
        content = api_file.read_text()
        
        required_endpoints = [
            ('POST', '/register', 'register_agent'),
            ('GET', '/list', 'list_agents'),
            ('GET', '/{agent_id}', 'get_agent_details'),
            ('POST', '/handoff/initiate', 'initiate_handoff'),
            ('GET', '/performance/{agent_id}', 'get_agent_performance'),
            ('GET', '/dashboard/overview', 'get_dashboard_overview')
        ]
        
        for method, path, function in required_endpoints:
            pattern = f'@router.{method.lower()}("{path}"'
            if pattern in content or pattern.replace('"', "'") in content:
                self._pass(f"Endpoint found: {method} {path}")
            else:
                self._fail(f"Endpoint missing: {method} {path}")
    
    def _validate_tools_and_scripts(self):
        """Validate agent tools and scripts."""
        print(f"\n{YELLOW}5. Validating Tools and Scripts{RESET}")
        
        scripts = {
            "scripts/agent_tools/workspace_isolation.py": ["WorkspaceIsolation", "create_workspace"],
            "scripts/agent_tools/onboard_agent.py": ["AgentOnboarding", "start_onboarding"]
        }
        
        for script_path, required_items in scripts.items():
            file_path = self.base_path / script_path
            if file_path.exists():
                # Check if executable
                if os.access(file_path, os.X_OK):
                    self._pass(f"Script is executable: {script_path}")
                else:
                    self._warn(f"Script not executable: {script_path}")
                
                # Check content
                content = file_path.read_text()
                for item in required_items:
                    if item in content:
                        self._pass(f"{script_path} contains: {item}")
                    else:
                        self._fail(f"{script_path} missing: {item}")
            else:
                self._fail(f"Script missing: {script_path}")
    
    def _validate_documentation(self):
        """Validate documentation completeness."""
        print(f"\n{YELLOW}6. Validating Documentation{RESET}")
        
        # Check if PRP 09 has been moved to archive
        active_prp = self.base_path / "PRPs/active/09_create_agent_assignment_system.md"
        archive_prp = self.base_path / "PRPs/archive/09_create_agent_assignment_system.md"
        
        if archive_prp.exists():
            self._pass("PRP 09 has been archived (completed)")
        elif active_prp.exists():
            self._warn("PRP 09 still in active folder")
        else:
            self._warn("PRP 09 not found in active or archive")
        
        # Check communication protocol
        protocol_file = self.base_path / "agent_contexts/AGENT_COMMUNICATION_PROTOCOL.md"
        if protocol_file.exists():
            content = protocol_file.read_text()
            required_sections = [
                "## Communication Channels",
                "## Message Formats",
                "## Protocol Rules",
                "## Security Protocols"
            ]
            
            missing = [s for s in required_sections if s not in content]
            if missing:
                self._warn(f"Communication protocol missing sections: {', '.join(missing)}")
            else:
                self._pass("Communication protocol is complete")
    
    def _pass(self, message: str):
        """Record a passing check."""
        self.validation_results["passed"].append(message)
        print(f"  {GREEN}✓{RESET} {message}")
    
    def _fail(self, message: str):
        """Record a failing check."""
        self.validation_results["failed"].append(message)
        print(f"  {RED}✗{RESET} {message}")
    
    def _warn(self, message: str):
        """Record a warning."""
        self.validation_results["warnings"].append(message)
        print(f"  {YELLOW}⚠{RESET} {message}")
    
    def _print_summary(self):
        """Print validation summary."""
        print(f"\n{BLUE}Validation Summary{RESET}")
        print("=" * 60)
        
        total = len(self.validation_results["passed"]) + len(self.validation_results["failed"])
        passed = len(self.validation_results["passed"])
        failed = len(self.validation_results["failed"])
        warnings = len(self.validation_results["warnings"])
        
        print(f"Total Checks: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"{YELLOW}Warnings: {warnings}{RESET}")
        
        if failed == 0:
            print(f"\n{GREEN}✅ All validation checks passed!{RESET}")
            print("\nThe Agent Assignment System is ready for use.")
        else:
            print(f"\n{RED}❌ Validation failed with {failed} errors.{RESET}")
            print("\nPlease fix the errors before proceeding.")
        
        # Save results
        results_file = self.base_path / "agent_system_validation_results.json"
        from datetime import datetime
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.validation_results,
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "warnings": warnings
                }
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")


def main():
    """Run validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Agent Assignment System")
    parser.add_argument("--base-path", default=".", help="Base path of the project")
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path).resolve()
    validator = AgentSystemValidator(base_path)
    
    success = validator.validate_all()
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()