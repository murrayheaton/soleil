import { ModuleProps } from '@/types/dashboard';

export function PendingOffersModule({ }: ModuleProps) {
  return (
    <div className="placeholder-module" style={{
      textAlign: 'center', 
      color: '#666', 
      padding: '2rem'
    }}>
      <p>Gig offers will appear here</p>
      <p className="coming-soon" style={{
        fontSize: '0.875rem', 
        color: '#999', 
        marginTop: '0.5rem'
      }}>
        Coming soon
      </p>
    </div>
  );
}