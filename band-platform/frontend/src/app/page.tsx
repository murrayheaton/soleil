'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Simple redirect to dashboard - let middleware handle auth
    router.replace('/dashboard');
  }, [router]);

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
      
      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}