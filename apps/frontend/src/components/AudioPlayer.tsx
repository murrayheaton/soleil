'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  PlayIcon,
  PauseIcon,
  ForwardIcon,
  BackwardIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ArrowDownTrayIcon,
  XMarkIcon,
} from '@heroicons/react/24/solid';
import { offlineStorage } from '@/lib/database';
import { apiService } from '@/lib/api';
import type { Audio } from '@/lib/api';

interface AudioPlayerProps {
  audio: Audio;
  onClose?: () => void;
  autoPlay?: boolean;
  onNext?: () => void;
  onPrevious?: () => void;
}

export default function AudioPlayer({
  audio,
  onClose,
  autoPlay = false,
  onNext,
  onPrevious,
}: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  
  const audioRef = useRef<HTMLAudioElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const volumeRef = useRef<HTMLDivElement>(null);

  // Load audio from offline storage or API
  useEffect(() => {
    const loadAudio = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Try to load from offline storage first
        const storedAudio = await offlineStorage.getAudio(audio.id);
        
        if (storedAudio?.file_data) {
          const blob = new Blob([storedAudio.file_data], { type: 'audio/mpeg' });
          const url = URL.createObjectURL(blob);
          setAudioUrl(url);
          setIsOffline(true);
        } else {
          // Download from API
          const blob = await apiService.downloadAudio(audio);
          const url = URL.createObjectURL(blob);
          setAudioUrl(url);
          
          // Store for offline access
          try {
            const arrayBuffer = await blob.arrayBuffer();
            await offlineStorage.storeAudio({
              ...audio,
              file_data: arrayBuffer,
              band_id: typeof audio.band_id === 'string' ? parseInt(audio.band_id) : audio.band_id,
              accessible_to_user: true,
              file_type: 'audio',
              file_url: audio.id,
              created_at: new Date(),
              updated_at: new Date(),
            });
          } catch (cacheError) {
            console.warn('Failed to cache audio offline:', cacheError);
          }
        }
      } catch (err) {
        console.error('Failed to load audio:', err);
        setError('Failed to load audio. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    loadAudio();

    // Cleanup
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audio]);

  // Update audio element when URL changes
  useEffect(() => {
    if (audioRef.current && audioUrl) {
      audioRef.current.load();
      if (autoPlay) {
        audioRef.current.play().catch(e => {
          console.warn('Autoplay blocked:', e);
        });
      }
    }
  }, [audioUrl, autoPlay]);

  // Handle play/pause
  const togglePlayPause = useCallback(() => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(e => {
        console.error('Play failed:', e);
        setError('Failed to play audio');
      });
    }
  }, [isPlaying]);

  // Handle seek
  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !progressRef.current) return;

    const rect = progressRef.current.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    const time = percent * duration;
    
    audioRef.current.currentTime = time;
    setCurrentTime(time);
  }, [duration]);

  // Handle volume
  const handleVolumeChange = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || !volumeRef.current) return;

    const rect = volumeRef.current.getBoundingClientRect();
    const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    
    setVolume(percent);
    audioRef.current.volume = percent;
    
    if (percent === 0) {
      setIsMuted(true);
    } else if (isMuted) {
      setIsMuted(false);
    }
  }, [isMuted]);

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (!audioRef.current) return;

    if (isMuted) {
      audioRef.current.volume = volume || 0.5;
      setIsMuted(false);
    } else {
      audioRef.current.volume = 0;
      setIsMuted(true);
    }
  }, [isMuted, volume]);

  // Skip forward/backward
  const skipForward = useCallback(() => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.min(duration, currentTime + 10);
  }, [currentTime, duration]);

  const skipBackward = useCallback(() => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = Math.max(0, currentTime - 10);
  }, [currentTime]);

  // Format time display
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Download audio
  const downloadAudio = async () => {
    if (audioUrl) {
      const link = document.createElement('a');
      link.href = audioUrl;
      link.download = `${audio.title}.mp3`;
      link.click();
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      switch (e.key) {
        case ' ':
          e.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          skipBackward();
          break;
        case 'ArrowRight':
          skipForward();
          break;
        case 'ArrowUp':
          e.preventDefault();
          setVolume(v => Math.min(1, v + 0.1));
          if (audioRef.current) audioRef.current.volume = Math.min(1, volume + 0.1);
          break;
        case 'ArrowDown':
          e.preventDefault();
          setVolume(v => Math.max(0, v - 0.1));
          if (audioRef.current) audioRef.current.volume = Math.max(0, volume - 0.1);
          break;
        case 'm':
          toggleMute();
          break;
        case 'Escape':
          if (onClose) onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [togglePlayPause, skipBackward, skipForward, toggleMute, volume, onClose]);

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <div className="text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      {/* Audio Element */}
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onLoadedMetadata={(e) => {
            const audioElement = e.currentTarget;
            setDuration(audioElement.duration);
          }}
          onTimeUpdate={(e) => {
            const audioElement = e.currentTarget;
            setCurrentTime(audioElement.currentTime);
          }}
          onEnded={() => {
            setIsPlaying(false);
            if (onNext) onNext();
          }}
        />
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {audio.title}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {audio.reference_type === 'reference' ? 'Reference Recording' : 
             audio.reference_type === 'demo' ? 'Demo' : 'Backing Track'}
          </p>
          {isOffline && (
            <span className="inline-block mt-2 px-2 py-1 text-xs font-medium text-green-800 bg-green-100 rounded-full dark:text-green-200 dark:bg-green-900">
              Available Offline
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2 ml-4">
          <button
            onClick={downloadAudio}
            className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            aria-label="Download"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              aria-label="Close"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-2">
        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
        <div
          ref={progressRef}
          className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full cursor-pointer"
          onClick={handleSeek}
        >
          <div
            className="h-full bg-blue-600 rounded-full transition-all duration-100"
            style={{ width: `${(currentTime / duration) * 100 || 0}%` }}
          />
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        {/* Play Controls */}
        <div className="flex items-center space-x-2">
          {onPrevious && (
            <button
              onClick={onPrevious}
              className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              aria-label="Previous"
            >
              <BackwardIcon className="h-5 w-5" />
            </button>
          )}
          
          <button
            onClick={skipBackward}
            className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            aria-label="Skip backward 10s"
          >
            <span className="text-xs font-medium">-10</span>
          </button>

          <button
            onClick={togglePlayPause}
            className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <PauseIcon className="h-6 w-6" />
            ) : (
              <PlayIcon className="h-6 w-6" />
            )}
          </button>

          <button
            onClick={skipForward}
            className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            aria-label="Skip forward 10s"
          >
            <span className="text-xs font-medium">+10</span>
          </button>

          {onNext && (
            <button
              onClick={onNext}
              className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              aria-label="Next"
            >
              <ForwardIcon className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Volume Control */}
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleMute}
            className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            aria-label={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted || volume === 0 ? (
              <SpeakerXMarkIcon className="h-5 w-5" />
            ) : (
              <SpeakerWaveIcon className="h-5 w-5" />
            )}
          </button>
          
          <div
            ref={volumeRef}
            className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full cursor-pointer"
            onClick={handleVolumeChange}
          >
            <div
              className="h-full bg-gray-600 dark:bg-gray-400 rounded-full transition-all duration-100"
              style={{ width: `${(isMuted ? 0 : volume) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
        Space: Play/Pause • ←→: Skip • ↑↓: Volume • M: Mute
      </div>
    </div>
  );
}