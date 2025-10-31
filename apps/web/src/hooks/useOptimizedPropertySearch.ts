import { useState, useEffect, useCallback, useRef } from 'react';
import { debounce } from 'lodash';

interface PropertySearchOptions {
  address?: string;
  city?: string;
  zip_code?: string;
  owner?: string;
  min_value?: number;
  max_value?: number;
  limit?: number;
  offset?: number;
}

interface PropertySearchResult {
  properties: any[];
  total: number;
  loading: boolean;
  error: string | null;
  cached: boolean;
  responseTime?: number;
}

// Optimized configuration for fast loading
const VIRTUAL_SCROLL_BUFFER = 5;
const ITEMS_PER_PAGE = 20;  // Load less initially for faster response
const AI_OPTIMIZED_API_URL = 'http://localhost:8080/api/properties/search';  // Ultra-fast optimized API with caching

export function useOptimizedPropertySearch() {
  const [searchOptions, setSearchOptions] = useState<PropertySearchOptions>({
    limit: ITEMS_PER_PAGE,
    offset: 0
  });

  const [result, setResult] = useState<PropertySearchResult>({
    properties: [],
    total: 0,
    loading: false,
    error: null,
    cached: false
  });

  const [visibleProperties, setVisibleProperties] = useState<any[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);
  const cacheRef = useRef<Map<string, any>>(new Map());

  // Generate cache key
  const getCacheKey = (options: PropertySearchOptions) => {
    return JSON.stringify(options);
  };

  // Optimized search function with request cancellation
  const performSearch = useCallback(async (options: PropertySearchOptions) => {
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Check local cache first
    const cacheKey = getCacheKey(options);
    const cached = cacheRef.current.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < 60000) { // 1 minute cache
      setResult({
        ...cached.data,
        cached: true
      });
      return;
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    setResult(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Build query string
      const params = new URLSearchParams();
      Object.entries(options).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, String(value));
        }
      });

      // Use correct API endpoint
      const response = await fetch(
        `${AI_OPTIMIZED_API_URL}?${params.toString()}`,
        {
          signal: abortControllerRef.current.signal,
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Cache the result
      cacheRef.current.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      // Limit cache size
      if (cacheRef.current.size > 50) {
        const firstKey = cacheRef.current.keys().next().value;
        cacheRef.current.delete(firstKey);
      }

      // Handle original API response format
      const properties = data.data || [];
      const total = data.total || data.pagination?.total || 0;

      setResult({
        properties: properties,
        total: total,
        loading: false,
        error: null,
        cached: data.cached || false,
        responseTime: data.response_time_ms
      });

      // Update visible properties for virtual scrolling
      setVisibleProperties(properties.slice(0, Math.min(properties.length, ITEMS_PER_PAGE)));

    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Search error:', error);
        setResult(prev => ({
          ...prev,
          loading: false,
          error: error.message || 'Failed to search properties'
        }));
      }
    }
  }, []);

  // Debounced search
  const debouncedSearch = useCallback(
    debounce((options: PropertySearchOptions) => {
      performSearch(options);
    }, 300),
    [performSearch]
  );

  // Search function exposed to components
  const search = useCallback((options: PropertySearchOptions) => {
    setSearchOptions(options);
    debouncedSearch(options);
  }, [debouncedSearch]);

  // Load more for infinite scrolling
  const loadMore = useCallback(() => {
    if (result.loading) return;

    const newOffset = searchOptions.offset! + ITEMS_PER_PAGE;
    if (newOffset < result.total) {
      const newOptions = { ...searchOptions, offset: newOffset };
      setSearchOptions(newOptions);
      performSearch(newOptions);
    }
  }, [searchOptions, result.loading, result.total, performSearch]);

  // Prefetch common searches - disabled for now since endpoint doesn't exist
  const prefetchCommon = useCallback(async () => {
    try {
      // Prefetch endpoint not available in current API
      // Silently skip - will be implemented when backend supports it
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('Prefetch error:', error);
      }
    }
  }, []);

  // Autocomplete function - connects to API autocomplete endpoints
  const autocomplete = useCallback(async (field: string, query: string): Promise<any[]> => {
    if (!query || query.length < 2) return [];

    try {
      const startTime = performance.now();

      // Map field types to API endpoints
      const endpointMap: Record<string, string> = {
        address: '/api/autocomplete/addresses',
        city: '/api/autocomplete/cities',
        owner: '/api/autocomplete/owners',
        zipCode: '/api/autocomplete/zipcodes',
      };

      const endpoint = endpointMap[field] || `/api/autocomplete/addresses`;
      const url = `http://localhost:8080${endpoint}?q=${encodeURIComponent(query)}&limit=20`;

      console.log(`[Autocomplete] ${field}: '${query}' -> ${url}`);

      // Fetch with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        }
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        console.warn(`[Autocomplete] ${field}: HTTP ${response.status}`);
        return [];
      }

      const data = await response.json();
      const results = data.suggestions || data.results || data || [];
      const endTime = performance.now();

      console.log(`[Autocomplete] ${field}: ${results.length} results in ${(endTime - startTime).toFixed(1)}ms`);

      return results;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.warn('[Autocomplete] Request timeout (>5s)');
      } else {
        console.error('[Autocomplete] Error:', error);
      }
      return [];
    }
  }, []);

  // Clear cache
  const clearCache = useCallback(async () => {
    cacheRef.current.clear();
    try {
      // Clear cache endpoint not available in current API
      console.log('Clear cache not implemented');
    } catch (error) {
      console.error('Clear cache error:', error);
    }
  }, []);

  // Virtual scrolling handler
  const handleScroll = useCallback((scrollTop: number, containerHeight: number, itemHeight: number) => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.ceil((scrollTop + containerHeight) / itemHeight);

    const start = Math.max(0, startIndex - VIRTUAL_SCROLL_BUFFER);
    const end = Math.min(result.properties.length, endIndex + VIRTUAL_SCROLL_BUFFER);

    setVisibleProperties(result.properties.slice(start, end));
  }, [result.properties]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Prefetch on mount
  useEffect(() => {
    prefetchCommon();
  }, [prefetchCommon]);

  return {
    ...result,
    visibleProperties,
    search,
    loadMore,
    autocomplete,
    clearCache,
    handleScroll,
    searchOptions
  };
}