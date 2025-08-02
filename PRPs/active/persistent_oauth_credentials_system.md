name: "Persistent OAuth Credentials System - Server-Side Isolation"
description: |

## Purpose
Implement a persistent OAuth credentials system where credentials remain untouched on the server during deployments, eliminating the need to re-enter credentials after each code update. This creates a clear separation between code (which changes) and secrets (which don't).

## Core Principles
1. **Credentials Stay on Server**: OAuth secrets never leave the production server
2. **Deployment Doesn't Touch Secrets**: Git pulls and deployments only update code
3. **Simple and Reliable**: No complex encryption or transfer mechanisms needed
4. **Claude-Friendly**: Works with non-interactive deployment automation
5. **Industry Standard**: Follows common production practices

---

## Goal
Create a credential management system that:
- Stores OAuth credentials in a protected server-side location
- Keeps credentials separate from deployed code
- Automatically loads credentials into the application environment
- Survives all deployment and update cycles
- Works seamlessly with automated deployments

## Why
- **Current Problem**: Credentials are lost during deployments because .env files are overwritten
- **Interactive Scripts Don't Work**: Claude/automation can't handle interactive prompts
- **Security**: Credentials should never be in git or deployment packages
- **Simplicity**: One-time setup is better than repeated configuration
- **Reliability**: Deployments should "just work" without credential management

## What
A server-side credential isolation system with protected configuration files

### Success Criteria
- [ ] OAuth credentials persist through all deployments
- [ ] No manual credential entry required after initial setup
- [ ] Credentials never appear in git history
- [ ] Deployment process is simplified
- [ ] System works with automated/Claude deployments
- [ ] Clear documentation for initial setup
- [ ] Backup and recovery procedures documented

## All Needed Context

### Current Credential Flow Issues
```yaml
problems:
  - ".env.production files are created fresh during deployment"
  - "Templates overwrite existing credentials"
  - "Interactive scripts fail with automation"
  - "Credentials mixed with application configuration"
  
current_files:
  - "backend/.env.production - Gets overwritten"
  - "frontend/.env.production - Gets overwritten"
  - "deploy.sh - Creates fresh env files"
```

### Required OAuth Variables
```bash
# Backend Requirements
GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
GOOGLE_DRIVE_SOURCE_FOLDER_ID=1PGL1NkfD39CDzVOxJt_X-rF48OAnd2kk

# Frontend Requirements  
NEXT_PUBLIC_GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
```

## Implementation Blueprint

### 1. Create Protected Credentials Directory
```bash
# File: band-platform/scripts/setup_persistent_credentials.sh
#!/bin/bash

# This script sets up persistent OAuth credentials on the server
# Run this ONCE on your production server

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
GOOGLE_DRIVE_SOURCE_FOLDER_ID=your_folder_id_here

# Frontend OAuth Configuration
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_client_id_here
EOF

# Secure the file
sudo chmod 600 "$CREDS_DIR/oauth.env"
sudo chown root:root "$CREDS_DIR/oauth.env"

echo -e "${GREEN}✅ Credentials directory created at $CREDS_DIR${NC}"
echo -e "${YELLOW}⚠️  Now edit $CREDS_DIR/oauth.env with your actual credentials${NC}"
echo "Run: sudo nano $CREDS_DIR/oauth.env"
```

### 2. Create Systemd Service for Environment Loading
```bash
# File: band-platform/scripts/soleil-credentials.service
[Unit]
Description=Soleil OAuth Credentials Environment
Before=docker.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'mkdir -p /etc/soleil/runtime && cp /etc/soleil/oauth.env /etc/soleil/runtime/oauth.env && chmod 644 /etc/soleil/runtime/oauth.env'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### 3. Modify Docker Compose for Credential Loading
```yaml
# File: band-platform/docker-compose.production.yml (additions)
version: '3.8'

services:
  backend:
    env_file:
      - .env.production
      - /etc/soleil/oauth.env  # Load persistent credentials
    environment:
      - OAUTH_SOURCE=persistent
    
  frontend:
    env_file:
      - .env.production
      - /etc/soleil/oauth.env  # Load persistent credentials
```

### 4. Update Deployment Script to Preserve Credentials
```bash
# File: band-platform/deploy.sh (modifications)

# Remove the OAuth setup section entirely
# Remove credential-related "Next steps"

# Add credential check function
check_persistent_credentials() {
    if [ -f "/etc/soleil/oauth.env" ]; then
        echo -e "${GREEN}✓ Persistent OAuth credentials found${NC}"
        return 0
    else
        echo -e "${RED}❌ No persistent credentials found!${NC}"
        echo -e "${YELLOW}Please run: ./scripts/setup_persistent_credentials.sh${NC}"
        return 1
    fi
}

# Early in the script, after domain/email validation
if ! check_persistent_credentials; then
    echo -e "${RED}Cannot proceed without OAuth credentials${NC}"
    exit 1
fi

# Update environment file creation to NOT include OAuth variables
# Only include non-sensitive configuration
echo -e "${YELLOW}📝 Creating production environment file...${NC}"
cat > .env.production << EOF
# Domain configuration
DOMAIN=$DOMAIN
SSL_EMAIL=$EMAIL

# Secure passwords (auto-generated)
DB_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_password)

# Non-sensitive configuration
FRONTEND_URL=https://$DOMAIN
DEBUG=False
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["https://$DOMAIN", "https://www.$DOMAIN"]
APP_NAME="SOLEil"
LOG_LEVEL=INFO
EOF

# Similar updates for frontend/.env.production - exclude OAuth variables
```

### 5. Create Credential Management Utility
```bash
# File: band-platform/scripts/manage_persistent_credentials.sh
#!/bin/bash

# Utility to manage persistent OAuth credentials

CREDS_FILE="/etc/soleil/oauth.env"

case "$1" in
    show)
        if [ -f "$CREDS_FILE" ]; then
            echo "Current OAuth Configuration:"
            sudo grep -E "CLIENT_ID|FOLDER_ID" "$CREDS_FILE" | sed 's/SECRET=.*/SECRET=***HIDDEN***/'
        else
            echo "No credentials file found"
        fi
        ;;
    edit)
        sudo nano "$CREDS_FILE"
        echo "Credentials updated. Restart services to apply changes."
        ;;
    backup)
        BACKUP_FILE="/etc/soleil/oauth.env.backup.$(date +%Y%m%d_%H%M%S)"
        sudo cp "$CREDS_FILE" "$BACKUP_FILE"
        sudo chmod 600 "$BACKUP_FILE"
        echo "Backup created: $BACKUP_FILE"
        ;;
    validate)
        if [ -f "$CREDS_FILE" ]; then
            source "$CREDS_FILE"
            if [ -n "$GOOGLE_CLIENT_ID" ] && [ -n "$GOOGLE_CLIENT_SECRET" ]; then
                echo "✅ Credentials file is valid"
            else
                echo "❌ Credentials file is missing required values"
            fi
        else
            echo "❌ No credentials file found"
        fi
        ;;
    *)
        echo "Usage: $0 {show|edit|backup|validate}"
        exit 1
        ;;
esac
```

### 6. Application Code Updates
```python
# File: band-platform/backend/app/config.py (modification)

import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with persistent credential support."""
    
    def __init__(self, **kwargs):
        # Load persistent credentials first if available
        persistent_creds = Path("/etc/soleil/oauth.env")
        if persistent_creds.exists():
            load_dotenv(persistent_creds)
        
        # Then load regular .env (for non-sensitive config)
        super().__init__(**kwargs)
    
    # Rest of configuration remains the same...
```

## Testing & Validation

### Initial Setup Test
```bash
# On production server
cd band-platform
sudo ./scripts/setup_persistent_credentials.sh
sudo nano /etc/soleil/oauth.env  # Add real credentials
./scripts/manage_persistent_credentials.sh validate
```

### Deployment Test
```bash
# Deploy without touching credentials
git pull origin main
./deploy.sh solepower.live admin@solepower.live
# Should work without asking for OAuth credentials
```

### Persistence Test
```bash
# After deployment completes
docker-compose -f docker-compose.production.yml exec backend env | grep GOOGLE_CLIENT_ID
# Should show the credential from /etc/soleil/oauth.env
```

## Rollback Plan

If persistent credentials aren't working:

1. **Quick Fix**: Copy credentials back to .env files
   ```bash
   source /etc/soleil/oauth.env
   echo "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" >> backend/.env.production
   echo "GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET" >> backend/.env.production
   echo "NEXT_PUBLIC_GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" >> frontend/.env.production
   ```

2. **Full Rollback**: Revert to previous deployment method
   ```bash
   git checkout main~1 deploy.sh
   ./scripts/oauth_credentials_manager.sh
   ```

## Post-Implementation

### One-Time Server Setup
```bash
# SSH to production server
ssh root@droplet-ip

# Run setup
cd soleil/band-platform
./scripts/setup_persistent_credentials.sh

# Add credentials
sudo nano /etc/soleil/oauth.env
# Paste in the actual OAuth credentials

# Validate
./scripts/manage_persistent_credentials.sh validate
```

### Future Deployments
```bash
# Just pull and deploy - credentials persist!
git pull origin main
./deploy.sh solepower.live admin@solepower.live
```

### Documentation Updates
- Update DEPLOYMENT_GUIDE.md with persistent credential setup
- Add troubleshooting section for credential issues
- Document backup/restore procedures

## Security Benefits

1. **No Git Exposure**: Credentials never enter version control
2. **Limited Access**: Only root can read/modify credential file
3. **Separation of Concerns**: Code and secrets are completely separate
4. **Audit Trail**: All credential changes require sudo access
5. **Backup Safety**: Easy to backup without exposing in code

## Completion Checklist
- [ ] Persistent credentials directory created and secured
- [ ] Setup script tested and working
- [ ] Deployment script updated to check for credentials
- [ ] Docker Compose configured to load persistent credentials
- [ ] Management utility created for maintenance
- [ ] Initial credentials configured on server
- [ ] Full deployment tested without credential prompts
- [ ] Documentation updated with new process