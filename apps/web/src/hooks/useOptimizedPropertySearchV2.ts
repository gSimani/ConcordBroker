import { useInfiniteQuery, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { debounce } from 'lodash';

interface PropertySearchOptions {
  address?: string;
  city?: string;
  zip_code?: string;
  owner?: string;
  min_value?: number;
  max_value?: number;
  county?: string;
  limit?: number;
  offset?: number;
}

interface PropertySearchResponse {
  data: any[];
  total: number;
  pagination?: {
    total: number;
    page: number;
    limit: number;
    has_more: boolean;
  };
  response_time_ms?: number;
  cached?: boolean;
}

// Configuration for optimized performance
const DEFAULT_PAGE_SIZE = 20;
const API_BASE_URL = 'http://localhost:8000/api/properties/search';
const STALE_TIME = 5 * 60 * 1000; // 5 minutes
const GC_TIME = 30 * 60 * 1000; // 30 minutes

// Generate query key for React Query
const generateQueryKey = (options: PropertySearchOptions) => {
  const { offset, limit, ...searchParams } = options;
  return ['properties', 'search', searchParams];
};

// Generate pagination key for infinite query
const generateInfiniteQueryKey = (options: PropertySearchOptions) => {
  const { offset, limit, ...searchParams } = options;
  return ['properties', 'infinite', searchParams];
};

// API function for fetching properties
const fetchProperties = async (options: PropertySearchOptions): Promise<PropertySearchResponse> => {
  const params = new URLSearchParams();

  Object.entries(options).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, String(value));
    }
  });

  const response = await fetch(`${API_BASE_URL}?${params.toString()}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

// Hook for basic property search with pagination
export function useOptimizedPropertySearch(searchOptions: PropertySearchOptions = {}) {
  const finalOptions = {
    limit: DEFAULT_PAGE_SIZE,
    offset: 0,
    ...searchOptions,
  };

  const queryKey = generateQueryKey(finalOptions);

  const {
    data,
    isLoading,
    error,
    refetch,
    isFetching,
    isStale
  } = useQuery({
    queryKey,
    queryFn: () => fetchProperties(finalOptions),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    enabled: true,
    retry: 2,
    refetchOnWindowFocus: false,
  });

  const properties = data?.data || [];
  const total = data?.total || 0;
  const responseTime = data?.response_time_ms;
  const cached = data?.cached || isStale;

  return {
    properties,
    total,
    loading: isLoading || isFetching,
    error: error?.message || null,
    cached,
    responseTime,
    refetch,
    searchOptions: finalOptions
  };
}

// Hook for infinite scroll property search
export function useInfinitePropertySearch(searchOptions: Omit<PropertySearchOptions, 'offset'> = {}) {
  const baseOptions = {
    limit: DEFAULT_PAGE_SIZE,
    ...searchOptions,
  };

  const queryKey = generateInfiniteQueryKey(baseOptions);

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
    isStale
  } = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam = 0 }) =>
      fetchProperties({ ...baseOptions, offset: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      const currentOffset = (allPages.length - 1) * baseOptions.limit!;
      const hasMore = lastPage.pagination?.has_more ||
                     (currentOffset + baseOptions.limit!) < lastPage.total;

      return hasMore ? currentOffset + baseOptions.limit! : undefined;
    },
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
    retry: 2,
    refetchOnWindowFocus: false,
  });

  // Flatten all pages into a single array
  const properties = useMemo(() => {
    return data?.pages.flatMap(page => page.data) || [];
  }, [data?.pages]);

  const total = data?.pages[0]?.total || 0;
  const responseTime = data?.pages[0]?.response_time_ms;
  const cached = data?.pages[0]?.cached || isStale;

  return {
    properties,
    total,
    loading: isLoading,
    error: error?.message || null,
    cached,
    responseTime,
    hasNextPage: !!hasNextPage,
    isLoadingMore: isFetchingNextPage,
    loadMore: fetchNextPage,
    refetch,
    searchOptions: baseOptions
  };
}

// Hook with debounced search functionality
export function useDebouncedPropertySearch(
  searchOptions: PropertySearchOptions = {},
  debounceMs: number = 300
) {
  const queryClient = useQueryClient();

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce((options: PropertySearchOptions) => {
      const queryKey = generateQueryKey({ limit: DEFAULT_PAGE_SIZE, offset: 0, ...options });
      queryClient.prefetchQuery({
        queryKey,
        queryFn: () => fetchProperties({ limit: DEFAULT_PAGE_SIZE, offset: 0, ...options }),
        staleTime: STALE_TIME,
      });
    }, debounceMs),
    [queryClient, debounceMs]
  );

  // Regular search hook
  const searchResult = useOptimizedPropertySearch(searchOptions);

  // Trigger debounced search when options change
  const search = useCallback((options: PropertySearchOptions) => {
    debouncedSearch(options);
  }, [debouncedSearch]);

  return {
    ...searchResult,
    search
  };
}

// Hook for property suggestions/autocomplete
export function usePropertySuggestions(field: string, query: string) {
  const {
    data,
    isLoading,
    error
  } = useQuery({
    queryKey: ['properties', 'suggestions', field, query],
    queryFn: async () => {
      if (!query || query.length < 2) return [];

      const response = await fetch(
        `${API_BASE_URL}/suggestions?field=${field}&query=${encodeURIComponent(query)}`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return response.json();
    },
    enabled: query.length >= 2,
    staleTime: 10 * 60 * 1000, // 10 minutes for suggestions
    gcTime: 30 * 60 * 1000,
  });

  return {
    suggestions: data || [],
    loading: isLoading,
    error: error?.message || null
  };
}

// Hook for prefetching common searches
export function usePrefetchCommonSearches() {
  const queryClient = useQueryClient();

  const prefetchCommonSearches = useCallback(async () => {
    const commonSearches = [
      { county: 'BROWARD' },
      { county: 'MIAMI-DADE' },
      { county: 'PALM BEACH' },
      { min_value: 100000, max_value: 500000 },
      { min_value: 500000, max_value: 1000000 },
    ];

    const prefetchPromises = commonSearches.map(options =>
      queryClient.prefetchQuery({
        queryKey: generateQueryKey({ limit: DEFAULT_PAGE_SIZE, offset: 0, ...options }),
        queryFn: () => fetchProperties({ limit: DEFAULT_PAGE_SIZE, offset: 0, ...options }),
        staleTime: STALE_TIME,
      })
    );

    await Promise.all(prefetchPromises);
  }, [queryClient]);

  return { prefetchCommonSearches };
}

// Hook for cache management
export function usePropertySearchCache() {
  const queryClient = useQueryClient();

  const clearCache = useCallback(() => {
    queryClient.removeQueries({ queryKey: ['properties'] });
  }, [queryClient]);

  const invalidateCache = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['properties'] });
  }, [queryClient]);

  const getCacheStats = useCallback(() => {
    const queryCache = queryClient.getQueryCache();
    const queries = queryCache.findAll({ queryKey: ['properties'] });

    return {
      totalQueries: queries.length,
      stalQueries: queries.filter(query => query.isStale()).length,
      errorQueries: queries.filter(query => query.state.status === 'error').length,
      loadingQueries: queries.filter(query => query.state.status === 'pending').length
    };
  }, [queryClient]);

  return {
    clearCache,
    invalidateCache,
    getCacheStats
  };
}