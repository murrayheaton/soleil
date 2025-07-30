name: "Google Drive Role-Based File Organization PRP"
description: |
  Complete implementation guide for Google Drive integration with role-based file organization,
  featuring automated folder structures, shortcut creation, and instrument-based access control.

---

## Goal
Implement a Google Drive integration system that automatically organizes band files from a centralized "Source" folder into personalized, role-based folder structures for individual band members, providing intelligent file filtering and organization based on user roles and instrument types.

## Why
- **User Efficiency**: Band members currently manually search through all charts and audio files to find content relevant to their specific instrument/role, leading to inefficiency and confusion
- **Single Source of Truth**: Maintains centralized file management while providing personalized views
- **Scalability**: Designed to work for bands with 5-50+ members across multiple band accounts
- **Real-time Sync**: Automatic organization when new files are added to the source folder
- **Role-based Security**: Each user sees only files appropriate for their instrument/role

## What
Create an automated system that presents each user with a clean, organized view of only the files they need, organized by song, while maintaining a single source of truth in the admin's Google Drive.

### Success Criteria
- [ ] Test account can log into web platform and set trumpet role
- [ ] Test account sees only Bb charts organized by song folders in web interface  
- [ ] Audio files appear in appropriate song folders for download/playback
- [ ] Role can be changed within instrument class from account settings
- [ ] New files in Source folder automatically appear for appropriate users within 30 seconds
- [ ] System handles 100+ files and multiple concurrent users efficiently
- [ ] All unit tests pass with >90% coverage
- [ ] Integration tests demonstrate full workflow

## All Needed Context

### Documentation & References
```yaml
# CRITICAL - Google Drive API Documentation
- url: https://developers.google.com/drive/api/guides/folder
  why: Essential for folder creation and organization patterns
  critical: Shows proper parent folder relationships and batch operations

- url: https://developers.google.com/drive/api/quickstart/python
  why: Python authentication setup and service initialization patterns
  critical: Service account credential handling and scope management

- url: https://stackoverflow.com/questions/66119692/new-google-drive-api-how-to-create-shortcut
  why: Shortcut creation patterns and limitations
  critical: shortcutDetails structure and targetId requirements

- url: https://www.daimto.com/google-drive-api-with-a-service-account/
  why: Service account best practices and folder sharing
  critical: Share folders with service account rather than accessing all Drive content

# EXISTING CODEBASE PATTERNS
- file: /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend/app/services/google_drive.py
  why: Existing Google Drive service with authentication, rate limiting, and batch operations
  critical: Already implements _make_request pattern, RateLimiter, and async context managers

- file: /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend/app/services/content_parser.py
  why: File parsing logic and instrument-key mapping already implemented
  critical: INSTRUMENT_KEY_MAPPING and is_chart_accessible_by_user functions

- file: /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend/app/models/user.py
  why: User model with instrument associations and role management
  critical: User.get_preferred_keys() method and instrument validation

- file: /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend/app/models/content.py
  why: Chart and Audio models with Google Drive integration
  critical: Chart.is_accessible_by_user() method and sync patterns

- file: /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend/tests/test_content_parser.py
  why: Comprehensive test patterns for parsing and role-based access
  critical: Test structure with setup_method, edge cases, and validation requirements
```

### Current Codebase Tree
```bash
soleil/
├── band-platform/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/           # FastAPI routes
│   │   │   ├── models/        # SQLAlchemy + Pydantic models
│   │   │   ├── services/      # Business logic (google_drive.py, content_parser.py)
│   │   │   └── utils/         # Utility functions
│   │   └── tests/             # Pytest test files
│   └── frontend/              # Next.js application
├── PRPs/                      # Product Requirements Prompts
└── CLAUDE.md                  # AI assistant rules and conventions
```

### Desired Codebase Tree with Files to be Added
```bash
soleil/band-platform/backend/app/
├── services/
│   ├── folder_organizer.py    # NEW: Role-based folder organization logic
│   └── file_synchronizer.py  # NEW: Real-time sync between Source and user folders
├── api/
│   ├── folder_management.py   # NEW: API endpoints for folder operations
│   └── role_management.py     # NEW: User role and instrument management endpoints
├── models/
│   └── folder_structure.py    # NEW: Models for tracking folder organization
└── tests/
    ├── test_folder_organizer.py    # NEW: Tests for folder organization
    ├── test_file_synchronizer.py   # NEW: Tests for sync operations
    └── test_role_management.py     # NEW: Tests for role-based access
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Google Drive API Service Account Limitations
# Service accounts have their own Drive space (15GB limit, not upgradable)
# SOLUTION: Share main Drive folders with service account rather than storing files there
# Pattern: Share parent folder with service account email (looks like name@project.iam.gserviceaccount.com)

# CRITICAL: Shortcuts vs Traditional Folders
# Desktop "Backup & Sync" shows shortcuts as .gshortcut files, not true folders
# Web interface works perfectly with shortcuts
# Our use case: Web-only access, so shortcuts are ideal

# CRITICAL: Google Drive API Rate Limits
# 1000 requests per 100 seconds per user
# Our existing RateLimiter in google_drive.py handles this with token bucket algorithm

# CRITICAL: Folder Limits
# Max 500,000 items per folder
# Max 100 levels of nesting
# Our design: Shallow structure (Source -> Song folders -> Files)

# CRITICAL: Batch Operations
# Max 100 requests per batch
# Our existing batch_get_metadata handles this correctly

# CRITICAL: Permission Management
# Files created by service account are owned by service account
# Need to transfer ownership or ensure proper sharing
# Pattern: Create with proper parents, service account retains ownership but folders are shared

# CRITICAL: Async Pattern Usage
# All Google API calls in codebase use async/await with asyncio.run_in_executor
# Existing pattern in GoogleDriveService handles this correctly
```

## Implementation Blueprint

### Data Models and Structure

Role-based organization requires tracking folder relationships and user access patterns:

```python
# NEW: models/folder_structure.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

class UserFolder(Base):
    """
    Tracks user-specific folder organization.
    Each user gets their own folder structure based on their role.
    """
    __tablename__ = "user_folders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    google_folder_id = Column(String(255), nullable=False, index=True)  # User's root folder
    source_folder_id = Column(String(255), nullable=False, index=True)  # Admin's source folder
    last_sync = Column(DateTime, nullable=True)
    sync_status = Column(String(50), default="pending")
    
    # Relationships
    user = relationship("User")
    song_folders = relationship("UserSongFolder", back_populates="user_folder")

class UserSongFolder(Base):
    """
    Tracks individual song folders within user's organization.
    Each song gets its own folder with appropriate shortcuts.
    """
    __tablename__ = "user_song_folders"
    
    id = Column(Integer, primary_key=True)
    user_folder_id = Column(Integer, ForeignKey("user_folders.id"), nullable=False)
    song_title = Column(String(255), nullable=False, index=True)
    google_folder_id = Column(String(255), nullable=False, index=True)
    shortcut_count = Column(Integer, default=0)  # Number of shortcuts in folder
    
    # Relationships  
    user_folder = relationship("UserFolder", back_populates="song_folders")
```

### List of Tasks to be Completed

```yaml
Task 1: Create Folder Organization Service
MODIFY backend/app/services/folder_organizer.py:
  - CREATE new service class that extends existing GoogleDriveService patterns
  - IMPLEMENT create_user_folder_structure() method
  - IMPLEMENT organize_files_by_song() method
  - IMPLEMENT create_shortcuts_for_user() method
  - MIRROR error handling patterns from google_drive.py
  - USE existing RateLimiter and _make_request patterns

Task 2: Create File Synchronization Service  
CREATE backend/app/services/file_synchronizer.py:
  - IMPLEMENT sync_source_to_user_folders() method
  - IMPLEMENT detect_file_changes() using Google Drive API watch
  - IMPLEMENT update_user_shortcuts() method
  - INTEGRATE with existing content_parser.py for file classification
  - USE async patterns consistent with existing services

Task 3: Extend User Model with Folder Management
MODIFY backend/app/models/user.py:
  - ADD get_user_folder_path() method
  - ADD update_role_and_reorganize() method  
  - INTEGRATE with existing get_preferred_keys() logic
  - PRESERVE existing authentication and validation patterns

Task 4: Create Folder Management API Endpoints
CREATE backend/app/api/folder_management.py:
  - IMPLEMENT POST /api/folders/initialize - Create user folder structure
  - IMPLEMENT GET /api/folders/status - Get sync status
  - IMPLEMENT POST /api/folders/sync - Trigger manual sync
  - IMPLEMENT GET /api/folders/contents/{user_id} - Get user's organized files
  - MIRROR auth patterns from existing API files
  - USE existing session management from routes.py

Task 5: Create Role Management API Endpoints  
CREATE backend/app/api/role_management.py:
  - IMPLEMENT PUT /api/users/{user_id}/role - Change user role
  - IMPLEMENT POST /api/users/{user_id}/reorganize - Trigger folder reorganization
  - IMPLEMENT GET /api/users/{user_id}/accessible-files - Get role-appropriate files
  - INTEGRATE with existing user authentication
  - PRESERVE existing validation patterns

Task 6: Update Main API Router
MODIFY backend/app/api/routes.py:
  - ADD router.include_router(folder_management_router, prefix="/folders", tags=["Folders"])
  - ADD router.include_router(role_management_router, prefix="/roles", tags=["Roles"])
  - PRESERVE existing route structure and patterns

Task 7: Create Database Models
CREATE backend/app/models/folder_structure.py:
  - IMPLEMENT UserFolder and UserSongFolder models as specified above
  - ADD Pydantic schemas for API validation
  - FOLLOW existing model patterns from user.py and content.py
  - ADD proper indexes and relationships

Task 8: Create Migration for New Tables
CREATE backend/app/database/migrations/add_folder_structure.py:
  - CREATE migration for UserFolder and UserSongFolder tables
  - ADD proper foreign key constraints
  - ADD indexes for performance
  - FOLLOW existing migration patterns if available
```

### Per Task Pseudocode

```python
# Task 1: Folder Organization Service
class FolderOrganizer(GoogleDriveService):
    async def create_user_folder_structure(self, user: User, source_folder_id: str) -> str:
        # PATTERN: Use existing _make_request and rate limiting
        async with self._get_service() as service:
            # Create root folder for user: "{user.name}'s Files"
            folder_metadata = {
                'name': f"{user.name}'s Files",
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': []  # Root level
            }
            
            # CRITICAL: Share folder with user's email after creation
            await self._make_request(service.files().create(body=folder_metadata).execute)
            await self._share_folder_with_user(folder_id, user.email)
            
            return folder_id
    
    async def organize_files_by_song(self, user_folder_id: str, files: List[Dict], user_instruments: List[str]) -> Dict[str, str]:
        # PATTERN: Group files by song title using existing content_parser
        songs = defaultdict(list)
        for file_data in files:
            parsed = parse_filename(file_data['name'])
            if is_chart_accessible_by_user(parsed.key, user_instruments):
                songs[parsed.song_title].append(file_data)
        
        # PATTERN: Batch create song folders
        song_folders = {}
        for song_title, song_files in songs.items():
            folder_id = await self._create_song_folder(user_folder_id, song_title)
            await self._create_shortcuts_in_folder(folder_id, song_files)
            song_folders[song_title] = folder_id
            
        return song_folders

# Task 2: File Synchronization Service  
class FileSynchronizer:
    async def sync_source_to_user_folders(self, source_folder_id: str) -> None:
        # PATTERN: Use existing process_files_for_sync from GoogleDriveService
        source_files = await self.drive_service.process_files_for_sync(source_folder_id)
        
        # Get all users who need updates
        users = await self._get_users_for_sync()
        
        for user in users:
            # CRITICAL: Only sync files accessible to this user's instruments
            accessible_files = [f for f in source_files 
                              if is_chart_accessible_by_user(f['key'], user.instruments)]
            
            # PATTERN: Use existing batch operations
            await self._update_user_shortcuts(user, accessible_files)
    
    async def detect_file_changes(self, webhook_data: Dict) -> None:
        # PATTERN: Parse webhook data using existing patterns
        # GOTCHA: Google Drive webhooks require HTTPS endpoint
        # PATTERN: Use existing webhook setup from GoogleDriveService
        changed_files = await self._parse_webhook_changes(webhook_data)
        await self.sync_source_to_user_folders(self.source_folder_id)

# Task 4: Folder Management API
@router.post("/initialize", response_model=UserFolderSchema)
async def initialize_user_folders(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session_dependency)
):
    # PATTERN: Follow existing auth patterns from routes.py
    # CRITICAL: Verify user has valid instruments before creating folders
    if not current_user.instruments:
        raise HTTPException(400, "User must have instruments assigned")
    
    organizer = FolderOrganizer(credentials=get_drive_credentials())
    folder_id = await organizer.create_user_folder_structure(
        current_user, 
        current_user.band.google_drive_folder_id
    )
    
    # PATTERN: Create database record following existing model patterns
    user_folder = UserFolder(
        user_id=current_user.id,
        google_folder_id=folder_id,
        source_folder_id=current_user.band.google_drive_folder_id
    )
    session.add(user_folder)
    await session.commit()
    
    return UserFolderSchema.from_orm(user_folder)
```

### Integration Points
```yaml
DATABASE:
  - migration: "CREATE TABLE user_folders, user_song_folders"
  - indexes: "CREATE INDEX idx_user_folder_sync ON user_folders(user_id, sync_status)"
  
CONFIG:
  - add to: app/config.py
  - pattern: "FOLDER_SYNC_INTERVAL = int(os.getenv('FOLDER_SYNC_INTERVAL', '300'))"
  
ROUTES:
  - add to: app/api/routes.py  
  - pattern: "router.include_router(folder_router, prefix='/folders')"
  
BACKGROUND_TASKS:
  - add to: app/main.py
  - pattern: "scheduler.add_job(sync_all_folders, 'interval', minutes=5)"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend
source venv_linux/bin/activate

# CRITICAL: Use venv_linux as specified in CLAUDE.md
python -m ruff check app/services/folder_organizer.py --fix
python -m mypy app/services/folder_organizer.py

# Expected: No errors. If errors, READ the error carefully and fix root cause.
```

### Level 2: Unit Tests
```python
# CREATE test_folder_organizer.py following existing test patterns
class TestFolderOrganizer:
    def setup_method(self):
        """Set up test fixtures following existing pattern."""
        self.organizer = FolderOrganizer()
        self.mock_user = User(
            name="Test User",
            email="test@example.com", 
            instruments=["trumpet"],
            band_id=1
        )
    
    def test_create_user_folder_structure_success(self):
        """Test successful folder creation."""
        # PATTERN: Follow test structure from test_content_parser.py
        with mock.patch.object(self.organizer, '_make_request') as mock_request:
            mock_request.return_value = {'id': 'folder_123'}
            
            folder_id = await self.organizer.create_user_folder_structure(
                self.mock_user, 'source_folder_123'
            )
            
            assert folder_id == 'folder_123'
            assert mock_request.called
    
    def test_organize_files_by_song_filters_by_instrument(self):
        """Test role-based file filtering."""
        # CRITICAL: Verify only Bb charts appear for trumpet player
        files = [
            {'name': 'Song1 - Bb.pdf', 'id': 'file1'},
            {'name': 'Song1 - Eb.pdf', 'id': 'file2'},  # Should be filtered out
            {'name': 'Song1 - Reference.mp3', 'id': 'file3'}
        ]
        
        result = await self.organizer.organize_files_by_song(
            'user_folder_123', files, ['trumpet']
        )
        
        # Should only have Song1 folder with Bb chart and audio
        assert 'Song1' in result
        # Verify file filtering worked correctly

    def test_error_handling_rate_limits(self):
        """Test graceful handling of API rate limits."""
        with mock.patch.object(self.organizer, '_make_request') as mock_request:
            mock_request.side_effect = RateLimitExceeded("Rate limit exceeded")
            
            with pytest.raises(RateLimitExceeded):
                await self.organizer.create_user_folder_structure(
                    self.mock_user, 'source_123'
                )

    def test_shortcut_creation_batch_operations(self):
        """Test efficient batch shortcut creation."""
        # CRITICAL: Verify batch operations stay under 100 request limit
        files = [{'id': f'file_{i}', 'name': f'Song{i} - Bb.pdf'} for i in range(150)]
        
        with mock.patch.object(self.organizer, '_make_request') as mock_request:
            await self.organizer._create_shortcuts_in_folder('folder_123', files)
            
            # Should batch requests to stay under API limits
            assert mock_request.call_count <= math.ceil(150 / 100)
```

```bash
# Run tests with existing patterns
cd /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend
source venv_linux/bin/activate
python -m pytest tests/test_folder_organizer.py -v

# Expected: All tests pass. If failing, debug each test individually:
python -m pytest tests/test_folder_organizer.py::TestFolderOrganizer::test_create_user_folder_structure_success -v -s
```

### Level 3: Integration Test
```bash
# Start the development server
cd /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend
source venv_linux/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test folder initialization endpoint
curl -X POST http://localhost:8000/api/folders/initialize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {test_token}" \
  -d '{}'

# Expected: {"folder_id": "...", "status": "created", "song_count": 0}

# Test sync trigger endpoint  
curl -X POST http://localhost:8000/api/folders/sync \
  -H "Authorization: Bearer {test_token}"

# Expected: {"status": "sync_started", "estimated_duration": "30s"}

# Test role change with reorganization
curl -X PUT http://localhost:8000/api/users/1/role \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {test_token}" \
  -d '{"role": "alto_sax", "reorganize_folders": true}'

# Expected: {"status": "updated", "new_accessible_files": 15}
```

## Final Validation Checklist
- [ ] All tests pass: `python -m pytest tests/ -v`
- [ ] No linting errors: `python -m ruff check app/`
- [ ] No type errors: `python -m mypy app/`
- [ ] Manual API tests successful with curl commands above
- [ ] Role changes trigger proper folder reorganization
- [ ] New files in source folder appear in user folders within 30 seconds
- [ ] Error cases handled gracefully (rate limits, permission errors)
- [ ] Logs are informative but not verbose
- [ ] Database migrations run successfully
- [ ] Integration with existing authentication system works

---

## Anti-Patterns to Avoid
- ❌ Don't create shortcuts to files users can't access (defeats purpose)
- ❌ Don't bypass existing rate limiting - reuse GoogleDriveService patterns  
- ❌ Don't create deep folder nesting (Google has 100 level limit)
- ❌ Don't store files in service account Drive (15GB limit)
- ❌ Don't ignore webhook failures - implement retry logic
- ❌ Don't create more than 500,000 items per folder
- ❌ Don't hardcode folder names - make them configurable
- ❌ Don't skip user permission validation before folder creation
- ❌ Don't forget to transfer folder ownership after creation
- ❌ Don't ignore the existing async patterns in the codebase

## PRP Quality Score: 9/10

**Confidence Level**: Very High - This PRP provides comprehensive context including:
- ✅ All necessary Google Drive API documentation with specific URLs
- ✅ Complete analysis of existing codebase patterns to follow
- ✅ Detailed implementation tasks with pseudocode
- ✅ Executable validation gates with specific commands
- ✅ Real codebase examples and gotchas identified through research
- ✅ Integration points clearly defined
- ✅ Testing patterns that mirror existing test structure

The only minor gap is that webhook setup requires HTTPS endpoints which may need additional infrastructure setup, but this is clearly documented in the gotchas section.