# Chart Viewing Implementation Guide

## Overview
The chart viewing functionality has been fully implemented to allow band members to access and view charts from Google Drive. This document outlines the implementation details and configuration requirements.

## Architecture

### Intelligent Content Discovery

The system uses a **single master assets folder** and intelligently discovers content based on:
- **File types**: PDFs and images are identified as charts, audio files are filtered out
- **Naming conventions**: SOLEIL naming system parses metadata from filenames
- **Recursive scanning**: Automatically discovers content in all subfolders
- **No hard-coded paths**: The system adapts to any folder structure

### Backend Components

1. **Content Module** (`/band-platform/backend/modules/content/`)
   - **API Routes** (`api/content_routes.py`): Handles all chart-related endpoints
   - **Chart Service** (`services/chart_service.py`): Recursively scans and intelligently filters content
   - **Models** (`models/content.py`): Defines Chart and ChartListResponse models
   - **SOLEIL Parser** (`services/soleil_content_parser.py`): Parses chart filenames using SOLEIL conventions

2. **Drive Module** (`/band-platform/backend/modules/drive/`)
   - **Drive Client** (`services/drive_client.py`): Google Drive API integration
   - **Drive Auth** (`services/drive_auth.py`): OAuth authentication service
   - **Drive Routes** (`api/drive_routes.py`): Additional Drive-specific endpoints including instrument views

### Frontend Components

1. **API Service** (`/band-platform/frontend/src/lib/api.ts`)
   - Handles all API communication with proper endpoint paths
   - Includes authentication error handling
   - Supports offline storage integration

2. **Chart Viewer** (`/band-platform/frontend/src/components/ChartViewer.tsx`)
   - PDF rendering using react-pdf
   - Offline storage support
   - Authentication flow integration

## API Endpoints

All endpoints are accessible under `/api/modules/content/`:

### Chart Operations
- `GET /api/modules/content/charts` - List charts with filtering
  - Query params: `folder_id`, `instrument`, `limit`, `offset`
- `GET /api/modules/content/charts/{chart_id}` - Get chart metadata
- `GET /api/modules/content/charts/{chart_id}/download` - Download chart file
- `GET /api/modules/content/charts/search` - Search charts
  - Query params: `query`, `folder_id`, `instrument`, `limit`
- `GET /api/modules/content/folders` - List available chart folders

### Google Drive Authentication
- `GET /api/modules/content/auth/google/url` - Get OAuth URL
- `POST /api/modules/content/auth/google/callback` - Handle OAuth callback
- `GET /api/modules/content/auth/google/status` - Check auth status

### Instrument Views (Drive Module)
- `GET /api/modules/drive/{instrument}-view` - Get filtered charts by instrument
  - Supported: `Bb`, `Eb`, `Concert`, `BassClef`, `Chords`, `Lyrics`

## Configuration Requirements

### Environment Variables

Add these to your `.env` file:

```bash
# Google OAuth Configuration (Required)
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback

# Google Drive Configuration (Required)
# Single master folder - system will recursively scan for all content
GOOGLE_DRIVE_SOURCE_FOLDER_ID=your_master_assets_folder_id_here

# API Configuration (Frontend)
NEXT_PUBLIC_API_URL=https://solepower.live
```

### Google Cloud Console Setup

1. **Enable APIs**:
   - Google Drive API
   - Google OAuth2 API

2. **OAuth 2.0 Configuration**:
   - Add authorized redirect URIs:
     - Production: `https://solepower.live/api/auth/google/callback`
     - Development: `http://localhost:8000/api/auth/google/callback`
   - Add scopes:
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/drive.file`

3. **Service Account** (Optional):
   - Create a service account for server-side operations
   - Download credentials JSON
   - Share Google Drive folders with service account email

## Authentication Flow

1. **Initial Setup**:
   - User visits charts page
   - Frontend checks auth status via `/api/modules/content/auth/google/status`
   - If not authenticated, shows "Authenticate with Google Drive" button

2. **OAuth Flow**:
   - User clicks authenticate button
   - Frontend requests auth URL from `/api/modules/content/auth/google/url`
   - User is redirected to Google OAuth consent screen
   - After approval, Google redirects to callback URL with auth code
   - Backend exchanges code for tokens and stores them

3. **Accessing Charts**:
   - Once authenticated, frontend can list and download charts
   - Authentication persists via stored tokens
   - Tokens are automatically refreshed when expired

## File Naming Convention (SOLEIL)

The system uses a simple, consistent naming convention for all chart files.

### Required naming format:
```
SongName_Transposition.pdf
```

### Examples:
- `TakeFive_Bb.pdf` (B-flat instruments)
- `BlueTrain_Concert.pdf` (Concert pitch)
- `Spain_Chords.pdf` (Chord charts)
- `MyFunnyValentine_Lyrics.pdf` (Lyrics sheet)

### Content Type Detection:
- **Charts**: Only `.pdf` files are recognized as charts
- **Audio**: `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg` (automatically filtered out from chart listings)
- **Folders**: Any folder structure is supported - the system scans recursively

## Supported Transpositions

- **Bb**: Trumpet, Tenor Sax
- **Eb**: Alto Sax, Bari Sax
- **Concert**: Violin
- **BassClef**: Trombone
- **Chords**: Piano/Keys, Guitar, Bass, Drums
- **Lyrics**: Singers

## Testing

### Manual Testing Steps

1. **Authentication**:
   ```bash
   curl -X GET "https://solepower.live/api/modules/content/auth/google/status"
   ```

2. **List Charts**:
   ```bash
   curl -X GET "https://solepower.live/api/modules/content/charts?limit=10"
   ```

3. **Download Chart**:
   ```bash
   curl -X GET "https://solepower.live/api/modules/content/charts/{chart_id}/download" -o chart.pdf
   ```

### Common Issues and Solutions

1. **401 Unauthorized Error**:
   - Solution: Ensure Google OAuth is properly configured
   - Check that tokens are stored and valid
   - Verify redirect URI matches configuration

2. **503 Service Unavailable**:
   - Solution: Check Google Drive API quotas
   - Verify service account credentials if using
   - Check network connectivity

3. **Empty Chart List**:
   - Solution: Verify GOOGLE_DRIVE_CHARTS_FOLDER_ID is set
   - Ensure folder is shared with authenticated account
   - Check that folder contains PDF files

## Production Deployment

1. **Backend**:
   - Ensure all environment variables are set
   - Run database migrations if any
   - Restart backend service

2. **Frontend**:
   - Update NEXT_PUBLIC_API_URL if needed
   - Build production bundle: `npm run build`
   - Deploy to hosting service

3. **Verification**:
   - Test authentication flow
   - Verify charts can be listed and downloaded
   - Check offline functionality works

## Future Enhancements

- [ ] Implement caching layer for frequently accessed charts
- [ ] Add support for setlist management
- [ ] Implement real-time sync with Google Drive changes
- [ ] Add annotation and markup features
- [ ] Support for audio file playback alongside charts