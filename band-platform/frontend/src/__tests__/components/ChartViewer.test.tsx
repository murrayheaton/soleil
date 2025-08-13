import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ChartViewer from '@/components/ChartViewer'
import type { Chart } from '@/lib/api'

// Mock dependencies
jest.mock('@/lib/database')
jest.mock('@/lib/api')

const mockChart: Chart = {
  id: 'chart-1',
  title: 'All of Me',
  key: 'Bb',
  composer: 'Gerald Marks',
  genre: 'Jazz Standard',
  tempo: 120,
  time_signature: '4/4',
  instrumentation: ['trumpet', 'trombone'],
  google_drive_file_id: 'drive-file-123',
  file_path: '/charts/all-of-me-bb.pdf',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  band_id: 'band-1',
}

describe('ChartViewer', () => {
  const mockOnClose = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock successful API responses
    const mockApiService = require('@/lib/api').apiService
    mockApiService.downloadChart = jest.fn().mockResolvedValue(new Blob(['pdf content'], { type: 'application/pdf' }))
    mockApiService.isAuthError = jest.fn().mockReturnValue(false)
    mockApiService.getAuthUrlOnError = jest.fn().mockResolvedValue('')
    
    // Mock offline storage
    const mockOfflineStorage = require('@/lib/database').offlineStorage
    mockOfflineStorage.getChart = jest.fn().mockResolvedValue(null)
    mockOfflineStorage.storeChart = jest.fn().mockResolvedValue(undefined)
    
    // Mock console.error to avoid noise in tests
    jest.spyOn(console, 'error').mockImplementation(() => {})
    jest.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders chart title and key in toolbar', async () => {
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('All of Me - Bb')).toBeInTheDocument()
    })
  })

  it('displays loading state initially', () => {
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)
    
    // Check for loading spinner
    const spinners = screen.getAllByRole('generic')
    const loadingSpinner = spinners.find(el => el.classList.contains('animate-spin'))
    expect(loadingSpinner).toBeInTheDocument()
  })

  it('shows PDF document after successful load', async () => {
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
      expect(screen.getByTestId('pdf-page')).toBeInTheDocument()
    })
  })

  it('handles zoom in and zoom out', async () => {
    const user = userEvent.setup()
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    const zoomInButton = screen.getByLabelText('Zoom in')
    const zoomOutButton = screen.getByLabelText('Zoom out')

    // Initial zoom should be 100%
    expect(screen.getByText('100%')).toBeInTheDocument()

    // Zoom in
    await user.click(zoomInButton)
    expect(screen.getByText('125%')).toBeInTheDocument()

    // Zoom out
    await user.click(zoomOutButton)
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('handles fullscreen toggle', async () => {
    const user = userEvent.setup()
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    const fullscreenButton = screen.getByLabelText('Toggle fullscreen')
    await user.click(fullscreenButton)

    // Should call requestFullscreen
    expect(Element.prototype.requestFullscreen).toHaveBeenCalled()
  })

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup()
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    const closeButton = screen.getByLabelText('Close')
    await user.click(closeButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('handles keyboard shortcuts', async () => {
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Test zoom in with + key
    fireEvent.keyDown(window, { key: '+' })
    expect(screen.getByText('125%')).toBeInTheDocument()

    // Test zoom out with - key
    fireEvent.keyDown(window, { key: '-' })
    expect(screen.getByText('100%')).toBeInTheDocument()

    // Test close with Escape key
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('downloads chart when download button is clicked', async () => {
    const user = userEvent.setup()
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    // Mock document.createElement
    const mockLink = { click: jest.fn(), href: '', download: '' }
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any)

    const downloadButton = screen.getByLabelText('Download')
    await user.click(downloadButton)

    expect(document.createElement).toHaveBeenCalledWith('a')
    expect(mockLink.click).toHaveBeenCalled()
    expect(mockLink.download).toBe('All of Me - Bb.pdf')
  })

  it('shows offline indicator when chart is cached', async () => {
    const mockOfflineStorage = require('@/lib/database').offlineStorage
    mockOfflineStorage.getChart.mockResolvedValue({
      id: 'chart-1',
      file_data: new ArrayBuffer(100),
    })

    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Offline')).toBeInTheDocument()
    })
  })

  it('handles touch gestures for zoom', async () => {
    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByTestId('pdf-document')).toBeInTheDocument()
    })

    const container = screen.getByTestId('pdf-document').parentElement

    // Simulate pinch gesture
    const touchStart = {
      touches: [
        { clientX: 100, clientY: 100 },
        { clientX: 200, clientY: 200 },
      ],
    }

    const touchMove = {
      touches: [
        { clientX: 90, clientY: 90 },
        { clientX: 210, clientY: 210 },
      ],
    }

    fireEvent.touchStart(container!, touchStart)
    fireEvent.touchMove(container!, touchMove)

    // Zoom level should change due to pinch gesture
    expect(screen.queryByText('100%')).not.toBeInTheDocument()
  })

  it('handles API error gracefully', async () => {
    const mockApiService = require('@/lib/api').apiService
    mockApiService.downloadChart.mockRejectedValue(new Error('Network error'))

    render(<ChartViewer chart={mockChart} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load chart. Please try again.')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })
  })
})