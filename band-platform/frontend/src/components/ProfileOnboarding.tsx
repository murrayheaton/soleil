'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface ProfileOnboardingProps {
  initialData?: {
    name?: string;
    email?: string;
    picture?: string;
  };
  onComplete: () => void;
}

export default function ProfileOnboarding({ initialData, onComplete }: ProfileOnboardingProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    email: initialData?.email || '',
    instrument: '',
    phone: '',
    dietary_restrictions: '',
    accessibility_needs: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live'}/api/user/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        onComplete();
        router.push('/repertoire');
      } else {
        console.error('Profile creation failed');
      }
    } catch (error) {
      console.error('Profile creation error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-lg">
        <h1 className="text-3xl font-bold mb-2">Welcome to SOLEil! ☀</h1>
        <p className="text-lg opacity-90">Let's set up your musician profile to get started.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 p-6 rounded-b-lg shadow-lg">
        <div className="space-y-6">
          {/* Name Field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Full Name *
            </label>
            <input
              type="text"
              name="name"
              required
              value={formData.name}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Your full name"
            />
          </div>

          {/* Email Field (Read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              readOnly
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-600 dark:text-gray-300"
            />
          </div>

          {/* Instrument Field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Primary Instrument *
            </label>
            <select
              name="instrument"
              required
              value={formData.instrument}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">Select your instrument</option>
              <option value="alto_sax">Alto Sax (E♭)</option>
              <option value="tenor_sax">Tenor Sax (B♭)</option>
              <option value="trumpet">Trumpet (B♭)</option>
              <option value="trombone">Trombone</option>
              <option value="guitar">Guitar</option>
              <option value="bass">Bass</option>
              <option value="drums">Drums</option>
              <option value="keyboard">Keyboard/Piano</option>
              <option value="vocals">Vocals</option>
              <option value="violin">Violin</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Phone Field */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Phone Number
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Optional - for gig notifications"
            />
          </div>

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 disabled:opacity-50"
            >
              {isSubmitting ? 'Creating Profile...' : 'Complete Setup'}
            </button>
          </div>
        </div>
      </form>

      <div className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
        <p>You can update these details anytime from your profile settings.</p>
      </div>
    </div>
  );
}