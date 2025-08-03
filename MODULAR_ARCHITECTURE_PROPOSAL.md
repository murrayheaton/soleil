# SOLEil Modular Architecture Proposal

## Executive Summary

This proposal outlines a modular refactoring strategy for the SOLEil band platform to enable multi-agent development while preserving existing functionality. The approach focuses on creating clear module boundaries with dedicated context files, making it easier for both human developers and AI agents to work independently without conflicts.

## Current Architecture Analysis

### Backend Structure
The backend currently has a semi-modular structure with:
- **API Layer**: Route handlers grouped by feature (auth, content, sync, etc.)
- **Service Layer**: Business logic classes (GoogleDriveService, AuthService, ContentParser, etc.)
- **Model Layer**: Database models (User, Content, FolderStructure, etc.)
- **Utils Layer**: Cross-cutting concerns (monitoring, helpers)

### Frontend Structure
The frontend follows Next.js conventions with:
- **Pages**: Route-based components in `/app`
- **Components**: Reusable UI components
- **Lib**: API clients and utilities
- **Types**: TypeScript definitions

### Identified Functional Domains

Based on the codebase analysis, the application has these core domains:

1. **Authentication & User Management**
   - Google OAuth integration
   - User profiles and preferences
   - Session management
   - JWT token handling

2. **Content Management**
   - File parsing and organization
   - Instrument-based filtering
   - Chart metadata extraction
   - File type detection

3. **Google Drive Integration**
   - File browsing and streaming
   - Folder structure management
   - Rate limiting and caching
   - OAuth token management

4. **Synchronization**
   - Real-time updates via WebSocket
   - File change detection
   - Sync state management
   - Event broadcasting

5. **UI/Presentation**
   - Dashboard modules
   - File browser interface
   - Audio/chart viewer
   - Mobile-responsive layouts

## Proposed Modular Architecture

### 1. Module Structure

Each module should be self-contained with:
```
module_name/
├── MODULE.md           # Module context and documentation
├── api/                # API endpoints specific to this module
├── services/           # Business logic
├── models/             # Data models
├── types/              # TypeScript definitions
├── tests/              # Module-specific tests
└── frontend/           # Frontend components (if applicable)
    ├── components/
    ├── hooks/
    └── utils/
```

### 2. Proposed Modules

#### Auth Module
```
auth/
├── MODULE.md
├── api/
│   ├── google_auth.py
│   └── auth_routes.py
├── services/
│   ├── google_auth_service.py
│   ├── jwt_service.py
│   └── session_service.py
├── models/
│   └── user.py
├── types/
│   └── auth.ts
├── tests/
└── frontend/
    ├── components/
    │   ├── LoginForm.tsx
    │   └── ProfileManager.tsx
    └── hooks/
        └── useAuth.ts
```

#### Content Module
```
content/
├── MODULE.md
├── api/
│   └── content_routes.py
├── services/
│   ├── content_parser.py
│   ├── file_organizer.py
│   └── instrument_filter.py
├── models/
│   └── content.py
├── types/
│   └── content.ts
├── tests/
└── frontend/
    ├── components/
    │   ├── ChartViewer.tsx
    │   ├── AudioPlayer.tsx
    │   └── FileList.tsx
    └── hooks/
        └── useContent.ts
```

#### Drive Module
```
drive/
├── MODULE.md
├── api/
│   └── drive_routes.py
├── services/
│   ├── drive_client.py
│   ├── drive_auth.py
│   ├── rate_limiter.py
│   └── cache_manager.py
├── models/
│   └── drive_metadata.py
├── types/
│   └── drive.ts
├── tests/
└── utils/
    └── drive_helpers.py
```

#### Sync Module
```
sync/
├── MODULE.md
├── api/
│   ├── sync_routes.py
│   └── websocket.py
├── services/
│   ├── sync_engine.py
│   ├── websocket_manager.py
│   └── event_broadcaster.py
├── models/
│   └── sync_state.py
├── types/
│   └── sync.ts
├── tests/
└── frontend/
    └── hooks/
        └── useWebSocket.ts
```

#### Dashboard Module
```
dashboard/
├── MODULE.md
├── api/
│   └── dashboard_routes.py
├── services/
│   └── dashboard_aggregator.py
├── types/
│   └── dashboard.ts
├── tests/
└── frontend/
    ├── components/
    │   ├── DashboardGrid.tsx
    │   └── modules/
    │       ├── GigsModule.tsx
    │       ├── RepertoireModule.tsx
    │       └── OffersModule.tsx
    └── config/
        └── dashboard-modules.ts
```

### 3. Module Context Files (MODULE.md)

Each module should have a MODULE.md file containing:

```markdown
# [Module Name] Module

## Purpose
Brief description of what this module handles.

## Dependencies
- Internal: List of other modules this depends on
- External: NPM packages, Python libraries

## API Endpoints
- `GET /api/[module]/...` - Description
- `POST /api/[module]/...` - Description

## Key Services
- `ServiceName`: What it does
- `AnotherService`: What it does

## Data Models
- `ModelName`: Key fields and purpose

## Frontend Components
- `ComponentName`: Usage and props

## Testing Strategy
- Unit tests: What to test
- Integration tests: Key scenarios

## Common Tasks
- How to add a new feature
- How to modify existing behavior
- Common debugging steps

## Module-Specific Rules
- Constraints or patterns specific to this module
- Security considerations
- Performance notes
```

### 4. Cross-Module Communication

#### API Gateway Pattern
```python
# core/api_gateway.py
class APIGateway:
    """Central point for module registration and routing"""
    
    def register_module(self, module_name: str, router: APIRouter):
        """Register a module's API routes"""
        pass
    
    def get_module_service(self, module_name: str, service_name: str):
        """Get a service from another module"""
        pass
```

#### Event Bus for Loose Coupling
```python
# core/event_bus.py
class EventBus:
    """Publish-subscribe pattern for module communication"""
    
    def publish(self, event_type: str, data: dict):
        """Publish an event"""
        pass
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event"""
        pass
```

### 5. Shared Core Module

```
core/
├── MODULE.md
├── config/
│   ├── settings.py
│   └── constants.py
├── middleware/
│   ├── auth_middleware.py
│   └── error_handler.py
├── utils/
│   ├── validators.py
│   └── formatters.py
├── types/
│   └── common.ts
└── tests/
```

## Implementation Strategy

### Phase 1: Create Module Structure (Non-Breaking)
1. Create new module directories alongside existing structure
2. Add MODULE.md files with documentation
3. Create module-specific __init__.py files

### Phase 2: Gradual Migration
1. Move services one at a time into modules
2. Update imports to use module structure
3. Add module registration to main app
4. Ensure all tests pass after each move

### Phase 3: API Versioning
1. Create v2 API routes using module structure
2. Keep v1 routes pointing to old structure
3. Update frontend to use v2 gradually
4. Deprecate v1 after full migration

### Phase 4: Enhanced Module Isolation
1. Add module-specific configuration
2. Implement event bus for cross-module communication
3. Add module health checks
4. Create module-specific documentation

## Benefits for Multi-Agent Development

### 1. Clear Boundaries
- Each agent can work on a specific module
- MODULE.md provides complete context
- Reduced chance of conflicts

### 2. Parallel Development
- Multiple agents can work simultaneously
- Each module has its own test suite
- Independent deployment possible

### 3. Easier Onboarding
- New agents can quickly understand a module
- Clear documentation of dependencies
- Explicit interfaces between modules

### 4. Better Testing
- Module-specific test suites
- Mocked dependencies for isolation
- Clearer test organization

## Example Agent Instructions

```markdown
## Agent: Content Module Specialist

You are responsible for the Content module at content/.

### Your Scope:
- All files within content/ directory
- Content parsing and organization logic
- Instrument-based filtering
- File metadata extraction

### Key Files:
- content/MODULE.md - Your primary context
- content/services/content_parser.py - Main parsing logic
- content/api/content_routes.py - API endpoints

### Before Making Changes:
1. Read content/MODULE.md
2. Check module dependencies
3. Run module-specific tests: pytest content/tests/

### Cross-Module Communication:
- Use EventBus for notifications
- Import only from module public interfaces
- Document any new dependencies in MODULE.md
```

## Migration Checklist

- [ ] Create module directory structure
- [ ] Write MODULE.md for each module
- [ ] Move auth services to auth module
- [ ] Move content services to content module
- [ ] Move drive services to drive module
- [ ] Move sync services to sync module
- [ ] Update all imports
- [ ] Add module registration
- [ ] Update tests
- [ ] Create v2 API routes
- [ ] Update frontend API clients
- [ ] Add event bus implementation
- [ ] Document migration in DEV_LOG.md

## Conclusion

This modular architecture will:
1. Enable parallel development by multiple agents
2. Reduce merge conflicts and breaking changes
3. Improve code organization and maintainability
4. Make the codebase more scalable
5. Provide clear boundaries for AI agents

The migration can be done incrementally without breaking existing functionality, allowing for a smooth transition to the new architecture.