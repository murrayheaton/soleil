"""
Agent Handoff System
Manages seamless task transitions between agents
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import logging
from collections import deque

from .event_bus import EventBus
from .agent_coordinator import AgentCoordinator, AgentType

logger = logging.getLogger(__name__)


class HandoffReason(str, Enum):
    """Reasons for agent handoffs."""
    EXPERTISE_REQUIRED = "expertise_required"
    WORKLOAD_BALANCE = "workload_balance"
    ERROR_RECOVERY = "error_recovery"
    SCHEDULED_ROTATION = "scheduled_rotation"
    PERMISSION_REQUIRED = "permission_required"
    TASK_COMPLETE = "task_complete"
    AGENT_UNAVAILABLE = "agent_unavailable"


class HandoffStatus(str, Enum):
    """Status of handoff operation."""
    INITIATED = "initiated"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class TaskContext:
    """Context for task being handed off."""
    task_id: str
    task_type: str
    description: str
    current_state: Dict[str, Any]
    history: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_history_entry(self, agent_id: str, action: str, details: Dict):
        """Add entry to task history."""
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "details": details
        })


@dataclass
class HandoffRequest:
    """Handoff request details."""
    handoff_id: str
    from_agent: str
    to_agent: str
    task_context: TaskContext
    reason: HandoffReason
    priority: str = "normal"  # low, normal, high, critical
    status: HandoffStatus = HandoffStatus.INITIATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    handoff_notes: Optional[str] = None


class HandoffProtocol:
    """Defines handoff protocol between agent types."""
    
    def __init__(self):
        self.allowed_handoffs = self._define_allowed_handoffs()
        self.handoff_validators = self._define_validators()
        
    def _define_allowed_handoffs(self) -> Dict[Tuple[AgentType, AgentType], List[str]]:
        """Define which handoffs are allowed between agent types."""
        return {
            # Content agent can hand off to Drive for file operations
            (AgentType.CONTENT, AgentType.DRIVE): [
                "file_retrieval", "file_update", "folder_organization"
            ],
            # Drive agent can hand off to Content for parsing
            (AgentType.DRIVE, AgentType.CONTENT): [
                "file_parsing", "metadata_extraction", "content_analysis"
            ],
            # Any agent can hand off to Integration for cross-module work
            (AgentType.CONTENT, AgentType.INTEGRATION): ["cross_module_change"],
            (AgentType.DRIVE, AgentType.INTEGRATION): ["cross_module_change"],
            (AgentType.AUTH, AgentType.INTEGRATION): ["cross_module_change"],
            (AgentType.SYNC, AgentType.INTEGRATION): ["cross_module_change"],
            (AgentType.DASHBOARD, AgentType.INTEGRATION): ["cross_module_change"],
            # Sync agent can hand off to any module for data updates
            (AgentType.SYNC, AgentType.CONTENT): ["content_sync"],
            (AgentType.SYNC, AgentType.DRIVE): ["file_sync"],
            (AgentType.SYNC, AgentType.DASHBOARD): ["dashboard_update"],
            # Dashboard can request data from other agents
            (AgentType.DASHBOARD, AgentType.CONTENT): ["data_aggregation"],
            (AgentType.DASHBOARD, AgentType.DRIVE): ["storage_metrics"],
            (AgentType.DASHBOARD, AgentType.AUTH): ["user_statistics"],
        }
    
    def _define_validators(self) -> Dict[str, Callable]:
        """Define validation functions for handoff types."""
        return {
            "file_retrieval": self._validate_file_operation,
            "file_parsing": self._validate_parsing_operation,
            "cross_module_change": self._validate_cross_module,
            "data_aggregation": self._validate_data_request,
        }
    
    def is_handoff_allowed(
        self, 
        from_type: AgentType, 
        to_type: AgentType,
        task_type: str
    ) -> bool:
        """Check if handoff is allowed."""
        allowed_tasks = self.allowed_handoffs.get((from_type, to_type), [])
        return task_type in allowed_tasks
    
    def validate_handoff(
        self,
        handoff_request: HandoffRequest,
        from_type: AgentType,
        to_type: AgentType
    ) -> Tuple[bool, Optional[str]]:
        """Validate handoff request."""
        # Check if handoff type is allowed
        if not self.is_handoff_allowed(from_type, to_type, handoff_request.task_context.task_type):
            return False, f"Handoff type '{handoff_request.task_context.task_type}' not allowed from {from_type} to {to_type}"
        
        # Run specific validator if exists
        validator = self.handoff_validators.get(handoff_request.task_context.task_type)
        if validator:
            return validator(handoff_request)
        
        return True, None
    
    def _validate_file_operation(self, request: HandoffRequest) -> Tuple[bool, Optional[str]]:
        """Validate file operation handoff."""
        required_fields = ["file_id", "operation"]
        context_state = request.task_context.current_state
        
        for field in required_fields:
            if field not in context_state:
                return False, f"Missing required field: {field}"
        
        return True, None
    
    def _validate_parsing_operation(self, request: HandoffRequest) -> Tuple[bool, Optional[str]]:
        """Validate parsing operation handoff."""
        if "file_data" not in request.task_context.current_state:
            return False, "Missing file_data in context"
        
        return True, None
    
    def _validate_cross_module(self, request: HandoffRequest) -> Tuple[bool, Optional[str]]:
        """Validate cross-module change handoff."""
        required_fields = ["affected_modules", "change_description"]
        context_state = request.task_context.current_state
        
        for field in required_fields:
            if field not in context_state:
                return False, f"Missing required field: {field}"
        
        return True, None
    
    def _validate_data_request(self, request: HandoffRequest) -> Tuple[bool, Optional[str]]:
        """Validate data aggregation request."""
        if "data_requirements" not in request.task_context.current_state:
            return False, "Missing data_requirements in context"
        
        return True, None


class HandoffManager:
    """Manages agent handoff operations."""
    
    def __init__(
        self,
        event_bus: EventBus,
        agent_coordinator: AgentCoordinator
    ):
        self.event_bus = event_bus
        self.agent_coordinator = agent_coordinator
        self.protocol = HandoffProtocol()
        self.active_handoffs: Dict[str, HandoffRequest] = {}
        self.handoff_queue: Dict[str, deque] = {}  # Per-agent queues
        self.handoff_history: deque = deque(maxlen=1000)
        
    async def initiate_handoff(
        self,
        from_agent_id: str,
        to_agent_id: str,
        task_context: TaskContext,
        reason: HandoffReason,
        priority: str = "normal",
        notes: Optional[str] = None
    ) -> str:
        """Initiate a handoff between agents."""
        # Generate handoff ID
        handoff_id = f"HO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{from_agent_id[:8]}"
        
        # Create handoff request
        handoff_request = HandoffRequest(
            handoff_id=handoff_id,
            from_agent=from_agent_id,
            to_agent=to_agent_id,
            task_context=task_context,
            reason=reason,
            priority=priority,
            handoff_notes=notes
        )
        
        # Validate agents exist
        from_agent = self.agent_coordinator.agents.get(from_agent_id)
        to_agent = self.agent_coordinator.agents.get(to_agent_id)
        
        if not from_agent or not to_agent:
            raise ValueError("Invalid agent IDs")
        
        # Validate handoff is allowed
        valid, error_msg = self.protocol.validate_handoff(
            handoff_request,
            from_agent.agent_type,
            to_agent.agent_type
        )
        
        if not valid:
            raise ValueError(f"Invalid handoff: {error_msg}")
        
        # Add to active handoffs
        self.active_handoffs[handoff_id] = handoff_request
        
        # Add to target agent's queue
        if to_agent_id not in self.handoff_queue:
            self.handoff_queue[to_agent_id] = deque()
        self.handoff_queue[to_agent_id].append(handoff_id)
        
        # Add history entry
        task_context.add_history_entry(
            from_agent_id,
            "handoff_initiated",
            {"to_agent": to_agent_id, "reason": reason.value}
        )
        
        # Publish handoff event
        await self.event_bus.publish(
            event_type="HANDOFF_INITIATED",
            data={
                "handoff_id": handoff_id,
                "from_agent": from_agent_id,
                "to_agent": to_agent_id,
                "task_id": task_context.task_id,
                "reason": reason.value,
                "priority": priority
            },
            source_module="core"
        )
        
        logger.info(f"Handoff {handoff_id} initiated from {from_agent_id} to {to_agent_id}")
        return handoff_id
    
    async def accept_handoff(
        self,
        agent_id: str,
        handoff_id: str,
        acceptance_notes: Optional[str] = None
    ) -> bool:
        """Accept a handoff request."""
        handoff = self.active_handoffs.get(handoff_id)
        if not handoff:
            raise ValueError(f"Unknown handoff: {handoff_id}")
        
        if handoff.to_agent != agent_id:
            raise ValueError("Agent not authorized to accept this handoff")
        
        if handoff.status != HandoffStatus.INITIATED:
            raise ValueError(f"Handoff in invalid state: {handoff.status}")
        
        # Update status
        handoff.status = HandoffStatus.ACCEPTED
        handoff.accepted_at = datetime.utcnow()
        
        if acceptance_notes:
            handoff.handoff_notes = (handoff.handoff_notes or "") + f"\nAcceptance: {acceptance_notes}"
        
        # Add history entry
        handoff.task_context.add_history_entry(
            agent_id,
            "handoff_accepted",
            {"notes": acceptance_notes}
        )
        
        # Publish acceptance event
        await self.event_bus.publish(
            event_type="HANDOFF_ACCEPTED",
            data={
                "handoff_id": handoff_id,
                "accepting_agent": agent_id,
                "task_context": handoff.task_context.__dict__
            },
            source_module="core"
        )
        
        logger.info(f"Handoff {handoff_id} accepted by {agent_id}")
        return True
    
    async def reject_handoff(
        self,
        agent_id: str,
        handoff_id: str,
        reason: str
    ) -> bool:
        """Reject a handoff request."""
        handoff = self.active_handoffs.get(handoff_id)
        if not handoff:
            raise ValueError(f"Unknown handoff: {handoff_id}")
        
        if handoff.to_agent != agent_id:
            raise ValueError("Agent not authorized to reject this handoff")
        
        if handoff.status != HandoffStatus.INITIATED:
            raise ValueError(f"Handoff in invalid state: {handoff.status}")
        
        # Update status
        handoff.status = HandoffStatus.REJECTED
        handoff.rejection_reason = reason
        
        # Remove from queue
        if agent_id in self.handoff_queue:
            self.handoff_queue[agent_id].remove(handoff_id)
        
        # Add history entry
        handoff.task_context.add_history_entry(
            agent_id,
            "handoff_rejected",
            {"reason": reason}
        )
        
        # Publish rejection event
        await self.event_bus.publish(
            event_type="HANDOFF_REJECTED",
            data={
                "handoff_id": handoff_id,
                "rejecting_agent": agent_id,
                "from_agent": handoff.from_agent,
                "reason": reason
            },
            source_module="core"
        )
        
        logger.info(f"Handoff {handoff_id} rejected by {agent_id}")
        return True
    
    async def complete_handoff(
        self,
        agent_id: str,
        handoff_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """Mark handoff as completed."""
        handoff = self.active_handoffs.get(handoff_id)
        if not handoff:
            raise ValueError(f"Unknown handoff: {handoff_id}")
        
        if handoff.to_agent != agent_id:
            raise ValueError("Agent not authorized to complete this handoff")
        
        if handoff.status not in [HandoffStatus.ACCEPTED, HandoffStatus.IN_PROGRESS]:
            raise ValueError(f"Handoff in invalid state: {handoff.status}")
        
        # Update status
        handoff.status = HandoffStatus.COMPLETED
        handoff.completed_at = datetime.utcnow()
        
        # Update task context with result
        handoff.task_context.current_state.update(result)
        handoff.task_context.add_history_entry(
            agent_id,
            "handoff_completed",
            {"result_summary": result.get("summary", "Task completed")}
        )
        
        # Move to history
        self.handoff_history.append(handoff)
        del self.active_handoffs[handoff_id]
        
        # Remove from queue
        if agent_id in self.handoff_queue and handoff_id in self.handoff_queue[agent_id]:
            self.handoff_queue[agent_id].remove(handoff_id)
        
        # Publish completion event
        await self.event_bus.publish(
            event_type="HANDOFF_COMPLETED",
            data={
                "handoff_id": handoff_id,
                "from_agent": handoff.from_agent,
                "to_agent": agent_id,
                "task_id": handoff.task_context.task_id,
                "result": result
            },
            source_module="core"
        )
        
        logger.info(f"Handoff {handoff_id} completed by {agent_id}")
        return True
    
    async def get_pending_handoffs(self, agent_id: str) -> List[HandoffRequest]:
        """Get pending handoffs for an agent."""
        if agent_id not in self.handoff_queue:
            return []
        
        pending = []
        for handoff_id in self.handoff_queue[agent_id]:
            handoff = self.active_handoffs.get(handoff_id)
            if handoff and handoff.status == HandoffStatus.INITIATED:
                pending.append(handoff)
        
        # Sort by priority and creation time
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        pending.sort(
            key=lambda h: (priority_order.get(h.priority, 2), h.created_at)
        )
        
        return pending
    
    async def update_handoff_progress(
        self,
        agent_id: str,
        handoff_id: str,
        progress_update: Dict[str, Any]
    ):
        """Update progress on a handoff."""
        handoff = self.active_handoffs.get(handoff_id)
        if not handoff:
            raise ValueError(f"Unknown handoff: {handoff_id}")
        
        if handoff.to_agent != agent_id:
            raise ValueError("Agent not authorized to update this handoff")
        
        # Update status if needed
        if handoff.status == HandoffStatus.ACCEPTED:
            handoff.status = HandoffStatus.IN_PROGRESS
        
        # Add progress update to context
        handoff.task_context.add_history_entry(
            agent_id,
            "progress_update",
            progress_update
        )
        
        # Publish progress event
        await self.event_bus.publish(
            event_type="HANDOFF_PROGRESS",
            data={
                "handoff_id": handoff_id,
                "agent_id": agent_id,
                "progress": progress_update
            },
            source_module="core"
        )
    
    async def escalate_handoff(
        self,
        handoff_id: str,
        escalation_reason: str
    ):
        """Escalate a stuck or failed handoff."""
        handoff = self.active_handoffs.get(handoff_id)
        if not handoff:
            raise ValueError(f"Unknown handoff: {handoff_id}")
        
        # Mark as failed
        handoff.status = HandoffStatus.FAILED
        
        # Publish escalation event for integration agent
        await self.event_bus.publish(
            event_type="HANDOFF_ESCALATION",
            data={
                "handoff_id": handoff_id,
                "original_handoff": handoff.__dict__,
                "escalation_reason": escalation_reason,
                "requires_integration_agent": True
            },
            source_module="core"
        )
        
        logger.warning(f"Handoff {handoff_id} escalated: {escalation_reason}")
    
    async def get_handoff_metrics(self) -> Dict:
        """Get handoff system metrics."""
        total_active = len(self.active_handoffs)
        by_status = {}
        by_reason = {}
        avg_completion_time = []
        
        # Analyze active handoffs
        for handoff in self.active_handoffs.values():
            by_status[handoff.status.value] = by_status.get(handoff.status.value, 0) + 1
            by_reason[handoff.reason.value] = by_reason.get(handoff.reason.value, 0) + 1
        
        # Analyze historical handoffs
        for handoff in self.handoff_history:
            if handoff.completed_at and handoff.accepted_at:
                completion_time = (handoff.completed_at - handoff.accepted_at).total_seconds()
                avg_completion_time.append(completion_time)
        
        return {
            "total_active": total_active,
            "by_status": by_status,
            "by_reason": by_reason,
            "total_completed": len(self.handoff_history),
            "avg_completion_seconds": sum(avg_completion_time) / len(avg_completion_time) if avg_completion_time else 0,
            "queue_depths": {
                agent_id: len(queue) 
                for agent_id, queue in self.handoff_queue.items()
            }
        }