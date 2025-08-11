#!/usr/bin/env python3
"""
SOLEil Multi-Agent Development System
A practical system that integrates with your existing PRPs and development workflow
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SOLEilAgent:
    """SOLEil development agent."""
    
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str], workspace_path: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.workspace_path = workspace_path
        self.active_tasks = []
        self.completed_tasks = []
        self.created_at = datetime.now()
        
    def can_handle(self, task_type: str) -> bool:
        """Check if agent can handle a task type."""
        return task_type in self.capabilities
    
    def assign_task(self, task: Dict) -> bool:
        """Assign a task to this agent."""
        if self.can_handle(task.get('type', '')):
            self.active_tasks.append(task)
            logger.info(f"Agent {self.agent_id} assigned task: {task.get('description', 'Unknown')}")
            return True
        return False
    
    def complete_task(self, task_id: str, result: Dict) -> bool:
        """Complete a task and move it to completed."""
        for i, task in enumerate(self.active_tasks):
            if task.get('id') == task_id:
                completed_task = self.active_tasks.pop(i)
                completed_task['result'] = result
                completed_task['completed_at'] = datetime.now()
                self.completed_tasks.append(completed_task)
                logger.info(f"Agent {self.agent_id} completed task: {completed_task.get('description', 'Unknown')}")
                return True
        return False
    
    def get_workspace_context(self) -> Dict:
        """Get context about the agent's workspace."""
        workspace = Path(self.workspace_path)
        if not workspace.exists():
            return {"error": f"Workspace {self.workspace_path} not found"}
        
        # Get relevant files in workspace
        relevant_files = []
        for file_path in workspace.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                relevant_files.append(str(file_path.relative_to(workspace)))
        
        return {
            "workspace": str(workspace),
            "total_files": len(relevant_files),
            "sample_files": relevant_files[:10]  # Show first 10 files
        }

class SOLEilCoordinator:
    """Coordinates SOLEil development agents."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.agents: Dict[str, SOLEilAgent] = {}
        self.tasks: Dict[str, Dict] = {}
        self.task_counter = 0
        self.prps = {}
        self._load_prps()
        
    def _load_prps(self):
        """Load existing PRPs from the project."""
        prp_dir = self.project_root / "PRPs"
        if not prp_dir.exists():
            logger.warning("PRPs directory not found")
            return
        
        # Load active PRPs
        active_dir = prp_dir / "active"
        if active_dir.exists():
            for prp_file in active_dir.glob("*.md"):
                try:
                    content = prp_file.read_text()
                    prp_id = prp_file.stem
                    self.prps[prp_id] = {
                        "file": str(prp_file),
                        "content": content,
                        "status": "active"
                    }
                    logger.info(f"📋 Loaded PRP: {prp_id}")
                except Exception as e:
                    logger.error(f"Failed to load PRP {prp_file}: {e}")
    
    def register_agent(self, agent: SOLEilAgent) -> bool:
        """Register a development agent."""
        if agent.agent_id in self.agents:
            logger.warning(f"Agent {agent.agent_id} already registered")
            return False
        
        self.agents[agent.agent_id] = agent
        logger.info(f"✅ Registered agent: {agent.agent_id} ({agent.agent_type})")
        return True
    
    def create_development_task(self, prp_id: str, task_type: str, description: str, priority: str = "normal") -> str:
        """Create a development task linked to a PRP."""
        if prp_id not in self.prps:
            logger.error(f"PRP {prp_id} not found")
            return None
        
        self.task_counter += 1
        task_id = f"TASK-{self.task_counter:03d}"
        
        task = {
            'id': task_id,
            'prp_id': prp_id,
            'type': task_type,
            'description': description,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now(),
            'assigned_to': None
        }
        
        self.tasks[task_id] = task
        logger.info(f"📋 Created development task: {task_id} for PRP {prp_id}")
        return task_id
    
    def create_profile_management_tasks(self) -> List[str]:
        """Create tasks for profile redirect logic and management script."""
        tasks = []
        
        # Task 1: Implement profile redirect logic
        task_1 = {
            "id": f"TASK-{self.task_counter + 1:03d}",
            "type": "backend",
            "prp_id": "profile_redirect_enhancement",
            "description": "Implement profile redirect logic: redirect existing users to dashboard, new users to profile setup",
            "priority": "high",
            "status": "pending",
            "created_at": datetime.now(),
            "assigned_to": None,
            "requirements": [
                "Modify OAuth callback to check if user has existing profile",
                "Redirect existing users to /dashboard",
                "Redirect new users to /profile?new_user=true",
                "Set appropriate cookies based on user status"
            ]
        }
        self.task_counter += 1
        self.tasks[task_1["id"]] = task_1
        tasks.append(task_1["id"])
        
        # Task 2: Create profile management script
        task_2 = {
            "id": f"TASK-{self.task_counter + 1:03d}",
            "type": "backend",
            "prp_id": "profile_management_script",
            "description": "Create backend script for easy profile registry management (add/remove profiles)",
            "priority": "high",
            "status": "pending",
            "created_at": datetime.now(),
            "assigned_to": None,
            "requirements": [
                "Create CLI script for profile management",
                "Add command to remove specific user profiles",
                "Add command to list all profiles",
                "Add command to backup/restore profile registry",
                "Ensure script is safe and has confirmation prompts"
            ]
        }
        self.task_counter += 1
        self.tasks[task_2["id"]] = task_2
        tasks.append(task_2["id"])
        
        logger.info(f"📋 Created {len(tasks)} profile management tasks")
        return tasks
    
    def assign_task_to_best_agent(self, task_id: str) -> Optional[str]:
        """Assign a task to the best available agent."""
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return None
        
        task = self.tasks[task_id]
        task_type = task['type']
        
        # Find agents that can handle this task type
        capable_agents = [
            agent for agent in self.agents.values()
            if agent.can_handle(task_type) and len(agent.active_tasks) < 3
        ]
        
        if not capable_agents:
            logger.warning(f"No capable agents available for task type: {task_type}")
            return None
        
        # Assign to agent with least active tasks
        best_agent = min(capable_agents, key=lambda a: len(a.active_tasks))
        
        if best_agent.assign_task(task):
            task['assigned_to'] = best_agent.agent_id
            task['status'] = 'assigned'
            task['assigned_at'] = datetime.now()
            logger.info(f"🎯 Task {task_id} assigned to {best_agent.agent_id}")
            return best_agent.agent_id
        
        return None
    
    def get_development_status(self) -> Dict:
        """Get current development status."""
        return {
            'project_root': str(self.project_root),
            'total_agents': len(self.agents),
            'total_tasks': len(self.tasks),
            'total_prps': len(self.prps),
            'pending_tasks': len([t for t in self.tasks.values() if t['status'] == 'pending']),
            'assigned_tasks': len([t for t in self.tasks.values() if t['status'] == 'assigned']),
            'completed_tasks': sum(len(agent.completed_tasks) for agent in self.agents.values()),
            'agents': [
                {
                    'id': agent.agent_id,
                    'type': agent.agent_type,
                    'workspace': agent.workspace_path,
                    'active_tasks': len(agent.active_tasks),
                    'completed_tasks': len(agent.completed_tasks),
                    'capabilities': agent.capabilities
                }
                for agent in self.agents.values()
            ],
            'prps': list(self.prps.keys())
        }
    
    def suggest_next_actions(self) -> List[str]:
        """Suggest next actions based on current state."""
        suggestions = []
        
        # Check for unassigned tasks
        unassigned = [t for t in self.tasks.values() if t['status'] == 'pending']
        if unassigned:
            suggestions.append(f"Assign {len(unassigned)} pending tasks to available agents")
        
        # Check for high-priority tasks
        high_priority = [t for t in self.tasks.values() if t['priority'] == 'high' and t['status'] != 'completed']
        if high_priority:
            suggestions.append(f"Focus on {len(high_priority)} high-priority tasks")
        
        # Check for completed tasks that need review
        completed = sum(len(agent.completed_tasks) for agent in self.agents.values())
        if completed > 0:
            suggestions.append(f"Review {completed} completed tasks")
        
        # Check for PRPs that need tasks created
        prps_without_tasks = [prp_id for prp_id in self.prps.keys() 
                             if not any(t['prp_id'] == prp_id for t in self.tasks.values())]
        if prps_without_tasks:
            suggestions.append(f"Create tasks for {len(prps_without_tasks)} PRPs without tasks")
        
        return suggestions

async def start_soleil_multi_agent_system():
    """Start the SOLEil multi-agent development system."""
    logger.info("🚀 Starting SOLEil Multi-Agent Development System...")
    
    # Get project root (assuming we're in band-platform/backend)
    project_root = Path(__file__).parent.parent.parent
    logger.info(f"📁 Project root: {project_root}")
    
    # Create coordinator
    coordinator = SOLEilCoordinator(project_root)
    
    # Create and register development agents
    agents = [
        SOLEilAgent(
            "orchestrator_001", 
            "orchestrator", 
            ["planning", "coordination", "deployment", "prp_management"],
            str(project_root)
        ),
        SOLEilAgent(
            "frontend_001", 
            "frontend", 
            ["ui_development", "component_creation", "styling", "responsive_design"],
            str(project_root / "frontend")
        ),
        SOLEilAgent(
            "backend_001", 
            "backend", 
            ["api_development", "database", "authentication", "oauth", "fastapi"],
            str(project_root / "backend")
        ),
        SOLEilAgent(
            "testing_001", 
            "testing", 
            ["unit_tests", "integration_tests", "e2e_tests", "test_automation"],
            str(project_root / "tests")
        ),
        SOLEilAgent(
            "security_001", 
            "security", 
            ["security_audit", "vulnerability_scan", "oauth_security", "compliance"],
            str(project_root)
        ),
        SOLEilAgent(
            "devops_001", 
            "devops", 
            ["deployment", "docker", "nginx", "ssl", "monitoring"],
            str(project_root)
        )
    ]
    
    for agent in agents:
        coordinator.register_agent(agent)
    
    # Show initial status
    logger.info("📊 Initial Development Status:")
    status = coordinator.get_development_status()
    logger.info(json.dumps(status, indent=2, default=str))
    
    # Show suggestions
    suggestions = coordinator.suggest_next_actions()
    if suggestions:
        logger.info("💡 Suggested Next Actions:")
        for suggestion in suggestions:
            logger.info(f"  - {suggestion}")
    
    # Create some development tasks based on current PRPs
    logger.info("🔧 Creating development tasks...")
    
    # Example: Create tasks for the offline chart viewer PRP
    if "10_implement_offline_chart_viewer" in coordinator.prps:
        coordinator.create_development_task(
            "10_implement_offline_chart_viewer",
            "ui_development",
            "Create responsive chart viewer component with offline support",
            "high"
        )
        coordinator.create_development_task(
            "10_implement_offline_chart_viewer",
            "api_development",
            "Implement offline chart data caching API",
            "high"
        )
        coordinator.create_development_task(
            "10_implement_offline_chart_viewer",
            "testing",
            "Write comprehensive tests for offline chart functionality",
            "medium"
        )
    
    # Create profile management tasks
    coordinator.create_profile_management_tasks()
    
    # Assign tasks to agents
    for task_id in coordinator.tasks:
        if coordinator.tasks[task_id]['status'] == 'pending':
            coordinator.assign_task_to_best_agent(task_id)
    
    # Show final status
    logger.info("📊 Final Development Status:")
    final_status = coordinator.get_development_status()
    logger.info(json.dumps(final_status, indent=2, default=str))
    
    logger.info("✅ SOLEil Multi-Agent Development System is ready!")
    logger.info("🔄 System is running. Press Ctrl+C to stop.")
    
    # Keep the system running
    while True:
        await asyncio.sleep(10)
        
        # Show periodic status updates
        suggestions = coordinator.suggest_next_actions()
        if suggestions:
            logger.info("💡 Current Suggestions:")
            for suggestion in suggestions:
                logger.info(f"  - {suggestion}")

if __name__ == "__main__":
    try:
        asyncio.run(start_soleil_multi_agent_system())
    except KeyboardInterrupt:
        logger.info("🛑 SOLEil Multi-Agent System stopped by user")
    except Exception as e:
        logger.error(f"💥 SOLEil Multi-Agent System error: {e}")
        raise
