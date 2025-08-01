name: "Navigation Enhancement and UI Improvements"
description: |
  Update navigation with functional logo link, new menu items, placeholder pages,
  and fix visual polish issues including overscroll background color.

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
   git checkout -b feature/navigation-ui-updates
   ```

3. **Review current navigation structure**:
   - Test navigation at https://solepower.live
   - Note current navigation items and behavior
   - Check mobile responsiveness

---

## Goal
Update navigation functionality with clickable logo, new menu items, proper page structure, and fix UI polish issues that affect perceived quality.

## Why
- **Usability**: Users expect logo to link to home/dashboard
- **Structure**: Clear navigation paths improve user experience
- **Polish**: Small details like overscroll color affect perceived quality
- **Foundation**: Sets up structure for future features

## Success Criteria
- [ ] SOLEil logo clicks through to /dashboard
- [ ] Navigation includes: Dashboard, Repertoire, Upcoming Gigs, Settings, Profile
- [ ] Active navigation item is visually highlighted
- [ ] Upcoming Gigs page shows professional "Under Construction" message
- [ ] Profile page moved to /profile route (no repertoire button)
- [ ] Overscroll background is white instead of blue
- [ ] All navigation works on mobile devices
- [ ] Works in production at https://solepower.live

## Implementation Tasks

### Task 1: Update Navigation Component with Clickable Logo
```typescript
// frontend/src/components/Layout.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navItems = [
    { href: '/dashboard', label: 'Dashboard' },
    { href: '/repertoire', label: 'Repertoire' },
    { href: '/upcoming-gigs', label: 'Upcoming Gigs' },
    { href: '/settings', label: 'Settings' },
    { href: '/profile', label: 'Profile' },
];

export function Layout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    
    const handleSignOut = async () => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include',
        });
        
        if (response.ok) {
            window.location.href = '/login';
        }
    };
    
    return (
        <div className="app-container">
            <nav className="nav-container">
                <div className="nav-content">
                    {/* Logo - Now clickable */}
                    <Link href="/dashboard" className="logo-link">
                        <div className="logo-wrapper">
                            <span className="logo-sole">SOLE</span>
                            <span className="logo-il">il</span>
                        </div>
                    </Link>
                    
                    {/* Navigation Items */}
                    <ul className="nav-items">
                        {navItems.map(item => (
                            <li key={item.href}>
                                <Link 
                                    href={item.href}
                                    className={cn(
                                        "nav-link",
                                        pathname === item.href && "active"
                                    )}
                                >
                                    {item.label}
                                </Link>
                            </li>
                        ))}
                    </ul>
                    
                    {/* Sign Out */}
                    <button 
                        onClick={handleSignOut}
                        className="sign-out-btn"
                    >
                        Sign Out
                    </button>
                </div>
            </nav>
            
            <main className="main-content">
                {children}
            </main>
        </div>
    );
}
```

### Task 2: Create Placeholder Pages

#### Upcoming Gigs Page
```typescript
// frontend/src/app/upcoming-gigs/page.tsx
export default function UpcomingGigsPage() {
    return (
        <div className="page-container">
            <div className="placeholder-content">
                <div className="placeholder-icon">🚧</div>
                <h1>Upcoming Gigs</h1>
                <p className="placeholder-message">
                    This feature is currently under construction
                </p>
                <p className="placeholder-eta">
                    Expected launch: Q1 2025
                </p>
                <div className="placeholder-contact">
                    <p>Have ideas for this feature?</p>
                    <a 
                        href="mailto:feedback@solepower.live" 
                        className="feedback-link"
                    >
                        Let us know!
                    </a>
                </div>
            </div>
        </div>
    );
}
```

#### Settings Page
```typescript
// frontend/src/app/settings/page.tsx
export default function SettingsPage() {
    return (
        <div className="page-container">
            <h1>Settings</h1>
            
            <div className="settings-sections">
                <section className="settings-section">
                    <h2>Account</h2>
                    <div className="settings-placeholder">
                        <p>Account management features coming soon</p>
                    </div>
                </section>
                
                <section className="settings-section">
                    <h2>Display Preferences</h2>
                    <div className="settings-placeholder">
                        <p>UI scaling options coming soon</p>
                        <p>Color theme selection coming soon</p>
                    </div>
                </section>
                
                <section className="settings-section">
                    <h2>Notifications</h2>
                    <div className="settings-placeholder">
                        <p>Email and push notification preferences coming soon</p>
                    </div>
                </section>
            </div>
        </div>
    );
}
```

### Task 3: Move and Update Profile Page

First, move the existing landing page to profile route:
```bash
# This will be done by Claude Code
mv frontend/src/app/page.tsx frontend/src/app/profile/page.tsx
```

Update the profile page to remove repertoire button:
```typescript
// frontend/src/app/profile/page.tsx
'use client';

// Remove any "Go to Repertoire" button from the existing code
// Keep all instrument selection and profile functionality
export default function ProfilePage() {
    // Existing profile code but remove:
    // - Any button or link that says "Go to Repertoire"
    // - Any automatic navigation to repertoire
    
    return (
        <div className="profile-page">
            <h1>My Profile</h1>
            {/* Existing profile content without repertoire navigation */}
        </div>
    );
}
```

Create new root page that redirects:
```typescript
// frontend/src/app/page.tsx (new file)
import { redirect } from 'next/navigation';

export default function HomePage() {
    // Always redirect to dashboard
    redirect('/dashboard');
}
```

### Task 4: Fix Overscroll Background Color
```css
/* frontend/src/app/globals.css - Add/update these styles */

/* Root color variables */
:root {
    --background: #ffffff;
    --foreground: #171717;
    --overscroll-bg: #ffffff; /* White overscroll instead of blue */
    --border: #e5e5e5;
    --primary: #ff6b00;
    --primary-foreground: #ffffff;
}

/* Fix overscroll on all platforms */
html {
    background-color: var(--overscroll-bg);
    min-height: 100%;
}

body {
    background-color: var(--background);
    color: var(--foreground);
    min-height: 100vh;
    margin: 0;
    
    /* Prevent overscroll bounce on iOS */
    overscroll-behavior-y: none;
    -webkit-overflow-scrolling: touch;
}

/* Additional overscroll fix for webkit browsers */
@supports (-webkit-touch-callout: none) {
    body::before,
    body::after {
        content: '';
        position: fixed;
        left: 0;
        right: 0;
        height: 100vh;
        background: var(--overscroll-bg);
        pointer-events: none;
        z-index: -1;
    }
    
    body::before {
        top: -100vh;
    }
    
    body::after {
        bottom: -100vh;
    }
}

/* Navigation Styles */
.nav-container {
    background: var(--background);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
    width: 100%;
}

.nav-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
}

/* Logo Styles */
.logo-link {
    text-decoration: none;
    transition: opacity 0.2s ease;
    flex-shrink: 0;
}

.logo-link:hover {
    opacity: 0.8;
}

.logo-wrapper {
    display: flex;
    align-items: baseline;
    font-size: 1.5rem;
    font-weight: bold;
}

.logo-sole {
    color: var(--foreground);
}

.logo-il {
    color: var(--primary);
    font-style: italic;
}

/* Navigation Items */
.nav-items {
    display: flex;
    gap: 0.5rem;
    list-style: none;
    margin: 0;
    padding: 0;
    flex: 1;
    justify-content: center;
}

.nav-link {
    display: block;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    text-decoration: none;
    color: var(--foreground);
    transition: all 0.2s ease;
    white-space: nowrap;
}

.nav-link:hover {
    background: rgba(0, 0, 0, 0.05);
}

.nav-link.active {
    background: var(--primary);
    color: var(--primary-foreground);
}

/* Sign Out Button */
.sign-out-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    background: transparent;
    color: var(--foreground);
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;
}

.sign-out-btn:hover {
    background: rgba(0, 0, 0, 0.05);
}

/* Placeholder Page Styles */
.placeholder-content {
    max-width: 600px;
    margin: 4rem auto;
    text-align: center;
    padding: 2rem;
}

.placeholder-icon {
    font-size: 4rem;
    margin-bottom: 2rem;
}

.placeholder-message {
    font-size: 1.25rem;
    color: #666;
    margin: 1rem 0;
}

.placeholder-eta {
    font-size: 1rem;
    color: #999;
    margin-bottom: 3rem;
}

.placeholder-contact {
    padding-top: 2rem;
    border-top: 1px solid var(--border);
}

.feedback-link {
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
}

.feedback-link:hover {
    text-decoration: underline;
}

/* Settings Page Styles */
.settings-sections {
    max-width: 800px;
    margin: 0 auto;
}

.settings-section {
    margin-bottom: 3rem;
    padding: 2rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
}

.settings-section h2 {
    margin-bottom: 1rem;
}

.settings-placeholder {
    color: #666;
}

.settings-placeholder p {
    margin: 0.5rem 0;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .nav-content {
        padding: 1rem;
        flex-wrap: wrap;
    }
    
    .nav-items {
        order: 3;
        width: 100%;
        justify-content: space-around;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border);
    }
    
    .nav-link {
        padding: 0.5rem;
        font-size: 0.875rem;
    }
    
    .logo-wrapper {
        font-size: 1.25rem;
    }
}
```

## Testing & Validation

### Local Testing
```bash
cd ~/Documents/GitHub/soleil/band-platform

# Start backend
cd backend
source venv_linux/bin/activate
python start_server.py

# Start frontend (new terminal)
cd frontend
npm run dev

# Test at http://localhost:3000
# 1. Click logo - should go to /dashboard
# 2. Navigate to each menu item
# 3. Check active state highlighting
# 4. Test overscroll at top/bottom of pages
# 5. Test on mobile view (375px, 768px)
```

### Production Deployment
```bash
cd ~/Documents/GitHub/soleil

# Commit changes
git add -A
git commit -m "feat: update navigation with new menu items and fix UI issues

- Make logo clickable to dashboard
- Add Settings and Profile to navigation
- Create placeholder pages for upcoming features
- Move profile to dedicated route
- Fix blue overscroll background to white
- Improve mobile responsive navigation"

# Push to feature branch
git push origin feature/navigation-ui-updates

# Deploy using the deploy script
./deploy-to-do.sh
```

### Validation Checklist
- [ ] Logo clicks through to /dashboard
- [ ] All navigation items are visible and functional
- [ ] Active navigation item has visual indicator
- [ ] Upcoming Gigs shows professional placeholder
- [ ] Settings page shows organized placeholder sections
- [ ] Profile page at /profile without repertoire button
- [ ] Root URL (/) redirects to /dashboard
- [ ] Overscroll is white on all pages
- [ ] Navigation collapses gracefully on mobile
- [ ] Sign out button works correctly
- [ ] All changes work at https://solepower.live

## Rollback Plan
If issues occur:
```bash
ssh root@159.203.62.132
cd /soleil/band-platform
git checkout main
docker-compose -f docker-compose.production.yml up -d --build
```

## Post-Deployment
1. Test all navigation paths on production
2. Verify mobile responsiveness on actual devices
3. Check browser console for any errors
4. Update DEV_LOG.md with user-facing changes
5. Update DEV_LOG_TECHNICAL.md with implementation details
6. Mark tasks complete in TASK.md