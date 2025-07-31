'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
  const router = useRouter();
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
        
        if (!response.ok) {
          if (response.status === 401) {
            router.push('/login');
            return;
          }
          throw new Error(`Profile fetch failed: ${response.status}`);
        }
        
        const profile = await response.json();
        
        // Profile is returned directly now, not wrapped in status/profile
        if (profile && (profile.id || profile.email)) {
          setUser(profile);
        } else {
          throw new Error('Invalid profile data received');
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, [router]);

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

  if (!user) {
    return null; // Redirecting to login
  }

  return (
    <div className="dashboard-container" style={{backgroundColor: '#171717', color: 'white', padding: '2rem', maxWidth: '1400px', margin: '0 auto'}}>
      <header className="dashboard-header" style={{marginBottom: '2rem'}}>
        <h1 style={{fontSize: '2rem', marginBottom: '0.5rem', fontWeight: 'bold'}}>
          Welcome back, {user.name}!
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
      
      <DashboardGrid 
        modules={moduleRegistry}
        userId={user.email}
      />

      <style jsx>{`
        @media (max-width: 768px) {
          .dashboard-container {
            padding: 1rem !important;
          }
          
          .dashboard-header h1 {
            font-size: 1.5rem !important;
          }
        }
      `}</style>
    </div>
  );
}