name: "Fix OAuth Build-Time Injection for Docker"
description: |

## Purpose
Fix the fundamental OAuth configuration issue where Next.js frontend cannot access OAuth credentials during Docker build time, causing "OAuth not configured" errors. This implements a build-time injection system that maintains security while ensuring credentials are available when needed.

## Core Principles
1. **Build-Time Availability**: Ensure OAuth credentials are available during Docker build
2. **Security Maintained**: Keep credentials secure and out of git
3. **Single Source of Truth**: Maintain persistent credentials as the authoritative source
4. **Deployment Simplicity**: No manual intervention required after initial setup
5. **Backwards Compatible**: Work with existing persistent credentials system

---

## Goal
Create a build-time injection system that:
- Reads OAuth credentials from persistent storage before Docker build
- Passes credentials as Docker build arguments
- Ensures frontend has access to NEXT_PUBLIC_* variables during build
- Maintains security by not exposing credentials in images
- Works seamlessly with automated deployments

## Why
- **Current Problem**: Frontend is built without OAuth credentials because Docker can't access host files
- **User Impact**: "OAuth not configured" error prevents all logins
- **Root Cause**: Next.js requires NEXT_PUBLIC_* variables at build time, not runtime
- **Security**: Current system is secure but non-functional
- **Business Impact**: Platform is unusable without working authentication

## What
A Docker build argument system that injects OAuth credentials at build time

### Success Criteria
- [ ] Frontend builds with OAuth credentials available
- [ ] "Sign in with Google" button works immediately after deployment
- [ ] No manual credential entry required during deployment
- [ ] Credentials remain secure and out of git/images
- [ ] Works with existing persistent credentials system
- [ ] Clear error messages if credentials are missing
- [ ] Deployment process remains simple and automated

## All Needed Context

### Current Issue Analysis
```yaml
problem_flow:
  1. "/etc/soleil/oauth.env exists on host"
  2. "Docker build starts in isolated context"
  3. "Frontend Dockerfile can't access host files"
  4. "Next.js builds without NEXT_PUBLIC_GOOGLE_CLIENT_ID"
  5. "process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID is undefined"
  6. "Login page shows 'OAuth not configured'"

technical_constraint:
  - "Next.js bakes NEXT_PUBLIC_* into the build at compile time"
  - "Docker builds are isolated from host filesystem"
  - "env_file in docker-compose only works at runtime"
  - "Frontend needs credentials during 'npm run build' step"
```

### Required Credentials
```bash
# From /etc/soleil/oauth.env
GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
GOOGLE_DRIVE_SOURCE_FOLDER_ID=1PGL1NkfD39CDzVOxJt_X-rF48OAnd2kk

# Frontend needs (at build time)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
```

### User Context from Initial Request
> "My last three sessions trying to fix it. I haven't been able to and therefore haven't been able to continue development on my web app because I can't even get past the login screen."

This is blocking all development work and needs immediate resolution.

## Implementation Blueprint

### 1. Update Frontend Dockerfile to Accept Build Args
```dockerfile
# File: band-platform/frontend/Dockerfile (modifications)

# Stage 2: Builder
FROM node:18-alpine AS builder
WORKDIR /app

# Accept OAuth credentials as build arguments
ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID
ARG NEXT_PUBLIC_API_URL=https://solepower.live/api

# Set them as environment variables for the build
ENV NEXT_PUBLIC_GOOGLE_CLIENT_ID=$NEXT_PUBLIC_GOOGLE_CLIENT_ID
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Log for debugging (remove in production)
RUN echo "Building with CLIENT_ID: ${NEXT_PUBLIC_GOOGLE_CLIENT_ID:0:20}..."

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Remove the COPY .env.production line - we're using build args instead
# Build the application with injected variables
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Rest of the file remains the same...
```

### 2. Update Docker Compose to Pass Build Args
```yaml
# File: band-platform/docker-compose.production.yml (modifications)

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - NODE_ENV=production
        - NEXT_PUBLIC_GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
        - NEXT_PUBLIC_API_URL=https://solepower.live/api
    # Rest remains the same...
```

### 3. Update Deployment Script to Load and Export Credentials
```bash
# File: band-platform/deploy.sh (modifications)

# Add this function after the check_persistent_credentials function
load_oauth_for_build() {
    echo -e "${YELLOW}📦 Loading OAuth credentials for build...${NC}"
    
    if [ -f "/etc/soleil/oauth.env" ]; then
        # Source the credentials into the current shell
        set -a  # Mark all new variables for export
        source /etc/soleil/oauth.env
        set +a
        
        # Verify they're loaded
        if [ -z "$GOOGLE_CLIENT_ID" ]; then
            echo -e "${RED}❌ Failed to load OAuth credentials${NC}"
            return 1
        fi
        
        echo -e "${GREEN}✓ OAuth credentials loaded for build${NC}"
        echo -e "${BLUE}Client ID: ${GOOGLE_CLIENT_ID:0:20}...${NC}"
        return 0
    else
        echo -e "${RED}❌ No persistent credentials found${NC}"
        return 1
    fi
}

# Call this before the Docker build section
if ! load_oauth_for_build; then
    echo -e "${RED}Cannot proceed without OAuth credentials${NC}"
    exit 1
fi

# Remove the ensure_frontend_credentials.sh call - no longer needed
# The Docker build will now have access to the exported variables
```

### 4. Create Build-Time Validation Script
```bash
# File: band-platform/scripts/validate_build_oauth.sh
#!/bin/bash

# This script validates that OAuth credentials are properly injected during build

set -e

echo "🔍 Validating Build-Time OAuth Configuration..."

# Check if we can read the built frontend files
BUILT_FILE=$(find frontend/.next -name "*.js" -type f | head -1)

if [ -z "$BUILT_FILE" ]; then
    echo "❌ No built files found. Run build first."
    exit 1
fi

# Check if the client ID is baked into the build
if grep -q "360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172" "$BUILT_FILE"; then
    echo "✅ OAuth Client ID found in built files"
else
    echo "❌ OAuth Client ID NOT found in built files"
    echo "   The build may not have had access to credentials"
    exit 1
fi

echo "✅ Build-time OAuth validation complete!"
```

### 5. Update Backend Config for Robustness
```python
# File: band-platform/backend/app/config.py (modification)

import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    """Application settings with multiple credential sources."""
    
    def __init__(self, **kwargs):
        # Try multiple sources for credentials
        # 1. First, try persistent credentials
        persistent_creds = Path("/etc/soleil/oauth.env")
        if persistent_creds.exists():
            load_dotenv(persistent_creds)
            print(f"Loaded credentials from {persistent_creds}")
        
        # 2. Then try local .env.production
        local_env = Path(".env.production")
        if local_env.exists():
            load_dotenv(local_env, override=True)
            print(f"Loaded credentials from {local_env}")
        
        # 3. Environment variables take precedence
        super().__init__(**kwargs)
        
        # Log credential status (without exposing secrets)
        if self.google_client_id and not self.google_client_id.startswith("test_"):
            print(f"OAuth configured with client ID: {self.google_client_id[:20]}...")
        else:
            print("WARNING: OAuth not properly configured")
    
    # Credential fields with validation
    google_client_id: str = Field(
        default="",
        description="Google OAuth 2.0 Client ID",
    )
    
    google_client_secret: str = Field(
        default="",
        description="Google OAuth 2.0 Client Secret",
    )
    
    @property
    def oauth_configured(self) -> bool:
        """Check if OAuth is properly configured."""
        return bool(
            self.google_client_id 
            and self.google_client_secret 
            and not self.google_client_id.startswith("test_")
        )
```

### 6. Add Emergency Fallback Script
```bash
# File: band-platform/scripts/oauth_emergency_fix.sh
#!/bin/bash

# Emergency script to manually set OAuth credentials if automated system fails

echo "🚨 OAuth Emergency Fix"
echo "This script manually configures OAuth credentials"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo $0"
    exit 1
fi

# Create persistent credentials
mkdir -p /etc/soleil
cat > /etc/soleil/oauth.env << 'EOF'
# Soleil OAuth Credentials
GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
GOOGLE_DRIVE_SOURCE_FOLDER_ID=1PGL1NkfD39CDzVOxJt_X-rF48OAnd2kk
NEXT_PUBLIC_GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
EOF

chmod 600 /etc/soleil/oauth.env

echo "✅ Persistent credentials created"
echo ""
echo "Now run:"
echo "cd /path/to/band-platform"
echo "./deploy.sh solepower.live admin@solepower.live"
```

## Testing & Validation

### Pre-Deployment Testing
```bash
# Test credential loading
cd band-platform
source /etc/soleil/oauth.env
echo "Client ID: $GOOGLE_CLIENT_ID"

# Test Docker build with args
docker build \
  --build-arg NEXT_PUBLIC_GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
  -t test-frontend \
  ./frontend

# Verify build
docker run --rm test-frontend sh -c 'find /app/.next -name "*.js" | head -1 | xargs grep -l "360999037847"'
```

### Post-Deployment Testing
```bash
# Run validation script
./scripts/validate_build_oauth.sh

# Check running container
docker-compose -f docker-compose.production.yml exec frontend sh -c 'ps aux'

# Test the actual login page
curl -s https://solepower.live/login | grep -o "Sign in with Google"
```

### Browser Testing
1. Clear browser cache completely
2. Visit https://solepower.live/login
3. Open browser console
4. Look for: "Client ID: Present" in debug output
5. Click "Sign in with Google"
6. Verify redirect to Google OAuth

## Rollback Plan

If the build-time injection fails:

1. **Immediate Rollback**:
   ```bash
   # Revert to previous Dockerfile
   git checkout main~1 -- frontend/Dockerfile docker-compose.production.yml deploy.sh
   
   # Use emergency fix script
   sudo ./scripts/oauth_emergency_fix.sh
   
   # Manual build with credentials
   cd frontend
   echo "NEXT_PUBLIC_GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com" > .env.production
   cd ..
   docker-compose -f docker-compose.production.yml build frontend
   docker-compose -f docker-compose.production.yml up -d
   ```

2. **Alternative Approach**:
   - Switch to runtime configuration
   - Create API endpoint for public OAuth config
   - Modify login page to fetch config

## Post-Implementation

### Documentation Updates
- Update DEPLOYMENT_GUIDE.md with new build process
- Document build argument approach in README
- Add troubleshooting section for OAuth issues

### Monitoring
- Add build-time logging to verify credentials
- Monitor login success rates
- Alert on OAuth configuration errors

### Future Improvements
1. Implement HashiCorp Vault for secrets management
2. Add OAuth credential rotation system
3. Implement multiple OAuth providers
4. Add credential validation in CI/CD pipeline

## Completion Checklist
- [ ] Frontend Dockerfile accepts build arguments
- [ ] Docker Compose passes OAuth credentials during build
- [ ] Deployment script loads and exports credentials
- [ ] Build validation confirms credentials are injected
- [ ] Frontend login page shows "Sign in with Google" working
- [ ] No manual intervention required during deployment
- [ ] Emergency fallback script tested and documented
- [ ] All OAuth flows tested end-to-end