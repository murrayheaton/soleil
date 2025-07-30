# INITIAL: Google Drive Integration with Role-Based File Organization

## 🎯 Feature Overview

Implement a Google Drive integration system that automatically organizes band files from a centralized "Source" folder into personalized, role-based folder structures for individual band members. The system should provide intelligent file filtering and organization based on user roles and instrument types.

## 🎵 Business Context

**Problem**: Band members currently need to manually search through all charts and audio files to find content relevant to their specific instrument/role, leading to inefficiency and confusion.

**Solution**: Create an automated system that presents each user with a clean, organized view of only the files they need, organized by song, while maintaining a single source of truth in the admin's Google Drive.

## 👥 User Stories

### Primary User (Test Account - Trumpet Player)
- As a trumpet player, I want to see folders organized by song title
- Each song folder should contain only Bb transposition charts and audio files
- I should not see charts for other instruments cluttering my view
- I want to access this through the band platform web interface (no Google account connection required)

### Band Administrator  
- As a band admin, I want to upload files to a single "Source" folder
- The system should automatically create shortcuts in member folders based on their roles
- I want to manage which members see which types of content

### General Band Member
- As a band member, I want to set my instrument role on first login to the web platform
- I want to change my role from account settings if needed (within my permission class)
- I want to view and download my role-appropriate files through the web interface

## 🏗️ Technical Requirements

### Google Drive Integration
- **Primary Account**: murray@projectbrass.live (backend service account only)
- **Authentication**: Service account authentication (no user Google account linking required)
- **Permissions**: Backend read access to specific band Drive folders
- **API Usage**: Google Drive API v3 for file operations and content serving
- **User Access**: Through web platform interface, not direct Drive access

### File Organization Structure

#### Source Structure (Admin View)
```
Band Drive Root/
├── Source/
│   ├── Audio/
│   │   ├── BadTouch.mp3
│   │   ├── LoveTonight.wav
│   │   └── ColdHeart.mp3
│   └── Charts/
│       ├── ColdHeart_Bb.pdf
│       ├── ColdHeart_Eb.pdf
│       ├── ColdHeart_BassClef.pdf
│       ├── Unholy_Bb.pdf
│       ├── Unholy_BassClef.pdf
│       └── BadTouch_Bb.pdf
```

#### User View Structure (Test Account - Trumpet)
```
TestUser's View/
├── BadTouch/
│   ├── BadTouch.mp3 (shortcut)
│   └── BadTouch_Bb.pdf (shortcut)
├── ColdHeart/
│   ├── ColdHeart.mp3 (shortcut)
│   └── ColdHeart_Bb.pdf (shortcut)
└── Unholy/
    └── Unholy_Bb.pdf (shortcut)
    (No audio file - doesn't exist in source)
```

### File Naming Conventions

#### Charts
- **Format**: `SongTitle_InstrumentTransposition.pdf`
- **Examples**: 
  - `ColdHeart_Bb.pdf` (for Trumpet, Tenor Sax, Clarinet)
  - `Unholy_BassClef.pdf` (for Trombone, Baritone, Tuba)
  - `LoveTonight_Eb.pdf` (for Alto Sax, Baritone Sax)

#### Audio Files
- **Format**: `SongTitle.(mp3|wav)`
- **Examples**: 
  - `BadTouch.mp3`
  - `LoveTonight.wav`
  - `ColdHeart.mp3`

### Role-Based Access System

#### Role Classes and Permissions
```yaml
instrument_class:
  roles: [trumpet, trombone, alto_sax, tenor_sax, bass_clarinet, etc.]
  transpositions: [Bb, Eb, BassClef, C]
  permissions: [view_charts, view_audio]
  changeable_to: [other_instrument_class_roles]

tech_class:
  roles: [sound_engineer, lighting_tech]  
  permissions: [view_all_files, manage_equipment_docs]
  changeable_to: [other_tech_class_roles]

admin_class:
  roles: [band_director, admin]
  permissions: [manage_all, upload_source, manage_users]
  changeable_to: [other_admin_class_roles]
```

#### Test Account Configuration
- **Initial Role**: trumpet (instrument_class)
- **Visible Transpositions**: Bb only
- **Folder Organization**: By song title
- **Content**: Bb charts + all audio files

## 🎨 User Interface Requirements

### First-Time Login Experience
1. Web platform authentication (username/password or simple login)
2. Role selection screen with instrument categories
3. Confirmation and welcome message
4. Access to personalized file view based on role

### Account Settings Tab
- **Current Role Display**: Show current instrument/role
- **Role Change Options**: Dropdown within same class only
- **Change Confirmation**: Require confirmation before role change
- **Folder Refresh**: Automatic reorganization after role change

### Main Dashboard Integration
- **File Browser Panel**: Show user's personalized song folders and files
- **Quick Access**: Recent songs/commonly used charts
- **Download/View**: Direct file access through web interface
- **Sync Status**: Show last sync time with source Google Drive

## 🔧 Implementation Approach

### Phase 1: Google Drive Backend Connection
- Set up Google Drive API service account credentials
- Implement backend-only Drive API authentication
- Create service for Drive API operations and file serving
- Test basic file listing and content delivery to web interface

### Phase 2: Role Management System  
- Design user role database schema
- Implement role assignment on first login
- Create role change functionality with class restrictions
- Build account settings interface

### Phase 3: File Organization Engine
- Develop file parsing logic for naming conventions
- Implement automatic shortcut creation based on roles
- Create song-based folder structure generator
- Add error handling for missing files/permissions

### Phase 4: Frontend Integration
- Build web platform authentication UI components
- Create role selection and management interfaces
- Integrate file browser display into main dashboard
- Add download/view capabilities and sync status

## 📋 Acceptance Criteria

### Must Have
- [ ] Test account can log into web platform and set trumpet role
- [ ] Test account sees only Bb charts organized by song folders in web interface
- [ ] Audio files appear in appropriate song folders for download/playback
- [ ] Role can be changed within instrument class from settings
- [ ] New files in Source folder automatically appear for appropriate users
- [ ] System is scalable for multiple band accounts

### Should Have
- [ ] Real-time sync status indicators
- [ ] Graceful handling of missing files
- [ ] Efficient API usage (minimal Drive API calls)
- [ ] Mobile-responsive role selection interface

### Could Have
- [ ] Bulk role assignment for multiple users
- [ ] Custom transposition mapping per user
- [ ] Offline file caching for frequently accessed charts

## 🚀 Success Metrics

- **User Experience**: Single role-appropriate view of all band content
- **Admin Efficiency**: One-time file upload automatically serves all users
- **Scalability**: System works for bands of 5-50+ members
- **Performance**: Folder organization completes within 30 seconds
- **Reliability**: 99%+ uptime for Google Drive integration

## 🔍 Technical Considerations

### Security
- Implement proper OAuth scopes (minimal required permissions)  
- Secure storage of refresh tokens
- User data privacy compliance
- Access logging for admin oversight

### Performance
- Implement caching for Drive API responses
- Batch operations for shortcut creation
- Lazy loading for large file collections
- Background sync processes

### Scalability  
- Design for multi-tenant band support
- Configurable file naming patterns
- Extensible role system architecture
- API rate limiting and retry logic

## 📚 Documentation Requirements

- Google Drive API setup guide
- Role configuration documentation  
- File naming convention standards
- Troubleshooting guide for common issues
- Multi-band deployment instructions

---

**Target Users**: Project Brass (murray@projectbrass.live) initially, designed for scalability to other bands
**Timeline**: 2-3 week implementation
**Dependencies**: Google Drive API access, user authentication system
**Risks**: Google API rate limits, complex file permission management