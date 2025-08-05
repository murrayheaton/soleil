# PRP: Implement Module Integration and Cleanup

## Overview
Complete the modular architecture migration by implementing cross-module communication, removing old code, and preparing for multi-agent development.

## Context
- This is the final phase of the modular architecture migration
- All modules have been migrated but need proper integration
- Old code structure needs to be cleaned up
- System needs to be prepared for multi-agent development
- Reference: MODULAR_ARCHITECTURE_PROPOSAL.md

## Pre-Implementation Requirements
1. Complete PRPs 04-07 (all module migrations)
2. Ensure all tests pass
3. Continue on branch: `feature/module-structure-foundation`
4. Document any issues discovered during previous migrations

## Implementation Tasks

### 1. Implement Cross-Module Communication
- [ ] Enhance `modules/core/event_bus.py`:
  ```python
  class EventBus:
      def publish(self, event_type: str, data: dict, source_module: str)
      def subscribe(self, event_type: str, handler: Callable, target_module: str)
      def unsubscribe(self, event_type: str, handler: Callable)
  ```
- [ ] Define standard event types in `modules/core/events.py`:
  - [ ] AUTH_STATE_CHANGED
  - [ ] CONTENT_UPDATED
  - [ ] SYNC_COMPLETED
  - [ ] DRIVE_FILE_CHANGED
- [ ] Implement event handlers in each module

### 2. Complete API Gateway Implementation
- [ ] Enhance `modules/core/api_gateway.py`:
  - [ ] Module registration with health checks
  - [ ] Service discovery mechanism
  - [ ] Module dependency validation
- [ ] Register all modules in main application
- [ ] Add module health endpoints

### 3. Create Module Communication Examples
- [ ] Implement auth → drive communication (OAuth tokens)
- [ ] Implement content → sync communication (file updates)
- [ ] Implement sync → frontend communication (WebSocket events)
- [ ] Document communication patterns

### 4. Remove Old Code Structure
- [ ] Remove duplicate code from `app/services/` (keep compatibility imports)
- [ ] Remove duplicate code from `app/api/` (keep compatibility imports)
- [ ] Update all remaining imports to use modules
- [ ] Clean up unused imports and dependencies

### 5. Implement Module Configuration
- [ ] Create `modules/[module]/config.py` for each module
- [ ] Move module-specific settings from main config
- [ ] Implement configuration validation
- [ ] Support environment-specific configs

### 6. Create Agent Development Tools
- [ ] Create `scripts/generate_module_context.py`:
  - [ ] Generate complete context for a specific module
  - [ ] Include dependencies and interfaces
  - [ ] Output agent-friendly documentation
- [ ] Create `scripts/validate_module.py`:
  - [ ] Check module structure compliance
  - [ ] Validate dependencies
  - [ ] Run module-specific tests

### 7. Implement Module Versioning
- [ ] Add version to each MODULE.md
- [ ] Create compatibility matrix in MODULES.md
- [ ] Document breaking changes process
- [ ] Add version checks in module imports

### 8. Create Integration Tests
- [ ] Create `tests/integration/` directory
- [ ] Test complete user flows across modules:
  - [ ] Login → Browse Files → Play Audio
  - [ ] Upload File → Parse → Sync to Users
  - [ ] WebSocket Connection → Real-time Updates
- [ ] Test module isolation and boundaries

### 9. Update Documentation
- [ ] Create comprehensive MODULES.md with:
  - [ ] Module architecture overview
  - [ ] Dependency graph
  - [ ] Communication patterns
  - [ ] Agent assignment guide
- [ ] Update PLANNING.md with new architecture
- [ ] Create AGENT_GUIDE.md for AI agents
- [ ] Update README.md with module information

### 10. Create Module Dashboard
- [ ] Add `/api/modules` endpoint showing:
  - [ ] Module health status
  - [ ] Version information
  - [ ] Dependencies
  - [ ] Recent events
- [ ] Create simple UI for module monitoring

## Validation Steps
1. Run all module tests independently
2. Run integration tests
3. Test with multiple concurrent users
4. Verify module isolation:
   - [ ] Modify one module without breaking others
   - [ ] Test with module disabled
5. Generate and review module contexts
6. Test agent-friendly documentation

## Success Criteria
- [ ] All modules communicate via EventBus
- [ ] Module boundaries are clearly enforced
- [ ] Old code structure is removed
- [ ] Integration tests pass
- [ ] Module dashboard shows all healthy
- [ ] Agent documentation is complete
- [ ] System is ready for multi-agent development

## Multi-Agent Readiness Checklist
- [ ] Each module has complete MODULE.md
- [ ] Module dependencies are documented
- [ ] Public interfaces are clearly defined
- [ ] Test suites are module-specific
- [ ] Event communication is documented
- [ ] Module context can be generated
- [ ] Agents can work independently

## Post-Implementation
1. Run complete test suite
2. Perform load testing with multiple users
3. Generate context for each module
4. Update all documentation
5. Create PR for review
6. Plan deployment strategy
7. Archive this PRP after successful merge

## Next Steps After Completion
1. Assign agents to specific modules
2. Create module-specific development workflows
3. Implement continuous integration per module
4. Consider microservices architecture for future