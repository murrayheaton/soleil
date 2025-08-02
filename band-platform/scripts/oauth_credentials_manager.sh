#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
BACKEND_ENV="backend/.env.production"
FRONTEND_ENV="frontend/.env.production"
CREDENTIALS_BACKUP_DIR=".credentials_backup"

# Function to create secure backup
backup_existing_credentials() {
    echo -e "${YELLOW}📦 Backing up existing credentials...${NC}"
    mkdir -p "$CREDENTIALS_BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    if [ -f "$BACKEND_ENV" ]; then
        cp "$BACKEND_ENV" "$CREDENTIALS_BACKUP_DIR/backend_env_$TIMESTAMP.bak"
    fi
    if [ -f "$FRONTEND_ENV" ]; then
        cp "$FRONTEND_ENV" "$CREDENTIALS_BACKUP_DIR/frontend_env_$TIMESTAMP.bak"
    fi
    
    echo -e "${GREEN}✓ Credentials backed up to $CREDENTIALS_BACKUP_DIR${NC}"
}

# Function to validate OAuth credentials format
validate_oauth_credentials() {
    local client_id=$1
    local client_secret=$2
    
    # Check if client_id matches Google OAuth pattern
    if [[ ! "$client_id" =~ ^[0-9]+-[a-z0-9]+\.apps\.googleusercontent\.com$ ]]; then
        echo -e "${RED}❌ Invalid Client ID format${NC}"
        echo "Expected format: XXXXXXXXX-XXXXXXXXXXXXXXXX.apps.googleusercontent.com"
        return 1
    fi
    
    # Check if client_secret is not empty and has reasonable length
    if [ ${#client_secret} -lt 20 ]; then
        echo -e "${RED}❌ Client Secret appears too short${NC}"
        return 1
    fi
    
    return 0
}

# Interactive credential input
interactive_credential_input() {
    echo -e "${BLUE}🔑 OAuth Credentials Setup${NC}"
    echo -e "${YELLOW}Please enter your Google OAuth credentials${NC}"
    echo -e "These can be found in your Google Cloud Console:"
    echo -e "https://console.cloud.google.com/apis/credentials"
    echo ""
    
    # Get Client ID
    while true; do
        read -p "Enter Google Client ID: " CLIENT_ID
        if validate_oauth_credentials "$CLIENT_ID" "dummy_secret"; then
            break
        fi
        echo -e "${RED}Please enter a valid Client ID${NC}"
    done
    
    # Get Client Secret
    while true; do
        read -s -p "Enter Google Client Secret (hidden): " CLIENT_SECRET
        echo ""
        if [ ${#CLIENT_SECRET} -ge 20 ]; then
            break
        fi
        echo -e "${RED}Client Secret appears invalid. Please try again.${NC}"
    done
    
    # Get Drive Folder ID (optional)
    echo ""
    read -p "Enter Google Drive Source Folder ID (optional, press Enter to skip): " DRIVE_FOLDER_ID
    
    # Confirm before proceeding
    echo ""
    echo -e "${YELLOW}Please confirm these settings:${NC}"
    echo "Client ID: $CLIENT_ID"
    echo "Client Secret: ****${CLIENT_SECRET: -4}"
    if [ -n "$DRIVE_FOLDER_ID" ]; then
        echo "Drive Folder ID: $DRIVE_FOLDER_ID"
    fi
    echo ""
    read -p "Is this correct? (y/N): " CONFIRM
    
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo -e "${RED}Setup cancelled${NC}"
        exit 1
    fi
}

# Update environment files with credentials
update_environment_files() {
    echo -e "${YELLOW}📝 Updating environment files...${NC}"
    
    # Update backend .env.production
    if [ -f "$BACKEND_ENV" ]; then
        # Update existing file
        sed -i.tmp "s/^GOOGLE_CLIENT_ID=.*/GOOGLE_CLIENT_ID=$CLIENT_ID/" "$BACKEND_ENV"
        sed -i.tmp "s/^GOOGLE_CLIENT_SECRET=.*/GOOGLE_CLIENT_SECRET=$CLIENT_SECRET/" "$BACKEND_ENV"
        
        # Add if not present
        grep -q "^GOOGLE_CLIENT_ID=" "$BACKEND_ENV" || echo "GOOGLE_CLIENT_ID=$CLIENT_ID" >> "$BACKEND_ENV"
        grep -q "^GOOGLE_CLIENT_SECRET=" "$BACKEND_ENV" || echo "GOOGLE_CLIENT_SECRET=$CLIENT_SECRET" >> "$BACKEND_ENV"
        
        if [ -n "$DRIVE_FOLDER_ID" ]; then
            sed -i.tmp "s/^GOOGLE_DRIVE_SOURCE_FOLDER_ID=.*/GOOGLE_DRIVE_SOURCE_FOLDER_ID=$DRIVE_FOLDER_ID/" "$BACKEND_ENV"
            grep -q "^GOOGLE_DRIVE_SOURCE_FOLDER_ID=" "$BACKEND_ENV" || echo "GOOGLE_DRIVE_SOURCE_FOLDER_ID=$DRIVE_FOLDER_ID" >> "$BACKEND_ENV"
        fi
        
        rm -f "$BACKEND_ENV.tmp"
    else
        echo -e "${RED}❌ Backend environment file not found at $BACKEND_ENV${NC}"
        exit 1
    fi
    
    # Update frontend .env.production
    if [ -f "$FRONTEND_ENV" ]; then
        sed -i.tmp "s/^NEXT_PUBLIC_GOOGLE_CLIENT_ID=.*/NEXT_PUBLIC_GOOGLE_CLIENT_ID=$CLIENT_ID/" "$FRONTEND_ENV"
        grep -q "^NEXT_PUBLIC_GOOGLE_CLIENT_ID=" "$FRONTEND_ENV" || echo "NEXT_PUBLIC_GOOGLE_CLIENT_ID=$CLIENT_ID" >> "$FRONTEND_ENV"
        rm -f "$FRONTEND_ENV.tmp"
    else
        echo -e "${RED}❌ Frontend environment file not found at $FRONTEND_ENV${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Environment files updated${NC}"
}

# Test OAuth configuration
test_oauth_configuration() {
    echo -e "${YELLOW}🧪 Testing OAuth configuration...${NC}"
    
    # Check if backend can read the credentials
    if docker-compose -f docker-compose.production.yml exec -T backend python -c "
from app.config import settings
print(f'Client ID loaded: {settings.google_client_id[:20]}...')
print(f'Client Secret loaded: ****{settings.google_client_secret[-4:]}')
exit(0 if settings.google_client_id != 'test_client_id' else 1)
" 2>/dev/null; then
        echo -e "${GREEN}✓ Backend OAuth configuration verified${NC}"
        return 0
    else
        echo -e "${RED}❌ Backend OAuth configuration test failed${NC}"
        return 1
    fi
}

# Main execution flow
main() {
    echo -e "${BLUE}🚀 Soleil OAuth Credentials Manager${NC}"
    echo ""
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.production.yml" ]; then
        echo -e "${RED}❌ Error: Must run from band-platform directory${NC}"
        exit 1
    fi
    
    # Backup existing credentials
    backup_existing_credentials
    
    # Get credentials interactively
    interactive_credential_input
    
    # Update environment files
    update_environment_files
    
    # Restart services if they're running
    if docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
        echo -e "${YELLOW}🔄 Restarting services to apply new credentials...${NC}"
        docker-compose -f docker-compose.production.yml restart backend frontend
        sleep 5
        
        # Test the configuration
        if test_oauth_configuration; then
            echo -e "${GREEN}✅ OAuth credentials successfully configured!${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not verify configuration. Please check logs.${NC}"
        fi
    else
        echo -e "${GREEN}✅ OAuth credentials saved. Will be used on next deployment.${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Ensure your Google OAuth consent screen is configured"
    echo "2. Add https://solepower.live/api/auth/google/callback to authorized redirect URIs"
    echo "3. Deploy or restart your application"
}

# Run main function
main "$@"