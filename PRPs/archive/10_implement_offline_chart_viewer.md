# PRP 10: Implement Offline Chart Viewer

## Overview
**Description**: Add offline viewing capability for charts so musicians can access their music without internet connection during gigs. This addresses the user story: As a musician, I want to view my charts offline so I can perform even without internet access.
**Priority**: High
**Estimated Effort**: L
**Modules Affected**: frontend, sync, content

## Business Justification
This feature is critical for live performance scenarios where internet connectivity may be unreliable or unavailable. Musicians need guaranteed access to their charts during gigs, making offline functionality a must-have feature for professional use.

## Pre-Implementation Requirements
- [ ] Read PWA documentation and service worker best practices
- [ ] Review current chart viewing implementation
- [ ] Check IndexedDB storage limits and strategies
- [ ] Create feature branch: `git checkout -b feature/offline-chart-viewer`
- [ ] Ensure service worker infrastructure is in place

## Success Criteria
- [ ] Charts can be viewed without internet connection
- [ ] User can select which charts to make available offline
- [ ] Offline charts sync when connection restored
- [ ] Clear indicator shows which charts are available offline
- [ ] Storage usage is displayed to user
- [ ] Works on iOS and Android devices
- [ ] No regression in online functionality

## Implementation Tasks

### Task 1: Implement Service Worker Caching
**Assigned to**: frontend_agent
**Estimated hours**: 16

**Files to modify**:
- `public/sw.js`
- `src/lib/serviceWorker.ts`
- `src/app/layout.tsx`

**Implementation steps**:
1. Create advanced caching strategy for PDF files
2. Implement selective caching based on user preference
3. Add cache versioning and cleanup logic
4. Register service worker with app

**Code example**:
```javascript
// public/sw.js
import { registerRoute } from 'workbox-routing';
import { CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// Implement offline chart caching
registerRoute(
  ({ request, url }) => {
    return request.destination === 'document' && 
           url.pathname.includes('/charts/') &&
           url.searchParams.get('offline') === 'true';
  },
  new CacheFirst({
    cacheName: 'offline-charts-v1',
    plugins: [
      new CacheableResponsePlugin({
        statuses: [0, 200],
      }),
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
        purgeOnQuotaError: true,
      }),
    ],
  })
);
```

**Testing requirements**:
- Service worker installs correctly
- Charts cache when marked for offline
- Cached charts load without network
- Cache size limits respected

### Task 2: Create Offline Management UI
**Assigned to**: frontend_agent
**Estimated hours**: 12

**Files to modify**:
- `src/components/OfflineManager.tsx`
- `src/components/ChartList.tsx`
- `src/hooks/useOfflineStorage.ts`
- `src/app/repertoire/page.tsx`

**Implementation steps**:
1. Create offline toggle component for each chart
2. Implement storage quota display
3. Add bulk offline management interface
4. Create offline indicator component

**Code example**:
```typescript
// src/components/OfflineToggle.tsx
import { useState, useEffect } from 'react';
import { useOfflineStorage } from '@/hooks/useOfflineStorage';

interface OfflineToggleProps {
  chartId: string;
  fileUrl: string;
  fileName: string;
}

export function OfflineToggle({ chartId, fileUrl, fileName }: OfflineToggleProps) {
  const { isOffline, makeOffline, removeOffline, checkStatus } = useOfflineStorage();
  const [isAvailableOffline, setIsAvailableOffline] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    checkStatus(chartId).then(setIsAvailableOffline);
  }, [chartId]);

  const handleToggle = async () => {
    setIsLoading(true);
    try {
      if (isAvailableOffline) {
        await removeOffline(chartId);
        setIsAvailableOffline(false);
      } else {
        await makeOffline(chartId, fileUrl, fileName);
        setIsAvailableOffline(true);
      }
    } catch (error) {
      console.error('Failed to toggle offline status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleToggle}
      disabled={isLoading || !isOffline}
      className={`offline-toggle ${isAvailableOffline ? 'active' : ''}`}
      aria-label={isAvailableOffline ? 'Remove from offline' : 'Make available offline'}
    >
      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <DownloadIcon filled={isAvailableOffline} />
      )}
    </button>
  );
}
```

**Testing requirements**:
- Toggle changes offline status correctly
- UI reflects current offline state
- Storage quota updates in real-time
- Handles errors gracefully

### Task 3: Implement IndexedDB Storage Layer
**Assigned to**: frontend_agent
**Estimated hours**: 8

**Files to modify**:
- `src/lib/db/offlineStorage.ts`
- `src/lib/db/schema.ts`
- `src/hooks/useOfflineStorage.ts`

**Implementation steps**:
1. Create IndexedDB schema for offline charts
2. Implement CRUD operations for offline storage
3. Add storage quota management
4. Create sync queue for pending changes

**Code example**:
```typescript
// src/lib/db/offlineStorage.ts
import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface OfflineDB extends DBSchema {
  charts: {
    key: string;
    value: {
      id: string;
      fileName: string;
      fileData: Blob;
      mimeType: string;
      savedAt: Date;
      lastAccessed: Date;
      size: number;
    };
    indexes: { 'by-date': Date };
  };
  metadata: {
    key: string;
    value: {
      totalSize: number;
      chartCount: number;
      lastSync: Date;
    };
  };
}

class OfflineStorage {
  private db: IDBPDatabase<OfflineDB> | null = null;

  async init() {
    this.db = await openDB<OfflineDB>('soleil-offline', 1, {
      upgrade(db) {
        const chartStore = db.createObjectStore('charts', { keyPath: 'id' });
        chartStore.createIndex('by-date', 'savedAt');
        db.createObjectStore('metadata', { keyPath: 'key' });
      },
    });
  }

  async saveChart(id: string, file: Blob, fileName: string, mimeType: string) {
    if (!this.db) await this.init();
    
    const size = file.size;
    await this.checkQuota(size);
    
    await this.db!.put('charts', {
      id,
      fileName,
      fileData: file,
      mimeType,
      savedAt: new Date(),
      lastAccessed: new Date(),
      size,
    });
    
    await this.updateMetadata(size, 1);
  }

  async getChart(id: string): Promise<Blob | null> {
    if (!this.db) await this.init();
    
    const chart = await this.db!.get('charts', id);
    if (chart) {
      // Update last accessed
      chart.lastAccessed = new Date();
      await this.db!.put('charts', chart);
      return chart.fileData;
    }
    return null;
  }
}

export const offlineStorage = new OfflineStorage();
```

**Testing requirements**:
- IndexedDB operations work correctly
- Storage quota enforced
- Data persists across sessions
- Cleanup of old data works

### Task 4: Implement Sync Module Updates
**Assigned to**: sync_agent
**Estimated hours**: 8

**Files to modify**:
- `modules/sync/services/offline_sync.py`
- `modules/sync/api/sync_routes.py`
- `modules/sync/models/sync_queue.py`

**Implementation steps**:
1. Create offline sync queue model
2. Implement sync status tracking
3. Add selective sync endpoints
4. Handle conflict resolution

**Code example**:
```python
# modules/sync/services/offline_sync.py
from typing import List, Dict, Optional
from datetime import datetime
from sqlmodel import Session, select

from ..models import SyncQueue, SyncStatus, Chart
from ...core.event_bus import EventBus

class OfflineSyncService:
    def __init__(self, session: Session, event_bus: EventBus):
        self.session = session
        self.event_bus = event_bus
    
    async def mark_for_offline(self, user_id: int, chart_id: str) -> Dict:
        """Mark a chart for offline availability."""
        sync_item = SyncQueue(
            user_id=user_id,
            chart_id=chart_id,
            action="make_offline",
            status=SyncStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.session.add(sync_item)
        await self.session.commit()
        
        # Notify frontend to cache
        await self.event_bus.publish(
            event_type="OFFLINE_SYNC_REQUESTED",
            data={
                "user_id": user_id,
                "chart_id": chart_id,
                "action": "cache"
            },
            source_module="sync"
        )
        
        return {"status": "queued", "sync_id": sync_item.id}
    
    async def get_offline_charts(self, user_id: int) -> List[str]:
        """Get list of charts marked for offline use."""
        query = select(SyncQueue).where(
            SyncQueue.user_id == user_id,
            SyncQueue.action == "make_offline",
            SyncQueue.status == SyncStatus.COMPLETED
        )
        
        results = await self.session.exec(query)
        return [item.chart_id for item in results]
    
    async def sync_offline_changes(self, user_id: int, changes: List[Dict]) -> Dict:
        """Sync offline changes when connection restored."""
        synced = []
        failed = []
        
        for change in changes:
            try:
                await self.apply_change(user_id, change)
                synced.append(change['id'])
            except Exception as e:
                failed.append({
                    'id': change['id'],
                    'error': str(e)
                })
        
        return {
            "synced": len(synced),
            "failed": len(failed),
            "details": failed
        }
```

**Testing requirements**:
- Sync queue processes correctly
- Offline marks propagate to frontend
- Conflict resolution works
- Events published correctly

## Testing Procedures

### Unit Tests
- Test service worker caching logic
- Test IndexedDB operations
- Test offline toggle component
- Test sync queue processing
- Test storage quota calculations

### Integration Tests
- Test complete offline workflow
- Test sync when returning online
- Test storage limit handling
- Test multi-device sync

### E2E Tests
- Test marking chart for offline
- Test viewing chart while offline
- Test sync on reconnection
- Test storage management UI

### Manual Testing Checklist
- [ ] Install PWA on mobile device
- [ ] Mark several charts for offline
- [ ] Enable airplane mode
- [ ] Verify charts still accessible
- [ ] Make changes while offline
- [ ] Restore connection and verify sync

## Deployment Steps
1. Ensure all tests pass locally
2. Build service worker with new caching strategy
3. Test on staging with various devices
4. Deploy backend sync updates first
5. Deploy frontend with service worker
6. Monitor service worker installation rates
7. Check for caching errors in production
8. Verify offline functionality for sample users

## Rollback Plan
If critical issues discovered:
1. Disable service worker: `navigator.serviceWorker.unregister()`
2. Clear offline caches via admin endpoint
3. Revert frontend deployment
4. Investigate issues in staging
5. Fix and re-test thoroughly before re-deployment

## Post-Deployment
- [ ] Monitor service worker error rates
- [ ] Check IndexedDB usage statistics  
- [ ] Gather user feedback on offline experience
- [ ] Monitor sync success rates
- [ ] Update documentation with offline features
- [ ] Create user guide for offline functionality
- [ ] Close related issues: #45, #67, #89
- [ ] Update TASK.md and DEV_LOG.md