'use client';

import React, { ReactNode, useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  HomeIcon,
  DocumentTextIcon,
  MusicalNoteIcon,
  ListBulletIcon,
  UserGroupIcon,
  Cog6ToothIcon,
  MoonIcon,
  SunIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  DocumentTextIcon as DocumentTextIconSolid,
  MusicalNoteIcon as MusicalNoteIconSolid,
  ListBulletIcon as ListBulletIconSolid,
  UserGroupIcon as UserGroupIconSolid,
  Cog6ToothIcon as Cog6ToothIconSolid,
} from '@heroicons/react/24/solid';

interface LayoutProps {
  children: ReactNode;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ForwardRefExoticComponent<React.SVGProps<SVGSVGElement>>;
  iconSolid: React.ForwardRefExoticComponent<React.SVGProps<SVGSVGElement>>;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: HomeIcon, iconSolid: HomeIconSolid },
  { name: 'Charts', href: '/charts', icon: DocumentTextIcon, iconSolid: DocumentTextIconSolid },
  { name: 'Audio', href: '/audio', icon: MusicalNoteIcon, iconSolid: MusicalNoteIconSolid },
  { name: 'Setlists', href: '/setlists', icon: ListBulletIcon, iconSolid: ListBulletIconSolid },
  { name: 'Band', href: '/band', icon: UserGroupIcon, iconSolid: UserGroupIconSolid },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon, iconSolid: Cog6ToothIconSolid },
];

export default function Layout({ children }: LayoutProps) {
  const pathname = usePathname();
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [scale, setScale] = useState(1);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [offlineMode, setOfflineMode] = useState(false);

  // Initialize theme, scale, and offline mode from localStorage or system preference
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const savedScale = localStorage.getItem('scale');
    const savedOffline = localStorage.getItem('offlineMode');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }
    if (savedScale) {
      setScale(parseFloat(savedScale));
      document.documentElement.style.setProperty('--scale', savedScale);
    }
    if (savedOffline === 'true') {
      setOfflineMode(true);
      setIsOnline(false);
    }
  }, []);

  // Update theme class and localStorage
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDarkMode]);

  // Update interface scale
  useEffect(() => {
    document.documentElement.style.setProperty('--scale', scale.toString());
    localStorage.setItem('scale', scale.toString());
  }, [scale]);

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

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <div className="min-h-screen flex flex-col" style={{backgroundColor: '#171717'}}>
      {/* Header Bar - Desktop */}
      <header className="hidden md:block border-b" style={{backgroundColor: '#262626', borderColor: '#404040'}}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-white">
                <span className="text-white">☀</span> <span className="font-black">SOLE</span><span className="font-serif italic font-semibold">il</span>
              </h1>
              {!isOnline && (
                <span className="ml-3 px-2 py-1 text-xs font-medium text-yellow-800 bg-yellow-100 rounded dark:text-yellow-200 dark:bg-yellow-900">
                  Offline
                </span>
              )}
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => {
                  // Clear any local storage
                  localStorage.clear();
                  // Redirect to home page to trigger re-authentication
                  window.location.href = '/';
                }}
                className="text-gray-400 hover:text-white text-sm transition-colors"
              >
                Sign Out
              </button>
            </div>

          </div>
        </div>
      </header>

      {/* Mobile Header */}
      <header className="md:hidden bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center h-16 px-4">
          <div className="flex items-center">
            <h1 className="text-lg font-semibold text-white">
              <span className="text-white">☀</span> <span className="font-black">SOLE</span><span className="font-serif italic font-semibold">il</span>
            </h1>
            {!isOnline && (
              <span className="ml-2 px-2 py-0.5 text-xs font-medium text-yellow-800 bg-yellow-100 rounded dark:text-yellow-200 dark:bg-yellow-900">
                Offline
              </span>
            )}
          </div>

          <div className="flex items-center">
            <button
              onClick={() => {
                // Clear any local storage
                localStorage.clear();
                // Redirect to home page to trigger re-authentication
                window.location.href = '/';
              }}
              className="text-gray-400 hover:text-white text-sm transition-colors"
            >
              Sign Out
            </button>
          </div>

        </div>

      </header>

      {/* Main Content */}
      <main className="flex-1 pb-20 md:pb-0" style={{backgroundColor: '#171717'}}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-8">
          {children}
        </div>
      </main>

    </div>
  );
}