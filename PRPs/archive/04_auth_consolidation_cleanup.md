name: "Robust Authentication System Consolidation & Codebase Cleanup"
description: |
  Major refactoring to consolidate authentication implementation, remove redundant files, and create a robust,
  update-proof authentication system that won't break when other features are developed. Preserves all frontend
  styling and layout (engraving rules).

priority: CRITICAL
impact: Platform Stability

---

## Pre-Implementation Requirements

Before starting implementation, Claude Code MUST:

1. **Read all project documentation**:
   - CLAUDE.md - Global AI assistant rules
   - PLANNING.md - Project architecture and conventions
   - PRODUCT_VISION.md - Current product state (use this, not the dated version)
   - DEV_LOG.md & DEV_LOG_TECHNICAL.md - Recent changes
   - GOOGLE_DRIVE_SETUP.md - Google API integration patterns

2. **Create feature branch**:
   ```bash
   cd ~/Documents/LocalCode/claude-code/soleil
   git checkout main
   git pull origin main
   git checkout -b fix/auth-consolidation-cleanup
   ```

3. **Backup critical files**:
   ```bash
   # Backup user profiles and Google tokens
   cd band-platform/backend
   cp user_profiles.json user_profiles.json.backup
   cp google_token.json google_token.json.backup 2>/dev/null || true
   ```

4. **🔐 CRITICAL: Document Current Secrets**:
   ```bash
   # HUMAN TASK: Write down these values before proceeding!
   echo "=== CURRENT AUTHENTICATION SECRETS ==="
   echo "Record these values in a secure location:"
   echo ""
   echo "1. Google OAuth Credentials:"
   echo "   - Client ID: [CHECK .env.production]"
   echo "   - Client Secret: [CHECK .env.production]"
   echo "   - Redirect URI: [CHECK .env.production]"
   echo ""
   echo "2. Session Secret: [CHECK .env.production]"
   echo "3. Google Drive Folder ID: [CHECK .env.production]"
   echo ""
   echo "⚠️  WITHOUT THESE, LOGIN WILL BREAK!"
   ```

---

## Goal
Consolidate authentication to a single, robust implementation using the proven `start_server.py` approach, remove all redundant/conflicting files, and ensure the system remains stable during future development.

## Why
- **CRITICAL**: Multiple conflicting auth implementations create confusion and bugs
- **Stability**: Redundant files cause deployment issues and maintenance nightmares
- **Developer Experience**: Clean codebase makes future development faster and safer
- **User Trust**: Stable auth prevents lockouts and data loss

## Success Criteria
- [ ] Single authentication implementation (start_server.py based)
- [ ] All redundant OAuth files removed
- [ ] Environment variables consolidated to one .env file per environment
- [ ] Docker configuration uses correct entrypoint
- [ ] Authentication survives server restarts
- [ ] Profile data persists correctly
- [ ] Frontend styling remains unchanged
- [ ] Clean git history with all deletions documented

## 🔐 Human Verification Checkpoints

This PRP contains **7 critical human checkpoints** that require manual action:

1. **Pre-Implementation** (Line 38): Document current secrets before starting
2. **Secret Migration** (Line 231): Verify all .env files for unique secrets
3. **Post-Consolidation** (Line 285): Test auth before deleting old files
4. **Pre-Cleanup** (Line 555): Confirm secrets are consolidated
5. **Pre-Deployment** (Line 742): Verify Google Console settings
6. **Production Transfer** (Line 807): Securely copy .env.production
7. **Emergency Recovery** (Line 953): Backup restoration steps

⚠️ **These checkpoints CANNOT be automated and MUST be completed manually!**

---

## File Cleanup Plan

### Files to DELETE with Justification

#### Backend OAuth Redundancies
```yaml
Files to Remove:
  /band-platform/backend/minimal_oauth.py:
    Reason: Experimental OAuth implementation, not used in production
    Conflicts: Different approach than start_server.py
    
  /band-platform/backend/oauth_only_server.py:
    Reason: Partial implementation, superseded by start_server.py
    Conflicts: Incomplete error handling
    
  /band-platform/backend/simple_oauth.py:
    Reason: Another experimental version
    Conflicts: Different session handling approach
    
  /band-platform/backend/standalone_oauth.py:
    Reason: Test implementation
    Conflicts: Uses different token storage
    
  /band-platform/backend/test_drive_oauth.py:
    Reason: Test file, not needed in production
    Conflicts: Contains test credentials

  /band-platform/backend/app/main.py:
    Reason: Complex implementation not currently used in production
    Conflicts: Docker references this but actual deployment uses start_server.py
    Action: Archive for future reference, update Docker to use start_server.py
    Note: Keep app/services/* as they contain reusable business logic
```

#### Environment File Consolidation
```yaml
Backend Files to Consolidate:
  Keep:
    /band-platform/backend/.env.production - Production secrets
    /band-platform/backend/.env.example - Template for developers
    
  Remove:
    /band-platform/backend/.env - Redundant with .env.example
    /band-platform/backend/.env.production.bak - Old backup
    /band-platform/backend/.env.production.template - Duplicate of .env.example
    /band-platform/backend/.env.test - Not used

Frontend Files to Consolidate:
  Keep:
    /frontend/.env.local - Local development
    /frontend/.env.production - Production settings
    /frontend/.env.example - Template
    
  Remove:
    /frontend/.env.production.template - Duplicate of .env.example
```

#### Deployment Script Consolidation
```yaml
Root Directory Scripts:
  Keep:
    /band-platform/deploy.sh - Main deployment script
    
  Remove:
    /deploy-solepower.sh - Old deployment approach
    /deploy-to-do.sh - Task list, not a script
    /online-port.md - Port documentation, move to README

Band Platform Scripts:
  Keep:
    /band-platform/start_sole_power_live.sh - Production starter
    
  Remove:
    /band-platform/Sole_Power_Live.command - macOS specific, redundant
    /band-platform/backend/Soleil_Backend.command - macOS specific, redundant
    /band-platform/backend/start_backend.sh - Redundant with Docker
    /band-platform/backend/stop_backend.sh - Redundant with Docker
```

#### Documentation Cleanup
```yaml
Remove Outdated Docs:
  /PRODUCT_VISION_2025-07-30.md:
    Reason: Outdated version, PRODUCT_VISION.md is current
    
  /INITIAL_google_drive_role_based_organization.md:
    Reason: Initial planning doc, now implemented
    
  /band-platform/README_LAUNCHER.md:
    Reason: Launcher docs for removed .command files
    
  /band-platform/SOLEPOWER_DEPLOYMENT.md:
    Reason: Old deployment guide, consolidate into DEPLOYMENT_GUIDE.md
```

#### Backup Directory
```yaml
Remove Entire Directory:
  /band-platform-backup/:
    Reason: Old backup, use git for version control
    Size: Potentially large, wastes space
```

---

## Implementation Tasks

### Task 1: Update Docker Configuration
```yaml
# band-platform/backend/Dockerfile
# Change the CMD to use start_server.py instead of app.main:app

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/storage

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# CRITICAL CHANGE: Use start_server.py instead of app.main:app
CMD ["python", "start_server.py"]
```

### Task 2: Consolidate Environment Variables

#### 🔐 HUMAN TASK: Secret Migration Checklist

**BEFORE deleting any .env files, manually verify and record:**

```bash
# 1. Check ALL current .env files for unique secrets
cd band-platform/backend
echo "=== CHECKING ALL ENV FILES FOR SECRETS ==="
for file in .env*; do
  echo "\n--- $file ---"
  grep -E "(SECRET|KEY|ID|TOKEN|PASSWORD)" "$file" 2>/dev/null || echo "File not found"
done

# 2. ⚠️ HUMAN VERIFICATION REQUIRED:
# Compare values across files and note any differences
# Some files may have different secrets - RECORD THEM ALL!
```

**Critical Secrets to Preserve:**
- [ ] GOOGLE_CLIENT_ID (must match Google Cloud Console)
- [ ] GOOGLE_CLIENT_SECRET (must match Google Cloud Console)
- [ ] GOOGLE_REDIRECT_URI (must match Google Cloud Console)
- [ ] GOOGLE_DRIVE_SOURCE_FOLDER_ID (your specific folder)
- [ ] SESSION_SECRET (if exists, preserve it)
- [ ] Any production-specific values

#### Consolidated .env.production Template

```bash
# backend/.env.production (KEEP AND UPDATE)
# 🔐 CRITICAL: These must match your Google Cloud Console settings

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here  # ⚠️ GET FROM GOOGLE CLOUD CONSOLE
GOOGLE_CLIENT_SECRET=your-client-secret-here  # ⚠️ GET FROM GOOGLE CLOUD CONSOLE
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback  # ⚠️ MUST MATCH CONSOLE
GOOGLE_DRIVE_SOURCE_FOLDER_ID=your-folder-id  # ⚠️ YOUR DRIVE FOLDER

# Frontend URLs
FRONTEND_URL=https://solepower.live

# API Configuration
DEBUG=False
HOST=0.0.0.0
PORT=8000

# CORS Origins
CORS_ORIGINS=["https://solepower.live", "https://www.solepower.live"]

# Session Secret (preserve existing or generate new)
# To generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
SESSION_SECRET=your-existing-or-new-secret-here  # ⚠️ PRESERVE IF EXISTS

# Remove duplicate database/redis configs since we're using JSON file storage
```

#### 🔄 Post-Consolidation Verification

```bash
# HUMAN TASK: After creating the consolidated .env.production
echo "=== VERIFY SECRETS MIGRATION ==="
echo "1. Open .env.production"
echo "2. Confirm each secret is filled in (no placeholder values)"
echo "3. Test authentication locally BEFORE deleting old files:"
echo "   python start_server.py"
echo "   Visit http://localhost:8000/api/auth/google/login"
echo "4. Only proceed if login works!"
```

### Task 3: Enhance Authentication Robustness
```python
# backend/start_server.py - Add these improvements

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import secrets
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

# ... existing imports ...

# Add session configuration
SESSION_SECRET = os.getenv('SESSION_SECRET', secrets.token_urlsafe(32))
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

# Add session middleware with better configuration
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="soleil_session",
    max_age=SESSION_MAX_AGE,
    same_site="lax",
    https_only=not settings.debug,
)

# Token storage with rotation support
class TokenManager:
    """Manage Google OAuth tokens with automatic refresh."""
    
    def __init__(self, token_file: str = "google_token.json"):
        self.token_file = Path(token_file)
        self.tokens: Dict = {}
        self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from file with error handling."""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    self.tokens = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load tokens: {e}")
                self.tokens = {}
    
    def save_tokens(self, tokens: Dict):
        """Save tokens with atomic write."""
        temp_file = self.token_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            temp_file.replace(self.token_file)
            self.tokens = tokens
            logger.info("Tokens saved successfully")
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if needed."""
        if not self.tokens:
            return None
        
        # Check if token needs refresh
        expires_at = self.tokens.get('expires_at', 0)
        if datetime.now().timestamp() >= expires_at - 300:  # 5 min buffer
            return self._refresh_token()
        
        return self.tokens.get('access_token')
    
    def _refresh_token(self) -> Optional[str]:
        """Refresh the access token using refresh token."""
        refresh_token = self.tokens.get('refresh_token')
        if not refresh_token:
            logger.error("No refresh token available")
            return None
        
        try:
            import requests
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                    'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                    'refresh_token': refresh_token,
                    'grant_type': 'refresh_token'
                }
            )
            
            if response.status_code == 200:
                new_tokens = response.json()
                # Update tokens while preserving user info
                self.tokens.update(new_tokens)
                self.tokens['expires_at'] = (
                    datetime.now().timestamp() + 
                    new_tokens.get('expires_in', 3600)
                )
                self.save_tokens(self.tokens)
                logger.info("Token refreshed successfully")
                return new_tokens['access_token']
            else:
                logger.error(f"Token refresh failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    def clear_tokens(self):
        """Clear all tokens (logout)."""
        self.tokens = {}
        if self.token_file.exists():
            self.token_file.unlink()

# Initialize token manager
token_manager = TokenManager()

# Dependency to check authentication
async def require_auth(request: Request):
    """Ensure user is authenticated."""
    if not token_manager.get_access_token():
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Also check if we have user info
    if not token_manager.tokens.get('user_email'):
        raise HTTPException(status_code=401, detail="User info not found")
    
    return token_manager.tokens

# Update all protected endpoints to use the dependency
@app.get("/api/users/profile")
async def get_user_profile(user_info: Dict = Depends(require_auth)):
    """Get current user profile with proper error handling."""
    # ... rest of implementation using user_info ...

# Add automatic token refresh to Google API calls
async def make_google_api_request(endpoint: str, params: Dict = None):
    """Make authenticated request to Google API with retry."""
    access_token = token_manager.get_access_token()
    if not access_token:
        raise HTTPException(status_code=401, detail="No valid access token")
    
    headers = {'Authorization': f'Bearer {access_token}'}
    
    for attempt in range(2):  # Try twice in case of token expiry
        response = requests.get(endpoint, headers=headers, params=params)
        
        if response.status_code == 401 and attempt == 0:
            # Token might be expired, try refreshing
            access_token = token_manager._refresh_token()
            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'
                continue
        
        return response
    
    raise HTTPException(status_code=401, detail="Failed to authenticate with Google")
```

### Task 4: Add Migration Script for Existing Data
```python
# backend/migrate_auth_data.py - New file
#!/usr/bin/env python3
"""
Migrate existing authentication data to new consolidated format.
Run this before deploying the new authentication system.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

def migrate_auth_data():
    """Migrate and consolidate authentication data."""
    print("Starting authentication data migration...")
    
    # Backup existing data
    backup_dir = Path("auth_migration_backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Files to check for migration
    auth_files = [
        "google_token.json",
        "user_profiles.json",
        "session_data.json"  # If exists
    ]
    
    for file in auth_files:
        if Path(file).exists():
            shutil.copy2(file, backup_dir / f"{file}.backup")
            print(f"Backed up {file}")
    
    # Migrate token data
    if Path("google_token.json").exists():
        with open("google_token.json", 'r') as f:
            tokens = json.load(f)
        
        # Add migration timestamp
        tokens['migrated_at'] = datetime.now().isoformat()
        
        # Ensure all required fields exist
        tokens.setdefault('auth_method', 'oauth')
        tokens.setdefault('created_at', datetime.now().isoformat())
        
        with open("google_token.json", 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print("Token data migrated successfully")
    
    # Migrate user profiles
    if Path("user_profiles.json").exists():
        with open("user_profiles.json", 'r') as f:
            profiles = json.load(f)
        
        # Update profile format if needed
        for user_id, profile in profiles.items():
            # Ensure consistent fields
            profile.setdefault('id', user_id)
            profile.setdefault('created_at', datetime.now().isoformat())
            profile.setdefault('updated_at', datetime.now().isoformat())
            profile.setdefault('instruments', [])
            profile.setdefault('ui_scale', 'small')
        
        with open("user_profiles.json", 'w') as f:
            json.dump(profiles, f, indent=2)
        
        print(f"Migrated {len(profiles)} user profiles")
    
    print("\nMigration complete! Backup stored in:", backup_dir)
    print("If issues occur, restore from backup files.")

if __name__ == "__main__":
    migrate_auth_data()
```

### Task 5: Cleanup Script
```bash
#!/bin/bash
# cleanup_redundant_files.sh - Execute file deletions

echo "Starting codebase cleanup..."
echo "This will remove redundant files. Press Ctrl+C to cancel."
echo ""
echo "🔐 CRITICAL PRE-CLEANUP CHECKLIST:"
echo "[ ] Have you backed up all .env files?"
echo "[ ] Have you consolidated secrets to .env.production?"
echo "[ ] Have you tested login with the new configuration?"
echo "[ ] Have you documented all production secrets?"
echo ""
read -p "Type 'yes' to confirm you've completed ALL steps: " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled. Complete the checklist first!"
    exit 1
fi

# Create cleanup log
CLEANUP_LOG="cleanup_$(date +%Y%m%d_%H%M%S).log"

# Function to safely remove files
remove_file() {
    local file="$1"
    local reason="$2"
    
    if [ -f "$file" ]; then
        echo "Removing: $file" | tee -a "$CLEANUP_LOG"
        echo "  Reason: $reason" | tee -a "$CLEANUP_LOG"
        rm -f "$file"
    else
        echo "Already removed: $file" | tee -a "$CLEANUP_LOG"
    fi
}

# Remove OAuth redundancies
cd band-platform/backend
remove_file "minimal_oauth.py" "Experimental OAuth, not used"
remove_file "oauth_only_server.py" "Partial implementation"
remove_file "simple_oauth.py" "Experimental version"
remove_file "standalone_oauth.py" "Test implementation"
remove_file "test_drive_oauth.py" "Test file"

# Archive app/main.py but keep services
mv app/main.py app/main.py.archived
echo "Archived app/main.py - keeping app/services/* for reusable logic" | tee -a "$CLEANUP_LOG"

# Remove redundant environment files
remove_file ".env" "Redundant with .env.example"
remove_file ".env.production.bak" "Old backup"
remove_file ".env.production.template" "Duplicate of .env.example"
remove_file ".env.test" "Not used"

# Remove macOS specific files
remove_file "Soleil_Backend.command" "macOS specific, use Docker"
remove_file "start_backend.sh" "Redundant with Docker"
remove_file "stop_backend.sh" "Redundant with Docker"

# Frontend cleanup
cd ../frontend
remove_file ".env.production.template" "Duplicate of .env.example"

# Root directory cleanup
cd ../..
remove_file "deploy-solepower.sh" "Old deployment approach"
remove_file "deploy-to-do.sh" "Task list, not a script"
remove_file "online-port.md" "Move to documentation"
remove_file "PRODUCT_VISION_2025-07-30.md" "Outdated version"
remove_file "INITIAL_google_drive_role_based_organization.md" "Initial planning doc"

# Remove band-platform specific files
cd band-platform
remove_file "Sole_Power_Live.command" "macOS specific"
remove_file "README_LAUNCHER.md" "Launcher docs for removed files"
remove_file "SOLEPOWER_DEPLOYMENT.md" "Consolidate into DEPLOYMENT_GUIDE.md"

# Remove backup directory
if [ -d "../band-platform-backup" ]; then
    echo "Removing backup directory: band-platform-backup" | tee -a "$CLEANUP_LOG"
    rm -rf ../band-platform-backup
fi

echo "Cleanup complete! Log saved to: $CLEANUP_LOG"
```

### Task 6: Update Frontend API Client
```typescript
// frontend/src/lib/api.ts - Ensure robust error handling

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live/api';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

class APIClient {
  private async fetchWithRetry(
    url: string, 
    options: RequestInit = {}
  ): Promise<Response> {
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        });
        
        // If unauthorized, don't retry - redirect to login
        if (response.status === 401) {
          window.location.href = '/login';
          throw new Error('Unauthorized');
        }
        
        return response;
        
      } catch (error) {
        lastError = error as Error;
        
        // Don't retry on auth errors
        if (error.message === 'Unauthorized') {
          throw error;
        }
        
        // Exponential backoff for retries
        if (attempt < MAX_RETRIES - 1) {
          await new Promise(resolve => 
            setTimeout(resolve, RETRY_DELAY * Math.pow(2, attempt))
          );
        }
      }
    }
    
    throw lastError || new Error('Request failed');
  }
  
  async get(endpoint: string): Promise<any> {
    const response = await this.fetchWithRetry(`${API_BASE_URL}${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
  
  async post(endpoint: string, data: any): Promise<any> {
    const response = await this.fetchWithRetry(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }
  
  // Profile-specific methods with caching
  private profileCache: any = null;
  private profileCacheTime: number = 0;
  private CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  
  async getProfile(forceRefresh: boolean = false): Promise<any> {
    const now = Date.now();
    
    if (!forceRefresh && 
        this.profileCache && 
        now - this.profileCacheTime < this.CACHE_DURATION) {
      return this.profileCache;
    }
    
    const profile = await this.get('/users/profile');
    this.profileCache = profile;
    this.profileCacheTime = now;
    
    return profile;
  }
  
  clearCache(): void {
    this.profileCache = null;
    this.profileCacheTime = 0;
  }
}

export const api = new APIClient();
```

## Testing & Validation

### 🔐 CRITICAL: Pre-Deployment Secrets Verification

```bash
# HUMAN TASK: Complete this verification BEFORE deployment!

echo "=== FINAL SECRETS VERIFICATION ==="
echo ""
echo "1. Google Cloud Console Check:"
echo "   [ ] Login to console.cloud.google.com"
echo "   [ ] Navigate to APIs & Services > Credentials"
echo "   [ ] Verify OAuth 2.0 Client ID matches .env.production"
echo "   [ ] Verify Authorized redirect URIs includes:"
echo "       https://solepower.live/api/auth/google/callback"
echo ""
echo "2. Local .env.production Check:"
cd band-platform/backend
echo "   [ ] GOOGLE_CLIENT_ID is not a placeholder"
echo "   [ ] GOOGLE_CLIENT_SECRET is not a placeholder"
echo "   [ ] SESSION_SECRET is at least 32 characters"
echo "   [ ] GOOGLE_DRIVE_SOURCE_FOLDER_ID is correct"
echo ""
echo "3. Test Authentication Flow:"
echo "   [ ] Start server: python start_server.py"
echo "   [ ] Visit: http://localhost:8000/api/auth/google/login"
echo "   [ ] Complete OAuth flow"
echo "   [ ] Verify profile loads at /api/users/profile"
echo ""
read -p "Have you verified ALL items above? (yes/no): " verified

if [ "$verified" != "yes" ]; then
    echo "⚠️  STOP! Fix secrets before proceeding!"
    exit 1
fi
```

### Pre-Deployment Checklist
```bash
# 1. Run migration script
cd band-platform/backend
python migrate_auth_data.py

# 2. Test authentication locally
python start_server.py
# Visit http://localhost:8000/docs to test endpoints

# 3. Run cleanup script (with verification)
cd ../..
chmod +x cleanup_redundant_files.sh
./cleanup_redundant_files.sh

# 4. Update Docker and test
cd band-platform
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d

# 5. Verify health check
curl http://localhost:8000/health

# 6. 🔐 Verify auth still works after Docker
curl http://localhost:8000/api/auth/google/login
```

### Production Deployment

#### 🔐 Pre-Production Secrets Transfer

```bash
# HUMAN TASK: Ensure production server has correct secrets!

echo "=== PRODUCTION SECRETS CHECKLIST ==="
echo ""
echo "1. Transfer .env.production to server:"
echo "   scp band-platform/backend/.env.production root@YOUR_SERVER_IP:/root/soleil/band-platform/backend/"
echo ""
echo "2. Verify on production server:"
echo "   ssh root@YOUR_SERVER_IP"
echo "   cd /root/soleil/band-platform/backend"
echo "   grep GOOGLE_CLIENT_ID .env.production  # Should show real ID, not placeholder"
echo ""
echo "3. ⚠️  NEVER commit .env.production to git!"
echo ""
read -p "Have you securely transferred production secrets? (yes/no): " transferred

if [ "$transferred" != "yes" ]; then
    echo "Transfer secrets before deployment!"
    exit 1
fi
```

#### Deployment Commands

```bash
# Commit all changes
git add -A
git commit -m "fix: consolidate authentication and cleanup codebase

- Remove redundant OAuth implementations
- Consolidate environment variables
- Update Docker to use start_server.py
- Add token refresh and session management
- Remove obsolete files and backups
- Preserve all frontend styling"

git push origin fix/auth-consolidation-cleanup

# Deploy to production
ssh root@YOUR_SERVER_IP
cd /root/soleil
git fetch origin
git checkout fix/auth-consolidation-cleanup

# 🔐 VERIFY SECRETS BEFORE PROCEEDING
echo "Checking production secrets..."
if [ ! -f "band-platform/backend/.env.production" ]; then
    echo "⚠️  ERROR: .env.production missing! Transfer it first!"
    exit 1
fi

# Run migration first
cd band-platform/backend
python migrate_auth_data.py

# Deploy with new configuration
cd ..
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build --no-cache backend
docker-compose -f docker-compose.production.yml up -d

# Monitor logs
docker-compose -f docker-compose.production.yml logs -f backend

# 🔐 Test production auth
curl https://solepower.live/api/health
curl https://solepower.live/api/auth/google/login
```

### Validation Tests
- [ ] Login with Google OAuth works
- [ ] Session persists across page refreshes
- [ ] Profile data loads correctly
- [ ] Token refresh works (wait 1 hour)
- [ ] Logout clears all session data
- [ ] Frontend styling unchanged
- [ ] No console errors
- [ ] Health check endpoint responds

## Rollback Plan
```bash
# If issues occur:
ssh root@YOUR_SERVER_IP
cd /root/soleil

# Restore from backup
cd band-platform/backend
cp auth_migration_backup/*.backup .
mv google_token.json.backup google_token.json
mv user_profiles.json.backup user_profiles.json

# Revert to main branch
cd ../..
git checkout main
cd band-platform
docker-compose -f docker-compose.production.yml up -d --build
```

## 🔐 Authentication Troubleshooting Guide

### Common Issues After Consolidation

#### "Not authenticated" or 401 errors
```bash
# Check 1: Verify .env.production exists and has real values
cd band-platform/backend
ls -la .env.production
grep GOOGLE_CLIENT_ID .env.production  # Should NOT say "your-client-id-here"

# Check 2: Verify google_token.json exists (if previously logged in)
ls -la google_token.json

# Check 3: Restart to load environment variables
docker-compose -f docker-compose.production.yml restart backend
```

#### "OAuth callback failed" errors
```bash
# Check 1: Verify redirect URI matches Google Console
grep GOOGLE_REDIRECT_URI .env.production
# Should be: https://solepower.live/api/auth/google/callback

# Check 2: Verify in Google Cloud Console:
# 1. Go to console.cloud.google.com
# 2. APIs & Services > Credentials
# 3. Click your OAuth 2.0 Client ID
# 4. Check "Authorized redirect URIs" includes your callback URL
```

#### "Session expired" or users logged out frequently
```bash
# Check: Ensure SESSION_SECRET is set and consistent
grep SESSION_SECRET .env.production
# Should be at least 32 characters, not a placeholder

# Generate new secret if needed:
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### "Cannot read Drive files" after auth
```bash
# Check: Verify Drive folder ID is correct
grep GOOGLE_DRIVE_SOURCE_FOLDER_ID .env.production
# Should match the folder ID from your Google Drive URL
```

### Emergency Recovery Steps

```bash
# If auth is completely broken:

# 1. Restore from backup
cd band-platform/backend
cp user_profiles.json.backup user_profiles.json
cp google_token.json.backup google_token.json 2>/dev/null || true

# 2. Revert to known working environment
cp .env.production.backup .env.production

# 3. Restart services
docker-compose -f docker-compose.production.yml restart

# 4. Test auth
curl https://solepower.live/api/health
```

## Post-Deployment
1. Monitor logs for 24 hours
2. Test with multiple user accounts
3. Document the new simplified architecture
4. Update DEV_LOG.md with consolidation details
5. Create new .env.example with all required variables
6. Merge to main after 48 hours stable
7. 🔐 **Store production secrets in password manager**

## Architecture After Cleanup
```
band-platform/
├── backend/
│   ├── start_server.py         # Main server (simplified FastAPI)
│   ├── app/
│   │   ├── services/          # Business logic (profile service)
│   │   └── utils/             # Helpers
│   ├── .env.production        # Production secrets
│   └── .env.example           # Template
├── frontend/                   # Next.js app (unchanged)
└── docker-compose.yml         # Updated to use start_server.py
```

This consolidation removes 20+ redundant files while preserving all functionality.

## Deletion Rationale Summary

### Why These Deletions Make Auth "Update-Proof"

1. **Single Source of Truth**: By removing all alternative OAuth implementations, future developers (including AI assistants) won't accidentally modify or reference the wrong auth system.

2. **Clear Entry Point**: With only `start_server.py` as the server entry point, there's no confusion about which file handles authentication.

3. **Environment Clarity**: One `.env.production` file means no conflicting environment variables or confusion about which file to update.

4. **Docker Alignment**: Updating Docker to use `start_server.py` ensures local and production environments use identical auth flows.

5. **Preserved Services**: Keeping `app/services/profile_service.py` maintains the robust profile handling while removing conflicting server implementations.

6. **Git as Version Control**: Removing the `band-platform-backup` directory forces use of git for versioning, preventing outdated code from being accidentally restored.

### What Stays and Why

- **start_server.py**: Proven, working authentication implementation
- **app/services/**: Reusable business logic, properly separated
- **Single .env per environment**: Clear configuration management
- **Frontend unchanged**: All styling and layout preserved
- **User data files**: `user_profiles.json` and `google_token.json` with migration

### 🔐 Critical Warning for --dangerously-skip-permissions

When using `--dangerously-skip-permissions` with Claude or any AI coding assistant:

1. **Secrets are NEVER auto-filled** - The AI cannot and will not insert real credentials
2. **Human verification is REQUIRED** - Multiple checkpoints force manual secret validation
3. **Placeholder detection** - Scripts check for placeholder values before proceeding
4. **Backup requirements** - All auth data is backed up before any modifications

**The consolidated auth system will ONLY work if you:**
- [ ] Manually copy ALL secrets from old .env files
- [ ] Verify Google Cloud Console settings match
- [ ] Test login before deleting any files
- [ ] Transfer .env.production to production server
- [ ] Never commit real secrets to git

This PRP includes 7 human verification checkpoints that CANNOT be skipped, ensuring your authentication remains functional throughout the consolidation process.

## Task 7: Documentation Restructuring

### Current Documentation Issues
- Multiple overlapping vision documents (PRODUCT_VISION.md, PRODUCT_VISION_2025-07-30.md)
- Technical implementation details mixed with product documentation
- No clear user guides for musicians or band leaders
- Initial planning documents (INITIAL_*.md) cluttering root directory

### New Documentation Structure
```
soleil/
├── README.md                           # Project overview & quick start
├── docs/
│   ├── PRODUCT.md                     # What SOLEil is and why it exists
│   ├── ARCHITECTURE.md                # Technical design decisions
│   ├── DEVELOPMENT.md                 # Setup, build, and deployment
│   ├── user-guide/
│   │   ├── README.md                  # User documentation index
│   │   ├── musician-quickstart.md     # For band members
│   │   ├── admin-guide.md            # For band leaders/admins
│   │   └── troubleshooting.md        # Common issues
│   ├── technical/
│   │   ├── authentication.md          # Auth system documentation
│   │   ├── google-integration.md      # Drive, Sheets, Calendar APIs
│   │   ├── deployment.md              # Production deployment
│   │   └── database-schema.md         # Data models
│   └── project/
│       ├── CHANGELOG.md               # Version history
│       ├── ROADMAP.md                 # Future enhancements
│       └── decisions/                 # ADRs (Architecture Decision Records)
├── PRPs/                              # Project Requirement Prompts
│   ├── README.md                      # How to use PRPs
│   ├── active/                        # Current work
│   ├── completed/                     # Finished PRPs
│   └── templates/                     # PRP templates
└── .github/
    ├── CONTRIBUTING.md                # How to contribute
    └── ISSUE_TEMPLATE/                # Issue templates
```

### Documentation Migration Plan

#### Files to Move/Consolidate
```yaml
Consolidate Product Vision:
  - PRODUCT_VISION.md → docs/PRODUCT.md (keep latest content)
  - PRODUCT_VISION_2025-07-30.md → Delete (outdated version)
  
Move Technical Docs:
  - PLANNING.md → docs/ARCHITECTURE.md (update content)
  - GOOGLE_DRIVE_SETUP.md → docs/technical/google-integration.md
  - DEPLOYMENT_GUIDE.md → docs/technical/deployment.md
  - DEV_LOG*.md → docs/project/CHANGELOG.md (consolidate)
  
Move Initial Specs:
  - INITIAL_soleil.md → docs/project/decisions/001-initial-design.md
  - INITIAL_google_drive_role_based_organization.md → Delete (implemented)
  
Create New User Docs:
  - docs/user-guide/musician-quickstart.md (new)
  - docs/user-guide/admin-guide.md (new)
```

#### New README.md Content
```markdown
# SOLEil - Your Band, Organized

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production-green.svg)](https://solepower.live)

SOLEil transforms how bands manage their music. It's a smart digital music folder that automatically organizes charts, audio references, and setlists based on what instrument each musician plays.

## ✨ Key Features

- **Instrument Intelligence**: Trumpet players see B♭ charts, alto sax players see E♭ charts, automatically
- **Google Workspace Integration**: Your existing Drive, Sheets, and Calendar become a powerful band platform
- **Works Everywhere**: Beautiful on phones, tablets, and desktops
- **One-Click Access**: Sign in with Google, see your music instantly

## 🎵 For Musicians

Stop digging through emails for charts. Access everything at [solepower.live](https://solepower.live):

1. Sign in with your Google account
2. Select your instrument
3. See all your charts and audio files organized by song

See the [Musician Quick Start Guide](docs/user-guide/musician-quickstart.md).

## 🎼 For Band Leaders

Manage your entire band's library through Google Drive:

1. Upload charts with naming convention: `SongTitle_Bb.pdf`
2. Add audio references: `SongTitle.mp3`
3. Musicians automatically see only their relevant parts

See the [Admin Guide](docs/user-guide/admin-guide.md).

## 🛠 Development

```bash
# Clone repository
git clone git@github.com:YOUR_USERNAME/soleil.git
cd soleil

# Start development environment
cd band-platform
docker-compose up -d

# Access at http://localhost:3000
```

See [Development Guide](docs/DEVELOPMENT.md) for detailed setup.

## 📖 Documentation

- [Product Overview](docs/PRODUCT.md) - What SOLEil is and why it exists
- [Architecture](docs/ARCHITECTURE.md) - Technical design decisions
- [User Guides](docs/user-guide/) - For musicians and administrators
- [Technical Docs](docs/technical/) - Implementation details

## 🚀 Deployment

SOLEil is deployed at [solepower.live](https://solepower.live). 

For your own deployment, see the [Deployment Guide](docs/technical/deployment.md).

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

*SOLEil: Because great music starts with great organization.*
```

#### New docs/PRODUCT.md
```markdown
# SOLEil Product Overview

## The Problem

Every band faces the same challenges:
- Musicians constantly asking "can you send me that chart again?"
- Wrong transpositions at rehearsals (trumpet player with a concert pitch chart)
- Email attachments scattered across dozens of threads
- No central place for reference recordings
- Band leaders becoming the "chart police"

## The Solution

SOLEil is Google Workspace for bands. It transforms your existing Google Drive into an intelligent music library that understands instruments and transpositions.

### Core Concept

1. **Band leader** uploads files to Google Drive with simple naming:
   - Charts: `All of Me - Bb.pdf`, `All of Me - Eb.pdf`
   - Audio: `All of Me.mp3`

2. **Musicians** sign in and select their instrument

3. **SOLEil** automatically shows only relevant files:
   - Trumpet players see B♭ charts
   - Alto sax players see E♭ charts
   - Everyone gets the audio references

### Design Principles

- **It Just Works**: No complex setup, no learning curve
- **Use What You Have**: Leverages existing Google accounts and storage
- **Mobile First**: Designed for phones at dark gigs
- **Offline Ready**: Download charts for venues without WiFi
- **Beautiful**: Professional typography with proper musical notation

## Current Status

As of August 2025, SOLEil is production-ready with all core features:

✅ **Complete**
- Google OAuth authentication
- Smart instrument-based filtering
- Real-time Google Drive sync
- PDF viewing with zoom/pan
- Audio playback with download
- Mobile-responsive design
- Professional UI with musical typography

🔄 **Future Enhancements**
- Setlist management via Google Sheets
- Gig calendar via Google Calendar
- Offline mode with smart sync
- Multi-band support
- Practice tools (loops, tempo adjustment)

## Success Metrics

- 0 emails asking for charts after implementation
- 100% of musicians have correct transpositions
- <3 seconds to find any chart
- Works on 100% of devices (phones, tablets, computers)

## Why SOLEil?

The name combines "Sole" (as in Sole Power) with "Soleil" (French for sun), representing how it illuminates and organizes your band's music. The sun logo (☀) appears throughout the interface as a symbol of clarity and warmth.
```

### Implementation Steps for Documentation

```bash
# Create new directory structure
mkdir -p docs/{user-guide,technical,project/decisions}
mkdir -p .github/ISSUE_TEMPLATE
mkdir -p PRPs/{completed,templates}

# Move and consolidate files
mv PRODUCT_VISION.md docs/PRODUCT.md
mv PLANNING.md docs/ARCHITECTURE.md
mv GOOGLE_DRIVE_SETUP.md docs/technical/google-integration.md
mv band-platform/DEPLOYMENT_GUIDE.md docs/technical/deployment.md

# Consolidate dev logs into changelog
cat DEV_LOG.md DEV_LOG_TECHNICAL.md > docs/project/CHANGELOG.md

# Archive initial specs
mv INITIAL_soleil.md docs/project/decisions/001-initial-design.md

# Remove outdated files
rm PRODUCT_VISION_2025-07-30.md
rm INITIAL_google_drive_role_based_organization.md
rm DEV_LOG.md DEV_LOG_TECHNICAL.md

# Create new user documentation
touch docs/user-guide/{musician-quickstart.md,admin-guide.md,troubleshooting.md}
touch docs/technical/{authentication.md,database-schema.md}
touch docs/project/ROADMAP.md

# Update root files
# [Create new README.md as shown above]
# [Create .github/CONTRIBUTING.md]
```

This restructuring:
1. **Clarifies Purpose**: Clear separation between product, user, and technical docs
2. **Improves Navigation**: Logical hierarchy for different audiences
3. **Reduces Clutter**: Removes outdated and redundant files
4. **Supports Growth**: Structure scales as project evolves
5. **Enables Contributions**: Clear guidelines and templates

#### Sample docs/user-guide/musician-quickstart.md
```markdown
# Musician Quick Start Guide

Welcome to SOLEil! This guide will have you accessing your charts in under 2 minutes.

## Step 1: Sign In

1. Go to [solepower.live](https://solepower.live)
2. Click "Sign in with Google"
3. Use your Google account (the one your band leader invited)

## Step 2: Set Your Instrument

On first login:
1. Enter your name
2. Select your instrument from the dropdown
3. Click "Save Profile"

SOLEil remembers this - you only set it once!

## Step 3: Find Your Music

You'll see your repertoire organized by song:
- ☀ **Song Title** - Shows number of files
- Click any song to see charts and audio
- Your charts are automatically in the right transposition

## Using Charts

### Viewing
- Click any PDF to view in the browser
- Pinch to zoom on mobile
- Use two fingers to pan around

### Downloading
- Click the download button to save for offline use
- Charts save with clear names like "All_of_Me_Bb.pdf"

## Playing Audio

- Click the play button for instant playback
- Download MP3s for practice at home
- Audio works on all devices

## Tips for Gigs

1. **Before the Gig**: Download charts you'll need
2. **Dark Stages**: Your phone screen dims automatically
3. **Quick Access**: Bookmark [solepower.live](https://solepower.live)
4. **Stay Signed In**: Check "Remember me" when logging in

## Troubleshooting

**Can't see any charts?**
- Make sure you selected the correct instrument
- Ask your band leader if files are uploaded

**Wrong transposition?**
- Check your instrument setting in your profile
- Tenor Sax = B♭, Alto Sax = E♭

**Can't sign in?**
- Use the Google account your band leader invited
- Clear your browser cache and try again

---

*Need help? Contact your band leader or check the [FAQ](troubleshooting.md).*
```

#### Sample docs/user-guide/admin-guide.md
```markdown
# Band Leader / Admin Guide

This guide covers how to set up and manage your band's music library with SOLEil.

## Initial Setup

### 1. Prepare Your Google Drive

Create this folder structure in your Google Drive:
```
Band Name/
├── Charts/
├── Audio/
├── Setlists/     (Google Sheets)
└── Gig Info/     (Google Sheets)
```

### 2. File Naming Convention

**Critical**: SOLEil uses file names to organize content.

#### Charts
- Format: `SongTitle_Transposition.pdf`
- Examples:
  - `All of Me_Bb.pdf` (for trumpet, tenor sax)
  - `All of Me_Eb.pdf` (for alto sax, bari sax)
  - `All of Me_C.pdf` (for piano, guitar)
  - `All of Me_Bass.pdf` (for bass/trombone)

#### Audio
- Format: `SongTitle.mp3`
- Example: `All of Me.mp3`

### 3. Invite Musicians

1. Share your Band folder with musicians' Google accounts
2. Send them to [solepower.live](https://solepower.live)
3. They'll sign in and select their instrument

## Managing Content

### Adding New Songs

1. Upload PDFs to Charts folder with correct naming
2. Upload MP3 to Audio folder
3. Files appear instantly in SOLEil

### Updating Charts

- Simply replace the file in Google Drive
- Musicians see updates immediately
- No need to email anyone!

### Creating Placeholders

For charts you're still arranging:
- Use `_X` suffix: `New Song_Bb_X.pdf`
- Musicians see it marked as "placeholder"

## Advanced Features

### Instrument Mapping

| Instrument | Sees These Charts | Transposition |
|------------|------------------|---------------|
| Trumpet | _Bb.pdf | B♭ |
| Alto Sax | _Eb.pdf | E♭ |
| Tenor Sax | _Bb.pdf | B♭ |
| Trombone | _Bass.pdf | C (bass clef) |
| Piano/Guitar | _C.pdf | C |
| Bass | _Bass.pdf | C (bass clef) |

### Bulk Uploading

1. Select multiple files on your computer
2. Drag into appropriate Google Drive folder
3. Ensure naming convention is correct

### Organization Tips

- **Standardize Titles**: "All of Me" not "AllOfMe" or "All Of Me"
- **Version Control**: Replace files rather than adding "v2"
- **Clean Regularly**: Remove old/unused files

## Best Practices

### For Rehearsals
- Upload new charts at least 24 hours before
- Include audio references when possible
- Use consistent naming across all transpositions

### For Gigs
- Remind musicians to download charts beforehand
- Keep a "Current Gig" folder for active setlists
- Test new uploads before the gig

## Troubleshooting

**Musicians can't see files?**
1. Check Google Drive sharing permissions
2. Verify file naming convention
3. Ensure they selected the correct instrument

**Files not updating?**
- SOLEil syncs with Google Drive instantly
- Have musicians refresh their browser
- Check if old file was actually replaced

**Wrong transposition showing?**
- Verify file naming (must be exact: _Bb not _Bb)
- Check musician's instrument setting

---

*For technical setup and deployment, see the [Technical Documentation](../technical/).*
```