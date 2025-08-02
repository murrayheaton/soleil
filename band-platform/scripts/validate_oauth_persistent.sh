#!/bin/bash

# Validation script for persistent OAuth credentials
echo "🔍 Validating Persistent OAuth Configuration..."

# Check if persistent credentials file exists
if [ ! -f "/etc/soleil/oauth.env" ]; then
    echo "❌ Persistent credentials file not found at /etc/soleil/oauth.env"
    exit 1
fi

# Source the persistent credentials
source /etc/soleil/oauth.env

# Validate required fields
if [ -z "$GOOGLE_CLIENT_ID" ] || [ "$GOOGLE_CLIENT_ID" = "your_client_id_here" ]; then
    echo "❌ OAuth Client ID not configured in persistent storage"
    exit 1
else
    echo "✓ OAuth Client ID configured"
fi

if [ -z "$GOOGLE_CLIENT_SECRET" ] || [ "$GOOGLE_CLIENT_SECRET" = "your_client_secret_here" ]; then
    echo "❌ OAuth Client Secret not configured in persistent storage"
    exit 1
else
    echo "✓ OAuth Client Secret configured"
fi

if [ -z "$NEXT_PUBLIC_GOOGLE_CLIENT_ID" ] || [ "$NEXT_PUBLIC_GOOGLE_CLIENT_ID" = "your_client_id_here" ]; then
    echo "❌ Frontend OAuth Client ID not configured in persistent storage"
    exit 1
else
    echo "✓ Frontend OAuth Client ID configured"
fi

# Check if frontend and backend client IDs match
if [ "$GOOGLE_CLIENT_ID" != "$NEXT_PUBLIC_GOOGLE_CLIENT_ID" ]; then
    echo "❌ Client ID mismatch between frontend and backend in persistent storage"
    exit 1
else
    echo "✓ Client IDs match between frontend and backend"
fi

# Check Google Drive folder ID if provided
if [ -n "$GOOGLE_DRIVE_SOURCE_FOLDER_ID" ] && [ "$GOOGLE_DRIVE_SOURCE_FOLDER_ID" != "your_folder_id_here" ]; then
    echo "✓ Google Drive folder ID configured"
fi

echo "✅ Persistent OAuth configuration validated successfully!"