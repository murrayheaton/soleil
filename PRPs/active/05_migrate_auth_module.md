# PRP: Migrate Auth Module

## Overview
Migrate all authentication-related code into the auth module structure while maintaining backward compatibility.

## Context
- This is Phase 2 of the modular architecture migration
- Builds on the module structure created in PRP 04
- Must maintain all existing API endpoints and functionality
- Reference: MODULAR_ARCHITECTURE_PROPOSAL.md

## Pre-Implementation Requirements
1. Complete PRP 04 (Module Structure Foundation)
2. Ensure all tests pass before starting
3. Continue on branch: `feature/module-structure-foundation`
4. Review all auth-related files in current structure

## Implementation Tasks

### 1. Migrate Auth Services
- [ ] Copy `app/services/auth.py` to `modules/auth/services/auth_service.py`
- [ ] Split auth.py into smaller services:
  - [ ] `google_auth_service.py` - GoogleAuthService class
  - [ ] `jwt_service.py` - JWTService class
  - [ ] `session_service.py` - Session management logic
- [ ] Update imports within auth module to use relative imports
- [ ] Create `modules/auth/services/__init__.py` with public exports

### 2. Migrate Auth API Routes
- [ ] Copy `app/api/auth.py` to `modules/auth/api/auth_routes.py`
- [ ] Copy `app/api/google_auth.py` to `modules/auth/api/google_auth_routes.py`
- [ ] Update route imports to use auth module services
- [ ] Create auth module router in `modules/auth/api/__init__.py`

### 3. Migrate Auth Models
- [ ] Copy `app/models/user.py` to `modules/auth/models/user.py`
- [ ] Update model imports in auth services
- [ ] Ensure database migrations still work

### 4. Create Auth Module Interface
- [ ] Create `modules/auth/__init__.py` with public API:
  ```python
  from .api import auth_router
  from .services import AuthService, GoogleAuthService
  from .models import User, UserCreate, UserUpdate
  ```
- [ ] Register auth module with APIGateway

### 5. Update Main Application
- [ ] Update `start_server.py` to import from auth module
- [ ] Create compatibility layer in old locations:
  - [ ] `app/services/auth.py` imports from `modules.auth`
  - [ ] `app/api/auth.py` imports from `modules.auth`
- [ ] Ensure all existing imports continue to work

### 6. Migrate Frontend Auth Code
- [ ] Move auth components to `frontend/src/modules/auth/components/`
  - [ ] LoginForm component
  - [ ] ProfileManager component
- [ ] Create `useAuth` hook in `frontend/src/modules/auth/hooks/`
- [ ] Move auth types to `frontend/src/modules/auth/types/`

### 7. Create Auth Tests
- [ ] Copy existing auth tests to `modules/auth/tests/`
- [ ] Update test imports to use module structure
- [ ] Add module-specific test configuration
- [ ] Ensure all tests pass with new structure

### 8. Update Auth MODULE.md
- [ ] Document all services and their purposes
- [ ] List all API endpoints with descriptions
- [ ] Document models and their relationships
- [ ] Add common auth tasks and patterns
- [ ] Include security considerations

## Validation Steps
1. Run auth module tests: `pytest modules/auth/tests/`
2. Run full test suite to ensure compatibility
3. Test all auth endpoints manually:
   - [ ] Google OAuth login flow
   - [ ] Profile creation/update
   - [ ] Session management
   - [ ] JWT token validation
4. Verify frontend auth functionality still works

## Success Criteria
- [ ] All auth code is migrated to auth module
- [ ] Backward compatibility is maintained
- [ ] All tests pass (both old and new)
- [ ] Auth MODULE.md is comprehensive
- [ ] No breaking changes to API or frontend

## Post-Implementation
1. Run full test suite
2. Test complete auth flow in browser
3. Update DEV_LOG.md with migration notes
4. Commit changes with message: "feat: migrate auth module to new structure"
5. Continue to next module migration PRP