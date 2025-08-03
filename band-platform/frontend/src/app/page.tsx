'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuthAndRedirect = async () => {
      try {
        const response = await fetch('/api/user/profile', {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.status === 401) {
          // User not authenticated - redirect to login
          router.replace('/login');
          return;
        }

        if (response.ok) {
          // User authenticated - redirect to dashboard
          router.replace('/dashboard');
          return;
        }

        // Other errors - redirect to login
        console.error('Profile check failed:', response.status);
        router.replace('/login');
      } catch (error) {
        console.error('Auth check error:', error);
        router.replace('/login');
      } finally {
        setIsChecking(false);
      }
    };

    checkAuthAndRedirect();
  }, [router]);

  if (isChecking) {
    return (
      <div style={{
        backgroundColor: '#171717',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column'
      }}>
        <div style={{
          width: '32px',
          height: '32px',
          border: '3px solid #404040',
          borderTopColor: '#888',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '1rem'
        }} />
        <p style={{color: '#888', fontSize: '1.1rem'}}>Checking authentication...</p>
        
        <style jsx>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // This should rarely be seen as redirects happen quickly
  return null;
}