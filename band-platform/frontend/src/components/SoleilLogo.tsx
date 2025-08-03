import React from 'react';

interface SoleilLogoProps {
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

export default function SoleilLogo({ size = 'medium', className = '' }: SoleilLogoProps) {
  const sizeStyles = {
    small: { fontSize: '1.25rem' },
    medium: { fontSize: '1.5rem' },
    large: { fontSize: '2rem' }
  };

  return (
    <div 
      className={`logo-wrapper ${className}`}
      style={{
        display: 'flex',
        alignItems: 'baseline',
        fontWeight: 'bold',
        gap: '0.25rem',
        ...sizeStyles[size]
      }}
    >
      <span style={{ color: 'white' }}>☀</span>
      <span className="logo-sole" style={{
        color: 'white',
        fontWeight: 900
      }}>SOLE</span>
      <span className="logo-il" style={{
        color: '#60a5fa',
        fontStyle: 'italic',
        fontFamily: 'serif'
      }}>il</span>
    </div>
  );
}