name: "Fix Profile Loading Issue & Persistent Storage"
description: |
  Critical bug fix for users getting stuck on "loading profile" screen after Google authorization.
  Implements robust profile persistence with proper error recovery mechanisms.

---

## Pre-Implementation Requirements

Before starting implementation, Claude Code MUST:

1. **Read all project documentation**:
   - CLAUDE.md - Global AI assistant rules
   - PLANNING.md - Project architecture and conventions
   - TASK.md - Current task tracking
   - DEV_LOG.md & DEV_LOG_TECHNICAL.md - Recent changes
   - PRODUCT_VISION.md - Product direction

2. **Create feature branch**:
   ```bash
   cd ~/Documents/GitHub/soleil
   git checkout main
   git pull origin main
   git checkout -b feature/fix-profile-loading
   ```

3. **Verify current deployment state**:
   - Check if site is currently accessible at https://solepower.live
   - Note any existing errors in production

---

## Goal
Fix the post-authorization infinite loading loop and implement bulletproof profile persistence that prevents users from being locked out of the platform.

## Why
- **CRITICAL BLOCKER**: Users cannot access the platform at all
- **Trust**: Profile data loss erodes user confidence  
- **Business Impact**: 100% user dropout rate after auth

## Success Criteria
- [ ] Users can complete login flow without getting stuck
- [ ] Profile data persists indefinitely (not session-based)
- [ ] Clear error messages displayed on failure
- [ ] Loading completes within 3 seconds
- [ ] Graceful recovery when profile data is missing
- [ ] Works in production at https://solepower.live

## Investigation Steps

```yaml
Priority Investigation:
  1. Check browser console at https://solepower.live for errors
  2. Inspect Network tab for failed API calls to /api endpoints
  3. Review backend logs on production server
  4. Test with fresh Google account
  5. Verify user_profiles.json exists and has correct permissions

Key Files to Examine:
  - backend/start_server.py - Auth endpoints and profile handling
  - backend/user_profiles.json - Current storage mechanism
  - frontend/src/app/page.tsx - Loading screen logic
  - frontend/src/lib/api.ts - API client configuration
  - Production logs via: ssh root@SERVER_IP "cd /root/soleil/band-platform && docker-compose -f docker-compose.production.yml logs backend"
```

## Implementation Tasks

### Task 1: Add Comprehensive Logging to Auth Flow
```python
# backend/start_server.py - Add detailed logging to auth endpoints
import logging
from datetime import datetime
import traceback

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.post("/auth/callback")
async def auth_callback(request: Request):
    """Handle Google OAuth callback with comprehensive logging."""
    start_time = datetime.now()
    session_id = request.session.get('session_id', 'unknown')
    
    logger.info(f"Auth callback started - Session: {session_id}")
    
    try:
        # Log each step of the auth process
        auth_code = request.query_params.get('code')
        logger.info(f"Auth code received: {'yes' if auth_code else 'no'}")
        
        # Exchange code for tokens
        token_data = await exchange_code_for_tokens(auth_code)
        logger.info(f"Token exchange: {'success' if token_data else 'failed'}")
        
        # Get user info
        user_info = await get_google_user_info(token_data['access_token'])
        logger.info(f"User info retrieved for: {user_info.get('email', 'unknown')}")
        
        # Get or create profile
        profile = await get_or_create_profile(
            user_id=user_info['id'],
            email=user_info['email'],
            name=user_info['name']
        )
        logger.info(f"Profile {'created' if profile.get('is_new') else 'loaded'} for {user_info['email']}")
        
        # Store in session
        request.session['user_profile'] = profile
        request.session['authenticated'] = True
        
        return RedirectResponse(url="/dashboard", status_code=302)
        
    except Exception as e:
        logger.error(f"Auth callback failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return RedirectResponse(url="/login?error=auth_failed", status_code=302)
    
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Auth callback completed in {duration:.2f}s")
```

### Task 2: Fix Frontend Loading State with Timeout and Retry
```typescript
// frontend/src/app/page.tsx - Robust loading with timeout and retry
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const PROFILE_LOAD_TIMEOUT = 10000; // 10 seconds
const MAX_RETRIES = 3;
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live/api';

export default function HomePage() {
    const router = useRouter();
    const [loadingState, setLoadingState] = useState<'loading' | 'error' | 'timeout' | 'success'>('loading');
    const [error, setError] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);

    const loadProfile = async () => {
        try {
            const response = await fetch(`${API_URL}/users/profile`, {
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Not authenticated, redirect to login
                    router.push('/login');
                    return;
                }
                throw new Error(`Profile load failed: ${response.status}`);
            }

            const profile = await response.json();
            
            if (profile && profile.id) {
                setLoadingState('success');
                // Store profile in local state management if needed
                router.push('/dashboard');
            } else {
                throw new Error('Invalid profile data received');
            }
        } catch (err) {
            console.error('Profile load error:', err);
            
            if (retryCount < MAX_RETRIES) {
                // Exponential backoff retry
                setTimeout(() => {
                    setRetryCount(prev => prev + 1);
                }, Math.pow(2, retryCount) * 1000);
            } else {
                setLoadingState('error');
                setError(err instanceof Error ? err.message : 'Failed to load profile');
            }
        }
    };

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            if (loadingState === 'loading') {
                setLoadingState('timeout');
                setError('Profile loading timed out. Please refresh the page.');
            }
        }, PROFILE_LOAD_TIMEOUT);

        loadProfile();

        return () => clearTimeout(timeoutId);
    }, [retryCount]);

    // Render states
    if (loadingState === 'loading') {
        return (
            <div className="loading-container">
                <div className="loading-spinner" />
                <p>Loading your profile...</p>
                {retryCount > 0 && <p className="retry-text">Retry attempt {retryCount} of {MAX_RETRIES}</p>}
            </div>
        );
    }

    if (loadingState === 'error' || loadingState === 'timeout') {
        return (
            <div className="error-container">
                <h2>Unable to Load Profile</h2>
                <p className="error-message">{error}</p>
                <div className="error-actions">
                    <button onClick={() => window.location.reload()}>
                        Refresh Page
                    </button>
                    <button onClick={() => router.push('/login')}>
                        Back to Login
                    </button>
                </div>
            </div>
        );
    }

    return null; // Success state redirects to dashboard
}
```

### Task 3: Implement Robust Profile Storage Service
```python
# backend/app/services/profile_service.py - New file
import json
import os
import asyncio
from typing import Optional, Dict
from datetime import datetime
import aiofiles
import logging

logger = logging.getLogger(__name__)

class ProfileService:
    """Robust profile storage with file locking and error recovery."""
    
    def __init__(self, storage_path: str = "user_profiles.json"):
        self.storage_path = storage_path
        self._lock = asyncio.Lock()
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Ensure storage file exists with correct permissions."""
        if not os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'w') as f:
                    json.dump({}, f)
                os.chmod(self.storage_path, 0o600)  # Read/write for owner only
                logger.info(f"Created profile storage at {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to create profile storage: {e}")
    
    async def _load_profiles(self) -> Dict:
        """Load profiles with error handling."""
        try:
            async with aiofiles.open(self.storage_path, 'r') as f:
                content = await f.read()
                return json.loads(content) if content else {}
        except FileNotFoundError:
            logger.warning("Profile file not found, creating new one")
            self._ensure_storage_exists()
            return {}
        except json.JSONDecodeError:
            logger.error("Corrupted profile file, backing up and creating new")
            # Backup corrupted file
            backup_path = f"{self.storage_path}.backup.{datetime.now().timestamp()}"
            os.rename(self.storage_path, backup_path)
            self._ensure_storage_exists()
            return {}
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            return {}
    
    async def _save_profiles(self, profiles: Dict):
        """Save profiles with atomic write."""
        temp_path = f"{self.storage_path}.tmp"
        try:
            async with aiofiles.open(temp_path, 'w') as f:
                await f.write(json.dumps(profiles, indent=2))
            
            # Atomic rename
            os.replace(temp_path, self.storage_path)
            logger.info(f"Saved {len(profiles)} profiles")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
    
    async def get_or_create_profile(
        self, 
        user_id: str, 
        email: str, 
        name: str
    ) -> Dict:
        """Get existing profile or create new one with retry logic."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with self._lock:
                    profiles = await self._load_profiles()
                    
                    if user_id in profiles:
                        # Update last accessed
                        profiles[user_id]['last_accessed'] = datetime.utcnow().isoformat()
                        await self._save_profiles(profiles)
                        
                        profile = profiles[user_id]
                        profile['is_new'] = False
                        return profile
                    
                    # Create new profile
                    profile = {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "instruments": [],
                        "ui_scale": "small",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "last_accessed": datetime.utcnow().isoformat(),
                        "is_new": True
                    }
                    
                    profiles[user_id] = profile
                    await self._save_profiles(profiles)
                    
                    logger.info(f"Created new profile for {email}")
                    return profile
                    
            except Exception as e:
                logger.error(f"Profile operation failed (attempt {attempt + 1}): {e}")
                
                if attempt == max_retries - 1:
                    # Last attempt - return minimal profile without saving
                    logger.error("All retries failed, returning transient profile")
                    return {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "instruments": [],
                        "ui_scale": "small",
                        "is_transient": True,
                        "error": "Profile storage temporarily unavailable"
                    }
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
    
    async def update_profile(self, user_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing profile."""
        async with self._lock:
            profiles = await self._load_profiles()
            
            if user_id not in profiles:
                logger.error(f"Profile not found for update: {user_id}")
                return None
            
            profiles[user_id].update(updates)
            profiles[user_id]['updated_at'] = datetime.utcnow().isoformat()
            
            await self._save_profiles(profiles)
            return profiles[user_id]

# Initialize global profile service
profile_service = ProfileService()
```

### Task 4: Update Backend Endpoints
```python
# backend/start_server.py - Update profile endpoints
from app.services.profile_service import profile_service

@app.get("/api/users/profile")
async def get_user_profile(request: Request):
    """Get current user profile with proper error handling."""
    try:
        # Check session
        if not request.session.get('authenticated'):
            return JSONResponse(
                status_code=401,
                content={"error": "Not authenticated"}
            )
        
        user_profile = request.session.get('user_profile')
        if not user_profile or not user_profile.get('id'):
            return JSONResponse(
                status_code=404,
                content={"error": "Profile not found in session"}
            )
        
        # Refresh from storage
        fresh_profile = await profile_service.get_or_create_profile(
            user_id=user_profile['id'],
            email=user_profile['email'],
            name=user_profile['name']
        )
        
        # Update session with fresh data
        request.session['user_profile'] = fresh_profile
        
        return JSONResponse(content=fresh_profile)
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to load profile"}
        )

@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user and clear session."""
    request.session.clear()
    return JSONResponse(content={"status": "logged out"})
```

## Testing & Validation

### Local Testing
```bash
# Test locally first
cd ~/Documents/GitHub/soleil/band-platform

# Backend
cd backend
source venv_linux/bin/activate
python start_server.py

# Frontend (new terminal)
cd frontend
npm run dev

# Test auth flow at http://localhost:3000
```

### Production Deployment
```bash
# Commit and push changes
cd ~/Documents/GitHub/soleil
git add -A
git commit -m "fix: resolve profile loading issue with robust error handling"
git push origin feature/fix-profile-loading

# SSH to server and deploy
ssh root@YOUR_SERVER_IP
cd /root/soleil
git fetch origin
git checkout feature/fix-profile-loading
cd band-platform
./deploy.sh solepower.live your-email@example.com

# Monitor logs
docker-compose -f docker-compose.production.yml logs -f backend
```

### Validation Checklist
- [ ] Login flow completes without hanging
- [ ] Profile loads within 3 seconds
- [ ] Error messages display properly
- [ ] Retry logic works on transient failures
- [ ] Profile data persists across sessions
- [ ] Works on production at https://solepower.live

## Rollback Plan
If issues occur in production:
```bash
ssh root@YOUR_SERVER_IP
cd /root/soleil
git checkout main
cd band-platform
docker-compose -f docker-compose.production.yml up -d --build
```

## Post-Deployment
1. Monitor error logs for 24 hours
2. Test with multiple user accounts
3. Verify no performance degradation
4. Update DEV_LOG.md and DEV_LOG_TECHNICAL.md
5. Merge to main if stable