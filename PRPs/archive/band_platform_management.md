name: "Band Platform Management System - Google Workspace Integration PWA"
description: |

## Purpose
Build a comprehensive band management platform that serves as a curated wrapper around Google Workspace, providing role-based access to charts, audio references, setlists, and gig information with intelligent filtering and offline support.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a production-ready Progressive Web App that integrates with Google Workspace APIs (Drive, Sheets, Calendar) to provide musicians and band administrators with intelligent, role-based access to band materials, with offline support and mobile-first design.

## Why
- **Business value**: Streamlines band management workflows and improves musician experience at gigs
- **Integration**: Leverages existing Google Workspace infrastructure bands already use
- **Problems solved**: Musicians need quick access to their specific charts without WiFi, admins need centralized content management

## What
A PWA system with:
- **Backend**: FastAPI with Google Workspace APIs integration, real-time sync engine, and role-based access control
- **Frontend**: Next.js PWA with offline PDF/audio storage, instrument-based filtering, and mobile-first UI
- **Sync Engine**: Real-time synchronization from Google Drive/Sheets with intelligent file parsing and tagging

### Success Criteria
- [ ] Google Workspace APIs authenticate and sync files/data in real-time
- [ ] Musicians see only their instrument-specific charts (e.g., trumpet players get Bb charts)
- [ ] PWA works offline with downloaded charts and audio references
- [ ] Admin interface manages content through familiar Google Workspace tools
- [ ] Mobile-first UI loads charts in <2 seconds and feels native-smooth
- [ ] Multi-tenant architecture supports multiple bands/organizations

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://developers.google.com/drive/api/v3/quickstart/python
  why: Core Drive API integration for file access and real-time sync
  critical: Use batch operations and implement exponential backoff for 429/503 errors
  
- url: https://developers.google.com/sheets/api/quickstart/python
  why: Sheets API for setlist and gig database management
  critical: Use spreadsheets.values collection for performance, batch operations reduce HTTP overhead
  
- url: https://developers.google.com/calendar/api/quickstart/python
  why: Calendar API for gig scheduling integration
  critical: Handle timezone properly and use proper scopes for read/write operations
  
- url: https://developers.google.com/drive/api/v3/push-notifications
  why: Real-time file sync implementation with webhooks
  critical: Requires HTTPS endpoints, implement token verification, handle 1 event/sec Gmail limit
  
- url: https://web.dev/progressive-web-apps/
  why: PWA best practices for offline functionality and native app feel
  critical: Service workers, manifest.json, and caching strategies for large files
  
- url: https://web.dev/indexeddb/
  why: Offline storage for charts and audio files
  critical: Use IDB-Keyval or Dexie.js for simpler syntax, implement delta sync
  
- url: https://fastapi.tiangolo.com/
  why: FastAPI backend patterns for async operations and WebSocket support
  critical: Use async/await consistently, implement proper dependency injection
  
- url: https://nextjs.org/docs
  why: Next.js PWA implementation with service workers
  critical: API routes integration with FastAPI, proper PWA manifest configuration
  
- file: use-cases/pydantic-ai/examples/main_agent_reference/cli.py
  why: Async patterns, error handling, and streaming response patterns
  critical: Real-time updates and WebSocket integration patterns
  
- file: PRPs/templates/prp_base.md
  why: Follow established PRP structure and validation patterns
  critical: Implement all validation loops and anti-patterns avoidance
```

### Current Codebase Structure
```bash
soleil/
├── band-platform/
│   ├── backend/
│   │   ├── app/
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── frontend/
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   └── next.config.ts
│   └── docker-compose.yml
├── CLAUDE.md
├── PRPs/
│   ├── active/
│   ├── archive/
│   └── templates/
└── INITIAL_soleil.md
```

### Desired Codebase Structure with New Files
```bash
band-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app with CORS, middleware
│   │   ├── config.py                  # Settings with Google API credentials
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User, Band, Instrument models
│   │   │   ├── content.py            # Chart, Audio, Setlist models
│   │   │   └── sync.py               # Sync status and metadata models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── google_drive.py       # Drive API integration with batch ops
│   │   │   ├── google_sheets.py      # Sheets API with setlist/gig parsing
│   │   │   ├── google_calendar.py    # Calendar API integration
│   │   │   ├── sync_engine.py        # Real-time sync with webhooks
│   │   │   ├── auth_service.py       # JWT + Google OAuth integration
│   │   │   └── content_parser.py     # File naming convention parsing
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # Main API routes
│   │   │   ├── auth.py               # Authentication endpoints
│   │   │   ├── content.py            # Content CRUD operations
│   │   │   ├── sync.py               # Sync status endpoints
│   │   │   └── websocket.py          # Real-time updates via WebSocket
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py         # SQLAlchemy setup
│   │   │   └── migrations/           # Alembic migrations
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_utils.py         # File processing utilities
│   │       └── rate_limiter.py       # Google API rate limiting
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_sync_engine.py       # Sync engine unit tests
│   │   ├── test_google_apis.py       # API integration tests
│   │   └── test_content_parser.py    # File parsing tests
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
├── frontend/
│   ├── public/
│   │   ├── manifest.json             # PWA manifest with band icons
│   │   └── sw.js                     # Service worker for offline support
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   │   ├── ChartViewer.tsx   # PDF viewer with zoom/pan
│   │   │   │   └── ChartList.tsx     # Filterable chart listing
│   │   │   ├── audio/
│   │   │   │   └── AudioPlayer.tsx   # Reference audio player
│   │   │   ├── setlists/
│   │   │   │   └── SetlistView.tsx   # Real-time setlist display
│   │   │   └── common/
│   │   │       ├── Layout.tsx        # Mobile-first layout
│   │   │       └── OfflineIndicator.tsx
│   │   ├── pages/
│   │   │   ├── index.tsx             # Dashboard with role-based content
│   │   │   ├── charts.tsx            # Chart library view
│   │   │   ├── setlists.tsx          # Setlist management
│   │   │   ├── gigs.tsx              # Gig calendar view
│   │   │   └── admin.tsx             # Admin panel for content management
│   │   ├── services/
│   │   │   ├── api.ts                # FastAPI client with auth
│   │   │   ├── offline.ts            # IndexedDB storage management
│   │   │   └── websocket.ts          # Real-time updates client
│   │   ├── utils/
│   │   │   ├── auth.ts               # JWT token management
│   │   │   └── instruments.ts        # Instrument-to-key mapping logic
│   │   └── styles/
│   │       └── globals.css           # Tailwind with dark mode support
│   ├── package.json
│   ├── next.config.js                # PWA configuration
│   └── tailwind.config.js
├── docker-compose.yml                # Development environment
├── README.md
└── .env.example
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Google APIs require specific authentication patterns
# Example: Drive API requires OAuth 2.0 with offline access for refresh tokens
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# GOTCHA: Google APIs have strict rate limits
# Drive API: 1,000 requests per 100 seconds per user
# Sheets API: 300 requests per 100 seconds per user  
# MUST implement exponential backoff for 429/503 responses

# CRITICAL: FastAPI requires async consistency
# All database operations must be async when using async endpoints
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# GOTCHA: Next.js PWA requires specific configuration
# Service worker must be registered properly and manifest.json configured
# IndexedDB storage has quotas (usually ~50% of available disk space)

# CRITICAL: File naming convention parsing is core to the system
# Pattern: "Song Title - Key.pdf" or "Song Title - Reference.mp3"
# Must handle edge cases like multiple hyphens, special characters

# GOTCHA: WebSocket connections need proper cleanup and reconnection logic
# Mobile browsers may kill connections when app goes to background
```

## Implementation Blueprint

### Data Models and Structure

Create the core data models to ensure type safety and consistency:

```python
# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    instruments = Column(JSON)  # List of instrument names
    band_id = Column(Integer, ForeignKey("bands.id"))
    role = Column(String, default="musician")  # musician, admin
    created_at = Column(DateTime, default=datetime.utcnow)
    
    band = relationship("Band", back_populates="members")

class Band(Base):
    __tablename__ = "bands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    google_drive_folder_id = Column(String)
    google_sheets_id = Column(String)
    google_calendar_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    members = relationship("User", back_populates="band")

# Pydantic schemas for API validation
class UserSchema(BaseModel):
    id: int
    email: str
    name: str
    instruments: List[str]
    role: str
    
    class Config:
        orm_mode = True
```

### List of Tasks to Complete the PRP (in order)

```yaml
Task 1 - Project Setup:
  CREATE backend/app/main.py:
    - IMPLEMENT FastAPI app with CORS middleware
    - ADD WebSocket support for real-time updates
    - CONFIGURE Google API credentials loading
    - PATTERN: Follow FastAPI official async patterns

Task 2 - Database Layer:
  CREATE backend/app/database/connection.py:
    - SETUP SQLAlchemy with async engine
    - IMPLEMENT connection pooling
    - PATTERN: Mirror async database patterns from existing examples
  
  CREATE backend/app/models/:
    - DEFINE User, Band, Chart, Audio, Setlist models
    - IMPLEMENT Pydantic schemas for validation
    - ADD proper relationships and indexes

Task 3 - Google APIs Integration:
  CREATE backend/app/services/google_drive.py:
    - IMPLEMENT OAuth 2.0 authentication flow
    - ADD batch file listing and metadata extraction
    - IMPLEMENT webhook endpoint for real-time sync
    - PATTERN: Use exponential backoff for rate limiting
  
  CREATE backend/app/services/google_sheets.py:
    - IMPLEMENT setlist and gig data parsing
    - ADD batch read operations for performance
    - HANDLE timezone conversion for gig dates

Task 4 - Content Intelligence:
  CREATE backend/app/services/content_parser.py:
    - IMPLEMENT file naming convention parsing
    - ADD instrument-to-key mapping logic (Trumpet→Bb, Alto Sax→Eb)
    - HANDLE edge cases in file names
    - PATTERN: Use regex with comprehensive test coverage

Task 5 - Real-time Sync Engine:
  CREATE backend/app/services/sync_engine.py:
    - IMPLEMENT Google Drive webhook processing
    - ADD delta sync to minimize API calls
    - HANDLE concurrent sync operations safely
    - PATTERN: Use async queues for batch processing

Task 6 - API Endpoints:
  CREATE backend/app/api/routes.py:
    - IMPLEMENT role-based content filtering
    - ADD file streaming for large PDFs/audio
    - INCLUDE proper error handling with status codes
    - PATTERN: Use FastAPI dependency injection

Task 7 - Authentication System:
  CREATE backend/app/services/auth_service.py:
    - IMPLEMENT JWT token generation and validation
    - ADD Google OAuth integration for seamless login
    - HANDLE refresh token management
    - PATTERN: Use secure HttpOnly cookies for token storage

Task 8 - Frontend PWA Structure:
  CREATE frontend/src/components/charts/ChartViewer.tsx:
    - IMPLEMENT PDF viewer with zoom/pan functionality
    - ADD touch gestures for mobile navigation
    - INCLUDE offline download capability
    - PATTERN: Use react-pdf with custom controls

Task 9 - Offline Storage:
  CREATE frontend/src/services/offline.ts:
    - IMPLEMENT IndexedDB wrapper with IDB-Keyval
    - ADD intelligent caching strategy for charts/audio
    - HANDLE storage quota management
    - PATTERN: Use delta sync with compression

Task 10 - Real-time Updates:
  CREATE frontend/src/services/websocket.ts:
    - IMPLEMENT WebSocket client with reconnection logic
    - ADD connection state management
    - HANDLE background/foreground app state changes
    - PATTERN: Use event-driven updates to UI components

Task 11 - Mobile-First UI:
  CREATE frontend/src/components/common/Layout.tsx:
    - IMPLEMENT responsive navigation with bottom tabs
    - ADD dark mode support for stage use
    - INCLUDE touch-friendly controls (44px minimum)
    - PATTERN: Use Tailwind with mobile-first breakpoints

Task 12 - PWA Configuration:
  CREATE frontend/public/manifest.json:
    - CONFIGURE PWA manifest with proper icons
    - ADD install prompts and splash screens
    - SET proper cache strategies
  
  CREATE frontend/public/sw.js:
    - IMPLEMENT service worker for offline functionality
    - ADD background sync for when connection returns
    - HANDLE file caching with size limits

Task 13 - Testing Suite:
  CREATE backend/tests/:
    - IMPLEMENT unit tests for sync engine logic
    - ADD integration tests for Google API calls
    - TEST file parsing edge cases
    - PATTERN: Use pytest with async test support
  
  CREATE frontend/src/tests/:
    - IMPLEMENT component tests with React Testing Library
    - ADD PWA functionality tests
    - TEST offline behavior scenarios

Task 14 - Performance Optimization:
  OPTIMIZE backend/app/services/:
    - IMPLEMENT Redis caching for frequently accessed data
    - ADD API response compression
    - OPTIMIZE database queries with proper indexes
  
  OPTIMIZE frontend/src/:
    - IMPLEMENT lazy loading for charts and components
    - ADD image optimization for chart thumbnails
    - MINIMIZE bundle size with code splitting

Task 15 - Deployment Configuration:
  CREATE docker-compose.yml:
    - SETUP development environment with PostgreSQL
    - ADD Redis for caching and session storage
    - INCLUDE nginx for static file serving
  
  CREATE production deployment configs:
    - SETUP environment variable templates
    - ADD health check endpoints
    - IMPLEMENT logging and monitoring
```

### Integration Points
```yaml
DATABASE:
  - migration: "CREATE EXTENSION IF NOT EXISTS 'uuid-ossp'"
  - indexes: "CREATE INDEX idx_user_instruments ON users USING GIN (instruments)"
  - pattern: "Use async SQLAlchemy sessions throughout"
  
CONFIG:
  - add to: backend/app/config.py
  - pattern: "Use pydantic-settings with .env file loading"
  - required: "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET_KEY"
  
ROUTES:
  - add to: backend/app/main.py
  - pattern: "app.include_router(auth_router, prefix='/api/auth')"
  - middleware: "Add JWT authentication middleware for protected routes"

FRONTEND_INTEGRATION:
  - api_client: "Implement typed API client with automatic token refresh"
  - websocket: "Connect to backend WebSocket for real-time setlist updates"
  - offline: "Sync local IndexedDB with server when connection available"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Backend validation
cd backend && python -m venv venv_linux && source venv_linux/bin/activate
pip install -r requirements.txt
ruff check app/ --fix
mypy app/
# Expected: No errors. Fix any type issues before proceeding.

# Frontend validation  
cd frontend
npm install
npm run lint
npm run type-check
# Expected: No linting or TypeScript errors.
```

### Level 2: Unit Tests
```python
# CREATE backend/tests/test_content_parser.py
def test_file_parsing_standard_format():
    """Test parsing standard format: 'Song Title - Bb.pdf'"""
    result = parse_filename("All of Me - Bb.pdf")
    assert result.song_title == "All of Me"
    assert result.key == "Bb"
    assert result.file_type == "chart"

def test_instrument_key_mapping():
    """Test instrument to key mapping logic"""
    user = User(instruments=["trumpet", "flugelhorn"])
    charts = get_charts_for_user(user)
    # Should only return Bb charts
    assert all(chart.key == "Bb" for chart in charts)

def test_google_api_rate_limiting():
    """Test exponential backoff implementation"""
    with mock.patch('google_drive_service.files().list', side_effect=HttpError(429)):
        result = sync_drive_files()
        # Should retry with exponential backoff
        assert result.retry_count > 0

def test_offline_storage():
    """Test IndexedDB storage and retrieval"""
    chart_data = {"title": "All of Me", "content": b"PDF_CONTENT"}
    await store_chart_offline(chart_data)
    retrieved = await get_chart_offline("All of Me")
    assert retrieved["title"] == "All of Me"
```

```bash
# Run and iterate until passing:
cd backend && source venv_linux/bin/activate
pytest tests/ -v --asyncio-mode=auto
# If failing: Read error, understand root cause, fix code, re-run

cd frontend
npm test
# Test PWA functionality, offline behavior, and UI components
```

### Level 3: Integration Test
```bash
# Start the development environment
docker-compose up -d
# This starts PostgreSQL, Redis, and the backend API

# Test Google API integration
curl -X POST http://localhost:8000/api/sync/drive \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json"
# Expected: {"status": "sync_started", "files_found": 42}

# Test WebSocket connection
curl -X GET http://localhost:8000/api/ws/test
# Expected: WebSocket connection established

# Test PWA offline functionality
# 1. Load the app in browser
# 2. Go offline (disable network)
# 3. Verify charts still load from IndexedDB
# 4. Verify "offline" indicator appears
# Expected: Charts load, offline mode works

# Test mobile responsiveness
# 1. Open Chrome DevTools mobile view
# 2. Test touch gestures on PDF viewer
# 3. Verify bottom navigation works
# Expected: Touch-friendly, fast loading (<2s)
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v && npm test`
- [ ] No linting errors: `ruff check app/ && npm run lint`
- [ ] No type errors: `mypy app/ && npm run type-check`
- [ ] Google APIs authenticate successfully
- [ ] Real-time sync works with Drive/Sheets webhooks
- [ ] PWA installs and works offline
- [ ] Mobile UI is touch-friendly and loads quickly
- [ ] Role-based filtering shows correct charts per instrument
- [ ] WebSocket real-time updates work
- [ ] File uploads handle large PDFs/audio files
- [ ] Error cases handled gracefully with user feedback
- [ ] Performance meets <2s chart loading requirement

---

## Anti-Patterns to Avoid
- ❌ Don't use sync operations in async FastAPI endpoints
- ❌ Don't ignore Google API rate limits - implement proper backoff
- ❌ Don't store sensitive credentials in code - use environment variables
- ❌ Don't skip PWA manifest configuration - required for install prompts
- ❌ Don't hardcode instrument mappings - make them configurable
- ❌ Don't skip WebSocket reconnection logic - mobile connections drop frequently
- ❌ Don't ignore IndexedDB storage quotas - implement cleanup strategies
- ❌ Don't skip mobile testing - this is a mobile-first application
- ❌ Don't use complex state management without proper error boundaries
- ❌ Don't skip real-time sync testing - data consistency is critical

## Performance Requirements Validation
- Charts must load in <2 seconds (test with 5MB PDF files)
- Search must be instant (client-side filtering when possible)
- PWA must feel native-smooth (60fps animations, proper touch handling)
- Sync must handle 1000+ files without blocking UI
- WebSocket updates must propagate in <500ms
- Offline mode must work for 7+ days with typical usage

**PRP Quality Score: 9/10** - Comprehensive context, executable validation loops, follows codebase patterns, includes all critical technical details for one-pass implementation success. The only missing element is a live staging environment for final integration testing.