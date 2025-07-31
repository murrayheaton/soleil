'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const PROFILE_LOAD_TIMEOUT = 10000; // 10 seconds
const MAX_RETRIES = 3;
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live';

export default function HomePage() {
    const router = useRouter();
    const [loadingState, setLoadingState] = useState<'loading' | 'error' | 'timeout' | 'success'>('loading');
    const [error, setError] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);

    const loadProfile = async () => {
        try {
            const response = await fetch(`${API_URL}/api/users/profile`, {
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Not authenticated, redirect to login
                    router.push('/login');
                    return;
                }
                throw new Error(`Profile load failed: ${response.status}`);
            }

            const profile = await response.json();
            
            if (profile && (profile.id || profile.email)) {
                setLoadingState('success');
                // Profile loaded successfully, redirect to dashboard
                router.push('/dashboard');
            } else {
                throw new Error('Invalid profile data received');
            }
        } catch (err) {
            console.error('Profile load error:', err);
            
            if (retryCount < MAX_RETRIES) {
                // Exponential backoff retry
                setTimeout(() => {
                    setRetryCount(prev => prev + 1);
                }, Math.pow(2, retryCount) * 1000);
            } else {
                setLoadingState('error');
                setError(err instanceof Error ? err.message : 'Failed to load profile');
            }
        }
    };

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            if (loadingState === 'loading') {
                setLoadingState('timeout');
                setError('Profile loading timed out. Please refresh the page.');
            }
        }, PROFILE_LOAD_TIMEOUT);

        loadProfile();

        return () => clearTimeout(timeoutId);
    }, [retryCount]);

    // Render states
    if (loadingState === 'loading') {
        return (
            <div className="loading-container" style={{
                backgroundColor: '#171717',
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column'
            }}>
                <div className="loading-spinner" style={{
                    width: '32px',
                    height: '32px',
                    border: '3px solid #404040',
                    borderTopColor: '#888',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    marginBottom: '1rem'
                }} />
                <p style={{color: '#888', fontSize: '1.1rem', marginBottom: '0.5rem'}}>Loading your profile...</p>
                {retryCount > 0 && <p style={{color: '#666', fontSize: '0.9rem'}}>Retry attempt {retryCount} of {MAX_RETRIES}</p>}
                
                <style jsx>{`
                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }
                `}</style>
            </div>
        );
    }

    if (loadingState === 'error' || loadingState === 'timeout') {
        return (
            <div className="error-container" style={{
                backgroundColor: '#171717',
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                padding: '2rem'
            }}>
                <h2 style={{color: '#ff6b6b', fontSize: '1.5rem', marginBottom: '1rem'}}>Unable to Load Profile</h2>
                <p style={{color: '#888', marginBottom: '2rem', textAlign: 'center', maxWidth: '400px'}}>{error}</p>
                <div className="error-actions" style={{display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center'}}>
                    <button 
                        onClick={() => window.location.reload()}
                        style={{
                            padding: '0.75rem 1.5rem',
                            backgroundColor: '#4CAF50',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '1rem'
                        }}
                    >
                        Refresh Page
                    </button>
                    <button 
                        onClick={() => router.push('/login')}
                        style={{
                            padding: '0.75rem 1.5rem',
                            backgroundColor: '#666',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '1rem'
                        }}
                    >
                        Back to Login
                    </button>
                </div>
            </div>
        );
    }

    return null; // Success state redirects to dashboard
}
