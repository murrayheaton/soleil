/**
 * API service for communicating with the SOLEil backend
 * Handles authentication, charts, and Google Drive integration
 */

// Chart interface matching backend model
export interface Chart {
  id: string;
  filename: string;
  title: string;
  instruments: string[];
  key?: string;
  tempo?: string;
  time_signature?: string;
  difficulty?: string;
  mime_type: string;
  size: number;
  created_at?: string;
  modified_at?: string;
  google_drive_id: string;
  download_url: string;
  // Legacy fields for backwards compatibility with existing code
  band_id?: string | number;
  composer?: string;
  genre?: string;
  instrumentation?: string[];
  google_drive_file_id?: string;
  file_path?: string;
  updated_at?: string;
}

export interface ChartListResponse {
  charts: Chart[];
  total: number;
  limit: number;
  offset: number;
}

export interface GoogleAuthStatus {
  authenticated: boolean;
  message: string;
  auth_url?: string;
}

export interface ChartFolder {
  id: string;
  name: string;
  path: string;
}

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public endpoint: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class AuthenticationError extends APIError {
  constructor(message: string, endpoint: string) {
    super(message, 401, endpoint);
    this.name = 'AuthenticationError';
  }
}

class APIService {
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'https://solepower.live';
    // Ensure baseURL doesn't end with /api
    this.baseURL = this.baseURL.replace(/\/api$/, '');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}/api${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage: string;
        
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorJson.message || response.statusText;
        } catch {
          errorMessage = errorText || response.statusText;
        }

        if (response.status === 401) {
          throw new AuthenticationError(errorMessage, endpoint);
        }
        
        throw new APIError(errorMessage, response.status, endpoint);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return response as unknown as T;
      }
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(
        `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0,
        endpoint
      );
    }
  }

  // Chart API methods
  async listCharts(options: {
    folder_id?: string;
    instrument?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<ChartListResponse> {
    const params = new URLSearchParams();
    
    if (options.folder_id) params.append('folder_id', options.folder_id);
    if (options.instrument) params.append('instrument', options.instrument);
    if (options.limit) params.append('limit', options.limit.toString());
    if (options.offset) params.append('offset', options.offset.toString());
    
    const query = params.toString();
    const endpoint = `/modules/content/charts${query ? `?${query}` : ''}`;
    
    return this.request<ChartListResponse>(endpoint);
  }

  async getChart(chartId: string): Promise<Chart> {
    return this.request<Chart>(`/modules/content/charts/${chartId}`);
  }

  async downloadChart(chart: Chart): Promise<Blob> {
    const url = `${this.baseURL}/api/modules/content/charts/${chart.id}/download`;
    
    const response = await fetch(url);
    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage: string;
      
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.detail || errorJson.message || response.statusText;
      } catch {
        errorMessage = errorText || response.statusText;
      }

      if (response.status === 401) {
        throw new AuthenticationError(errorMessage, `/charts/${chart.id}/download`);
      }
      
      throw new APIError(errorMessage, response.status, `/charts/${chart.id}/download`);
    }
    
    return response.blob();
  }

  async searchCharts(options: {
    query: string;
    folder_id?: string;
    instrument?: string;
    limit?: number;
  }): Promise<ChartListResponse> {
    const params = new URLSearchParams();
    params.append('query', options.query);
    
    if (options.folder_id) params.append('folder_id', options.folder_id);
    if (options.instrument) params.append('instrument', options.instrument);
    if (options.limit) params.append('limit', options.limit.toString());
    
    return this.request<ChartListResponse>(`/modules/content/charts/search?${params.toString()}`);
  }

  async getChartFolders(): Promise<ChartFolder[]> {
    const response = await this.request<{ folders: ChartFolder[] }>('/modules/content/folders');
    return response.folders;
  }

  // Google Auth methods
  async getGoogleAuthUrl(): Promise<{ auth_url: string; message: string }> {
    return this.request<{ auth_url: string; message: string }>('/modules/content/auth/google/url');
  }

  async handleGoogleCallback(authorizationCode: string): Promise<{ message: string }> {
    return this.request<{ message: string }>('/modules/content/auth/google/callback', {
      method: 'POST',
      body: JSON.stringify({ authorization_code: authorizationCode }),
    });
  }

  async checkGoogleAuthStatus(): Promise<GoogleAuthStatus> {
    return this.request<GoogleAuthStatus>('/modules/content/auth/google/status');
  }

  // Helper method to check if an error is an authentication error
  isAuthError(error: unknown): error is AuthenticationError {
    return error instanceof AuthenticationError;
  }

  // Helper method to get auth URL on auth errors
  async getAuthUrlOnError(): Promise<string> {
    try {
      const status = await this.checkGoogleAuthStatus();
      return status.auth_url || '';
    } catch (error) {
      console.error('Failed to get auth URL:', error);
      return '';
    }
  }
}

// Export singleton instance
export const apiService = new APIService();