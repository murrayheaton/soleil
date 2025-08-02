name: "Fix Google Sign-In Button Responsiveness"
description: |

## Purpose
Fix the unresponsive "Sign in with Google" button on the login page, ensuring all users (authorized or unauthorized) can attempt the login process. This is critical for user onboarding as unauthorized users need to be able to attempt login to communicate their need for access.

## Core Principles
1. **Universal Access**: Login button must work for everyone, regardless of authorization status
2. **Clear Feedback**: Users should receive immediate visual and functional feedback
3. **Error Transparency**: Failed login attempts should provide clear next steps
4. **Progressive Enhancement**: Button should work even with JavaScript issues
5. **Debug Visibility**: Console logging for troubleshooting in production

---

## Goal
Create a robust Google sign-in button that:
- Responds to all click events reliably
- Provides immediate visual feedback on interaction
- Works for both authorized and unauthorized users
- Handles OAuth environment variable issues gracefully
- Logs diagnostic information for debugging
- Shows loading states during OAuth redirect

## Why
- **Current Issue**: "Sign in with Google" button doesn't respond to clicks
- **User Impact**: New users cannot request access to the platform
- **Business Impact**: Blocks user onboarding and growth
- **Debug Challenge**: No error messages or feedback when button fails
- **Authorization Flow**: Unauthorized users need to attempt login to be identified

## What
A comprehensive fix for the Google sign-in button with enhanced error handling and debugging

### Success Criteria
- [ ] Button responds to all click events immediately
- [ ] Visual feedback on hover, click, and processing states
- [ ] Console logging for debugging OAuth flow
- [ ] Clear error messages when environment variables are missing
- [ ] Unauthorized users can complete OAuth flow (even if denied app access)
- [ ] Loading indicator during OAuth redirect
- [ ] Fallback behavior if JavaScript fails

## All Needed Context

### Current Implementation Analysis
```typescript
// Current login/page.tsx issues identified:
1. No console logging for debugging
2. Silent failure when environment variables are missing
3. No visual feedback during OAuth redirect
4. Possible event propagation issues with Layout wrapper
5. No error boundary for React errors
```

### OAuth Flow for Unauthorized Users
```yaml
desired_flow:
  1. User clicks "Sign in with Google"
  2. Redirected to Google OAuth consent
  3. User authorizes app permissions
  4. Callback returns to app with auth code
  5. Backend attempts to validate user
  6. If unauthorized: Show "Request Access" page with user email
  7. Admin receives notification of access request
```

### Environment Variables Required
```bash
# Frontend (Next.js)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
NEXT_PUBLIC_API_URL=https://solepower.live/api

# Backend (FastAPI)
GOOGLE_CLIENT_ID=360999037847-dg2hqrp1ftfvuc1klpl4cuagsc499172.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://solepower.live/api/auth/google/callback
```

### Known Issues to Address
```yaml
potential_causes:
  - React hydration mismatch between server and client
  - Event handler not attaching properly in production
  - Layout component interfering with click events
  - CSP or security headers blocking inline scripts
  - Environment variables not available at runtime
  - OAuth redirect URI mismatch
```

## Implementation Blueprint

### 1. Enhanced Login Page with Debugging
```typescript
// File: band-platform/frontend/src/app/login/page.tsx
'use client';

import { useEffect, useState } from 'react';

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string[]>([]);

  // Add debug logging
  const addDebug = (message: string) => {
    console.log(`[Login Debug] ${message}`);
    setDebugInfo(prev => [...prev, `${new Date().toISOString()}: ${message}`]);
  };

  useEffect(() => {
    addDebug('Login page mounted');
    
    // Check environment variables
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    
    addDebug(`Client ID: ${clientId ? 'Present' : 'Missing'}`);
    addDebug(`API URL: ${apiUrl || 'Missing'}`);

    // Check for auth callback parameters
    const urlParams = new URLSearchParams(window.location.search);
    const authParam = urlParams.get('auth');
    const messageParam = urlParams.get('message');
    
    if (authParam === 'success') {
      addDebug('Auth success detected, redirecting to profile');
      window.location.href = '/profile?auth=success';
    } else if (authParam === 'error') {
      addDebug(`Auth error: ${messageParam || 'Unknown error'}`);
      setError(decodeURIComponent(messageParam || 'Authentication failed'));
    } else if (authParam === 'unauthorized') {
      addDebug('User unauthorized - needs access request');
      setError('Your account is not authorized. Please contact an administrator to request access.');
    }
  }, []);

  const handleGoogleSignIn = async () => {
    try {
      addDebug('Sign in button clicked');
      setIsLoading(true);
      setError(null);

      // Get environment variables
      const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live/api';

      if (!clientId) {
        const errorMsg = 'Google OAuth Client ID is not configured';
        addDebug(`Error: ${errorMsg}`);
        setError(errorMsg);
        setIsLoading(false);
        return;
      }

      // Build OAuth URL
      const redirectUri = `${apiUrl}/api/auth/google/callback`;
      const scope = encodeURIComponent('https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile');
      const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${scope}&access_type=offline&prompt=consent`;

      addDebug(`Redirecting to: ${authUrl.substring(0, 50)}...`);
      
      // Add small delay to ensure state updates are visible
      setTimeout(() => {
        window.location.href = authUrl;
      }, 100);
      
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to initiate sign in';
      addDebug(`Exception: ${errorMsg}`);
      setError(errorMsg);
      setIsLoading(false);
    }
  };

  // Test button click handler
  const handleTestClick = () => {
    addDebug('Test button clicked - UI is responsive');
    alert('Button click works! Check console for debug info.');
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center" style={{backgroundColor: '#171717', paddingBottom: '25vh'}}>
      <div className="max-w-md w-full mx-4">
        <div className="rounded border p-8 shadow-xl" style={{backgroundColor: '#262626', borderColor: '#404040'}}>
          <div className="text-center mb-8">
            <h1 className="text-3xl font-black text-white mb-0">Sole Power <span className="font-thin">Live</span></h1>
            <p className="text-gray-400 text-sm font-light -mt-1">Assets access</p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded" style={{backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)'}}>
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <div className="text-center space-y-3">
            <button
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full bg-white hover:bg-gray-100 disabled:bg-gray-300 text-gray-800 font-semibold px-6 py-4 rounded transition-all transform hover:scale-105 active:scale-95 flex items-center justify-center shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
              style={{touchAction: 'manipulation'}}
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 mr-3 border-2 border-gray-800 border-t-transparent rounded-full animate-spin" />
                  Redirecting to Google...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Sign in with Google
                </>
              )}
            </button>

            {/* Debug test button */}
            <button
              onClick={handleTestClick}
              className="w-full bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm px-4 py-2 rounded transition-colors"
            >
              Test Button Responsiveness
            </button>
          </div>

          {/* Debug info in development */}
          {process.env.NODE_ENV === 'development' && debugInfo.length > 0 && (
            <div className="mt-6 p-3 rounded text-xs" style={{backgroundColor: '#1a1a1a', border: '1px solid #333'}}>
              <p className="text-gray-500 mb-2">Debug Log:</p>
              {debugInfo.slice(-5).map((info, idx) => (
                <p key={idx} className="text-gray-600 font-mono">{info}</p>
              ))}
            </div>
          )}
        </div>

        {/* Always visible debug hint */}
        <p className="text-center text-gray-600 text-xs mt-4">
          Check browser console for authentication debug information
        </p>
      </div>
    </div>
  );
}
```

### 2. Create Error Boundary for Login Page
```typescript
// File: band-platform/frontend/src/app/login/error.tsx
'use client';

export default function LoginError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-gray-900">
      <div className="max-w-md w-full mx-4 p-8 bg-gray-800 rounded-lg">
        <h2 className="text-2xl font-bold text-red-400 mb-4">Login Error</h2>
        <p className="text-gray-300 mb-4">
          Something went wrong with the login page. This might be due to:
        </p>
        <ul className="list-disc list-inside text-gray-400 mb-6 space-y-1">
          <li>Missing environment variables</li>
          <li>JavaScript loading issues</li>
          <li>Network connectivity problems</li>
        </ul>
        <p className="text-sm text-gray-500 mb-6 font-mono bg-gray-900 p-2 rounded">
          {error.message || 'Unknown error'}
        </p>
        <div className="flex gap-4">
          <button
            onClick={reset}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={() => window.location.href = '/'}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
          >
            Go Home
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 3. Update Backend to Handle Unauthorized Users
```python
# File: band-platform/backend/start_server.py (modification to auth callback)

@app.get("/api/auth/google/callback")
async def auth_callback(request: Request, code: str = None, error: str = None):
    """Handle Google OAuth callback with support for unauthorized users."""
    
    frontend_url = os.getenv('FRONTEND_URL', 'https://solepower.live')
    
    if error:
        logger.error(f"Auth callback received error: {error}")
        return RedirectResponse(url=f"{frontend_url}/login?auth=error&message={error}")
    
    if not code:
        logger.error("Auth callback missing authorization code")
        return RedirectResponse(url=f"{frontend_url}/login?auth=error&message=No+authorization+code")
    
    try:
        # Exchange code for tokens
        token_data = {
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'https://solepower.live/api/auth/google/callback')
        }
        
        logger.info("Exchanging authorization code for tokens")
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        tokens = response.json()
        
        if 'access_token' not in tokens:
            logger.error(f"Token exchange failed: {tokens}")
            error_msg = tokens.get('error_description', 'Failed to get access token')
            return RedirectResponse(url=f"{frontend_url}/login?auth=error&message={error_msg}")
        
        # Get user info
        user_info_response = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
        user_info = user_info_response.json()
        
        logger.info(f"OAuth successful for user: {user_info.get('email')}")
        
        # Check if user is authorized in your system
        # This is where you'd check against your user database
        # For now, we'll create a session for all Google users
        
        # Create session
        request.session['user_id'] = user_info.get('id')
        request.session['user_email'] = user_info.get('email')
        request.session['user_name'] = user_info.get('name')
        request.session['access_token'] = tokens['access_token']
        
        # Store refresh token if provided
        if 'refresh_token' in tokens:
            request.session['refresh_token'] = tokens['refresh_token']
        
        # Log unauthorized access attempts
        # In a real implementation, you'd check against an authorized users list
        # For now, we'll allow all users but log them
        logger.info(f"New user login: {user_info.get('email')} - Consider adding authorization check")
        
        return RedirectResponse(url=f"{frontend_url}/login?auth=success")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        return RedirectResponse(url=f"{frontend_url}/login?auth=error&message=Authentication+failed")
```

### 4. Add Login Route Without Layout Wrapper
```typescript
// File: band-platform/frontend/src/app/login/layout.tsx
export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Don't wrap login page in the main Layout component
  return <>{children}</>;
}
```

### 5. Add Client-Side Environment Variable Check
```typescript
// File: band-platform/frontend/src/app/components/EnvCheck.tsx
'use client';

import { useEffect } from 'react';

export default function EnvCheck() {
  useEffect(() => {
    // Log environment variables for debugging
    console.log('Environment Check:', {
      NEXT_PUBLIC_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ? 'Set' : 'Missing',
      NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'Not set',
      NODE_ENV: process.env.NODE_ENV,
    });
  }, []);

  return null;
}

// Add to login page:
// import EnvCheck from '@/components/EnvCheck';
// Add <EnvCheck /> in the component
```

## Testing & Validation

### Local Testing Steps
1. **Test Button Responsiveness**:
   ```bash
   cd band-platform/frontend
   npm run dev
   # Open http://localhost:3000/login
   # Click "Test Button Responsiveness"
   # Check console for debug logs
   ```

2. **Test OAuth Flow**:
   ```bash
   # Ensure environment variables are set
   echo $NEXT_PUBLIC_GOOGLE_CLIENT_ID
   # Click "Sign in with Google"
   # Monitor console for redirect logs
   ```

3. **Test Error States**:
   ```bash
   # Temporarily remove environment variables
   unset NEXT_PUBLIC_GOOGLE_CLIENT_ID
   npm run dev
   # Should see error message
   ```

### Production Testing
```bash
# On production server
cd band-platform
docker-compose -f docker-compose.production.yml logs -f frontend
# In another terminal
curl -I https://solepower.live/login
# Check for any CSP headers blocking scripts
```

### Browser Console Checks
```javascript
// Run in browser console on login page
document.querySelector('button').onclick = () => console.log('Direct click works');
// Check for any errors in console
// Check Network tab for failed resource loads
```

## Rollback Plan

If the new implementation causes issues:

1. **Quick Revert**:
   ```bash
   git checkout main~1 -- frontend/src/app/login/page.tsx
   git commit -m "Revert login page changes"
   git push
   ```

2. **Minimal Fix**:
   ```typescript
   // Add just console logging to existing button
   onClick={() => {
     console.log('Button clicked', new Date().toISOString());
     handleGoogleSignIn();
   }}
   ```

## Post-Implementation

### Monitoring Setup
1. Add frontend error tracking (Sentry or similar)
2. Monitor OAuth callback success/failure rates
3. Track button click events in analytics

### User Communication
1. Add status page for known issues
2. Provide clear error messages with support contact
3. Document access request process for unauthorized users

### Future Enhancements
1. Add Apple/Microsoft sign-in options
2. Implement magic link authentication as fallback
3. Add offline detection and messaging
4. Create admin dashboard for access requests

## Completion Checklist
- [ ] Login button responds to all clicks
- [ ] Debug logging implemented
- [ ] Error states handled gracefully
- [ ] Loading states during OAuth redirect
- [ ] Environment variable validation
- [ ] Unauthorized user flow documented
- [ ] Production deployment tested
- [ ] Browser console free of errors