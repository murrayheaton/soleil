# Content Module

## Purpose and Scope
The Content module manages all music-related content including charts (sheet music), audio files, and setlists. It handles content parsing, organization, and instrument-based filtering.

## Module Context
This module is responsible for:
- Content file parsing and metadata extraction
- Instrument-based content filtering
- Chart organization by key
- Audio file management
- Setlist creation and management

## Dependencies
- Core module (for EventBus)
- Auth module (for user instrument preferences)
- External: None specific

## API Endpoints (To Be Migrated)
- `GET /api/content/charts` - List available charts
- `GET /api/content/charts/{id}` - Get chart details
- `GET /api/content/audio` - List audio files
- `GET /api/content/audio/{id}` - Get audio details
- `GET /api/content/setlists` - List setlists
- `POST /api/content/setlists` - Create setlist

## Key Services (To Be Migrated)
- `ContentParser` - Parse filenames and extract metadata
- `InstrumentKeyMapper` - Map instruments to musical keys
- `ChartService` - Chart management
- `AudioService` - Audio file management
- `SetlistService` - Setlist operations

## Events Published
- `content.chart.added` - New chart available
- `content.audio.added` - New audio file available
- `content.setlist.created` - Setlist created
- `content.setlist.updated` - Setlist modified

## Events Subscribed
- `drive.file.created` - New file in Drive
- `drive.file.updated` - File updated in Drive
- `user.profile.updated` - User instruments changed

## Testing Strategy
- Comprehensive unit tests for ContentParser
- Tests for all instrument key mappings
- Integration tests for content filtering
- Mock file system for testing

## Module-Specific Rules
1. Content parsing must handle various filename formats
2. Instrument filtering must be accurate
3. Key transposition logic must be correct
4. Setlist ordering must be preserved
5. Content metadata must be cached appropriately