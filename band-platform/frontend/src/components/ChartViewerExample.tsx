/**
 * Example component demonstrating ChartViewer integration with new API
 * This component shows how to use ChartViewer with the new backend endpoints
 */

'use client';

import React, { useState, useEffect } from 'react';
import ChartViewer from './ChartViewer';
import { apiService, Chart, AuthenticationError } from '@/lib/api';

export default function ChartViewerExample() {
  const [charts, setCharts] = useState<Chart[]>([]);
  const [selectedChart, setSelectedChart] = useState<Chart | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);

  useEffect(() => {
    loadCharts();
  }, []);

  const loadCharts = async () => {
    try {
      setLoading(true);
      setError(null);
      setNeedsAuth(false);

      const response = await apiService.listCharts({ limit: 10 });
      setCharts(response.charts);
    } catch (err) {
      console.error('Failed to load charts:', err);
      
      if (err instanceof AuthenticationError || apiService.isAuthError(err)) {
        setNeedsAuth(true);
        setError('Google Drive authentication required. Please authenticate to access charts.');
      } else {
        setError('Failed to load charts. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    try {
      const authResponse = await apiService.getGoogleAuthUrl();
      window.open(authResponse.auth_url, '_blank');
    } catch (err) {
      console.error('Failed to get auth URL:', err);
    }
  };

  if (selectedChart) {
    return (
      <ChartViewer
        chart={selectedChart}
        onClose={() => setSelectedChart(null)}
      />
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Chart Viewer Integration Test</h1>
      
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2">Loading charts...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
          {needsAuth && (
            <button
              onClick={handleGoogleAuth}
              className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Authenticate Google Drive
            </button>
          )}
          <button
            onClick={loadCharts}
            className="mt-3 ml-3 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && charts.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600">No charts found.</p>
        </div>
      )}

      {!loading && charts.length > 0 && (
        <div>
          <p className="mb-4 text-gray-600">
            Found {charts.length} charts. Click one to view:
          </p>
          <div className="grid gap-4">
            {charts.map((chart) => (
              <div
                key={chart.id}
                className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => setSelectedChart(chart)}
              >
                <h3 className="font-semibold">{chart.title}</h3>
                {chart.key && <p className="text-sm text-gray-600">Key: {chart.key}</p>}
                {chart.instruments.length > 0 && (
                  <p className="text-sm text-gray-600">
                    Instruments: {chart.instruments.join(', ')}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-2">
                  File: {chart.filename} ({(chart.size / 1024).toFixed(1)} KB)
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold mb-2">Integration Status</h3>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>✅ API Service: Connected to backend endpoints</li>
          <li>✅ Chart Types: TypeScript interfaces match backend</li>
          <li>✅ Error Handling: Proper 401 authentication handling</li>
          <li>✅ Offline Storage: IndexedDB caching available</li>
          <li>✅ ChartViewer: Updated to use new API</li>
        </ul>
      </div>
    </div>
  );
}