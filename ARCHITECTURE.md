# Planning Overview

# SOLEil Band Platform - Project Planning

## 🎯 Project Overview

SOLEil (Sole Power Live) is a band platform designed to help musicians collaborate, manage their creative process, and build their careers. The project uses Context Engineering methodology to ensure high-quality, AI-assisted development.

**Current Status**: Production-ready platform with complete authentication, file management, and professional UI.

## 🏗️ Architecture

### Modular Architecture (Completed)
The platform has been successfully migrated to a modular architecture that enables multi-agent development and better scalability.

**Core Modules**:
- **Auth Module (v1.0.0)**: Google OAuth, JWT, session management, user profiles
- **Content Module (v1.0.0)**: File parsing, instrument filtering, chart metadata
- **Drive Module (v1.0.0)**: Google Drive integration, file streaming, caching
- **Sync Module (v1.0.0)**: WebSocket real-time updates, event broadcasting
- **Dashboard Module (v1.0.0)**: UI components, module grid system
- **Core Module (v1.0.0)**: EventBus, API Gateway, shared infrastructure

See MODULES.md for detailed module documentation and AGENT_GUIDE.md for AI agent development guidelines.

### Backend
- **Framework**: FastAPI with modular routing
- **Database**: SQLAlchemy/SQLModel for ORM
- **Environment**: Python with venv_linux virtual environment
- **Testing**: Pytest with module-specific test suites
- **Code Quality**: Black formatter, Ruff linter, MyPy type checking
- **Architecture**: Service layer pattern with clear module boundaries

### Frontend
- **Framework**: Next.js with module-based component organization
- **Design**: Mobile-first responsive design
- **Data Fetching**: React Query with module-specific hooks
- **Testing**: Jest/React Testing Library
- **Build**: npm run build
- **State Management**: Module-scoped contexts and hooks

### Development Philosophy
- **File Size Limit**: Never exceed 500 lines per file
- **Modularity**: Self-contained modules with MODULE.md documentation
- **Testing**: Module-specific test suites (unit, integration, e2e)
- **Documentation**: MODULE.md for each module + function docstrings
- **Communication**: Event bus for loose coupling between modules

## 📁 Project Structure

### Current Structure (Production)
```
soleil/
├── band-platform/
│   ├── backend/
│   │   ├── venv_linux/          # Virtual environment
│   │   ├── start_server.py      # Main FastAPI application
│   │   ├── app/                 # Application code
│   │   │   ├── services/        # Business logic services
│   │   │   ├── models/          # Database models
│   │   │   └── utils/           # Utilities and helpers
│   │   └── user_profiles.json   # User profile persistence
│   └── frontend/
│       └── src/
│           ├── app/             # Next.js pages
│           ├── components/      # React components
│           ├── lib/             # API clients and utilities
│           └── types/           # TypeScript definitions
├── PRPs/                        # Project Requirement Prompts
│   ├── active/                  # PRPs ready for execution
│   └── archive/                 # Completed PRPs
├── MODULAR_ARCHITECTURE_PROPOSAL.md  # Migration plan
└── [documentation files]        # Various .md files
```

### Current Modular Structure
```
soleil/
├── band-platform/
│   ├── backend/
│   │   ├── modules/
│   │   │   ├── auth/           # Authentication module
│   │   │   ├── content/        # Content management module
│   │   │   ├── drive/          # Google Drive module
│   │   │   ├── sync/           # Synchronization module
│   │   │   └── dashboard/      # Dashboard aggregation
│   │   ├── core/               # Shared utilities and config
│   │   └── start_server.py     # Module registration and startup
│   └── frontend/
│       └── src/
│           ├── modules/         # Frontend module components
│           └── core/            # Shared components and utilities
└── [documentation files]
```

## 🧱 Code Organization Patterns

### Module Structure
Each module follows this pattern:
```
module_name/
├── MODULE.md           # Module documentation and context
├── __init__.py         # Public module interface
├── api/                # FastAPI route handlers
├── services/           # Business logic
├── models/             # Data models
├── types/              # TypeScript types (frontend modules)
├── tests/              # Module-specific tests
└── frontend/           # Frontend components (if applicable)
    ├── components/
    ├── hooks/
    └── utils/
```

### Module Communication
- **Direct Import**: Only from module's public interface (`__init__.py`)
- **Event Bus**: For loose coupling between modules
- **API Gateway**: Central routing and service discovery
- **Dependency Injection**: For testing and flexibility

### General Principles
- Each module must have a MODULE.md file
- Use relative imports within modules
- Use python_dotenv and load_env() for environment variables
- Follow PEP8 with type hints
- Use Pydantic for data validation
- Module interfaces must be explicitly defined

## 🧪 Testing Strategy

- **Location**: Tests mirror main app structure in `/tests` folder
- **Framework**: Pytest for backend, Jest for frontend
- **Coverage**: Minimum 3 tests per feature:
  1. Expected use case
  2. Edge case
  3. Failure case

## 📝 Documentation Requirements

Every implementation must update:
1. **DEV_LOG.md** - Human-friendly summary
2. **DEV_LOG_TECHNICAL.md** - Technical details
3. **README.md** - If dependencies or setup changed
4. **PRODUCT_VISION.md** - If user-facing features added

## 🔄 Development Workflow

1. Check `TASK.md` before starting work
2. Add new tasks with today's date
3. Create tests first (TDD approach)
4. Implement feature following architecture patterns
5. Run quality checks (ruff, mypy, tests)
6. Update documentation
7. Mark tasks complete in `TASK.md`

## 🎨 Style Guidelines

- **Python**: PEP8, Black formatting, type hints required
- **TypeScript**: ESLint configuration, functional components
- **Comments**: Use `# Reason:` for complex logic explanations
- **Imports**: Prefer relative imports within packages
- **Environment**: Always use venv_linux for Python commands

## 🚫 Constraints

- Never create files longer than 500 lines
- Never assume missing context - ask questions
- Never hallucinate libraries - only use verified packages
- Always confirm file paths exist before referencing
- Never delete existing code unless explicitly instructed


---

# Module Reference

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


---

# Historical Proposal (for archive)

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
