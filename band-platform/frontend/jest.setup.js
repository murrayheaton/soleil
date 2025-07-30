import '@testing-library/jest-dom'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return '/'
  },
}))

// Mock react-pdf
jest.mock('react-pdf', () => ({
  Document: ({ children, onLoadSuccess }) => {
    // Simulate successful load
    if (onLoadSuccess) {
      setTimeout(() => onLoadSuccess({ numPages: 1 }), 0)
    }
    return <div data-testid="pdf-document">{children}</div>
  },
  Page: () => <div data-testid="pdf-page">PDF Page</div>,
  pdfjs: {
    GlobalWorkerOptions: {
      workerSrc: '',
    },
    version: '3.0.0',
  },
}))

// Mock IndexedDB
global.indexedDB = {
  open: jest.fn(),
  deleteDatabase: jest.fn(),
}

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  send: jest.fn(),
  close: jest.fn(),
  readyState: 1,
}))

// Mock URL.createObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-url')
global.URL.revokeObjectURL = jest.fn()

// Mock HTMLMediaElement
Object.defineProperty(HTMLMediaElement.prototype, 'play', {
  writable: true,
  value: jest.fn().mockImplementation(() => Promise.resolve()),
})

Object.defineProperty(HTMLMediaElement.prototype, 'pause', {
  writable: true,
  value: jest.fn(),
})

Object.defineProperty(HTMLMediaElement.prototype, 'load', {
  writable: true,
  value: jest.fn(),
})

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock fullscreen API
Object.defineProperty(document, 'fullscreenElement', {
  writable: true,
  value: null,
})

Object.defineProperty(document, 'exitFullscreen', {
  writable: true,
  value: jest.fn().mockImplementation(() => Promise.resolve()),
})

Object.defineProperty(Element.prototype, 'requestFullscreen', {
  writable: true,
  value: jest.fn().mockImplementation(() => Promise.resolve()),
})

// Mock navigator.onLine
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true,
})