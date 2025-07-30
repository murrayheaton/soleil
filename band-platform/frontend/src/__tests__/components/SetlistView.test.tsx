import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SetlistView from '@/components/SetlistView'
import type { Setlist, SetlistItem } from '@/lib/api'

// Mock dependencies
jest.mock('@/lib/websocket')
jest.mock('@/lib/api')

const mockSetlistItems: SetlistItem[] = [
  {
    title: 'All of Me',
    key: 'Bb',
    order_index: 1,
    estimated_duration: 4,
    notes: 'Medium swing',
  },
  {
    title: 'Take Five',
    key: 'Eb',
    order_index: 2,
    estimated_duration: 6,
    notes: '5/4 time signature',
  },
]

const mockSetlist: Setlist = {
  id: 'setlist-1',
  name: 'Jazz Standards Night',
  performance_date: '2023-12-31T20:00:00Z',
  venue: 'Blue Note',
  notes: 'Special New Year show',
  items: mockSetlistItems,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  band_id: 'band-1',
}

describe('SetlistView', () => {
  const mockOnUpdate = jest.fn()
  const mockOnDelete = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    
    // Mock API service
    const mockApiService = require('@/lib/api').apiService
    mockApiService.updateSetlist = jest.fn().mockResolvedValue(mockSetlist)
    mockApiService.getSetlist = jest.fn().mockResolvedValue(mockSetlist)
    
    // Mock WebSocket
    const mockUseWebSocket = require('@/lib/websocket').useWebSocket
    mockUseWebSocket.mockReturnValue({
      subscribe: jest.fn(() => jest.fn()),
      unsubscribe: jest.fn(),
      isConnected: true,
    })
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('renders setlist information', () => {
    render(<SetlistView setlist={mockSetlist} />)

    expect(screen.getByText('Jazz Standards Night')).toBeInTheDocument()
    expect(screen.getByText(/12\/31\/2023.*Blue Note/)).toBeInTheDocument()
    expect(screen.getByText('Special New Year show')).toBeInTheDocument()
    expect(screen.getByText('2 songs')).toBeInTheDocument()
    expect(screen.getByText('10 minutes')).toBeInTheDocument()
  })

  it('renders setlist items in order', () => {
    render(<SetlistView setlist={mockSetlist} />)

    const items = screen.getAllByText(/^\d+\./)
    expect(items).toHaveLength(2)
    expect(screen.getByText('1.')).toBeInTheDocument()
    expect(screen.getByText('2.')).toBeInTheDocument()
    expect(screen.getByText('All of Me')).toBeInTheDocument()
    expect(screen.getByText('Take Five')).toBeInTheDocument()
  })

  it('displays item details correctly', () => {
    render(<SetlistView setlist={mockSetlist} />)

    expect(screen.getByText('Bb')).toBeInTheDocument()
    expect(screen.getByText('Eb')).toBeInTheDocument()
    expect(screen.getByText('4m')).toBeInTheDocument()
    expect(screen.getByText('6m')).toBeInTheDocument()
    expect(screen.getByText('Medium swing')).toBeInTheDocument()
    expect(screen.getByText('5/4 time signature')).toBeInTheDocument()
  })

  it('shows edit button when isEditable is true', () => {
    render(<SetlistView setlist={mockSetlist} isEditable={true} />)

    expect(screen.getByText('Edit')).toBeInTheDocument()
  })

  it('does not show edit button when isEditable is false', () => {
    render(<SetlistView setlist={mockSetlist} isEditable={false} />)

    expect(screen.queryByText('Edit')).not.toBeInTheDocument()
  })

  it('enters edit mode when edit button is clicked', async () => {
    const user = userEvent.setup()
    render(<SetlistView setlist={mockSetlist} isEditable={true} />)

    const editButton = screen.getByText('Edit')
    await user.click(editButton)

    expect(screen.getByText('Done')).toBeInTheDocument()
    expect(screen.getByText('Add song')).toBeInTheDocument()
  })

  it('shows drag handles and edit buttons in edit mode', async () => {
    const user = userEvent.setup()
    render(<SetlistView setlist={mockSetlist} isEditable={true} />)

    const editButton = screen.getByText('Edit')
    await user.click(editButton)

    // Should show drag handles
    const dragHandles = screen.getAllByRole('button', { hidden: true })
    expect(dragHandles.length).toBeGreaterThan(2)
  })

  it('allows adding new items in edit mode', async () => {
    const user = userEvent.setup()
    render(<SetlistView setlist={mockSetlist} isEditable={true} onUpdate={mockOnUpdate} />)

    // Enter edit mode
    const editButton = screen.getByText('Edit')
    await user.click(editButton)

    // Click add song
    const addButton = screen.getByText('Add song')
    await user.click(addButton)

    // Fill in form
    const titleInput = screen.getByPlaceholderText('Song title')
    const keyInput = screen.getByPlaceholderText('Key')
    const durationInput = screen.getByPlaceholderText('Minutes')
    const notesInput = screen.getByPlaceholderText('Notes')

    await user.type(titleInput, 'Blue Moon')
    await user.type(keyInput, 'C')
    await user.type(durationInput, '5')
    await user.type(notesInput, 'Ballad tempo')

    // Submit
    const addSongButton = screen.getByText('Add Song')
    await user.click(addSongButton)

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalled()
    })
  })

  it('allows editing existing items', async () => {
    const user = userEvent.setup()
    render(<SetlistView setlist={mockSetlist} isEditable={true} onUpdate={mockOnUpdate} />)

    // Enter edit mode
    const editButton = screen.getByText('Edit')
    await user.click(editButton)

    // Click edit on first item
    const editItemButtons = screen.getAllByLabelText('Edit item')
    await user.click(editItemButtons[0])

    // Should show edit form
    const titleInput = screen.getByDisplayValue('All of Me')
    expect(titleInput).toBeInTheDocument()

    // Edit title
    await user.clear(titleInput)
    await user.type(titleInput, 'All of Me (Updated)')

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalled()
    })
  })

  it('allows deleting items with confirmation', async () => {
    const user = userEvent.setup()
    
    // Mock window.confirm
    const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(true)
    
    render(<SetlistView setlist={mockSetlist} isEditable={true} onUpdate={mockOnUpdate} />)

    // Enter edit mode
    const editButton = screen.getByText('Edit')
    await user.click(editButton)

    // Click delete on first item
    const deleteButtons = screen.getAllByLabelText('Delete item')
    await user.click(deleteButtons[0])

    expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to remove this item?')
    
    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalled()
    })

    mockConfirm.mockRestore()
  })

  it('cancels delete when user declines confirmation', async () => {
    const user = userEvent.setup()
    
    // Mock window.confirm to return false
    const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(false)
    
    render(<SetlistView setlist={mockSetlist} isEditable={true} onUpdate={mockOnUpdate} />)

    // Enter edit mode
    const editButton = screen.getByText('Edit')
    await user.click(editButton)

    // Click delete on first item
    const deleteButtons = screen.getAllByLabelText('Delete item')
    await user.click(deleteButtons[0])

    expect(mockConfirm).toHaveBeenCalled()
    expect(mockOnUpdate).not.toHaveBeenCalled()

    mockConfirm.mockRestore()
  })

  it('calls onDelete when delete setlist button is clicked', async () => {
    const user = userEvent.setup()
    render(<SetlistView setlist={mockSetlist} isEditable={true} onDelete={mockOnDelete} />)

    const deleteButton = screen.getByLabelText('Delete setlist')
    await user.click(deleteButton)

    expect(mockOnDelete).toHaveBeenCalledTimes(1)
  })

  it('handles real-time updates via WebSocket', async () => {
    const mockUseWebSocket = require('@/lib/websocket').useWebSocket
    const mockSubscribe = jest.fn()
    
    mockUseWebSocket.mockReturnValue({
      subscribe: mockSubscribe,
      unsubscribe: jest.fn(),
      isConnected: true,
    })

    render(<SetlistView setlist={mockSetlist} onUpdate={mockOnUpdate} />)

    expect(mockSubscribe).toHaveBeenCalledWith('setlist_updated', expect.any(Function))
  })

  it('validates required fields when adding items', async () => {
    const user = userEvent.setup()
    render(<SetlistView setlist={mockSetlist} isEditable={true} />)

    // Enter edit mode
    const editButton = screen.getByText('Edit')
    await user.click(editButton)

    // Click add song
    const addButton = screen.getByText('Add song')
    await user.click(addButton)

    // Try to submit without title
    const addSongButton = screen.getByText('Add Song')
    expect(addSongButton).toBeDisabled()

    // Add title
    const titleInput = screen.getByPlaceholderText('Song title')
    await user.type(titleInput, 'Test Song')

    // Button should now be enabled
    expect(addSongButton).not.toBeDisabled()
  })

  it('cancels add item form', async () => {
    const user = userEvent.setup()
    render(<SetlistView setlist={mockSetlist} isEditable={true} />)

    // Enter edit mode
    const editButton = screen.getByText('Edit')
    await user.click(editButton)

    // Click add song
    const addButton = screen.getByText('Add song')
    await user.click(addButton)

    // Fill some data
    const titleInput = screen.getByPlaceholderText('Song title')
    await user.type(titleInput, 'Test Song')

    // Cancel
    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)

    // Should return to add button state
    expect(screen.getByText('Add song')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Song title')).not.toBeInTheDocument()
  })

  it('calculates total duration correctly', () => {
    render(<SetlistView setlist={mockSetlist} />)

    // Total should be 4 + 6 = 10 minutes
    expect(screen.getByText('10 minutes')).toBeInTheDocument()
  })

  it('handles setlist without performance date gracefully', () => {
    const setlistWithoutDate = { ...mockSetlist, performance_date: null }
    render(<SetlistView setlist={setlistWithoutDate} />)

    expect(screen.getByText('Jazz Standards Night')).toBeInTheDocument()
    // Should not crash without performance date
  })
})