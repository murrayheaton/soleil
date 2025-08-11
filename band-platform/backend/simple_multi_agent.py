#!/usr/bin/env python3
"""
Simple Multi-Agent System for SOLEil
A working version that focuses on core functionality
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAgent:
    """Simple agent implementation."""
    
    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
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

class SimpleAgentCoordinator:
    """Simple agent coordinator."""
    
    def __init__(self):
        self.agents: Dict[str, SimpleAgent] = {}
        self.tasks: Dict[str, Dict] = {}
        self.task_counter = 0
        
    def register_agent(self, agent: SimpleAgent) -> bool:
        """Register an agent."""
        if agent.agent_id in self.agents:
            logger.warning(f"Agent {agent.agent_id} already registered")
            return False
        
        self.agents[agent.agent_id] = agent
        logger.info(f"✅ Registered agent: {agent.agent_id} ({agent.agent_type})")
        return True
    
    def create_task(self, task_type: str, description: str, priority: str = "normal") -> str:
        """Create a new task."""
        self.task_counter += 1
        task_id = f"TASK-{self.task_counter:03d}"
        
        task = {
            'id': task_id,
            'type': task_type,
            'description': description,
            'priority': priority,
            'status': 'pending',
            'created_at': datetime.now(),
            'assigned_to': None
        }
        
        self.tasks[task_id] = task
        logger.info(f"📋 Created task: {task_id} - {description}")
        return task_id
    
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
    
    def get_system_status(self) -> Dict:
        """Get current system status."""
        return {
            'total_agents': len(self.agents),
            'total_tasks': len(self.tasks),
            'pending_tasks': len([t for t in self.tasks.values() if t['status'] == 'pending']),
            'assigned_tasks': len([t for t in self.tasks.values() if t['status'] == 'assigned']),
            'completed_tasks': sum(len(agent.completed_tasks) for agent in self.agents.values()),
            'agents': [
                {
                    'id': agent.agent_id,
                    'type': agent.agent_type,
                    'active_tasks': len(agent.active_tasks),
                    'completed_tasks': len(agent.completed_tasks),
                    'capabilities': agent.capabilities
                }
                for agent in self.agents.values()
            ]
        }

async def demo_multi_agent_system():
    """Demonstrate the multi-agent system."""
    logger.info("🚀 Starting Simple Multi-Agent System Demo...")
    
    # Create coordinator
    coordinator = SimpleAgentCoordinator()
    
    # Create and register agents
    agents = [
        SimpleAgent("orchestrator_001", "orchestrator", ["planning", "coordination", "deployment"]),
        SimpleAgent("frontend_001", "frontend", ["ui_development", "component_creation", "styling"]),
        SimpleAgent("backend_001", "backend", ["api_development", "database", "authentication"]),
        SimpleAgent("testing_001", "testing", ["unit_tests", "integration_tests", "e2e_tests"]),
        SimpleAgent("security_001", "security", ["security_audit", "vulnerability_scan", "compliance"])
    ]
    
    for agent in agents:
        coordinator.register_agent(agent)
    
    # Create some sample tasks
    tasks = [
        ("ui_development", "Create responsive chart viewer component", "high"),
        ("api_development", "Implement user profile API endpoint", "high"),
        ("unit_tests", "Write tests for auth validation routes", "medium"),
        ("security_audit", "Review OAuth implementation security", "high"),
        ("planning", "Create PRP for offline chart viewing", "medium")
    ]
    
    for task_type, description, priority in tasks:
        task_id = coordinator.create_task(task_type, description, priority)
        coordinator.assign_task_to_best_agent(task_id)
    
    # Show system status
    logger.info("📊 System Status:")
    status = coordinator.get_system_status()
    logger.info(json.dumps(status, indent=2, default=str))
    
    # Simulate some task completion
    await asyncio.sleep(2)
    
    # Complete a task
    for agent in agents:
        if agent.active_tasks:
            task = agent.active_tasks[0]
            agent.complete_task(task['id'], {'result': 'success', 'notes': 'Task completed successfully'})
            break
    
    # Show final status
    logger.info("📊 Final System Status:")
    final_status = coordinator.get_system_status()
    logger.info(json.dumps(final_status, indent=2, default=str))
    
    logger.info("✅ Multi-agent system demo completed!")

if __name__ == "__main__":
    try:
        asyncio.run(demo_multi_agent_system())
    except KeyboardInterrupt:
        logger.info("🛑 Multi-agent system stopped by user")
    except Exception as e:
        logger.error(f"💥 Multi-agent system error: {e}")
        raise
