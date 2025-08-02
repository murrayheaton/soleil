'use client';

import { useEffect, useState } from 'react';

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string[]>([]);

  // Add debug logging
  const addDebug = (message: string) => {
    console.log(`[Login Debug] ${message}`);
    setDebugInfo(prev => [...prev, `${new Date().toISOString()}: ${message}`]);
  };

  useEffect(() => {
    addDebug('Login page mounted');
    
    // Check environment variables
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    
    addDebug(`Client ID: ${clientId ? 'Present' : 'Missing'}`);
    addDebug(`API URL: ${apiUrl || 'Missing'}`);

    // Check for auth callback parameters
    const urlParams = new URLSearchParams(window.location.search);
    const authParam = urlParams.get('auth');
    const messageParam = urlParams.get('message');
    
    if (authParam === 'success') {
      addDebug('Auth success detected, redirecting to profile');
      window.location.href = '/profile?auth=success';
    } else if (authParam === 'error') {
      addDebug(`Auth error: ${messageParam || 'Unknown error'}`);
      setError(decodeURIComponent(messageParam || 'Authentication failed'));
    } else if (authParam === 'unauthorized') {
      addDebug('User unauthorized - needs access request');
      setError('Your account is not authorized. Please contact an administrator to request access.');
    }
  }, []);

  const handleGoogleSignIn = async () => {
    try {
      addDebug('Sign in button clicked');
      setIsLoading(true);
      setError(null);

      // Get environment variables
      const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live/api';

      if (!clientId) {
        const errorMsg = 'Google OAuth Client ID is not configured';
        addDebug(`Error: ${errorMsg}`);
        setError(errorMsg);
        setIsLoading(false);
        return;
      }

      // Build OAuth URL
      const redirectUri = `${apiUrl}/api/auth/google/callback`;
      const scope = encodeURIComponent('https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile');
      const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${scope}&access_type=offline&prompt=consent`;

      addDebug(`Redirecting to: ${authUrl.substring(0, 50)}...`);
      
      // Add small delay to ensure state updates are visible
      setTimeout(() => {
        window.location.href = authUrl;
      }, 100);
      
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to initiate sign in';
      addDebug(`Exception: ${errorMsg}`);
      setError(errorMsg);
      setIsLoading(false);
    }
  };

  // Test button click handler
  const handleTestClick = () => {
    addDebug('Test button clicked - UI is responsive');
    alert('Button click works! Check console for debug info.');
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center" style={{backgroundColor: '#171717', paddingBottom: '25vh'}}>
      <div className="max-w-md w-full mx-4">
        <div className="rounded border p-8 shadow-xl" style={{backgroundColor: '#262626', borderColor: '#404040'}}>
          <div className="text-center mb-8">
            <h1 className="text-3xl font-black text-white mb-0">Sole Power <span className="font-thin">Live</span></h1>
            <p className="text-gray-400 text-sm font-light -mt-1">Assets access</p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded" style={{backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)'}}>
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <div className="text-center space-y-3">
            <button
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full bg-white hover:bg-gray-100 disabled:bg-gray-300 text-gray-800 font-semibold px-6 py-4 rounded transition-all transform hover:scale-105 active:scale-95 flex items-center justify-center shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
              style={{touchAction: 'manipulation'}}
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 mr-3 border-2 border-gray-800 border-t-transparent rounded-full animate-spin" />
                  Redirecting to Google...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Sign in with Google
                </>
              )}
            </button>

            {/* Debug test button */}
            <button
              onClick={handleTestClick}
              className="w-full bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm px-4 py-2 rounded transition-colors"
            >
              Test Button Responsiveness
            </button>
          </div>

          {/* Debug info in development */}
          {process.env.NODE_ENV === 'development' && debugInfo.length > 0 && (
            <div className="mt-6 p-3 rounded text-xs" style={{backgroundColor: '#1a1a1a', border: '1px solid #333'}}>
              <p className="text-gray-500 mb-2">Debug Log:</p>
              {debugInfo.slice(-5).map((info, idx) => (
                <p key={idx} className="text-gray-600 font-mono">{info}</p>
              ))}
            </div>
          )}
        </div>

        {/* Always visible debug hint */}
        <p className="text-center text-gray-600 text-xs mt-4">
          Check browser console for authentication debug information
        </p>
      </div>
    </div>
  );
}