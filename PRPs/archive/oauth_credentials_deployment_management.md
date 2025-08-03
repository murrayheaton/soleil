name: "OAuth Credentials Secure Deployment Management"
description: |

## Purpose
Implement a robust and secure OAuth credentials management system that ensures Google OAuth credentials are properly transferred and configured during deployments without affecting other processes, with options for both interactive CLI input and secure transfer mechanisms.

## Core Principles
1. **Security First**: Never commit OAuth credentials to git, secure transfer methods only
2. **Zero Disruption**: Credentials setup must not interfere with other deployment processes
3. **User-Friendly**: Simple CLI interface for manual entry with validation
4. **Automated Options**: Support for secure automated transfer methods
5. **Rollback Safe**: Always backup existing credentials before updates

---

## Goal
Create a comprehensive OAuth credentials management system that:
- Provides interactive CLI for secure credential entry during deployment
- Supports encrypted credential transfer between environments
- Validates OAuth credentials before deployment continues
- Maintains separation from other deployment processes
- Provides clear feedback and error handling

## Why
- **Current Issue**: OAuth credentials are lost after each deployment, breaking authentication
- **Security Risk**: Credentials might be accidentally committed to git
- **User Experience**: Manual credential re-entry is error-prone and frustrating
- **Production Impact**: Authentication failures affect all users immediately
- **Compliance**: OAuth credentials require special handling for security

## What
A secure credentials management system integrated into the deployment workflow

### Success Criteria
- [ ] Interactive CLI for OAuth credential input at deployment start
- [ ] Encrypted credential storage and transfer mechanism
- [ ] Validation of credentials before deployment proceeds
- [ ] Zero impact on other deployment processes
- [ ] Clear documentation for both manual and automated methods
- [ ] Automatic backup of existing credentials
- [ ] Rollback procedure if credentials are invalid

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: /Users/murrayheaton/Documents/GitHub/soleil/band-platform/backend/app/config.py
  why: Shows how OAuth credentials are loaded and used
  
- file: /Users/murrayheaton/Documents/GitHub/soleil/band-platform/deploy.sh
  why: Current deployment script that needs credential management integration
  
- file: /Users/murrayheaton/Documents/GitHub/soleil/band-platform/.env.example
  why: Shows required OAuth environment variables
  
- file: /Users/murrayheaton/Documents/GitHub/soleil/CLAUDE.md
  why: Project conventions and security requirements
  
- url: https://developers.google.com/identity/protocols/oauth2
  why: Google OAuth requirements and best practices
```

### Current OAuth Configuration
```python
# From backend/app/config.py
google_client_id: str = Field(
    default="test_client_id",
    description="Google OAuth 2.0 Client ID",
)
google_client_secret: str = Field(
    default="test_client_secret", 
    description="Google OAuth 2.0 Client Secret",
)
google_redirect_uri: str = Field(
    default="http://localhost:8000/api/auth/google/callback",
    description="Google OAuth redirect URI"
)
```

### Required Environment Variables
```bash
# Backend OAuth variables
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback

# Frontend OAuth variables
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here

# Google Drive Integration
GOOGLE_DRIVE_SOURCE_FOLDER_ID=your_drive_folder_id_here
```

### Known Issues
```yaml
deployment_issues:
  - "OAuth credentials in .env files are not persisted across deployments"
  - "No validation of credentials before deployment"
  - "Manual credential entry is error-prone"
  - "No secure transfer mechanism between environments"
  - "Frontend and backend credentials must match"
  
security_concerns:
  - "Credentials might be accidentally committed"
  - "No encryption for credentials at rest"
  - "Plain text storage in .env files"
  - "No audit trail for credential changes"
```

## Implementation Blueprint

### 1. Create OAuth Credentials Manager Script
```bash
# File: band-platform/scripts/oauth_credentials_manager.sh
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
```

### 2. Create Encrypted Credentials Transfer Script
```bash
# File: band-platform/scripts/credentials_transfer.sh
#!/bin/bash

# This script provides secure transfer of OAuth credentials between environments
# Usage: ./credentials_transfer.sh [export|import] [passphrase]

set -e

OPERATION=$1
PASSPHRASE=$2
EXPORT_FILE="oauth_credentials.enc"

# Export credentials with encryption
export_credentials() {
    if [ -z "$PASSPHRASE" ]; then
        read -s -p "Enter encryption passphrase: " PASSPHRASE
        echo ""
    fi
    
    # Create temporary file with credentials
    TEMP_FILE=$(mktemp)
    echo "GOOGLE_CLIENT_ID=$(grep GOOGLE_CLIENT_ID backend/.env.production | cut -d= -f2)" > "$TEMP_FILE"
    echo "GOOGLE_CLIENT_SECRET=$(grep GOOGLE_CLIENT_SECRET backend/.env.production | cut -d= -f2)" >> "$TEMP_FILE"
    echo "GOOGLE_DRIVE_SOURCE_FOLDER_ID=$(grep GOOGLE_DRIVE_SOURCE_FOLDER_ID backend/.env.production | cut -d= -f2)" >> "$TEMP_FILE"
    
    # Encrypt the file
    openssl enc -aes-256-cbc -salt -in "$TEMP_FILE" -out "$EXPORT_FILE" -k "$PASSPHRASE"
    
    # Clean up
    rm -f "$TEMP_FILE"
    
    echo "✓ Credentials exported to $EXPORT_FILE"
    echo "Transfer this file securely to your deployment environment"
}

# Import credentials with decryption
import_credentials() {
    if [ ! -f "$EXPORT_FILE" ]; then
        echo "❌ Export file $EXPORT_FILE not found"
        exit 1
    fi
    
    if [ -z "$PASSPHRASE" ]; then
        read -s -p "Enter decryption passphrase: " PASSPHRASE
        echo ""
    fi
    
    # Decrypt the file
    TEMP_FILE=$(mktemp)
    openssl enc -aes-256-cbc -d -in "$EXPORT_FILE" -out "$TEMP_FILE" -k "$PASSPHRASE"
    
    # Source the credentials
    source "$TEMP_FILE"
    
    # Update environment files
    ./scripts/oauth_credentials_manager.sh <<EOF
$GOOGLE_CLIENT_ID
$GOOGLE_CLIENT_SECRET
$GOOGLE_DRIVE_SOURCE_FOLDER_ID
y
EOF
    
    # Clean up
    rm -f "$TEMP_FILE" "$EXPORT_FILE"
    
    echo "✓ Credentials imported successfully"
}

case "$OPERATION" in
    export)
        export_credentials
        ;;
    import)
        import_credentials
        ;;
    *)
        echo "Usage: $0 [export|import] [passphrase]"
        exit 1
        ;;
esac
```

### 3. Integrate with Deployment Script
```bash
# Updates to band-platform/deploy.sh

# Add near the beginning of the script, after parameter validation
echo -e "${BLUE}🔑 OAuth Credentials Setup${NC}"
echo "Do you need to configure OAuth credentials?"
echo "1) Enter credentials interactively"
echo "2) Import encrypted credentials file"
echo "3) Skip (credentials already configured)"
read -p "Select option (1-3): " OAUTH_OPTION

case $OAUTH_OPTION in
    1)
        # Make script executable and run
        chmod +x scripts/oauth_credentials_manager.sh
        ./scripts/oauth_credentials_manager.sh
        ;;
    2)
        # Import encrypted credentials
        chmod +x scripts/credentials_transfer.sh
        ./scripts/credentials_transfer.sh import
        ;;
    3)
        echo -e "${YELLOW}⚠️  Skipping OAuth setup. Ensure credentials are configured!${NC}"
        ;;
    *)
        echo -e "${RED}Invalid option. Continuing without OAuth setup.${NC}"
        ;;
esac

# Continue with rest of deployment...
```

### 4. Create Validation Script
```bash
# File: band-platform/scripts/validate_oauth.sh
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
```

## Testing & Validation

### Local Testing Steps
1. **Test Interactive Input**:
   ```bash
   cd band-platform
   ./scripts/oauth_credentials_manager.sh
   # Enter test credentials and verify files are updated
   ```

2. **Test Encrypted Transfer**:
   ```bash
   # On local machine
   ./scripts/credentials_transfer.sh export mypassword
   
   # On deployment machine
   scp user@local:~/oauth_credentials.enc .
   ./scripts/credentials_transfer.sh import mypassword
   ```

3. **Test Validation**:
   ```bash
   ./scripts/validate_oauth.sh
   ```

### Production Deployment Testing
1. **Fresh Deployment**:
   ```bash
   ./deploy.sh solepower.live admin@solepower.live
   # Choose option 1 for interactive credentials
   ```

2. **Update Existing Deployment**:
   ```bash
   ./scripts/oauth_credentials_manager.sh
   # Enter new credentials
   docker-compose -f docker-compose.production.yml restart backend frontend
   ```

## Rollback Plan

If OAuth credentials are incorrectly configured:

1. **Restore from Backup**:
   ```bash
   # List available backups
   ls -la .credentials_backup/
   
   # Restore specific backup
   cp .credentials_backup/backend_env_TIMESTAMP.bak backend/.env.production
   cp .credentials_backup/frontend_env_TIMESTAMP.bak frontend/.env.production
   
   # Restart services
   docker-compose -f docker-compose.production.yml restart backend frontend
   ```

2. **Manual Correction**:
   ```bash
   # Edit files directly if needed
   nano backend/.env.production
   nano frontend/.env.production
   
   # Restart services
   docker-compose -f docker-compose.production.yml restart backend frontend
   ```

## Post-Implementation

### Documentation Updates
1. Update `DEPLOYMENT_GUIDE.md` with new OAuth setup instructions
2. Add credentials management section to `README.md`
3. Update `DEV_LOG.md` with implementation details

### Security Checklist
- [ ] Ensure `.credentials_backup/` is added to `.gitignore`
- [ ] Verify no credentials are committed to git
- [ ] Test credential rotation procedure
- [ ] Document passphrase management for team

### Monitoring
- Set up alerts for OAuth authentication failures
- Monitor credential expiration dates
- Track failed authentication attempts

## Completion Checklist
- [ ] OAuth credentials manager script created and tested
- [ ] Encrypted transfer mechanism implemented
- [ ] Deployment script integrated with credentials setup
- [ ] Validation scripts working correctly
- [ ] Backup and restore procedures tested
- [ ] Documentation updated
- [ ] No credentials exposed in git history