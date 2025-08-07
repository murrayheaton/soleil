# PRP 11: Fix Authentication System - Complete Overhaul

## 🚨 CRITICAL PRIORITY
This PRP addresses critical authentication issues that prevent users from successfully using the application after OAuth login.

## Current Issues
1. **Profile Setup Broken**: Email field in ProfileOnboarding component is not accepting input
2. **Session Persistence Failure**: After successful OAuth, navigating away or refreshing returns user to login screen
3. **No Auth State Management**: Application lacks centralized auth state management
4. **Cookie/Token Issues**: Authentication tokens not properly stored or validated

## Root Cause Analysis
Based on investigation:
- No AuthContext or auth state provider exists
- Authentication state only lives in cookies/localStorage without proper React state management
- Profile setup component likely has controlled input issues with email field
- Session validation happens on every page load without caching auth state
- No proper token refresh mechanism

## Solution Architecture

### 1. Create Centralized Auth System
```typescript
// contexts/AuthContext.tsx
- Global auth state management
- Persistent session handling
- Token refresh logic
- User profile caching
```

### 2. Fix Profile Setup Component
```typescript
// components/ProfileOnboarding.tsx
- Fix email input field (likely missing value/onChange binding)
- Add proper form validation
- Ensure proper state management for all inputs
```

### 3. Implement Session Persistence
```typescript
// middleware/auth.ts
- Check and validate tokens on app initialization
- Implement token refresh before expiry
- Store tokens securely (httpOnly cookies preferred)
```

## Detailed Requirements

### Phase 1: Auth Context Implementation
1. **Create AuthContext Provider**
   - Manage user authentication state
   - Handle login/logout flows
   - Persist auth state to localStorage/cookies
   - Provide auth hooks (useAuth, useUser)

2. **Wrap Application**
   - Add AuthProvider to app layout
   - Protect routes with auth guards
   - Implement loading states during auth check

### Phase 2: Fix Profile Setup
1. **Debug Email Input Issue**
   - Check ProfileOnboarding component for controlled/uncontrolled input conflicts
   - Ensure proper state binding for email field
   - Add console logging to track state changes
   - Fix any TypeScript type issues

2. **Improve Form Handling**
   - Add proper validation
   - Show clear error messages
   - Prevent submission with invalid data
   - Add loading states during submission

### Phase 3: Session Management
1. **Backend Session Handling**
   - Implement proper JWT tokens with refresh tokens
   - Set appropriate token expiry (access: 15min, refresh: 7days)
   - Add /api/auth/refresh endpoint
   - Validate tokens on every API request

2. **Frontend Token Management**
   - Store tokens securely (httpOnly cookies or secure localStorage)
   - Auto-refresh tokens before expiry
   - Handle token expiry gracefully
   - Clear tokens on logout

### Phase 4: Auth Flow Optimization
1. **OAuth Callback Handling**
   - Properly process OAuth callback
   - Set auth cookies/tokens immediately
   - Redirect to profile setup for new users
   - Redirect to dashboard for existing users

2. **Navigation Guards**
   - Check auth status before route changes
   - Preserve intended destination after login
   - Handle deep linking with auth

## Implementation Steps

### Backend Changes
```python
# app/api/auth/routes.py
1. Fix /api/auth/callback to properly set session cookies
2. Add /api/auth/refresh endpoint for token refresh
3. Add /api/auth/validate endpoint for session validation
4. Ensure cookies have proper SameSite and Secure attributes
```

### Frontend Changes
```typescript
// 1. Create contexts/AuthContext.tsx
interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

// 2. Fix components/ProfileOnboarding.tsx
- Debug why email field isn't accepting input
- Check for conflicting event handlers
- Ensure proper React state management
- Add detailed console logging

// 3. Update app/layout.tsx
- Wrap with AuthProvider
- Add session validation on mount

// 4. Create middleware.ts
- Validate auth on protected routes
- Redirect to login if unauthorized
- Preserve original URL for post-login redirect
```

## Testing Requirements
1. **Unit Tests**
   - Auth context methods
   - Token refresh logic
   - Profile form validation

2. **Integration Tests**
   - Complete OAuth flow
   - Session persistence across refreshes
   - Profile setup completion

3. **E2E Tests**
   - Full user journey from login to dashboard
   - Session timeout handling
   - Logout and re-login flow

## Acceptance Criteria
1. ✅ User can complete OAuth login successfully
2. ✅ Email field in profile setup accepts input
3. ✅ Session persists across page refreshes
4. ✅ Navigation doesn't return to login screen after auth
5. ✅ Tokens refresh automatically before expiry
6. ✅ Logout properly clears all auth data
7. ✅ Deep links work with authentication
8. ✅ Clear error messages for auth failures

## Risk Mitigation
- Add extensive logging for debugging
- Implement feature flags for gradual rollout
- Keep old auth code until new system proven stable
- Add monitoring for auth success/failure rates

## Success Metrics
- 100% OAuth completion rate
- 0% unexpected logouts
- <500ms auth check time
- 95%+ user satisfaction with login flow

## Timeline
- Day 1: Auth Context implementation
- Day 2: Fix Profile Setup component
- Day 3: Backend session management
- Day 4: Frontend token handling
- Day 5: Testing and deployment

## Dependencies
- No external dependencies
- Must maintain backward compatibility with existing user sessions
- Coordinate with DevOps for cookie domain settings

## Post-Implementation
1. Monitor auth metrics for 48 hours
2. Gather user feedback
3. Document auth flow for future reference
4. Create runbook for auth issues

## Emergency Rollback Plan
If critical issues arise:
1. Revert frontend changes via git
2. Revert backend changes via git  
3. Clear all user sessions
4. Notify users of temporary login issues
5. Restore from backup auth system

---

**Note**: This is a CRITICAL fix that blocks all user functionality. Should be implemented and deployed ASAP with careful testing.