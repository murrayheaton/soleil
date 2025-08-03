# PRP: Migrate Content Module

## Overview
Migrate all content management and parsing functionality into the content module structure while maintaining backward compatibility.

## Context
- This continues Phase 2 of the modular architecture migration
- Builds on the auth module migration pattern
- Content module handles file parsing, organization, and instrument-based filtering
- Reference: MODULAR_ARCHITECTURE_PROPOSAL.md

## Pre-Implementation Requirements
1. Complete PRP 05 (Auth Module Migration)
2. Ensure all tests pass before starting
3. Continue on branch: `feature/module-structure-foundation`
4. Review all content-related files in current structure

## Implementation Tasks

### 1. Migrate Content Services
- [ ] Copy `app/services/content_parser.py` to `modules/content/services/content_parser.py`
- [ ] Copy `app/services/folder_organizer.py` to `modules/content/services/file_organizer.py`
- [ ] Create `modules/content/services/instrument_filter.py`:
  - [ ] Extract instrument-related logic from content_parser
  - [ ] Create clean interface for instrument filtering
- [ ] Update imports within content module
- [ ] Create `modules/content/services/__init__.py` with public exports

### 2. Migrate Content API Routes
- [ ] Copy `app/api/content.py` to `modules/content/api/content_routes.py`
- [ ] Update route imports to use content module services
- [ ] Create content module router in `modules/content/api/__init__.py`
- [ ] Ensure all content endpoints maintain same interface

### 3. Migrate Content Models
- [ ] Copy `app/models/content.py` to `modules/content/models/content.py`
- [ ] Copy `app/models/folder_structure.py` to `modules/content/models/folder_structure.py`
- [ ] Update model imports in content services
- [ ] Ensure relationships with other models are maintained

### 4. Create Content Module Interface
- [ ] Create `modules/content/__init__.py` with public API:
  ```python
  from .api import content_router
  from .services import ContentParser, FileOrganizer, InstrumentFilter
  from .models import Content, FolderStructure, ParsedFile
  ```
- [ ] Register content module with APIGateway

### 5. Implement Content-Specific Utilities
- [ ] Create `modules/content/utils/` directory
- [ ] Move content-specific helpers:
  - [ ] File type detection utilities
  - [ ] Naming convention helpers
  - [ ] Metadata extraction utilities

### 6. Update Main Application
- [ ] Update imports in `start_server.py` for content routes
- [ ] Create compatibility layer:
  - [ ] `app/services/content_parser.py` imports from `modules.content`
  - [ ] `app/api/content.py` imports from `modules.content`
- [ ] Ensure drive service can still access content parser

### 7. Migrate Frontend Content Code
- [ ] Move content components to `frontend/src/modules/content/components/`
  - [ ] ChartViewer component
  - [ ] AudioPlayer component
  - [ ] FileList component
- [ ] Create content hooks in `frontend/src/modules/content/hooks/`
  - [ ] `useContent` - content fetching and management
  - [ ] `useInstrumentFilter` - instrument-based filtering
- [ ] Move content types to `frontend/src/modules/content/types/`

### 8. Create Content Tests
- [ ] Copy existing content tests to `modules/content/tests/`
- [ ] Add comprehensive tests for:
  - [ ] Content parsing with various file formats
  - [ ] Instrument filtering logic
  - [ ] File organization rules
- [ ] Ensure all tests pass with new structure

### 9. Update Content MODULE.md
- [ ] Document parsing rules and patterns
- [ ] List supported file types and formats
- [ ] Document instrument mapping logic
- [ ] Include examples of common parsing scenarios
- [ ] Add troubleshooting guide for parsing issues

## Validation Steps
1. Run content module tests: `pytest modules/content/tests/`
2. Test content functionality:
   - [ ] File upload and parsing
   - [ ] Instrument-based filtering
   - [ ] Chart viewing
   - [ ] Audio playback
3. Verify file organization still works correctly
4. Test edge cases (unusual file names, formats)

## Success Criteria
- [ ] All content code is migrated to content module
- [ ] File parsing maintains same accuracy
- [ ] Instrument filtering works as before
- [ ] All tests pass
- [ ] Content MODULE.md is comprehensive
- [ ] No breaking changes to functionality

## Post-Implementation
1. Run full test suite
2. Test complete content browsing flow
3. Verify audio and chart viewing work
4. Update DEV_LOG.md with migration notes
5. Commit changes with message: "feat: migrate content module to new structure"