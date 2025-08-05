"""
Agent Dashboard API Routes
Provides endpoints for monitoring and managing agents
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from ..agent_coordinator import AgentCoordinator, AgentType, PermissionLevel
from ..agent_handoff_system import HandoffManager, HandoffReason
from ..agent_performance_tracker import PerformanceTracker, MetricType

router = APIRouter(prefix="/api/agents", tags=["agent-dashboard"])


# Pydantic models for API
class AgentRegistration(BaseModel):
    agent_id: str
    agent_type: AgentType
    custom_permissions: Optional[Dict[str, List[str]]] = None


class HandoffRequest(BaseModel):
    from_agent_id: str
    to_agent_id: str
    task_id: str
    task_type: str
    description: str
    context: Dict
    reason: HandoffReason
    priority: str = "normal"
    notes: Optional[str] = None


class HandoffAction(BaseModel):
    action: str  # accept, reject, complete
    handoff_id: str
    agent_id: str
    notes: Optional[str] = None
    result: Optional[Dict] = None


class PerformanceMetric(BaseModel):
    agent_id: str
    metric_type: MetricType
    value: float
    metadata: Optional[Dict] = None


class ChangeRequestSubmission(BaseModel):
    requesting_agent_id: str
    affected_modules: List[str]
    change_type: str
    description: str
    changes: Dict


# Dependencies
async def get_coordinator() -> AgentCoordinator:
    """Get agent coordinator instance."""
    # In production, this would be injected
    from ..dependencies import get_agent_coordinator
    return get_agent_coordinator()


async def get_handoff_manager() -> HandoffManager:
    """Get handoff manager instance."""
    from ..dependencies import get_handoff_manager
    return get_handoff_manager()


async def get_performance_tracker() -> PerformanceTracker:
    """Get performance tracker instance."""
    from ..dependencies import get_performance_tracker
    return get_performance_tracker()


# Agent Management Endpoints
@router.post("/register")
async def register_agent(
    registration: AgentRegistration,
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Register a new agent in the system."""
    try:
        # Convert permissions if provided
        permissions = None
        if registration.custom_permissions:
            permissions = {
                path: {PermissionLevel(perm) for perm in perms}
                for path, perms in registration.custom_permissions.items()
            }
        
        agent = await coordinator.register_agent(
            agent_id=registration.agent_id,
            agent_type=registration.agent_type,
            custom_permissions=permissions
        )
        
        return {
            "status": "success",
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type.value,
            "module_scope": agent.module_scope,
            "registered_at": agent.registered_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list")
async def list_agents(
    active_only: bool = Query(False, description="Only show active agents"),
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """List all registered agents."""
    agents = []
    
    for agent_id, agent in coordinator.agents.items():
        # Filter by active status
        if active_only:
            if (datetime.utcnow() - agent.last_active).total_seconds() > 300:
                continue
        
        # Filter by type
        if agent_type and agent.agent_type != agent_type:
            continue
        
        agents.append({
            "agent_id": agent_id,
            "agent_type": agent.agent_type.value,
            "module_scope": agent.module_scope,
            "registered_at": agent.registered_at.isoformat(),
            "last_active": agent.last_active.isoformat(),
            "active_tasks": len(agent.active_tasks),
            "performance_metrics": agent.performance_metrics
        })
    
    return {
        "total": len(agents),
        "agents": agents
    }


@router.get("/{agent_id}")
async def get_agent_details(
    agent_id: str,
    coordinator: AgentCoordinator = Depends(get_coordinator),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker)
):
    """Get detailed information about a specific agent."""
    agent = coordinator.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get performance snapshot
    performance = await performance_tracker.get_performance_snapshot(agent_id)
    
    # Get current alerts
    alerts = await performance_tracker.check_alerts(agent_id)
    
    return {
        "agent_id": agent_id,
        "agent_type": agent.agent_type.value,
        "module_scope": agent.module_scope,
        "permissions": {
            path: [perm.value for perm in perms]
            for path, perms in agent.permissions.items()
        },
        "registered_at": agent.registered_at.isoformat(),
        "last_active": agent.last_active.isoformat(),
        "active_tasks": agent.active_tasks,
        "performance": {
            "health_score": performance.health_score,
            "metrics": {k.value: v for k, v in performance.metrics.items()},
            "error_count": performance.error_count,
            "success_count": performance.success_count,
            "avg_response_time": performance.avg_response_time
        },
        "alerts": alerts
    }


# Handoff Management Endpoints
@router.post("/handoff/initiate")
async def initiate_handoff(
    request: HandoffRequest,
    handoff_manager: HandoffManager = Depends(get_handoff_manager)
):
    """Initiate a handoff between agents."""
    try:
        from ..agent_handoff_system import TaskContext
        
        task_context = TaskContext(
            task_id=request.task_id,
            task_type=request.task_type,
            description=request.description,
            current_state=request.context
        )
        
        handoff_id = await handoff_manager.initiate_handoff(
            from_agent_id=request.from_agent_id,
            to_agent_id=request.to_agent_id,
            task_context=task_context,
            reason=request.reason,
            priority=request.priority,
            notes=request.notes
        )
        
        return {
            "status": "success",
            "handoff_id": handoff_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/handoff/action")
async def handle_handoff_action(
    action: HandoffAction,
    handoff_manager: HandoffManager = Depends(get_handoff_manager)
):
    """Handle handoff actions (accept, reject, complete)."""
    try:
        if action.action == "accept":
            await handoff_manager.accept_handoff(
                action.agent_id,
                action.handoff_id,
                action.notes
            )
        elif action.action == "reject":
            await handoff_manager.reject_handoff(
                action.agent_id,
                action.handoff_id,
                action.notes or "No reason provided"
            )
        elif action.action == "complete":
            if not action.result:
                raise ValueError("Result required for completion")
            await handoff_manager.complete_handoff(
                action.agent_id,
                action.handoff_id,
                action.result
            )
        else:
            raise ValueError(f"Unknown action: {action.action}")
        
        return {"status": "success", "action": action.action}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/handoff/pending/{agent_id}")
async def get_pending_handoffs(
    agent_id: str,
    handoff_manager: HandoffManager = Depends(get_handoff_manager)
):
    """Get pending handoffs for an agent."""
    pending = await handoff_manager.get_pending_handoffs(agent_id)
    
    return {
        "agent_id": agent_id,
        "pending_count": len(pending),
        "handoffs": [
            {
                "handoff_id": h.handoff_id,
                "from_agent": h.from_agent,
                "task_id": h.task_context.task_id,
                "task_type": h.task_context.task_type,
                "description": h.task_context.description,
                "reason": h.reason.value,
                "priority": h.priority,
                "created_at": h.created_at.isoformat()
            }
            for h in pending
        ]
    }


@router.get("/handoff/metrics")
async def get_handoff_metrics(
    handoff_manager: HandoffManager = Depends(get_handoff_manager)
):
    """Get handoff system metrics."""
    metrics = await handoff_manager.get_handoff_metrics()
    return metrics


# Performance Monitoring Endpoints
@router.post("/performance/metric")
async def record_performance_metric(
    metric: PerformanceMetric,
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker)
):
    """Record a performance metric for an agent."""
    await performance_tracker.record_metric(
        agent_id=metric.agent_id,
        metric_type=metric.metric_type,
        value=metric.value,
        metadata=metric.metadata
    )
    
    return {"status": "success"}


@router.get("/performance/{agent_id}")
async def get_agent_performance(
    agent_id: str,
    time_window_hours: int = Query(24, description="Time window in hours"),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker)
):
    """Get performance data for an agent."""
    report = await performance_tracker.generate_performance_report(agent_id)
    
    # Get trends for specified time window
    time_window = timedelta(hours=time_window_hours)
    trends = {}
    
    for metric_type in MetricType:
        trend_data = await performance_tracker.get_performance_trends(
            agent_id, metric_type, time_window
        )
        trends[metric_type.value] = trend_data
    
    report["trends"] = trends
    return report


@router.get("/performance/compare")
async def compare_agent_performance(
    agent_ids: List[str] = Query(..., description="Agent IDs to compare"),
    metric_type: MetricType = Query(..., description="Metric to compare"),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker)
):
    """Compare performance across multiple agents."""
    if len(agent_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 agents required for comparison")
    
    comparison = await performance_tracker.compare_agents(agent_ids, metric_type)
    
    return {
        "metric_type": metric_type.value,
        "timestamp": datetime.utcnow().isoformat(),
        "comparison": comparison
    }


# Change Request Endpoints
@router.post("/change-request")
async def submit_change_request(
    request: ChangeRequestSubmission,
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Submit a cross-module change request."""
    try:
        request_id = await coordinator.request_cross_module_change(
            requesting_agent_id=request.requesting_agent_id,
            affected_modules=request.affected_modules,
            change_type=request.change_type,
            description=request.description,
            changes=request.changes
        )
        
        return {
            "status": "success",
            "request_id": request_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/change-request/{request_id}")
async def get_change_request(
    request_id: str,
    coordinator: AgentCoordinator = Depends(get_coordinator)
):
    """Get details of a change request."""
    change_request = coordinator.change_requests.get(request_id)
    if not change_request:
        raise HTTPException(status_code=404, detail="Change request not found")
    
    return {
        "request_id": request_id,
        "requesting_agent": change_request.requesting_agent,
        "affected_modules": change_request.affected_modules,
        "change_type": change_request.change_type,
        "description": change_request.description,
        "changes": change_request.changes,
        "status": change_request.status.value,
        "created_at": change_request.created_at.isoformat(),
        "reviewed_by": change_request.reviewed_by,
        "reviewed_at": change_request.reviewed_at.isoformat() if change_request.reviewed_at else None
    }


# System Overview Endpoints
@router.get("/dashboard/overview")
async def get_dashboard_overview(
    coordinator: AgentCoordinator = Depends(get_coordinator),
    handoff_manager: HandoffManager = Depends(get_handoff_manager),
    performance_tracker: PerformanceTracker = Depends(get_performance_tracker)
):
    """Get comprehensive dashboard overview."""
    # Get active agents
    active_agents = await coordinator.get_active_agents()
    
    # Get handoff metrics
    handoff_metrics = await handoff_manager.get_handoff_metrics()
    
    # Get overall system health
    system_health = {
        "total_agents": len(coordinator.agents),
        "active_agents": len(active_agents),
        "total_handoffs": handoff_metrics["total_active"],
        "pending_changes": len([
            cr for cr in coordinator.change_requests.values()
            if cr.status.value == "pending"
        ])
    }
    
    # Get alerts across all agents
    all_alerts = []
    for agent_id in coordinator.agents:
        alerts = await performance_tracker.check_alerts(agent_id)
        for alert in alerts:
            alert["agent_id"] = agent_id
            all_alerts.append(alert)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system_health": system_health,
        "active_agents": active_agents,
        "handoff_metrics": handoff_metrics,
        "critical_alerts": [a for a in all_alerts if a["level"] == "critical"],
        "warning_alerts": [a for a in all_alerts if a["level"] == "warning"]
    }


@router.get("/dashboard/activity-timeline")
async def get_activity_timeline(
    hours: int = Query(1, description="Hours to look back"),
    coordinator: AgentCoordinator = Depends(get_coordinator),
    handoff_manager: HandoffManager = Depends(get_handoff_manager)
):
    """Get activity timeline for the dashboard."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    timeline = []
    
    # Add handoff events
    for handoff in handoff_manager.handoff_history:
        if handoff.created_at > cutoff:
            timeline.append({
                "timestamp": handoff.created_at.isoformat(),
                "type": "handoff",
                "description": f"Handoff from {handoff.from_agent} to {handoff.to_agent}",
                "status": handoff.status.value
            })
    
    # Add change requests
    for cr in coordinator.change_requests.values():
        if cr.created_at > cutoff:
            timeline.append({
                "timestamp": cr.created_at.isoformat(),
                "type": "change_request",
                "description": f"Change request from {cr.requesting_agent}",
                "status": cr.status.value
            })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "hours": hours,
        "event_count": len(timeline),
        "timeline": timeline[:100]  # Limit to 100 most recent
    }