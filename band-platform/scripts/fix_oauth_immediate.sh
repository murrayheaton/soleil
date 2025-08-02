#!/bin/bash

# Immediate fix for OAuth configuration
# This script manually injects OAuth credentials into the frontend build

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Immediate OAuth Fix${NC}"

# Your OAuth credentials (replace with actual values)
GOOGLE_CLIENT_ID="360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="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"
GOOGLE_DRIVE_FOLDER_ID="1PGL1NkfD39CDzVOxJt_X-rF48OAnd2kk"

# Create frontend .env.production
cat > frontend/.env.production << EOF
NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
NEXT_PUBLIC_API_URL=https://solepower.live/api
EOF

# Create backend .env.production
cat > backend/.env.production << EOF
GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
GOOGLE_DRIVE_SOURCE_FOLDER_ID=$GOOGLE_DRIVE_FOLDER_ID
FRONTEND_URL=https://solepower.live
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["https://solepower.live"]
APP_NAME="SOLEil"
LOG_LEVEL=INFO
EOF

echo -e "${GREEN}✅ Environment files created${NC}"
echo -e "${YELLOW}Now rebuild and deploy:${NC}"
echo "docker-compose -f docker-compose.production.yml build frontend"
echo "docker-compose -f docker-compose.production.yml up -d"