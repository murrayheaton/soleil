# SOLEil Product Vision

# SOLEil - Your Band, Organized

## What is SOLEil?

SOLEil is a modern web app that makes managing band charts, setlists, and gig information effortless. Think of it as your band's digital music folder that's always organized, always accessible, and always up-to-date with assets that only pertain to YOU.

## Who It's For

- **Musicians** who are tired of digging through email attachments for charts
- **Band Leaders** who want to stop being the "chart police" at every gig
- **Music Directors** who need everyone on the same page (literally)

## The SOLEil Experience

Imagine you're a trumpet player. You get a gig notification on your phone. You tap it, and there's everything you need: the setlist, your B♭ charts, the venue address, and even recordings to practice with. No emails, no "hey, can you send me that chart again?" - just music, ready when you are.

## Current Features

### Complete Platform Experience ✅
**Fully Functional**: Musicians have a complete, production-ready platform with professional UI and seamless authentication.

- **Google Authentication**: One-click sign-in with your Google account - no passwords to remember
- **Profile Management**: Set your instrument once, and everything is automatically filtered for your needs
- **Professional Interface**: Clean, musical typography with proper flat symbols (B♭, E♭) and elegant spacing
- **Mobile-Ready Design**: Works perfectly on phones, tablets, and desktops with responsive touch targets

### Smart File Organization ✅ 
**Completely Implemented**: Musicians no longer need to dig through hundreds of files to find their charts.

- **Instrument Intelligence**: Trumpet players see B♭ charts, Alto saxophone players see E♭ charts, rhythm section sees chord charts
- **Automatic Organization**: Files are automatically sorted by song with clean, descriptive names
- **Real-Time Access**: Direct connection to the band Google Drive with instant file access
- **Study Mode**: Split-screen viewing with charts and audio synchronized for practice

### Live Platform Screenshots
The actual SOLEil interface shows this professional, clean design:

**Profile Setup**
```
☀ SOLEil
Sole Power Live
Assets access

Name: [Murray]
Instrument: Alto Sax (E♭)
[View Repertoire] [Sign Out]
```

**Repertoire Browser**
```
Repertoire
E♭  -  247 songs

☀ All Of Me                          6 files  >
☀ Blue Moon                          4 files  >
☀ Don't You Worry 'Bout A Thing     3 files  >
☀ Fly Me To The Moon                5 files  >
```

**Study Mode**
Split-screen with PDF chart on top, audio controls on bottom, download buttons for both chart and audio files.

### Technical Foundation ✅
- **Complete Authentication**: Working Google OAuth2 with session management
- **Production API**: FastAPI backend with file streaming and user management
- **Responsive Frontend**: Next.js with TypeScript, works on all devices
- **Real Google Drive**: Direct integration with pagination for large file collections
- **Professional UI**: Custom typography, musical notation, desaturated color scheme

## What Makes SOLEil Special

1. **It Just Works**: ✅ **COMPLETED** - No complex setup. Sign in with Google and start using immediately.
2. **Instrument Intelligence**: ✅ **COMPLETED** - Knows that trumpet players need B♭ parts, not concert pitch
3. **Professional Design**: ✅ **COMPLETED** - Typography and interface designed specifically for musicians
4. **Beautiful on Any Device**: ✅ **COMPLETED** - Responsive design optimized for phones, tablets, and desktops

## Production Ready Features ✅

All core functionality is complete and working:
- ✅ **Google OAuth authentication** - One-click sign-in
- ✅ **Google Drive integration** - Direct file access with streaming
- ✅ **Smart instrument-based filtering** - See only your relevant charts
- ✅ **User profile management** - Persistent instrument settings
- ✅ **Professional UI design** - Custom branding and musical typography
- ✅ **Mobile-responsive interface** - Works on all screen sizes
- ✅ **Study mode** - Chart viewing with synchronized audio playback
- ✅ **File downloads** - PDF and audio downloads with proper naming

## Technical Architecture Evolution

### Modular Architecture (In Development)
SOLEil is evolving to a modular architecture that enables:
- **Parallel Development**: Multiple developers/AI agents can work on different modules simultaneously
- **Better Scalability**: Each module can be scaled independently based on usage
- **Cleaner Codebase**: Clear boundaries between features reduce complexity
- **Easier Testing**: Module-specific test suites ensure reliability

### Core Modules
1. **Auth Module**: Handles all authentication and user management
2. **Content Module**: Manages file parsing, organization, and metadata
3. **Drive Module**: Google Drive integration with caching and rate limiting
4. **Sync Module**: Real-time updates and WebSocket connections
5. **Dashboard Module**: Aggregates data for the musician dashboard

## Future Enhancements

While the core platform is complete, potential additions include:
- **Offline Mode**: Download charts and audio for venues without WiFi (PWA enhancement)
- **Live Setlist Management**: Real-time setlist updates during performances
- **Multi-Band Support**: Switch between multiple bands seamlessly
- **Push Notifications**: Updates for new charts, gig changes, and announcements
- **Practice Tools**: Loop points, tempo adjustment, and practice tracking
- **Band Communication**: In-app messaging and announcements
- **Analytics Dashboard**: Track which songs are played most, practice time, etc.

---

*SOLEil: Because great music starts with great organization.*

## Development Philosophy

### For Musicians, By Musicians
Every feature in SOLEil is designed with real-world band experience in mind. We understand the chaos of last-minute chart changes, the frustration of missing files, and the need for instant access during performances.

### Open for Extension
The modular architecture ensures that SOLEil can grow with your band's needs. Whether it's integrating with new services, adding custom features, or scaling to support larger organizations, the platform is built to evolve.

### AI-Assisted Development
SOLEil leverages AI agents for development, ensuring consistent code quality, comprehensive testing, and rapid feature delivery while maintaining human oversight for musical domain expertise.


---

# Technical Vision & Feature Set

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


---

# README Product Summary

Soleil provides role-based access to charts, audio references, setlists, and gig information, with intelligent filtering based on instrument types. Musicians get a premium, simple interface while administrators manage everything through familiar Google tools.
