"""
Multi-Agent Testing Framework
Tests agent interactions, handoffs, and coordination
"""

import asyncio
import pytest
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import json

from modules.core.agent_coordinator import (
    AgentCoordinator, AgentType, PermissionLevel, ChangeRequestStatus
)
from modules.core.agent_handoff_system import (
    HandoffManager, HandoffReason, HandoffStatus, TaskContext
)
from modules.core.agent_performance_tracker import (
    PerformanceTracker, MetricType
)
from modules.core.event_bus import EventBus, Event
from modules.core.api_gateway import APIGateway


class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.received_events = []
        self.handoff_responses = {}
        self.task_results = {}
        
    async def handle_event(self, event: Event):
        """Handle incoming event."""
        self.received_events.append(event)
        
    async def process_handoff(self, handoff_id: str) -> Dict:
        """Process a handoff request."""
        if handoff_id in self.handoff_responses:
            return self.handoff_responses[handoff_id]
        return {"status": "completed", "result": "success"}
    
    async def execute_task(self, task_id: str, context: Dict) -> Dict:
        """Execute a task."""
        if task_id in self.task_results:
            return self.task_results[task_id]
        return {"status": "success", "output": "task completed"}


class MultiAgentTestFramework:
    """Framework for testing multi-agent scenarios."""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.api_gateway = APIGateway()
        self.coordinator = AgentCoordinator(self.event_bus, self.api_gateway)
        self.handoff_manager = HandoffManager(self.event_bus, self.coordinator)
        self.performance_tracker = PerformanceTracker()
        self.mock_agents: Dict[str, MockAgent] = {}
        
    async def setup_test_environment(self):
        """Setup test environment with mock agents."""
        # Register mock agents
        agent_configs = [
            ("auth_test", AgentType.AUTH),
            ("content_test", AgentType.CONTENT),
            ("drive_test", AgentType.DRIVE),
            ("sync_test", AgentType.SYNC),
            ("dashboard_test", AgentType.DASHBOARD),
            ("integration_test", AgentType.INTEGRATION),
        ]
        
        for agent_id, agent_type in agent_configs:
            await self.coordinator.register_agent(agent_id, agent_type)
            self.mock_agents[agent_id] = MockAgent(agent_id, agent_type)
            
            # Subscribe to events
            await self.event_bus.subscribe(
                f"{agent_type.value.upper()}_*",
                self.mock_agents[agent_id].handle_event
            )
    
    async def simulate_file_upload_workflow(self) -> Dict:
        """Simulate complete file upload and processing workflow."""
        results = {
            "events_published": [],
            "handoffs": [],
            "errors": [],
            "metrics": {}
        }
        
        try:
            # Step 1: Drive agent detects new file
            file_event = Event(
                event_type="DRIVE_FILE_ADDED",
                data={
                    "file_id": "test_file_123",
                    "filename": "All of Me_Bb.pdf",
                    "size": 1024000,
                    "mimetype": "application/pdf"
                },
                source_module="drive"
            )
            await self.event_bus.publish_event(file_event)
            results["events_published"].append("DRIVE_FILE_ADDED")
            
            # Step 2: Content agent requests file parsing
            task_context = TaskContext(
                task_id="PARSE_001",
                task_type="file_parsing",
                description="Parse new chart file",
                current_state={
                    "file_id": "test_file_123",
                    "file_data": {"name": "All of Me_Bb.pdf"}
                }
            )
            
            handoff_id = await self.handoff_manager.initiate_handoff(
                from_agent_id="drive_test",
                to_agent_id="content_test",
                task_context=task_context,
                reason=HandoffReason.EXPERTISE_REQUIRED
            )
            results["handoffs"].append(handoff_id)
            
            # Step 3: Content agent accepts and processes
            await self.handoff_manager.accept_handoff("content_test", handoff_id)
            
            # Simulate processing
            await asyncio.sleep(0.1)
            
            await self.handoff_manager.complete_handoff(
                "content_test",
                handoff_id,
                {
                    "parsed": True,
                    "metadata": {
                        "title": "All of Me",
                        "key": "Bb",
                        "type": "chart"
                    }
                }
            )
            
            # Step 4: Publish content updated event
            content_event = Event(
                event_type="CONTENT_UPDATED",
                data={
                    "file_id": "test_file_123",
                    "metadata": {
                        "title": "All of Me",
                        "key": "Bb"
                    }
                },
                source_module="content"
            )
            await self.event_bus.publish_event(content_event)
            results["events_published"].append("CONTENT_UPDATED")
            
            # Step 5: Sync broadcasts to users
            sync_event = Event(
                event_type="SYNC_FILE_UPDATED",
                data={
                    "file_id": "test_file_123",
                    "broadcast_to": ["user1", "user2"]
                },
                source_module="sync"
            )
            await self.event_bus.publish_event(sync_event)
            results["events_published"].append("SYNC_FILE_UPDATED")
            
            # Collect metrics
            results["metrics"] = await self.handoff_manager.get_handoff_metrics()
            
        except Exception as e:
            results["errors"].append(str(e))
            
        return results
    
    async def test_cross_module_change_request(self) -> Dict:
        """Test cross-module change request workflow."""
        results = {
            "change_request_id": None,
            "approval_status": None,
            "errors": []
        }
        
        try:
            # Content agent requests API change
            change_request_id = await self.coordinator.request_cross_module_change(
                requesting_agent_id="content_test",
                affected_modules=["drive", "sync"],
                change_type="api_enhancement",
                description="Add duration field to file metadata",
                changes={
                    "new_fields": ["duration", "bitrate"],
                    "affected_endpoints": ["/api/files/{id}"],
                    "backward_compatible": True
                }
            )
            results["change_request_id"] = change_request_id
            
            # Integration agent reviews and approves
            await self.coordinator.approve_change_request(
                change_request_id,
                "integration_test",
                notes="Change approved - backward compatible"
            )
            
            # Check status
            change_request = self.coordinator.change_requests[change_request_id]
            results["approval_status"] = change_request.status.value
            
        except Exception as e:
            results["errors"].append(str(e))
            
        return results
    
    async def test_agent_performance_tracking(self) -> Dict:
        """Test agent performance tracking."""
        results = {
            "metrics_recorded": 0,
            "health_scores": {},
            "alerts": {},
            "errors": []
        }
        
        try:
            # Simulate various agent activities
            agents = ["content_test", "drive_test", "sync_test"]
            
            for agent_id in agents:
                # Record task completions
                for i in range(10):
                    success = i % 5 != 0  # 20% failure rate
                    await self.performance_tracker.record_task_completion(
                        agent_id=agent_id,
                        task_id=f"TASK_{i}",
                        duration_seconds=5.0 + i * 0.5,
                        success=success
                    )
                    results["metrics_recorded"] += 1
                
                # Record response times
                for i in range(20):
                    await self.performance_tracker.record_response_time(
                        agent_id=agent_id,
                        operation=f"op_{i % 3}",
                        response_time_ms=100 + i * 10
                    )
                    results["metrics_recorded"] += 1
                
                # Get health score
                health_score = await self.performance_tracker.calculate_health_score(agent_id)
                results["health_scores"][agent_id] = health_score
                
                # Check alerts
                alerts = await self.performance_tracker.check_alerts(agent_id)
                if alerts:
                    results["alerts"][agent_id] = alerts
                    
        except Exception as e:
            results["errors"].append(str(e))
            
        return results
    
    async def test_agent_failover(self) -> Dict:
        """Test agent failover scenario."""
        results = {
            "failover_triggered": False,
            "backup_agent": None,
            "recovery_time": None,
            "errors": []
        }
        
        try:
            # Simulate agent failure
            failed_agent = "content_test"
            start_time = datetime.utcnow()
            
            # Mark agent as unavailable
            self.coordinator.agents[failed_agent].last_active = datetime.utcnow() - timedelta(minutes=10)
            
            # Create urgent task
            task_context = TaskContext(
                task_id="URGENT_001",
                task_type="file_parsing",
                description="Urgent file parsing needed",
                current_state={"file_id": "urgent_file"}
            )
            
            # Try handoff to failed agent
            try:
                await self.handoff_manager.initiate_handoff(
                    from_agent_id="drive_test",
                    to_agent_id=failed_agent,
                    task_context=task_context,
                    reason=HandoffReason.EXPERTISE_REQUIRED,
                    priority="critical"
                )
            except Exception:
                # Failover to integration agent
                results["failover_triggered"] = True
                results["backup_agent"] = "integration_test"
                
                handoff_id = await self.handoff_manager.initiate_handoff(
                    from_agent_id="drive_test",
                    to_agent_id="integration_test",
                    task_context=task_context,
                    reason=HandoffReason.AGENT_UNAVAILABLE,
                    priority="critical"
                )
                
                await self.handoff_manager.accept_handoff("integration_test", handoff_id)
                await self.handoff_manager.complete_handoff(
                    "integration_test",
                    handoff_id,
                    {"status": "completed_by_backup"}
                )
                
                results["recovery_time"] = (datetime.utcnow() - start_time).total_seconds()
                
        except Exception as e:
            results["errors"].append(str(e))
            
        return results
    
    async def test_concurrent_handoffs(self) -> Dict:
        """Test multiple concurrent handoffs."""
        results = {
            "total_handoffs": 0,
            "successful": 0,
            "failed": 0,
            "avg_completion_time": 0,
            "errors": []
        }
        
        try:
            handoff_tasks = []
            handoff_ids = []
            
            # Create multiple handoffs
            for i in range(10):
                from_agent = f"{'drive' if i % 2 == 0 else 'content'}_test"
                to_agent = f"{'content' if i % 2 == 0 else 'sync'}_test"
                
                task_context = TaskContext(
                    task_id=f"CONCURRENT_{i}",
                    task_type="data_processing",
                    description=f"Concurrent task {i}",
                    current_state={"task_num": i}
                )
                
                handoff_id = await self.handoff_manager.initiate_handoff(
                    from_agent_id=from_agent,
                    to_agent_id=to_agent,
                    task_context=task_context,
                    reason=HandoffReason.WORKLOAD_BALANCE
                )
                handoff_ids.append(handoff_id)
                results["total_handoffs"] += 1
            
            # Process handoffs concurrently
            async def process_handoff(handoff_id: str, agent_id: str):
                try:
                    await self.handoff_manager.accept_handoff(agent_id, handoff_id)
                    await asyncio.sleep(0.1)  # Simulate processing
                    await self.handoff_manager.complete_handoff(
                        agent_id,
                        handoff_id,
                        {"processed": True}
                    )
                    return True
                except Exception:
                    return False
            
            # Execute concurrently
            tasks = []
            for i, handoff_id in enumerate(handoff_ids):
                to_agent = f"{'content' if i % 2 == 0 else 'sync'}_test"
                tasks.append(process_handoff(handoff_id, to_agent))
            
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count results
            for result in results_list:
                if isinstance(result, bool) and result:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
            
            # Get metrics
            metrics = await self.handoff_manager.get_handoff_metrics()
            results["avg_completion_time"] = metrics["avg_completion_seconds"]
            
        except Exception as e:
            results["errors"].append(str(e))
            
        return results


@pytest.fixture
async def test_framework():
    """Create test framework instance."""
    framework = MultiAgentTestFramework()
    await framework.setup_test_environment()
    return framework


@pytest.mark.asyncio
async def test_file_upload_workflow(test_framework):
    """Test complete file upload workflow."""
    results = await test_framework.simulate_file_upload_workflow()
    
    assert len(results["errors"]) == 0
    assert "DRIVE_FILE_ADDED" in results["events_published"]
    assert "CONTENT_UPDATED" in results["events_published"]
    assert "SYNC_FILE_UPDATED" in results["events_published"]
    assert len(results["handoffs"]) > 0
    assert results["metrics"]["total_completed"] > 0


@pytest.mark.asyncio
async def test_cross_module_changes(test_framework):
    """Test cross-module change requests."""
    results = await test_framework.test_cross_module_change_request()
    
    assert len(results["errors"]) == 0
    assert results["change_request_id"] is not None
    assert results["approval_status"] == "approved"


@pytest.mark.asyncio
async def test_performance_monitoring(test_framework):
    """Test agent performance tracking."""
    results = await test_framework.test_agent_performance_tracking()
    
    assert len(results["errors"]) == 0
    assert results["metrics_recorded"] > 0
    assert all(score > 0 for score in results["health_scores"].values())
    
    # Check for expected alerts (20% error rate should trigger)
    assert len(results["alerts"]) > 0


@pytest.mark.asyncio
async def test_failover_scenario(test_framework):
    """Test agent failover handling."""
    results = await test_framework.test_agent_failover()
    
    assert len(results["errors"]) == 0
    assert results["failover_triggered"] is True
    assert results["backup_agent"] == "integration_test"
    assert results["recovery_time"] is not None


@pytest.mark.asyncio
async def test_concurrent_operations(test_framework):
    """Test concurrent handoff operations."""
    results = await test_framework.test_concurrent_handoffs()
    
    assert len(results["errors"]) == 0
    assert results["total_handoffs"] == 10
    assert results["successful"] > 0
    assert results["avg_completion_time"] > 0


class AgentSimulator:
    """Simulates realistic agent behavior for testing."""
    
    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.processing_delay = {
            AgentType.CONTENT: 0.2,
            AgentType.DRIVE: 0.1,
            AgentType.SYNC: 0.05,
            AgentType.DASHBOARD: 0.15,
            AgentType.AUTH: 0.1,
            AgentType.INTEGRATION: 0.3
        }
        
    async def process_task(self, task_context: TaskContext) -> Dict:
        """Simulate task processing."""
        delay = self.processing_delay.get(self.agent_type, 0.1)
        await asyncio.sleep(delay)
        
        # Simulate occasional errors
        if task_context.task_id.endswith("_fail"):
            raise Exception("Simulated task failure")
        
        return {
            "status": "success",
            "processed_by": self.agent_id,
            "processing_time": delay,
            "output": f"Processed {task_context.task_type}"
        }


def create_test_scenarios():
    """Create various test scenarios for multi-agent testing."""
    return {
        "scenarios": [
            {
                "name": "High Load Test",
                "description": "Test system under high load",
                "tasks": 100,
                "agents": 6,
                "error_rate": 0.1
            },
            {
                "name": "Cascade Failure",
                "description": "Test cascading agent failures",
                "failing_agents": ["content", "drive"],
                "recovery_expected": True
            },
            {
                "name": "Priority Queue Test",
                "description": "Test priority-based task handling",
                "task_priorities": ["critical", "high", "normal", "low"],
                "expected_order": ["critical", "high", "normal", "low"]
            },
            {
                "name": "Cross-Module Integration",
                "description": "Test complex cross-module workflows",
                "modules_involved": ["auth", "content", "drive", "sync", "dashboard"],
                "expected_events": 15
            }
        ]
    }


if __name__ == "__main__":
    # Run tests
    asyncio.run(pytest.main([__file__, "-v"]))