import { DashboardModule } from '@/types/dashboard';
import { UpcomingGigsModule } from '@/components/dashboard/modules/UpcomingGigsModule';
import { RecentRepertoireModule } from '@/components/dashboard/modules/RecentRepertoireModule';
import { PendingOffersModule } from '@/components/dashboard/modules/PendingOffersModule';
import { CompletedGigsModule } from '@/components/dashboard/modules/CompletedGigsModule';

export const moduleRegistry = new Map<string, DashboardModule>([
  ['upcoming-gigs', {
    id: 'upcoming-gigs',
    title: 'Upcoming Gigs',
    component: UpcomingGigsModule,
    defaultSize: {
      mobile: { cols: 1, rows: 2 },
      tablet: { cols: 1, rows: 2 },
      desktop: { cols: 2, rows: 2 }
    }
  }],
  ['recent-repertoire', {
    id: 'recent-repertoire',
    title: 'Recently Added',
    component: RecentRepertoireModule,
    defaultSize: {
      mobile: { cols: 1, rows: 2 },
      tablet: { cols: 1, rows: 2 },
      desktop: { cols: 2, rows: 2 }
    }
  }],
  ['pending-offers', {
    id: 'pending-offers',
    title: 'Pending Offers',
    component: PendingOffersModule,
    defaultSize: {
      mobile: { cols: 1, rows: 1 },
      tablet: { cols: 1, rows: 1 },
      desktop: { cols: 2, rows: 1 }
    }
  }],
  ['completed-gigs', {
    id: 'completed-gigs',
    title: 'Completed Gigs',
    component: CompletedGigsModule,
    defaultSize: {
      mobile: { cols: 1, rows: 1 },
      tablet: { cols: 1, rows: 1 },
      desktop: { cols: 2, rows: 1 }
    }
  }]
]);