"""
SOLEil Orchestrator Agent - Production Deployment
Main coordination agent for the multi-agent development system
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


class OrchestratorAgent:
    """Main orchestrator agent for coordinating multi-agent development"""
    
    def __init__(self, config_path: Path = Path("./agent_deployment/config.json")):
        self.config_path = config_path
        self.config = self._load_config()
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
        
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "max_parallel_tasks": 5,
            "task_timeout": 3600,  # 1 hour
            "retry_limit": 3,
            "monitoring_interval": 60  # seconds
        }
    
    async def start(self):
        """Start the orchestrator agent"""
        logger.info("🚀 Starting SOLEil Orchestrator Agent")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._monitor_agents()),
            asyncio.create_task(self._process_task_queue()),
            asyncio.create_task(self._collect_metrics()),
            asyncio.create_task(self._handle_failures())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down Orchestrator Agent")
            for task in tasks:
                task.cancel()
    
    async def receive_prp(self, prp_content: Dict) -> PRP:
        """Receive and process a new PRP"""
        prp_id = f"PRP_{uuid.uuid4().hex[:8]}"
        logger.info(f"📋 Received new PRP: {prp_id}")
        
        # Parse PRP and create tasks
        tasks = await self._parse_prp_to_tasks(prp_id, prp_content)
        
        prp = PRP(
            prp_id=prp_id,
            title=prp_content.get("title", "Untitled PRP"),
            description=prp_content.get("description", ""),
            tasks=tasks,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            completed_at=None
        )
        
        self.active_prps[prp_id] = prp
        
        # Add tasks to queue
        for task in tasks:
            self.task_queue.append(task)
            self.active_tasks[task.task_id] = task
        
        logger.info(f"✅ PRP {prp_id} created with {len(tasks)} tasks")
        return prp
    
    async def _parse_prp_to_tasks(self, prp_id: str, prp_content: Dict) -> List[Task]:
        """Parse PRP content into executable tasks"""
        tasks = []
        
        # Example task breakdown logic
        task_definitions = [
            {
                "description": "Analyze requirements and create implementation plan",
                "agent": AgentType.PLANNING,
                "priority": 1,
                "dependencies": []
            },
            {
                "description": "Implement backend API endpoints",
                "agent": AgentType.BACKEND,
                "priority": 2,
                "dependencies": ["planning"]
            },
            {
                "description": "Create frontend components",
                "agent": AgentType.FRONTEND,
                "priority": 2,
                "dependencies": ["planning"]
            },
            {
                "description": "Set up database schema",
                "agent": AgentType.DATABASE,
                "priority": 2,
                "dependencies": ["planning"]
            },
            {
                "description": "Write unit tests",
                "agent": AgentType.UNIT_TEST,
                "priority": 3,
                "dependencies": ["backend", "frontend"]
            },
            {
                "description": "Perform security scan",
                "agent": AgentType.SECURITY,
                "priority": 3,
                "dependencies": ["backend", "database"]
            },
            {
                "description": "Review code quality",
                "agent": AgentType.CODE_REVIEW,
                "priority": 4,
                "dependencies": ["backend", "frontend", "unit_test"]
            },
            {
                "description": "Generate documentation",
                "agent": AgentType.DOCUMENTATION,
                "priority": 5,
                "dependencies": ["code_review"]
            }
        ]
        
        for i, task_def in enumerate(task_definitions):
            task = Task(
                task_id=f"{prp_id}_task_{i:03d}",
                prp_id=prp_id,
                description=task_def["description"],
                agent_type=task_def["agent"],
                status=TaskStatus.PENDING,
                priority=task_def["priority"],
                dependencies=task_def["dependencies"],
                created_at=datetime.now()
            )
            tasks.append(task)
        
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
        
        # Simulate agent execution (in production, this would be actual agent call)
        asyncio.create_task(self._execute_task(task))
        
        return True
    
    async def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies are met"""
        for dep in task.dependencies:
            # Find dependent tasks
            for other_task in self.active_tasks.values():
                if dep in other_task.description.lower() and other_task.status != TaskStatus.COMPLETED:
                    return False
        return True
    
    async def _execute_task(self, task: Task):
        """Execute a task (simulated for now)"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            logger.info(f"🔄 Executing task {task.task_id}")
            
            # Simulate task execution time
            await asyncio.sleep(5)  # In production, this would be actual agent execution
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = {
                "success": True,
                "files_modified": ["file1.py", "file2.py"],
                "tests_passed": True
            }
            
            self.metrics["tasks_completed"] += 1
            logger.info(f"✅ Task {task.task_id} completed successfully")
            
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
        report_path = Path(f"./agent_deployment/reports/PRP_{prp.prp_id}_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report generated for PRP {prp.prp_id}")
    
    async def _monitor_agents(self):
        """Monitor agent health and status"""
        while True:
            await asyncio.sleep(self.config["monitoring_interval"])
            
            active_agents = sum(1 for status in self.agent_status.values() if status == "busy")
            idle_agents = sum(1 for status in self.agent_status.values() if status == "idle")
            
            logger.debug(f"Agent Status - Active: {active_agents}, Idle: {idle_agents}")
            
            # Calculate utilization
            for agent_type in AgentType:
                if agent_type not in self.metrics["agent_utilization"]:
                    self.metrics["agent_utilization"][agent_type.value] = []
                
                utilization = 100 if self.agent_status[agent_type] == "busy" else 0
                self.metrics["agent_utilization"][agent_type.value].append(utilization)
    
    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while True:
            await asyncio.sleep(5)  # Check queue every 5 seconds
            
            if not self.task_queue:
                continue
            
            # Sort by priority
            self.task_queue.sort(key=lambda t: t.priority)
            
            # Try to assign tasks
            for task in self.task_queue[:]:
                if task.status == TaskStatus.PENDING:
                    if await self.assign_task(task):
                        self.task_queue.remove(task)
    
    async def _collect_metrics(self):
        """Collect and save metrics periodically"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            
            metrics_snapshot = {
                "timestamp": datetime.now().isoformat(),
                "tasks_completed": self.metrics["tasks_completed"],
                "tasks_failed": self.metrics["tasks_failed"],
                "active_prps": len([p for p in self.active_prps.values() if p.status != TaskStatus.COMPLETED]),
                "queue_size": len(self.task_queue),
                "agent_utilization": {
                    agent: statistics.mean(util[-10:]) if util else 0
                    for agent, util in self.metrics["agent_utilization"].items()
                }
            }
            
            # Save metrics
            metrics_path = Path("./agent_deployment/metrics/metrics.jsonl")
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(metrics_path, 'a') as f:
                f.write(json.dumps(metrics_snapshot) + '\n')
            
            logger.debug("Metrics collected and saved")
    
    async def _handle_failures(self):
        """Handle failed tasks and retry logic"""
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            failed_tasks = [
                task for task in self.active_tasks.values()
                if task.status == TaskStatus.FAILED
            ]
            
            for task in failed_tasks:
                logger.info(f"🔄 Retrying failed task {task.task_id}")
                task.status = TaskStatus.PENDING
                self.task_queue.append(task)
    
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


# CLI Interface
async def main():
    """Main entry point for orchestrator"""
    orchestrator = OrchestratorAgent()
    
    # Start orchestrator in background
    orchestrator_task = asyncio.create_task(orchestrator.start())
    
    # Example: Process a test PRP
    test_prp = {
        "title": "Implement User Dashboard",
        "description": "Create a comprehensive user dashboard with analytics and settings"
    }
    
    await orchestrator.receive_prp(test_prp)
    
    # Keep running
    try:
        await orchestrator_task
    except KeyboardInterrupt:
        logger.info("Orchestrator shutdown requested")


if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════╗
    ║   SOLEil Orchestrator Agent v1.0.0    ║
    ║   Multi-Agent Development System       ║
    ╚════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Orchestrator Agent stopped")