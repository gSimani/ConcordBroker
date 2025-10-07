import { useState, useEffect, useCallback, useRef } from 'react';
import { parcelService } from '@/lib/supabase';

// Cache configuration
const CACHE_TTL = 60000; // 1 minute
const cache = new Map<string, { data: any; timestamp: number }>();

// Request deduplication
const pendingRequests = new Map<string, Promise<any>>();

interface OptimizedFilters {
  county?: string;
  city?: string;
  limit?: number;
  offset?: number;
  propertyType?: string;
  minPrice?: number;
  maxPrice?: number;
}

export function useOptimizedSupabase(initialFilters: OptimizedFilters = {}) {
  const [properties, setProperties] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  // Use refs for optimization
  const abortControllerRef = useRef<AbortController | null>(null);
  const loadedPagesRef = useRef(new Set<number>());

  // Generate cache key
  const getCacheKey = (filters: OptimizedFilters) => {
    return JSON.stringify(filters);
  };

  // Check if cache is valid
  const isCacheValid = (timestamp: number) => {
    return Date.now() - timestamp < CACHE_TTL;
  };

  // Optimized fetch with caching and deduplication
  const fetchOptimized = useCallback(async (filters: OptimizedFilters) => {
    const cacheKey = getCacheKey(filters);

    // Check cache first
    const cached = cache.get(cacheKey);
    if (cached && isCacheValid(cached.timestamp)) {
      console.log('Using cached data');
      setProperties(cached.data.properties);
      setTotal(cached.data.total);
      return cached.data;
    }

    // Check if request is already pending
    const pending = pendingRequests.get(cacheKey);
    if (pending) {
      console.log('Request already pending, waiting...');
      return pending;
    }

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    // Create request promise
    const request = (async () => {
      setLoading(true);
      setError(null);

      try {
        // Optimized query - fetch only needed fields
        const result = await parcelService.getParcels({
          county: filters.county || 'BROWARD',
          city: filters.city,
          propertyType: filters.propertyType,
          minPrice: filters.minPrice,
          maxPrice: filters.maxPrice,
          limit: filters.limit || 50, // Reduced default limit
          offset: filters.offset || 0
        });

        if (result.error) throw result.error;

        const data = {
          properties: result.data || [],
          total: result.count || 0
        };

        // Update cache
        cache.set(cacheKey, {
          data,
          timestamp: Date.now()
        });

        // Clean old cache entries
        if (cache.size > 50) {
          const oldestKey = cache.keys().next().value;
          cache.delete(oldestKey);
        }

        setProperties(data.properties);
        setTotal(data.total);

        return data;
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          console.error('Fetch error:', err);
          setError(err.message || 'Failed to fetch properties');
        }
        throw err;
      } finally {
        setLoading(false);
        pendingRequests.delete(cacheKey);
      }
    })();

    // Store pending request
    pendingRequests.set(cacheKey, request);

    return request;
  }, []);

  // Virtual scrolling support
  const loadPage = useCallback(async (pageNumber: number, pageSize: number = 50) => {
    if (loadedPagesRef.current.has(pageNumber)) {
      console.log(`Page ${pageNumber} already loaded`);
      return;
    }

    const offset = pageNumber * pageSize;
    await fetchOptimized({
      county: 'BROWARD',
      limit: pageSize,
      offset
    });

    loadedPagesRef.current.add(pageNumber);
  }, [fetchOptimized]);

  // Prefetch next page for smoother scrolling
  const prefetchNext = useCallback((currentOffset: number, limit: number) => {
    const nextOffset = currentOffset + limit;
    const filters = {
      county: 'BROWARD',
      limit,
      offset: nextOffset
    };

    const cacheKey = getCacheKey(filters);
    const cached = cache.get(cacheKey);

    if (!cached || !isCacheValid(cached.timestamp)) {
      // Prefetch in background
      fetchOptimized(filters).catch(() => {
        // Silently handle prefetch errors
      });
    }
  }, [fetchOptimized]);

  // Search with debouncing
  const searchDebounced = useCallback((searchTerm: string, delay: number = 300) => {
    const timeoutId = setTimeout(() => {
      fetchOptimized({
        county: 'BROWARD',
        city: searchTerm,
        limit: 50
      });
    }, delay);

    return () => clearTimeout(timeoutId);
  }, [fetchOptimized]);

  // Load initial data
  useEffect(() => {
    fetchOptimized({
      county: 'BROWARD',
      limit: 50,
      offset: 0
    });
  }, []);

  return {
    properties,
    loading,
    error,
    total,
    fetchOptimized,
    loadPage,
    prefetchNext,
    searchDebounced,
    clearCache: () => cache.clear()
  };
}