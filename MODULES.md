# SOLEil Modules Overview

## Module Architecture

The SOLEil platform is organized into self-contained modules that communicate through well-defined interfaces. This architecture enables:

- Clear separation of concerns
- Independent development and testing
- Easy maintenance and updates
- Multi-agent development support

## Core Infrastructure

### Event Bus
- Publish/subscribe pattern for loose coupling
- Asynchronous event handling
- Event history and replay

### API Gateway
- Dynamic module registration
- Centralized routing
- Dependency management

## Application Modules

### 1. Authentication Module (`/modules/auth`)
**Purpose**: User authentication and authorization
- Google OAuth integration
- JWT token management
- User profile operations
- Session management

### 2. Content Module (`/modules/content`)
**Purpose**: Music content management
- Chart (sheet music) organization
- Audio file management
- Setlist creation
- Instrument-based filtering

### 3. Drive Module (`/modules/drive`)
**Purpose**: Google Drive integration
- File browsing and streaming
- Folder organization
- Caching and rate limiting
- OAuth token management

### 4. Sync Module (`/modules/sync`)
**Purpose**: Real-time synchronization
- WebSocket connections
- Change detection
- Event broadcasting
- Offline sync support

### 5. Dashboard Module (`/modules/dashboard`)
**Purpose**: Analytics and monitoring
- System health checks
- Usage analytics
- Performance metrics
- Audit logging

## Module Communication

Modules communicate through:
1. **Events** - Asynchronous notifications via EventBus
2. **API Calls** - Direct service invocations when needed
3. **Shared Data** - Through defined interfaces only

## Development Guidelines

1. Each module must have a `MODULE.md` file documenting its purpose and interfaces
2. Modules should minimize dependencies on other modules
3. All inter-module communication should be documented
4. Tests should mock external module dependencies
5. Module initialization should be handled through the module loader

## Module Load Order

1. Core (always first)
2. Auth
3. Drive
4. Content
5. Sync
6. Dashboard

This order ensures dependencies are satisfied during initialization.