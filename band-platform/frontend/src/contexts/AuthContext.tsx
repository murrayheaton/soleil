'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  profile_complete: boolean;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  // Check for existing session on mount
  const checkAuth = useCallback(async () => {
    console.log('[AuthContext] Checking authentication status...');
    setLoading(true);
    setError(null);

    try {
      // First check if we have a session cookie
      const sessionCookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('soleil_session='));
      
      if (!sessionCookie) {
        console.log('[AuthContext] No session cookie found');
        setIsAuthenticated(false);
        setUser(null);
        setLoading(false);
        return;
      }

      // Validate session with backend
      const response = await fetch(`${API_URL}/api/auth/validate`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[AuthContext] Session valid:', data);
        
        setUser(data.user);
        setIsAuthenticated(true);
        
        // Set the auth cookie that middleware expects
        document.cookie = `soleil_auth=true; path=/; max-age=86400; SameSite=Lax`;
        
        // Store auth state in localStorage for persistence
        localStorage.setItem('soleil_auth', JSON.stringify({
          user: data.user,
          timestamp: Date.now()
        }));
      } else if (response.status === 401) {
        console.log('[AuthContext] Session invalid or expired');
        // Try to refresh token
        await refreshSession();
      } else {
        console.error('[AuthContext] Auth check failed:', response.status);
        setIsAuthenticated(false);
        setUser(null);
        clearAuthData();
      }
    } catch (err) {
      console.error('[AuthContext] Auth check error:', err);
      setError('Failed to check authentication status');
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Refresh session with refresh token
  const refreshSession = useCallback(async () => {
    console.log('[AuthContext] Attempting to refresh session...');
    
    try {
      const response = await fetch(`${API_URL}/api/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('[AuthContext] Session refreshed successfully');
        
        setUser(data.user);
        setIsAuthenticated(true);
        
        // Update stored auth state
        localStorage.setItem('soleil_auth', JSON.stringify({
          user: data.user,
          timestamp: Date.now()
        }));
        
        // Set new session cookie if provided
        if (data.session_token) {
          document.cookie = `soleil_session=${data.session_token}; path=/; max-age=86400; SameSite=Lax`;
        }
      } else {
        console.log('[AuthContext] Session refresh failed');
        setIsAuthenticated(false);
        setUser(null);
        clearAuthData();
      }
    } catch (err) {
      console.error('[AuthContext] Session refresh error:', err);
      setIsAuthenticated(false);
      setUser(null);
      clearAuthData();
    }
  }, []);

  // Initialize OAuth login
  const login = useCallback(() => {
    console.log('[AuthContext] Initiating OAuth login...');
    // Store current path to redirect back after login
    const currentPath = window.location.pathname;
    if (currentPath !== '/login' && currentPath !== '/') {
      sessionStorage.setItem('soleil_redirect', currentPath);
    }
    
    // Redirect to backend OAuth endpoint
    window.location.href = `${API_URL}/api/auth/google`;
  }, []);

  // Logout user
  const logout = useCallback(async () => {
    console.log('[AuthContext] Logging out...');
    setLoading(true);
    
    try {
      await fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('[AuthContext] Logout error:', err);
    } finally {
      // Clear all auth data regardless of API response
      clearAuthData();
      setUser(null);
      setIsAuthenticated(false);
      setLoading(false);
      router.push('/login');
    }
  }, [router]);

  // Clear all auth data
  const clearAuthData = () => {
    console.log('[AuthContext] Clearing auth data...');
    // Clear cookies
    document.cookie = 'soleil_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'soleil_refresh=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    document.cookie = 'soleil_profile_complete=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    
    // Clear localStorage
    localStorage.removeItem('soleil_auth');
    sessionStorage.removeItem('soleil_redirect');
  };

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Check auth on mount and when window regains focus
  useEffect(() => {
    checkAuth();

    // Re-check auth when window regains focus
    const handleFocus = () => {
      console.log('[AuthContext] Window focused, checking auth...');
      checkAuth();
    };

    // Re-check auth when coming back online
    const handleOnline = () => {
      console.log('[AuthContext] Back online, checking auth...');
      checkAuth();
    };

    window.addEventListener('focus', handleFocus);
    window.addEventListener('online', handleOnline);

    // Set up token refresh interval (every 10 minutes)
    const refreshInterval = setInterval(() => {
      if (isAuthenticated) {
        refreshSession();
      }
    }, 10 * 60 * 1000); // 10 minutes

    return () => {
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('online', handleOnline);
      clearInterval(refreshInterval);
    };
  }, []);

  // Handle OAuth callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const authSuccess = urlParams.get('auth') === 'success';
    const authError = urlParams.get('error');
    
    if (authSuccess) {
      console.log('[AuthContext] OAuth callback success detected');
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
      
      // Check for redirect
      const redirect = sessionStorage.getItem('soleil_redirect');
      if (redirect) {
        sessionStorage.removeItem('soleil_redirect');
        router.push(redirect);
      } else {
        checkAuth();
      }
    } else if (authError) {
      console.error('[AuthContext] OAuth error:', authError);
      setError(`Authentication failed: ${authError}`);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [router, checkAuth]);

  const value: AuthContextType = {
    user,
    loading,
    error,
    isAuthenticated,
    login,
    logout,
    refreshSession,
    checkAuth,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// HOC for protected routes
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
  return function ProtectedComponent(props: P) {
    const { isAuthenticated, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
      if (!loading && !isAuthenticated) {
        router.push('/login');
      }
    }, [isAuthenticated, loading, router]);

    if (loading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return null;
    }

    return <Component {...props} />;
  };
}