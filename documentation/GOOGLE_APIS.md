# Google APIs Documentation for SOLEil

## Overview
SOLEil uses Google APIs for authentication and file management. This document provides essential reference information for working with these APIs in the project.

## Google OAuth 2.0

### Current Implementation
- **Location**: `/band-platform/backend/modules/auth/`
- **Client ID**: Stored in environment variables
- **Redirect URI**: `https://solepower.live/api/auth/google/callback`
- **Scopes Used**:
  - `openid`
  - `email`
  - `profile`
  - `https://www.googleapis.com/auth/drive.readonly`

### Key Endpoints
```python
# Authentication flow
GET /api/auth/google/login     # Initiates OAuth flow
GET /api/auth/google/callback  # Handles OAuth callback
GET /api/auth/session          # Retrieves current session
POST /api/auth/logout          # Ends session
```

### Implementation Notes
- JWT tokens are used for session management
- Tokens are stored in HTTP-only cookies
- User profiles are persisted in `user_profiles.json`

### Common Issues & Solutions

#### Token Refresh
```python
# Token refresh implementation in google_auth_service.py
async def refresh_access_token(refresh_token: str):
    """Refresh an expired access token"""
    # Implementation handles automatic token refresh
```

#### CORS Configuration
- Production: `https://solepower.live`
- Local development: `http://localhost:3000`

## Google Drive API

### Current Implementation
- **Location**: `/band-platform/backend/modules/drive/`
- **Source Folder ID**: `1PGL1NkfD39CDzVOxJt_X-rF48OAnd2kk`
- **File Types Supported**: PDF, Images, Audio files

### Key Functions

#### List Files
```python
async def list_drive_files(
    folder_id: str,
    file_type: Optional[str] = None
) -> List[DriveFile]:
    """List files in a Drive folder with optional filtering"""
```

#### Stream File Content
```python
async def stream_file_content(
    file_id: str,
    mime_type: str
) -> AsyncIterator[bytes]:
    """Stream file content for efficient delivery"""
```

#### File Organization
- Files are organized by instrument type
- Metadata includes: title, artist, key, tempo, genre
- Chart types: Guitar, Bass, Drums, Keys, Vocals

### Drive API Quotas
- **Queries per day**: 1,000,000,000
- **Queries per 100 seconds**: 20,000
- **Queries per 100 seconds per user**: 1,000

### Best Practices
1. **Batch Requests**: Use batch operations when fetching multiple files
2. **Caching**: Implement caching for frequently accessed files
3. **Error Handling**: Handle rate limits with exponential backoff
4. **Fields Parameter**: Only request needed fields to reduce bandwidth

### Error Codes
- `401`: Invalid credentials - refresh token
- `403`: Insufficient permissions - check scopes
- `404`: File not found - verify file ID
- `429`: Rate limit exceeded - implement backoff

## Google Sheets API

### Current Implementation
- **Location**: `/band-platform/backend/app/services/google_sheets.py`
- **Usage**: Metadata management for songs

### Common Operations
```python
# Read sheet data
values = sheet.values().get(
    spreadsheetId=SHEET_ID,
    range='A1:E10'
).execute()

# Update sheet data
sheet.values().update(
    spreadsheetId=SHEET_ID,
    range='A1',
    valueInputOption='RAW',
    body={'values': data}
).execute()
```

## Authentication Setup

### Environment Variables Required
```bash
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
GOOGLE_DRIVE_SOURCE_FOLDER_ID=folder_id
```

### OAuth Consent Screen Configuration
1. **Application Type**: Web application
2. **Authorized JavaScript origins**: `https://solepower.live`
3. **Authorized redirect URIs**: `https://solepower.live/api/auth/google/callback`

## Security Considerations

1. **Token Storage**: Never store tokens in frontend code
2. **Scope Limitations**: Only request necessary scopes
3. **HTTPS Required**: Always use HTTPS in production
4. **Token Validation**: Validate tokens on every API request

## Testing

### Mock Credentials for Testing
```python
# Use google-auth-library test utilities
from google.auth import credentials

test_credentials = credentials.AnonymousCredentials()
```

### Integration Testing
- Use service account for CI/CD testing
- Mock API responses for unit tests
- Test token refresh flows

## Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Drive API Reference](https://developers.google.com/drive/api/v3/reference)
- [Google Sheets API Reference](https://developers.google.com/sheets/api/reference/rest)
- [Python Client Library](https://github.com/googleapis/google-api-python-client)