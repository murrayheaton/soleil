name: "Modular Dashboard Implementation"
description: |
  Create an extensible dashboard as the new landing page with modular widgets
  for gigs, repertoire updates, and future features.

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
   git checkout -b feature/dashboard-implementation
   ```

3. **Dependencies**: This PRP depends on:
   - PRP 01: Profile loading fix (for authentication)
   - PRP 02: Navigation updates (for /dashboard route)

---

## Goal
Replace the profile landing page with a modular dashboard that displays widgets for band activities and can grow with future features without major refactoring.

## Why
- **Central Hub**: Musicians need one place to see all important information
- **Scalability**: Easy to add new features as widgets without restructuring
- **Efficiency**: Quick access to most-used features at a glance
- **Future-Proof**: Built to accommodate features we haven't thought of yet

## Success Criteria
- [ ] Dashboard loads as default post-login page
- [ ] Shows 4 initial modules working correctly:
  - [ ] Upcoming Gigs (with empty state)
  - [ ] Recent Repertoire (last 10 added)
  - [ ] Pending Offers (placeholder)
  - [ ] Completed Gigs (placeholder)
- [ ] Responsive grid layout adapts to screen size
- [ ] Modules load independently (one failing doesn't break others)
- [ ] Total load time under 2 seconds
- [ ] Empty states show helpful messages
- [ ] Works at https://solepower.live

## Implementation Tasks

### Task 1: Create Dashboard Page Structure
```typescript
// frontend/src/app/dashboard/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';
import { moduleRegistry } from '@/config/dashboard-modules';
import { useAuth } from '@/hooks/useAuth';

export default function DashboardPage() {
    const router = useRouter();
    const { user, isLoading: authLoading } = useAuth();
    const [modules, setModules] = useState([]);
    
    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
        }
    }, [authLoading, user, router]);
    
    if (authLoading) {
        return (
            <div className="dashboard-loading">
                <div className="loading-spinner" />
                <p>Loading dashboard...</p>
            </div>
        );
    }
    
    if (!user) {
        return null; // Redirecting to login
    }
    
    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Welcome back, {user.name}!</h1>
                <p className="dashboard-date">
                    {new Date().toLocaleDateString('en-US', { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                    })}
                </p>
            </header>
            
            <DashboardGrid 
                modules={moduleRegistry}
                userId={user.id}
            />
        </div>
    );
}
```

### Task 2: Create Module System Architecture
```typescript
// frontend/src/types/dashboard.ts
export interface DashboardModule {
    id: string;
    title: string;
    description?: string;
    component: React.ComponentType<ModuleProps>;
    defaultSize: {
        mobile: { cols: number; rows: number };
        tablet: { cols: number; rows: number };
        desktop: { cols: number; rows: number };
    };
    permissions?: string[];
}

export interface ModuleProps {
    userId: string;
}

// frontend/src/components/dashboard/DashboardGrid.tsx
import { Suspense } from 'react';
import { ModuleWrapper } from './ModuleWrapper';

interface DashboardGridProps {
    modules: Map<string, DashboardModule>;
    userId: string;
}

export function DashboardGrid({ modules, userId }: DashboardGridProps) {
    return (
        <div className="dashboard-grid">
            {Array.from(modules.values()).map(module => (
                <ModuleWrapper 
                    key={module.id}
                    module={module}
                >
                    <Suspense 
                        fallback={
                            <div className="module-loading">
                                <div className="loading-spinner" />
                            </div>
                        }
                    >
                        <module.component userId={userId} />
                    </Suspense>
                </ModuleWrapper>
            ))}
        </div>
    );
}

// frontend/src/components/dashboard/ModuleWrapper.tsx
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    module: DashboardModule;
    children: ReactNode;
}

interface State {
    hasError: boolean;
}

export class ModuleWrapper extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }
    
    static getDerivedStateFromError(): State {
        return { hasError: true };
    }
    
    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error(`Module ${this.props.module.id} error:`, error, errorInfo);
    }
    
    render() {
        if (this.state.hasError) {
            return (
                <div className="module-error">
                    <h3>{this.props.module.title}</h3>
                    <p>Unable to load this module</p>
                    <button 
                        onClick={() => this.setState({ hasError: false })}
                        className="retry-btn"
                    >
                        Retry
                    </button>
                </div>
            );
        }
        
        return (
            <div 
                className={`dashboard-module module-${this.props.module.id}`}
                data-module-id={this.props.module.id}
            >
                <div className="module-header">
                    <h3>{this.props.module.title}</h3>
                </div>
                <div className="module-content">
                    {this.props.children}
                </div>
            </div>
        );
    }
}
```

### Task 3: Create Individual Module Components

#### Upcoming Gigs Module
```typescript
// frontend/src/components/dashboard/modules/UpcomingGigsModule.tsx
import { useState, useEffect } from 'react';
import Link from 'next/link';

export function UpcomingGigsModule({ userId }: ModuleProps) {
    const [gigs, setGigs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        fetchUpcomingGigs();
    }, [userId]);
    
    const fetchUpcomingGigs = async () => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/dashboard/upcoming-gigs`,
                { credentials: 'include' }
            );
            
            if (!response.ok) throw new Error('Failed to fetch gigs');
            
            const data = await response.json();
            setGigs(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) {
        return <div className="module-spinner">Loading gigs...</div>;
    }
    
    if (error) {
        return <div className="module-error-text">Unable to load gigs</div>;
    }
    
    if (gigs.length === 0) {
        return (
            <div className="empty-state">
                <p>No upcoming gigs scheduled</p>
                <Link href="/upcoming-gigs" className="empty-state-link">
                    View gig calendar →
                </Link>
            </div>
        );
    }
    
    return (
        <ul className="gig-list">
            {gigs.slice(0, 5).map(gig => (
                <li key={gig.id} className="gig-item">
                    <div className="gig-date">
                        <span className="day">{new Date(gig.date).getDate()}</span>
                        <span className="month">
                            {new Date(gig.date).toLocaleDateString('en-US', { month: 'short' })}
                        </span>
                    </div>
                    <div className="gig-details">
                        <h4>{gig.venue}</h4>
                        <p>{gig.time} • {gig.type}</p>
                    </div>
                </li>
            ))}
        </ul>
    );
}
```

#### Recent Repertoire Module
```typescript
// frontend/src/components/dashboard/modules/RecentRepertoireModule.tsx
import { useState, useEffect } from 'react';
import Link from 'next/link';

export function RecentRepertoireModule({ userId }: ModuleProps) {
    const [repertoire, setRepertoire] = useState([]);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        fetchRecentRepertoire();
    }, [userId]);
    
    const fetchRecentRepertoire = async () => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/dashboard/recent-repertoire`,
                { credentials: 'include' }
            );
            
            if (response.ok) {
                const data = await response.json();
                setRepertoire(data);
            }
        } catch (err) {
            console.error('Failed to fetch repertoire:', err);
        } finally {
            setLoading(false);
        }
    };
    
    if (loading) {
        return <div className="module-spinner">Loading repertoire...</div>;
    }
    
    if (repertoire.length === 0) {
        return (
            <div className="empty-state">
                <p>No repertoire added yet</p>
                <Link href="/repertoire" className="empty-state-link">
                    Browse repertoire →
                </Link>
            </div>
        );
    }
    
    return (
        <div className="repertoire-list">
            {repertoire.slice(0, 10).map(item => (
                <div key={item.id} className="repertoire-item">
                    <span className="repertoire-icon">☀</span>
                    <div className="repertoire-details">
                        <span className="title">{item.title}</span>
                        <span className="meta">
                            {item.key && `${item.key} • `}
                            Added {formatRelativeTime(item.addedAt)}
                        </span>
                    </div>
                </div>
            ))}
        </div>
    );
}

function formatRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'today';
    if (diffInDays === 1) return 'yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
    return date.toLocaleDateString();
}
```

#### Placeholder Modules
```typescript
// frontend/src/components/dashboard/modules/PendingOffersModule.tsx
export function PendingOffersModule({ userId }: ModuleProps) {
    return (
        <div className="placeholder-module">
            <p>Gig offers will appear here</p>
            <p className="coming-soon">Coming soon</p>
        </div>
    );
}

// frontend/src/components/dashboard/modules/CompletedGigsModule.tsx
export function CompletedGigsModule({ userId }: ModuleProps) {
    return (
        <div className="placeholder-module">
            <p>Track completed performances</p>
            <p className="coming-soon">Coming soon</p>
        </div>
    );
}
```

### Task 4: Create Module Registry
```typescript
// frontend/src/config/dashboard-modules.ts
import { DashboardModule } from '@/types/dashboard';
import { UpcomingGigsModule } from '@/components/dashboard/modules/UpcomingGigsModule';
import { RecentRepertoireModule } from '@/components/dashboard/modules/RecentRepertoireModule';
import { PendingOffersModule } from '@/components/dashboard/modules/PendingOffersModule';
import { CompletedGigsModule } from '@/components/dashboard/modules/CompletedGigsModule';

export const moduleRegistry = new Map<string, DashboardModule>([
    ['upcoming-gigs', {
        id: 'upcoming-gigs',
        title: 'Upcoming Gigs',
        component: UpcomingGigsModule,
        defaultSize: {
            mobile: { cols: 1, rows: 2 },
            tablet: { cols: 1, rows: 2 },
            desktop: { cols: 2, rows: 2 }
        }
    }],
    ['recent-repertoire', {
        id: 'recent-repertoire',
        title: 'Recently Added',
        component: RecentRepertoireModule,
        defaultSize: {
            mobile: { cols: 1, rows: 2 },
            tablet: { cols: 1, rows: 2 },
            desktop: { cols: 2, rows: 2 }
        }
    }],
    ['pending-offers', {
        id: 'pending-offers',
        title: 'Pending Offers',
        component: PendingOffersModule,
        defaultSize: {
            mobile: { cols: 1, rows: 1 },
            tablet: { cols: 1, rows: 1 },
            desktop: { cols: 2, rows: 1 }
        }
    }],
    ['completed-gigs', {
        id: 'completed-gigs',
        title: 'Completed Gigs',
        component: CompletedGigsModule,
        defaultSize: {
            mobile: { cols: 1, rows: 1 },
            tablet: { cols: 1, rows: 1 },
            desktop: { cols: 2, rows: 1 }
        }
    }]
]);
```

### Task 5: Create Backend Dashboard Endpoints
```python
# backend/start_server.py - Add dashboard endpoints

@app.get("/api/dashboard/upcoming-gigs")
async def get_upcoming_gigs(request: Request):
    """Get upcoming gigs for dashboard widget."""
    try:
        if not request.session.get('authenticated'):
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        # For now, return empty array (will be implemented with gig management)
        # In future: query database for actual gigs
        return JSONResponse(content=[])
        
    except Exception as e:
        logger.error(f"Failed to fetch upcoming gigs: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to fetch gigs"})

@app.get("/api/dashboard/recent-repertoire")
async def get_recent_repertoire(request: Request):
    """Get recently added repertoire items."""
    try:
        if not request.session.get('authenticated'):
            return JSONResponse(status_code=401, content={"error": "Not authenticated"})
        
        user_profile = request.session.get('user_profile', {})
        
        # Get recent files from Google Drive sync
        # This is placeholder - integrate with actual file sync
        recent_items = []
        
        # In future: Query actual synced files from database
        # For now, return sample data for testing
        if os.path.exists("user_profiles.json"):
            # Could check for recent sync activity here
            pass
        
        return JSONResponse(content=recent_items)
        
    except Exception as e:
        logger.error(f"Failed to fetch recent repertoire: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to fetch repertoire"})
```

### Task 6: Add Dashboard Styles
```css
/* frontend/src/app/dashboard/dashboard.css */
.dashboard-container {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
}

.dashboard-header {
    margin-bottom: 2rem;
}

.dashboard-header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.dashboard-date {
    color: #666;
    font-size: 1rem;
}

/* Grid Layout */
.dashboard-grid {
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    grid-auto-rows: minmax(200px, auto);
}

/* Module Styles */
.dashboard-module {
    background: white;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.module-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border);
    background: #fafafa;
}

.module-header h3 {
    margin: 0;
    font-size: 1.125rem;
}

.module-content {
    padding: 1.5rem;
    flex: 1;
    overflow-y: auto;
}

/* Loading States */
.dashboard-loading,
.module-spinner {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    color: #666;
}

.loading-spinner {
    width: 24px;
    height: 24px;
    border: 2px solid #f0f0f0;
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-right: 0.5rem;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Empty States */
.empty-state {
    text-align: center;
    color: #666;
    padding: 2rem;
}

.empty-state-link {
    color: var(--primary);
    text-decoration: none;
    font-weight: 500;
    margin-top: 1rem;
    display: inline-block;
}

.empty-state-link:hover {
    text-decoration: underline;
}

/* Gig List */
.gig-list {
    list-style: none;
    padding: 0;
    margin: 0;
}

.gig-item {
    display: flex;
    align-items: center;
    padding: 1rem 0;
    border-bottom: 1px solid #f0f0f0;
}

.gig-item:last-child {
    border-bottom: none;
}

.gig-date {
    flex-shrink: 0;
    width: 50px;
    text-align: center;
    margin-right: 1rem;
}

.gig-date .day {
    display: block;
    font-size: 1.5rem;
    font-weight: bold;
    line-height: 1;
}

.gig-date .month {
    display: block;
    font-size: 0.875rem;
    text-transform: uppercase;
    color: #666;
}

.gig-details h4 {
    margin: 0 0 0.25rem 0;
    font-size: 1rem;
}

.gig-details p {
    margin: 0;
    color: #666;
    font-size: 0.875rem;
}

/* Repertoire List */
.repertoire-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.repertoire-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.repertoire-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
}

.repertoire-details {
    flex: 1;
    min-width: 0;
}

.repertoire-details .title {
    display: block;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.repertoire-details .meta {
    display: block;
    font-size: 0.875rem;
    color: #666;
}

/* Placeholder Modules */
.placeholder-module {
    text-align: center;
    color: #666;
    padding: 2rem;
}

.coming-soon {
    font-size: 0.875rem;
    color: #999;
    margin-top: 0.5rem;
}

/* Module Error State */
.module-error {
    padding: 2rem;
    text-align: center;
}

.module-error h3 {
    margin-bottom: 1rem;
}

.retry-btn {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    border: 1px solid var(--primary);
    background: white;
    color: var(--primary);
    border-radius: 0.25rem;
    cursor: pointer;
}

.retry-btn:hover {
    background: var(--primary);
    color: white;
}

/* Responsive Grid */
@media (max-width: 768px) {
    .dashboard-container {
        padding: 1rem;
    }
    
    .dashboard-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
    
    .dashboard-header h1 {
        font-size: 1.5rem;
    }
}

@media (min-width: 769px) and (max-width: 1024px) {
    .dashboard-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (min-width: 1025px) {
    .dashboard-grid {
        grid-template-columns: repeat(4, 1fr);
    }
    
    /* Span modules across grid */
    .module-upcoming-gigs,
    .module-recent-repertoire {
        grid-column: span 2;
        grid-row: span 2;
    }
    
    .module-pending-offers,
    .module-completed-gigs {
        grid-column: span 2;
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
# 1. Login and verify redirect to /dashboard
# 2. Check all 4 modules load
# 3. Test empty states
# 4. Check responsive grid at different sizes
# 5. Verify module error handling (disconnect network)
```

### Production Deployment
```bash
cd ~/Documents/GitHub/soleil

# Commit changes
git add -A
git commit -m "feat: implement modular dashboard with widgets

- Create extensible dashboard architecture
- Add 4 initial modules (gigs, repertoire, offers, completed)
- Implement responsive grid layout
- Add loading and error states
- Create dashboard API endpoints"

# Push and deploy
git push origin feature/dashboard-implementation
./deploy-to-do.sh
```

### Validation Checklist
- [ ] Dashboard loads after login
- [ ] All 4 modules display correctly
- [ ] Empty states show helpful messages
- [ ] Loading states work properly
- [ ] Error boundaries prevent cascade failures
- [ ] Grid adapts to screen size
- [ ] Total load time under 2 seconds
- [ ] Works at https://solepower.live

## Post-Deployment
1. Monitor dashboard performance
2. Check error logs for module failures
3. Gather user feedback on module usefulness
4. Update documentation with changes
5. Plan next modules based on user needs