'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import {
  ArrowDownTrayIcon,
  MagnifyingGlassPlusIcon,
  MagnifyingGlassMinusIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { offlineStorage } from '@/lib/database';
import { apiService, AuthenticationError } from '@/lib/api';
import type { Chart } from '@/lib/api';

// Configure PDF.js worker - only on client side
if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;
}

interface ChartViewerProps {
  chart: Chart;
  onClose?: () => void;
}

export default function ChartViewer({ chart, onClose }: ChartViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState<boolean>(false);
  const [needsAuth, setNeedsAuth] = useState<boolean>(false);
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const touchStartRef = useRef<{ x: number; y: number; distance: number } | null>(null);
  const [pageWidth, setPageWidth] = useState<number>(0);

  // Calculate optimal page width based on container
  useEffect(() => {
    const updatePageWidth = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.clientWidth;
        setPageWidth(Math.min(containerWidth - 32, 800)); // Max 800px width
      }
    };

    updatePageWidth();
    window.addEventListener('resize', updatePageWidth);
    return () => window.removeEventListener('resize', updatePageWidth);
  }, []);

  // Load PDF from offline storage or API
  useEffect(() => {
    const loadPdf = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Try to load from offline storage first
        const storedChart = await offlineStorage.getChart(chart.id);
        
        if (storedChart?.file_data) {
          const blob = new Blob([storedChart.file_data], { type: 'application/pdf' });
          const url = URL.createObjectURL(blob);
          setPdfUrl(url);
          setIsOffline(true);
        } else {
          // Download from API
          const blob = await apiService.downloadChart(chart);
          const url = URL.createObjectURL(blob);
          setPdfUrl(url);
          
          // Store for offline access
          try {
            const arrayBuffer = await blob.arrayBuffer();
            await offlineStorage.storeChart({
              ...chart,
              file_data: arrayBuffer,
              band_id: typeof chart.band_id === 'string' ? parseInt(chart.band_id) : chart.band_id,
              accessible_to_user: true,
              file_type: 'chart',
              file_url: chart.id,
              created_at: new Date(),
              updated_at: new Date(),
            });
          } catch (cacheError) {
            console.warn('Failed to cache chart offline:', cacheError);
          }
        }
      } catch (err) {
        console.error('Failed to load PDF:', err);
        
        if (err instanceof AuthenticationError) {
          setNeedsAuth(true);
          setError('Google Drive authentication required to access charts.');
          
          // Try to get auth URL
          try {
            const authUrlResponse = await apiService.getAuthUrlOnError();
            setAuthUrl(authUrlResponse);
          } catch (authError) {
            console.error('Failed to get auth URL:', authError);
          }
        } else if (apiService.isAuthError(err)) {
          setNeedsAuth(true);
          setError('Google Drive authentication required to access charts.');
        } else {
          setError('Failed to load chart. Please try again.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadPdf();

    // Cleanup
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [chart]);

  // Handle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  // Handle zoom
  const handleZoomIn = useCallback(() => {
    setScale(prev => Math.min(prev + 0.25, 3.0));
  }, []);

  const handleZoomOut = useCallback(() => {
    setScale(prev => Math.max(prev - 0.25, 0.5));
  }, []);

  const handleZoomReset = useCallback(() => {
    setScale(1.0);
  }, []);

  // Handle page navigation
  const goToPreviousPage = useCallback(() => {
    setPageNumber(prev => Math.max(prev - 1, 1));
  }, []);

  const goToNextPage = useCallback(() => {
    setPageNumber(prev => Math.min(prev + 1, numPages));
  }, [numPages]);

  // Handle touch gestures for pinch zoom
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      const touch1 = e.touches[0];
      const touch2 = e.touches[1];
      const distance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      );
      touchStartRef.current = {
        x: (touch1.clientX + touch2.clientX) / 2,
        y: (touch1.clientY + touch2.clientY) / 2,
        distance,
      };
    }
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2 && touchStartRef.current) {
      const touch1 = e.touches[0];
      const touch2 = e.touches[1];
      const distance = Math.hypot(
        touch2.clientX - touch1.clientX,
        touch2.clientY - touch1.clientY
      );
      
      const scaleFactor = distance / touchStartRef.current.distance;
      setScale(prev => Math.min(Math.max(prev * scaleFactor, 0.5), 3.0));
      
      touchStartRef.current.distance = distance;
    }
  }, []);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowLeft':
          goToPreviousPage();
          break;
        case 'ArrowRight':
          goToNextPage();
          break;
        case '+':
        case '=':
          handleZoomIn();
          break;
        case '-':
          handleZoomOut();
          break;
        case '0':
          handleZoomReset();
          break;
        case 'f':
          toggleFullscreen();
          break;
        case 'Escape':
          if (isFullscreen) {
            toggleFullscreen();
          } else if (onClose) {
            onClose();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [goToPreviousPage, goToNextPage, handleZoomIn, handleZoomOut, handleZoomReset, toggleFullscreen, isFullscreen, onClose]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  const downloadChart = async () => {
    if (pdfUrl) {
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = `${chart.title} - ${chart.key}.pdf`;
      link.click();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center">
        <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
        <div className="flex space-x-3">
          {needsAuth && authUrl ? (
            <button
              onClick={() => window.open(authUrl, '_blank')}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Authenticate Google Drive
            </button>
          ) : null}
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
        {needsAuth && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
            After authenticating, please refresh this page to load the chart.
          </p>
        )}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`${
        isFullscreen ? 'fixed inset-0 z-50' : 'relative'
      } bg-gray-100 dark:bg-gray-800 flex flex-col`}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
    >
      {/* Toolbar */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">
              {chart.title} - {chart.key}
            </h2>
            {isOffline && (
              <span className="px-2 py-1 text-xs font-medium text-green-800 bg-green-100 rounded-full dark:text-green-200 dark:bg-green-900">
                Offline
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            {/* Page Navigation */}
            {numPages > 1 && (
              <div className="flex items-center space-x-1 mr-4">
                <button
                  onClick={goToPreviousPage}
                  disabled={pageNumber <= 1}
                  className="p-1 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 disabled:opacity-50"
                  aria-label="Previous page"
                >
                  <ChevronLeftIcon className="h-5 w-5" />
                </button>
                <span className="text-sm text-gray-600 dark:text-gray-400 mx-2">
                  {pageNumber} / {numPages}
                </span>
                <button
                  onClick={goToNextPage}
                  disabled={pageNumber >= numPages}
                  className="p-1 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 disabled:opacity-50"
                  aria-label="Next page"
                >
                  <ChevronRightIcon className="h-5 w-5" />
                </button>
              </div>
            )}

            {/* Zoom Controls */}
            <button
              onClick={handleZoomOut}
              className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              aria-label="Zoom out"
            >
              <MagnifyingGlassMinusIcon className="h-5 w-5" />
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400 min-w-[3rem] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
              aria-label="Zoom in"
            >
              <MagnifyingGlassPlusIcon className="h-5 w-5" />
            </button>

            {/* Action Buttons */}
            <div className="flex items-center space-x-1 ml-4">
              <button
                onClick={downloadChart}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
                aria-label="Download"
              >
                <ArrowDownTrayIcon className="h-5 w-5" />
              </button>
              <button
                onClick={toggleFullscreen}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
                aria-label="Toggle fullscreen"
              >
                {isFullscreen ? (
                  <ArrowsPointingInIcon className="h-5 w-5" />
                ) : (
                  <ArrowsPointingOutIcon className="h-5 w-5" />
                )}
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
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 overflow-auto flex items-center justify-center p-4">
        {pdfUrl && (
          <Document
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            }
            error={
              <div className="text-red-600 dark:text-red-400">
                Failed to load PDF
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              width={pageWidth}
              scale={scale}
              className="shadow-lg"
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
          </Document>
        )}
      </div>

      {/* Mobile Touch Instructions */}
      <div className="md:hidden absolute bottom-4 left-4 right-4 bg-black/70 text-white text-xs p-2 rounded-lg text-center">
        Pinch to zoom • Swipe to navigate
      </div>
    </div>
  );
}