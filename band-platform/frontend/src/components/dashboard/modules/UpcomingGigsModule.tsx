import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ModuleProps } from '@/types/dashboard';

interface Gig {
  id: string;
  venue: string;
  date: string;
  time: string;
  type: string;
}

export function UpcomingGigsModule({ userId }: ModuleProps) {
  const [gigs, setGigs] = useState<Gig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    fetchUpcomingGigs();
  }, [userId]);
  
  const fetchUpcomingGigs = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/upcoming-gigs`,
        { credentials: 'include' }
      );
      
      if (!response.ok) throw new Error('Failed to fetch gigs');
      
      const data = await response.json();
      setGigs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="module-spinner" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100px',
        color: '#666'
      }}>
        Loading gigs...
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="module-error-text" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100px',
        color: '#999'
      }}>
        Unable to load gigs
      </div>
    );
  }
  
  if (gigs.length === 0) {
    return (
      <div className="empty-state" style={{textAlign: 'center', color: '#666', padding: '2rem'}}>
        <p>No upcoming gigs scheduled</p>
        <Link href="/upcoming-gigs" className="empty-state-link" style={{
          color: '#666',
          textDecoration: 'none',
          fontWeight: '500',
          marginTop: '1rem',
          display: 'inline-block'
        }}>
          View gig calendar →
        </Link>
      </div>
    );
  }
  
  return (
    <ul className="gig-list" style={{listStyle: 'none', padding: 0, margin: 0}}>
      {gigs.slice(0, 5).map(gig => (
        <li key={gig.id} className="gig-item" style={{
          display: 'flex',
          alignItems: 'center',
          padding: '1rem 0',
          borderBottom: '1px solid #404040'
        }}>
          <div className="gig-date" style={{
            flexShrink: 0,
            width: '50px',
            textAlign: 'center',
            marginRight: '1rem'
          }}>
            <span className="day" style={{
              display: 'block',
              fontSize: '1.5rem',
              fontWeight: 'bold',
              lineHeight: 1,
              color: 'white'
            }}>
              {new Date(gig.date).getDate()}
            </span>
            <span className="month" style={{
              display: 'block',
              fontSize: '0.875rem',
              textTransform: 'uppercase',
              color: '#666'
            }}>
              {new Date(gig.date).toLocaleDateString('en-US', { month: 'short' })}
            </span>
          </div>
          <div className="gig-details">
            <h4 style={{margin: '0 0 0.25rem 0', fontSize: '1rem', color: 'white'}}>
              {gig.venue}
            </h4>
            <p style={{margin: 0, color: '#666', fontSize: '0.875rem'}}>
              {gig.time} • {gig.type}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}