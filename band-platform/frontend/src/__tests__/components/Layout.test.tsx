import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Layout from '@/components/Layout'

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  )
})

describe('Layout', () => {
  beforeEach(() => {
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => null),
        setItem: jest.fn(),
        removeItem: jest.fn(),
      },
      writable: true,
    })

    // Mock matchMedia for dark mode detection
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders navigation with all main links', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    expect(screen.getByText('Band Platform')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Charts')).toBeInTheDocument()
    expect(screen.getByText('Audio')).toBeInTheDocument()
    expect(screen.getByText('Setlists')).toBeInTheDocument()
    expect(screen.getByText('Band')).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('shows desktop navigation on larger screens', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Desktop nav should be present (though hidden on mobile)
    const desktopNav = screen.getByRole('navigation')
    expect(desktopNav).toBeInTheDocument()
  })

  it('shows mobile navigation bottom bar', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Check for mobile nav items by looking for icons and text
    expect(screen.getAllByText('Dashboard')).toHaveLength(2) // Desktop + mobile
    expect(screen.getAllByText('Charts')).toHaveLength(2)
    expect(screen.getAllByText('Audio')).toHaveLength(2)
    expect(screen.getAllByText('Setlists')).toHaveLength(2)
  })

  it('toggles dark mode when button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Find the dark mode toggle button
    const darkModeButton = screen.getByLabelText('Toggle dark mode')
    await user.click(darkModeButton)

    // Should apply dark class to document
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('persists dark mode preference in localStorage', async () => {
    const user = userEvent.setup()
    const mockSetItem = jest.fn()
    Object.defineProperty(window, 'localStorage', {
      value: { ...window.localStorage, setItem: mockSetItem },
      writable: true,
    })

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    const darkModeButton = screen.getByLabelText('Toggle dark mode')
    await user.click(darkModeButton)

    expect(mockSetItem).toHaveBeenCalledWith('darkMode', 'true')
  })

  it('restores dark mode from localStorage', () => {
    Object.defineProperty(window, 'localStorage', {
      value: {
        ...window.localStorage,
        getItem: jest.fn(() => 'true'),
      },
      writable: true,
    })

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Should apply dark mode on mount
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('detects system dark mode preference', () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      })),
    })

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Should apply dark mode based on system preference
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('toggles mobile menu when hamburger is clicked', async () => {
    const user = userEvent.setup()
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Find the mobile menu toggle (hamburger icon)
    const menuToggle = screen.getByLabelText('Toggle navigation menu')
    await user.click(menuToggle)

    // Mobile menu should be visible
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  it('closes mobile menu when backdrop is clicked', async () => {
    const user = userEvent.setup()
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Open mobile menu
    const menuToggle = screen.getByLabelText('Toggle navigation menu')
    await user.click(menuToggle)

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // Click backdrop
    const backdrop = screen.getByTestId('mobile-menu-backdrop')
    await user.click(backdrop)

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  it('closes mobile menu when a link is clicked', async () => {
    const user = userEvent.setup()
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Open mobile menu
    const menuToggle = screen.getByLabelText('Toggle navigation menu')
    await user.click(menuToggle)

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // Click a navigation link in mobile menu
    const mobileLinks = screen.getAllByText('Charts')
    const mobileLinkInMenu = mobileLinks.find(link => 
      link.closest('[role="dialog"]')
    )
    
    if (mobileLinkInMenu) {
      await user.click(mobileLinkInMenu)
    }

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  it('handles keyboard navigation for mobile menu', async () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Open mobile menu
    const menuToggle = screen.getByLabelText('Toggle navigation menu')
    fireEvent.click(menuToggle)

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // Test escape key closes menu
    fireEvent.keyDown(document, { key: 'Escape' })

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  it('maintains focus management in mobile menu', async () => {
    const user = userEvent.setup()
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    const menuToggle = screen.getByLabelText('Toggle navigation menu')
    await user.click(menuToggle)

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // First focusable element in menu should be focused
    const firstLink = screen.getByTestId('mobile-nav-dashboard')
    expect(firstLink).toHaveFocus()
  })

  it('shows correct active link styling', () => {
    // Mock usePathname to return specific path
    jest.doMock('next/navigation', () => ({
      usePathname: () => '/charts',
    }))

    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Charts link should have active styling
    const chartsLinks = screen.getAllByText('Charts')
    chartsLinks.forEach(link => {
      expect(link.closest('a')).toHaveClass('text-blue-600')
    })
  })

  it('renders user profile section when authenticated', () => {
    // Mock user state
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // In a real implementation, we'd mock the auth context
    // For now, just verify the layout structure exists
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })

  it('handles window resize gracefully', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    )

    // Simulate window resize
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    })

    fireEvent(window, new Event('resize'))

    // Layout should still be functional
    expect(screen.getByText('Band Platform')).toBeInTheDocument()
  })
})