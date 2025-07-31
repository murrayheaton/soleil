'use client';

import React, { ReactNode, useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import {
  HomeIcon,
  MusicalNoteIcon,
  CalendarDaysIcon,
  Cog6ToothIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';

interface LayoutProps {
  children: ReactNode;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ForwardRefExoticComponent<React.SVGProps<SVGSVGElement>>;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Repertoire', href: '/repertoire', icon: MusicalNoteIcon },
  { name: 'Upcoming Gigs', href: '/upcoming-gigs', icon: CalendarDaysIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
  { name: 'Profile', href: '/profile', icon: UserCircleIcon },
];

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname();
  // Short fade transition to keep animations smooth (~60fps)
  const variants = {
    initial: { opacity: 0 },
    animate: { opacity: 1, transition: { duration: 0.25 } },
    exit: { opacity: 0, transition: { duration: 0.25 } },
  };
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [offlineMode, setOfflineMode] = useState(false);

  // Initialize offline mode from localStorage
  useEffect(() => {
    const savedOffline = localStorage.getItem('offlineMode');
    if (savedOffline === 'true') {
      setOfflineMode(true);
      setIsOnline(false);
    }
  }, []);

  // Monitor online/offline status
  useEffect(() => {
    if (offlineMode) {
      setIsOnline(false);
      return;
    }

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    setIsOnline(navigator.onLine);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [offlineMode]);

  useEffect(() => {
    localStorage.setItem('offlineMode', offlineMode ? 'true' : 'false');
  }, [offlineMode]);

  // Handle sign out
  const handleSignOut = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live/api'}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      
      if (response.ok) {
        // Clear local storage and redirect to login
        localStorage.clear();
        window.location.href = '/';
      }
    } catch (error) {
      // Fallback: clear storage and redirect anyway
      localStorage.clear();
      window.location.href = '/';
    }
  };

  return (
    <div className="min-h-screen" style={{backgroundColor: '#ffffff'}}>
      {/* Navigation Header */}
      <nav className="nav-container">
        <div className="nav-content">
          {/* Logo - Now clickable */}
          <Link href="/dashboard" className="logo-link">
            <div className="logo-wrapper">
              <span className="text-white">☀</span> <span className="logo-sole">SOLE</span><span className="logo-il">il</span>
            </div>
          </Link>
          
          {/* Navigation Items - Desktop */}
          <ul className="nav-items hidden md:flex">
            {navigation.map(item => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link 
                    href={item.href}
                    className={`nav-link ${isActive ? 'active' : ''}`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
          
          {/* Sign Out Button */}
          <button 
            onClick={handleSignOut}
            className="sign-out-btn hidden md:block"
          >
            Sign Out
          </button>
          
          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden text-white hover:opacity-80 transition-opacity"
          >
            {isMobileMenuOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
        
        {/* Mobile Navigation Menu */}
        {isMobileMenuOpen && (
          <div className="mobile-nav">
            {navigation.map(item => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link 
                  key={item.href}
                  href={item.href}
                  className={`mobile-nav-link ${isActive ? 'active' : ''}`}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
            <button 
              onClick={handleSignOut}
              className="mobile-nav-link text-left w-full"
            >
              Sign Out
            </button>
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            variants={variants}
            initial="initial"
            animate="animate"
            exit="exit"
            style={{ willChange: 'opacity' }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}