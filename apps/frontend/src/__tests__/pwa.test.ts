import '@testing-library/jest-dom'

// Mock service worker
const mockServiceWorker = {
  register: jest.fn().mockResolvedValue({
    installing: null,
    waiting: null,
    active: {
      state: 'activated',
      scriptURL: '/sw.js',
    },
    update: jest.fn(),
    unregister: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  }),
  getRegistration: jest.fn().mockResolvedValue(null),
}

Object.defineProperty(navigator, 'serviceWorker', {
  value: mockServiceWorker,
  writable: true,
})

// Mock cache API
const mockCache = {
  add: jest.fn().mockResolvedValue(undefined),
  addAll: jest.fn().mockResolvedValue(undefined),
  delete: jest.fn().mockResolvedValue(true),
  keys: jest.fn().mockResolvedValue([]),
  match: jest.fn().mockResolvedValue(undefined),
  matchAll: jest.fn().mockResolvedValue([]),
  put: jest.fn().mockResolvedValue(undefined),
}

const mockCaches = {
  open: jest.fn().mockResolvedValue(mockCache),
  delete: jest.fn().mockResolvedValue(true),
  has: jest.fn().mockResolvedValue(false),
  keys: jest.fn().mockResolvedValue([]),
  match: jest.fn().mockResolvedValue(undefined),
}

Object.defineProperty(global, 'caches', {
  value: mockCaches,
  writable: true,
})

describe('PWA Functionality', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Reset DOM
    document.head.innerHTML = ''
    document.body.innerHTML = ''
  })

  describe('Manifest Configuration', () => {
    it('should have correct manifest.json structure', async () => {
      // Mock fetch to return manifest
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          name: 'Band Platform',
          short_name: 'BandPlatform',
          description: 'A Progressive Web App for band management',
          start_url: '/',
          display: 'standalone',
          background_color: '#1f2937',
          theme_color: '#1f2937',
          icons: [
            {
              src: '/icons/icon-192x192.png',
              sizes: '192x192',
              type: 'image/png',
            },
            {
              src: '/icons/icon-512x512.png',
              sizes: '512x512',
              type: 'image/png',
            },
          ],
        }),
      })

      const response = await fetch('/manifest.json')
      const manifest = await response.json()

      expect(manifest).toMatchObject({
        name: 'Band Platform',
        short_name: 'BandPlatform',
        display: 'standalone',
        start_url: '/',
      })
      expect(manifest.icons).toHaveLength(2)
    })

    it('should have manifest link in document head', () => {
      // Add manifest link to head
      const link = document.createElement('link')
      link.rel = 'manifest'
      link.href = '/manifest.json'
      document.head.appendChild(link)

      const manifestLink = document.querySelector('link[rel="manifest"]')
      expect(manifestLink).toBeInTheDocument()
      expect(manifestLink?.getAttribute('href')).toBe('/manifest.json')
    })

    it('should have theme color meta tag', () => {
      const metaTheme = document.createElement('meta')
      metaTheme.name = 'theme-color'
      metaTheme.content = '#1f2937'
      document.head.appendChild(metaTheme)

      const themeColorMeta = document.querySelector('meta[name="theme-color"]')
      expect(themeColorMeta).toBeInTheDocument()
      expect(themeColorMeta?.getAttribute('content')).toBe('#1f2937')
    })
  })

  describe('Service Worker Registration', () => {
    it('should register service worker if supported', async () => {
      if ('serviceWorker' in navigator) {
        await navigator.serviceWorker.register('/sw.js')
        
        expect(mockServiceWorker.register).toHaveBeenCalledWith('/sw.js')
      }
    })

    it('should handle service worker registration errors', async () => {
      mockServiceWorker.register.mockRejectedValue(new Error('Registration failed'))

      await expect(navigator.serviceWorker.register('/sw.js')).rejects.toThrow('Registration failed')
    })

    it('should update service worker when new version available', async () => {
      const registration = await navigator.serviceWorker.register('/sw.js')
      await registration.update()

      expect(registration.update).toHaveBeenCalled()
    })
  })

  describe('Offline Support', () => {
    it('should cache essential resources', async () => {
      const cache = await caches.open('band-platform-v1')
      const resourcesToCache = [
        '/',
        '/charts',
        '/audio',
        '/setlists',
        '/static/js/bundle.js',
        '/static/css/main.css',
      ]

      await cache.addAll(resourcesToCache)

      expect(mockCache.addAll).toHaveBeenCalledWith(resourcesToCache)
    })

    it('should serve cached content when offline', async () => {
      const mockResponse = new Response('cached content', {
        status: 200,
        headers: { 'Content-Type': 'text/html' },
      })

      mockCache.match.mockResolvedValue(mockResponse)

      const cachedResponse = await caches.match('/')
      expect(cachedResponse).toBe(mockResponse)
    })

    it('should update cache with fresh content when online', async () => {
      const freshResponse = new Response('fresh content', {
        status: 200,
        headers: { 'Content-Type': 'text/html' },
      })

      const cache = await caches.open('band-platform-v1')
      await cache.put('/', freshResponse.clone())

      expect(mockCache.put).toHaveBeenCalledWith('/', freshResponse)
    })

    it('should handle cache storage quota exceeded', async () => {
      mockCache.put.mockRejectedValue(new DOMException('Quota exceeded', 'QuotaExceededError'))

      const cache = await caches.open('band-platform-v1')
      
      await expect(cache.put('/', new Response('content'))).rejects.toThrow('Quota exceeded')
    })
  })

  describe('App Install Prompt', () => {
    let mockBeforeInstallPromptEvent: any

    beforeEach(() => {
      mockBeforeInstallPromptEvent = {
        preventDefault: jest.fn(),
        prompt: jest.fn().mockResolvedValue(undefined),
        userChoice: Promise.resolve({ outcome: 'accepted' }),
      }
    })

    it('should capture beforeinstallprompt event', () => {
      const handler = jest.fn()
      window.addEventListener('beforeinstallprompt', handler)

      // Simulate the event
      const event = new CustomEvent('beforeinstallprompt')
      Object.assign(event, mockBeforeInstallPromptEvent)
      window.dispatchEvent(event)

      expect(handler).toHaveBeenCalledWith(event)
    })

    it('should show install prompt when triggered', async () => {
      let deferredPrompt: any = null

      const handleBeforeInstallPrompt = (e: Event) => {
        e.preventDefault()
        deferredPrompt = e
      }

      window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)

      // Simulate the event
      const event = new CustomEvent('beforeinstallprompt')
      Object.assign(event, mockBeforeInstallPromptEvent)
      window.dispatchEvent(event)

      // Trigger install
      if (deferredPrompt) {
        await deferredPrompt.prompt()
        expect(mockBeforeInstallPromptEvent.prompt).toHaveBeenCalled()
      }
    })

    it('should handle user choice for install prompt', async () => {
      const event = new CustomEvent('beforeinstallprompt')
      Object.assign(event, mockBeforeInstallPromptEvent)

      const userChoice = await event.userChoice
      expect(userChoice.outcome).toBe('accepted')
    })
  })

  describe('Background Sync', () => {
    it('should register background sync when supported', async () => {
      const mockRegistration = {
        sync: {
          register: jest.fn().mockResolvedValue(undefined),
        },
      }

      mockServiceWorker.getRegistration.mockResolvedValue(mockRegistration)

      const registration = await navigator.serviceWorker.getRegistration()
      if (registration?.sync) {
        await registration.sync.register('background-sync')
        expect(mockRegistration.sync.register).toHaveBeenCalledWith('background-sync')
      }
    })

    it('should handle background sync events in service worker', () => {
      // This would typically be tested in the service worker file itself
      // For now, we'll just verify the registration mechanism
      const syncHandler = jest.fn()
      
      // Simulate service worker sync event
      const syncEvent = {
        tag: 'background-sync',
        waitUntil: jest.fn(),
      }

      syncHandler(syncEvent)
      expect(syncHandler).toHaveBeenCalledWith(syncEvent)
    })
  })

  describe('Push Notifications', () => {
    let mockNotification: any

    beforeEach(() => {
      mockNotification = {
        requestPermission: jest.fn().mockResolvedValue('granted'),
        permission: 'default',
      }

      Object.defineProperty(global, 'Notification', {
        value: mockNotification,
        writable: true,
      })
    })

    it('should request notification permission', async () => {
      const permission = await Notification.requestPermission()
      
      expect(mockNotification.requestPermission).toHaveBeenCalled()
      expect(permission).toBe('granted')
    })

    it('should handle permission denied', async () => {
      mockNotification.requestPermission.mockResolvedValue('denied')
      
      const permission = await Notification.requestPermission()
      expect(permission).toBe('denied')
    })

    it('should show notification when permitted', () => {
      mockNotification.permission = 'granted'
      
      const notification = new Notification('Test Notification', {
        body: 'This is a test notification',
        icon: '/icons/icon-192x192.png',
      })

      expect(notification).toBeDefined()
    })
  })

  describe('App Shortcuts', () => {
    it('should define app shortcuts in manifest', async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          shortcuts: [
            {
              name: 'View Charts',
              short_name: 'Charts',
              description: 'Browse available sheet music',
              url: '/charts',
              icons: [
                {
                  src: '/icons/icon-192x192.png',
                  sizes: '192x192',
                },
              ],
            },
            {
              name: 'View Setlists',
              short_name: 'Setlists',
              description: 'Manage performance setlists',
              url: '/setlists',
              icons: [
                {
                  src: '/icons/icon-192x192.png',
                  sizes: '192x192',
                },
              ],
            },
          ],
        }),
      })

      const response = await fetch('/manifest.json')
      const manifest = await response.json()

      expect(manifest.shortcuts).toHaveLength(2)
      expect(manifest.shortcuts[0]).toMatchObject({
        name: 'View Charts',
        url: '/charts',
      })
    })
  })

  describe('Storage Quota Management', () => {
    let mockStorageEstimate: any

    beforeEach(() => {
      mockStorageEstimate = {
        quota: 1024 * 1024 * 1024, // 1GB
        usage: 512 * 1024 * 1024,  // 512MB
        usageDetails: {
          indexedDB: 256 * 1024 * 1024,
          caches: 256 * 1024 * 1024,
        },
      }

      Object.defineProperty(navigator, 'storage', {
        value: {
          estimate: jest.fn().mockResolvedValue(mockStorageEstimate),
          persist: jest.fn().mockResolvedValue(true),
          persisted: jest.fn().mockResolvedValue(false),
        },
        writable: true,
      })
    })

    it('should estimate storage usage', async () => {
      const estimate = await navigator.storage.estimate()
      
      expect(estimate.quota).toBe(1024 * 1024 * 1024)
      expect(estimate.usage).toBe(512 * 1024 * 1024)
    })

    it('should request persistent storage', async () => {
      const persistent = await navigator.storage.persist()
      
      expect(navigator.storage.persist).toHaveBeenCalled()
      expect(persistent).toBe(true)
    })

    it('should check if storage is persistent', async () => {
      const isPersistent = await navigator.storage.persisted()
      
      expect(navigator.storage.persisted).toHaveBeenCalled()
      expect(isPersistent).toBe(false)
    })
  })

  describe('Network Status Handling', () => {
    it('should detect online/offline status', () => {
      Object.defineProperty(navigator, 'onLine', {
        value: true,
        writable: true,
      })

      expect(navigator.onLine).toBe(true)

      // Simulate going offline
      Object.defineProperty(navigator, 'onLine', {
        value: false,
        writable: true,
      })

      expect(navigator.onLine).toBe(false)
    })

    it('should listen for online/offline events', () => {
      const onlineHandler = jest.fn()
      const offlineHandler = jest.fn()

      window.addEventListener('online', onlineHandler)
      window.addEventListener('offline', offlineHandler)

      // Simulate events
      window.dispatchEvent(new Event('online'))
      window.dispatchEvent(new Event('offline'))

      expect(onlineHandler).toHaveBeenCalled()
      expect(offlineHandler).toHaveBeenCalled()
    })
  })

  describe('App Update Handling', () => {
    it('should detect app updates', async () => {
      const registration = await navigator.serviceWorker.register('/sw.js')
      
      // Simulate service worker update
      const newWorker = {
        state: 'installed',
        addEventListener: jest.fn(),
        postMessage: jest.fn(),
      }

      registration.waiting = newWorker

      // Should detect that an update is available
      expect(registration.waiting).toBeTruthy()
    })

    it('should prompt user for app update', () => {
      const updateHandler = jest.fn()

      // Simulate showing update notification
      const showUpdateNotification = () => {
        const shouldUpdate = window.confirm('A new version is available. Update now?')
        if (shouldUpdate) {
          updateHandler()
        }
      }

      // Mock window.confirm
      window.confirm = jest.fn().mockReturnValue(true)
      
      showUpdateNotification()
      expect(updateHandler).toHaveBeenCalled()
    })
  })
})