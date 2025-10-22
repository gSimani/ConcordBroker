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
  limit: 500,
  offset: 0,
  sortBy: 'just_value',
  sortOrder: 'desc'
};

export const useAdvancedPropertySearch = (): UseAdvancedPropertySearchResult => {
  // State management
  const [filters, setFiltersState] = useState<PropertySearchFilters>(DEFAULT_FILTERS);
  const [results, setResults] = useState<PropertySearchResult[]>([]);
  const [metadata, setMetadata] = useState<SearchMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  // Main search function - FIXED: Using correct API endpoint
  const search = useCallback(async (searchFilters: PropertySearchFilters) => {
    setIsLoading(true);
    setIsError(false);
    setError(null);

    try {
      // Validate and clean filters
      const cleanFilters = validateAndCleanFilters(searchFilters);

      // Transform to API parameters (camelCase → snake_case)
      const apiParams: Record<string, any> = {
        limit: cleanFilters.limit,
        page: Math.floor((cleanFilters.offset || 0) / (cleanFilters.limit || 500)) + 1
      };

      if (cleanFilters.minValue) apiParams.min_value = cleanFilters.minValue;
      if (cleanFilters.maxValue) apiParams.max_value = cleanFilters.maxValue;
      if (cleanFilters.minSqft) apiParams.min_building_sqft = cleanFilters.minSqft;
      if (cleanFilters.maxSqft) apiParams.max_building_sqft = cleanFilters.maxSqft;
      if (cleanFilters.minLandSqft) apiParams.min_land_sqft = cleanFilters.minLandSqft;
      if (cleanFilters.maxLandSqft) apiParams.max_land_sqft = cleanFilters.maxLandSqft;
      if (cleanFilters.minYearBuilt) apiParams.min_year = cleanFilters.minYearBuilt;
      if (cleanFilters.maxYearBuilt) apiParams.max_year = cleanFilters.maxYearBuilt;
      if (cleanFilters.county) apiParams.county = cleanFilters.county;
      if (cleanFilters.city) apiParams.city = cleanFilters.city;
      if (cleanFilters.zipCode) apiParams.zip_code = cleanFilters.zipCode;
      if (cleanFilters.propertyUseCode) apiParams.property_type = cleanFilters.propertyUseCode;
      if (cleanFilters.subUsageCode) apiParams.sub_usage_code = cleanFilters.subUsageCode;
      if (cleanFilters.minAssessedValue) apiParams.min_appraised_value = cleanFilters.minAssessedValue;
      if (cleanFilters.maxAssessedValue) apiParams.max_appraised_value = cleanFilters.maxAssessedValue;

      // FIXED: Using correct endpoint path
      const queryString = new URLSearchParams(apiParams).toString();
      const response = await fetch(`/api/properties/search?${queryString}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        // Transform API response to match expected format
        const transformedResults = (data.data || []).map((item: any) => ({
          parcelId: item.parcel_id || item.id,
          ownerName: item.owner_name || '',
          address: item.address || '',
          city: item.city || '',
          county: item.county || '',
          zipCode: item.zip_code || '',
          justValue: item.just_value || 0,
          assessedValue: item.taxable_value || 0,
          landValue: item.land_value || 0,
          buildingValue: item.building_value || 0,
          landSqft: item.land_sqft || 0,
          buildingSqft: item.living_area || 0,
          yearBuilt: item.year_built || 0,
          propertyUseCode: item.property_type || '',
          propertyUseDescription: getPropertyTypeDescription(item.property_type),
          subUsageCode: item.property_type || '',
          saleDate: item.sale_date || undefined,
          salePrice: item.sale_price || undefined,
          pricePerSqft: item.living_area > 0 ? Math.round(item.just_value / item.living_area) : undefined,
          landPricePerSqft: item.land_sqft > 0 ? Math.round(item.land_value / item.land_sqft) : undefined,
          fullAddress: `${item.address}, ${item.city}, ${item.county}, FL ${item.zip_code}`
        }));

        setResults(transformedResults);
        setMetadata({
          totalCount: data.pagination?.total || 0,
          executionTimeSeconds: 0,
          filtersApplied: apiParams,
          queryHash: JSON.stringify(apiParams),
          hasMore: (data.pagination?.page || 1) < (data.pagination?.totalPages || 1)
        });
      } else {
        throw new Error(data.error || 'Search failed');
      }
    } catch (err) {
      setIsError(true);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setResults([]);
      setMetadata(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load more results (pagination)
  const loadMore = useCallback(async () => {
    if (!metadata?.hasMore || isLoading) return;

    const newFilters = {
      ...filters,
      offset: (filters.offset || 0) + (filters.limit || 500)
    };

    await search(newFilters);
    setFiltersState(newFilters);
  }, [filters, metadata, isLoading, search]);

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
      commonCities
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

  // Ensure pagination defaults
  cleaned.limit = cleaned.limit || 500;
  cleaned.offset = cleaned.offset || 0;

  // Ensure sorting defaults
  cleaned.sortBy = cleaned.sortBy || 'just_value';
  cleaned.sortOrder = cleaned.sortOrder || 'desc';

  return cleaned;
}

// Helper to get property type description
function getPropertyTypeDescription(code: string): string {
  const descriptions: Record<string, string> = {
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
  };
  return descriptions[code] || 'Unknown';
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
