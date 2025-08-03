# PRP: Implement New User Profile Setup Flow

**Description**: Create a proper onboarding flow for new users that prompts them to set up their profile immediately after Google authentication, preventing the broken experience of trying to load non-existent profiles.

**Priority**: High  
**Impact**: Critical User Experience

## Pre-Implementation Requirements

1. **Read Documentation**:
   - [ ] Review PRODUCT_VISION.md for onboarding requirements
   - [ ] Check profile model in `band-platform/backend/app/models/user.py`
   - [ ] Review authentication flow documentation

2. **Git Setup**:
   ```bash
   cd /Users/murrayheaton/Documents/GitHub/soleil
   git checkout main
   git pull origin main
   git checkout -b feature/new-user-onboarding-flow
   ```

3. **Current State Verification**:
   ```bash
   # Check current profile page implementation
   cat band-platform/frontend/src/app/profile/page.tsx | grep -A 10 "isEditing"
   # Check backend profile creation endpoint
   grep -n "POST" band-platform/backend/app/api/user.py
   ```

## Goal

Implement a seamless onboarding experience where new users are automatically prompted to create their profile after successful Google authentication, eliminating the current issue where the system tries to load non-existent profiles.

## Why

New users currently face a broken experience where the system attempts to load a profile that doesn't exist, causing loading spinners and non-responsive edit buttons. This creates confusion and a poor first impression.

## Success Criteria

- [ ] New users are automatically shown profile creation form after Google auth
- [ ] Profile form is pre-filled with Google account data (name, email)
- [ ] Clear onboarding messaging guides new users
- [ ] Successful profile creation redirects to dashboard
- [ ] Edit profile button works immediately for new users
- [ ] Loading states are clear and purposeful
- [ ] Backend properly handles profile creation for new users

## Implementation Tasks

### 1. Enhance Backend Profile Creation

**File**: `band-platform/backend/app/api/user.py`

Ensure the profile creation endpoint handles Google OAuth data properly. Update the profile creation logic to accept initial data from OAuth:

```python
@router.post("/profile")
async def create_or_update_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update user profile"""
    try:
        # Check if profile exists
        user = db.query(User).filter(User.email == current_user["email"]).first()
        
        if not user:
            # Create new user with OAuth data
            user = User(
                email=current_user["email"],
                name=profile_data.name or current_user.get("name", ""),
                google_id=current_user.get("sub", ""),
                picture=current_user.get("picture", "")
            )
            db.add(user)
        
        # Update profile fields
        if profile_data.name is not None:
            user.name = profile_data.name
        if profile_data.instrument is not None:
            user.instrument = profile_data.instrument
        if profile_data.phone is not None:
            user.phone = profile_data.phone
        if profile_data.dietary_restrictions is not None:
            user.dietary_restrictions = profile_data.dietary_restrictions
        if profile_data.accessibility_needs is not None:
            user.accessibility_needs = profile_data.accessibility_needs
            
        db.commit()
        db.refresh(user)
        
        return {
            "name": user.name,
            "email": user.email,
            "instrument": user.instrument,
            "phone": user.phone,
            "dietary_restrictions": user.dietary_restrictions,
            "accessibility_needs": user.accessibility_needs,
            "picture": user.picture
        }
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Profile update failed")
```

### 2. Create Dedicated Onboarding Component

**File**: `band-platform/frontend/src/components/ProfileOnboarding.tsx`

Create a new component for the onboarding experience:

```tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface ProfileOnboardingProps {
  initialData?: {
    name?: string;
    email?: string;
    picture?: string;
  };
  onComplete: () => void;
}

export default function ProfileOnboarding({ initialData, onComplete }: ProfileOnboardingProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    email: initialData?.email || '',
    instrument: '',
    phone: '',
    dietary_restrictions: '',
    accessibility_needs: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/user/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        onComplete();
        router.push('/dashboard');
      } else {
        console.error('Profile creation failed');
      }
    } catch (error) {
      console.error('Profile creation error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-lg">
        <h1 className="text-3xl font-bold mb-2">Welcome to Soleil! 🎵</h1>
        <p className="text-lg opacity-90">Let's set up your musician profile to get started.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 p-6 rounded-b-lg shadow-lg">
        <div className="space-y-6">
          {/* Name Field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Full Name *
            </label>
            <input
              type="text"
              name="name"
              required
              value={formData.name}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Your full name"
            />
          </div>

          {/* Email Field (Read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              readOnly
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-600 dark:text-gray-300"
            />
          </div>

          {/* Instrument Field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Primary Instrument *
            </label>
            <select
              name="instrument"
              required
              value={formData.instrument}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">Select your instrument</option>
              <option value="Vocals">Vocals</option>
              <option value="Guitar">Guitar</option>
              <option value="Bass">Bass</option>
              <option value="Drums">Drums</option>
              <option value="Keyboard">Keyboard/Piano</option>
              <option value="Saxophone">Saxophone</option>
              <option value="Trumpet">Trumpet</option>
              <option value="Trombone">Trombone</option>
              <option value="Violin">Violin</option>
              <option value="Other">Other</option>
            </select>
          </div>

          {/* Phone Field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Phone Number
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Optional - for gig notifications"
            />
          </div>

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50"
            >
              {isSubmitting ? 'Creating Profile...' : 'Complete Setup'}
            </button>
          </div>
        </div>
      </form>

      <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
        <p>You can update these details anytime from your profile settings.</p>
      </div>
    </div>
  );
}
```

### 3. Update Login Success Redirect

**File**: `band-platform/frontend/src/app/login/page.tsx`

Modify the sign-in success handler to check if user needs onboarding (around line 70):

```tsx
window.location.href = '/api/auth/google';
// The backend will redirect to /profile?auth=success&new_user=true for new users
```

### 4. Update Profile Page for Onboarding

**File**: `band-platform/frontend/src/app/profile/page.tsx`

Import the onboarding component and handle new user flow:

```tsx
import ProfileOnboarding from '@/components/ProfileOnboarding';

// In the component, add URL param check for new users
const searchParams = useSearchParams();
const isNewUserParam = searchParams.get('new_user') === 'true';

// After the profile fetch (around line 85), handle new user state:
if (response.status === 404 || isNewUserParam) {
  setIsNewUser(true);
  setIsLoading(false);
  
  // Try to get Google user data from session
  try {
    const sessionResponse = await fetch('/api/auth/session');
    if (sessionResponse.ok) {
      const sessionData = await sessionResponse.json();
      setGoogleUserData({
        name: sessionData.name,
        email: sessionData.email,
        picture: sessionData.picture
      });
    }
  } catch (error) {
    console.error('Failed to get session data:', error);
  }
  return;
}

// In the render section, show onboarding for new users:
{isNewUser && !profile?.name ? (
  <ProfileOnboarding 
    initialData={googleUserData}
    onComplete={() => {
      setIsNewUser(false);
      fetchProfile(); // Refresh profile data
    }}
  />
) : (
  // Existing profile display code
)}
```

### 5. Update Backend Auth Callback

**File**: `band-platform/backend/app/api/auth.py`

Modify the Google callback to detect new users:

```python
@router.get("/callback/google")
async def google_callback(code: str, state: str, request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # ... existing token exchange code ...
        
        # Check if user exists
        user = db.query(User).filter(User.email == user_info["email"]).first()
        is_new_user = user is None
        
        if is_new_user:
            # Create basic user record
            user = User(
                email=user_info["email"],
                google_id=user_info["sub"],
                name=user_info.get("name", ""),
                picture=user_info.get("picture", "")
            )
            db.add(user)
            db.commit()
        
        # ... existing session creation code ...
        
        # Redirect with new_user flag if applicable
        redirect_url = "/profile?auth=success"
        if is_new_user:
            redirect_url += "&new_user=true"
            
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}")
        return RedirectResponse(url="/login?auth=error")
```

## Testing & Validation

### Local Testing
```bash
cd band-platform
docker-compose -f docker-compose.dev.yml up
```

1. **Test New User Flow**:
   - Use a new Google account or clear user from database
   - Sign in with Google
   - Verify redirect to profile with onboarding form
   - Fill out required fields
   - Submit and verify redirect to dashboard

2. **Test Existing User Flow**:
   - Sign in with existing account
   - Verify normal profile page loads
   - No onboarding shown

3. **Test Profile Creation**:
   - Verify all fields save correctly
   - Check database for new user record
   - Verify can edit profile after creation

### Production Deployment
```bash
cd /Users/murrayheaton/Documents/GitHub/soleil
./scripts/deploy_backend.sh
./scripts/deploy_frontend.sh
```

### Post-Deployment Validation
1. Test with new Google account on production
2. Verify smooth onboarding flow
3. Check error logs for any issues
4. Test profile editing after creation

## Rollback Plan

If issues occur:
```bash
cd /Users/murrayheaton/Documents/GitHub/soleil
git checkout main
./scripts/deploy_backend.sh
./scripts/deploy_frontend.sh
```

## Post-Implementation Steps

1. Update TASK.md with completion
2. Update DEV_LOG.md:
   - Added new user onboarding flow
   - Improved first-time user experience
   - Fixed profile creation issues
3. Update DEV_LOG_TECHNICAL.md:
   - New ProfileOnboarding component
   - Backend new user detection
   - Session data integration
4. Commit changes:
   ```bash
   git add -A
   git commit -m "feat: implement new user onboarding flow

   - Add ProfileOnboarding component with welcoming UI
   - Detect new users in backend auth callback
   - Pre-fill form with Google account data
   - Fix profile creation for first-time users
   - Improve overall onboarding experience"
   
   git push origin feature/new-user-onboarding-flow
   ```
5. Create pull request
6. Archive this PRP after merge