# Drive Module

**Version:** 1.0.0  
**Last Updated:** 2025-08-05  
**Status:** Active

## Overview
The Drive module manages all Google Drive integration for the band platform, providing file synchronization, metadata extraction, and real-time updates through webhooks.

## Architecture

### Services
- **GoogleDriveService**: Core service for Drive API operations with rate limiting and error handling
- **GoogleDriveOAuthService**: Handles OAuth 2.0 authentication flow for user authorization
- **RateLimiter**: Token bucket rate limiter with dynamic adjustment based on API responses
- **CacheManager**: In-memory caching with TTL and LRU eviction for optimizing API calls

### Models
- **DriveFile**: Tracks Google Drive files and their metadata
- **DrivePermission**: Manages file permissions and sharing settings
- **DriveWebhook**: Tracks active webhooks for real-time notifications

### API Routes
- `/drive/auth/*`: OAuth authentication endpoints
- `/drive/folders/*`: Folder listing and management
- `/drive/files/*`: File operations and metadata
- `/drive/webhook`: Webhook setup and management

## Key Features

### 1. Rate Limiting
- Token bucket algorithm with configurable limits
- Dynamic rate limiting that adjusts based on API responses
- Automatic backoff on rate limit errors

### 2. Caching Strategy
- In-memory cache with configurable TTL
- LRU eviction policy
- Cache invalidation by prefix
- Decorator-based caching for easy integration

### 3. File Processing
- Automatic parsing of musical filenames (song title, key, type)
- Support for charts (PDF), audio files, and setlists
- Batch operations for efficient processing

### 4. Real-time Updates
- Webhook support for instant file change notifications
- Integration with sync module for processing updates
- Automatic webhook renewal before expiration

## Dependencies
- **Auth Module**: For user authentication and band associations
- **Content Module**: For content parsing and file type detection

## Configuration
```python
# Required environment variables
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/drive/auth/callback
```

## Usage Examples

### Basic File Listing
```python
from modules.drive import GoogleDriveService

service = GoogleDriveService(credentials)
files = await service.list_files(folder_id="folder_123")
```

### Setting Up Webhooks
```python
webhook_info = await service.setup_webhook(
    folder_id="folder_123",
    webhook_url="https://api.example.com/webhook/drive"
)
```

### Using Rate Limiter
```python
from modules.drive import DynamicRateLimiter

limiter = DynamicRateLimiter(initial_requests_per_second=10)
await limiter.acquire()
# Make API call
limiter.report_success()
```

## Error Handling
- **DriveAPIError**: Base exception for all Drive API errors
- **RateLimitExceeded**: Raised when rate limits are hit
- **AuthenticationError**: OAuth or credential issues

## Performance Considerations
- Batch operations for processing multiple files
- Caching reduces API calls by up to 80%
- Rate limiting prevents API exhaustion
- Async operations throughout for non-blocking I/O

## Security
- OAuth 2.0 for secure authentication
- No service account keys stored
- Credentials refreshed automatically
- Webhook secrets for verification

## Future Enhancements
- [ ] Resumable uploads for large files
- [ ] Team Drive support
- [ ] Advanced search with full-text indexing
- [ ] Offline sync capabilities