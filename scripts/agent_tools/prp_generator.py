#!/usr/bin/env python3
"""
PRP Generator for SOLEil Multi-Agent Development System
Automatically generates Project Requirement Prompts from user requirements
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import argparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Complexity(str, Enum):
    SMALL = "S"      # 1-4 hours
    MEDIUM = "M"     # 4-16 hours
    LARGE = "L"      # 16-40 hours
    XLARGE = "XL"    # 40+ hours


class TaskType(str, Enum):
    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"


@dataclass
class UserRequirement:
    """User requirement input."""
    description: str
    type: TaskType
    priority: Priority = Priority.MEDIUM
    user_story: Optional[str] = None
    acceptance_criteria: List[str] = field(default_factory=list)
    technical_notes: Optional[str] = None


@dataclass
class ImplementationTask:
    """Individual implementation task."""
    title: str
    agent_type: str
    description: str
    files_to_modify: List[str]
    implementation_steps: List[str]
    test_requirements: List[str]
    estimated_hours: float


@dataclass
class PRP:
    """Project Requirement Prompt."""
    number: int
    title: str
    description: str
    priority: Priority
    complexity: Complexity
    modules_affected: List[str]
    business_justification: str
    pre_implementation: List[str]
    success_criteria: List[str]
    implementation_tasks: List[ImplementationTask]
    testing_procedures: Dict[str, List[str]]
    deployment_steps: List[str]
    rollback_plan: List[str]
    post_deployment: List[str]


class PRPGenerator:
    """Generates PRPs from user requirements."""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.prp_dir = base_path / "PRPs" / "active"
        self.prp_dir.mkdir(parents=True, exist_ok=True)
        self.template_path = base_path / ".claude" / "commands" / "prp_generation_template.md"
        
    def analyze_requirement(self, requirement: UserRequirement) -> Dict:
        """Analyze requirement to determine affected modules and complexity."""
        analysis = {
            "modules": self._identify_modules(requirement),
            "complexity": self._estimate_complexity(requirement),
            "agents_needed": self._determine_agents(requirement),
            "dependencies": self._find_dependencies(requirement),
            "risks": self._assess_risks(requirement)
        }
        return analysis
    
    def _identify_modules(self, requirement: UserRequirement) -> List[str]:
        """Identify which modules are affected by the requirement."""
        modules = []
        desc_lower = requirement.description.lower()
        
        # Module detection patterns
        module_patterns = {
            "auth": ["login", "authentication", "oauth", "session", "user", "profile"],
            "content": ["chart", "pdf", "music", "repertoire", "instrument", "parsing"],
            "drive": ["google drive", "file", "storage", "sync", "folder"],
            "sync": ["real-time", "websocket", "update", "broadcast", "offline"],
            "dashboard": ["ui", "interface", "display", "widget", "layout", "responsive"],
            "frontend": ["react", "component", "ui", "interface", "responsive", "pwa"],
            "backend": ["api", "endpoint", "database", "service", "business logic"]
        }
        
        for module, keywords in module_patterns.items():
            if any(keyword in desc_lower for keyword in keywords):
                modules.append(module)
        
        # Default to frontend/backend if no specific module identified
        if not modules:
            if any(word in desc_lower for word in ["ui", "display", "show", "view"]):
                modules.append("frontend")
            else:
                modules.append("backend")
        
        return list(set(modules))
    
    def _estimate_complexity(self, requirement: UserRequirement) -> Complexity:
        """Estimate implementation complexity."""
        desc_lower = requirement.description.lower()
        
        # Complexity indicators
        if any(word in desc_lower for word in ["simple", "minor", "small", "tweak"]):
            return Complexity.SMALL
        elif any(word in desc_lower for word in ["integrate", "major", "redesign", "architecture"]):
            return Complexity.XLARGE
        elif any(word in desc_lower for word in ["new feature", "implement", "create"]):
            return Complexity.LARGE
        else:
            return Complexity.MEDIUM
    
    def _determine_agents(self, requirement: UserRequirement) -> List[str]:
        """Determine which agents are needed."""
        agents = ["orchestrator", "planning"]  # Always involved
        
        modules = self._identify_modules(requirement)
        
        # Map modules to agents
        if "frontend" in modules or "dashboard" in modules:
            agents.append("frontend")
        if "backend" in modules or any(m in modules for m in ["auth", "content", "drive", "sync"]):
            agents.append("backend")
        if "drive" in modules:
            agents.append("integration")
        
        # Always include testing
        agents.extend(["unit_test", "integration_test"])
        
        return list(set(agents))
    
    def _find_dependencies(self, requirement: UserRequirement) -> List[str]:
        """Find potential dependencies."""
        dependencies = []
        desc_lower = requirement.description.lower()
        
        if "google" in desc_lower:
            dependencies.append("Google API credentials configured")
        if "offline" in desc_lower:
            dependencies.append("Service worker implementation")
        if "database" in desc_lower:
            dependencies.append("Database migrations")
        
        return dependencies
    
    def _assess_risks(self, requirement: UserRequirement) -> List[str]:
        """Assess potential risks."""
        risks = []
        desc_lower = requirement.description.lower()
        
        if "authentication" in desc_lower or "security" in desc_lower:
            risks.append("Security vulnerability if not implemented correctly")
        if "performance" in desc_lower:
            risks.append("Potential performance degradation")
        if "google" in desc_lower:
            risks.append("API quota limits")
        if "breaking" in desc_lower or "migration" in desc_lower:
            risks.append("Breaking changes for existing users")
        
        return risks
    
    def generate_prp(self, requirement: UserRequirement) -> PRP:
        """Generate a complete PRP from a requirement."""
        analysis = self.analyze_requirement(requirement)
        
        # Get next PRP number
        prp_number = self._get_next_prp_number()
        
        # Generate title
        title = self._generate_title(requirement)
        
        # Create implementation tasks
        tasks = self._create_implementation_tasks(requirement, analysis)
        
        prp = PRP(
            number=prp_number,
            title=title,
            description=self._expand_description(requirement),
            priority=requirement.priority,
            complexity=analysis["complexity"],
            modules_affected=analysis["modules"],
            business_justification=self._create_business_justification(requirement),
            pre_implementation=self._create_pre_implementation_checklist(requirement, analysis),
            success_criteria=self._create_success_criteria(requirement),
            implementation_tasks=tasks,
            testing_procedures=self._create_testing_procedures(tasks),
            deployment_steps=self._create_deployment_steps(requirement),
            rollback_plan=self._create_rollback_plan(requirement),
            post_deployment=self._create_post_deployment_steps(requirement)
        )
        
        return prp
    
    def _get_next_prp_number(self) -> int:
        """Get the next available PRP number."""
        existing_prps = list(self.prp_dir.glob("*.md"))
        if not existing_prps:
            return 10  # Start from 10 for user-generated PRPs
        
        numbers = []
        for prp in existing_prps:
            match = re.match(r"(\d+)_", prp.name)
            if match:
                numbers.append(int(match.group(1)))
        
        return max(numbers) + 1 if numbers else 10
    
    def _generate_title(self, requirement: UserRequirement) -> str:
        """Generate a descriptive title."""
        # Simple title generation - could be enhanced with NLP
        words = requirement.description.split()[:6]
        title = "_".join(word.lower() for word in words if word.isalnum())
        return title
    
    def _expand_description(self, requirement: UserRequirement) -> str:
        """Expand the description with more detail."""
        base = requirement.description
        if requirement.user_story:
            base += f" This addresses the user story: {requirement.user_story}"
        return base
    
    def _create_business_justification(self, requirement: UserRequirement) -> str:
        """Create business justification."""
        if requirement.user_story:
            return f"This feature is needed because: {requirement.user_story}"
        
        # Generate based on type
        if requirement.type == TaskType.FEATURE:
            return "This new feature will enhance user experience and provide additional value to musicians using the platform."
        elif requirement.type == TaskType.BUG_FIX:
            return "This fix is critical to ensure platform reliability and user satisfaction."
        elif requirement.type == TaskType.PERFORMANCE:
            return "This optimization will improve platform responsiveness and user experience, especially on mobile devices."
        else:
            return "This improvement will enhance the overall quality and maintainability of the platform."
    
    def _create_pre_implementation_checklist(self, requirement: UserRequirement, analysis: Dict) -> List[str]:
        """Create pre-implementation checklist."""
        checklist = [
            "Read relevant module documentation (MODULE.md files)",
            "Review current implementation in affected modules",
            "Check for existing tests that might be affected",
            f"Create feature branch: `git checkout -b {requirement.type.value}/{self._generate_title(requirement)}`"
        ]
        
        if analysis["dependencies"]:
            checklist.extend([f"Ensure {dep}" for dep in analysis["dependencies"]])
        
        return checklist
    
    def _create_success_criteria(self, requirement: UserRequirement) -> List[str]:
        """Create measurable success criteria."""
        criteria = requirement.acceptance_criteria.copy() if requirement.acceptance_criteria else []
        
        # Add standard criteria based on type
        if requirement.type == TaskType.FEATURE:
            criteria.extend([
                "Feature works as described in all supported browsers",
                "Feature is responsive on mobile devices",
                "No regression in existing functionality"
            ])
        elif requirement.type == TaskType.BUG_FIX:
            criteria.extend([
                "Bug no longer reproducible",
                "No new bugs introduced",
                "Regression test added to prevent recurrence"
            ])
        elif requirement.type == TaskType.PERFORMANCE:
            criteria.extend([
                "Performance improvement measurable (specify metric)",
                "No functional regressions",
                "Performance test added to maintain improvement"
            ])
        
        return criteria
    
    def _create_implementation_tasks(self, requirement: UserRequirement, analysis: Dict) -> List[ImplementationTask]:
        """Create detailed implementation tasks."""
        tasks = []
        
        # Frontend tasks
        if "frontend" in analysis["modules"]:
            tasks.append(ImplementationTask(
                title="Implement UI Components",
                agent_type="frontend",
                description="Create or modify React components for the feature",
                files_to_modify=self._estimate_frontend_files(requirement),
                implementation_steps=[
                    "Create/modify React components",
                    "Add TypeScript interfaces",
                    "Implement responsive design",
                    "Add accessibility features"
                ],
                test_requirements=[
                    "Component renders correctly",
                    "User interactions work as expected",
                    "Responsive on all screen sizes",
                    "Accessibility standards met"
                ],
                estimated_hours=self._estimate_hours(analysis["complexity"], "frontend")
            ))
        
        # Backend tasks
        if "backend" in analysis["modules"]:
            tasks.append(ImplementationTask(
                title="Implement Backend Logic",
                agent_type="backend",
                description="Create or modify API endpoints and services",
                files_to_modify=self._estimate_backend_files(requirement),
                implementation_steps=[
                    "Create/modify FastAPI endpoints",
                    "Implement service layer logic",
                    "Add data validation",
                    "Handle errors appropriately"
                ],
                test_requirements=[
                    "API endpoints return correct data",
                    "Input validation works",
                    "Error cases handled gracefully",
                    "Performance within acceptable limits"
                ],
                estimated_hours=self._estimate_hours(analysis["complexity"], "backend")
            ))
        
        return tasks
    
    def _estimate_frontend_files(self, requirement: UserRequirement) -> List[str]:
        """Estimate which frontend files need modification."""
        files = []
        desc_lower = requirement.description.lower()
        
        if "component" in desc_lower or "ui" in desc_lower:
            files.append("src/components/NewComponent.tsx")
        if "page" in desc_lower or "route" in desc_lower:
            files.append("src/app/new-route/page.tsx")
        if "api" in desc_lower:
            files.append("src/lib/api/client.ts")
        
        return files if files else ["src/components/[ComponentName].tsx"]
    
    def _estimate_backend_files(self, requirement: UserRequirement) -> List[str]:
        """Estimate which backend files need modification."""
        files = []
        desc_lower = requirement.description.lower()
        
        if "endpoint" in desc_lower or "api" in desc_lower:
            files.append("app/api/routes.py")
        if "service" in desc_lower or "logic" in desc_lower:
            files.append("app/services/service.py")
        if "model" in desc_lower or "database" in desc_lower:
            files.append("app/models/model.py")
        
        return files if files else ["app/api/[endpoint].py"]
    
    def _estimate_hours(self, complexity: Complexity, agent_type: str) -> float:
        """Estimate hours for a task."""
        base_hours = {
            Complexity.SMALL: 2,
            Complexity.MEDIUM: 8,
            Complexity.LARGE: 24,
            Complexity.XLARGE: 40
        }
        
        # Adjust based on agent type
        multipliers = {
            "frontend": 1.0,
            "backend": 1.2,
            "integration": 1.5,
            "testing": 0.5
        }
        
        return base_hours[complexity] * multipliers.get(agent_type, 1.0)
    
    def _create_testing_procedures(self, tasks: List[ImplementationTask]) -> Dict[str, List[str]]:
        """Create testing procedures."""
        procedures = {
            "unit_tests": [],
            "integration_tests": [],
            "e2e_tests": []
        }
        
        for task in tasks:
            if task.agent_type == "frontend":
                procedures["unit_tests"].extend([
                    "Test component rendering",
                    "Test user interactions",
                    "Test edge cases"
                ])
                procedures["e2e_tests"].extend([
                    "Test complete user flow",
                    "Test on multiple devices"
                ])
            elif task.agent_type == "backend":
                procedures["unit_tests"].extend([
                    "Test service functions",
                    "Test data validation",
                    "Test error handling"
                ])
                procedures["integration_tests"].extend([
                    "Test API endpoints",
                    "Test database operations"
                ])
        
        return procedures
    
    def _create_deployment_steps(self, requirement: UserRequirement) -> List[str]:
        """Create deployment steps."""
        return [
            "Ensure all tests pass locally",
            "Create pull request with detailed description",
            "Wait for code review approval",
            "Merge to main branch",
            "Deploy to staging environment",
            "Run smoke tests on staging",
            "Deploy to production",
            "Monitor for errors"
        ]
    
    def _create_rollback_plan(self, requirement: UserRequirement) -> List[str]:
        """Create rollback plan."""
        return [
            "If critical issues discovered:",
            "1. Revert the merge commit: `git revert <commit-hash>`",
            "2. Deploy reverted code to production",
            "3. Investigate issue in development environment",
            "4. Fix issue and re-test thoroughly",
            "5. Re-deploy when confidence restored"
        ]
    
    def _create_post_deployment_steps(self, requirement: UserRequirement) -> List[str]:
        """Create post-deployment steps."""
        return [
            "Monitor error logs for 24 hours",
            "Check performance metrics",
            "Gather user feedback",
            "Update documentation if needed",
            "Close related issues/tickets",
            "Update TASK.md and DEV_LOG.md"
        ]
    
    def save_prp(self, prp: PRP) -> Path:
        """Save PRP to file."""
        filename = f"{prp.number:02d}_{prp.title}.md"
        filepath = self.prp_dir / filename
        
        content = self._format_prp(prp)
        filepath.write_text(content)
        
        return filepath
    
    def _format_prp(self, prp: PRP) -> str:
        """Format PRP as markdown."""
        lines = [
            f"# PRP {prp.number:02d}: {prp.title.replace('_', ' ').title()}",
            "",
            "## Overview",
            f"**Description**: {prp.description}",
            f"**Priority**: {prp.priority.value.title()}",
            f"**Estimated Effort**: {prp.complexity.value}",
            f"**Modules Affected**: {', '.join(prp.modules_affected)}",
            "",
            "## Business Justification",
            prp.business_justification,
            "",
            "## Pre-Implementation Requirements"
        ]
        
        for item in prp.pre_implementation:
            lines.append(f"- [ ] {item}")
        
        lines.extend([
            "",
            "## Success Criteria"
        ])
        
        for criterion in prp.success_criteria:
            lines.append(f"- [ ] {criterion}")
        
        lines.extend([
            "",
            "## Implementation Tasks",
            ""
        ])
        
        for i, task in enumerate(prp.implementation_tasks, 1):
            lines.extend([
                f"### Task {i}: {task.title}",
                f"**Assigned to**: {task.agent_type}_agent",
                f"**Estimated hours**: {task.estimated_hours}",
                "",
                "**Files to modify**:"
            ])
            
            for file in task.files_to_modify:
                lines.append(f"- `{file}`")
            
            lines.extend([
                "",
                "**Implementation steps**:"
            ])
            
            for step in task.implementation_steps:
                lines.append(f"1. {step}")
            
            lines.extend([
                "",
                "**Testing requirements**:"
            ])
            
            for req in task.test_requirements:
                lines.append(f"- {req}")
            
            lines.append("")
        
        lines.extend([
            "## Testing Procedures",
            ""
        ])
        
        for test_type, procedures in prp.testing_procedures.items():
            if procedures:
                lines.append(f"### {test_type.replace('_', ' ').title()}")
                for proc in procedures:
                    lines.append(f"- {proc}")
                lines.append("")
        
        lines.extend([
            "## Deployment Steps"
        ])
        
        for i, step in enumerate(prp.deployment_steps, 1):
            lines.append(f"{i}. {step}")
        
        lines.extend([
            "",
            "## Rollback Plan"
        ])
        
        for step in prp.rollback_plan:
            lines.append(step)
        
        lines.extend([
            "",
            "## Post-Deployment"
        ])
        
        for step in prp.post_deployment:
            lines.append(f"- [ ] {step}")
        
        return "\n".join(lines)


def main():
    """CLI for PRP generation."""
    parser = argparse.ArgumentParser(description="Generate PRPs for SOLEil development")
    parser.add_argument("description", help="Description of the requirement")
    parser.add_argument("--type", choices=[t.value for t in TaskType], 
                      default="feature", help="Type of requirement")
    parser.add_argument("--priority", choices=[p.value for p in Priority],
                      default="medium", help="Priority level")
    parser.add_argument("--user-story", help="User story for context")
    parser.add_argument("--criteria", nargs="+", help="Acceptance criteria")
    parser.add_argument("--base-path", default=".", help="Base path of project")
    
    args = parser.parse_args()
    
    # Create requirement
    requirement = UserRequirement(
        description=args.description,
        type=TaskType(args.type),
        priority=Priority(args.priority),
        user_story=args.user_story,
        acceptance_criteria=args.criteria or []
    )
    
    # Generate PRP
    generator = PRPGenerator(Path(args.base_path))
    prp = generator.generate_prp(requirement)
    
    # Save PRP
    filepath = generator.save_prp(prp)
    
    print(f"✅ PRP generated successfully!")
    print(f"📄 Saved to: {filepath}")
    print(f"📊 Complexity: {prp.complexity.value}")
    print(f"👥 Agents needed: {len(set(task.agent_type for task in prp.implementation_tasks))}")
    print(f"⏱️  Estimated hours: {sum(task.estimated_hours for task in prp.implementation_tasks)}")


if __name__ == "__main__":
    main()