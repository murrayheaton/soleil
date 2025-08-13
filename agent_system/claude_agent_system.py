#!/usr/bin/env python3
"""
Claude-Compatible Agent System for SOLEil
This system is designed to work with Claude's Task tool for agent delegation
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Specialized agent types that Claude can delegate to"""
    PLANNING = "planning"          # Break down requirements into tasks
    FRONTEND = "frontend"          # React/Next.js development
    BACKEND = "backend"            # Python/FastAPI development
    DATABASE = "database"          # Schema design and migrations
    TESTING = "testing"            # Unit, integration, E2E tests
    SECURITY = "security"          # Security analysis and fixes
    DOCUMENTATION = "documentation" # Update docs and guides
    DEVOPS = "devops"             # Deployment and CI/CD


@dataclass
class AgentTask:
    """Task structure for agent delegation"""
    task_id: str
    agent_type: AgentType
    description: str
    context: Dict[str, Any]
    priority: int = 1
    dependencies: List[str] = None
    
    def to_prompt(self) -> str:
        """Convert task to a prompt for Claude's Task tool"""
        prompt = f"""
You are a specialized {self.agent_type.value} agent working on the SOLEil Band Platform.

Task: {self.description}

Context:
{json.dumps(self.context, indent=2)}

Requirements:
- Focus only on {self.agent_type.value} aspects
- Follow SOLEil coding standards (CLAUDE.md)
- Use the modular architecture
- Create tests for any new code
- Update relevant documentation

Please complete this task and provide:
1. Summary of changes made
2. Files modified/created
3. Any issues encountered
4. Recommendations for next steps
"""
        return prompt


class ClaudeAgentSystem:
    """Agent system designed to work with Claude's capabilities"""
    
    def __init__(self):
        self.project_root = Path("/Users/murrayheaton/Documents/GitHub/soleil")
        self.prp_dir = self.project_root / "PRPs" / "active"
        self.agent_contexts_dir = self.project_root / "agent_contexts"
        self.active_tasks: Dict[str, AgentTask] = {}
        
    def analyze_prp(self, prp_path: Path) -> List[AgentTask]:
        """Analyze a PRP and break it down into agent tasks"""
        tasks = []
        
        try:
            with open(prp_path, 'r') as f:
                prp_content = f.read()
            
            # Parse PRP sections
            if "Backend" in prp_content or "API" in prp_content:
                tasks.append(self._create_backend_task(prp_content))
            
            if "Frontend" in prp_content or "UI" in prp_content or "Component" in prp_content:
                tasks.append(self._create_frontend_task(prp_content))
            
            if "Database" in prp_content or "Schema" in prp_content:
                tasks.append(self._create_database_task(prp_content))
            
            if "Test" in prp_content or "Testing" in prp_content:
                tasks.append(self._create_testing_task(prp_content))
            
            logger.info(f"Created {len(tasks)} tasks from PRP: {prp_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to analyze PRP: {e}")
            
        return tasks
    
    def _create_backend_task(self, prp_content: str) -> AgentTask:
        """Create a backend development task"""
        return AgentTask(
            task_id=f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_type=AgentType.BACKEND,
            description="Implement backend API endpoints and services",
            context={
                "module_path": "/band-platform/backend/modules",
                "framework": "FastAPI",
                "requirements": self._extract_backend_requirements(prp_content)
            }
        )
    
    def _create_frontend_task(self, prp_content: str) -> AgentTask:
        """Create a frontend development task"""
        return AgentTask(
            task_id=f"frontend_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_type=AgentType.FRONTEND,
            description="Implement frontend components and UI",
            context={
                "module_path": "/band-platform/frontend/src",
                "framework": "Next.js/React",
                "requirements": self._extract_frontend_requirements(prp_content)
            }
        )
    
    def _create_database_task(self, prp_content: str) -> AgentTask:
        """Create a database task"""
        return AgentTask(
            task_id=f"database_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_type=AgentType.DATABASE,
            description="Design database schema and migrations",
            context={
                "orm": "SQLAlchemy/SQLModel",
                "requirements": self._extract_database_requirements(prp_content)
            }
        )
    
    def _create_testing_task(self, prp_content: str) -> AgentTask:
        """Create a testing task"""
        return AgentTask(
            task_id=f"testing_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            agent_type=AgentType.TESTING,
            description="Create comprehensive tests",
            context={
                "backend_framework": "pytest",
                "frontend_framework": "Jest",
                "requirements": "Unit, integration, and E2E tests"
            }
        )
    
    def _extract_backend_requirements(self, content: str) -> List[str]:
        """Extract backend-specific requirements from PRP"""
        requirements = []
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['endpoint', 'api', 'service', 'backend']):
                requirements.append(line.strip())
        
        return requirements[:10]  # Limit to top 10 requirements
    
    def _extract_frontend_requirements(self, content: str) -> List[str]:
        """Extract frontend-specific requirements from PRP"""
        requirements = []
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['component', 'ui', 'frontend', 'react', 'display']):
                requirements.append(line.strip())
        
        return requirements[:10]
    
    def _extract_database_requirements(self, content: str) -> List[str]:
        """Extract database-specific requirements from PRP"""
        requirements = []
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['database', 'schema', 'table', 'model', 'migration']):
                requirements.append(line.strip())
        
        return requirements[:10]
    
    def get_agent_context(self, agent_type: AgentType) -> str:
        """Get the context/instructions for a specific agent type"""
        contexts = {
            AgentType.BACKEND: """
Focus on:
- FastAPI endpoint implementation
- Service layer business logic
- Google API integrations
- Database operations
- Error handling and validation
""",
            AgentType.FRONTEND: """
Focus on:
- React/Next.js components
- Responsive design
- State management
- API integration
- User experience
""",
            AgentType.DATABASE: """
Focus on:
- Schema design
- Data relationships
- Query optimization
- Migration scripts
- Data integrity
""",
            AgentType.TESTING: """
Focus on:
- Unit test coverage
- Integration tests
- E2E test scenarios
- Test data fixtures
- Performance testing
""",
            AgentType.SECURITY: """
Focus on:
- Authentication/authorization
- Input validation
- SQL injection prevention
- XSS protection
- Security best practices
""",
            AgentType.DOCUMENTATION: """
Focus on:
- API documentation
- Code comments
- README updates
- User guides
- Architecture diagrams
""",
            AgentType.DEVOPS: """
Focus on:
- CI/CD pipelines
- Docker configuration
- Environment setup
- Deployment scripts
- Monitoring setup
""",
            AgentType.PLANNING: """
Focus on:
- Task breakdown
- Dependency analysis
- Time estimation
- Risk assessment
- Implementation strategy
"""
        }
        
        return contexts.get(agent_type, "General development tasks")
    
    def create_task_summary(self) -> str:
        """Create a summary of all active tasks"""
        if not self.active_tasks:
            return "No active tasks"
        
        summary = "Active Tasks:\n"
        for task_id, task in self.active_tasks.items():
            summary += f"\n{task.agent_type.value.upper()} Agent:\n"
            summary += f"  Task ID: {task_id}\n"
            summary += f"  Description: {task.description}\n"
            summary += f"  Priority: {task.priority}\n"
        
        return summary
    
    def save_task_report(self, task_id: str, result: Dict[str, Any]):
        """Save the result of a completed task"""
        report_dir = self.project_root / "agent_system" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / f"{task_id}_report.json"
        
        report = {
            "task_id": task_id,
            "completed_at": datetime.now().isoformat(),
            "result": result
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Saved task report: {report_path}")


def main():
    """Example usage of the Claude Agent System"""
    system = ClaudeAgentSystem()
    
    # Check for active PRPs
    active_prps = list(system.prp_dir.glob("*.md"))
    
    if active_prps:
        print(f"Found {len(active_prps)} active PRPs:")
        for prp in active_prps:
            print(f"  - {prp.name}")
            
            # Analyze PRP and create tasks
            tasks = system.analyze_prp(prp)
            
            for task in tasks:
                system.active_tasks[task.task_id] = task
                print(f"\nCreated task for {task.agent_type.value} agent:")
                print(f"  ID: {task.task_id}")
                print(f"  Description: {task.description}")
    
    # Show task summary
    print("\n" + "="*50)
    print(system.create_task_summary())


if __name__ == "__main__":
    main()