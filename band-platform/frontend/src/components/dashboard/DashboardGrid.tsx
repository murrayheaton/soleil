import { Suspense } from 'react';
import { DashboardModule } from '@/types/dashboard';
import { ModuleWrapper } from './ModuleWrapper';

interface DashboardGridProps {
  modules: Map<string, DashboardModule>;
  userId: string;
}

export function DashboardGrid({ modules, userId }: DashboardGridProps) {
  return (
    <div className="dashboard-grid">
      {Array.from(modules.values()).map(module => (
        <ModuleWrapper 
          key={module.id}
          module={module}
        >
          <Suspense 
            fallback={
              <div className="module-loading">
                <div className="loading-spinner" />
              </div>
            }
          >
            <module.component userId={userId} />
          </Suspense>
        </ModuleWrapper>
      ))}

      <style jsx>{`
        .dashboard-grid {
          display: grid;
          gap: 1.5rem;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          grid-auto-rows: minmax(200px, auto);
        }

        .module-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 200px;
          color: #666;
        }

        .loading-spinner {
          width: 24px;
          height: 24px;
          border: 2px solid #404040;
          border-top-color: #666;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
          margin-right: 0.5rem;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
          .dashboard-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
          }
        }

        @media (min-width: 769px) and (max-width: 1024px) {
          .dashboard-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (min-width: 1025px) {
          .dashboard-grid {
            grid-template-columns: repeat(4, 1fr);
          }
          
          /* Span modules across grid */
          :global(.module-upcoming-gigs),
          :global(.module-recent-repertoire) {
            grid-column: span 2;
            grid-row: span 2;
          }
          
          :global(.module-pending-offers),
          :global(.module-completed-gigs) {
            grid-column: span 2;
          }
        }
      `}</style>
    </div>
  );
}