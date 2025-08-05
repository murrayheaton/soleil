# AI Agent Development Guide for SOLEil

**Last Updated:** 2025-08-05

## Welcome AI Agent!

This guide will help you work effectively with the SOLEil modular architecture. Please read this completely before starting any development work.

## Quick Start

1. **Identify your assigned module** from the module assignment table below
2. **Generate module context**: 
   ```bash
   python scripts/generate_module_context.py [module_name]
   ```
3. **Read the MODULE.md** file in your module directory
4. **Validate module structure** before making changes:
   ```bash
   python scripts/validate_module.py [module_name]
   ```

## Module Assignment Table

| Module | Description | Key Responsibilities |
|--------|-------------|---------------------|
| **auth** | Authentication & Authorization | OAuth, JWT, sessions, user management |
| **content** | Content Management | File parsing, metadata, organization |
| **drive** | Google Drive Integration | API calls, caching, file streaming |
| **sync** | Real-time Synchronization | WebSockets, event broadcasting |
| **dashboard** | Dashboard & UI | Frontend components, user preferences |

## Development Rules

### 🚫 NEVER DO THIS

1. **NEVER modify files outside your assigned module**
2. **NEVER create direct dependencies between modules**
3. **NEVER access another module's database tables directly**
4. **NEVER import private functions (those starting with _)**
5. **NEVER commit without running module validation**

### ✅ ALWAYS DO THIS

1. **ALWAYS read MODULE.md before starting work**
2. **ALWAYS use EventBus for cross-module communication**
3. **ALWAYS write tests for new functionality**
4. **ALWAYS update MODULE.md when adding features**
5. **ALWAYS use the module's configuration system**

## Module Structure

Each module follows this structure:
```
modules/[module_name]/
├── MODULE.md           # Your primary documentation
├── __init__.py        # Module initialization
├── config.py          # Module configuration
├── api/               # API endpoints
├── services/          # Business logic
├── models/            # Data models
├── tests/             # Module tests
└── exceptions.py      # Module-specific exceptions
```

## Communication Patterns

### 1. Event-Based Communication (Async)

```python
from modules.core import get_event_bus, events

# Publishing an event
event_bus = get_event_bus()
await event_bus.publish(
    event_type=events.CONTENT_UPDATED,
    data={'file_id': '123', 'action': 'parsed'},
    source_module='content'
)

# Subscribing to events
def handle_auth_change(event):
    # Handle the event
    pass

event_bus.subscribe(
    events.AUTH_STATE_CHANGED,
    handle_auth_change,
    target_module='content'
)
```

### 2. Service Discovery (Sync)

```python
from modules.core import get_api_gateway

# Get another module's service
gateway = get_api_gateway()
auth_service = gateway.get_module_service('auth', 'jwt')

# Use the service
token = auth_service.create_token(user_data)
```

## Testing Your Module

### Run Module Tests
```bash
cd band-platform/backend
pytest modules/[module_name]/tests/ -v
```

### Validate Module Structure
```bash
python scripts/validate_module.py [module_name]
```

### Check Module Context
```bash
python scripts/generate_module_context.py [module_name]
```

## Common Tasks

### Adding a New API Endpoint

1. Create route in `api/` directory
2. Implement business logic in `services/`
3. Update MODULE.md with endpoint documentation
4. Write tests for the endpoint
5. Register route with module router

### Adding a New Service

1. Create service class in `services/`
2. Follow naming convention: `[Feature]Service`
3. Register with API Gateway if needed by other modules
4. Document public methods
5. Write comprehensive tests

### Publishing Events

1. Import event constants from `modules.core.events`
2. Use meaningful event data structure
3. Document event in MODULE.md
4. Consider event versioning for breaking changes

### Handling Configuration

```python
from modules.[module_name].config import [Module]ModuleConfig

# Load module config
config = [Module]ModuleConfig()

# Access config values
timeout = config.timeout
api_key = config.api_key
```

## Module-Specific Guidelines

### Auth Module
- Always hash passwords with bcrypt
- Validate JWT tokens properly
- Handle OAuth state securely
- Emit events for login/logout

### Content Module
- Parse files asynchronously
- Extract comprehensive metadata
- Handle multiple file formats
- Maintain instrument mappings

### Drive Module
- Implement rate limiting
- Cache frequently accessed data
- Handle API errors gracefully
- Stream large files efficiently

### Sync Module
- Manage WebSocket connections
- Handle reconnection logic
- Broadcast events efficiently
- Maintain connection state

### Dashboard Module
- Keep components modular
- Manage user preferences
- Handle responsive layouts
- Optimize data fetching

## Error Handling

```python
from modules.[module_name].exceptions import [Module]Error

try:
    # Your code
    pass
except SpecificError as e:
    # Log error
    logger.error(f"Error in {module_name}: {e}")
    # Publish error event if needed
    await event_bus.publish(
        events.SYSTEM_ERROR,
        {'module': module_name, 'error': str(e)},
        source_module=module_name
    )
```

## Version Management

When making changes:
- **Bug fixes**: Increment PATCH (1.0.0 → 1.0.1)
- **New features**: Increment MINOR (1.0.0 → 1.1.0)
- **Breaking changes**: Increment MAJOR (1.0.0 → 2.0.0)

Update version in:
1. MODULE.md header
2. config.py module_version
3. MODULES.md compatibility matrix

## Getting Help

1. **Check MODULE.md** for module-specific guidance
2. **Read communication_examples.py** for patterns
3. **Look at existing code** in your module
4. **Check test files** for usage examples
5. **Ask for clarification** if requirements are unclear

## Debugging Tips

1. **Enable debug logging**:
   ```python
   import logging
   logging.getLogger('modules.[module_name]').setLevel(logging.DEBUG)
   ```

2. **Check event history**:
   ```python
   event_bus = get_event_bus()
   history = event_bus.get_history('event_name')
   ```

3. **Validate module health**:
   ```python
   gateway = get_api_gateway()
   health = await gateway.check_module_health('[module_name]')
   ```

## Best Practices

1. **Write Clear Code**
   - Use descriptive variable names
   - Add docstrings to all functions
   - Keep functions focused and small

2. **Handle Errors Gracefully**
   - Catch specific exceptions
   - Log errors with context
   - Provide meaningful error messages

3. **Optimize Performance**
   - Use caching where appropriate
   - Batch operations when possible
   - Profile code for bottlenecks

4. **Maintain Security**
   - Validate all inputs
   - Use parameterized queries
   - Don't log sensitive data

## Final Checklist

Before committing changes:
- [ ] All tests pass
- [ ] Module validation passes
- [ ] MODULE.md is updated
- [ ] Version bumped if needed
- [ ] No cross-module imports
- [ ] Events documented
- [ ] Configuration documented
- [ ] Error handling in place

Remember: You're part of a larger system. Your module's reliability affects the entire platform!