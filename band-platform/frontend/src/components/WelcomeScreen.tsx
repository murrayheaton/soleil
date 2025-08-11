'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface WelcomeScreenProps {
  userData?: {
    name?: string;
    email?: string;
    picture?: string;
  };
}

const INSTRUMENTS = [
  { value: 'alto_sax', label: 'Alto Saxophone', emoji: '🎷' },
  { value: 'tenor_sax', label: 'Tenor Saxophone', emoji: '🎷' },
  { value: 'soprano_sax', label: 'Soprano Saxophone', emoji: '🎷' },
  { value: 'baritone_sax', label: 'Baritone Saxophone', emoji: '🎷' },
  { value: 'trumpet', label: 'Trumpet', emoji: '🎺' },
  { value: 'flugelhorn', label: 'Flugelhorn', emoji: '🎺' },
  { value: 'trombone', label: 'Trombone', emoji: '🎺' },
  { value: 'euphonium', label: 'Euphonium', emoji: '🎺' },
  { value: 'tuba', label: 'Tuba', emoji: '🎺' },
  { value: 'flute', label: 'Flute', emoji: '🎵' },
  { value: 'clarinet', label: 'Clarinet', emoji: '🎵' },
  { value: 'oboe', label: 'Oboe', emoji: '🎵' },
  { value: 'bassoon', label: 'Bassoon', emoji: '🎵' },
  { value: 'guitar', label: 'Guitar', emoji: '🎸' },
  { value: 'bass', label: 'Bass Guitar', emoji: '🎸' },
  { value: 'piano', label: 'Piano', emoji: '🎹' },
  { value: 'drums', label: 'Drums', emoji: '🥁' },
  { value: 'vocals', label: 'Vocals', emoji: '🎤' },
  { value: 'other', label: 'Other Instrument', emoji: '🎵' }
];

export default function WelcomeScreen({ userData }: WelcomeScreenProps) {
  const router = useRouter();
  const [selectedInstrument, setSelectedInstrument] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [firstName, setFirstName] = useState('');

  useEffect(() => {
    // Extract first name from user data
    if (userData?.name) {
      const nameParts = userData.name.split(' ');
      setFirstName(nameParts[0] || '');
    }
  }, [userData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedInstrument) {
      alert('Please select an instrument to continue.');
      return;
    }

    setIsSubmitting(true);

    try {
      // Create profile with minimal required data
      const profileData = {
        email: userData?.email || '',
        name: userData?.name || '',
        instrument: selectedInstrument,
        display_name: userData?.name || '',
        transposition: getTransposition(selectedInstrument)
      };

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live'}/api/profile/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(profileData),
      });

      if (response.ok) {
        // Set profile complete cookie
        document.cookie = 'soleil_profile_complete=true; path=/; max-age=86400';
        document.cookie = 'soleil_auth=true; path=/; max-age=86400';
        
        // Redirect to dashboard
        router.push('/dashboard');
      } else {
        const errorText = await response.text();
        console.error('Profile save failed:', response.status, errorText);
        alert('Something went wrong. Please try again.');
      }
    } catch (error) {
      console.error('Profile save error:', error);
      alert('Connection error. Please check your internet and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getTransposition = (instrument: string): string => {
    const transpositions: { [key: string]: string } = {
      'alto_sax': 'E♭',
      'tenor_sax': 'B♭',
      'soprano_sax': 'B♭',
      'baritone_sax': 'E♭',
      'trumpet': 'B♭',
      'flugelhorn': 'B♭',
      'trombone': 'C',
      'euphonium': 'C',
      'tuba': 'C',
      'flute': 'C',
      'clarinet': 'B♭',
      'oboe': 'C',
      'bassoon': 'C',
      'guitar': 'C',
      'bass': 'C',
      'piano': 'C',
      'drums': 'C',
      'vocals': 'C',
      'other': 'C'
    };
    return transpositions[instrument] || 'C';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Welcome Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">☀️</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Hey {firstName || 'there'}!
          </h1>
          <p className="text-lg text-gray-600">
            Welcome to SOLEil - your band platform
          </p>
        </div>

        {/* Main Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="text-center mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              What instrument do you play?
            </h2>
            <p className="text-gray-500 text-sm">
              This helps us personalize your experience
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Instrument Selection */}
            <div>
              <label htmlFor="instrument" className="sr-only">
                Select your instrument
              </label>
              <select
                id="instrument"
                value={selectedInstrument}
                onChange={(e) => setSelectedInstrument(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl text-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                required
              >
                <option value="">Choose your instrument...</option>
                {INSTRUMENTS.map((instrument) => (
                  <option key={instrument.value} value={instrument.value}>
                    {instrument.emoji} {instrument.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!selectedInstrument || isSubmitting}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-xl font-semibold text-lg transition-all duration-200 transform hover:scale-105 hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Setting up your profile...
                </span>
              ) : (
                'Get Started! 🚀'
              )}
            </button>
          </form>

          {/* Helpful Note */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              Don't worry, you can change this later in your profile settings
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8">
          <p className="text-sm text-gray-400">
            SOLEil Band Platform • Making music together easier
          </p>
        </div>
      </div>
    </div>
  );
}
