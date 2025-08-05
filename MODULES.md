# SOLEil Modules Overview

**Last Updated:** 2025-08-05

## Module Architecture

The SOLEil platform is organized into self-contained modules that communicate through well-defined interfaces. This architecture enables parallel development by multiple agents and maintains clear boundaries between different functional areas.

## Core Modules

### 🔐 Auth Module (v1.0.0)
**Status:** Active  
**Purpose:** Manages authentication, authorization, and user sessions  
**Key Features:**
- Google OAuth integration
- JWT token management
- Role-based access control
- Session management

### 📄 Content Module (v1.0.0)
**Status:** Active  
**Purpose:** Handles music content parsing, organization, and metadata  
**Key Features:**
- File parsing and metadata extraction
- Instrument-based filtering
- Content organization
- Chart and audio file management

### 📁 Drive Module (v1.0.0)
**Status:** Active  
**Purpose:** Integrates with Google Drive for file storage and streaming  
**Key Features:**
- Google Drive API integration
- File streaming and caching
- Folder structure management
- Rate limiting and optimization

### 🔄 Sync Module (v1.0.0)
**Status:** Active  
**Purpose:** Manages real-time synchronization and WebSocket communication  
**Key Features:**
- WebSocket server management
- Real-time event broadcasting
- File change detection
- Client synchronization

### 📊 Dashboard Module (v1.0.0)
**Status:** Active  
**Purpose:** Provides customizable dashboard functionality  
**Key Features:**
- Modular dashboard components
- User preference management
- Data aggregation
- Widget system

### 🛠️ Core Module (v1.0.0)
**Status:** Active  
**Purpose:** Shared infrastructure and utilities  
**Key Features:**
- Event bus for inter-module communication
- API gateway for module registration
- Common middleware
- Shared configuration

## Module Dependency Graph

```
┌─────────────┐
│    Core     │ ← All modules depend on Core
└──────┬──────┘
       │
┌──────┴──────┐     ┌─────────────┐
│    Auth     │ ← ─ │  Dashboard  │
└──────┬──────┘     └─────────────┘
       │
┌──────┴──────┐     ┌─────────────┐
│   Content   │ ← ─ │    Sync     │
└──────┬──────┘     └──────┬──────┘
       │                   │
┌──────┴──────┐           │
│    Drive    │ ← ─ ─ ─ ─ ┘
└─────────────┘
```

## Compatibility Matrix

| Module | Min Core Version | Compatible With |
|--------|------------------|-----------------|
| Auth v1.0.0 | Core v1.0.0 | All modules |
| Content v1.0.0 | Core v1.0.0 | Auth v1.0.0+ |
| Drive v1.0.0 | Core v1.0.0 | Auth v1.0.0+, Content v1.0.0+ |
| Sync v1.0.0 | Core v1.0.0 | All modules |
| Dashboard v1.0.0 | Core v1.0.0 | Auth v1.0.0+ |

## Communication Patterns

### Event-Based Communication
Modules communicate asynchronously through the EventBus:
- **Publish:** Modules emit events when state changes occur
- **Subscribe:** Modules listen for relevant events from other modules
- **Decoupling:** No direct dependencies between event producers and consumers

### Service Discovery
Modules can discover and use services from other modules:
- **Registration:** Modules register their services with the API Gateway
- **Discovery:** Modules query the API Gateway for available services
- **Invocation:** Direct service calls for synchronous operations

## Module Development Guidelines

### For Human Developers
1. Always work within module boundaries
2. Use EventBus for cross-module communication
3. Document all public interfaces in MODULE.md
4. Write module-specific tests in the tests/ directory
5. Update version when making breaking changes

### For AI Agents
1. Read MODULE.md before making any changes
2. Use `scripts/generate_module_context.py` to understand module structure
3. Run `scripts/validate_module.py` before committing changes
4. Only modify files within your assigned module
5. Coordinate through events, not direct dependencies

## Version Management

### Version Format
Modules use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR:** Breaking changes to public interfaces
- **MINOR:** New features, backward compatible
- **PATCH:** Bug fixes, no interface changes

### Breaking Changes Process
1. Announce deprecation in current version
2. Support both old and new interfaces for one minor version
3. Remove deprecated code in next major version
4. Update all dependent modules

## Module Health Monitoring

Each module provides health checks through the API Gateway:
- **Endpoint:** `/api/modules/{module_name}/health`
- **Status:** OK, WARNING, ERROR
- **Details:** Module-specific health information

## Adding New Modules

To add a new module:
1. Create directory structure under `modules/`
2. Include all required subdirectories
3. Create MODULE.md with complete documentation
4. Implement configuration class
5. Register with API Gateway
6. Add to this compatibility matrix
7. Run validation script

## Module Assignment for Agents

| Module | Assigned Agent | Specialization |
|--------|----------------|----------------|
| Auth | auth-agent | Security, OAuth, JWT |
| Content | content-agent | Parsing, metadata, organization |
| Drive | drive-agent | Google APIs, caching, streaming |
| Sync | sync-agent | WebSockets, real-time, events |
| Dashboard | ui-agent | Frontend, components, UX |

## Future Modules (Planned)

- **Analytics Module:** Usage tracking and insights
- **Notification Module:** Email and push notifications
- **Backup Module:** Data backup and recovery
- **Admin Module:** Administration interface
- **API Module:** External API gateway