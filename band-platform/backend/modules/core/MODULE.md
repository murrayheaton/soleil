# Core Module

## Purpose and Scope
The Core module provides shared infrastructure and utilities that all other SOLEil modules depend on. It acts as the foundation for the modular architecture.

## Module Context
This module enables:
- Inter-module communication through the EventBus
- Dynamic module registration via the APIGateway
- Shared middleware for common concerns (auth, logging, error handling)
- Shared utilities for common operations
- Configuration management across modules

## Dependencies
- FastAPI (for APIGateway)
- Pydantic (for configuration models)
- No dependencies on other SOLEil modules (this is the foundation)

## API Endpoints
This module does not expose direct API endpoints. Instead, it provides infrastructure for other modules to register their endpoints.

## Key Services

### EventBus
- Publish/subscribe pattern for inter-module communication
- Asynchronous event handling
- Event history and replay capabilities

### APIGateway
- Dynamic route registration
- Module lifecycle management
- Request routing and middleware application

## Testing Strategy
- Unit tests for EventBus functionality
- Integration tests for APIGateway registration
- Mock implementations for testing other modules

## Module-Specific Rules
1. This module must not depend on any other SOLEil modules
2. All interfaces must be backward compatible
3. Configuration changes must be versioned
4. Event schemas must be documented and versioned
5. Middleware must be optional and configurable