---
name: "execute-soleil-prp"
description: "Execute Soleil Band Platform PRP with component validation and functionality testing"
---

## Purpose

Execute a Soleil Band Platform PRP (Problem Resolution Process) with comprehensive validation of both new implementations and preserved existing functionality, ensuring all components work together seamlessly.

## Usage

```bash
/execute-soleil-prp <prp_file>
```

Where `<prp_file>` is the path to a generated Soleil PRP document.

## Core Functionality

This command executes a Soleil PRP with special focus on:

1. **Preserving existing functionality** throughout implementation
2. **Validating component integration** between new and existing code
3. **Testing Google Workspace API integrations** against production patterns
4. **Ensuring PWA capabilities** remain functional during development
5. **Verifying template compliance** without breaking working features
6. **Running comprehensive test suites** for both backend and frontend

## Execution Process

### Phase 1: Pre-Implementation Validation
- Verify existing functionality is working before changes
- Run current test suites to establish baseline
- Document current component state for regression testing
- Validate Google API connections and authentication flows

### Phase 2: Incremental Implementation
- Implement changes in small, testable increments
- Preserve existing functionality at each step
- Apply template patterns gradually to existing code
- Maintain component interfaces to prevent breaking changes

### Phase 3: Component Integration Testing
- Test new features with existing authentication system
- Validate Google Workspace API integration continuity
- Ensure PWA capabilities remain functional
- Verify offline storage and sync mechanisms

### Phase 4: Comprehensive Validation
- Run full test suite including preserved functionality
- Test Google API rate limiting and error handling
- Validate PWA installation and offline capabilities
- Confirm template compliance without functionality loss

## Validation Loops

### Existing Functionality Regression Testing
```bash
# Backend service validation
cd examples/band-platform/backend && python -m pytest tests/ -v

# Frontend component validation  
cd examples/band-platform/frontend && npm test

# Google API integration validation
python -c "from examples.band_platform.backend.app.services.google_drive import GoogleDriveService; print('Google API accessible')"

# PWA functionality validation
cd examples/band-platform/frontend && npm run build && npm run start
```

### New Feature Validation
```bash
# Feature-specific test execution
pytest tests/test_[feature_name].py -v

# Integration testing with existing components
pytest tests/test_integration_[feature_name].py -v

# API endpoint validation
curl -X GET "http://localhost:8000/api/[endpoint]" -H "Authorization: Bearer [token]"
```

### Template Compliance Validation
```bash
# Code quality checks
ruff check --select E,W,F app/
mypy app/ --ignore-missing-imports

# Documentation validation
grep -r "TODO\|FIXME\|HACK" app/ || echo "No TODO markers found"

# Security validation
bandit -r app/ -f json
```

## Execution Strategy

### Development Environment Focus
- All work stays within `soleil-rebuild/` project structure
- Changes applied incrementally to preserve stability
- Existing `examples/` folder used as component source
- Template patterns adopted without breaking functionality

### Component Preservation Approach
1. **Authentication Systems** - Maintain OAuth flows and session management
2. **Google API Services** - Preserve Drive, Sheets, Calendar integration
3. **PWA Infrastructure** - Keep service workers and offline capabilities
4. **UI Components** - Maintain chart viewer, audio player, dashboard
5. **Database Models** - Preserve user profiles and content organization
6. **Deployment Configuration** - Keep Docker, nginx, SSL setup functional

### Integration Testing Strategy
- Test preserved components with new features
- Validate authentication flows remain functional
- Ensure Google API integrations continue working
- Confirm PWA capabilities survive changes
- Verify deployment processes remain stable

## Success Criteria Validation

### Feature Implementation Success
- [ ] New feature implemented according to PRP specification
- [ ] Integration with existing codebase completed
- [ ] Template compliance achieved incrementally
- [ ] Documentation updated with implementation details

### Existing Functionality Preservation
- [ ] All existing tests continue passing
- [ ] Authentication and session management unchanged
- [ ] Google Workspace API integration functional
- [ ] PWA capabilities preserved (offline, installation, caching)
- [ ] UI components maintain previous functionality
- [ ] Database operations continue working
- [ ] Deployment processes remain stable

### Template Compliance Achievement
- [ ] Code follows template-generator guidelines
- [ ] Documentation standards met
- [ ] Security best practices implemented
- [ ] Error handling comprehensive
- [ ] Validation loops executable

## Error Handling and Recovery

### Functionality Regression Detection
```bash
# Automated regression testing
./run_regression_tests.sh || echo "REGRESSION DETECTED - HALT IMPLEMENTATION"

# Manual functionality verification
./verify_google_api_connection.sh
./verify_pwa_functionality.sh  
./verify_authentication_flow.sh
```

### Recovery Procedures
- Immediate rollback to last known working state
- Component-by-component restoration
- Incremental re-application of changes
- Enhanced testing before retry

## Integration Points

### Google Workspace APIs
- Drive API v3 with existing authentication
- Sheets API for setlist management  
- Calendar API for gig scheduling
- OAuth 2.0 flow preservation

### PWA Infrastructure
- Next.js with next-pwa configuration
- Service worker functionality
- IndexedDB offline storage
- Manifest and installation support

### Backend Services
- FastAPI with existing middleware
- SQLAlchemy database integration
- Real-time WebSocket connections
- Background task processing

## Anti-Patterns Avoided

- ❌ Implementing without regression testing
- ❌ Breaking existing authentication flows
- ❌ Disrupting Google API integrations
- ❌ Removing PWA capabilities during development
- ❌ Ignoring existing test suites
- ❌ Template compliance at the expense of functionality
- ❌ Large-scale changes without incremental validation

This command ensures every Soleil PRP execution maintains the stability and functionality of the existing band platform while systematically implementing improvements.