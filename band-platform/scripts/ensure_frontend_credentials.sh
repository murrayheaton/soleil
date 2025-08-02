#!/bin/bash

# This script ensures frontend has OAuth credentials before building
# Critical for Next.js which needs NEXT_PUBLIC_* vars at build time

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔧 Ensuring Frontend OAuth Credentials${NC}"

# Check if persistent credentials exist
if [ -f "/etc/soleil/oauth.env" ]; then
    echo -e "${GREEN}✓ Found persistent credentials${NC}"
    
    # Source the credentials
    source /etc/soleil/oauth.env
    
    # Check if frontend .env.production exists
    if [ ! -f "frontend/.env.production" ]; then
        echo -e "${YELLOW}Creating frontend/.env.production${NC}"
        touch frontend/.env.production
    fi
    
    # Update or add NEXT_PUBLIC_GOOGLE_CLIENT_ID
    if grep -q "^NEXT_PUBLIC_GOOGLE_CLIENT_ID=" frontend/.env.production; then
        echo -e "${YELLOW}Updating existing NEXT_PUBLIC_GOOGLE_CLIENT_ID${NC}"
        sed -i.bak "s/^NEXT_PUBLIC_GOOGLE_CLIENT_ID=.*/NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID/" frontend/.env.production
    else
        echo -e "${YELLOW}Adding NEXT_PUBLIC_GOOGLE_CLIENT_ID${NC}"
        echo "NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" >> frontend/.env.production
    fi
    
    # Also ensure it's in the docker build context
    echo "NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" > frontend/.env.production.build
    
    echo -e "${GREEN}✅ Frontend credentials configured${NC}"
    echo -e "${BLUE}Client ID: ${GOOGLE_CLIENT_ID:0:20}...${NC}"
    
else
    echo -e "${RED}❌ No persistent credentials found at /etc/soleil/oauth.env${NC}"
    echo -e "${YELLOW}Run setup_persistent_credentials.sh first${NC}"
    exit 1
fi