## FEATURE:

A web and mobile platform for band/gig management that serves as a curated wrapper around Google Workspace, designed for both band administrators and musicians. The platform provides role-based access to charts, audio references, setlists, and gig information, with intelligent filtering based on instrument types and user roles.

**Core Functionality:**
- **For Musicians**: Simple, premium interface to access their specific charts, gig details, setlists, and reference materials
- **For Admins**: Manage all content through familiar Google Workspace tools (Drive, Sheets, Calendar)
- **Smart Filtering**: Musicians only see content relevant to their instrument (e.g., trumpet players automatically get Bb charts)
- **Multi-Device**: Progressive Web App that works seamlessly on desktop, tablet, and mobile
- **Offline Support**: Download charts and audio for gigs to use without internet

**Key Technical Requirements:**
- Google Workspace integration (Drive for files, Sheets for setlists/data, Calendar for schedule)
- Intelligent file tagging system based on naming conventions (e.g., "Song Title - Bb.pdf")
- Real-time sync from Google sources to app database
- Role-based access control with instrument-to-transposition mapping
- PWA for cross-platform compatibility
- Beautiful, musician-friendly UI that feels premium

## EXAMPLES:

Since this is a new project, we'll use the template's existing examples for patterns:

- `examples/agent/` - Reference for modular code organization and dependency injection patterns
- `examples/cli.py` - Use async patterns and error handling approaches (though we're building a web app, not CLI)
- The modular structure demonstrated in examples for organizing our sync engine, API, and frontend services

**File Organization Pattern in Google Drive (for context):**
```
Band Google Drive/
├── Charts/
│   ├── All of Me - Bb.pdf
│   ├── All of Me - Eb.pdf
│   ├── All of Me - C.pdf
│   └── Spain - Rhythm.pdf
├── Audio References/
│   ├── All of Me - Reference.mp3
│   └── Spain - Reference.mp3
├── Setlists/ (Google Sheets)
│   └── 2024 Gigs Setlists
└── Gig Info/ (Google Sheets)
    └── 2024 Gig Database
```

## DOCUMENTATION:

**Google APIs:**
- https://developers.google.com/drive/api/v3/quickstart/python - Drive API for file access
- https://developers.google.com/sheets/api/quickstart/python - Sheets API for setlist/data
- https://developers.google.com/calendar/api/quickstart/python - Calendar API for schedule
- https://developers.google.com/drive/api/v3/push-notifications - For real-time sync

**PWA & Mobile:**
- https://web.dev/progressive-web-apps/ - PWA best practices
- https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API - Offline functionality
- https://web.dev/indexeddb/ - Local storage for offline charts

**Backend Framework:**
- https://fastapi.tiangolo.com/ - FastAPI for Python backend
- https://docs.sqlalchemy.org/ - SQLAlchemy for database
- https://python-socketio.readthedocs.io/ - For real-time updates
- https://docs.celeryq.dev/ - Background tasks for syncing

**Frontend:**
- https://nextjs.org/docs - Next.js for React + PWA
- https://tailwindcss.com/docs - Tailwind for styling
- https://react-query-v3.tanstack.com/ - Data fetching and caching
- https://react-pdf.org/ - PDF viewing in browser

**Similar Platforms (for inspiration):**
- Planning Centre: https://www.planningcenter.com/services
- OnSong: https://onsongapp.com/
- MasterTour: https://mastertour.net/

## OTHER CONSIDERATIONS:

**Authentication & Security:**
- Start with simple email/password auth
- Each user has a profile with their instrument(s) defined
- Session management for web and mobile
- Consider Google OAuth in the future for seamless integration

**Instrument Mapping Logic:**
The app needs to understand instrument transpositions:
```
Trumpet → Bb
Alto Sax → Eb  
Tenor Sax → Bb
Baritone Sax → Eb
French Horn → F
Trombone/Piano/Bass/Guitar → C
```

**File Naming Conventions:**
- Charts: `[Song Title] - [Key].pdf` (e.g., "All of Me - Bb.pdf")
- Audio: `[Song Title] - Reference.mp3`
- The system parses filenames to auto-tag content

**Google Sheets Structure:**
- Setlist Sheet: Order | Song Title | Key | Duration | Notes
- Gig Database: Date | Venue | Load-in | Downbeat | Dress Code | Personnel | Notes

**Critical Features Often Missed:**
- **Offline Mode**: Musicians NEED access without WiFi at venues
- **Fast Load Times**: Musicians pull up charts seconds before playing
- **Large File Support**: Some charts are high-res scans
- **Print Capability**: Sometimes musicians need physical copies
- **Dark Mode**: For dark stages and pit orchestras
- **Zoom/Pan on PDFs**: Especially important on phones
- **Setlist Changes**: Must sync quickly when changed in Google Sheets

**Performance Requirements:**
- Charts must load in <2 seconds
- Search must be instant (client-side when possible)
- Sync from Google should happen in background
- Mobile app should feel native-smooth

**Scalability Considerations:**
- Design database for multi-tenant use from the start
- Consider how to handle multiple bands/organizations later
- File storage strategy for growth (CDN for static assets)
- Rate limiting for Google API calls

**Development Approach:**
- Start with core sync engine and database
- Build API with clear separation of concerns
- Create mobile-first PWA frontend
- Add offline support as enhancement
- Include comprehensive logging for debugging sync issues

**Testing Requirements:**
- Unit tests for sync engine logic
- Integration tests for Google API interactions
- E2E tests for critical user flows
- Performance tests for file loading
- Offline functionality tests