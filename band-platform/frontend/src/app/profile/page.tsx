'use client';

import { useState, useEffect, Suspense } from 'react';
import { 
  UserCircleIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { useSearchParams } from 'next/navigation';
import ProfileOnboarding from '@/components/ProfileOnboarding';

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


interface UserProfile {
  email: string;
  name: string;
  instrument: string;
  transposition: string;
  display_name: string;
}

function ProfileContent() {
  useSearchParams(); // Hook is required for component but not used directly
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authStatus, setAuthStatus] = useState<'checking' | 'needed' | 'success' | 'error'>('checking');
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editedProfile, setEditedProfile] = useState<UserProfile | null>(null);
  const [isNewUser, setIsNewUser] = useState(false);
  const [googleUserData, setGoogleUserData] = useState<{name?: string; email?: string; picture?: string} | null>(null);

  const fetchProfile = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live'}/api/user/profile`);
      const data = await response.json();
      
      console.log('Profile API response:', data);
      
      if (response.status === 404) {
        // New user - no profile exists yet
        setIsNewUser(true);
        setProfile({
          name: '',
          email: '',
          instrument: '',
          transposition: '',
          display_name: ''
        });
        setAuthStatus('success');
        setLoading(false);
        
        // Try to get Google user data from session
        try {
          const sessionResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live'}/api/auth/session`);
          if (sessionResponse.ok) {
            const sessionData = await sessionResponse.json();
            setGoogleUserData({
              name: sessionData.name,
              email: sessionData.email,
              picture: sessionData.picture
            });
          }
        } catch (error) {
          console.error('Failed to get session data:', error);
        }
        return;
      }
      
      if (data.status === 'success') {
        setProfile(data.profile);
        setAuthStatus('success');
      } else if (data.message && data.message.includes('Not authenticated')) {
        setAuthStatus('needed');
        setError('Please connect your Google Drive to access your profile.');
      } else {
        setError(data.message || 'Failed to load profile');
      }
    } catch {
      setError('Failed to connect to backend. Make sure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check URL parameters for auth status
    const urlParams = new URLSearchParams(window.location.search);
    const authParam = urlParams.get('auth');
    const isNewUserParam = urlParams.get('new_user') === 'true';
    
    if (authParam === 'success') {
      setAuthStatus('success');
      if (isNewUserParam) {
        setIsNewUser(true);
      }
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

  const updateProfile = async (updatedProfile: Partial<UserProfile>) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live'}/api/user/profile`, {
        method: 'POST',
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
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!clientId || !apiUrl) {
      console.error('Google OAuth environment variables are not set');
      return;
    }

    const baseUrl = apiUrl.replace(/\/api$/, ''); // Remove trailing /api if present
    const redirectUri = `${baseUrl}/api/auth/google/callback`;
    const authUrl =
      `https://accounts.google.com/o/oauth2/auth?client_id=${clientId}` +
      `&response_type=code&scope=https://www.googleapis.com/auth/drive.readonly` +
      ` https://www.googleapis.com/auth/userinfo.email&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&access_type=offline&prompt=consent`;
    window.location.href = authUrl;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading your profile...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show login screen when authentication is needed
  if (authStatus === 'needed' || (error && error.includes('Not authenticated'))) {
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
            
          </div>
        </div>
      </div>

      {/* Profile Content */}
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
          {/* Show onboarding for new users without a profile */}
          {isNewUser && !profile?.name ? (
            <ProfileOnboarding 
              initialData={googleUserData || undefined}
              onComplete={() => {
                setIsNewUser(false);
                fetchProfile(); // Refresh profile data
              }}
            />
          ) : (
            /* Profile Card */
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
          )}
        </div>
      </div>
    </div>
  );
}

export default function BandPlatform() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading...</p>
          </div>
        </div>
      </div>
    }>
      <ProfileContent />
    </Suspense>
  );
}
