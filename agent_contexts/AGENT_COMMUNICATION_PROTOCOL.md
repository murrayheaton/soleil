# SOLEil Agent Communication Protocol

## Overview
This document defines the communication standards and protocols for agent interactions within the SOLEil Band Platform. All agents must follow these protocols to ensure smooth coordination and system integrity.

## Communication Channels

### 1. Event-Based Communication (Primary)
All agents communicate primarily through the EventBus system.

```python
# Publishing an event
await event_bus.publish(
    event_type="CONTENT_UPDATED",
    data={
        "file_id": "abc123",
        "changes": {...}
    },
    source_module="content"
)

# Subscribing to events
@event_bus.subscribe("DRIVE_FILE_CHANGED")
async def handle_file_change(event: Event):
    # Process the event
    pass
```

### 2. Service Discovery (Synchronous)
For direct service calls when needed.

```python
# Getting a service from another module
gateway = get_api_gateway()
auth_service = gateway.get_module_service('auth', 'user_service')
user_data = await auth_service.get_user(user_id)
```

### 3. Cross-Module Change Requests
For changes that affect multiple modules.

```python
# Submitting a change request
coordinator = get_agent_coordinator()
request_id = await coordinator.request_cross_module_change(
    requesting_agent_id="content_agent_001",
    affected_modules=["drive", "sync"],
    change_type="api_update",
    description="Add new file metadata fields",
    changes={
        "new_fields": ["duration", "bitrate"],
        "migration_required": True
    }
)
```

## Message Formats

### Event Message Structure
```json
{
    "event_id": "uuid",
    "event_type": "MODULE_EVENT_NAME",
    "source_module": "module_name",
    "timestamp": "2025-01-23T10:00:00Z",
    "data": {
        // Event-specific data
    },
    "metadata": {
        "agent_id": "agent_identifier",
        "correlation_id": "uuid",
        "priority": "high|normal|low"
    }
}
```

### Service Call Structure
```json
{
    "request_id": "uuid",
    "service": "service_name",
    "method": "method_name",
    "params": {
        // Method parameters
    },
    "timeout": 30000,
    "retry_policy": {
        "max_attempts": 3,
        "backoff": "exponential"
    }
}
```

### Change Request Structure
```json
{
    "request_id": "CR-20250123100000-content",
    "requesting_agent": "content_agent_001",
    "affected_modules": ["drive", "sync"],
    "change_type": "api_update|schema_change|integration_update",
    "description": "Human-readable description",
    "changes": {
        // Specific changes proposed
    },
    "impact_analysis": {
        "breaking_changes": false,
        "migration_required": false,
        "estimated_effort": "small|medium|large"
    },
    "testing_plan": {
        "unit_tests": ["test_1", "test_2"],
        "integration_tests": ["test_3"]
    }
}
```

## Communication Patterns

### 1. Request-Response Pattern
For synchronous operations requiring immediate response.

```python
# Agent A requests data from Agent B
async def get_user_files(user_id: int):
    try:
        drive_service = gateway.get_module_service('drive', 'file_service')
        files = await drive_service.list_user_files(user_id)
        return files
    except ServiceUnavailable:
        # Handle gracefully
        return []
```

### 2. Publish-Subscribe Pattern
For asynchronous notifications and updates.

```python
# Publisher (Drive Agent)
async def on_file_uploaded(file_data):
    await event_bus.publish(
        event_type="DRIVE_FILE_ADDED",
        data=file_data,
        source_module="drive"
    )

# Subscriber (Content Agent)
@event_bus.subscribe("DRIVE_FILE_ADDED")
async def process_new_file(event: Event):
    await parse_file_content(event.data)
```

### 3. Orchestration Pattern
For complex workflows involving multiple agents.

```python
# Integration Agent orchestrating a workflow
async def orchestrate_file_sync(file_id: str):
    # Step 1: Get file from Drive
    await event_bus.publish("REQUEST_FILE_DATA", {"file_id": file_id})
    
    # Step 2: Wait for file data
    file_data = await wait_for_event("FILE_DATA_READY", timeout=30)
    
    # Step 3: Parse content
    await event_bus.publish("PARSE_FILE_CONTENT", {"file_data": file_data})
    
    # Step 4: Sync to users
    await event_bus.publish("SYNC_FILE_TO_USERS", {"file_id": file_id})
```

## Protocol Rules

### 1. Event Naming Convention
- Format: `MODULE_ACTION_OBJECT`
- Examples:
  - `AUTH_USER_LOGGED_IN`
  - `DRIVE_FILE_UPDATED`
  - `CONTENT_CHART_PARSED`

### 2. Timeout Policies
- Service calls: 30 seconds default
- Event processing: 5 seconds
- File operations: 2 minutes
- Batch operations: 5 minutes

### 3. Retry Strategies
```python
RETRY_POLICIES = {
    "transient_error": {
        "max_attempts": 3,
        "delays": [1, 2, 4],  # seconds
        "jitter": True
    },
    "rate_limit": {
        "max_attempts": 5,
        "delays": [5, 10, 30, 60, 120],
        "respect_retry_after": True
    },
    "service_unavailable": {
        "max_attempts": 3,
        "delays": [10, 30, 60],
        "circuit_breaker": True
    }
}
```

### 4. Error Handling
```python
class AgentCommunicationError(Exception):
    """Base exception for agent communication errors."""
    pass

class ServiceUnavailable(AgentCommunicationError):
    """Service temporarily unavailable."""
    pass

class PermissionDenied(AgentCommunicationError):
    """Agent lacks permission for operation."""
    pass

class MessageTimeout(AgentCommunicationError):
    """Message processing timed out."""
    pass
```

## Security Protocols

### 1. Agent Authentication
```python
# Each agent message includes authentication
message_header = {
    "agent_id": "content_agent_001",
    "agent_token": "jwt_token_here",
    "timestamp": datetime.utcnow().isoformat(),
    "signature": "message_signature"
}
```

### 2. Permission Validation
```python
# Before processing requests
async def validate_agent_permission(agent_id: str, operation: str):
    coordinator = get_agent_coordinator()
    return await coordinator.validate_agent_action(
        agent_id=agent_id,
        action_path=operation,
        permission_level=PermissionLevel.EXECUTE
    )
```

### 3. Message Encryption
- All inter-module communication uses TLS
- Sensitive data fields are additionally encrypted
- JWT tokens expire after 1 hour

## Monitoring and Observability

### 1. Communication Metrics
```python
METRICS_TO_TRACK = {
    "message_sent_count": Counter,
    "message_received_count": Counter,
    "message_processing_time": Histogram,
    "message_queue_size": Gauge,
    "communication_errors": Counter,
    "retry_count": Counter
}
```

### 2. Logging Standards
```python
# Log all communications
logger.info(
    "Agent communication",
    extra={
        "agent_id": agent_id,
        "operation": operation,
        "target_module": target,
        "correlation_id": correlation_id,
        "duration_ms": duration
    }
)
```

### 3. Distributed Tracing
```python
# Include trace headers
trace_headers = {
    "X-Trace-ID": trace_id,
    "X-Span-ID": span_id,
    "X-Parent-Span-ID": parent_span_id
}
```

## Agent Coordination Scenarios

### Scenario 1: File Upload and Processing
```
1. User uploads file to Drive
2. Drive Agent → DRIVE_FILE_ADDED
3. Content Agent receives event
4. Content Agent parses file
5. Content Agent → CONTENT_PARSED
6. Sync Agent receives event
7. Sync Agent broadcasts to users
```

### Scenario 2: Cross-Module API Change
```
1. Content Agent needs new field from Drive
2. Content Agent → Submit change request
3. Integration Agent reviews request
4. Integration Agent approves
5. Drive Agent implements change
6. Content Agent updates integration
7. Both agents run tests
8. Change marked complete
```

### Scenario 3: System-Wide Update
```
1. Integration Agent → SYSTEM_MAINTENANCE
2. All agents enter read-only mode
3. Updates applied
4. Integration Agent → SYSTEM_READY
5. All agents resume normal operation
```

## Best Practices

### 1. Message Design
- Keep messages small and focused
- Include only necessary data
- Use references for large data
- Version your message schemas

### 2. Error Recovery
- Always implement timeouts
- Provide fallback behavior
- Log all errors with context
- Implement circuit breakers

### 3. Performance
- Batch similar operations
- Use async/await properly
- Cache frequently accessed data
- Monitor queue depths

### 4. Testing
- Test timeout scenarios
- Simulate service failures
- Verify retry logic
- Test permission boundaries

## Agent Handoff Protocol

### Initiating Handoff
```python
async def initiate_handoff(from_agent: str, to_agent: str, context: dict):
    await coordinator.handle_agent_handoff(
        from_agent_id=from_agent,
        to_agent_id=to_agent,
        task_context={
            "task_id": "TASK-001",
            "current_state": context,
            "handoff_reason": "expertise_required",
            "priority": "high"
        }
    )
```

### Receiving Handoff
```python
@event_bus.subscribe("AGENT_HANDOFF")
async def receive_handoff(event: Event):
    if event.data["to_agent"] == self.agent_id:
        context = event.data["task_context"]
        await self.continue_task(context)
```

## Compliance Checklist

- [ ] All events follow naming convention
- [ ] Error handling implemented
- [ ] Timeouts configured
- [ ] Retry logic in place
- [ ] Permissions validated
- [ ] Metrics tracked
- [ ] Logging complete
- [ ] Tests written
- [ ] Documentation updated

Remember: Clear communication between agents ensures system reliability and maintainability. Follow these protocols consistently!