import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ModuleProps } from '@/types/dashboard';

interface RepertoireItem {
  id: string;
  title: string;
  key?: string;
  addedAt: string;
}

export function RecentRepertoireModule({ userId }: ModuleProps) {
  const [repertoire, setRepertoire] = useState<RepertoireItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchRecentRepertoire();
  }, [userId]);
  
  const fetchRecentRepertoire = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/recent-repertoire`,
        { credentials: 'include' }
      );
      
      if (response.ok) {
        const data = await response.json();
        setRepertoire(data);
      }
    } catch (err) {
      console.error('Failed to fetch repertoire:', err);
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
        Loading repertoire...
      </div>
    );
  }
  
  if (repertoire.length === 0) {
    return (
      <div className="empty-state" style={{textAlign: 'center', color: '#666', padding: '2rem'}}>
        <p>No repertoire added yet</p>
        <Link href="/repertoire" className="empty-state-link" style={{
          color: '#666',
          textDecoration: 'none',
          fontWeight: '500',
          marginTop: '1rem',
          display: 'inline-block'
        }}>
          Browse repertoire →
        </Link>
      </div>
    );
  }
  
  return (
    <div className="repertoire-list" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem'
    }}>
      {repertoire.slice(0, 10).map(item => (
        <div key={item.id} className="repertoire-item" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem'
        }}>
          <span className="repertoire-icon" style={{
            fontSize: '1.25rem',
            flexShrink: 0
          }}>
            ☀
          </span>
          <div className="repertoire-details" style={{
            flex: 1,
            minWidth: 0
          }}>
            <span className="title" style={{
              display: 'block',
              fontWeight: '500',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              color: 'white'
            }}>
              {item.title}
            </span>
            <span className="meta" style={{
              display: 'block',
              fontSize: '0.875rem',
              color: '#666'
            }}>
              {item.key && `${item.key} • `}
              Added {formatRelativeTime(item.addedAt)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  
  if (diffInDays === 0) return 'today';
  if (diffInDays === 1) return 'yesterday';
  if (diffInDays < 7) return `${diffInDays} days ago`;
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
  return date.toLocaleDateString();
}