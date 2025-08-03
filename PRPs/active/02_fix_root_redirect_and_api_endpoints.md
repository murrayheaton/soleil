# PRP: Fix Root Page Redirect Logic and API Endpoint Consistency

**Description**: Fix the root page (/) to properly redirect new users to login instead of attempting to load non-existent profiles. Also resolve API endpoint inconsistencies between pages.

**Priority**: High  
**Impact**: Critical User Flow

## Pre-Implementation Requirements

1. **Read Documentation**:
   - [ ] Review PRODUCT_VISION.md for user flow requirements
   - [ ] Check backend API routes in `band-platform/backend/app/api/user.py`
   - [ ] Review authentication flow in DEV_LOG_TECHNICAL.md

2. **Git Setup**:
   ```bash
   cd /Users/murrayheaton/Documents/GitHub/soleil
   git checkout main
   git pull origin main
   git checkout -b fix/root-redirect-api-consistency
   ```

3. **Current State Verification**:
   ```bash
   # Check API endpoint usage
   grep -n "api/users/profile" band-platform/frontend/src/app/page.tsx
   grep -n "api/user/profile" band-platform/frontend/src/app/profile/page.tsx
   grep -n "api/user/profile" band-platform/frontend/src/app/dashboard/page.tsx
   ```

## Goal

Ensure consistent API endpoint usage across all pages and implement proper redirect logic for the root page that directs unauthenticated users to login immediately.

## Why

Currently, visiting solepower.live attempts to load a user profile that may not exist, causing delays and confusion. New users should be directed to login immediately. Additionally, the API endpoint inconsistency (`/api/users/profile` vs `/api/user/profile`) causes profile loading failures.

## Success Criteria

- [ ] Root page (/) redirects to /login for unauthenticated users
- [ ] All pages use consistent API endpoint (`/api/user/profile`)
- [ ] No loading delays for new users
- [ ] Authenticated users still redirect to dashboard
- [ ] Clean error handling without retries for 401 responses
- [ ] Profile creation flow works for new authenticated users

## Implementation Tasks

### 1. Fix API Endpoint in Root Page

**File**: `band-platform/frontend/src/app/page.tsx`

Change line 18 from:
```tsx
const response = await fetch('/api/users/profile', {
```

To:
```tsx
const response = await fetch('/api/user/profile', {
```

### 2. Simplify Root Page Redirect Logic

**File**: `band-platform/frontend/src/app/page.tsx`

Replace the entire component with simplified logic:

```tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import LoadingScreen from '@/components/LoadingScreen';

export default function HomePage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuthAndRedirect = async () => {
      try {
        const response = await fetch('/api/user/profile', {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.status === 401) {
          // User not authenticated - redirect to login
          router.replace('/login');
          return;
        }

        if (response.ok) {
          // User authenticated - redirect to dashboard
          router.replace('/dashboard');
          return;
        }

        // Other errors - redirect to login
        console.error('Profile check failed:', response.status);
        router.replace('/login');
      } catch (error) {
        console.error('Auth check error:', error);
        router.replace('/login');
      } finally {
        setIsChecking(false);
      }
    };

    checkAuthAndRedirect();
  }, [router]);

  if (isChecking) {
    return <LoadingScreen message="Checking authentication..." />;
  }

  // This should rarely be seen as redirects happen quickly
  return null;
}
```

### 3. Enhance Profile Page for New Users

**File**: `band-platform/frontend/src/app/profile/page.tsx`

Add better handling for new users after successful Google authentication. After line 71 (in the profile fetch), add logic to handle 404 responses:

```tsx
if (response.status === 404) {
  // New user - no profile exists yet
  setIsNewUser(true);
  setProfile({
    name: '',
    email: '',
    instrument: '',
    phone: '',
    dietary_restrictions: '',
    accessibility_needs: ''
  });
  setIsLoading(false);
  return;
}
```

Add state for new user detection (after line 15):
```tsx
const [isNewUser, setIsNewUser] = useState(false);
```

Update the UI to show a welcome message for new users (around line 140):
```tsx
{isNewUser && !isEditing && (
  <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
    <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
      Welcome to Soleil!
    </h3>
    <p className="text-blue-700 dark:text-blue-300">
      Please set up your profile to get started.
    </p>
  </div>
)}
```

### 4. Update Navigation Links to Check Auth

**File**: `band-platform/frontend/src/components/Layout.tsx`

While the navigation is correctly hidden on login pages, we should ensure navigation links redirect to login if session expires. This can be handled by middleware (future PRP) or by updating individual page components to check auth status.

## Testing & Validation

### Local Testing
```bash
cd band-platform/frontend
npm run dev
```

1. **Test Unauthenticated Flow**:
   - Clear cookies/use incognito
   - Visit http://localhost:3000
   - Verify immediate redirect to /login
   - No loading delays or retries

2. **Test Authenticated Flow**:
   - Sign in with Google
   - Visit http://localhost:3000
   - Verify redirect to /dashboard
   
3. **Test New User Flow**:
   - Sign in with a new Google account
   - Verify profile page shows welcome message
   - Test profile creation

4. **Test API Consistency**:
   - Check network tab for all API calls
   - Verify all use `/api/user/profile`

### Production Deployment
```bash
cd /Users/murrayheaton/Documents/GitHub/soleil
./scripts/deploy_frontend.sh
```

### Post-Deployment Validation
1. Visit https://solepower.live in incognito
2. Verify immediate redirect to login
3. Test full authentication flow
4. Monitor error logs for any 404s or failed requests

## Rollback Plan

If issues occur after deployment:
```bash
cd /Users/murrayheaton/Documents/GitHub/soleil
git checkout main
./scripts/deploy_frontend.sh
```

## Post-Implementation Steps

1. Update TASK.md with completion status
2. Update DEV_LOG.md with summary:
   - Fixed root page redirect for better UX
   - Resolved API endpoint inconsistency
   - Improved new user experience
3. Update DEV_LOG_TECHNICAL.md with:
   - API endpoint standardization details
   - Redirect flow changes
   - New user detection logic
4. Commit and push:
   ```bash
   git add -A
   git commit -m "fix: improve root redirect and standardize API endpoints

   - Fix root page to redirect unauthenticated users to login immediately
   - Standardize API endpoint to /api/user/profile across all pages
   - Add new user welcome message on profile page
   - Remove unnecessary retry logic for 401 responses"
   
   git push origin fix/root-redirect-api-consistency
   ```
5. Create pull request to main branch
6. Archive this PRP after merge