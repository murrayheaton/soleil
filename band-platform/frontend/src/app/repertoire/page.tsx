'use client';

import { useState, useEffect } from 'react';
import { 
  DocumentTextIcon, 
  MusicalNoteIcon,
  ArrowDownTrayIcon,
  PlayIcon,
  EyeIcon,
  HomeIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { apiService } from '@/lib/api';
import type { Chart, ChartListResponse } from '@/lib/api';
import ChartViewer from '@/components/ChartViewer';

interface UserProfile {
  email: string;
  name: string;
  instrument: string;
  transposition: string;
  display_name: string;
}

export default function RepertoirePage() {
  const [charts, setCharts] = useState<Chart[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedChart, setSelectedChart] = useState<Chart | null>(null);
  const [authStatus, setAuthStatus] = useState<'checking' | 'needed' | 'success' | 'error'>('checking');
  const [searchQuery, setSearchQuery] = useState('');
  const [groupedCharts, setGroupedCharts] = useState<Map<string, Chart[]>>(new Map());

  const fetchProfile = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live'}/api/profile/profile`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setProfile(data.profile);
        return data.profile;
      } else {
        setError(data.message || 'Failed to load profile');
        return null;
      }
    } catch {
      setError('Failed to connect to backend.');
      return null;
    }
  };

  const fetchCharts = async (instrument?: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // First check auth status
      const authStatus = await apiService.checkGoogleAuthStatus();
      
      if (!authStatus.authenticated) {
        setAuthStatus('needed');
        setError('Please authenticate with Google Drive to access your charts.');
        return;
      }

      // Fetch charts using the content module API
      const response = await apiService.listCharts({
        instrument: instrument,
        limit: 100
      });
      
      setCharts(response.charts);
      setAuthStatus('success');
      
      // Group charts by song title
      const grouped = new Map<string, Chart[]>();
      response.charts.forEach(chart => {
        const songTitle = chart.title;
        if (!grouped.has(songTitle)) {
          grouped.set(songTitle, []);
        }
        grouped.get(songTitle)?.push(chart);
      });
      setGroupedCharts(grouped);
      
    } catch (err: any) {
      if (apiService.isAuthError(err)) {
        setAuthStatus('needed');
        setError('Google Drive authentication required to access charts.');
      } else {
        setError(err.message || 'Failed to load charts');
      }
    } finally {
      setLoading(false);
    }
  };

  const searchCharts = async () => {
    if (!searchQuery.trim()) {
      await fetchCharts(profile?.transposition);
      return;
    }

    setLoading(true);
    try {
      const response = await apiService.searchCharts({
        query: searchQuery,
        instrument: profile?.transposition,
        limit: 50
      });
      
      setCharts(response.charts);
      
      // Group search results
      const grouped = new Map<string, Chart[]>();
      response.charts.forEach(chart => {
        const songTitle = chart.title;
        if (!grouped.has(songTitle)) {
          grouped.set(songTitle, []);
        }
        grouped.get(songTitle)?.push(chart);
      });
      setGroupedCharts(grouped);
      
    } catch (err: any) {
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      const userProfile = await fetchProfile();
      if (userProfile) {
        // Map instrument to transposition
        const transpositionMap: { [key: string]: string } = {
          'trumpet': 'Bb',
          'tenor_sax': 'Bb',
          'alto_sax': 'Eb',
          'bari_sax': 'Eb',
          'violin': 'Concert',
          'trombone': 'BassClef',
          'piano': 'Chords',
          'guitar': 'Chords',
          'bass': 'Chords',
          'drums': 'Chords',
          'singer': 'Lyrics'
        };
        
        const transposition = transpositionMap[userProfile.instrument.toLowerCase()] || userProfile.transposition;
        await fetchCharts(transposition);
      }
    };
    
    loadData();
  }, []);

  const handleGoogleAuth = async () => {
    try {
      const authData = await apiService.getGoogleAuthUrl();
      if (authData.auth_url) {
        window.location.href = authData.auth_url;
      }
    } catch (err) {
      setError('Failed to get authentication URL');
    }
  };

  const downloadChart = async (chart: Chart) => {
    try {
      const blob = await apiService.downloadChart(chart);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = chart.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen text-white p-8" style={{backgroundColor: '#171717'}}>
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading your repertoire...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show authentication screen if needed
  if (authStatus === 'needed') {
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
                onClick={handleGoogleAuth}
                className="w-full bg-white hover:bg-gray-100 text-gray-800 font-semibold px-6 py-4 rounded transition-colors flex items-center justify-center shadow-lg"
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Authenticate with Google Drive
              </button>
            </div>
            
            {error && (
              <div className="mt-4 p-3 rounded bg-red-900 bg-opacity-50 text-red-200 text-sm">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Show chart viewer if a chart is selected
  if (selectedChart) {
    return (
      <ChartViewer 
        chart={selectedChart} 
        onClose={() => setSelectedChart(null)} 
      />
    );
  }

  return (
    <div className="min-h-screen text-white" style={{backgroundColor: '#171717'}}>
      {/* Header */}
      <div className="border-b px-8 py-6" style={{backgroundColor: '#171717', borderColor: '#404040'}}>
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-black text-white mb-0">Repertoire</h1>
              <p className="text-gray-400 text-sm font-light">
                {profile?.transposition} Charts • {groupedCharts.size} Songs
              </p>
            </div>
            
            {/* Navigation */}
            <div className="flex items-center space-x-4">
              <Link 
                href="/" 
                className="text-white px-4 py-2 rounded transition-colors inline-flex items-center hover:opacity-80"
                style={{backgroundColor: '#000000'}}
              >
                <HomeIcon className="w-4 h-4 mr-2" />
                Profile
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="px-8 py-4 border-b" style={{borderColor: '#404040'}}>
        <div className="max-w-4xl mx-auto">
          <div className="relative">
            <input
              type="text"
              placeholder="Search for songs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && searchCharts()}
              className="w-full px-4 py-3 pl-10 rounded text-white placeholder-gray-500"
              style={{backgroundColor: '#262626'}}
            />
            <MagnifyingGlassIcon className="absolute left-3 top-3.5 w-5 h-5 text-gray-500" />
          </div>
        </div>
      </div>

      {/* Song List */}
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
          {error && (
            <div className="mb-4 p-4 rounded bg-red-900 bg-opacity-50 text-red-200">
              {error}
            </div>
          )}

          {groupedCharts.size === 0 ? (
            <div className="text-center py-12">
              <DocumentTextIcon className="w-16 h-16 mx-auto mb-4 text-gray-600" />
              <p className="text-gray-400">No charts found</p>
            </div>
          ) : (
            <div className="space-y-2">
              {Array.from(groupedCharts.entries()).map(([songTitle, songCharts]) => (
                <div
                  key={songTitle}
                  className="rounded p-4 flex items-center justify-between hover:opacity-80 transition-colors cursor-pointer"
                  style={{backgroundColor: '#262626'}}
                  onClick={() => setSelectedChart(songCharts[0])}
                >
                  <div className="flex items-center space-x-4">
                    <DocumentTextIcon className="w-6 h-6 text-gray-400" />
                    <div>
                      <p className="font-medium text-white">{songTitle}</p>
                      <p className="text-sm text-gray-400">
                        {songCharts.length} version{songCharts.length !== 1 ? 's' : ''} • 
                        {songCharts[0].key && ` ${songCharts[0].key}`}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedChart(songCharts[0]);
                      }}
                      className="px-3 py-1.5 rounded text-white text-sm hover:opacity-80"
                      style={{backgroundColor: '#000000'}}
                    >
                      <EyeIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        downloadChart(songCharts[0]);
                      }}
                      className="px-3 py-1.5 rounded text-white text-sm hover:opacity-80"
                      style={{backgroundColor: '#525252'}}
                    >
                      <ArrowDownTrayIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}