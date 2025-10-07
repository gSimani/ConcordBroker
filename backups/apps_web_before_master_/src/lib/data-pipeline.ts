/**
 * Fast Data Pipeline for Property Filtering
 * Implements efficient streaming and caching for real-time filter updates
 */

interface FilterCache {
  data: any[];
  timestamp: number;
  query: string;
}

class DataPipeline {
  private cache = new Map<string, FilterCache>();
  private pendingRequests = new Map<string, Promise<any>>();
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes
  private abortControllers = new Map<string, AbortController>();

  /**
   * Creates a cache key from filter parameters
   */
  private getCacheKey(filters: Record<string, any>): string {
    return JSON.stringify(filters);
  }

  /**
   * Checks if cached data is still valid
   */
  private isCacheValid(cached: FilterCache): boolean {
    return Date.now() - cached.timestamp < this.cacheTimeout;
  }

  /**
   * Cancels any pending requests for a given key
   */
  private cancelPendingRequest(key: string): void {
    const controller = this.abortControllers.get(key);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(key);
    }
    this.pendingRequests.delete(key);
  }

  /**
   * Fast parallel fetch with deduplication
   */
  async fetchWithCache(
    url: string,
    filters: Record<string, any>,
    options: RequestInit = {}
  ): Promise<any> {
    const cacheKey = this.getCacheKey({ url, ...filters });

    // Check cache first
    const cached = this.cache.get(cacheKey);
    if (cached && this.isCacheValid(cached)) {
      console.log('Cache hit for:', cacheKey);
      return Promise.resolve(cached.data);
    }

    // Check if request is already pending
    const pending = this.pendingRequests.get(cacheKey);
    if (pending) {
      console.log('Request already pending, reusing:', cacheKey);
      return pending;
    }

    // Cancel any previous request for this key
    this.cancelPendingRequest(cacheKey);

    // Create new abort controller
    const controller = new AbortController();
    this.abortControllers.set(cacheKey, controller);

    // Create new request
    const request = this.performFetch(url, filters, {
      ...options,
      signal: controller.signal
    }).then(data => {
      // Cache the result
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now(),
        query: cacheKey
      });
      
      // Cleanup
      this.pendingRequests.delete(cacheKey);
      this.abortControllers.delete(cacheKey);
      
      return data;
    }).catch(error => {
      // Cleanup on error
      this.pendingRequests.delete(cacheKey);
      this.abortControllers.delete(cacheKey);
      
      if (error.name === 'AbortError') {
        console.log('Request canceled:', cacheKey);
        return [];
      }
      throw error;
    });

    this.pendingRequests.set(cacheKey, request);
    return request;
  }

  /**
   * Performs the actual fetch with optimized parameters
   */
  private async performFetch(
    url: string,
    filters: Record<string, any>,
    options: RequestInit
  ): Promise<any> {
    const params = new URLSearchParams();
    
    // Add filters to params
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== '' && value !== 'all-cities' && value !== 'all-types') {
        params.append(key, value);
      }
    });

    // Add optimization parameters - only if not already set
    if (!params.has('limit')) {
      params.append('limit', '100'); // Default limit for better performance
    }
    params.append('fast', 'true'); // Use fast query mode if available

    const finalUrl = `${url}?${params.toString()}`;
    console.log('Fetching:', finalUrl);

    const response = await fetch(finalUrl, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Batch fetch multiple endpoints in parallel
   */
  async batchFetch(requests: Array<{ url: string; filters: Record<string, any> }>): Promise<any[]> {
    return Promise.all(
      requests.map(req => this.fetchWithCache(req.url, req.filters))
    );
  }

  /**
   * Stream process results as they arrive
   */
  async *streamResults(
    url: string,
    filters: Record<string, any>,
    pageSize = 100
  ): AsyncGenerator<any[], void, unknown> {
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const pageFilters = { ...filters, page, limit: pageSize };
      const data = await this.fetchWithCache(url, pageFilters);
      
      if (data.properties && data.properties.length > 0) {
        yield data.properties;
        hasMore = data.properties.length === pageSize;
        page++;
      } else {
        hasMore = false;
      }
    }
  }

  /**
   * Prefetch common filter combinations
   */
  async prefetchCommon(baseUrl: string): Promise<void> {
    const commonFilters = [
      { city: 'Fort Lauderdale' },
      { city: 'Hollywood' },
      { city: 'Pompano Beach' },
      { propertyType: 'Residential' },
      { propertyType: 'Commercial' }
    ];

    // Prefetch in parallel but don't await
    commonFilters.forEach(filter => {
      this.fetchWithCache(baseUrl, filter).catch(() => {
        // Ignore prefetch errors
      });
    });
  }

  /**
   * Clear cache for specific filters or all
   */
  clearCache(filters?: Record<string, any>): void {
    if (filters) {
      const key = this.getCacheKey(filters);
      this.cache.delete(key);
      this.cancelPendingRequest(key);
    } else {
      this.cache.clear();
      this.pendingRequests.clear();
      this.abortControllers.forEach(controller => controller.abort());
      this.abortControllers.clear();
    }
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; entries: string[] } {
    return {
      size: this.cache.size,
      entries: Array.from(this.cache.keys())
    };
  }
}

// Create singleton instance
export const dataPipeline = new DataPipeline();

/**
 * React hook for using the data pipeline
 */
export function useDataPipeline() {
  return {
    fetchWithCache: dataPipeline.fetchWithCache.bind(dataPipeline),
    batchFetch: dataPipeline.batchFetch.bind(dataPipeline),
    streamResults: dataPipeline.streamResults.bind(dataPipeline),
    prefetchCommon: dataPipeline.prefetchCommon.bind(dataPipeline),
    clearCache: dataPipeline.clearCache.bind(dataPipeline),
    getCacheStats: dataPipeline.getCacheStats.bind(dataPipeline)
  };
}

/**
 * Optimized filter processor
 */
export class FilterProcessor {
  private filterQueue: Array<() => Promise<any>> = [];
  private processing = false;
  private batchSize = 3;
  
  /**
   * Add filter operation to queue
   */
  async addFilter(operation: () => Promise<any>): Promise<any> {
    return new Promise((resolve, reject) => {
      this.filterQueue.push(async () => {
        try {
          const result = await operation();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      
      if (!this.processing) {
        this.processQueue();
      }
    });
  }

  /**
   * Process queued filter operations in batches
   */
  private async processQueue(): Promise<void> {
    if (this.processing || this.filterQueue.length === 0) {
      return;
    }

    this.processing = true;

    while (this.filterQueue.length > 0) {
      const batch = this.filterQueue.splice(0, this.batchSize);
      await Promise.all(batch.map(op => op()));
    }

    this.processing = false;
  }
}

export const filterProcessor = new FilterProcessor();

/**
 * Transform and optimize property data
 */
export function transformPropertyData(data: any): any {
  if (!data) return null;

  // Extract only needed fields for list view
  const optimized = {
    id: data.id,
    parcel_id: data.parcel_id,
    address: data.phy_addr1,
    city: data.phy_city,
    zip: data.phy_zipcd,
    owner: data.own_name,
    value: data.jv,
    sqft: data.tot_lvg_area,
    year_built: data.act_yr_blt,
    property_type: data.dor_uc,
    // Minimal fields for performance
    _full: false
  };

  return optimized;
}

/**
 * Batch transform multiple properties
 */
export function batchTransform(properties: any[]): any[] {
  return properties.map(transformPropertyData);
}