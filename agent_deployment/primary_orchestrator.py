#!/usr/bin/env python3
"""
SOLEil Primary Orchestrator Agent
Main coordination agent that I control directly to manage the multi-agent development system
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class AgentType(Enum):
    """Available agent types"""
    ORCHESTRATOR = "orchestrator"
    PLANNING = "planning"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    SECURITY = "security"
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    E2E_TEST = "e2e_test"
    DEVOPS = "devops"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"

@dataclass
class Task:
    """Task representation"""
    task_id: str
    prp_id: str
    description: str
    agent_type: AgentType
    status: TaskStatus
    priority: int
    dependencies: List[str]
    created_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class PRP:
    """Project Requirement Prompt representation"""
    prp_id: str
    title: str
    description: str
    tasks: List[Task]
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

class PrimaryOrchestratorAgent:
    """Primary orchestrator agent that I control directly"""
    
    def __init__(self):
        self.active_tasks: Dict[str, Task] = {}
        self.active_prps: Dict[str, PRP] = {}
        self.agent_status: Dict[AgentType, str] = {
            agent: "idle" for agent in AgentType
        }
        self.task_queue: List[Task] = []
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_completion_time": 0,
            "agent_utilization": {}
        }
        
    async def receive_prp(self, prp_content: Dict) -> PRP:
        """Receive and process a new PRP"""
        prp_id = f"PRP_{uuid.uuid4().hex[:8]}"
        
        # Parse PRP content into tasks
        tasks = await self._parse_prp_to_tasks(prp_id, prp_content)
        
        # Create PRP
        prp = PRP(
            prp_id=prp_id,
            title=prp_content.get('title', 'Untitled PRP'),
            description=prp_content.get('description', ''),
            tasks=tasks,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Add to active PRPs
        self.active_prps[prp_id] = prp
        
        # Add tasks to queue
        for task in tasks:
            self.task_queue.append(task)
            self.active_tasks[task.task_id] = task
        
        logger.info(f"📋 Received new PRP: {prp_id}")
        logger.info(f"✅ PRP {prp_id} created with {len(tasks)} tasks")
        
        return prp
    
    async def _parse_prp_to_tasks(self, prp_id: str, prp_content: Dict) -> List[Task]:
        """Parse PRP content into actionable tasks"""
        tasks = []
        
        # Extract content for analysis
        content = prp_content.get('full_content', prp_content.get('description', ''))
        
        # Create tasks based on content analysis
        if 'auth' in content.lower() or 'authentication' in content.lower():
            tasks.extend([
                Task(
                    task_id=f"{prp_id}_task_000",
                    prp_id=prp_id,
                    description="Analyze authentication requirements and create implementation plan",
                    agent_type=AgentType.PLANNING,
                    status=TaskStatus.PENDING,
                    priority=1,
                    dependencies=[],
                    created_at=datetime.now()
                ),
                Task(
                    task_id=f"{prp_id}_task_001",
                    prp_id=prp_id,
                    description="Implement backend authentication endpoints and JWT handling",
                    agent_type=AgentType.BACKEND,
                    status=TaskStatus.PENDING,
                    priority=2,
                    dependencies=[f"{prp_id}_task_000"],
                    created_at=datetime.now()
                ),
                Task(
                    task_id=f"{prp_id}_task_002",
                    prp_id=prp_id,
                    description="Create frontend authentication components and context",
                    agent_type=AgentType.FRONTEND,
                    status=TaskStatus.PENDING,
                    priority=2,
                    dependencies=[f"{prp_id}_task_000"],
                    created_at=datetime.now()
                ),
                Task(
                    task_id=f"{prp_id}_task_003",
                    prp_id=prp_id,
                    description="Update database schema for user authentication",
                    agent_type=AgentType.DATABASE,
                    status=TaskStatus.PENDING,
                    priority=2,
                    dependencies=[f"{prp_id}_task_000"],
                    created_at=datetime.now()
                ),
                Task(
                    task_id=f"{prp_id}_task_004",
                    prp_id=prp_id,
                    description="Write unit tests for authentication components",
                    agent_type=AgentType.UNIT_TEST,
                    status=TaskStatus.PENDING,
                    priority=3,
                    dependencies=[f"{prp_id}_task_001", f"{prp_id}_task_002"],
                    created_at=datetime.now()
                ),
                Task(
                    task_id=f"{prp_id}_task_005",
                    prp_id=prp_id,
                    description="Perform security review of authentication implementation",
                    agent_type=AgentType.SECURITY,
                    status=TaskStatus.PENDING,
                    priority=4,
                    dependencies=[f"{prp_id}_task_001", f"{prp_id}_task_002"],
                    created_at=datetime.now()
                ),
                Task(
                    task_id=f"{prp_id}_task_006",
                    prp_id=prp_id,
                    description="Run integration tests for complete auth flow",
                    agent_type=AgentType.INTEGRATION_TEST,
                    status=TaskStatus.PENDING,
                    priority=5,
                    dependencies=[f"{prp_id}_task_004", f"{prp_id}_task_005"],
                    created_at=datetime.now()
                ),
                Task(
                    task_id=f"{prp_id}_task_007",
                    prp_id=prp_id,
                    description="Update documentation for authentication system",
                    agent_type=AgentType.DOCUMENTATION,
                    status=TaskStatus.PENDING,
                    priority=6,
                    dependencies=[f"{prp_id}_task_006"],
                    created_at=datetime.now()
                )
            ])
        else:
            # Generic task breakdown
            tasks.append(Task(
                task_id=f"{prp_id}_task_000",
                prp_id=prp_id,
                description="Analyze requirements and create implementation plan",
                agent_type=AgentType.PLANNING,
                status=TaskStatus.PENDING,
                priority=1,
                dependencies=[],
                created_at=datetime.now()
            ))
        
        return tasks
    
    async def assign_task(self, task: Task) -> bool:
        """Assign a task to an agent"""
        agent_type = task.agent_type
        
        # Check if agent is available
        if self.agent_status[agent_type] != "idle":
            logger.debug(f"Agent {agent_type.value} is busy, task {task.task_id} queued")
            return False
        
        # Check dependencies
        if not await self._check_dependencies(task):
            logger.debug(f"Task {task.task_id} has unmet dependencies")
            task.status = TaskStatus.BLOCKED
            return False
        
        # Assign task
        logger.info(f"📤 Assigning task {task.task_id} to {agent_type.value}")
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now()
        self.agent_status[agent_type] = "busy"
        
        # Execute task
        asyncio.create_task(self._execute_task(task))
        
        return True
    
    async def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are met"""
        for dep in task.dependencies:
            # Find dependent tasks
            dependent_task_found = False
            for other_task in self.active_tasks.values():
                if dep in other_task.task_id:
                    dependent_task_found = True
                    if other_task.status != TaskStatus.COMPLETED:
                        logger.debug(f"Task {task.task_id} blocked by {dep} (status: {other_task.status.value})")
                        return False
                    break
            
            if not dependent_task_found:
                logger.warning(f"Dependency {dep} not found for task {task.task_id}")
                return False
        
        return True

    async def _execute_task(self, task: Task):
        """Execute a task using the appropriate agent"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            logger.info(f"🔄 Executing task {task.task_id}")
            
            # Simulate agent execution (in production, this would call actual agents)
            await asyncio.sleep(3)  # Simulate work time
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = {
                "success": True,
                "agent": task.agent_type.value,
                "files_modified": [f"task_{task.task_id}_result.py"],
                "tests_passed": True
            }
            
            self.metrics["tasks_completed"] += 1
            logger.info(f"✅ Task {task.task_id} completed successfully by {task.agent_type.value}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self.metrics["tasks_failed"] += 1
            logger.error(f"❌ Task {task.task_id} failed: {e}")
        
        finally:
            # Free up agent
            self.agent_status[task.agent_type] = "idle"
            
            # Check if PRP is complete
            await self._check_prp_completion(task.prp_id)
            
            # Re-evaluate blocked tasks that might now be unblocked
            await self._reevaluate_blocked_tasks()
    
    async def _reevaluate_blocked_tasks(self):
        """Re-evaluate blocked tasks to see if they can now proceed"""
        for task in self.active_tasks.values():
            if task.status == TaskStatus.BLOCKED:
                if await self._check_dependencies(task):
                    logger.info(f"🔄 Task {task.task_id} is now unblocked, setting to PENDING")
                    task.status = TaskStatus.PENDING
                    # Add back to queue if not already there
                    if task not in self.task_queue:
                        self.task_queue.append(task)
    
    async def _check_prp_completion(self, prp_id: str):
        """Check if all tasks in a PRP are complete"""
        prp = self.active_prps.get(prp_id)
        if not prp:
            return
        
        all_tasks = [t for t in self.active_tasks.values() if t.prp_id == prp_id]
        completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
        
        if len(completed_tasks) == len(all_tasks):
            prp.status = TaskStatus.COMPLETED
            prp.completed_at = datetime.now()
            logger.info(f"🎉 PRP {prp_id} completed successfully!")
            
            # Generate summary report
            await self._generate_prp_report(prp)
    
    async def _generate_prp_report(self, prp: PRP):
        """Generate completion report for PRP"""
        duration = (prp.completed_at - prp.created_at).total_seconds() / 3600
        
        report = {
            "prp_id": prp.prp_id,
            "title": prp.title,
            "status": "completed",
            "duration_hours": round(duration, 2),
            "tasks_completed": len(prp.tasks),
            "timestamp": prp.completed_at.isoformat()
        }
        
        # Save report
        reports_path = Path("./agent_deployment/reports")
        reports_path.mkdir(parents=True, exist_ok=True)
        
        with open(reports_path / f"{prp.prp_id}_report.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📊 Report saved for PRP {prp.prp_id}")
    
    async def process_task_queue(self):
        """Process tasks from the queue"""
        while True:
            await asyncio.sleep(2)  # Check queue every 2 seconds
            
            if not self.task_queue:
                continue
            
            # Sort by priority
            self.task_queue.sort(key=lambda t: t.priority)
            
            # Try to assign tasks
            for task in self.task_queue[:]:
                if task.status == TaskStatus.PENDING:
                    if await self.assign_task(task):
                        self.task_queue.remove(task)
                    elif task.status == TaskStatus.BLOCKED:
                        # Remove blocked tasks from queue (they'll be re-added when unblocked)
                        self.task_queue.remove(task)
    
    def get_status(self) -> Dict:
        """Get current orchestrator status"""
        return {
            "active_prps": len(self.active_prps),
            "active_tasks": len([t for t in self.active_tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
            "queued_tasks": len(self.task_queue),
            "completed_tasks": self.metrics["tasks_completed"],
            "failed_tasks": self.metrics["tasks_failed"],
            "agent_status": {k.value: v for k, v in self.agent_status.items()}
        }
    
    def get_detailed_status(self) -> Dict:
        """Get detailed status including task details"""
        return {
            "summary": self.get_status(),
            "prps": {
                prp_id: {
                    "title": prp.title,
                    "status": prp.status.value,
                    "tasks": len(prp.tasks)
                }
                for prp_id, prp in self.active_prps.items()
            },
            "tasks": {
                task_id: {
                    "description": task.description[:100],
                    "status": task.status.value,
                    "agent": task.agent_type.value,
                    "priority": task.priority
                }
                for task_id, task in self.active_tasks.items()
            }
        }

async def main():
    """Main entry point for the primary orchestrator"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     SOLEil Primary Orchestrator Agent                    ║
    ║              Multi-Agent Development System               ║
    ╚═══════════════════════════════════════════════════════════╝
    
    🚀 Starting Primary Orchestrator...
    """)
    
    # Initialize orchestrator
    orchestrator = PrimaryOrchestratorAgent()
    
    # Start task queue processor
    queue_processor = asyncio.create_task(orchestrator.process_task_queue())
    
    # Wait for system to initialize
    await asyncio.sleep(1)
    
    print("✅ Primary Orchestrator initialized successfully!")
    print("\n📋 Available Commands:")
    print("  - status: Show system status")
    print("  - detailed: Show detailed status")
    print("  - prp <file>: Process a PRP file")
    print("  - metrics: Show performance metrics")
    print("  - quit: Shutdown system")
    
    # Keep running
    try:
        await queue_processor
    except KeyboardInterrupt:
        logger.info("Primary Orchestrator shutdown requested")

if __name__ == "__main__":
    asyncio.run(main())
