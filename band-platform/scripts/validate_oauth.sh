#!/bin/bash

# Quick validation script to check OAuth setup
echo "🔍 Validating OAuth Configuration..."

# Check backend credentials
if grep -q "GOOGLE_CLIENT_ID=your_google_client_id_here\|GOOGLE_CLIENT_ID=test_client_id" backend/.env.production; then
    echo "❌ Backend: OAuth Client ID not configured"
    exit 1
else
    echo "✓ Backend: OAuth Client ID configured"
fi

if grep -q "GOOGLE_CLIENT_SECRET=your_google_client_secret_here\|GOOGLE_CLIENT_SECRET=test_client_secret" backend/.env.production; then
    echo "❌ Backend: OAuth Client Secret not configured"
    exit 1
else
    echo "✓ Backend: OAuth Client Secret configured"
fi

# Check frontend credentials
if grep -q "NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here" frontend/.env.production; then
    echo "❌ Frontend: OAuth Client ID not configured"
    exit 1
else
    echo "✓ Frontend: OAuth Client ID configured"
fi

# Check if frontend and backend client IDs match
BACKEND_CLIENT_ID=$(grep "^GOOGLE_CLIENT_ID=" backend/.env.production | cut -d= -f2)
FRONTEND_CLIENT_ID=$(grep "^NEXT_PUBLIC_GOOGLE_CLIENT_ID=" frontend/.env.production | cut -d= -f2)

if [ "$BACKEND_CLIENT_ID" != "$FRONTEND_CLIENT_ID" ]; then
    echo "❌ Client ID mismatch between frontend and backend"
    exit 1
else
    echo "✓ Client IDs match between frontend and backend"
fi

echo "✅ OAuth configuration validated successfully!"