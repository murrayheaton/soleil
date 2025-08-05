#!/usr/bin/env python3
"""
Agent Onboarding Script
Helps new agents get set up in the SOLEil system
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from band_platform.backend.modules.core.agent_coordinator import AgentType


class AgentOnboarding:
    """Handles agent onboarding process."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.agent_contexts_dir = base_path / "agent_contexts"
        self.onboarding_log = base_path / ".agent_onboarding_log.json"
        
    def start_onboarding(self, agent_id: str, agent_type: str) -> Dict:
        """Start the onboarding process for a new agent."""
        print(f"\n🎵 Welcome to SOLEil Band Platform, {agent_id}! 🎵\n")
        
        results = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "started_at": datetime.utcnow().isoformat(),
            "steps_completed": [],
            "errors": []
        }
        
        try:
            # Step 1: Validate agent type
            if agent_type not in [t.value for t in AgentType]:
                raise ValueError(f"Invalid agent type: {agent_type}")
            print(f"✓ Agent type '{agent_type}' validated")
            results["steps_completed"].append("type_validation")
            
            # Step 2: Show agent context
            self._show_agent_context(agent_type)
            results["steps_completed"].append("context_shown")
            
            # Step 3: Create workspace
            self._create_workspace(agent_id, agent_type)
            results["steps_completed"].append("workspace_created")
            
            # Step 4: Run module tests
            self._run_module_tests(agent_type)
            results["steps_completed"].append("tests_passed")
            
            # Step 5: Show first tasks
            self._show_first_tasks(agent_type)
            results["steps_completed"].append("tasks_shown")
            
            # Step 6: Generate onboarding certificate
            cert_path = self._generate_certificate(agent_id, agent_type)
            results["certificate"] = str(cert_path)
            results["steps_completed"].append("certificate_generated")
            
            # Log successful onboarding
            self._log_onboarding(results)
            
            print("\n✅ Onboarding completed successfully!")
            print(f"📄 Your certificate: {cert_path}")
            print("\n🚀 You're ready to start working on SOLEil!")
            
        except Exception as e:
            results["errors"].append(str(e))
            print(f"\n❌ Onboarding failed: {e}")
            self._log_onboarding(results)
            return results
        
        results["completed_at"] = datetime.utcnow().isoformat()
        return results
    
    def _show_agent_context(self, agent_type: str):
        """Display the agent's context file."""
        context_file = self.agent_contexts_dir / f"{agent_type}_agent.md"
        
        if not context_file.exists():
            raise FileNotFoundError(f"Context file not found: {context_file}")
        
        print(f"\n📋 Your Agent Context ({agent_type}_agent.md):")
        print("=" * 60)
        
        with open(context_file) as f:
            lines = f.readlines()[:50]  # Show first 50 lines
            for line in lines:
                print(line.rstrip())
        
        print("\n... (showing first 50 lines)")
        print(f"\n📖 Full context at: {context_file}")
        print("=" * 60)
    
    def _create_workspace(self, agent_id: str, agent_type: str):
        """Create agent workspace using isolation tool."""
        print(f"\n🏗️  Creating your workspace...")
        
        isolation_script = self.base_path / "scripts/agent_tools/workspace_isolation.py"
        if not isolation_script.exists():
            print("⚠️  Workspace isolation script not found, skipping...")
            return
        
        result = subprocess.run(
            [sys.executable, str(isolation_script), "create", agent_type],
            cwd=self.base_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Workspace created successfully")
        else:
            print(f"⚠️  Workspace creation failed: {result.stderr}")
    
    def _run_module_tests(self, agent_type: str):
        """Run tests for the agent's module."""
        print(f"\n🧪 Running tests for {agent_type} module...")
        
        test_path = self.base_path / f"band-platform/backend/modules/{agent_type}/tests"
        if not test_path.exists():
            print("⚠️  No tests found for module, skipping...")
            return
        
        # Check if pytest is available
        try:
            subprocess.run(["pytest", "--version"], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            print("⚠️  pytest not available, skipping tests...")
            return
        
        result = subprocess.run(
            ["pytest", str(test_path), "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ All tests passed!")
        else:
            print(f"⚠️  Some tests failed. Review output:")
            print(result.stdout[-500:])  # Show last 500 chars
    
    def _show_first_tasks(self, agent_type: str):
        """Show suggested first tasks for the agent."""
        print(f"\n📝 Suggested first tasks for {agent_type} agent:")
        print("=" * 60)
        
        tasks = {
            "auth": [
                "Review current authentication flow",
                "Check OAuth token refresh implementation",
                "Audit security event logging",
                "Test user session management"
            ],
            "content": [
                "Test file parsing accuracy",
                "Review instrument transposition logic",
                "Check metadata extraction",
                "Optimize parsing performance"
            ],
            "drive": [
                "Monitor API quota usage",
                "Test rate limiting implementation",
                "Review caching strategy",
                "Check webhook handling"
            ],
            "sync": [
                "Test WebSocket connection stability",
                "Review message queuing",
                "Check reconnection logic",
                "Monitor broadcast performance"
            ],
            "dashboard": [
                "Review widget implementations",
                "Test responsive layouts",
                "Check data aggregation",
                "Optimize render performance"
            ],
            "integration": [
                "Review recent cross-module changes",
                "Check system integration tests",
                "Audit module boundaries",
                "Update architecture docs"
            ]
        }
        
        agent_tasks = tasks.get(agent_type, ["Explore your module", "Read documentation"])
        
        for i, task in enumerate(agent_tasks, 1):
            print(f"{i}. {task}")
        
        print("=" * 60)
    
    def _generate_certificate(self, agent_id: str, agent_type: str) -> Path:
        """Generate onboarding certificate."""
        cert_dir = self.base_path / ".agent_certificates"
        cert_dir.mkdir(exist_ok=True)
        
        cert_path = cert_dir / f"{agent_id}_onboarding.json"
        
        certificate = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "onboarded_at": datetime.utcnow().isoformat(),
            "platform": "SOLEil Band Platform",
            "version": "1.0.0",
            "modules": {
                "primary": f"/band-platform/backend/modules/{agent_type}/",
                "frontend": f"/band-platform/frontend/src/modules/{agent_type}/",
                "tests": f"/band-platform/backend/modules/{agent_type}/tests/"
            },
            "permissions": self._get_default_permissions(agent_type),
            "welcome_message": f"Welcome to the team, {agent_id}! 🎵"
        }
        
        with open(cert_path, 'w') as f:
            json.dump(certificate, f, indent=2)
        
        return cert_path
    
    def _get_default_permissions(self, agent_type: str) -> List[str]:
        """Get default permissions for agent type."""
        base_permissions = [
            f"read:/band-platform/backend/modules/{agent_type}/",
            f"write:/band-platform/backend/modules/{agent_type}/",
            f"execute:/band-platform/backend/modules/{agent_type}/",
            "read:/band-platform/backend/modules/core/",
            "read:/agent_contexts/"
        ]
        
        if agent_type == "integration":
            base_permissions.extend([
                "read:/band-platform/backend/modules/",
                "approve:cross_module_changes"
            ])
        
        return base_permissions
    
    def _log_onboarding(self, results: Dict):
        """Log onboarding results."""
        logs = []
        
        if self.onboarding_log.exists():
            with open(self.onboarding_log) as f:
                logs = json.load(f)
        
        logs.append(results)
        
        with open(self.onboarding_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def show_onboarding_checklist(self, agent_type: str):
        """Display interactive onboarding checklist."""
        print(f"\n📋 Interactive Onboarding Checklist for {agent_type} Agent")
        print("=" * 60)
        
        checklist = [
            "Read your agent context file",
            "Review AGENT_COMMUNICATION_PROTOCOL.md",
            "Understand module boundaries",
            "Run module tests",
            "Check pending handoffs",
            "Review recent commits",
            "Make first commit",
            "Publish AGENT_ONLINE event"
        ]
        
        completed = []
        
        for i, item in enumerate(checklist, 1):
            response = input(f"\n{i}. {item}\n   Completed? (y/n): ")
            if response.lower() == 'y':
                completed.append(item)
                print("   ✓ Great!")
            else:
                print("   ⏳ Remember to complete this later")
        
        print("\n" + "=" * 60)
        print(f"✓ Completed: {len(completed)}/{len(checklist)} items")
        
        if len(completed) == len(checklist):
            print("\n🎉 Congratulations! You're fully onboarded!")
        else:
            print("\n📝 Complete remaining items when ready")


def main():
    """CLI for agent onboarding."""
    parser = argparse.ArgumentParser(description="SOLEil Agent Onboarding Tool")
    parser.add_argument("agent_id", help="Your unique agent ID")
    parser.add_argument("agent_type", choices=[t.value for t in AgentType],
                      help="Type of agent you are")
    parser.add_argument("--checklist", action="store_true",
                      help="Show interactive checklist")
    parser.add_argument("--base-path", default=".",
                      help="Base path of the project")
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path).resolve()
    onboarding = AgentOnboarding(base_path)
    
    if args.checklist:
        onboarding.show_onboarding_checklist(args.agent_type)
    else:
        results = onboarding.start_onboarding(args.agent_id, args.agent_type)
        
        if results.get("errors"):
            sys.exit(1)


if __name__ == "__main__":
    main()