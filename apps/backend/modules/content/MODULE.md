# Content Module

**Version:** 1.0.0  
**Last Updated:** 2025-08-05  
**Status:** Active

## Overview
The Content module handles all file parsing, organization, and instrument-based filtering for the band platform. It manages charts, audio files, and setlists with intelligent key mapping for transposing instruments.

## Key Features
- File parsing for charts and audio files
- Instrument-based key mapping and filtering
- User folder organization
- Support for multiple file formats (PDF, MP3, WAV, etc.)
- Placeholder file detection
- Smart filename parsing

## Module Structure
```
content/
├── api/
│   ├── __init__.py
│   └── content_routes.py      # Content-related endpoints
├── models/
│   ├── __init__.py
│   ├── content.py             # Chart, Audio, and Setlist models
│   └── folder_structure.py    # User folder organization models
├── services/
│   ├── __init__.py
│   ├── content_parser.py      # File parsing logic
│   ├── file_organizer.py      # User folder organization
│   └── instrument_filter.py   # Instrument-based filtering
├── utils/
│   ├── __init__.py
│   ├── file_types.py          # File type detection
│   ├── naming.py              # Naming convention helpers
│   └── metadata.py            # Metadata extraction
├── tests/
│   └── ...                    # Module tests
└── MODULE.md                  # This file
```

## Dependencies
- Internal: auth module (for user context)
- External: pydantic, sqlalchemy, python-magic

## Public API
```python
from modules.content import (
    # API Router
    content_router,
    
    # Services
    ContentParser,
    FileOrganizer,
    InstrumentFilter,
    
    # Models
    Chart,
    Audio,
    Setlist,
    UserFolder,
    
    # Utilities
    parse_filename,
    get_file_type,
    extract_metadata
)
```

## Parsing Rules

### Chart File Naming
Charts follow the pattern: `SongTitle_Key.pdf`
- Example: `AllOfMe_Bb.pdf` (B♭ transposed chart)
- Example: `BlueMoon_Concert.pdf` (Concert pitch chart)
- Example: `Summertime_X.pdf` (Placeholder)

### Audio File Naming
Audio files follow the pattern: `SongTitle.ext` or `SongTitle_Type.ext`
- Example: `AllOfMe.mp3` (Performance audio)
- Example: `BlueMoon_Reference.mp3` (Reference track)
- Example: `Summertime_X.mp3` (Placeholder)

### Instrument Key Mapping
```python
INSTRUMENT_KEY_MAPPING = {
    # B♭ Instruments
    'trumpet': 'Bb',
    'tenor_sax': 'Bb',
    'soprano_sax': 'Bb',
    'clarinet': 'Bb',
    
    # E♭ Instruments
    'alto_sax': 'Eb',
    'bari_sax': 'Eb',
    
    # Concert Pitch
    'piano': 'C',
    'guitar': 'C',
    'bass': 'C',
    'drums': 'C',
    'violin': 'C',
    'voice': 'C',
    'trombone': 'C',
    'flute': 'C'
}
```

## Common Usage Patterns

### Parsing a Chart File
```python
parser = ContentParser()
chart = await parser.parse_chart_file(
    filename="AllOfMe_Bb.pdf",
    file_id="drive_file_id",
    band_id=1
)
```

### Filtering Content by Instrument
```python
filter = InstrumentFilter()
user_content = await filter.get_content_for_user(
    user_id=1,
    instruments=['alto_sax', 'flute']
)
```

### Organizing User Folders
```python
organizer = FileOrganizer()
folder_structure = await organizer.create_user_folder_structure(
    user_id=1,
    google_drive_service=drive_service
)
```

## Error Handling
- `ContentParsingError`: Raised when file parsing fails
- `InvalidFileFormatError`: Raised for unsupported file types
- `FolderOrganizationError`: Raised when folder operations fail

## Testing
Run module tests:
```bash
pytest modules/content/tests/
```

## Integration Points
- Auth module: User context and permissions
- Drive module: Google Drive file operations
- Sync module: Content synchronization
- Dashboard module: Content display