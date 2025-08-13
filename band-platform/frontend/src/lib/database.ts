/**
 * Offline database service using IndexedDB for chart storage
 * Provides offline access to downloaded charts
 */

export interface StoredChart {
  id: string;
  title: string;
  key?: string;
  band_id: number;
  accessible_to_user: boolean;
  file_type: string;
  file_url: string;
  file_data: ArrayBuffer;
  created_at: Date;
  updated_at: Date;
}

class OfflineStorage {
  private dbName = 'soleil-charts';
  private dbVersion = 1;
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        // Create charts store
        if (!db.objectStoreNames.contains('charts')) {
          const chartStore = db.createObjectStore('charts', { keyPath: 'id' });
          chartStore.createIndex('title', 'title', { unique: false });
          chartStore.createIndex('key', 'key', { unique: false });
        }
      };
    });
  }

  private async ensureDB(): Promise<IDBDatabase> {
    if (!this.db) {
      await this.init();
    }
    if (!this.db) {
      throw new Error('Failed to initialize database');
    }
    return this.db;
  }

  async storeChart(chart: StoredChart): Promise<void> {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['charts'], 'readwrite');
      const store = transaction.objectStore('charts');
      const request = store.put(chart);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async getChart(id: string): Promise<StoredChart | null> {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['charts'], 'readonly');
      const store = transaction.objectStore('charts');
      const request = store.get(id);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result || null);
    });
  }

  async getAllCharts(): Promise<StoredChart[]> {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['charts'], 'readonly');
      const store = transaction.objectStore('charts');
      const request = store.getAll();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  async removeChart(id: string): Promise<void> {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['charts'], 'readwrite');
      const store = transaction.objectStore('charts');
      const request = store.delete(id);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async clearAllCharts(): Promise<void> {
    const db = await this.ensureDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(['charts'], 'readwrite');
      const store = transaction.objectStore('charts');
      const request = store.clear();

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async getStorageInfo(): Promise<{ used: number; available: number }> {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      const estimate = await navigator.storage.estimate();
      return {
        used: estimate.usage || 0,
        available: estimate.quota || 0,
      };
    }
    return { used: 0, available: 0 };
  }
}

// Export singleton instance
export const offlineStorage = new OfflineStorage();