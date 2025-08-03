import { ModuleProps } from '@/types/dashboard';

export function CompletedGigsModule({ }: ModuleProps) {
  return (
    <div className="placeholder-module" style={{
      textAlign: 'center', 
      color: '#666', 
      padding: '2rem'
    }}>
      <p>Track completed performances</p>
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