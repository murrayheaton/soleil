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
  HomeIcon
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

export default function RepertoirePage() {
  const [files, setFiles] = useState<FilesResponse | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<{type: 'pdf' | 'audio' | 'study', file: ChartFile | AudioFile, song: string, songData?: Song} | null>(null);
  const [selectedSong, setSelectedSong] = useState<Song | null>(null);
  const [authStatus, setAuthStatus] = useState<'checking' | 'needed' | 'success' | 'error'>('checking');

  const fetchProfile = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/user/profile');
      const data = await response.json();
      
      if (data.status === 'success') {
        setProfile(data.profile);
        return data.profile;
      } else {
        setError(data.message || 'Failed to load profile');
        return null;
      }
    } catch (err) {
      setError('Failed to connect to backend.');
      return null;
    }
  };

  const fetchFiles = async (instrument: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/drive/${instrument}-view`);
      const data = await response.json();
      
      if (data.status === 'success') {
        setFiles(data);
        setAuthStatus('success');
      } else if (data.message && data.message.includes('Not authenticated')) {
        setAuthStatus('needed');
        setError('Please connect your Google Drive to access your files.');
      } else {
        setError(data.message || 'Failed to load files');
      }
    } catch (err) {
      setError('Failed to connect to backend. Make sure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      const userProfile = await fetchProfile();
      if (userProfile) {
        await fetchFiles(userProfile.instrument);
      }
    };
    
    loadData();
  }, []);

  const downloadFile = async (fileId: string, fileName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/drive/download/${fileId}`);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const viewFile = (type: 'pdf' | 'audio', file: ChartFile | AudioFile, song: string) => {
    setSelectedFile({ type, file, song });
  };

  const studySong = (song: Song) => {
    setSelectedFile({ type: 'study', file: song.charts[0] || song.audio[0], song: song.song_title, songData: song });
  };

  const handleGoogleSignIn = () => {
    const authUrl = `https://accounts.google.com/o/oauth2/auth?client_id=360999037847-1kkj607098goc38mvurbk91beukr3egn.apps.googleusercontent.com&response_type=code&scope=https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/userinfo.email&redirect_uri=http://localhost:8000/api/auth/google/callback&access_type=offline&prompt=consent`;
    window.location.href = authUrl;
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
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-black text-white mb-0">Sole Power <span className="font-thin">Live</span></h1>
              <p className="text-gray-400 text-sm font-light -mt-1">Assets access</p>
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

      {/* Song List or Song Folder View */}
      <div className="p-8">
        <div className="max-w-4xl mx-auto">
          {selectedSong ? (
            /* Song Folder View */
            <div className="rounded border overflow-hidden" style={{backgroundColor: '#262626', borderColor: '#404040'}}>
              {/* Back Button and Song Header */}
              <div className="px-6 py-4 border-b" style={{backgroundColor: '#404040', borderColor: '#525252'}}>
                <button
                  onClick={() => setSelectedSong(null)}
                  className="flex items-center text-gray-400 hover:text-white mb-4 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back to Song List
                </button>
                
                <div>
                  <h2 className="text-2xl font-semibold text-gray-200">{selectedSong.song_title}</h2>
                  <p className="text-gray-400 text-sm">{selectedSong.total_files} files available</p>
                </div>
              </div>
              
              <div className="p-6">
                {/* Charts */}
                {selectedSong.charts.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                      <DocumentTextIcon className="w-5 h-5 mr-2 text-gray-400" />
                      Charts
                    </h3>
                    <div className="space-y-2">
                      {selectedSong.charts.map((chart, chartIndex) => (
                        <div
                          key={chartIndex}
                          className={`rounded p-4 flex items-center justify-between transition-colors ${
                            chart.is_placeholder 
                              ? 'border hover:opacity-80' 
                              : 'hover:opacity-80'
                          }`}
                          style={chart.is_placeholder ? {backgroundColor: '#404040', borderColor: '#525252'} : {backgroundColor: '#404040'}}
                        >
                          <div className="flex-1">
                            <div className="flex items-center">
                              <p className="font-medium text-white">{chart.name}</p>
                              {chart.is_placeholder && (
                                <span className="ml-2 px-2 py-1 text-white text-xs rounded-full" style={{backgroundColor: '#525252'}}>
                                  Coming Soon
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-400">
                              Type: {chart.is_placeholder ? <>{profile?.transposition === 'B♭' || profile?.transposition === 'E♭' ? <span style={{letterSpacing: '-0.25em'}}>{profile?.transposition}</span> : profile?.transposition} (Preview)</> : chart.type}
                            </p>
                          </div>
                          <div className="flex space-x-3">
                            <button
                              onClick={() => viewFile('pdf', chart, selectedSong.song_title)}
                              disabled={chart.is_placeholder}
                              className={`px-4 py-2 rounded transition-colors flex items-center ${
                                chart.is_placeholder
                                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                  : 'text-white hover:opacity-80'
                              }`}
                              style={!chart.is_placeholder ? {backgroundColor: '#000000'} : {}}
                            >
                              <EyeIcon className="w-4 h-4 mr-2" />
                              {chart.is_placeholder ? 'Preview' : 'View'}
                            </button>
                            <button
                              onClick={() => downloadFile(chart.id, chart.name)}
                              disabled={chart.is_placeholder}
                              className={`px-4 py-2 rounded transition-colors flex items-center ${
                                chart.is_placeholder
                                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                  : 'text-white hover:opacity-80'
                              }`}
                              style={!chart.is_placeholder ? {backgroundColor: '#525252'} : {}}
                            >
                              <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                              Download
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Audio */}
                {selectedSong.audio.length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                      <MusicalNoteIcon className="w-5 h-5 mr-2 text-gray-400" />
                      Audio
                    </h3>
                    <div className="space-y-2">
                      {selectedSong.audio.map((audio, audioIndex) => (
                        <div
                          key={audioIndex}
                          className={`rounded p-4 flex items-center justify-between transition-colors ${
                            audio.is_placeholder 
                              ? 'border hover:opacity-80' 
                              : 'hover:opacity-80'
                          }`}
                          style={audio.is_placeholder ? {backgroundColor: '#404040', borderColor: '#525252'} : {backgroundColor: '#404040'}}
                        >
                          <div className="flex-1">
                            <div className="flex items-center">
                              <p className="font-medium text-white">{audio.name}</p>
                              {audio.is_placeholder && (
                                <span className="ml-2 px-2 py-1 text-white text-xs rounded-full" style={{backgroundColor: '#525252'}}>
                                  Coming Soon
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-400">
                              {audio.is_placeholder ? 'Audio Reference (Preview)' : 'Audio Reference'}
                            </p>
                          </div>
                          <div className="flex space-x-3">
                            <button
                              onClick={() => viewFile('audio', audio, selectedSong.song_title)}
                              disabled={audio.is_placeholder}
                              className={`px-4 py-2 rounded transition-colors flex items-center ${
                                audio.is_placeholder
                                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                  : 'text-white hover:opacity-80'
                              }`}
                              style={!audio.is_placeholder ? {backgroundColor: '#000000'} : {}}
                            >
                              <PlayIcon className="w-4 h-4 mr-2" />
                              {audio.is_placeholder ? 'Preview' : 'Play'}
                            </button>
                            <button
                              onClick={() => downloadFile(audio.id, audio.name)}
                              disabled={audio.is_placeholder}
                              className={`px-4 py-2 rounded transition-colors flex items-center ${
                                audio.is_placeholder
                                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                                  : 'text-white hover:opacity-80'
                              }`}
                              style={!audio.is_placeholder ? {backgroundColor: '#525252'} : {}}
                            >
                              <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                              Download
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedSong.charts.length === 0 && selectedSong.audio.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-400">No files available for this song.</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Song List View */
            files && files.songs.length > 0 ? (
              <div className="rounded border overflow-hidden" style={{backgroundColor: '#262626', borderColor: '#404040'}}>
                <div className="px-6 py-4 border-b" style={{backgroundColor: '#404040', borderColor: '#525252'}}>
                  <h2 className="text-xl font-black text-white">Repertoire</h2>
                  <p className="text-white text-sm">
                    <span>
                      {profile?.transposition === 'B♭' || profile?.transposition === 'E♭' ? (
                        <span style={{letterSpacing: '-0.25em'}}>{profile?.transposition}</span>
                      ) : (
                        profile?.transposition
                      )}
                    </span>
                    {' '}  -  {files.total_songs} songs
                  </p>
                </div>
                <div style={{borderTop: '1px solid #404040'}}>
                  {files.songs.map((song, index) => (
                    <div 
                      key={index} 
                      className="px-6 py-4 flex items-center justify-between group cursor-pointer hover:opacity-80 transition-colors"
                      onClick={() => studySong(song)}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#404040'} 
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                      style={{backgroundColor: 'transparent'}}
                    >
                      <div className="flex items-center flex-1">
                        <span className="text-gray-400 mr-3 text-lg">☀</span>
                        <span className="text-left text-white font-medium">
                          {song.song_title}
                        </span>
                      </div>
                      <div className="flex items-center text-gray-400 text-sm space-x-2">
                        <span>{song.total_files} files</span>
                        <button
                          onClick={() => setSelectedSong(song)}
                          className="p-1 hover:text-white transition-colors"
                          title="View file details"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">No files found for your instrument.</p>
                <p className="text-gray-500 text-sm mt-2">
                  Make sure you have {profile?.transposition === 'B♭' || profile?.transposition === 'E♭' ? <span style={{letterSpacing: '-0.25em'}}>{profile?.transposition}</span> : profile?.transposition} charts in your Google Drive.
                </p>
              </div>
            )
          )}
        </div>
      </div>

      {/* File Viewer Modal */}
      {selectedFile && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          {selectedFile.type === 'study' && selectedFile.songData ? (
            /* Reference Material - Split Screen */
            <div className="rounded h-full max-h-none overflow-hidden" style={{ width: 'fit-content', minWidth: '800px', backgroundColor: '#262626' }}>
              {/* Header */}
              <div className="px-6 py-4 border-b flex justify-between items-center" style={{backgroundColor: '#404040', borderColor: '#525252'}}>
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    {selectedFile.song}
                  </h3>
                  <p className="text-gray-400 text-sm">Reference Material</p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-gray-400 hover:text-white text-2xl font-bold"
                >
                  ×
                </button>
              </div>
              
              {/* Horizontal Split Content */}
              <div className="flex flex-col h-[calc(100vh-120px)]">
                {/* Top - Chart Viewer (takes most of the space) */}
                {selectedFile.songData.charts.length > 0 ? (
                  <div className="flex-1" style={{backgroundColor: '#171717'}}>
                    <iframe
                      src={`http://localhost:8000/api/drive/view/${selectedFile.songData.charts.find(c => !c.is_placeholder)?.id || selectedFile.songData.charts[0].id}#toolbar=0&navpanes=0&scrollbar=0&zoom=page-fit`}
                      className="w-full h-full"
                      title={`Chart - ${selectedFile.song}`}
                    />
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center" style={{backgroundColor: '#171717'}}>
                    <div className="text-center text-gray-400">
                      <DocumentTextIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p>No chart available for this song</p>
                    </div>
                  </div>
                )}
                
                {/* Bottom - Audio Control Bar */}
                {selectedFile.songData.audio.length > 0 ? (
                  <div className="border-t p-4" style={{backgroundColor: '#262626', borderColor: '#525252'}}>
                    <div className="flex items-center justify-between max-w-4xl mx-auto">
                      {/* Song Info */}
                      <div className="flex items-center space-x-3">
                        <MusicalNoteIcon className="w-6 h-6 text-gray-400" />
                        <div>
                          <p className="text-white font-medium text-sm">{selectedFile.song}</p>
                          <p className="text-gray-400 text-xs">Audio Reference</p>
                        </div>
                      </div>
                      
                      {/* Audio Player */}
                      <div className="flex-1 mx-6">
                        <audio
                          controls
                          className="w-full"
                          preload="metadata"
                          controlsList="nodownload"
                          style={{ height: '40px' }}
                          onLoadedMetadata={(e) => {
                            const audio = e.currentTarget;
                            console.log(`Audio duration: ${audio.duration}s`);
                            // Force update the UI by triggering a re-render
                            audio.currentTime = 0;
                          }}
                          onCanPlay={(e) => {
                            // Additional check when audio is ready to play
                            const audio = e.currentTarget;
                            if (audio.duration && isFinite(audio.duration)) {
                              console.log(`Audio ready: ${audio.duration}s duration`);
                            }
                          }}
                        >
                          <source 
                            src={`http://localhost:8000/api/drive/view/${selectedFile.songData.audio.find(a => !a.is_placeholder)?.id || selectedFile.songData.audio[0].id}`}
                            type="audio/mpeg"
                          />
                          <source 
                            src={`http://localhost:8000/api/drive/view/${selectedFile.songData.audio.find(a => !a.is_placeholder)?.id || selectedFile.songData.audio[0].id}`}
                            type="audio/wav"
                          />
                          <source 
                            src={`http://localhost:8000/api/drive/view/${selectedFile.songData.audio.find(a => !a.is_placeholder)?.id || selectedFile.songData.audio[0].id}`}
                            type="audio/m4a"
                          />
                          Your browser does not support the audio element.
                        </audio>
                      </div>
                      
                      {/* Download Options */}
                      <div className="flex space-x-3">
                        {selectedFile.songData.charts.length > 0 && (
                          <button
                            onClick={() => downloadFile(selectedFile.songData.charts.find(c => !c.is_placeholder)?.id || selectedFile.songData.charts[0].id, selectedFile.songData.charts[0].name)}
                            className="text-white px-3 py-2 rounded text-sm inline-flex items-center border hover:opacity-80"
                            style={{backgroundColor: '#404040', borderColor: '#525252'}}
                          >
                            <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                            Download Chart
                          </button>
                        )}
                        <button
                          onClick={() => downloadFile(selectedFile.songData.audio.find(a => !a.is_placeholder)?.id || selectedFile.songData.audio[0].id, selectedFile.songData.audio[0].name)}
                          className="text-white px-3 py-2 rounded text-sm inline-flex items-center border hover:opacity-80"
                          style={{backgroundColor: '#525252', borderColor: '#525252'}}
                        >
                          <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                          Download Audio
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="border-t p-4" style={{backgroundColor: '#262626', borderColor: '#525252'}}>
                    <div className="text-center text-gray-400 text-sm">
                      <p>No audio reference available for this song</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Regular Single File View */
            <div className="rounded max-w-4xl w-full max-h-[90vh] overflow-hidden" style={{backgroundColor: '#262626'}}>
              <div className="px-6 py-4 border-b flex justify-between items-center" style={{backgroundColor: '#404040', borderColor: '#525252'}}>
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    {selectedFile.song} - {selectedFile.file.name}
                  </h3>
                  <p className="text-gray-400 text-sm">
                    {selectedFile.type === 'pdf' ? 'Chart Viewer' : 'Audio Player'}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedFile(null)}
                  className="text-gray-400 hover:text-white text-2xl font-bold"
                >
                  ×
                </button>
              </div>
              
              <div className="p-6 overflow-auto max-h-[calc(90vh-100px)]">
                {selectedFile.type === 'pdf' ? (
                  <div className="space-y-4">
                    <div className="bg-gray-900 rounded overflow-hidden" style={{ height: '70vh' }}>
                      <iframe
                        src={`http://localhost:8000/api/drive/view/${selectedFile.file.id}#toolbar=0&navpanes=0&scrollbar=0&zoom=page-fit`}
                        className="w-full h-full"
                        title={`PDF Viewer - ${selectedFile.file.name}`}
                      />
                    </div>
                    <div className="text-center">
                      <button
                        onClick={() => downloadFile(selectedFile.file.id, selectedFile.file.name)}
                        className="bg-gray-900 hover:bg-black text-white px-6 py-2 rounded inline-flex items-center"
                      >
                        <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                        Download PDF
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="bg-gray-900 rounded p-8">
                      <div className="flex items-center justify-center mb-6">
                        <MusicalNoteIcon className="w-16 h-16 text-gray-400" />
                      </div>
                      <audio
                        controls
                        className="w-full"
                        preload="metadata"
                      >
                        <source 
                          src={`http://localhost:8000/api/drive/view/${selectedFile.file.id}`}
                          type="audio/mpeg"
                        />
                        <source 
                          src={`http://localhost:8000/api/drive/view/${selectedFile.file.id}`}
                          type="audio/wav"
                        />
                        Your browser does not support the audio element.
                      </audio>
                      <div className="text-center mt-4 text-gray-400">
                        <p className="text-sm">Use the controls above to play, pause, and adjust volume</p>
                      </div>
                    </div>
                    <div className="text-center">
                      <button
                        onClick={() => downloadFile(selectedFile.file.id, selectedFile.file.name)}
                        className="bg-gray-900 hover:bg-black text-white px-6 py-2 rounded inline-flex items-center"
                      >
                        <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                        Download Audio
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}