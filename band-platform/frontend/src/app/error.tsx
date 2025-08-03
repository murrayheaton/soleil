'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error('Global error:', error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="fixed inset-0 flex items-center justify-center bg-gray-900">
          <div className="max-w-md w-full mx-4 p-8 bg-gray-800 rounded-lg shadow-xl">
            <h1 className="text-3xl font-bold text-red-400 mb-4">Oops! Something went wrong</h1>
            <p className="text-gray-300 mb-6">
              We apologize for the inconvenience. The application encountered an unexpected error.
            </p>
            
            {process.env.NODE_ENV === 'development' && (
              <details className="mb-6">
                <summary className="cursor-pointer text-gray-400 hover:text-gray-300">
                  Error details (development only)
                </summary>
                <pre className="mt-2 text-xs text-gray-500 bg-gray-900 p-3 rounded overflow-auto">
                  {error.message}
                  {error.stack}
                </pre>
              </details>
            )}
            
            <div className="flex gap-4">
              <button
                onClick={reset}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
              >
                Go to Home
              </button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}