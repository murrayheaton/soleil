'use client';

import { useState, useEffect } from 'react';
import { 
  DocumentTextIcon, 
  MusicalNoteIcon,
  ArrowDownTrayIcon,
  PlayIcon,
  PauseIcon,
  EyeIcon,
  UserCircleIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import Link from 'next/link';

interface ChartFile {
  id: string;
  name: string;
  type: string;
  link: string;
  is_placeholder?: boolean;
}

interface AudioFile {
  id: string;
  name: string;
  link: string;
  is_placeholder?: boolean;
}

interface Song {
  song_title: string;
  charts: ChartFile[];
  audio: AudioFile[];
  total_files: number;
}

interface FilesResponse {
  status: string;
  instrument: string;
  transposition: string;
  songs: Song[];
  total_songs: number;
  message: string;
}

interface UserProfile {
  email: string;
  name: string;
  instrument: string;
  transposition: string;
  display_name: string;
}

const PROFILE_LOAD_TIMEOUT = 10000; // 10 seconds
const MAX_RETRIES = 3;
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live/api';

export default function BandPlatform() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authStatus, setAuthStatus] = useState<'checking' | 'needed' | 'success' | 'error'>('checking');
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editedProfile, setEditedProfile] = useState<UserProfile | null>(null);
  const [loadingState, setLoadingState] = useState<'loading' | 'error' | 'timeout' | 'success'>('loading');
  const [retryCount, setRetryCount] = useState(0);

  const loadProfile = async () => {
    try {
      const response = await fetch(`${API_URL}/users/profile`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Not authenticated, redirect to login
          setAuthStatus('needed');
          setError('Please connect your Google Drive to access your profile.');
          return;
        }
        throw new Error(`Profile load failed: ${response.status}`);
      }

      const profileData = await response.json();
      
      if (profileData && (profileData.email || profileData.id)) {
        setProfile(profileData);
        setLoadingState('success');
        setAuthStatus('success');
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

  const fetchProfile = async () => {
    setLoading(true);
    setError(null);
    setLoadingState('loading');
    setRetryCount(0);
    
    // Set up timeout
    const timeoutId = setTimeout(() => {
      if (loadingState === 'loading') {
        setLoadingState('timeout');
        setError('Profile loading timed out. Please refresh the page.');
        setLoading(false);
      }
    }, PROFILE_LOAD_TIMEOUT);

    try {
      await loadProfile();
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check URL parameters for auth status
    const urlParams = new URLSearchParams(window.location.search);
    const authParam = urlParams.get('auth');
    
    if (authParam === 'success') {
      setAuthStatus('success');
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
      // Fetch profile after successful auth
      fetchProfile();
    } else if (authParam === 'error') {
      setAuthStatus('error');
      setError('Authentication failed. Please try again.');
      window.history.replaceState({}, document.title, window.location.pathname);
    } else {
      // Check if we need authentication by trying to fetch profile
      fetchProfile();
    }
  }, []);

  // Retry effect
  useEffect(() => {
    if (retryCount > 0 && retryCount <= MAX_RETRIES) {
      loadProfile();
    }
  }, [retryCount]);

  const updateProfile = async (updatedProfile: Partial<UserProfile>) => {
    try {
      const response = await fetch(`${API_URL}/user/profile`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedProfile),
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        setProfile(data.profile);
        setIsEditingProfile(false);
        setEditedProfile(null);
      } else {
        setError(data.message || 'Failed to update profile');
      }
    } catch (error) {
      setError('Failed to update profile. Please try again.');
    }
  };

  const startEditingProfile = () => {
    if (profile) {
      setEditedProfile({...profile});
      setIsEditingProfile(true);
    }
  };

  const cancelEditingProfile = () => {
    setEditedProfile(null);
    setIsEditingProfile(false);
  };

  const handleGoogleSignIn = () => {
    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'https://solepower.live';
    
    if (!clientId) {
      console.error('Google OAuth client ID is not set');
      return;
    }

    const redirectUri = `${backendUrl}/api/auth/google/callback`;
    const authUrl =
      `https://accounts.google.com/o/oauth2/auth?client_id=${clientId}` +
      `&response_type=code&scope=https://www.googleapis.com/auth/drive.readonly` +
      ` https://www.googleapis.com/auth/userinfo.email&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&access_type=offline&prompt=consent`;
    window.location.href = authUrl;
  };

  // Render loading states
  if (loadingState === 'loading' || loading) {
    return (
      <div className="loading-container min-h-screen text-white p-8" style={{backgroundColor: '#171717'}}>
        <div className="max-w-4xl mx-auto">
          <div className="text-center">
            <div className="loading-spinner animate-spin rounded-full h-12 w-12 border-b-2 border-gray-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading your profile...</p>
            {retryCount > 0 && <p className="retry-text text-gray-500 text-sm mt-2">Retry attempt {retryCount} of {MAX_RETRIES}</p>}
          </div>
        </div>
      </div>
    );
  }

  if (loadingState === 'error' || loadingState === 'timeout') {
    return (
      <div className="error-container min-h-screen text-white p-8" style={{backgroundColor: '#171717'}}>
        <div className="max-w-4xl mx-auto">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Unable to Load Profile</h2>
            <p className="error-message text-gray-400 mb-6">{error}</p>
            <div className="error-actions space-x-4">
              <button 
                onClick={() => window.location.reload()}
                className="text-white px-6 py-3 rounded transition-colors hover:opacity-80"
                style={{backgroundColor: '#000000'}}
              >
                Refresh Page
              </button>
              <button 
                onClick={() => {
                  setAuthStatus('needed');
                  setLoadingState('loading');
                  setError(null);
                }}
                className="text-white px-6 py-3 rounded transition-colors hover:opacity-80"
                style={{backgroundColor: '#525252'}}
              >
                Back to Login
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show login screen when authentication is needed
  if (authStatus === 'needed' || authStatus === 'error' || (error && error.includes('Not authenticated'))) {
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{backgroundColor: '#171717', paddingBottom: '25vh'}}>
        <div className="max-w-md w-full mx-4">
          <div className="rounded border p-8 shadow-xl" style={{backgroundColor: '#262626', borderColor: '#404040'}}>
            <div className="text-center mb-8">
              <h1 className="text-3xl font-black text-white mb-0">Sole Power <span className="font-thin">Live</span></h1>
              <p className="text-gray-400 text-sm font-light -mt-1">Assets access</p>
            </div>
            
            <div className="text-center">
              <button
                onClick={handleGoogleSignIn}
                className="w-full bg-white hover:bg-gray-100 text-gray-800 font-semibold px-6 py-4 rounded transition-colors flex items-center justify-center shadow-lg"
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Sign in with Google
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen text-white" style={{backgroundColor: '#171717'}}>
      {/* Header */}
      <div className="border-b px-8 py-6" style={{backgroundColor: '#171717', borderColor: '#404040'}}>
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-black text-white mb-0">Sole Power <span className="font-thin">Live</span></h1>
              <p className="text-gray-400 text-sm font-light -mt-1">Assets access</p>
            </div>
            
            {/* Navigation */}
            <div className="flex items-center space-x-4">
              <Link 
                href="/repertoire" 
                className="text-white px-4 py-2 rounded transition-colors inline-flex items-center hover:opacity-80"
                style={{backgroundColor: '#000000'}}
              >
                <MusicalNoteIcon className="w-4 h-4 mr-2" />
                View Repertoire
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Profile Content */}
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
          {/* Profile Card */}
          <div className="rounded border overflow-hidden" style={{backgroundColor: '#262626', borderColor: '#404040'}}>
            {/* Profile Header */}
            <div className="px-6 py-4 border-b" style={{backgroundColor: '#404040', borderColor: '#525252'}}>
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <UserCircleIcon className="w-12 h-12 text-white mr-4" />
                  <div>
                    <h2 className="text-2xl font-black text-white">{profile?.name || 'Loading...'}</h2>
                    <p className="text-gray-400 text-sm">{profile?.email}</p>
                  </div>
                </div>
                
                {!isEditingProfile && (
                  <button
                    onClick={startEditingProfile}
                    className="text-white px-4 py-2 rounded transition-colors inline-flex items-center hover:opacity-80"
                style={{backgroundColor: '#000000'}}
                  >
                    <Cog6ToothIcon className="w-4 h-4 mr-2" />
                    Edit Profile
                  </button>
                )}
              </div>
            </div>
            
            {/* Profile Content */}
            <div className="p-6">
              {isEditingProfile && editedProfile ? (
                /* Edit Profile Form */
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Edit Profile</h3>
                  
                  {/* Name Field */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Name</label>
                    <input
                      type="text"
                      value={editedProfile.name}
                      onChange={(e) => setEditedProfile({...editedProfile, name: e.target.value})}
                      className="w-full rounded px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-gray-400"
                      style={{backgroundColor: '#404040', border: '1px solid #525252'}}
                    />
                  </div>
                  
                  {/* Instrument Field */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">Instrument</label>
                    <select
                      value={editedProfile.instrument}
                      onChange={(e) => {
                        const instrumentMap: {[key: string]: {transposition: string, display_name: string}} = {
                          'trumpet': {transposition: 'B♭', display_name: 'Trumpet'},
                          'alto_sax': {transposition: 'E♭', display_name: 'Alto Sax'},
                          'tenor_sax': {transposition: 'B♭', display_name: 'Tenor Sax'},
                          'bari_sax': {transposition: 'E♭', display_name: 'Bari Sax'},
                          'violin': {transposition: 'Concert', display_name: 'Violin'},
                          'cello': {transposition: 'Concert', display_name: 'Cello'},
                          'trombone': {transposition: 'Bass Clef', display_name: 'Trombone'},
                          'guitar': {transposition: 'Chord Charts', display_name: 'Guitar'},
                          'bass': {transposition: 'Chord Charts', display_name: 'Bass'},
                          'keys': {transposition: 'Chord Charts', display_name: 'Keys'},
                          'drums': {transposition: 'Chord Charts', display_name: 'Drums'},
                          'vocals': {transposition: 'Lyrics', display_name: 'Vocals'}
                        };
                        const selected = instrumentMap[e.target.value];
                        setEditedProfile({
                          ...editedProfile, 
                          instrument: e.target.value,
                          transposition: selected.transposition,
                          display_name: selected.display_name
                        });
                      }}
                      className="w-full rounded px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-gray-400"
                      style={{backgroundColor: '#404040', border: '1px solid #525252'}}
                    >
                      <option value="trumpet">Trumpet</option>
                      <option value="alto_sax">Alto Sax</option>
                      <option value="tenor_sax">Tenor Sax</option>
                      <option value="bari_sax">Bari Sax</option>
                      <option value="violin">Violin</option>
                      <option value="cello">Cello</option>
                      <option value="trombone">Trombone</option>
                      <option value="guitar">Guitar</option>
                      <option value="bass">Bass</option>
                      <option value="keys">Keys</option>
                      <option value="drums">Drums</option>
                      <option value="vocals">Vocals</option>
                    </select>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex space-x-3 pt-4">
                    <button
                      onClick={() => updateProfile(editedProfile)}
                      className="text-white px-6 py-2 rounded transition-colors hover:opacity-80"
                      style={{backgroundColor: '#000000'}}
                    >
                      Save Changes
                    </button>
                    <button
                      onClick={cancelEditingProfile}
                      className="text-white px-6 py-2 rounded transition-colors hover:opacity-80"
                      style={{backgroundColor: '#525252'}}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                /* Profile Display */
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">Your Instrument</h3>
                    <div className="rounded p-4" style={{backgroundColor: '#404040'}}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium text-lg">{profile?.display_name}</p>
                          <p className="text-gray-400 text-sm">
                            Transposition: {profile?.transposition === 'B♭' || profile?.transposition === 'E♭' ? <span style={{letterSpacing: '-0.25em'}}>{profile?.transposition}</span> : profile?.transposition}
                          </p>
                        </div>
                        <div className="text-4xl">
                          {profile?.instrument === 'trumpet' && '🎺'}
                          {profile?.instrument === 'alto_sax' && '🎷'}
                          {profile?.instrument === 'tenor_sax' && '🎷'}
                          {profile?.instrument === 'bari_sax' && '🎷'}
                          {profile?.instrument === 'violin' && '🎻'}
                          {profile?.instrument === 'cello' && '🎻'}
                          {profile?.instrument === 'trombone' && '🎺'}
                          {profile?.instrument === 'guitar' && '🎸'}
                          {profile?.instrument === 'bass' && '🎸'}
                          {profile?.instrument === 'keys' && '🎹'}
                          {profile?.instrument === 'drums' && '🥁'}
                          {profile?.instrument === 'vocals' && '🎤'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
