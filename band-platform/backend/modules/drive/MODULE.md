# # Google Drive Module

**Version:** 1.0.0  
**Last Updated:** 2025-08-05  
**Status:** Active

## Purpose and Scope
The Drive module manages all interactions with Google Drive, including file browsing, streaming, folder organization, and caching.

## Module Context
This module is responsible for:
- Google Drive API integration
- File browsing and metadata retrieval
- File streaming and downloading
- Folder structure management
- Rate limiting and caching
- OAuth token management for Drive access

## Dependencies
- Core module (for EventBus)
- Auth module (for user credentials)
- External: google-api-python-client, google-auth

## API Endpoints (To Be Migrated)
- `GET /api/drive/files` - List files in folder
- `GET /api/drive/files/{id}` - Get file metadata
- `GET /api/drive/files/{id}/stream` - Stream file content
- `GET /api/drive/folders` - List folders
- `POST /api/drive/folders` - Create folder structure

## Key Services (To Be Migrated)
- `GoogleDriveService` - Core Drive API operations
- `DriveAuthService` - Drive-specific auth handling
- `FileCacheService` - File caching logic
- `RateLimiter` - API rate limiting
- `FolderOrganizer` - Folder structure management

## Events Published
- `drive.file.created` - New file detected
- `drive.file.updated` - File updated
- `drive.file.deleted` - File removed
- `drive.folder.created` - New folder created
- `drive.sync.completed` - Sync operation finished

## Events Subscribed
- `user.login` - Initialize Drive connection
- `sync.requested` - Start sync operation

## Testing Strategy
- Mock Google Drive API responses
- Test rate limiting behavior
- Test caching mechanisms
- Integration tests with test Drive
- Test error handling and retries

## Module-Specific Rules
1. Must respect Google API rate limits
2. Cache must have size limits
3. OAuth tokens must be refreshed properly
4. File streaming must be efficient
5. Error handling must be comprehensive