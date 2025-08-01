name: "SOLEil Platform Updates Collection - July 2025"
description: |
  Comprehensive collection of platform updates including critical bug fixes, UI enhancements,
  new features, and mobile optimization. This PRP contains 8 interconnected but independently
  executable sub-PRPs that can be implemented based on priority and need.

---

## Meta-Context for Claude Code

This document contains a collection of PRPs for multiple SOLEil platform updates. As Claude Code, you have the flexibility to:
1. Assess which PRPs are most critical based on the current state of the codebase
2. Identify dependencies between PRPs and suggest optimal implementation order
3. Pivot implementation strategy if you discover better approaches while exploring the codebase
4. Break down complex PRPs into smaller, manageable tasks using your TodoWrite tool
5. Extend research beyond what's provided here if needed for successful implementation

The PRPs are ordered by suggested priority, but you should validate this against the current codebase state.

## Overall Goals

Transform SOLEil into a more robust, user-friendly platform by:
- Fixing critical authentication/profile loading issues
- Creating a modular dashboard system for future growth
- Enhancing the repertoire interface with better organization
- Ensuring mobile responsiveness across all features
- Adding user customization options (scaling, themes)
- Improving navigation and overall UX

## Implementation Philosophy

- **Fix Critical Issues First**: Profile loading bug prevents user access
- **Foundation Before Features**: Navigation and structure updates enable other features
- **User-Facing Before Backend**: Prioritize visible improvements
- **Maintain Existing Patterns**: Follow conventions in CLAUDE.md and existing code
- **Test Everything**: Each PRP includes comprehensive validation steps

---

# PRP Collection Contents

1. **Fix Profile Loading Issue & Persistent Storage** (CRITICAL)
2. **Dashboard Implementation with Modular Design** (HIGH)
3. **Enhanced Repertoire Page with Tabs and Sorting** (HIGH)
4. **Recursive Google Drive Parsing** (MEDIUM)
5. **Navigation and UI Updates** (HIGH)
6. **UI Scaling System** (MEDIUM)
7. **Mobile Responsiveness** (HIGH)
8. **Color Scheme Options** (LOW - Test Feature)

---

# PRP 1: Fix Profile Loading Issue & Implement Persistent User Profiles

name: "Fix Profile Loading & Persistent Storage Implementation"
priority: CRITICAL
estimated_effort: 4-6 hours

## Context
Users are experiencing an infinite loading loop on the "loading profile" screen after Google authorization. This completely blocks platform access and must be fixed immediately.

## Goal
Diagnose and fix the post-authorization loading issue, then implement robust profile persistence with proper error recovery mechanisms.

## Why
- **Blocker**: Users cannot access the platform at all
- **Trust**: Profile data loss erodes user confidence
- **Reliability**: Need bulletproof auth flow

## Success Criteria
- [ ] Users can log in without getting stuck
- [ ] Profile data persists indefinitely
- [ ] Clear error messages on failure
- [ ] Loading completes within 3 seconds
- [ ] Graceful recovery from missing profiles

## Investigation Steps

```yaml
Priority Checks:
  - Check browser console for errors during loading
  - Inspect network tab for failed API calls
  - Review backend logs for auth errors
  - Test with fresh user account
  - Check if user_profiles.json is corrupted

Key Files to Examine:
  - backend/start_server.py - Auth endpoints
  - backend/user_profiles.json - Storage mechanism  
  - frontend/src/app/page.tsx - Loading logic
  - frontend/src/app/api/auth/route.ts - Client auth
```

## Implementation Tasks

### Task 1: Add Comprehensive Logging
```python
# In backend/start_server.py auth endpoints
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@app.post("/auth/callback")
async def auth_callback(request: Request):
    start_time = datetime.now()
    logger.info(f"Auth callback started for session {request.session.get('id')}")
    
    try:
        # Existing auth logic with added logging
        profile = await get_or_create_profile(user_info)
        logger.info(f"Profile {'created' if created else 'retrieved'} for {user_info.email}")
        
    except Exception as e:
        logger.error(f"Auth callback failed: {str(e)}", exc_info=True)
        raise
    
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Auth callback completed in {duration}s")
```

### Task 2: Fix Frontend Loading State
```typescript
// frontend/src/app/page.tsx
const PROFILE_LOAD_TIMEOUT = 10000; // 10 seconds

export default function HomePage() {
    const [loadingState, setLoadingState] = useState<'loading' | 'error' | 'timeout' | 'success'>('loading');
    const [error, setError] = useState<string | null>(null);
    
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            if (loadingState === 'loading') {
                setLoadingState('timeout');
                setError('Profile loading timed out. Please refresh the page.');
            }
        }, PROFILE_LOAD_TIMEOUT);
        
        loadProfile()
            .then(profile => {
                setLoadingState('success');
                // Redirect to dashboard
            })
            .catch(err => {
                setLoadingState('error');
                setError(err.message || 'Failed to load profile');
            })
            .finally(() => {
                clearTimeout(timeoutId);
            });
            
        return () => clearTimeout(timeoutId);
    }, []);
    
    // Render appropriate UI based on state
}
```

### Task 3: Implement Robust Profile Storage
```python
# backend/app/services/profile_service.py
import json
import asyncio
from typing import Optional
from datetime import datetime

class ProfileService:
    def __init__(self, storage_path: str = "user_profiles.json"):
        self.storage_path = storage_path
        self._lock = asyncio.Lock()
        
    async def get_or_create_profile(self, user_id: str, email: str, name: str) -> dict:
        """Get existing profile or create new one with retry logic."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with self._lock:
                    profiles = await self._load_profiles()
                    
                    if user_id in profiles:
                        return profiles[user_id]
                    
                    # Create new profile
                    profile = {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "instruments": [],
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    profiles[user_id] = profile
                    await self._save_profiles(profiles)
                    
                    return profile
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt - create minimal profile in memory
                    return {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "instruments": [],
                        "error": "Profile storage unavailable"
                    }
                await asyncio.sleep(2 ** attempt)
```

## Validation Commands

```bash
# Backend validation
cd band-platform/backend
source venv_linux/bin/activate

# Check for syntax errors
python -m py_compile start_server.py

# Run with debug logging
python start_server.py --log-level=DEBUG

# Test auth endpoint directly
curl -X POST http://localhost:8000/auth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "test_auth_code"}'

# Frontend validation
cd ../frontend
npm run dev

# Test in browser
# 1. Clear all cookies/storage
# 2. Go through full auth flow
# 3. Verify no loading hang
```

---

# PRP 2: Dashboard Implementation with Modular Design

name: "Modular Dashboard Implementation"
priority: HIGH
estimated_effort: 6-8 hours
dependencies: ["PRP 1", "PRP 5"]

## Goal
Replace the profile landing page with an extensible dashboard that displays modular widgets for various band activities and can grow with future features.

## Why
- **Central Hub**: One place for all important information
- **Scalability**: Easy to add new features as widgets
- **User Experience**: Quick access to key functions
- **Future-Proof**: Built for expansion

## Success Criteria
- [ ] Dashboard loads as default post-login page
- [ ] Shows 4 initial modules: upcoming gigs, pending offers, completed gigs, recent repertoire
- [ ] Responsive grid layout on all devices
- [ ] Modules load independently (no cascade failures)
- [ ] Load time under 2 seconds
- [ ] Empty states handled gracefully

## Implementation Blueprint

### Module Architecture
```typescript
// frontend/src/types/dashboard.ts
export interface DashboardModule {
    id: string;
    title: string;
    description?: string;
    icon: React.ComponentType<IconProps>;
    component: React.ComponentType<ModuleProps>;
    defaultSize: GridSize;
    minSize?: GridSize;
    maxSize?: GridSize;
    permissions?: string[];
    refreshInterval?: number; // in milliseconds
}

export interface ModuleProps {
    isLoading?: boolean;
    error?: Error | null;
    onRefresh?: () => void;
}

export interface GridSize {
    w: number; // width in grid units
    h: number; // height in grid units
}
```

### Task 1: Create Dashboard Layout
```typescript
// frontend/src/app/dashboard/page.tsx
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';
import { moduleRegistry } from '@/config/dashboard-modules';

export default function DashboardPage() {
    const { user } = useAuth();
    const modules = useUserModules(user?.id);
    
    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <h1>Welcome back, {user?.name}</h1>
                <p className="subtitle">
                    {new Date().toLocaleDateString('en-US', { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                    })}
                </p>
            </header>
            
            <DashboardGrid 
                modules={modules}
                registry={moduleRegistry}
                onLayoutChange={handleLayoutChange}
            />
        </div>
    );
}
```

### Task 2: Create Module Components

```typescript
// frontend/src/components/dashboard/modules/UpcomingGigsWidget.tsx
export const UpcomingGigsWidget: React.FC<ModuleProps> = ({ onRefresh }) => {
    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['dashboard', 'upcoming-gigs'],
        queryFn: fetchUpcomingGigs,
        staleTime: 5 * 60 * 1000, // 5 minutes
        refetchInterval: 10 * 60 * 1000, // 10 minutes
    });
    
    if (isLoading) return <ModuleLoader />;
    if (error) return <ModuleError error={error} onRetry={refetch} />;
    if (!data?.length) {
        return (
            <EmptyState 
                icon={CalendarIcon}
                message="No upcoming gigs"
                action={{ label: "Add a gig", href: "/gigs/new" }}
            />
        );
    }
    
    return (
        <div className="module-content">
            <div className="module-header">
                <h3>Upcoming Gigs</h3>
                <button onClick={onRefresh || refetch} className="refresh-btn">
                    <RefreshIcon />
                </button>
            </div>
            
            <ul className="gig-list">
                {data.slice(0, 5).map(gig => (
                    <li key={gig.id} className="gig-item">
                        <div className="gig-date">
                            <span className="day">{format(gig.date, 'dd')}</span>
                            <span className="month">{format(gig.date, 'MMM')}</span>
                        </div>
                        <div className="gig-details">
                            <h4>{gig.venue}</h4>
                            <p>{gig.time} • {gig.setLength}</p>
                        </div>
                    </li>
                ))}
            </ul>
            
            {data.length > 5 && (
                <Link href="/gigs" className="view-all-link">
                    View all {data.length} gigs →
                </Link>
            )}
        </div>
    );
};

// frontend/src/components/dashboard/modules/RecentRepertoireWidget.tsx
export const RecentRepertoireWidget: React.FC<ModuleProps> = () => {
    const { data, isLoading, error } = useQuery({
        queryKey: ['dashboard', 'recent-repertoire'],
        queryFn: fetchRecentRepertoire,
    });
    
    return (
        <div className="module-content">
            <h3>Recently Added</h3>
            <div className="repertoire-list">
                {data?.map(item => (
                    <div key={item.id} className="repertoire-item">
                        <MusicNoteIcon className="item-icon" />
                        <div className="item-details">
                            <span className="title">{item.title}</span>
                            <span className="meta">
                                {item.key} • Added {formatRelative(item.addedAt)}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
```

### Task 3: Create Dashboard API
```python
# backend/app/api/dashboard_routes.py
from fastapi import APIRouter, Depends
from typing import Dict, Any
import asyncio

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/data")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Fetch all dashboard data in one request."""
    
    # Parallel fetch all widget data
    results = await asyncio.gather(
        get_upcoming_gigs(current_user.band_id, db),
        get_pending_offers(current_user.band_id, db),
        get_completed_gigs(current_user.band_id, db),
        get_recent_repertoire(current_user.band_id, db),
        return_exceptions=True
    )
    
    return {
        "upcoming_gigs": results[0] if not isinstance(results[0], Exception) else [],
        "pending_offers": results[1] if not isinstance(results[1], Exception) else [],
        "completed_gigs": results[2] if not isinstance(results[2], Exception) else [],
        "recent_repertoire": results[3] if not isinstance(results[3], Exception) else [],
    }

async def get_upcoming_gigs(band_id: int, db: AsyncSession):
    """Get upcoming gigs for the band."""
    query = select(Gig).where(
        Gig.band_id == band_id,
        Gig.date >= datetime.utcnow(),
        Gig.status == "confirmed"
    ).order_by(Gig.date).limit(10)
    
    result = await db.execute(query)
    return [GigSchema.from_orm(gig) for gig in result.scalars()]
```

### Module Registry Configuration
```typescript
// frontend/src/config/dashboard-modules.ts
import { DashboardModule } from '@/types/dashboard';
import { 
    UpcomingGigsWidget,
    PendingOffersWidget,
    CompletedGigsWidget,
    RecentRepertoireWidget 
} from '@/components/dashboard/modules';

export const moduleRegistry