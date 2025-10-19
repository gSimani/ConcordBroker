/**
 * Advanced Property Search Hook
 * Frontend integration for property filters from Min Value to Sub-Usage Code
 * Optimized for performance with debouncing and intelligent caching
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useValueDebounce } from './useDebounce';

export interface PropertySearchFilters {
  // Value filters (Min Value input field)
  minValue?: number;
  maxValue?: number;

  // Size filters
  minSqft?: number;
  maxSqft?: number;
  minLandSqft?: number;
  maxLandSqft?: number;

  // Year filters
  minYearBuilt?: number;
  maxYearBuilt?: number;

  // Property type filters (Sub-Usage Code input field - final filter)
  propertyUseCode?: string;
  subUsageCode?: string;
  propertyType?: string;

  // Location filters
  county?: string;
  city?: string;
  zipCode?: string;

  // Assessment filters
  minAssessedValue?: number;
  maxAssessedValue?: number;
  taxExempt?: boolean;

  // Sales history filters
  recentlySold?: boolean;
  saleDateFrom?: string;
  saleDateTo?: string;

  // Feature filters
  hasPool?: boolean;
  waterfront?: boolean;
  gatedCommunity?: boolean;

  // Phase 1 filters - using existing database columns
  hasHomesteadExemption?: boolean;  // homestead_exemption = 'Y'
  qualifiedSaleOnly?: boolean;  // qual_cd1 = 'Q'
  excludeMultiParcel?: boolean;  // multi_par_sal1 = 'N' or NULL
  subdivision?: string;  // subdivision ILIKE '%value%'
  zoning?: string;  // zoning ILIKE '%value%'

  // Pagination and sorting
  limit?: number;
  offset?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PropertySearchResult {
  parcelId: string;
  ownerName: string;
  address: string;
  city: string;
  county: string;
  zipCode: string;
  justValue: number;
  assessedValue: number;
  landValue: number;
  buildingValue: number;
  landSqft: number;
  buildingSqft: number;
  yearBuilt: number;
  propertyUseCode: string;
  propertyUseDescription: string;
  subUsageCode: string;
  saleDate?: string;
  salePrice?: number;
  pricePerSqft?: number;
  landPricePerSqft?: number;
  assessmentRatio?: number;
  fullAddress: string;
}

export interface SearchMetadata {
  totalCount: number;
  executionTimeSeconds: number;
  filtersApplied: Record<string, any>;
  queryHash: string;
  hasMore: boolean;
}

export interface UseAdvancedPropertySearchResult {
  // Data
  results: PropertySearchResult[];
  metadata: SearchMetadata | null;

  // State
  isLoading: boolean;
  isError: boolean;
  error: string | null;

  // Actions
  search: (filters: PropertySearchFilters) => Promise<void>;
  clearResults: () => void;
  loadMore: () => Promise<void>;

  // Filter helpers
  setFilters: (filters: Partial<PropertySearchFilters>) => void;
  resetFilters: () => void;
  filters: PropertySearchFilters;

  // Suggestions
  suggestions: {
    propertyUseCodes: Array<{ code: string; description: string }>;
    valueRanges: Array<{ label: string; min: number; max?: number }>;
    sqftRanges: Array<{ label: string; min: number; max?: number }>;
    commonCities: string[];
  };
}

const DEFAULT_FILTERS: PropertySearchFilters = {
  limit: 500, // FIXED: Increased from 100 to 500 for better UX
  offset: 0,
  sortBy: 'just_value',
  sortOrder: 'desc'
};

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:3005';
const API_KEY = 'concordbroker-mcp-key-claude';

export const useAdvancedPropertySearch = (): UseAdvancedPropertySearchResult => {
  // State management
  const [filters, setFiltersState] = useState<PropertySearchFilters>(DEFAULT_FILTERS);
  const [results, setResults] = useState<PropertySearchResult[]>([]);
  const [metadata, setMetadata] = useState<SearchMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<any>({});

  // Debounced filters for automatic search
  const debouncedFilters = useValueDebounce(filters, 800);

  // Property use codes mapping
  const propertyUseCodes = useMemo(() => [
    { code: '01', description: 'Single Family' },
    { code: '02', description: 'Mobile Home' },
    { code: '03', description: 'Multi-Family' },
    { code: '04', description: 'Condominium' },
    { code: '05', description: 'Cooperative' },
    { code: '10', description: 'Vacant Commercial' },
    { code: '11', description: 'Stores/Office, One Story' },
    { code: '12', description: 'Mixed Use Commercial' },
    { code: '20', description: 'Vacant Industrial' },
    { code: '21', description: 'Light Manufacturing' },
    { code: '30', description: 'Institutional' },
    { code: '31', description: 'Hospitals, Nursing Homes' }
  ], []);

  // Value and size range suggestions
  const valueRanges = useMemo(() => [
    { label: 'Under $200K', min: 0, max: 200000 },
    { label: '$200K - $500K', min: 200000, max: 500000 },
    { label: '$500K - $1M', min: 500000, max: 1000000 },
    { label: 'Over $1M', min: 1000000 }
  ], []);

  const sqftRanges = useMemo(() => [
    { label: 'Under 1,000 sq ft', min: 0, max: 1000 },
    { label: '1,000 - 2,000 sq ft', min: 1000, max: 2000 },
    { label: '2,000 - 3,000 sq ft', min: 2000, max: 3000 },
    { label: 'Over 3,000 sq ft', min: 3000 }
  ], []);

  const commonCities = useMemo(() => [
    'Miami', 'Fort Lauderdale', 'Hollywood', 'Pembroke Pines',
    'Coral Springs', 'Miramar', 'Davie', 'Plantation', 'Sunrise'
  ], []);

  // API request helper
  const makeApiRequest = useCallback(async (endpoint: string, options: RequestInit = {}) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY,
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }, []);

  // Main search function
  const search = useCallback(async (searchFilters: PropertySearchFilters) => {
    setIsLoading(true);
    setIsError(false);
    setError(null);

    try {
      // Validate and clean filters
      const cleanFilters = validateAndCleanFilters(searchFilters);

      // Make API request
      const response = await makeApiRequest('/api/properties/search', {
        method: 'POST',
        body: JSON.stringify(cleanFilters)
      });

      if (response.success) {
        setResults(response.data || []);
        setMetadata(response.metadata || null);
      } else {
        throw new Error(response.error || 'Search failed');
      }
    } catch (err) {
      setIsError(true);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setResults([]);
      setMetadata(null);
    } finally {
      setIsLoading(false);
    }
  }, [makeApiRequest]);

  // Load more results (pagination)
  const loadMore = useCallback(async () => {
    if (!metadata?.hasMore || isLoading) return;

    const newFilters = {
      ...filters,
      offset: (filters.offset || 0) + (filters.limit || 100)
    };

    setIsLoading(true);
    try {
      const response = await makeApiRequest('/api/properties/search', {
        method: 'POST',
        body: JSON.stringify(newFilters)
      });

      if (response.success) {
        setResults(prev => [...prev, ...(response.data || [])]);
        setMetadata(response.metadata || null);
        setFiltersState(newFilters);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load more results');
    } finally {
      setIsLoading(false);
    }
  }, [filters, metadata, isLoading, makeApiRequest]);

  // Filter management functions
  const setFilters = useCallback((newFilters: Partial<PropertySearchFilters>) => {
    setFiltersState(prev => ({
      ...prev,
      ...newFilters,
      offset: 0 // Reset pagination when filters change
    }));
  }, []);

  const resetFilters = useCallback(() => {
    setFiltersState(DEFAULT_FILTERS);
    setResults([]);
    setMetadata(null);
    setError(null);
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
    setMetadata(null);
    setError(null);
  }, []);

  // Load suggestions on mount
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const response = await makeApiRequest('/api/search/suggestions');
        setSuggestions(response);
      } catch (err) {
        console.warn('Failed to load suggestions:', err);
      }
    };

    loadSuggestions();
  }, [makeApiRequest]);

  // Auto-search when filters change (debounced)
  useEffect(() => {
    const hasFilters = Object.values(debouncedFilters).some(value =>
      value !== undefined && value !== null && value !== ''
    );

    if (hasFilters && Object.keys(debouncedFilters).length > 2) { // More than just limit/offset
      search(debouncedFilters);
    }
  }, [debouncedFilters, search]);

  // Return the hook interface
  return {
    // Data
    results,
    metadata,

    // State
    isLoading,
    isError,
    error,

    // Actions
    search,
    clearResults,
    loadMore,

    // Filter management
    setFilters,
    resetFilters,
    filters,

    // Suggestions
    suggestions: {
      propertyUseCodes,
      valueRanges,
      sqftRanges,
      commonCities: suggestions.commonCities || commonCities
    }
  };
};

// Helper function to validate and clean filters
function validateAndCleanFilters(filters: PropertySearchFilters): PropertySearchFilters {
  const cleaned: PropertySearchFilters = { ...filters };

  // Remove empty string values
  Object.keys(cleaned).forEach(key => {
    if (cleaned[key as keyof PropertySearchFilters] === '') {
      delete cleaned[key as keyof PropertySearchFilters];
    }
  });

  // Validate numeric ranges
  if (cleaned.minValue !== undefined && cleaned.maxValue !== undefined) {
    if (cleaned.minValue > cleaned.maxValue) {
      [cleaned.minValue, cleaned.maxValue] = [cleaned.maxValue, cleaned.minValue];
    }
  }

  if (cleaned.minSqft !== undefined && cleaned.maxSqft !== undefined) {
    if (cleaned.minSqft > cleaned.maxSqft) {
      [cleaned.minSqft, cleaned.maxSqft] = [cleaned.maxSqft, cleaned.minSqft];
    }
  }

  if (cleaned.minYearBuilt !== undefined && cleaned.maxYearBuilt !== undefined) {
    if (cleaned.minYearBuilt > cleaned.maxYearBuilt) {
      [cleaned.minYearBuilt, cleaned.maxYearBuilt] = [cleaned.maxYearBuilt, cleaned.minYearBuilt];
    }
  }

  // Validate year built ranges
  const currentYear = new Date().getFullYear();
  if (cleaned.minYearBuilt !== undefined && cleaned.minYearBuilt < 1800) {
    cleaned.minYearBuilt = 1800;
  }
  if (cleaned.maxYearBuilt !== undefined && cleaned.maxYearBuilt > currentYear) {
    cleaned.maxYearBuilt = currentYear;
  }

  // Validate property use codes (should be 2-digit strings)
  if (cleaned.propertyUseCode && !/^\d{2}$/.test(cleaned.propertyUseCode)) {
    delete cleaned.propertyUseCode;
  }

  // Validate sub-usage codes (should be 2-digit strings)
  if (cleaned.subUsageCode && !/^\d{2}$/.test(cleaned.subUsageCode)) {
    delete cleaned.subUsageCode;
  }

  // Ensure pagination defaults - FIXED: Increased from 100 to 500
  cleaned.limit = cleaned.limit || 500;
  cleaned.offset = cleaned.offset || 0;

  // Ensure sorting defaults
  cleaned.sortBy = cleaned.sortBy || 'just_value';
  cleaned.sortOrder = cleaned.sortOrder || 'desc';

  return cleaned;
}

// Hook for property use code lookup
export const usePropertyUseCodes = () => {
  return useMemo(() => ({
    '01': 'Single Family',
    '02': 'Mobile Home',
    '03': 'Multi-Family',
    '04': 'Condominium',
    '05': 'Cooperative',
    '06': 'Retirement Home',
    '07': 'Manufactured Home',
    '08': 'Miscellaneous Residential',
    '09': 'Multi-Family 10+ Units',
    '10': 'Vacant Commercial',
    '11': 'Stores/Office, One Story',
    '12': 'Mixed Use Commercial',
    '13': 'Department Store',
    '14': 'Supermarket',
    '15': 'Regional Shopping Center',
    '16': 'Community Shopping Center',
    '17': 'Office Building, Multi-Story',
    '18': 'Office Building, One Story',
    '19': 'Professional Service Building',
    '20': 'Vacant Industrial',
    '21': 'Light Manufacturing',
    '22': 'Heavy Industrial',
    '23': 'Mini Warehouse',
    '24': 'Warehouse, Distribution Terminal',
    '25': 'Open Storage',
    '30': 'Institutional',
    '31': 'Hospitals, Nursing Homes',
    '32': 'Educational',
    '33': 'Religious',
    '34': 'Cultural, Entertainment, Recreational',
    '35': 'Governmental'
  }), []);
};

export default useAdvancedPropertySearch;