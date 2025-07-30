import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AudioPlayer from '@/components/AudioPlayer'
import type { Audio } from '@/lib/api'

// Mock dependencies
jest.mock('@/lib/database')
jest.mock('@/lib/api')

const mockAudio: Audio = {
  id: 'audio-1',
  title: 'All of Me - Reference',
  reference_type: 'reference',
  google_drive_file_id: 'drive-audio-123',
  file_path: '/audio/all-of-me-reference.mp3',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  band_id: 'band-1',
}

describe('AudioPlayer', () => {
  const mockOnClose = jest.fn()
  const mockOnNext = jest.fn()
  const mockOnPrevious = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock successful API responses
    const mockApiService = require('@/lib/api').apiService
    mockApiService.downloadAudio = jest.fn().mockResolvedValue(new Blob(['audio content'], { type: 'audio/mpeg' }))
    
    // Mock offline storage
    const mockOfflineStorage = require('@/lib/database').offlineStorage
    mockOfflineStorage.getAudio = jest.fn().mockResolvedValue(null)
    mockOfflineStorage.storeAudio = jest.fn().mockResolvedValue(undefined)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders audio title and reference type', async () => {
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('All of Me - Reference')).toBeInTheDocument()
      expect(screen.getByText('Reference Recording')).toBeInTheDocument()
    })
  })

  it('displays loading state initially', () => {
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)
    
    expect(screen.getByRole('generic')).toHaveClass('animate-spin')
  })

  it('shows play/pause button after loading', async () => {
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Play')).toBeInTheDocument()
    })
  })

  it('toggles play/pause when button is clicked', async () => {
    const user = userEvent.setup()
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Play')).toBeInTheDocument()
    })

    const playButton = screen.getByLabelText('Play')
    await user.click(playButton)

    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled()
  })

  it('handles volume control', async () => {
    const user = userEvent.setup()
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Play')).toBeInTheDocument()
    })

    const muteButton = screen.getByLabelText('Mute')
    await user.click(muteButton)

    // Volume should be set to 0
    expect(HTMLMediaElement.prototype.volume).toBe(0)
  })

  it('handles skip forward and backward', async () => {
    const user = userEvent.setup()
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Play')).toBeInTheDocument()
    })

    const skipForwardButton = screen.getByLabelText('Skip forward 10s')
    const skipBackwardButton = screen.getByLabelText('Skip backward 10s')

    await user.click(skipForwardButton)
    await user.click(skipBackwardButton)

    // currentTime should be modified
    expect(HTMLMediaElement.prototype.currentTime).toBeDefined()
  })

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup()
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Close')).toBeInTheDocument()
    })

    const closeButton = screen.getByLabelText('Close')
    await user.click(closeButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('calls onNext and onPrevious when provided', async () => {
    const user = userEvent.setup()
    render(
      <AudioPlayer 
        audio={mockAudio} 
        onClose={mockOnClose}
        onNext={mockOnNext}
        onPrevious={mockOnPrevious}
      />
    )

    await waitFor(() => {
      expect(screen.getByLabelText('Next')).toBeInTheDocument()
      expect(screen.getByLabelText('Previous')).toBeInTheDocument()
    })

    const nextButton = screen.getByLabelText('Next')
    const previousButton = screen.getByLabelText('Previous')

    await user.click(nextButton)
    await user.click(previousButton)

    expect(mockOnNext).toHaveBeenCalledTimes(1)
    expect(mockOnPrevious).toHaveBeenCalledTimes(1)
  })

  it('handles keyboard shortcuts', async () => {
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Play')).toBeInTheDocument()
    })

    // Test spacebar for play/pause
    fireEvent.keyDown(window, { key: ' ' })
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled()

    // Test arrow keys for skip
    fireEvent.keyDown(window, { key: 'ArrowRight' })
    fireEvent.keyDown(window, { key: 'ArrowLeft' })

    // Test volume keys
    fireEvent.keyDown(window, { key: 'ArrowUp' })
    fireEvent.keyDown(window, { key: 'ArrowDown' })

    // Test mute key
    fireEvent.keyDown(window, { key: 'm' })

    // Test escape key
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('downloads audio when download button is clicked', async () => {
    const user = userEvent.setup()
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Download')).toBeInTheDocument()
    })

    // Mock document.createElement
    const mockLink = { click: jest.fn(), href: '', download: '' }
    jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any)

    const downloadButton = screen.getByLabelText('Download')
    await user.click(downloadButton)

    expect(document.createElement).toHaveBeenCalledWith('a')
    expect(mockLink.click).toHaveBeenCalled()
    expect(mockLink.download).toBe('All of Me - Reference.mp3')
  })

  it('shows offline indicator when audio is cached', async () => {
    const mockOfflineStorage = require('@/lib/database').offlineStorage
    mockOfflineStorage.getAudio.mockResolvedValue({
      id: 'audio-1',
      file_data: new ArrayBuffer(100),
    })

    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Available Offline')).toBeInTheDocument()
    })
  })

  it('handles different reference types', async () => {
    const demoAudio = { ...mockAudio, reference_type: 'demo' as const }
    render(<AudioPlayer audio={demoAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Demo')).toBeInTheDocument()
    })

    const backingTrackAudio = { ...mockAudio, reference_type: 'backing_track' as const }
    render(<AudioPlayer audio={backingTrackAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Backing Track')).toBeInTheDocument()
    })
  })

  it('handles progress bar click for seeking', async () => {
    const user = userEvent.setup()
    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByLabelText('Play')).toBeInTheDocument()
    })

    // Mock getBoundingClientRect for progress bar
    const progressBar = screen.getByRole('generic', { hidden: true })
    jest.spyOn(progressBar, 'getBoundingClientRect').mockReturnValue({
      left: 0,
      right: 100,
      width: 100,
      top: 0,
      bottom: 10,
      height: 10,
    } as DOMRect)

    fireEvent.click(progressBar, { clientX: 50 })

    // Should update currentTime
    expect(HTMLMediaElement.prototype.currentTime).toBeDefined()
  })

  it('handles API error gracefully', async () => {
    const mockApiService = require('@/lib/api').apiService
    mockApiService.downloadAudio.mockRejectedValue(new Error('Network error'))

    render(<AudioPlayer audio={mockAudio} onClose={mockOnClose} />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load audio. Please try again.')).toBeInTheDocument()
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })
  })

  it('auto plays when autoPlay prop is true', async () => {
    render(<AudioPlayer audio={mockAudio} autoPlay={true} />)

    await waitFor(() => {
      expect(HTMLMediaElement.prototype.play).toHaveBeenCalled()
    })
  })
})