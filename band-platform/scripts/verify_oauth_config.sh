#!/bin/bash

# Script to verify OAuth configuration and display what should be in Google Cloud Console

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 OAuth Configuration Verification${NC}"
echo ""

# OAuth Credentials
CLIENT_ID="360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com"

echo -e "${YELLOW}=== Required Google Cloud Console Settings ===${NC}"
echo ""
echo -e "${GREEN}1. OAuth 2.0 Client ID:${NC}"
echo "   $CLIENT_ID"
echo ""
echo -e "${GREEN}2. Authorized JavaScript origins:${NC}"
echo "   - https://solepower.live"
echo ""
echo -e "${GREEN}3. Authorized redirect URIs (MUST include ALL of these):${NC}"
echo "   - https://solepower.live/api/auth/google/callback"
echo ""

echo -e "${YELLOW}=== Current Configuration in Code ===${NC}"
echo ""

# Check backend .env.production
if [ -f "backend/.env.production" ]; then
    echo -e "${GREEN}Backend .env.production:${NC}"
    grep -E "GOOGLE_|FRONTEND_URL" backend/.env.production | sed 's/SECRET=.*/SECRET=***HIDDEN***/'
else
    echo -e "${RED}❌ Backend .env.production not found${NC}"
fi

echo ""

# Check frontend .env.production
if [ -f "frontend/.env.production" ]; then
    echo -e "${GREEN}Frontend .env.production:${NC}"
    grep -E "NEXT_PUBLIC_" frontend/.env.production
else
    echo -e "${RED}❌ Frontend .env.production not found${NC}"
fi

echo ""
echo -e "${YELLOW}=== Verification Steps ===${NC}"
echo ""
echo "1. Go to: https://console.cloud.google.com/apis/credentials"
echo "2. Click on your OAuth 2.0 Client ID ($CLIENT_ID)"
echo "3. Verify ALL redirect URIs listed above are added"
echo "4. Save changes in Google Cloud Console"
echo "5. Wait 5 minutes for changes to propagate"
echo ""

echo -e "${YELLOW}=== Testing OAuth Flow ===${NC}"
echo ""
echo "The OAuth flow constructs these URLs:"
echo ""
echo "1. Frontend initiates:"
echo "   API URL: https://solepower.live/api"
echo "   Redirect URI: https://solepower.live/api/api/auth/google/callback"
echo ""
echo "2. Backend expects:"
echo "   Redirect URI: https://solepower.live/api/auth/google/callback"
echo ""
echo -e "${RED}⚠️  IMPORTANT: Make sure there's no double '/api/api/' in the redirect URI!${NC}"

# Check for common issues
echo ""
echo -e "${YELLOW}=== Common Issues ===${NC}"
echo ""

# Check if running locally
if [ -f ".env" ]; then
    if grep -q "localhost" .env; then
        echo -e "${RED}⚠️  Found localhost in .env file - make sure you're not mixing local and production configs${NC}"
    fi
fi

# Check Docker status
if command -v docker &> /dev/null; then
    if docker ps | grep -q "band_platform"; then
        echo -e "${GREEN}✓ Docker containers are running${NC}"
        
        # Check if backend can read env vars
        echo ""
        echo -e "${YELLOW}Checking backend environment variables:${NC}"
        docker exec band_platform_backend sh -c 'echo "GOOGLE_REDIRECT_URI=$GOOGLE_REDIRECT_URI"' || echo "Failed to check backend env"
    else
        echo -e "${YELLOW}ℹ️  Docker containers not running${NC}"
    fi
fi

echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo "1. Verify Google Cloud Console settings match above"
echo "2. Check browser console for exact redirect URI being used"
echo "3. Ensure no trailing slashes or double slashes in URIs"
echo "4. Clear browser cache and cookies for solepower.live"