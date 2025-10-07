/**
 * Algolia Search Integration Hook
 * Provides instant search for 7.31M Florida properties
 */
import React, { useEffect, useState, useCallback, useRef } from 'react';
import algoliasearch from 'algoliasearch/lite';
import { InstantSearch, SearchBox, Hits, Configure, Pagination } from 'react-instantsearch-dom';

// Algolia configuration
const ALGOLIA_APP_ID = process.env.VITE_ALGOLIA_APP_ID || 'YOUR_APP_ID';
const ALGOLIA_SEARCH_KEY = process.env.VITE_ALGOLIA_SEARCH_KEY || 'YOUR_SEARCH_KEY';
const ALGOLIA_INDEX_NAME = 'florida_properties';

// Initialize Algolia client
const searchClient = algoliasearch(ALGOLIA_APP_ID, ALGOLIA_SEARCH_KEY);

interface AlgoliaProperty {
  objectID: string;
  parcel_id: string;
  owner_name: string;
  phy_addr1: string;
  phy_city: string;
  phy_zipcd: string;
  county: string;
  just_value: number;
  sale_price: number;
  year_built: number;
  total_living_area: number;
  bedrooms: number;
  bathrooms: number;
  _highlightResult?: any;
  _snippetResult?: any;
  _rankingInfo?: any;
}

interface SearchState {
  query: string;
  page: number;
  hitsPerPage: number;
  filters: string;
  facets: string[];
}

interface SearchResults {
  hits: AlgoliaProperty[];
  nbHits: number;
  page: number;
  nbPages: number;
  hitsPerPage: number;
  processingTimeMS: number;
  query: string;
  facets?: Record<string, Record<string, number>>;
}

interface UseAlgoliaSearchOptions {
  hitsPerPage?: number;
  facets?: string[];
  filters?: Record<string, any>;
  enablePersonalization?: boolean;
  enableAnalytics?: boolean;
}

/**
 * Custom hook for Algolia search integration
 */
export function useAlgoliaSearch(options: UseAlgoliaSearchOptions = {}) {
  const {
    hitsPerPage = 20,
    facets = ['county', 'phy_city', 'bedrooms', 'bathrooms'],
    filters: initialFilters = {},
    enablePersonalization = false,
    enableAnalytics = true
  } = options;

  const [searchState, setSearchState] = useState<SearchState>({
    query: '',
    page: 0,
    hitsPerPage,
    filters: '',
    facets
  });

  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * Build Algolia filter string from filter object
   */
  const buildFilterString = useCallback((filters: Record<string, any>): string => {
    const filterParts: string[] = [];

    // County filter
    if (filters.county && filters.county !== 'all') {
      filterParts.push(`county:"${filters.county.toUpperCase()}"`);
    }

    // Price range filter
    if (filters.minPrice || filters.maxPrice) {
      const min = filters.minPrice || 0;
      const max = filters.maxPrice || 999999999;
      filterParts.push(`just_value:${min} TO ${max}`);
    }

    // Bedrooms filter
    if (filters.bedrooms) {
      filterParts.push(`bedrooms >= ${filters.bedrooms}`);
    }

    // Bathrooms filter
    if (filters.bathrooms) {
      filterParts.push(`bathrooms >= ${filters.bathrooms}`);
    }

    // Year built filter
    if (filters.yearBuiltMin || filters.yearBuiltMax) {
      const min = filters.yearBuiltMin || 1800;
      const max = filters.yearBuiltMax || new Date().getFullYear();
      filterParts.push(`year_built:${min} TO ${max}`);
    }

    // Property type filter
    if (filters.propertyType && filters.propertyType !== 'all') {
      filterParts.push(`use:"${filters.propertyType}"`);
    }

    // Living area filter
    if (filters.minSqft || filters.maxSqft) {
      const min = filters.minSqft || 0;
      const max = filters.maxSqft || 999999;
      filterParts.push(`total_living_area:${min} TO ${max}`);
    }

    return filterParts.join(' AND ');
  }, []);

  /**
   * Perform search with debouncing
   */
  const search = useCallback(async (
    query: string,
    filters: Record<string, any> = {},
    page: number = 0
  ) => {
    // Cancel previous search
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Debounce search
    searchTimeoutRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        // Create new abort controller
        abortControllerRef.current = new AbortController();

        // Build filter string
        const filterString = buildFilterString(filters);

        // Update search state
        setSearchState({
          query,
          page,
          hitsPerPage,
          filters: filterString,
          facets
        });

        // Perform search
        const index = searchClient.initIndex(ALGOLIA_INDEX_NAME);
        const searchResults = await index.search<AlgoliaProperty>(query, {
          page,
          hitsPerPage,
          filters: filterString,
          facets,
          attributesToRetrieve: [
            'parcel_id',
            'owner_name',
            'phy_addr1',
            'phy_city',
            'phy_zipcd',
            'county',
            'just_value',
            'sale_price',
            'year_built',
            'total_living_area',
            'bedrooms',
            'bathrooms'
          ],
          attributesToHighlight: [
            'owner_name',
            'phy_addr1',
            'phy_city'
          ],
          highlightPreTag: '<mark>',
          highlightPostTag: '</mark>',
          enablePersonalization,
          analytics: enableAnalytics,
          clickAnalytics: enableAnalytics
        });

        setResults(searchResults);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Search failed');
          console.error('Algolia search error:', err);
        }
      } finally {
        setLoading(false);
      }
    }, 300); // 300ms debounce
  }, [hitsPerPage, facets, buildFilterString, enablePersonalization, enableAnalytics]);

  /**
   * Get search suggestions
   */
  const getSuggestions = useCallback(async (query: string): Promise<string[]> => {
    if (!query || query.length < 2) {
      return [];
    }

    try {
      const index = searchClient.initIndex(ALGOLIA_INDEX_NAME);
      const results = await index.search<AlgoliaProperty>(query, {
        hitsPerPage: 5,
        attributesToRetrieve: ['phy_addr1', 'phy_city', 'owner_name'],
        attributesToHighlight: []
      });

      // Extract unique suggestions
      const suggestions = new Set<string>();

      results.hits.forEach(hit => {
        if (hit.phy_addr1) suggestions.add(hit.phy_addr1);
        if (hit.phy_city) suggestions.add(hit.phy_city);
        if (hit.owner_name) suggestions.add(hit.owner_name);
      });

      return Array.from(suggestions).slice(0, 10);
    } catch (err) {
      console.error('Failed to get suggestions:', err);
      return [];
    }
  }, []);

  /**
   * Get facet values for filtering
   */
  const getFacetValues = useCallback(async (facetName: string): Promise<Record<string, number>> => {
    try {
      const index = searchClient.initIndex(ALGOLIA_INDEX_NAME);
      const results = await index.search('', {
        facets: [facetName],
        hitsPerPage: 0,
        attributesToRetrieve: []
      });

      return results.facets?.[facetName] || {};
    } catch (err) {
      console.error(`Failed to get facet values for ${facetName}:`, err);
      return {};
    }
  }, []);

  /**
   * Clear search results
   */
  const clearSearch = useCallback(() => {
    setSearchState({
      query: '',
      page: 0,
      hitsPerPage,
      filters: '',
      facets
    });
    setResults(null);
    setError(null);
  }, [hitsPerPage, facets]);

  /**
   * Go to specific page
   */
  const goToPage = useCallback((page: number) => {
    if (searchState.query || searchState.filters) {
      search(searchState.query, initialFilters, page);
    }
  }, [searchState.query, searchState.filters, initialFilters, search]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    // Search functions
    search,
    clearSearch,
    getSuggestions,
    getFacetValues,
    goToPage,

    // Search state
    searchState,
    results,
    loading,
    error,

    // Pagination helpers
    currentPage: results?.page || 0,
    totalPages: results?.nbPages || 0,
    totalHits: results?.nbHits || 0,
    hasNextPage: (results?.page || 0) < (results?.nbPages || 0) - 1,
    hasPreviousPage: (results?.page || 0) > 0,

    // Navigation functions
    nextPage: () => goToPage((results?.page || 0) + 1),
    previousPage: () => goToPage((results?.page || 0) - 1)
  };
}

/**
 * Algolia search provider component
 */
export function AlgoliaSearchProvider({ children }: { children: React.ReactNode }) {
  return (
    <InstantSearch searchClient={searchClient} indexName={ALGOLIA_INDEX_NAME}>
      {children}
    </InstantSearch>
  );
}

/**
 * Export Algolia components for direct use
 */
export { SearchBox, Hits, Configure, Pagination } from 'react-instantsearch-dom';