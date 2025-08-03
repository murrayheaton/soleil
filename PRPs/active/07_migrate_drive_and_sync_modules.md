# PRP: Migrate Drive and Sync Modules

## Overview
Migrate Google Drive integration and synchronization functionality into their respective modules while maintaining seamless operation.

## Context
- This continues Phase 2 of the modular architecture migration
- Drive and Sync modules are closely related and should be migrated together
- These modules handle critical real-time functionality
- Reference: MODULAR_ARCHITECTURE_PROPOSAL.md

## Pre-Implementation Requirements
1. Complete PRP 06 (Content Module Migration)
2. Ensure all tests pass before starting
3. Continue on branch: `feature/module-structure-foundation`
4. Review WebSocket and sync implementation carefully

## Implementation Tasks

### 1. Migrate Drive Module Services
- [ ] Copy `app/services/google_drive.py` to `modules/drive/services/drive_client.py`
- [ ] Copy `app/services/google_drive_oauth.py` to `modules/drive/services/drive_auth.py`
- [ ] Copy `app/services/drive_helpers.py` to `modules/drive/utils/drive_helpers.py`
- [ ] Create `modules/drive/services/rate_limiter.py`:
  - [ ] Extract RateLimiter class from drive_helpers
  - [ ] Enhance with configurable limits
- [ ] Create `modules/drive/services/cache_manager.py`:
  - [ ] Implement caching strategy for drive operations
- [ ] Update all imports within drive module

### 2. Migrate Sync Module Services
- [ ] Copy `app/services/sync_engine.py` to `modules/sync/services/sync_engine.py`
- [ ] Copy `app/services/websocket_manager.py` to `modules/sync/services/websocket_manager.py`
- [ ] Copy `app/services/file_synchronizer.py` to `modules/sync/services/file_synchronizer.py`
- [ ] Create `modules/sync/services/event_broadcaster.py`:
  - [ ] Extract event broadcasting logic
  - [ ] Integrate with core EventBus
- [ ] Update sync module internal imports

### 3. Migrate API Routes
- [ ] Copy `app/api/sync.py` to `modules/sync/api/sync_routes.py`
- [ ] Copy `app/api/websocket.py` to `modules/sync/api/websocket.py`
- [ ] Create drive-specific routes in `modules/drive/api/drive_routes.py`
- [ ] Update route imports to use module services

### 4. Migrate Models
- [ ] Copy `app/models/sync.py` to `modules/sync/models/sync_state.py`
- [ ] Create `modules/drive/models/drive_metadata.py` for drive-specific models
- [ ] Update model imports in services

### 5. Handle Module Dependencies
- [ ] Drive module depends on auth module for OAuth
- [ ] Sync module depends on drive module for file operations
- [ ] Sync module depends on content module for parsing
- [ ] Update imports to use module interfaces:
  ```python
  from modules.auth import GoogleAuthService
  from modules.content import ContentParser
  ```

### 6. Create Module Interfaces
- [ ] Create `modules/drive/__init__.py`:
  ```python
  from .api import drive_router
  from .services import DriveClient, DriveAuth, RateLimiter
  from .models import DriveMetadata
  ```
- [ ] Create `modules/sync/__init__.py`:
  ```python
  from .api import sync_router, websocket_endpoint
  from .services import SyncEngine, WebSocketManager
  from .models import SyncState
  ```

### 7. Update WebSocket Implementation
- [ ] Ensure WebSocket manager works with new module structure
- [ ] Update event types to use EventBus
- [ ] Maintain real-time functionality
- [ ] Test connection stability

### 8. Migrate Frontend Code
- [ ] Create `frontend/src/modules/sync/hooks/useWebSocket.ts`
- [ ] Move WebSocket utilities to sync module
- [ ] Update components to use module hooks
- [ ] Ensure real-time updates still work

### 9. Create Module Tests
- [ ] Copy and enhance drive tests in `modules/drive/tests/`
- [ ] Copy and enhance sync tests in `modules/sync/tests/`
- [ ] Add integration tests for drive-sync interaction
- [ ] Test WebSocket functionality thoroughly

### 10. Update Module Documentation
- [ ] Complete Drive MODULE.md:
  - [ ] Rate limiting strategies
  - [ ] Caching policies
  - [ ] OAuth token management
  - [ ] Error handling patterns
- [ ] Complete Sync MODULE.md:
  - [ ] WebSocket protocol
  - [ ] Event types and payloads
  - [ ] Sync strategies
  - [ ] Conflict resolution

## Validation Steps
1. Run module tests:
   - `pytest modules/drive/tests/`
   - `pytest modules/sync/tests/`
2. Test critical functionality:
   - [ ] Google Drive authentication
   - [ ] File browsing and streaming
   - [ ] Real-time sync updates
   - [ ] WebSocket connection stability
3. Test rate limiting under load
4. Verify caching improves performance

## Success Criteria
- [ ] Drive and sync modules are fully migrated
- [ ] WebSocket real-time updates work perfectly
- [ ] Google Drive operations maintain performance
- [ ] Rate limiting prevents API exhaustion
- [ ] All tests pass
- [ ] No functionality is broken

## Post-Implementation
1. Run full test suite
2. Test complete sync flow with multiple clients
3. Monitor WebSocket connections for stability
4. Update DEV_LOG.md with migration notes
5. Commit changes with message: "feat: migrate drive and sync modules to new structure"