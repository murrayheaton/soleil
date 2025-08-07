'use client';

import { useEffect, useState } from 'react';
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';
import { moduleRegistry } from '@/config/dashboard-modules';
import './dashboard.css';

interface UserProfile {
  email: string;
  name: string;
  instrument: string;
  transposition: string;
  display_name: string;
}

export default function DashboardPage() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live'}/api/user/profile`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (response.ok) {
          const profile = await response.json();
          
          // Profile is returned directly now, not wrapped in status/profile
          if (profile && (profile.id || profile.email)) {
            setUser(profile);
          }
        }
      } catch {
        // Failed to load profile - using default
        // For now, use a default user to keep the UI functional
        setUser({
          email: 'user@example.com',
          name: 'Band Member',
          instrument: 'guitar',
          transposition: 'C',
          display_name: 'Band Member'
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, []);

  if (isLoading) {
    return (
      <div className="dashboard-loading" style={{
        backgroundColor: '#171717', 
        minHeight: '400px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column'
      }}>
        <div className="loading-spinner" style={{
          width: '24px',
          height: '24px',
          border: '2px solid #404040',
          borderTopColor: '#666',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
          marginBottom: '0.5rem'
        }} />
        <p style={{color: '#666'}}>Loading dashboard...</p>

        <style jsx>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Default user if none loaded
  const displayUser = user || {
    name: 'Band Member',
    email: 'user@example.com',
    instrument: 'guitar',
    transposition: 'C',
    display_name: 'Band Member'
  };

  return (
    <div className="dashboard-container" style={{backgroundColor: '#171717', color: 'white', padding: '2rem', maxWidth: '1400px', margin: '0 auto'}}>
      <header className="dashboard-header" style={{marginBottom: '2rem'}}>
        <h1 style={{fontSize: '2rem', marginBottom: '0.5rem', fontWeight: 'bold'}}>
          Welcome back, {displayUser.name}!
        </h1>
        <p className="dashboard-date" style={{color: '#666', fontSize: '1rem'}}>
          {new Date().toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </p>
      </header>

      <DashboardGrid modules={moduleRegistry} userId={displayUser.email} />
    </div>
  );
}