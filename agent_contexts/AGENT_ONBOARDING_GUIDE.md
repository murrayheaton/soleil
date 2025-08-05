# Agent Onboarding Guide

Welcome to the SOLEil Band Platform multi-agent development system! This guide will help you get started as an AI agent working on this codebase.

## Quick Start

### 1. Identify Your Role
First, determine which type of agent you are:
- **Auth Agent**: Authentication and user management
- **Content Agent**: Music file parsing and organization
- **Drive Agent**: Google Drive integration
- **Sync Agent**: Real-time synchronization
- **Dashboard Agent**: UI and data visualization
- **Integration Agent**: Cross-module coordination

### 2. Read Your Context
Navigate to `/agent_contexts/[your_type]_agent.md` for your specific guidelines.

### 3. Understand Your Boundaries
```yaml
Your Module: /band-platform/backend/modules/[your_module]/
Your Frontend: /band-platform/frontend/src/modules/[your_module]/
Your Tests: /band-platform/backend/modules/[your_module]/tests/
```

## First Day Checklist

### Morning: Orientation
- [ ] Read your agent context file completely
- [ ] Review the AGENT_COMMUNICATION_PROTOCOL.md
- [ ] Familiarize yourself with your module's MODULE.md
- [ ] Check your module's current test coverage

### Afternoon: First Tasks
- [ ] Run your module's tests to ensure everything works
- [ ] Review recent commits in your module
- [ ] Check for any pending handoffs in your queue
- [ ] Introduce yourself via an event: `AGENT_ONLINE`

## Key Concepts

### 1. Event-Driven Architecture
Everything in SOLEil is event-driven. You communicate by:
```python
# Publishing events
await event_bus.publish(
    event_type="CONTENT_UPDATED",
    data={"file_id": "123"},
    source_module="content"
)

# Subscribing to events
@event_bus.subscribe("DRIVE_FILE_ADDED")
async def handle_new_file(event):
    # Your logic here
```

### 2. Module Boundaries
- ✅ **DO**: Work within your assigned module paths
- ✅ **DO**: Use events to communicate with other modules
- ✅ **DO**: Request services via API Gateway
- ❌ **DON'T**: Import code from other modules directly
- ❌ **DON'T**: Modify files outside your scope
- ❌ **DON'T**: Access databases owned by other modules

### 3. Cross-Module Changes
When you need changes in another module:
```python
# Submit a change request
request_id = await coordinator.request_cross_module_change(
    requesting_agent_id="your_agent_id",
    affected_modules=["other_module"],
    change_type="api_enhancement",
    description="Need new endpoint for X",
    changes={"details": "here"}
)
```

## Common Workflows

### Handling Your First Task
1. Check pending handoffs:
   ```python
   pending = await get_pending_handoffs("your_agent_id")
   ```

2. Accept the handoff:
   ```python
   await accept_handoff("your_agent_id", handoff_id)
   ```

3. Process the task:
   ```python
   result = await process_task(task_context)
   ```

4. Complete the handoff:
   ```python
   await complete_handoff("your_agent_id", handoff_id, result)
   ```

### Publishing Your First Event
```python
# Announce you're online
await event_bus.publish(
    event_type="AGENT_ONLINE",
    data={
        "agent_id": "your_agent_id",
        "agent_type": "your_type",
        "capabilities": ["list", "your", "skills"]
    },
    source_module="your_module"
)
```

### Making Your First Service Call
```python
# Get a service from another module
gateway = get_api_gateway()
other_service = gateway.get_module_service('other_module', 'service_name')
result = await other_service.method_name(params)
```

## Best Practices

### 1. Error Handling
Always handle errors gracefully:
```python
try:
    result = await risky_operation()
except SpecificError as e:
    # Log the error
    logger.error(f"Operation failed: {e}")
    # Publish error event
    await publish_error_event(e)
    # Return safe default
    return safe_default
```

### 2. Performance Tracking
Track your performance:
```python
start_time = time.time()
result = await do_work()
duration = time.time() - start_time

await record_metric(
    agent_id="your_agent_id",
    metric_type=MetricType.TASK_COMPLETION_TIME,
    value=duration
)
```

### 3. Documentation
Always document your changes:
- Update MODULE.md when adding features
- Add docstrings to all functions
- Comment complex logic
- Update tests

## Communication Etiquette

### With Other Agents
- Be specific in event data
- Include correlation IDs
- Acknowledge received events
- Report completion status

### With the Integration Agent
- Provide detailed change requests
- Include impact analysis
- Suggest testing strategies
- Be responsive to questions

### In Handoffs
- Accept or reject promptly
- Provide clear completion results
- Include helpful notes
- Escalate when blocked

## Troubleshooting

### Common Issues

#### "Permission Denied"
- Check you're working in your module
- Verify your agent permissions
- Request help from Integration Agent

#### "Service Unavailable"
- Check if module is registered
- Verify API Gateway connection
- Try exponential backoff

#### "Event Not Received"
- Confirm subscription pattern
- Check event_type spelling
- Verify source_module

### Getting Help
1. Check documentation first
2. Review similar code in your module
3. Submit question as handoff to Integration Agent
4. Check test examples

## Performance Expectations

### Response Times
- Event handling: <100ms
- Service calls: <1s
- File operations: <5s
- Batch operations: <30s

### Quality Metrics
- Test coverage: >80%
- Error rate: <5%
- Code review pass rate: >90%
- Documentation completeness: 100%

## Module-Specific Tips

### Auth Agent
- Security is paramount
- Always hash passwords
- Validate all inputs
- Log security events

### Content Agent
- Parse files accurately
- Handle all formats
- Maintain metadata
- Optimize for speed

### Drive Agent
- Respect API quotas
- Cache intelligently
- Handle rate limits
- Stream large files

### Sync Agent
- Maintain connections
- Buffer messages
- Handle reconnections
- Ensure delivery

### Dashboard Agent
- Optimize queries
- Cache visualizations
- Responsive design
- Smooth animations

### Integration Agent
- Think system-wide
- Coordinate carefully
- Document decisions
- Test thoroughly

## Your First Week Goals

### Day 1-2: Orientation
- Complete this guide
- Run all tests
- Read recent PRs
- Make first commit

### Day 3-4: First Feature
- Pick a small task
- Implement solution
- Write tests
- Submit for review

### Day 5-7: Integration
- Handle first handoff
- Publish useful events
- Help another agent
- Document learnings

## Resources

### Essential Reading
1. `/agent_contexts/AGENT_TEMPLATE.md` - Base template
2. `/agent_contexts/AGENT_COMMUNICATION_PROTOCOL.md` - How to communicate
3. `/MODULAR_ARCHITECTURE_PROPOSAL.md` - System design
4. Your module's `MODULE.md` - Specific details

### Useful Commands
```bash
# Run your tests
pytest band-platform/backend/modules/your_module/tests/

# Check code style
black band-platform/backend/modules/your_module/
mypy band-platform/backend/modules/your_module/

# See your metrics
curl localhost:8000/api/agents/performance/your_agent_id
```

### API Endpoints
- `GET /api/agents/list` - List all agents
- `GET /api/agents/{agent_id}` - Your details
- `GET /api/agents/handoff/pending/{agent_id}` - Your tasks
- `GET /api/agents/dashboard/overview` - System status

## Remember

You're part of a team! The SOLEil platform depends on all agents working together harmoniously. When in doubt:
- Communicate clearly
- Ask for help
- Document everything
- Test thoroughly
- Be helpful to others

Welcome aboard! 🎵