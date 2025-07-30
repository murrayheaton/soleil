'use client';
import { useState, useEffect } from 'react';

export default function SettingsPage() {
  const [darkMode, setDarkMode] = useState(false);
  const [scale, setScale] = useState('1');

  useEffect(() => {
    const theme = localStorage.getItem('theme');
    const savedScale = localStorage.getItem('scale');
    if (theme === 'dark') {
      setDarkMode(true);
    }
    if (savedScale) {
      setScale(savedScale);
    }
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  useEffect(() => {
    document.documentElement.style.setProperty('--scale', scale);
    localStorage.setItem('scale', scale);
  }, [scale]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <div className="flex items-center space-x-2">
        <input
          id="darkMode"
          type="checkbox"
          checked={darkMode}
          onChange={() => setDarkMode(!darkMode)}
        />
        <label htmlFor="darkMode">Dark Mode</label>
      </div>
      <div>
        <label htmlFor="scale" className="block mb-1">
          Interface Scale
        </label>
        <select
          id="scale"
          value={scale}
          onChange={(e) => setScale(e.target.value)}
          className="text-black p-1 border rounded"
        >
          <option value="0.875">Small</option>
          <option value="1">Medium</option>
          <option value="1.25">Large</option>
        </select>
      </div>
    </div>
  );
}
