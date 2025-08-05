"""
Agent Coordinator for SOLEil Platform
Manages agent registration, permissions, and cross-module change requests
"""

from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from pathlib import Path

from .event_bus import EventBus
from .api_gateway import APIGateway
from .events import Event

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents in the system."""
    AUTH = "auth"
    CONTENT = "content"
    DRIVE = "drive"
    SYNC = "sync"
    DASHBOARD = "dashboard"
    INTEGRATION = "integration"
    HUMAN = "human"  # For manual overrides


class PermissionLevel(str, Enum):
    """Permission levels for agents."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    APPROVE = "approve"


class ChangeRequestStatus(str, Enum):
    """Status of cross-module change requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"


@dataclass
class Agent:
    """Represents an agent in the system."""
    agent_id: str
    agent_type: AgentType
    module_scope: List[str]
    permissions: Dict[str, Set[PermissionLevel]]
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    active_tasks: List[str] = field(default_factory=list)
    
    def has_permission(self, path: str, level: PermissionLevel) -> bool:
        """Check if agent has permission for a path."""
        for scope_path, perms in self.permissions.items():
            if path.startswith(scope_path) and level in perms:
                return True
        return False


@dataclass
class ChangeRequest:
    """Cross-module change request."""
    request_id: str
    requesting_agent: str
    affected_modules: List[str]
    change_type: str
    description: str
    changes: Dict[str, any]
    status: ChangeRequestStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    implementation_result: Optional[Dict] = None


class AgentCoordinator:
    """Coordinates agent activities and cross-module changes."""
    
    def __init__(self, event_bus: EventBus, api_gateway: APIGateway):
        self.event_bus = event_bus
        self.api_gateway = api_gateway
        self.agents: Dict[str, Agent] = {}
        self.change_requests: Dict[str, ChangeRequest] = {}
        self.approval_queue: asyncio.Queue = asyncio.Queue()
        self._setup_default_permissions()
        
    def _setup_default_permissions(self):
        """Setup default permission mappings."""
        self.default_permissions = {
            AgentType.AUTH: {
                "/band-platform/backend/modules/auth/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE, 
                    PermissionLevel.EXECUTE
                },
                "/band-platform/frontend/src/modules/auth/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE
                }
            },
            AgentType.CONTENT: {
                "/band-platform/backend/modules/content/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE, 
                    PermissionLevel.EXECUTE
                },
                "/band-platform/frontend/src/modules/content/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE
                }
            },
            AgentType.DRIVE: {
                "/band-platform/backend/modules/drive/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE, 
                    PermissionLevel.EXECUTE
                },
                "/band-platform/frontend/src/modules/drive/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE
                }
            },
            AgentType.SYNC: {
                "/band-platform/backend/modules/sync/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE, 
                    PermissionLevel.EXECUTE
                },
                "/band-platform/frontend/src/modules/sync/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE
                }
            },
            AgentType.DASHBOARD: {
                "/band-platform/backend/modules/dashboard/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE, 
                    PermissionLevel.EXECUTE
                },
                "/band-platform/frontend/src/modules/dashboard/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE
                }
            },
            AgentType.INTEGRATION: {
                "/band-platform/backend/modules/core/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE, 
                    PermissionLevel.EXECUTE,
                    PermissionLevel.APPROVE
                },
                "/band-platform/backend/tests/integration/": {
                    PermissionLevel.READ, 
                    PermissionLevel.WRITE, 
                    PermissionLevel.EXECUTE
                },
                "/": {PermissionLevel.READ}  # Read access to entire codebase
            }
        }
    
    async def register_agent(
        self, 
        agent_id: str, 
        agent_type: AgentType,
        custom_permissions: Optional[Dict[str, Set[PermissionLevel]]] = None
    ) -> Agent:
        """Register a new agent in the system."""
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already registered")
        
        # Get default permissions for agent type
        permissions = self.default_permissions.get(agent_type, {}).copy()
        
        # Add any custom permissions
        if custom_permissions:
            permissions.update(custom_permissions)
        
        # Determine module scope from permissions
        module_scope = list(permissions.keys())
        
        agent = Agent(
            agent_id=agent_id,
            agent_type=agent_type,
            module_scope=module_scope,
            permissions=permissions
        )
        
        self.agents[agent_id] = agent
        
        # Notify system of new agent
        await self.event_bus.publish(
            event_type="AGENT_REGISTERED",
            data={
                "agent_id": agent_id,
                "agent_type": agent_type.value,
                "module_scope": module_scope
            },
            source_module="core"
        )
        
        logger.info(f"Registered agent: {agent_id} of type {agent_type}")
        return agent
    
    async def request_cross_module_change(
        self,
        requesting_agent_id: str,
        affected_modules: List[str],
        change_type: str,
        description: str,
        changes: Dict[str, any]
    ) -> str:
        """Submit a cross-module change request."""
        if requesting_agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {requesting_agent_id}")
        
        request_id = f"CR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{requesting_agent_id[:8]}"
        
        change_request = ChangeRequest(
            request_id=request_id,
            requesting_agent=requesting_agent_id,
            affected_modules=affected_modules,
            change_type=change_type,
            description=description,
            changes=changes,
            status=ChangeRequestStatus.PENDING
        )
        
        self.change_requests[request_id] = change_request
        
        # Queue for approval by integration agent
        await self.approval_queue.put(request_id)
        
        # Notify integration agent
        await self.event_bus.publish(
            event_type="CHANGE_REQUEST_SUBMITTED",
            data={
                "request_id": request_id,
                "requesting_agent": requesting_agent_id,
                "affected_modules": affected_modules,
                "change_type": change_type
            },
            source_module="core"
        )
        
        logger.info(f"Change request {request_id} submitted by {requesting_agent_id}")
        return request_id
    
    async def approve_change_request(
        self, 
        request_id: str, 
        approving_agent_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Approve a change request (integration agent only)."""
        if request_id not in self.change_requests:
            raise ValueError(f"Unknown change request: {request_id}")
        
        agent = self.agents.get(approving_agent_id)
        if not agent or agent.agent_type != AgentType.INTEGRATION:
            raise PermissionError("Only integration agent can approve changes")
        
        change_request = self.change_requests[request_id]
        change_request.status = ChangeRequestStatus.APPROVED
        change_request.reviewed_by = approving_agent_id
        change_request.reviewed_at = datetime.utcnow()
        
        # Notify affected modules
        await self.event_bus.publish(
            event_type="CHANGE_REQUEST_APPROVED",
            data={
                "request_id": request_id,
                "approved_by": approving_agent_id,
                "affected_modules": change_request.affected_modules,
                "changes": change_request.changes,
                "notes": notes
            },
            source_module="core"
        )
        
        logger.info(f"Change request {request_id} approved by {approving_agent_id}")
        return True
    
    async def reject_change_request(
        self, 
        request_id: str, 
        rejecting_agent_id: str,
        reason: str
    ) -> bool:
        """Reject a change request."""
        if request_id not in self.change_requests:
            raise ValueError(f"Unknown change request: {request_id}")
        
        agent = self.agents.get(rejecting_agent_id)
        if not agent or agent.agent_type != AgentType.INTEGRATION:
            raise PermissionError("Only integration agent can reject changes")
        
        change_request = self.change_requests[request_id]
        change_request.status = ChangeRequestStatus.REJECTED
        change_request.reviewed_by = rejecting_agent_id
        change_request.reviewed_at = datetime.utcnow()
        
        # Notify requesting agent
        await self.event_bus.publish(
            event_type="CHANGE_REQUEST_REJECTED",
            data={
                "request_id": request_id,
                "rejected_by": rejecting_agent_id,
                "reason": reason
            },
            source_module="core"
        )
        
        logger.info(f"Change request {request_id} rejected by {rejecting_agent_id}")
        return True
    
    async def validate_agent_action(
        self, 
        agent_id: str, 
        action_path: str,
        permission_level: PermissionLevel
    ) -> bool:
        """Validate if an agent can perform an action."""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        # Update last active time
        agent.last_active = datetime.utcnow()
        
        return agent.has_permission(action_path, permission_level)
    
    async def get_agent_performance(self, agent_id: str) -> Dict[str, float]:
        """Get performance metrics for an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        return {
            "tasks_completed": agent.performance_metrics.get("tasks_completed", 0),
            "average_task_time": agent.performance_metrics.get("avg_task_time", 0.0),
            "error_rate": agent.performance_metrics.get("error_rate", 0.0),
            "active_tasks": len(agent.active_tasks),
            "uptime_minutes": (datetime.utcnow() - agent.registered_at).total_seconds() / 60
        }
    
    async def assign_task_to_agent(
        self, 
        agent_id: str, 
        task_id: str,
        task_description: str
    ):
        """Assign a task to an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_id}")
        
        agent.active_tasks.append(task_id)
        
        await self.event_bus.publish(
            event_type="TASK_ASSIGNED",
            data={
                "agent_id": agent_id,
                "task_id": task_id,
                "description": task_description
            },
            source_module="core"
        )
    
    async def complete_agent_task(
        self, 
        agent_id: str, 
        task_id: str,
        duration_seconds: float,
        success: bool = True
    ):
        """Mark a task as completed."""
        agent = self.agents.get(agent_id)
        if not agent or task_id not in agent.active_tasks:
            return
        
        agent.active_tasks.remove(task_id)
        
        # Update performance metrics
        completed_count = agent.performance_metrics.get("tasks_completed", 0)
        agent.performance_metrics["tasks_completed"] = completed_count + 1
        
        # Update average task time
        avg_time = agent.performance_metrics.get("avg_task_time", 0.0)
        new_avg = ((avg_time * completed_count) + duration_seconds) / (completed_count + 1)
        agent.performance_metrics["avg_task_time"] = new_avg
        
        # Update error rate if task failed
        if not success:
            error_count = agent.performance_metrics.get("error_count", 0)
            agent.performance_metrics["error_count"] = error_count + 1
            agent.performance_metrics["error_rate"] = error_count / (completed_count + 1)
    
    async def get_active_agents(self) -> List[Dict]:
        """Get list of active agents."""
        active_threshold = datetime.utcnow().timestamp() - 300  # 5 minutes
        
        active_agents = []
        for agent_id, agent in self.agents.items():
            if agent.last_active.timestamp() > active_threshold:
                active_agents.append({
                    "agent_id": agent_id,
                    "agent_type": agent.agent_type.value,
                    "active_tasks": len(agent.active_tasks),
                    "last_active": agent.last_active.isoformat()
                })
        
        return active_agents
    
    async def handle_agent_handoff(
        self,
        from_agent_id: str,
        to_agent_id: str,
        task_context: Dict
    ):
        """Handle task handoff between agents."""
        from_agent = self.agents.get(from_agent_id)
        to_agent = self.agents.get(to_agent_id)
        
        if not from_agent or not to_agent:
            raise ValueError("Invalid agent IDs for handoff")
        
        # Publish handoff event
        await self.event_bus.publish(
            event_type="AGENT_HANDOFF",
            data={
                "from_agent": from_agent_id,
                "to_agent": to_agent_id,
                "task_context": task_context,
                "timestamp": datetime.utcnow().isoformat()
            },
            source_module="core"
        )
        
        logger.info(f"Task handoff from {from_agent_id} to {to_agent_id}")