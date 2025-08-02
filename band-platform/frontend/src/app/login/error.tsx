'use client';

export default function LoginError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-gray-900">
      <div className="max-w-md w-full mx-4 p-8 bg-gray-800 rounded-lg">
        <h2 className="text-2xl font-bold text-red-400 mb-4">Login Error</h2>
        <p className="text-gray-300 mb-4">
          Something went wrong with the login page. This might be due to:
        </p>
        <ul className="list-disc list-inside text-gray-400 mb-6 space-y-1">
          <li>Missing environment variables</li>
          <li>JavaScript loading issues</li>
          <li>Network connectivity problems</li>
        </ul>
        <p className="text-sm text-gray-500 mb-6 font-mono bg-gray-900 p-2 rounded">
          {error.message || 'Unknown error'}
        </p>
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
            Go Home
          </button>
        </div>
      </div>
    </div>
  );
}