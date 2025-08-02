#!/bin/bash

# This script sets up persistent OAuth credentials on the server
# Run this ONCE on your production server

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔐 Setting up Persistent OAuth Credentials${NC}"

# Create protected credentials directory
CREDS_DIR="/etc/soleil"
sudo mkdir -p "$CREDS_DIR"
sudo chmod 700 "$CREDS_DIR"

# Create OAuth credentials file
echo -e "${YELLOW}📝 Creating OAuth credentials file...${NC}"
sudo tee "$CREDS_DIR/oauth.env" > /dev/null << 'EOF'
# Soleil OAuth Credentials - Persistent Storage
# These credentials are loaded by the application but never modified by deployments

# Google OAuth Configuration
GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
GOOGLE_DRIVE_SOURCE_FOLDER_ID=1PGL1NkfD39CDzVOxJt_X-rF48OAnd2kk

# Frontend OAuth Configuration
NEXT_PUBLIC_GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
EOF

# Secure the file
sudo chmod 600 "$CREDS_DIR/oauth.env"
sudo chown root:root "$CREDS_DIR/oauth.env"

echo -e "${GREEN}✅ Credentials directory created at $CREDS_DIR${NC}"
echo -e "${GREEN}✅ OAuth credentials have been configured${NC}"