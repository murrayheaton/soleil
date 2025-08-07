export interface DashboardModule {
  id: string;
  title: string;
  description?: string;
  component: React.ComponentType<ModuleProps>;
  defaultSize: {
    mobile: { cols: number; rows: number };
    tablet: { cols: number; rows: number };
    desktop: { cols: number; rows: number };
  };
  permissions?: string[];
}

export interface ModuleProps {
  userId: string;
}