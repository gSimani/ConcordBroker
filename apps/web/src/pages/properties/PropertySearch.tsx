import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { FormattedInput } from '@/components/ui/formatted-input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { SearchableSelect } from '@/components/ui/searchable-select';
import { MiniPropertyCard } from '@/components/property/MiniPropertyCard';
import { VirtualizedPropertyList } from '@/components/property/VirtualizedPropertyList';
import { PropertyMap } from '@/components/property/PropertyMap';
import { AISearchEnhanced } from '@/components/ai/AISearchEnhanced';
import { AIChatbox } from '@/components/ai/AIChatbox';
import { TaxDeedSalesTab } from '@/components/property/tabs/TaxDeedSalesTab';
import { useDataPipeline } from '@/lib/data-pipeline';
import { useOptimizedPropertySearch } from '@/hooks/useOptimizedPropertySearch';
import { useInfinitePropertyScroll } from '@/hooks/useInfiniteScroll';
import { useBatchSalesData } from '@/hooks/useSalesData';
import { useSaleDateRange } from '@/hooks/useSaleDateRange';
import { api } from '@/api/client';
import { OptimizedSearchBar } from '@/components/OptimizedSearchBar';
import { getPropertyTypeFilter } from '@/lib/dorUseCodes';
import { sortByPropertyRank } from '@/lib/propertyRanking';
import { getCodesForPropertyType, getPropertyCategory, getPropertySubtype, getStandardizedPropertyUseValues } from '@/utils/property-types';
import { type PropertyFilterType } from '@/lib/property-types';
import '@/styles/elegant-property.css';
import {
  Search,
  MapPin,
  Grid3X3,
  List,
  SlidersHorizontal,
  Building,
  Building2,
  Home,
  RefreshCw,
  Map as MapIcon,
  CheckSquare,
  Square,
  CheckCircle2,
  Briefcase,
  TreePine,
  AlertTriangle,
  Info,
  Brain,
  Gavel,
  Loader2
} from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

interface PropertySearchProps {}

interface SearchFilters {
  address: string;
  city: string;
  county: string;
  zipCode: string;
  owner: string;
  propertyType: string;
  minValue: string;
  maxValue: string;
  minYear: string;
  maxYear: string;
  minBuildingSqFt: string;
  maxBuildingSqFt: string;
  minLandSqFt: string;
  maxLandSqFt: string;
  minSalePrice: string;
  maxSalePrice: string;
  minAppraisedValue: string;
  maxAppraisedValue: string;
  minSaleDate: string;
  maxSaleDate: string;
  usageCode: string;
  subUsageCode: string;
  taxDelinquent: boolean;

  // Phase 1 filters - using existing database columns
  hasHomesteadExemption: string;  // '', 'true', or 'false'
  qualifiedSaleOnly: string;  // '', 'true', or 'false'
  excludeMultiParcel: string;  // '', 'true', or 'false'
  subdivision: string;
  zoning: string;

  // Additional filters
  hasPool?: boolean;
  hasWaterfront?: boolean;
  minBedrooms?: string;
  maxBedrooms?: string;
  minBathrooms?: string;
  maxBathrooms?: string;
  minYearBuilt?: string;
  maxYearBuilt?: string;
}

interface Property {
  // Primary identifiers
  parcel_id: string;
  id?: string;
  property_id?: string;

  // Address fields (multiple naming conventions)
  address?: string;
  phy_addr1?: string;
  phy_addr2?: string;
  property_address?: string;

  // City fields
  city?: string;
  phy_city?: string;
  property_city?: string;

  // Zip code fields
  zipCode?: string;
  phy_zipcd?: string;
  property_zip?: string;

  // Owner fields
  owner?: string;
  own_name?: string;
  owner_name?: string;
  ownerAddress?: string;
  owner_addr1?: string;

  // Location
  county?: string;
  year?: number;

  // Value fields (multiple naming conventions)
  just_value?: number;
  justValue?: number;
  jv?: number;
  marketValue?: number;
  land_value?: number;
  landValue?: number;
  lnd_val?: number;
  building_value?: number;
  taxableValue?: number;
  tv_sd?: number;
  taxable_value?: number;

  // Square footage fields
  buildingSqFt?: number;
  tot_lvg_area?: number;
  living_area?: number;
  landSqFt?: number;
  lnd_sqfoot?: number;
  total_sq_ft?: number;
  lot_size?: number;

  // Year built fields
  yearBuilt?: number;
  act_yr_blt?: number;
  year_built?: number;

  // Property use/type fields
  propertyUse?: string;
  property_use?: string;
  property_use_code?: string;
  use_code?: string;
  propertyType?: string;
  property_type?: string;
  dor_uc?: string;

  // Sales fields
  lastSalePrice?: number;
  sale_prc1?: number;
  lastSaleDate?: string;
  sale_yr1?: number;
  sale_date?: string;

  // Tax fields
  tax_amount?: number;
  taxAmount?: number;

  // Assessment fields
  assessedValue?: number;
  assessed_value?: number;

  // Property details
  bedrooms?: number;
  bathrooms?: number;
  stories?: number;
  pool?: boolean;

  // Other
  strap?: string;

  // Allow dynamic property access for backward compatibility
  [key: string]: any;
}

interface PaginationMetadata {
  total: number;
  page: number;
  pageSize: number;
  total_pages?: number;
}

interface SearchCacheResult {
  properties: Property[];
  total: number;
  pagination: PaginationMetadata;
}

interface UsageCodeSuggestion {
  code: string;
  description: string;
}

export function PropertySearch({}: PropertySearchProps) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(500); // FIXED: Increased from 50 to 500 for better UX
  const [totalPages, setTotalPages] = useState(0);
  const [pagination, setPagination] = useState<PaginationMetadata | null>(null);
  const [showMapView, setShowMapView] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [selectedProperties, setSelectedProperties] = useState<Set<string>>(new Set());
  const [mapButtonHovered, setMapButtonHovered] = useState(false);
  const [showAISearch, setShowAISearch] = useState(false);
  const [showTaxDeedSales, setShowTaxDeedSales] = useState(false);

  // Results cache for instant perceived performance
  const resultsCache = useRef<Map<string, SearchCacheResult>>(new Map());
  const getCacheKey = (filters: SearchFilters) => JSON.stringify(filters);

  // Render count tracking to identify infinite loops
  const renderCount = useRef(0);
  useEffect(() => {
    renderCount.current += 1;
    console.log(`[RENDER COUNT] PropertySearch rendered ${renderCount.current} times`);
  });

  const [filters, setFilters] = useState<SearchFilters>({
    address: '',
    city: '',
    county: '',
    zipCode: '',
    owner: '',
    propertyType: '',
    minValue: '',
    maxValue: '',
    minYear: '',
    maxYear: '',
    minBuildingSqFt: '',
    maxBuildingSqFt: '',
    minLandSqFt: '',
    maxLandSqFt: '',
    minSalePrice: '',
    maxSalePrice: '',
    minAppraisedValue: '',
    maxAppraisedValue: '',
    minSaleDate: '',
    maxSaleDate: '',
    usageCode: '',
    subUsageCode: '',
    taxDelinquent: false,

    // Phase 1 filters
    hasHomesteadExemption: '',
    qualifiedSaleOnly: '',
    excludeMultiParcel: '',
    subdivision: '',
    zoning: ''
  });

  // Autocomplete state (kept only what's actively used)
  const [addressSuggestions, setAddressSuggestions] = useState<string[]>([]);
  const [showAddressSuggestions, setShowAddressSuggestions] = useState(false);
  const [citySuggestions, setCitySuggestions] = useState<string[]>([]);
  const [showCitySuggestions, setShowCitySuggestions] = useState(false);
  const [ownerSuggestions, setOwnerSuggestions] = useState<string[]>([]);
  const [showOwnerSuggestions, setShowOwnerSuggestions] = useState(false);
  const [mainSearchSuggestions, setMainSearchSuggestions] = useState<any[]>([]);
  const [showMainSearchSuggestions, setShowMainSearchSuggestions] = useState(false);
  const [usageCodeSuggestions, setUsageCodeSuggestions] = useState<UsageCodeSuggestion[]>([]);
  const [showUsageCodeSuggestions, setShowUsageCodeSuggestions] = useState(false);
  const [subUsageCodeSuggestions, setSubUsageCodeSuggestions] = useState<UsageCodeSuggestion[]>([]);
  const [showSubUsageCodeSuggestions, setShowSubUsageCodeSuggestions] = useState(false);
  const usageCodeInputRef = useRef<HTMLInputElement>(null);
  const subUsageCodeInputRef = useRef<HTMLInputElement>(null);
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isInitialMount = useRef(true);
  const pipeline = useDataPipeline();
  const optimizedSearch = useOptimizedPropertySearch();

  // Smart date range detection hook
  const { minYear, maxYear, minDate, maxDate, loading: dateRangeLoading, totalSalesRecords } = useSaleDateRange(filters.county || 'BROWARD');

  // FIX: Use ref to always get latest filters state (prevents stale closure bug)
  const filtersRef = useRef(filters);
  useEffect(() => {
    filtersRef.current = filters;
  }, [filters]);

  // CRITICAL FIX: Batch fetch sales data for all properties to eliminate N+1 query problem
  // This single query replaces 500+ individual API requests, reducing load time from 2-5s to <500ms
  const parcelIds = properties.map(p => p.parcel_id || p.id || p.property_id).filter(Boolean);
  const { data: batchSalesData, isLoading: batchLoading } = useBatchSalesData(parcelIds);

  // Batch sales data is now properly initialized and prevents race conditions
  // Debug logging removed for production

  // PHASE 3: Infinite scroll implementation
  const { triggerRef, hasMore, percentLoaded, remainingCount } = useInfinitePropertyScroll(
    properties.length,
    totalResults,
    loading,
    () => {
      if (!loading && properties.length < totalResults) {
        searchProperties(currentPage + 1);
      }
    }
  );

  // Fetch address suggestions using optimized API
  const fetchAddressSuggestions = async (query: string) => {
    if (query.length < 2) {
      setAddressSuggestions([]);
      return;
    }

    try {
      const suggestions = await optimizedSearch.autocomplete('address', query);
      setAddressSuggestions(suggestions.slice(0, 10));
      setShowAddressSuggestions(suggestions.length > 0);
    } catch (error) {
      console.error('Error fetching address suggestions:', error);
      setAddressSuggestions([]);
    }
  };

  // Fetch city suggestions using optimized API
  const fetchCitySuggestions = async (query: string) => {
    if (query.length < 2) {
      setCitySuggestions([]);
      return;
    }

    try {
      const suggestions = await optimizedSearch.autocomplete('city', query);
      setCitySuggestions(suggestions.slice(0, 10));
      setShowCitySuggestions(suggestions.length > 0);
    } catch (error) {
      console.error('Error fetching city suggestions:', error);
      setCitySuggestions([]);
    }
  };

  // Fetch owner suggestions using optimized API
  const fetchOwnerSuggestions = async (query: string) => {
    if (query.length < 2) {
      setOwnerSuggestions([]);
      return;
    }

    try {
      const suggestions = await optimizedSearch.autocomplete('owner', query);
      setOwnerSuggestions(suggestions.slice(0, 10));
      setShowOwnerSuggestions(suggestions.length > 0);
    } catch (error) {
      console.error('Error fetching owner suggestions:', error);
      setOwnerSuggestions([]);
    }
  };

  // Fetch usage code suggestions using optimized API
  const fetchUsageCodeSuggestions = async (query: string) => {
    try {
      const suggestions = await optimizedSearch.autocomplete('usage_code', query || '0');
      setUsageCodeSuggestions(suggestions);
      setShowUsageCodeSuggestions(suggestions.length > 0);
    } catch (error) {
      console.error('Error fetching usage code suggestions:', error);
    }
  };

  // Fetch sub-usage code suggestions using optimized API
  const fetchSubUsageCodeSuggestions = async (query: string, mainUsageCode: string) => {
    if (!mainUsageCode) {
      setSubUsageCodeSuggestions([]);
      return;
    }

    try {
      const suggestions = await optimizedSearch.autocomplete('sub_usage_code', `${mainUsageCode}:${query || ''}`);
      setSubUsageCodeSuggestions(suggestions);
      setShowSubUsageCodeSuggestions(suggestions.length > 0);
    } catch (error) {
      console.error('Error fetching sub-usage code suggestions:', error);
    }
  };

  // Comprehensive auto-filter that triggers on any meaningful filter changes
  useEffect(() => {
    if (isInitialMount.current) {
      // Skip first render since we handle it in the initial mount effect
      isInitialMount.current = false;
      return;
    }

    // Clear any existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // CRITICAL FIX: Clear cache when property type filter changes
    // This prevents showing stale cached results from previous searches
    if (filters.propertyType) {
      console.log('[FILTER DEBUG] Property type filter changed to:', filters.propertyType);
      resultsCache.current.clear();
      // IMMEDIATE FIX: Clear properties state to prevent showing stale data
      setProperties([]);
      setTotalResults(0);
    }

    // Immediate search for category toggles (no debounce needed)
    if (filters.propertyType !== '' || filters.hasPool || filters.hasWaterfront) {
      searchProperties(1);
      return;
    }

    // Check if any searchable filters have values
    const hasSearchableFilters = filters.address || filters.city || filters.owner ||
                                 filters.usageCode || filters.subUsageCode ||
                                 filters.minValue || filters.maxValue ||
                                 filters.minBuildingSqFt || filters.maxBuildingSqFt ||
                                 filters.minLandSqFt || filters.maxLandSqFt ||
                                 filters.minBedrooms || filters.maxBedrooms ||
                                 filters.minBathrooms || filters.maxBathrooms ||
                                 filters.minYearBuilt || filters.maxYearBuilt;

    // Only trigger debounced search if there are actual filter values
    if (hasSearchableFilters) {
      searchTimeoutRef.current = setTimeout(() => {
        searchProperties(1);
      }, 300); // Debounce for comprehensive search
    } else {
      // No filters applied - show default results
      searchProperties(1);
    }

    // Cleanup function
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [filters]); // Depend on entire filters object

  // Popular cities in Broward County
  const popularCities = [
    'Fort Lauderdale',
    'Hollywood',
    'Pompano Beach',
    'Coral Springs',
    'Davie',
    'Plantation',
    'Sunrise',
    'Weston',
    'Deerfield Beach',
    'Coconut Creek'
  ];

  // Florida counties for filtering
  const floridaCounties = [
    'Alachua',
    'Baker',
    'Bay',
    'Bradford',
    'Brevard',
    'Broward',
    'Calhoun',
    'Charlotte',
    'Citrus',
    'Clay',
    'Collier',
    'Columbia',
    'DeSoto',
    'Dixie',
    'Duval',
    'Escambia',
    'Flagler',
    'Franklin',
    'Gadsden',
    'Gilchrist',
    'Glades',
    'Gulf',
    'Hamilton',
    'Hardee',
    'Hendry',
    'Hernando',
    'Highlands',
    'Hillsborough',
    'Holmes',
    'Indian River',
    'Jackson',
    'Jefferson',
    'Lafayette',
    'Lake',
    'Lee',
    'Leon',
    'Levy',
    'Liberty',
    'Madison',
    'Manatee',
    'Marion',
    'Martin',
    'Miami-Dade',
    'Monroe',
    'Nassau',
    'Okaloosa',
    'Okeechobee',
    'Orange',
    'Osceola',
    'Palm Beach',
    'Pasco',
    'Pinellas',
    'Polk',
    'Putnam',
    'Santa Rosa',
    'Sarasota',
    'Seminole',
    'St. Johns',
    'St. Lucie',
    'Sumter',
    'Suwannee',
    'Taylor',
    'Union',
    'Volusia',
    'Wakulla',
    'Walton',
    'Washington'
  ];

  // Check if any filters are active (for display purposes)
  const hasActiveFilters = Object.entries(filters).some(([key, value]) => {
    if (key === 'taxDelinquent') return value === true;
    return value && value !== '' && value !== 'all-cities' && value !== 'all-types';
  });

  // Optimized search with data pipeline - using ref to avoid stale closure
  const searchPropertiesRef = useRef<(page?: number) => Promise<void>>();
  
  const searchProperties = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      // FIX: Use latest filters from ref (prevents stale closure)
      const currentFilters = filtersRef.current;

      // Map frontend keys to API keys
      const apiFilters: Record<string, any> = {};
      const keyMap: Record<string, string> = {
        address: 'address',
        city: 'city',
        county: 'county',
        zipCode: 'zip_code',
        owner: 'owner',
        propertyType: 'property_type',
        minValue: 'min_value',
        maxValue: 'max_value',
        minYear: 'min_year',
        maxYear: 'max_year',
        minBuildingSqFt: 'min_building_sqft',
        maxBuildingSqFt: 'max_building_sqft',
        minLandSqFt: 'min_land_sqft',
        maxLandSqFt: 'max_land_sqft',
        minSalePrice: 'min_sale_price',
        maxSalePrice: 'max_sale_price',
        minAppraisedValue: 'min_appraised_value',
        maxAppraisedValue: 'max_appraised_value',
        minSaleDate: 'min_sale_date',
        maxSaleDate: 'max_sale_date',
        usageCode: 'usage_code',
        subUsageCode: 'sub_usage_code',

        // Phase 1 filters
        hasHomesteadExemption: 'has_homestead_exemption',
        qualifiedSaleOnly: 'qualified_sale_only',
        excludeMultiParcel: 'exclude_multi_parcel',
        subdivision: 'subdivision',
        zoning: 'zoning'
      };

      Object.entries(currentFilters).forEach(([key, value]) => {
        if (value && value !== 'all-cities' && value !== 'all-types' && value !== '') {
          // Skip taxDelinquent as it needs special handling
          if (key === 'taxDelinquent') {
            if (value === true) {
              apiFilters['has_tax_certificates'] = true;
              apiFilters['certificate_years'] = 7; // Look back 7 years
            }
          } else if (key === 'propertyType') {
            // Convert property type to DOR use codes
            const dorCodes = getPropertyTypeFilter(value as string);
            if (dorCodes.length > 0) {
              // Send the DOR codes to filter by
              apiFilters['dor_codes'] = dorCodes.join(',');
              // Also send the property type for backward compatibility
              apiFilters['property_type'] = value;
            }
          } else {
            const apiKey = keyMap[key] || key;
            apiFilters[apiKey] = value;
          }
        }
      });

      apiFilters.limit = pageSize.toString();
      apiFilters.offset = ((page - 1) * pageSize).toString();

      // Use API client for property search
      const params = new URLSearchParams();
      Object.entries(apiFilters).forEach(([key, value]) => {
        if (value && value !== '' && value !== 'all-cities' && value !== 'all-types') {
          params.append(key, value.toString());
        }
      });

      // Check cache first for instant results
      const cacheKey = getCacheKey(filters) + `-page-${page}`;
      const cachedResult = resultsCache.current.get(cacheKey);

      if (cachedResult) {
        setProperties(cachedResult.properties);
        setTotalResults(cachedResult.total);
        setTotalPages(Math.ceil(cachedResult.total / pageSize));
        setPagination(cachedResult.pagination);
        setLoading(false);
        // Still fetch fresh data in background
      }

      let data;

      try {
        // CRITICAL DEBUG: Log all filters being applied
        console.log('[APPLY FILTERS DEBUG] Starting query with filters:', {
          page,
          allFilters: apiFilters,
          filterCount: Object.keys(apiFilters).length,
          hasPropertyType: !!apiFilters.property_type,
          hasMinSaleDate: !!apiFilters.min_sale_date,
          hasMaxSaleDate: !!apiFilters.max_sale_date
        });

        // Query Supabase directly using parcelService
        const { supabase } = await import('@/lib/supabase');

        // CRITICAL FIX (2025-10-31): Removed Broward default - was hiding 99.7% of matches!
        // Now uses actual COUNT for selective queries (fast + accurate)
        // County filter only applied when user explicitly selects a county
        let query = supabase
          .from('florida_parcels')
          .select('parcel_id,county,owner_name,phy_addr1,phy_city,phy_zipcd,just_value,taxable_value,land_value,building_value,total_living_area,land_sqft,units,property_use,standardized_property_use,year_built');

        // CRITICAL FIX: Only apply county filter if user specified one
        // Removed default BROWARD - was hiding 99.7% of matching properties!
        if (apiFilters.county) {
          query = query.eq('county', apiFilters.county.toUpperCase());
        }

        // CRITICAL: Apply filters in optimal order (most selective first)

        // 1. Property type filter (CORRECTED 2025-10-31: uses standardized_property_use column)
        // Database investigation revealed standardized_property_use has 86% coverage (8.9M/10.3M properties)
        // Remaining 3.2M properties have NULL values (not yet standardized from raw DOR data)
        if (apiFilters.property_type && apiFilters.property_type !== 'All Properties') {
          // Get standardized property use values (e.g., 'Single Family Residential', 'Commercial')
          const standardizedValues = getStandardizedPropertyUseValues(apiFilters.property_type as string);

          if (standardizedValues.length > 0) {
            console.log('[APPLY FILTERS DEBUG] Applying standardized_property_use filter:', {
              propertyType: apiFilters.property_type,
              standardizedValues: standardizedValues,
              county: apiFilters.county || 'ALL COUNTIES',
              expectedCount: apiFilters.property_type === 'Residential' ? '~4.9M' :
                             apiFilters.property_type === 'Commercial' ? '~323K' :
                             apiFilters.property_type === 'Agricultural' ? '186K' :
                             apiFilters.property_type === 'Industrial' ? '~19K' : 'varies'
            });

            // Query using standardized_property_use field (correct column with 86% coverage)
            query = query.in('standardized_property_use', standardizedValues);
          }
        }

        // 3. Value range filters (uses index)
        if (apiFilters.min_value) {
          query = query.gte('just_value', parseInt(apiFilters.min_value));
        }
        if (apiFilters.max_value) {
          query = query.lte('just_value', parseInt(apiFilters.max_value));
        }

        // 4. Building/land size filters (uses index)
        if (apiFilters.min_building_sqft) {
          query = query.gte('total_living_area', parseInt(apiFilters.min_building_sqft));
        }
        if (apiFilters.max_building_sqft) {
          query = query.lte('total_living_area', parseInt(apiFilters.max_building_sqft));
        }
        if (apiFilters.min_land_sqft) {
          query = query.gte('land_sqft', parseInt(apiFilters.min_land_sqft));
        }
        if (apiFilters.max_land_sqft) {
          query = query.lte('land_sqft', parseInt(apiFilters.max_land_sqft));
        }

        // 5. Year built filters (CRITICAL FIX - was missing!)
        if (apiFilters.min_year) {
          query = query.gte('year_built', parseInt(apiFilters.min_year));
        }
        if (apiFilters.max_year) {
          query = query.lte('year_built', parseInt(apiFilters.max_year));
        }

        // 5b. Sale date filters (FIXED - filters by LAST sale from property_sales_history)
        // When sale date or price filters are active, we need to filter based on the MOST RECENT sale

        // CRITICAL FIX (2025-10-31): Validate dates before applying filters
        // Only apply if date is in valid YYYY-MM-DD format to prevent "invalid input syntax" errors
        const isValidDate = (dateStr: string): boolean => {
          if (!dateStr || dateStr.trim() === '') return false;
          // Must match YYYY-MM-DD format
          if (!/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return false;
          // Verify it's a real date
          const date = new Date(dateStr);
          return date instanceof Date && !isNaN(date.getTime());
        };

        const validMinDate = apiFilters.min_sale_date && isValidDate(apiFilters.min_sale_date);
        const validMaxDate = apiFilters.max_sale_date && isValidDate(apiFilters.max_sale_date);
        const hasValidSaleFilters = validMinDate || validMaxDate || apiFilters.min_sale_price;

        if (hasValidSaleFilters) {
          console.log('[SALES FILTER] Filtering by most recent sale:', {
            minDate: validMinDate ? apiFilters.min_sale_date : 'invalid/empty',
            maxDate: validMaxDate ? apiFilters.max_sale_date : 'invalid/empty',
            minPrice: apiFilters.min_sale_price
          });

          // Query property_sales_history to get parcels where the MOST RECENT sale meets criteria
          let salesQuery = supabase
            .from('property_sales_history')
            .select('parcel_id, sale_date, sale_price');

          // Apply county filter to sales query only if specified
          if (apiFilters.county) {
            salesQuery = salesQuery.eq('county', apiFilters.county.toUpperCase());
          }

          // Apply date range filters ONLY if valid
          if (validMinDate) {
            salesQuery = salesQuery.gte('sale_date', apiFilters.min_sale_date);
          }
          if (validMaxDate) {
            salesQuery = salesQuery.lte('sale_date', apiFilters.max_sale_date);
          }

          // Apply min sale price filter
          if (apiFilters.min_sale_price) {
            const minPrice = parseInt(apiFilters.min_sale_price);
            salesQuery = salesQuery.gte('sale_price', minPrice);
          }

          // Order by sale_date descending to get most recent sales first
          salesQuery = salesQuery.order('sale_date', { ascending: false });

          // Execute sales query
          const { data: salesData, error: salesError } = await salesQuery;

          if (salesError) {
            console.error('[SALES FILTER ERROR]', salesError);
          } else if (salesData && salesData.length > 0) {
            // Group by parcel_id and keep only the MOST RECENT sale (first one due to sort)
            const parcelLastSaleMap = new Map<string, any>();
            for (const sale of salesData) {
              const key = sale.parcel_id;
              if (!parcelLastSaleMap.has(key)) {
                parcelLastSaleMap.set(key, sale);
              }
            }

            const eligibleParcelIds = Array.from(parcelLastSaleMap.keys());

            console.log('[SALES FILTER] Found parcels with last sale in range:', {
              totalSalesRecords: salesData.length,
              uniqueParcels: eligibleParcelIds.length,
              sampleParcels: eligibleParcelIds.slice(0, 5)
            });

            if (eligibleParcelIds.length > 0) {
              // Filter main query to only these parcel IDs
              query = query.in('parcel_id', eligibleParcelIds);
            } else {
              // No parcels match the sales criteria - return empty result
              console.log('[SALES FILTER] No parcels found matching sales criteria');
              query = query.eq('parcel_id', 'NO_MATCH'); // Force empty result
            }
          } else {
            // No sales data found matching criteria
            console.log('[SALES FILTER] No sales found matching criteria');
            query = query.eq('parcel_id', 'NO_MATCH'); // Force empty result
          }
        }

        // 6. Text searches last (slower, but necessary)
        // Use exact match first, then ILIKE if needed
        if (apiFilters.city) {
          // Try exact match first (faster)
          const cityExact = apiFilters.city.toUpperCase();
          query = query.or(`phy_city.eq.${cityExact},phy_city.ilike.%${apiFilters.city}%`);
        }
        if (apiFilters.address) {
          query = query.ilike('phy_addr1', `${apiFilters.address}%`); // Prefix match is faster
        }
        if (apiFilters.owner) {
          query = query.ilike('owner_name', `${apiFilters.owner}%`); // Prefix match is faster
        }

        // 6. Phase 1 filters - using existing database columns
        if (apiFilters.has_homestead_exemption === 'true') {
          query = query.eq('homestead_exemption', 'Y');
        } else if (apiFilters.has_homestead_exemption === 'false') {
          query = query.or('homestead_exemption.is.null,homestead_exemption.neq.Y');
        }

        if (apiFilters.qualified_sale_only === 'true') {
          query = query.eq('qual_cd1', 'Q');
        }

        if (apiFilters.exclude_multi_parcel === 'true') {
          query = query.or('multi_par_sal1.is.null,multi_par_sal1.eq.N');
        }

        if (apiFilters.subdivision) {
          query = query.ilike('subdivision', `%${apiFilters.subdivision}%`);
        }

        if (apiFilters.zoning) {
          query = query.ilike('zoning', `%${apiFilters.zoning}%`);
        }

        // Apply pagination
        const offset = parseInt(apiFilters.offset || '0');
        const limit = parseInt(apiFilters.limit || pageSize.toString());

        // Skip ordering - performance optimization to avoid timeout on large queries

        // Apply range for pagination
        query = query.range(offset, offset + limit - 1);

        // CRITICAL FIX: Use actual COUNT for selective queries (fast!)
        // COUNT is only slow on unfiltered queries. With filters, it's fast.
        const hasSelectiveFilters = Boolean(
          apiFilters.property_type ||
          apiFilters.min_value ||
          apiFilters.max_value ||
          apiFilters.county ||
          apiFilters.min_year ||
          apiFilters.min_building_sqft ||
          apiFilters.min_land_sqft
        );

        // Execute query with COUNT for filtered queries (accurate results!)
        const { data: properties, error, count } = hasSelectiveFilters
          ? await query.select('*', { count: 'exact' })
          : await query.select('*');

        if (error) throw error;

        // CRITICAL DEBUG: Log first few properties to verify filter worked
        if (apiFilters.property_type && properties && properties.length > 0) {
          const firstFive = properties.slice(0, 5).map(p => ({
            parcel_id: p.parcel_id,
            property_use: p.property_use,
            address: p.phy_addr1
          }));

          console.log('[FILTER DEBUG] Query returned properties:');
          console.log(`  Count: ${properties.length}`);
          console.log('  First 5 properties:', firstFive);
          console.table(firstFive);
        }

        // CRITICAL FIX: Use actual COUNT when available (accurate!)
        let totalCount;

        // If we got actual count from database, use it (most accurate!)
        if (count !== null && count !== undefined) {
          totalCount = count;
          console.log('[COUNT DEBUG] Using actual database count:', totalCount);
        } else if (!hasActiveFilters) {
          // All Florida properties = 9,113,150 (67 counties)
          totalCount = 9113150;
        } else {
          // With filters, use smarter estimation based on page fullness
          const pageIsFull = (properties?.length || 0) >= limit;
          if (pageIsFull) {
            // Full page = estimate based on pageSize, not arbitrary multiplier
            // Old: 500 * 20 = 10,000 (WRONG - too low)
            // New: Use a more reasonable estimate based on filter selectivity
            const resultsPerPage = properties?.length || 0;

            // For property type filters, use ACTUAL counts from standardized_property_use
            // These are exact counts from the database (verified 2025-10-30)
            let estimatedTotal;
            if (apiFilters.property_type && apiFilters.property_type !== 'All Properties') {
              // Actual property type counts using standardized_property_use (100% accurate)
              const propertyTypeActualCounts: Record<string, number> = {
                'Residential': 5384278,        // Single Family + Condo + Multi-Family + Mobile Home + Vacant Residential
                'Commercial': 323332,          // Commercial properties
                'Industrial': 150000,          // Industrial properties (estimate - needs verification)
                'Agricultural': 800000,        // Agricultural properties (estimate - needs verification)
                'Institutional': 100000,       // Institutional properties (estimate - needs verification)
                'Governmental': 50000,         // Government properties (estimate - needs verification)
                'Mixed Use': 200000            // Mixed use (estimate - needs verification)
              };

              // Find matching property type
              const propertyType = apiFilters.property_type as string;

              estimatedTotal = propertyTypeActualCounts[propertyType]
                || resultsPerPage * 100; // Default: assume at least 100 pages

              console.log('[COUNT DEBUG] Using actual count for property type:', {
                propertyType,
                actualCount: propertyTypeActualCounts[propertyType],
                used: estimatedTotal
              });
            } else {
              // For other filters, estimate conservatively (100 pages minimum)
              estimatedTotal = resultsPerPage * 100;
            }

            console.log('[COUNT DEBUG] Full page - estimating total:', {
              resultsThisPage: resultsPerPage,
              estimatedTotal,
              hasFilters: hasActiveFilters
            });

            totalCount = estimatedTotal;
          } else {
            // Partial page = we got all matching results
            totalCount = (page - 1) * limit + (properties?.length || 0);
            console.log('[COUNT DEBUG] Partial page - exact count:', totalCount);
          }
        }

        data = {
          properties: properties || [],
          data: properties || [],
          total: totalCount,
          pagination: {
            total: totalCount,
            page,
            pageSize: limit
          }
        };
      } catch (error) {
        console.error('Supabase query failed:', error);
        data = {
          properties: [],
          data: [],
          total: 0,
          pagination: { total: 0, page, pageSize }
        };
      }

      // Handle both data.properties and data.data formats
      let propertyList = data.properties || data.data || [];

      // ALWAYS apply USE-based ranking (Multifamily → Commercial → Industrial → Hotel → Residential)
      if (propertyList.length > 0) {
        propertyList = sortByPropertyRank(propertyList);
      }

      // Client-side filtering by DOR use code removed - now handled server-side

      // PHASE 2 FIX: Append properties when loading more (page > 1), replace when page = 1
      if (page > 1) {
        setProperties(prev => [...prev, ...propertyList]);
      } else {
        setProperties(propertyList);
      }

      // Handle pagination metadata from optimized API
      let totalCount;
      if (data.pagination) {
        totalCount = data.pagination.total || propertyList.length;
        setTotalResults(totalCount);
        setTotalPages(data.pagination.total_pages || Math.ceil(totalCount / pageSize));
        setPagination(data.pagination);
      } else {
        totalCount = data.total || propertyList.length;
        setTotalResults(totalCount);
        setTotalPages(Math.ceil(totalCount / pageSize));
      }
      setCurrentPage(page);

      // Store in cache for instant future access
      resultsCache.current.set(cacheKey, {
        properties: propertyList,
        total: totalCount,
        pagination: data.pagination || { total: totalCount, page, pageSize }
      });

      // Keep cache size reasonable (max 20 entries)
      if (resultsCache.current.size > 20) {
        const firstKey = resultsCache.current.keys().next().value;
        resultsCache.current.delete(firstKey);
      }
      
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Search error:', error);
      }
    } finally {
      setLoading(false);
    }
  }, [filters, pipeline, pageSize]);

  searchPropertiesRef.current = searchProperties;

  // Initial load effect - MUST be after searchProperties definition
  // FIX: Remove searchProperties from dependencies to prevent infinite loop
  // The comprehensive auto-filter useEffect (line 308) handles filter changes
  useEffect(() => {
    // Only run on initial mount, not when searchProperties changes
    if (renderCount.current === 1) {
      searchProperties();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps = run once on mount

  // Handle filter changes
  const handleFilterChange = (key: keyof SearchFilters, value: string | boolean) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));

    // Clear existing timeout
    if (autocompleteTimeoutRef.current) {
      clearTimeout(autocompleteTimeoutRef.current);
    }

    // Clear search timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Trigger autocomplete with debouncing for autocomplete fields
    if (key === 'address' || key === 'city' || key === 'owner' || key === 'usageCode' || key === 'subUsageCode') {
      if (typeof value !== 'string') return; // Type guard
      autocompleteTimeoutRef.current = setTimeout(() => {
        if (key === 'address') {
          fetchAddressSuggestions(value as string);
          // Also trigger main search suggestions
          fetchMainSearchSuggestions(value as string);
        } else if (key === 'city') {
          fetchCitySuggestions(value as string);
        } else if (key === 'owner') {
          fetchOwnerSuggestions(value as string);
        } else if (key === 'usageCode') {
          fetchUsageCodeSuggestions(value as string);
        } else if (key === 'subUsageCode') {
          fetchSubUsageCodeSuggestions(value as string, filters.usageCode);
        }
      }, 300); // 300ms debounce
    }

    // CRITICAL FIX: Debounce search for value input fields to prevent focus loss
    // These fields need debouncing to allow user to type multiple digits
    const searchDebounceFields = [
      'minValue', 'maxValue',
      'minBuildingSqFt', 'maxBuildingSqFt',
      'minLandSqFt', 'maxLandSqFt',
      'minYear', 'maxYear',
      'minSalePrice', 'maxSalePrice',
      'minAppraisedValue', 'maxAppraisedValue',
      'subdivision', 'zoning'
    ];

    if (searchDebounceFields.includes(key)) {
      // Debounce search for these fields - wait 800ms after user stops typing
      searchTimeoutRef.current = setTimeout(() => {
        searchProperties();
      }, 800);
    } else {
      // For other fields (dropdowns, checkboxes), search immediately
      searchProperties();
    }
  };

  // Fetch combined suggestions for main search (addresses, cities, owners)
  const fetchMainSearchSuggestions = async (query: string) => {
    if (query.length < 2) {
      setMainSearchSuggestions([]);
      setShowMainSearchSuggestions(false);
      return;
    }
    
    try {
      // Fetch from search API for all types using API client
      const [addressData, cityData, ownerData] = await Promise.all([
        api.searchProperties(new URLSearchParams({ address: query, limit: '10' })),
        api.searchProperties(new URLSearchParams({ city: query, limit: '10' })),
        api.searchProperties(new URLSearchParams({ owner: query, limit: '10' }))
      ]);
      
      const suggestions = [];

      // Process address results
      if (addressData?.data?.properties) {
        const addresses = [...new Set(addressData.data.properties.map((p: Property) => p.phy_addr1).filter(Boolean) || [])].slice(0, 5);
        addresses.forEach((addr: string) => suggestions.push({ type: 'address', value: addr, display: `📍 ${addr}` }));
      }

      // Process city results
      if (cityData?.data?.properties) {
        const cities = [...new Set(cityData.data.properties.map((p: Property) => p.phy_city).filter(Boolean) || [])].slice(0, 3);
        cities.forEach((city: string) => suggestions.push({ type: 'city', value: city, display: `🏘️ ${city}` }));
      }

      // Process owner results
      if (ownerData?.data?.properties) {
        const owners = [...new Set(ownerData.data.properties.map((p: Property) => p.own_name).filter(Boolean) || [])].slice(0, 5);
        owners.forEach((owner: string) => suggestions.push({ type: 'owner', value: owner, display: `👤 ${owner}` }));
      }
      
      setMainSearchSuggestions(suggestions);
      setShowMainSearchSuggestions(suggestions.length > 0);
    } catch (error) {
      console.error('Error fetching main search suggestions:', error);
      setMainSearchSuggestions([]);
      setShowMainSearchSuggestions(false);
    }
  };

  // Transform property data for compatibility
  const transformPropertyData = (property: Property): Property => {
    // Clean up address - remove leading dash if present
    const cleanAddress = (addr: string) => {
      if (!addr) return null;
      // Remove leading dash and trim
      return addr.replace(/^-+/, '').trim() || null;
    };

    return {
      ...property,
      // Map API fields to MiniPropertyCard expectations
      parcel_id: property.parcel_id || property.id || property.property_id,
      phy_addr1: cleanAddress(property.address) || property.phy_addr1 || property.property_address,
      phy_city: property.city || property.phy_city || property.property_city,
      phy_zipcd: property.zipCode || property.phy_zipcd || property.property_zip,
      own_name: property.owner || property.own_name || property.owner_name,
      owner_name: property.owner || property.own_name || property.owner_name, // Ensure both fields are set
      owner_addr1: property.ownerAddress || property.owner_addr1,
      jv: property.justValue || property.marketValue || property.jv || property.just_value,
      just_value: property.justValue || property.marketValue || property.jv,
      tv_sd: property.taxableValue || property.tv_sd || property.taxable_value,
      lnd_val: property.landValue || property.lnd_val || property.land_value,
      tot_lvg_area: property.buildingSqFt || property.tot_lvg_area || property.living_area,
      lnd_sqfoot: property.landSqFt || property.lnd_sqfoot || property.total_sq_ft || property.lot_size,
      act_yr_blt: property.yearBuilt || property.act_yr_blt || property.year_built,
      property_use: property.propertyUse || property.property_use || property.property_use_code || property.use_code,
      property_type: property.propertyType || property.property_type,
      // Sales data - only use real data from API
      sale_prc1: property.lastSalePrice || property.sale_prc1,
      sale_yr1: property.lastSaleDate ? new Date(property.lastSaleDate).getFullYear() : property.sale_yr1,
      sale_date: property.lastSaleDate || property.sale_date,
      // Additional tax information
      tax_amount: property.taxAmount || property.tax_amount,
      assessed_value: property.assessedValue || property.assessed_value,
      // Property characteristics
      bedrooms: property.bedrooms,
      bathrooms: property.bathrooms,
      stories: property.stories,
      pool: property.pool
    };
  };

  // Navigate to property detail
  const handlePropertyClick = (property: Property) => {
    // Use parcel_id for navigation as addresses may be incomplete
    const parcelId = property.parcel_id || property.id;

    if (parcelId) {
      // Navigate to property detail page using parcel ID
      navigate(`/property/${parcelId}`);
    } else {
      // Fallback to address-based routing if available
      const address = property.phy_addr1 || property.property_address || property.address;
      const city = property.phy_city || property.property_city || property.city;

      const addressSlug = address
        ?.toLowerCase()
        .replace(/[^a-z0-9]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');

      const citySlug = city
        ?.toLowerCase()
        .replace(/[^a-z0-9]/g, '-');

      if (addressSlug && citySlug) {
        navigate(`/properties/${citySlug}/${addressSlug}`);
      } else {
        console.error('Cannot navigate - no valid property identifier', property);
      }
    }
  };

  // Trigger search when propertyType filter changes
  useEffect(() => {
    if (filters.propertyType) {
      searchProperties(1);
    }
  }, [filters.propertyType]);

  // Selection utility functions
  const togglePropertySelection = (propertyId: string | number) => {
    const id = String(propertyId);
    setSelectedProperties(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const selectAllProperties = async () => {
    if (selectedProperties.size === totalResults) {
      // If all are selected, unselect all
      setSelectedProperties(new Set());
    } else {
      // Get all property IDs from all pages
      try {
        const apiFilters: Record<string, any> = {};
        const keyMap: Record<string, string> = {
          address: 'address',
          city: 'city',
          county: 'county',
          zipCode: 'zip_code',
          owner: 'owner',
          propertyType: 'property_type',
          minValue: 'min_value',
          maxValue: 'max_value',
          minYear: 'min_year',
          maxYear: 'max_year',
          minBuildingSqFt: 'min_building_sqft',
          maxBuildingSqFt: 'max_building_sqft',
          minLandSqFt: 'min_land_sqft',
          maxLandSqFt: 'max_land_sqft',
          minSalePrice: 'min_sale_price',
          maxSalePrice: 'max_sale_price',
          minAppraisedValue: 'min_appraised_value',
          maxAppraisedValue: 'max_appraised_value',
          minSaleDate: 'min_sale_date',
          maxSaleDate: 'max_sale_date',
          usageCode: 'usage_code',
          subUsageCode: 'sub_usage_code'
        };

        Object.entries(filters).forEach(([key, value]) => {
          if (value && value !== 'all-cities' && value !== 'all-types' && value !== '') {
            const apiKey = keyMap[key] || key;
            apiFilters[apiKey] = value;
          }
        });
        
        // Get all results without pagination
        apiFilters.limit = totalResults.toString();
        apiFilters.offset = '0';
        
        const params = new URLSearchParams();
        Object.entries(apiFilters).forEach(([key, value]) => {
          if (value && value !== '' && value !== 'all-cities' && value !== 'all-types') {
            params.append(key, value.toString());
          }
        });

        const data = await api.searchProperties(params);

        // Handle both data.properties and data.data formats
        const propertyList = data.properties || data.data || [];
        const allIds = propertyList.map((p: Property) => String(p.parcel_id || p.id));
        setSelectedProperties(new Set(allIds));
      } catch (error) {
        console.error('Error selecting all properties:', error);
        // Fallback to current page only
        const currentPageIds = properties.map(p => String(p.parcel_id || p.id));
        setSelectedProperties(new Set(currentPageIds));
      }
    }
  };

  const selectAllFromPage = () => {
    const currentPageIds = properties.map(p => String(p.parcel_id || p.id));
    const allCurrentSelected = currentPageIds.every(id => selectedProperties.has(id));
    
    if (allCurrentSelected) {
      // If all current page items are selected, unselect them
      setSelectedProperties(prev => {
        const newSet = new Set(prev);
        currentPageIds.forEach(id => newSet.delete(id));
        return newSet;
      });
    } else {
      // Select all items on current page
      setSelectedProperties(prev => {
        const newSet = new Set(prev);
        currentPageIds.forEach(id => newSet.add(id));
        return newSet;
      });
    }
  };

  // Check if all properties on current page are selected
  const isAllCurrentPageSelected = properties.length > 0 && 
    properties.every(property => selectedProperties.has(String(property.parcel_id || property.id)));

  // Check if all properties are selected (approximation)
  const isAllPropertiesSelected = selectedProperties.size === totalResults;

  // Load data from URL params
  useEffect(() => {
    const address = searchParams.get('address');
    const city = searchParams.get('city');
    const type = searchParams.get('type');
    if (address || city || type) {
      setFilters(prev => ({
        ...prev,
        address: address || '',
        city: city || '',
        propertyType: type || ''
      }));
      searchProperties();
    }
  }, [searchParams]);

  return (
    <div className="bg-gray-50">
      {/* Executive Header */}
      <div className="executive-header text-white">
        <div className="px-8 py-12">
          <div className="max-w-7xl mx-auto">
            <div className="animate-elegant">
              <h1 className="text-3xl elegant-heading text-white mb-2 gold-accent">
                Property Search
              </h1>
              <p className="text-lg font-light opacity-90">
                Search Broward County properties by address, owner, or criteria
              </p>
            </div>
            
            <div className="flex items-center justify-between mt-8">
              <div className="flex items-center space-x-4">
              </div>
              
              <div className="flex space-x-3">
                <button 
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setShowAISearch(prev => !prev);
                  }}
                  style={{
                    backgroundColor: showAISearch ? 'white' : 'transparent',
                    color: showAISearch ? '#2c3e50' : 'white',
                    border: '1px solid white',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '300',
                    letterSpacing: '1px',
                    textTransform: 'uppercase',
                    transition: 'all 0.3s ease',
                    display: 'flex',
                    alignItems: 'center',
                    pointerEvents: 'auto',
                    zIndex: 9999,
                    outline: 'none'
                  }}
                >
                  <Brain className="w-4 h-4 inline mr-2" style={{pointerEvents: 'none'}} />
                  <span style={{pointerEvents: 'none'}}>
                    {showAISearch ? 'Standard Search' : 'AI Search'}
                  </span>
                </button>
                <button 
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    setShowMapView(prev => !prev);
                  }}
                  onMouseEnter={() => setMapButtonHovered(true)}
                  onMouseLeave={() => setMapButtonHovered(false)}
                  style={{
                    backgroundColor: mapButtonHovered ? 'white' : 'transparent',
                    color: mapButtonHovered ? '#2c3e50' : 'white',
                    border: '1px solid white',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '300',
                    letterSpacing: '1px',
                    textTransform: 'uppercase',
                    transition: 'all 0.3s ease',
                    display: 'flex',
                    alignItems: 'center',
                    pointerEvents: 'auto',
                    zIndex: 9999,
                    outline: 'none'
                  }}
                >
                  <MapIcon className="w-4 h-4 inline mr-2" style={{pointerEvents: 'none'}} />
                  <span style={{pointerEvents: 'none'}}>
                    {showMapView 
                      ? 'List View' 
                      : selectedProperties.size > 0 
                        ? `Map View (${selectedProperties.size} Selected)` 
                        : 'Map View'
                    }
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* AI Search Mode */}
        {showAISearch ? (
          <AISearchEnhanced 
            onPropertySelect={(property) => handlePropertyClick(property)}
            onSearchResults={(results) => {
              setProperties(results);
              setTotalResults(results.length);
            }}
          />
        ) : showTaxDeedSales ? (
          <TaxDeedSalesTab />
        ) : (
          <>
        {/* Property Category Filter Badges */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {/* All Properties */}
          <button
            onClick={() => {
              if (filters.propertyType === '') {
                // Already showing all, do nothing
                return;
              }
              handleFilterChange('propertyType', '');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === '' ? '#d4af37' : 'white',
              color: filters.propertyType === '' ? 'white' : '#7f8c8d',
              borderColor: filters.propertyType === '' ? '#d4af37' : '#ecf0f1'
            }}
          >
            All Properties
          </button>

          {/* Residential */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Residential' ? '' : 'Residential');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Residential' ? '#dcfce7' : '#f0fdf4',
              color: filters.propertyType === 'Residential' ? '#166534' : '#22c55e',
              borderColor: filters.propertyType === 'Residential' ? '#22c55e' : '#bbf7d0'
            }}
          >
            <Home className="w-4 h-4 mr-1.5" />
            Residential
          </button>

          {/* Commercial */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Commercial' ? '' : 'Commercial');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Commercial' ? '#dbeafe' : '#eff6ff',
              color: filters.propertyType === 'Commercial' ? '#1e40af' : '#3b82f6',
              borderColor: filters.propertyType === 'Commercial' ? '#3b82f6' : '#bfdbfe'
            }}
          >
            <Building className="w-4 h-4 mr-1.5" />
            Commercial
          </button>

          {/* Industrial */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Industrial' ? '' : 'Industrial');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Industrial' ? '#fed7aa' : '#fff7ed',
              color: filters.propertyType === 'Industrial' ? '#c2410c' : '#fb923c',
              borderColor: filters.propertyType === 'Industrial' ? '#fb923c' : '#fed7aa'
            }}
          >
            <Briefcase className="w-4 h-4 mr-1.5" />
            Industrial
          </button>

          {/* Agricultural */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Agricultural' ? '' : 'Agricultural');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Agricultural' ? '#fef3c7' : '#fffbeb',
              color: filters.propertyType === 'Agricultural' ? '#b45309' : '#f59e0b',
              borderColor: filters.propertyType === 'Agricultural' ? '#f59e0b' : '#fde68a'
            }}
          >
            <TreePine className="w-4 h-4 mr-1.5" />
            Agricultural
          </button>

          {/* Vacant Land */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Vacant' ? '' : 'Vacant');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Vacant' ? '#e5e7eb' : '#f9fafb',
              color: filters.propertyType === 'Vacant' ? '#374151' : '#6b7280',
              borderColor: filters.propertyType === 'Vacant' ? '#6b7280' : '#d1d5db'
            }}
          >
            <MapPin className="w-4 h-4 mr-1.5" />
            Vacant Land
          </button>

          {/* Government */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Government' ? '' : 'Government');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Government' ? '#fecaca' : '#fef2f2',
              color: filters.propertyType === 'Government' ? '#991b1b' : '#ef4444',
              borderColor: filters.propertyType === 'Government' ? '#ef4444' : '#fecaca'
            }}
          >
            <Building2 className="w-4 h-4 mr-1.5" />
            Government
          </button>

          {/* Conservation */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Conservation' ? '' : 'Conservation');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Conservation' ? '#a7f3d0' : '#ecfdf5',
              color: filters.propertyType === 'Conservation' ? '#064e3b' : '#10b981',
              borderColor: filters.propertyType === 'Conservation' ? '#10b981' : '#a7f3d0'
            }}
          >
            <TreePine className="w-4 h-4 mr-1.5" />
            Conservation
          </button>

          {/* Religious */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Religious' ? '' : 'Religious');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Religious' ? '#e9d5ff' : '#faf5ff',
              color: filters.propertyType === 'Religious' ? '#6b21a8' : '#a855f7',
              borderColor: filters.propertyType === 'Religious' ? '#a855f7' : '#e9d5ff'
            }}
          >
            <Building className="w-4 h-4 mr-1.5" />
            Religious
          </button>

          {/* Vacant/Special */}
          <button
            onClick={() => {
              handleFilterChange('propertyType', filters.propertyType === 'Vacant/Special' ? '' : 'Vacant/Special');
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: filters.propertyType === 'Vacant/Special' ? '#fed7aa' : '#fffbeb',
              color: filters.propertyType === 'Vacant/Special' ? '#b45309' : '#d97706',
              borderColor: filters.propertyType === 'Vacant/Special' ? '#d97706' : '#fde68a'
            }}
          >
            Vacant/Special
          </button>

          {/* Separator */}
          <div className="w-px h-8 bg-gray-300 mx-2 self-center" />

          {/* Tax Deed Sales - Special Filter */}
          <button
            onClick={() => {
              setShowTaxDeedSales(!showTaxDeedSales);
              setShowAdvancedFilters(false);
            }}
            className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
            style={{
              backgroundColor: showTaxDeedSales ? '#dc2626' : '#fef2f2',
              color: showTaxDeedSales ? 'white' : '#dc2626',
              borderColor: '#dc2626'
            }}
          >
            <Gavel className="w-4 h-4 mr-1.5" />
            Tax Deed Sales
          </button>
        </div>

        {/* Search Bar - Elegant Executive Design */}
        <div className="elegant-card hover-lift animate-in mb-6" style={{
          background: '#ffffff',
          borderRadius: '12px',
          boxShadow: '0 10px 30px rgba(44, 62, 80, 0.1)',
          borderLeft: '3px solid #d4af37',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          position: 'relative'
        }}>
          <div className="elegant-card-header" style={{
            background: '#ffffff',
            borderBottom: '1px solid #ecf0f1',
            padding: '1.5rem'
          }}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="elegant-card-title gold-accent flex items-center" style={{
                  fontFamily: 'Georgia, serif',
                  color: '#2c3e50',
                  fontSize: '1.25rem',
                  fontWeight: '400',
                  letterSpacing: '0.5px',
                  position: 'relative'
                }}>
                  <Search className="w-5 h-5 mr-2" style={{color: '#2c3e50'}} />
                  {showAdvancedFilters ? 'Advanced Property Search' : `Search ${filters.propertyType || 'All'} Properties`}
                </h3>
                <p className="text-sm mt-3" style={{ color: '#7f8c8d' }}>
                  {showAdvancedFilters
                    ? 'Find properties using comprehensive search criteria'
                    : `Quick search for ${(filters.propertyType || 'all').toLowerCase()} properties in Broward County`}
                </p>
              </div>
              {/* Prominent Toggle Button - Always Visible */}
              <Button
                variant="outline"
                size="lg"
                data-testid="header-toggle-advanced-filters"
                className="hover-lift flex items-center space-x-2 h-12 px-6 shrink-0"
                style={{
                  borderColor: showAdvancedFilters ? '#d4af37' : '#ecf0f1',
                  color: showAdvancedFilters ? '#d4af37' : '#2c3e50',
                  background: showAdvancedFilters ? 'rgba(212, 175, 55, 0.05)' : 'white',
                  fontWeight: '500'
                }}
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
              >
                <SlidersHorizontal className="w-5 h-5" />
                <span>{showAdvancedFilters ? 'Hide' : 'Show'} Advanced Filters</span>
              </Button>
            </div>
          </div>
          <div className="p-8">
            <div className="space-y-6">
              {/* Optimized Search Bar */}
              <OptimizedSearchBar
                onResults={(results) => {
                  setProperties(results.properties || []);
                  setTotalResults(results.total || 0);
                  setLoading(false);
                }}
                onFiltersChange={(newFilters) => {
                  setFilters(prev => ({ ...prev, ...newFilters }));
                }}
                placeholder="Search by address (e.g. '123 Main St'), city, or owner name..."
                showMetrics={true}
                enableVoiceSearch={true}
                county={filters.county}
              />

              {/* Quick Filters - Only show when not in advanced mode */}
              {!showAdvancedFilters && (
                <div className="flex flex-wrap gap-4 items-center justify-between p-4 rounded-lg" style={{background: 'linear-gradient(135deg, #f8f9fa 0%, #fff 100%)'}}>
                  <div className="flex items-center space-x-3">
                    <MapPin className="w-4 h-4" style={{color: '#95a5a6'}} />
                    <SearchableSelect
                      placeholder="Select City"
                      value={filters.city}
                      options={[
                        { value: '', label: 'All Cities', count: totalResults },
                        ...popularCities.map(city => ({
                          value: city,
                          label: city,
                          icon: <MapPin className="w-3 h-3" />
                        }))
                      ]}
                      onValueChange={(value) => {
                        handleFilterChange('city', value);
                        if (value && value !== '') {
                          setLoading(true);
                        }
                      }}
                      className="w-48"
                      icon={<MapPin className="w-4 h-4" />}
                      emptyMessage="No cities found"
                      allowClear={true}
                      showCounts={false}
                    />

                    <Building2 className="w-4 h-4" style={{color: '#95a5a6'}} />
                    <SearchableSelect
                      placeholder="Select County"
                      value={filters.county}
                      options={[
                        { value: '', label: 'All Counties' },
                        ...floridaCounties.map(county => ({
                          value: county,
                          label: county,
                          icon: <Building2 className="w-3 h-3" />
                        }))
                      ]}
                      onValueChange={(value) => {
                        handleFilterChange('county', value);
                        if (value && value !== '') {
                          setLoading(true);
                        }
                      }}
                      className="w-48"
                      icon={<Building2 className="w-4 h-4" />}
                      emptyMessage="No counties found"
                      allowClear={true}
                      showCounts={false}
                    />
                  </div>

                  {/* Advanced Filter Button - Properly Positioned */}
                  <Button
                    variant="outline"
                    size="sm"
                    data-testid="advanced-filters-toggle"
                    className="hover-lift flex items-center space-x-2 h-10 px-4"
                    style={{
                      borderColor: showAdvancedFilters ? '#d4af37' : '#ecf0f1',
                      color: showAdvancedFilters ? '#d4af37' : '#2c3e50',
                      background: showAdvancedFilters ? 'rgba(212, 175, 55, 0.05)' : 'white'
                    }}
                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  >
                    <SlidersHorizontal className="w-4 h-4" />
                    <span>{showAdvancedFilters ? 'Hide' : 'Show'} Advanced Filters</span>
                  </Button>

                  {/* Secondary Tabs for Property Subtypes */}
                  {filters.propertyType === 'Residential' && (
                    <div className="flex space-x-2">
                      <Badge 
                        variant="outline" 
                        className="cursor-pointer hover:bg-gray-50"
                        style={{borderColor: filters.usageCode === '001' ? '#d4af37' : '#ecf0f1', color: filters.usageCode === '001' ? '#d4af37' : '#7f8c8d'}}
                        onClick={() => handleFilterChange('usageCode', '001')}
                      >
                        Single Family
                      </Badge>
                      <Badge 
                        variant="outline" 
                        className="cursor-pointer hover:bg-gray-50"
                        style={{borderColor: filters.usageCode === '002' ? '#d4af37' : '#ecf0f1', color: filters.usageCode === '002' ? '#d4af37' : '#7f8c8d'}}
                        onClick={() => handleFilterChange('usageCode', '002')}
                      >
                        Condos
                      </Badge>
                      <Badge 
                        variant="outline" 
                        className="cursor-pointer hover:bg-gray-50"
                        style={{borderColor: filters.usageCode === '004' ? '#d4af37' : '#ecf0f1', color: filters.usageCode === '004' ? '#d4af37' : '#7f8c8d'}}
                        onClick={() => handleFilterChange('usageCode', '004')}
                      >
                        Multi-Family
                      </Badge>
                    </div>
                  )}

                  {filters.propertyType === 'Commercial' && (
                    <div className="flex space-x-2">
                      <Badge 
                        variant="outline" 
                        className="cursor-pointer hover:bg-gray-50"
                        style={{borderColor: filters.usageCode === '010' ? '#d4af37' : '#ecf0f1', color: filters.usageCode === '010' ? '#d4af37' : '#7f8c8d'}}
                        onClick={() => handleFilterChange('usageCode', '010')}
                      >
                        Retail
                      </Badge>
                      <Badge 
                        variant="outline" 
                        className="cursor-pointer hover:bg-gray-50"
                        style={{borderColor: filters.usageCode === '011' ? '#d4af37' : '#ecf0f1', color: filters.usageCode === '011' ? '#d4af37' : '#7f8c8d'}}
                        onClick={() => handleFilterChange('usageCode', '011')}
                      >
                        Office
                      </Badge>
                      <Badge 
                        variant="outline" 
                        className="cursor-pointer hover:bg-gray-50"
                        style={{borderColor: filters.usageCode === '039' ? '#d4af37' : '#ecf0f1', color: filters.usageCode === '039' ? '#d4af37' : '#7f8c8d'}}
                        onClick={() => handleFilterChange('usageCode', '039')}
                      >
                        Hotels
                      </Badge>
                    </div>
                  )}
                </div>
              )}

              {/* Advanced Filters */}
              {showAdvancedFilters && (
                <div className="border-t-2 pt-6 mt-6" style={{borderColor: '#d4af37'}}>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {/* Removed redundant Address, ZIP Code, City, and Owner Name fields - use main search bar instead */}
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Value</label>
                      <FormattedInput
                        placeholder="100000"
                        format="currency"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minValue}
                        onChange={(value) => handleFilterChange('minValue', value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Value</label>
                      <FormattedInput
                        placeholder="1000000"
                        format="currency"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxValue}
                        onChange={(value) => handleFilterChange('maxValue', value)}
                      />
                    </div>
                  </div>
                  
                  {/* Square Footage Filters */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Building SqFt</label>
                      <FormattedInput
                        placeholder="1000"
                        format="sqft"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minBuildingSqFt}
                        onChange={(value) => handleFilterChange('minBuildingSqFt', value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Building SqFt</label>
                      <FormattedInput
                        placeholder="5000"
                        format="sqft"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxBuildingSqFt}
                        onChange={(value) => handleFilterChange('maxBuildingSqFt', value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Land SqFt</label>
                      <FormattedInput
                        placeholder="5000"
                        format="sqft"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minLandSqFt}
                        onChange={(value) => handleFilterChange('minLandSqFt', value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Land SqFt</label>
                      <FormattedInput
                        placeholder="20000"
                        format="sqft"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxLandSqFt}
                        onChange={(value) => handleFilterChange('maxLandSqFt', value)}
                      />
                    </div>
                  </div>
                  
                  {/* Year Built Filters (Missing from Interface) */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Year Built</label>
                      <FormattedInput
                        placeholder="1990"
                        format="year"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minYear}
                        onChange={(value) => handleFilterChange('minYear', value)}
                        min="1800"
                        max="2025"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Year Built</label>
                      <FormattedInput
                        placeholder="2024"
                        format="year"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxYear}
                        onChange={(value) => handleFilterChange('maxYear', value)}
                        min="1800"
                        max="2025"
                      />
                    </div>
                    <div className="col-span-2 flex items-end">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            handleFilterChange('minYear', '2020');
                            handleFilterChange('maxYear', '2025');
                          }}
                          className="px-3 py-1 text-xs rounded-lg border hover:bg-gray-50"
                          style={{borderColor: '#ecf0f1'}}
                        >
                          New Construction (2020+)
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            handleFilterChange('minYear', '2000');
                            handleFilterChange('maxYear', '2019');
                          }}
                          className="px-3 py-1 text-xs rounded-lg border hover:bg-gray-50"
                          style={{borderColor: '#ecf0f1'}}
                        >
                          2000s Era
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            handleFilterChange('minYear', '1980');
                            handleFilterChange('maxYear', '1999');
                          }}
                          className="px-3 py-1 text-xs rounded-lg border hover:bg-gray-50"
                          style={{borderColor: '#ecf0f1'}}
                        >
                          1980s-90s
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Sales and Appraised Value Filters */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Sale Price</label>
                      <FormattedInput
                        placeholder="100000"
                        format="currency"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minSalePrice}
                        onChange={(value) => handleFilterChange('minSalePrice', value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Sale Price</label>
                      <FormattedInput
                        placeholder="500000"
                        format="currency"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxSalePrice}
                        onChange={(value) => handleFilterChange('maxSalePrice', value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Appraised Value</label>
                      <FormattedInput
                        placeholder="150000"
                        format="currency"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minAppraisedValue}
                        onChange={(value) => handleFilterChange('minAppraisedValue', value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Appraised Value</label>
                      <FormattedInput
                        placeholder="600000"
                        format="currency"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxAppraisedValue}
                        onChange={(value) => handleFilterChange('maxAppraisedValue', value)}
                      />
                    </div>
                  </div>

                  {/* Sale Date Range Filters */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Sale Date</label>
                      <Input
                        placeholder="YYYY or MM/DD/YYYY"
                        type="text"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minSaleDate}
                        onChange={(e) => {
                          const value = e.target.value.trim();
                          // Handle year-only input (e.g., "2023" → "2023-01-01")
                          if (/^\d{4}$/.test(value)) {
                            handleFilterChange('minSaleDate', `${value}-01-01`);
                          } else {
                            handleFilterChange('minSaleDate', value);
                          }
                        }}
                        onBlur={(e) => {
                          const value = e.target.value.trim();
                          // Convert year to date format on blur for display
                          if (/^\d{4}$/.test(value)) {
                            e.target.value = `${value}-01-01`;
                          }
                        }}
                      />
                      {!dateRangeLoading && minYear && maxYear ? (
                        <p className="text-xs" style={{color: '#27ae60'}}>
                          Available: {minYear}-{maxYear} ({totalSalesRecords?.toLocaleString() || '0'} sales records)
                        </p>
                      ) : dateRangeLoading ? (
                        <p className="text-xs" style={{color: '#95a5a6'}}>Loading available dates...</p>
                      ) : (
                        <p className="text-xs" style={{color: '#e74c3c'}}>No sales data found for this county</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Sale Date</label>
                      <Input
                        placeholder="YYYY or MM/DD/YYYY"
                        type="text"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxSaleDate}
                        onChange={(e) => {
                          const value = e.target.value.trim();
                          // Handle year-only input (e.g., "2023" → "2023-12-31")
                          if (/^\d{4}$/.test(value)) {
                            handleFilterChange('maxSaleDate', `${value}-12-31`);
                          } else {
                            handleFilterChange('maxSaleDate', value);
                          }
                        }}
                        onBlur={(e) => {
                          const value = e.target.value.trim();
                          // Convert year to date format on blur for display
                          if (/^\d{4}$/.test(value)) {
                            e.target.value = `${value}-12-31`;
                          }
                        }}
                      />
                      {!dateRangeLoading && minYear && maxYear ? (
                        <p className="text-xs" style={{color: '#27ae60'}}>
                          Tip: Try year only (e.g., {maxYear}) for quick filtering
                        </p>
                      ) : (
                        <p className="text-xs" style={{color: '#95a5a6'}}>Enter year (2023) or full date (12/31/2023)</p>
                      )}
                    </div>
                    <div className="col-span-2 flex items-end">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            const today = new Date();
                            const lastMonth = new Date(today);
                            lastMonth.setMonth(today.getMonth() - 1);
                            handleFilterChange('minSaleDate', lastMonth.toISOString().split('T')[0]);
                            handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                          }}
                          className="px-3 py-1 text-xs rounded-lg border hover:bg-gray-50"
                          style={{borderColor: '#ecf0f1'}}
                        >
                          Last 30 Days
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            const today = new Date();
                            const lastQuarter = new Date(today);
                            lastQuarter.setMonth(today.getMonth() - 3);
                            handleFilterChange('minSaleDate', lastQuarter.toISOString().split('T')[0]);
                            handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                          }}
                          className="px-3 py-1 text-xs rounded-lg border hover:bg-gray-50"
                          style={{borderColor: '#ecf0f1'}}
                        >
                          Last 90 Days
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            const today = new Date();
                            const lastYear = new Date(today);
                            lastYear.setFullYear(today.getFullYear() - 1);
                            handleFilterChange('minSaleDate', lastYear.toISOString().split('T')[0]);
                            handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                          }}
                          className="px-3 py-1 text-xs rounded-lg border hover:bg-gray-50"
                          style={{borderColor: '#ecf0f1'}}
                        >
                          Last Year
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            const today = new Date();
                            const yearStart = new Date(today.getFullYear(), 0, 1);
                            handleFilterChange('minSaleDate', yearStart.toISOString().split('T')[0]);
                            handleFilterChange('maxSaleDate', today.toISOString().split('T')[0]);
                          }}
                          className="px-3 py-1 text-xs rounded-lg border hover:bg-gray-50"
                          style={{borderColor: '#ecf0f1'}}
                        >
                          Year to Date
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Tax Status Filters */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                    <div className="col-span-2">
                      <label className="text-xs uppercase tracking-wider font-medium mb-3 block" style={{color: '#95a5a6'}}>
                        Tax Certificate Status
                      </label>
                      <div className="p-4 rounded-lg border" style={{
                        borderColor: filters.taxDelinquent ? '#d4af37' : '#ecf0f1',
                        background: filters.taxDelinquent ? 'rgba(212, 175, 55, 0.05)' : 'white'
                      }}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <input
                              type="checkbox"
                              id="taxDelinquent"
                              checked={filters.taxDelinquent}
                              onChange={(e) => handleFilterChange('taxDelinquent', e.target.checked)}
                              className="w-5 h-5 rounded border-gray-300 text-gold focus:ring-gold"
                              style={{accentColor: '#d4af37'}}
                            />
                            <label htmlFor="taxDelinquent" className="cursor-pointer">
                              <div className="flex items-center space-x-2">
                                <AlertTriangle className="w-4 h-4" style={{color: filters.taxDelinquent ? '#d4af37' : '#95a5a6'}} />
                                <span className="font-medium text-sm" style={{color: '#2c3e50'}}>
                                  Tax Delinquent Properties
                                </span>
                              </div>
                              <p className="text-xs mt-1" style={{color: '#7f8c8d'}}>
                                Show only properties with tax certificates in the last 7 years
                              </p>
                            </label>
                          </div>
                          {filters.taxDelinquent && (
                            <Badge className="bg-orange-100 text-orange-800 border-orange-200">
                              Filter Active
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="col-span-2 flex items-end">
                      <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 w-full">
                        <div className="flex items-start space-x-2">
                          <Info className="w-4 h-4 text-blue-600 mt-0.5" />
                          <div>
                            <p className="text-xs text-blue-800 font-medium">Investment Opportunity</p>
                            <p className="text-xs text-blue-600 mt-1">
                              Tax delinquent properties may offer investment opportunities but require careful due diligence.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Phase 1 Filters - Using Existing Database Columns */}
                  <div className="border-t-2 pt-6 mt-6" style={{borderColor: '#d4af37'}}>
                    <h3 className="text-lg font-semibold mb-4" style={{color: '#2c3e50'}}>Advanced Filters (Phase 1)</h3>

                    {/* Exemption and Sales Quality Filters */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Homestead Exemption:</label>
                        <select
                          className="w-full h-12 rounded-lg border px-4"
                          style={{borderColor: '#ecf0f1'}}
                          value={filters.hasHomesteadExemption}
                          onChange={(e) => handleFilterChange('hasHomesteadExemption', e.target.value)}
                        >
                          <option value="">Any</option>
                          <option value="true">Has Homestead</option>
                          <option value="false">No Homestead</option>
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Sales Quality:</label>
                        <select
                          className="w-full h-12 rounded-lg border px-4"
                          style={{borderColor: '#ecf0f1'}}
                          value={filters.qualifiedSaleOnly}
                          onChange={(e) => handleFilterChange('qualifiedSaleOnly', e.target.value)}
                        >
                          <option value="">All Sales</option>
                          <option value="true">Qualified Sales Only</option>
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Multi-Parcel Sales:</label>
                        <select
                          className="w-full h-12 rounded-lg border px-4"
                          style={{borderColor: '#ecf0f1'}}
                          value={filters.excludeMultiParcel}
                          onChange={(e) => handleFilterChange('excludeMultiParcel', e.target.value)}
                        >
                          <option value="">Include All</option>
                          <option value="true">Exclude Multi-Parcel</option>
                        </select>
                      </div>
                    </div>

                    {/* Location Detail Filters */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Subdivision:</label>
                        <Input
                          placeholder="e.g., Oak Hammock"
                          className="h-12 rounded-lg"
                          style={{borderColor: '#ecf0f1'}}
                          value={filters.subdivision}
                          onChange={(e) => handleFilterChange('subdivision', e.target.value)}
                        />
                        <p className="text-xs" style={{color: '#95a5a6'}}>Search by neighborhood or subdivision name</p>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Zoning:</label>
                        <Input
                          placeholder="e.g., R-1, C-2"
                          className="h-12 rounded-lg"
                          style={{borderColor: '#ecf0f1'}}
                          value={filters.zoning}
                          onChange={(e) => handleFilterChange('zoning', e.target.value)}
                        />
                        <p className="text-xs" style={{color: '#95a5a6'}}>Filter by zoning classification</p>
                      </div>
                    </div>
                  </div>

                  {/* Property Usage Code Filters */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
                    <div className="relative space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Usage Code (DOR Code)</label>
                      <Input
                        ref={usageCodeInputRef}
                        placeholder="e.g., 001 for Single Family"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.usageCode}
                        onChange={(e) => handleFilterChange('usageCode', e.target.value)}
                        onFocus={() => {
                          if (usageCodeSuggestions.length > 0) {
                            setShowUsageCodeSuggestions(true);
                          } else {
                            fetchUsageCodeSuggestions('');
                          }
                        }}
                        onBlur={() => {
                          setTimeout(() => setShowUsageCodeSuggestions(false), 200);
                        }}
                      />
                      <p className="text-xs" style={{color: '#95a5a6'}}>000-099: Residential | 100-399: Commercial | 400-499: Industrial</p>
                      
                      {/* Usage Code Autocomplete Dropdown */}
                      {showUsageCodeSuggestions && usageCodeSuggestions.length > 0 && (
                        <div className="absolute z-50 w-full mt-2 bg-white border rounded-lg shadow-lg max-h-60 overflow-auto" style={{ top: 'calc(100% - 20px)', borderColor: '#ecf0f1' }}>
                          {usageCodeSuggestions.map((suggestion, index) => (
                            <div
                              key={index}
                              className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                              style={{borderColor: '#ecf0f1'}}
                              onClick={() => {
                                const selectedCode = suggestion.code;
                                handleFilterChange('usageCode', selectedCode);
                                setShowUsageCodeSuggestions(false);
                                setTimeout(() => {
                                  if (usageCodeInputRef.current) {
                                    usageCodeInputRef.current.value = selectedCode;
                                    usageCodeInputRef.current.blur();
                                  }
                                }, 10);
                                fetchSubUsageCodeSuggestions('', selectedCode);
                                setTimeout(() => searchProperties(), 100);
                              }}
                            >
                              <div className="font-medium" style={{color: '#2c3e50'}}>{suggestion.code} - {suggestion.description}</div>
                              <div className="text-xs" style={{color: '#95a5a6'}}>{suggestion.category}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    
                    <div className="relative space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Sub-Usage Code</label>
                      <Input
                        ref={subUsageCodeInputRef}
                        placeholder="e.g., 00 for standard"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.subUsageCode}
                        onChange={(e) => handleFilterChange('subUsageCode', e.target.value)}
                        onFocus={() => {
                          if (filters.usageCode) {
                            fetchSubUsageCodeSuggestions('', filters.usageCode);
                          }
                        }}
                        onBlur={() => {
                          setTimeout(() => setShowSubUsageCodeSuggestions(false), 200);
                        }}
                        disabled={!filters.usageCode}
                      />
                      <p className="text-xs" style={{color: '#95a5a6'}}>Two-digit sub-classification</p>
                      
                      {/* Sub-Usage Code Autocomplete Dropdown */}
                      {showSubUsageCodeSuggestions && subUsageCodeSuggestions.length > 0 && (
                        <div className="absolute z-50 w-full mt-2 bg-white border rounded-lg shadow-lg max-h-60 overflow-auto" style={{ top: 'calc(100% - 20px)', borderColor: '#ecf0f1' }}>
                          {subUsageCodeSuggestions.map((suggestion, index) => (
                            <div
                              key={index}
                              className="px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
                              style={{borderColor: '#ecf0f1'}}
                              onClick={() => {
                                const selectedCode = suggestion.code;
                                handleFilterChange('subUsageCode', selectedCode);
                                setShowSubUsageCodeSuggestions(false);
                                setTimeout(() => {
                                  if (subUsageCodeInputRef.current) {
                                    subUsageCodeInputRef.current.value = selectedCode;
                                    subUsageCodeInputRef.current.blur();
                                  }
                                }, 10);
                                setTimeout(() => searchProperties(), 100);
                              }}
                            >
                              <span className="text-sm font-medium" style={{color: '#2c3e50'}}>{suggestion.display}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex justify-end mt-8 space-x-4">
                    <Button 
                      variant="outline" 
                      className="hover-lift h-12 px-6"
                      style={{borderColor: '#ecf0f1'}}
                      onClick={() => {
                        setFilters({
                          address: '',
                          city: '',
                          county: '',
                          zipCode: '',
                          owner: '',
                          propertyType: '',
                          minValue: '',
                          maxValue: '',
                          minYear: '',
                          maxYear: '',
                          minBuildingSqFt: '',
                          maxBuildingSqFt: '',
                          minLandSqFt: '',
                          maxLandSqFt: '',
                          minSalePrice: '',
                          maxSalePrice: '',
                          minAppraisedValue: '',
                          maxAppraisedValue: '',
                          minSaleDate: '',
                          maxSaleDate: '',
                          usageCode: '',
                          subUsageCode: '',
                          taxDelinquent: false
                        });
                        setCurrentPage(1);
                      }}
                    >
                      <span style={{color: '#2c3e50'}}>Clear All</span>
                    </Button>
                    <Button
                      className="h-12 px-6 hover-lift relative overflow-hidden transition-all duration-300"
                      style={{
                        background: loading ? '#b8962d' : '#d4af37',
                        borderColor: loading ? '#b8962d' : '#d4af37',
                        opacity: loading ? 0.9 : 1,
                        transform: loading ? 'scale(0.98)' : 'scale(1)',
                        boxShadow: loading ? '0 0 20px rgba(212, 175, 55, 0.5)' : '0 2px 4px rgba(0,0,0,0.1)'
                      }}
                      onClick={() => searchProperties(1)}
                      disabled={loading}
                    >
                      {loading && (
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"
                             style={{
                               backgroundSize: '200% 100%',
                               animation: 'shimmer 1.5s infinite'
                             }}
                        />
                      )}
                      <div className="flex items-center gap-2 relative z-10">
                        {loading && (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        )}
                        <span>{loading ? 'Processing...' : 'Apply Filters'}</span>
                      </div>
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Results Header - Clean Design */}
        {!showTaxDeedSales && (
        <div className="elegant-card hover-lift animate-in mb-6">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <h3 className="text-xl font-semibold" style={{color: '#2c3e50'}}>
                  {totalResults.toLocaleString()} Properties Found
                </h3>
                {filters.city && filters.city !== 'all-cities' && filters.city !== '' && (
                  <div className="badge-elegant" style={{borderColor: '#3498db', color: '#3498db', background: 'rgba(52, 152, 219, 0.1)'}}>
                    <MapPin className="w-3 h-3 mr-1" />
                    {filters.city}
                  </div>
                )}
                {filters.county && filters.county !== '' && (
                  <div className="badge-elegant" style={{borderColor: '#e67e22', color: '#e67e22', background: 'rgba(230, 126, 34, 0.1)'}}>
                    <Building2 className="w-3 h-3 mr-1" />
                    {filters.county}
                  </div>
                )}
                {filters.propertyType && filters.propertyType !== 'all-types' && (
                  <div className="badge-elegant" style={{borderColor: '#9b59b6', color: '#9b59b6', background: 'rgba(155, 89, 182, 0.1)'}}>
                    <Building className="w-3 h-3 mr-1" />
                    {filters.propertyType}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-3">
                <div className="flex border rounded-lg" style={{borderColor: '#ecf0f1'}}>
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    size="sm"
                    className="hover-lift"
                    style={viewMode === 'grid' ? {background: '#d4af37', borderColor: '#d4af37'} : {}}
                    onClick={() => setViewMode('grid')}
                  >
                    <Grid3X3 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'ghost'}
                    size="sm"
                    className="hover-lift"
                    style={viewMode === 'list' ? {background: '#d4af37', borderColor: '#d4af37'} : {}}
                    onClick={() => setViewMode('list')}
                  >
                    <List className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Selection Controls - Executive Design */}
            <div className="flex items-center space-x-3">
              <button
                className="px-4 py-2 rounded-lg transition-all duration-300 flex items-center space-x-2 hover:shadow-md"
                style={{
                  background: isAllPropertiesSelected 
                    ? 'linear-gradient(135deg, #d4af37 0%, #b8941f 100%)' 
                    : 'white',
                  border: isAllPropertiesSelected 
                    ? '1px solid #d4af37' 
                    : '1px solid #ecf0f1',
                  color: isAllPropertiesSelected ? 'white' : '#2c3e50',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '400',
                  letterSpacing: '0.5px'
                }}
                onClick={selectAllProperties}
              >
                {isAllPropertiesSelected ? (
                  <CheckSquare className="w-4 h-4" />
                ) : (
                  <Square className="w-4 h-4" />
                )}
                <span>
                  {isAllPropertiesSelected ? 'Unselect All' : 'Select All'} 
                  {totalResults > 0 && ` (${totalResults})`}
                </span>
              </button>
              
              <button
                className="px-4 py-2 rounded-lg transition-all duration-300 flex items-center space-x-2 hover:shadow-md"
                style={{
                  background: isAllCurrentPageSelected 
                    ? 'linear-gradient(135deg, #d4af37 0%, #b8941f 100%)' 
                    : 'white',
                  border: isAllCurrentPageSelected 
                    ? '1px solid #d4af37' 
                    : '1px solid #ecf0f1',
                  color: isAllCurrentPageSelected ? 'white' : '#2c3e50',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '400',
                  letterSpacing: '0.5px'
                }}
                onClick={selectAllFromPage}
              >
                {isAllCurrentPageSelected ? (
                  <CheckSquare className="w-4 h-4" />
                ) : (
                  <Square className="w-4 h-4" />
                )}
                <span>
                  {isAllCurrentPageSelected ? 'Unselect Page' : 'Select Page'}
                  {properties.length > 0 && ` (${properties.length})`}
                </span>
              </button>

              {/* Selection Count Badge */}
              {selectedProperties.size > 0 && (
                <div 
                  className="px-3 py-1 rounded-full"
                  style={{
                    background: 'rgba(212, 175, 55, 0.1)',
                    border: '1px solid #d4af37',
                    color: '#d4af37',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  {selectedProperties.size} selected
                </div>
              )}
            </div>
          </div>
        </div>
        )}

        {/* Map View */}
        {showMapView && properties.length > 0 && (
          <PropertyMap
            properties={selectedProperties.size > 0 
              ? properties.filter(property => selectedProperties.has(String(property.parcel_id || property.id)))
              : properties
            }
            onPropertySelect={(property) => {
              setSelectedProperty(property);
              handlePropertyClick(property);
            }}
            onClose={() => setShowMapView(false)}
            selectedProperty={selectedProperty}
            showingSelectedOnly={selectedProperties.size > 0}
            totalSelected={selectedProperties.size}
          />
        )}

        {/* Tax Deed Sales Tab Content */}
        {showTaxDeedSales && (
          <div className="animate-in">
            <TaxDeedSalesTab />
          </div>
        )}

        {/* Results */}
        {!showMapView && !showTaxDeedSales && (
          loading ? (
            <div className="text-center py-20">
              <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-6" style={{ color: '#d4af37' }} />
              <p className="text-xl font-medium mb-2" style={{ color: '#2c3e50' }}>Searching Properties...</p>
              <p className="text-sm" style={{ color: '#7f8c8d' }}>Loading premium Florida property data</p>
            </div>
          ) : (
            <>
              {/* Pagination Display */}
              {properties.length > 0 && (
                <div className="mb-6 flex items-center justify-between px-4 py-3 rounded-lg" style={{ backgroundColor: '#f8f9fa', borderLeft: '4px solid #d4af37' }}>
                  <div className="flex items-center space-x-3">
                    {hasActiveFilters && (
                      <Badge variant="outline" style={{ borderColor: '#d4af37', color: '#d4af37' }}>
                        Filtered Results
                      </Badge>
                    )}
                  </div>
                  <span className="text-sm" style={{ color: '#7f8c8d' }}>
                    Page {currentPage} of {totalPages}
                  </span>
                </div>
              )}
              {properties.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <Search className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">No Properties Found</h3>
                  <p className="text-gray-600 mb-4">
                    Try adjusting your search criteria or browse by city
                  </p>

                  {/* Smart sale date guidance */}
                  {(filters.minSaleDate || filters.maxSaleDate) && minYear && maxYear && (
                    <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg max-w-md mx-auto">
                      <div className="flex items-start space-x-3">
                        <Info className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                        <div className="text-left">
                          <p className="text-sm font-medium text-yellow-900 mb-1">
                            Sale Date Filter Active
                          </p>
                          <p className="text-xs text-yellow-700">
                            No properties found with sales in your date range.
                            Available sales data: {minYear}-{maxYear}
                          </p>
                          <button
                            onClick={() => {
                              handleFilterChange('minSaleDate', '');
                              handleFilterChange('maxSaleDate', '');
                              searchProperties();
                            }}
                            className="text-xs text-yellow-800 underline hover:text-yellow-900 mt-2"
                          >
                            Clear sale date filters
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-center space-x-2">
                    {popularCities.slice(0, 3).map(city => (
                      <Button
                        key={city}
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          handleFilterChange('city', city);
                          searchProperties();
                        }}
                      >
                        {city}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <>
                {/* FIXED: Display info if more properties are available */}
                {totalResults > properties.length && (
                  <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-blue-900">
                          Showing {properties.length.toLocaleString()} of {totalResults.toLocaleString()} Properties
                        </p>
                        <p className="text-xs text-blue-700 mt-1">
                          {totalResults - properties.length > 0 && `${(totalResults - properties.length).toLocaleString()} more properties match your search. `}
                          Scroll down or click "Load More" to see additional results.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* PHASE 3: Virtual Scrolling for Performance - Renders only visible properties */}
                <VirtualizedPropertyList
                  properties={properties.map(transformPropertyData)}
                  hasNextPage={hasMore}
                  isNextPageLoading={loading}
                  loadNextPage={async () => {
                    if (!loading && hasMore) {
                      await searchProperties(currentPage + 1);
                    }
                  }}
                  onPropertyClick={handlePropertyClick}
                  viewMode={viewMode}
                  height={800}
                  selectedProperties={selectedProperties}
                  onToggleSelection={togglePropertySelection}
                  batchSalesData={batchSalesData}
                  isBatchLoading={batchLoading}
                />

                {/* Load More Button (backup for manual loading) */}
                {hasMore && !loading && (
                  <div className="mt-8 text-center py-4">
                    <Button
                      onClick={() => searchProperties(currentPage + 1)}
                      size="lg"
                      className="px-8 py-4"
                        style={{
                          backgroundColor: '#d4af37',
                          color: 'white',
                          fontSize: '16px',
                          fontWeight: '500'
                        }}
                      >
                        Load More Properties
                        <span className="ml-2 text-sm opacity-90">
                          ({remainingCount.toLocaleString()} remaining)
                        </span>
                      </Button>
                    </div>
                  )}

                {/* Property count and progress bar */}
                {properties.length > 0 && (
                  <div className="mt-8 text-center">
                    <div className="mt-4 space-y-2">
                      <p className="text-sm text-gray-600">
                        Showing {properties.length.toLocaleString()} of {totalResults.toLocaleString()} total properties
                      </p>
                      <div className="w-full max-w-md mx-auto">
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full transition-all duration-500"
                            style={{
                              width: `${percentLoaded}%`,
                              backgroundColor: '#d4af37'
                            }}
                          />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{percentLoaded}% loaded</p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Elegant Pagination Footer */}
            {totalResults > pageSize && (
              <div className="elegant-card hover-lift animate-in mt-8">
                <div className="p-6">
                  <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
                    {/* Page Size Selector */}
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-medium" style={{color: '#2c3e50'}}>Show per page:</span>
                      <Select
                        value={pageSize.toString()}
                        onValueChange={(value) => {
                          const newPageSize = parseInt(value);
                          setPageSize(newPageSize);
                          setCurrentPage(1);
                          // Trigger search with new page size
                          searchPropertiesRef.current(1);
                        }}
                      >
                        <SelectTrigger className="w-20 h-9 rounded-lg" style={{borderColor: '#ecf0f1'}}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="10">10</SelectItem>
                          <SelectItem value="20">20</SelectItem>
                          <SelectItem value="50">50</SelectItem>
                          <SelectItem value="100">100</SelectItem>
                        </SelectContent>
                      </Select>
                      <span className="text-sm" style={{color: '#7f8c8d'}}>
                        Showing {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, totalResults)} of {totalResults.toLocaleString()} properties
                      </span>
                    </div>

                    {/* Page Navigation */}
                    <div className="flex items-center space-x-2">
                      {/* First Page Button */}
                      <Button
                        variant="outline"
                        disabled={currentPage === 1}
                        className="hover-lift h-9 px-3"
                        style={{borderColor: '#ecf0f1'}}
                        onClick={() => searchProperties(1)}
                        title="First page"
                      >
                        <span style={{color: '#2c3e50'}}>««</span>
                      </Button>

                      <Button
                        variant="outline"
                        disabled={currentPage === 1}
                        className="hover-lift h-9 px-4"
                        style={{borderColor: '#ecf0f1'}}
                        onClick={() => searchProperties(currentPage - 1)}
                      >
                        <span style={{color: '#2c3e50'}}>Previous</span>
                      </Button>

                      <div className="flex items-center space-x-1">
                        {(() => {
                          const pages = [];
                          let startPage = Math.max(1, currentPage - 2);
                          let endPage = Math.min(totalPages, startPage + 4);

                          // Adjust startPage if we're near the end
                          if (endPage - startPage < 4) {
                            startPage = Math.max(1, endPage - 4);
                          }

                          // Add first page if not in range
                          if (startPage > 1) {
                            pages.push(
                              <Button
                                key={1}
                                variant="outline"
                                size="sm"
                                className="hover-lift h-9 w-9"
                                style={{borderColor: '#ecf0f1', color: '#2c3e50'}}
                                onClick={() => searchProperties(1)}
                              >
                                1
                              </Button>
                            );
                            if (startPage > 2) {
                              pages.push(<span key="start-ellipsis" className="px-2" style={{color: '#7f8c8d'}}>...</span>);
                            }
                          }

                          // Add page buttons in range
                          for (let page = startPage; page <= endPage; page++) {
                            pages.push(
                              <Button
                                key={page}
                                variant={currentPage === page ? 'default' : 'outline'}
                                size="sm"
                                className="hover-lift h-9 w-9"
                                style={currentPage === page ?
                                  {background: '#d4af37', borderColor: '#d4af37', color: 'white'} :
                                  {borderColor: '#ecf0f1', color: '#2c3e50'}
                                }
                                onClick={() => searchProperties(page)}
                              >
                                {page}
                              </Button>
                            );
                          }

                          // Add last page if not in range
                          if (endPage < totalPages) {
                            if (endPage < totalPages - 1) {
                              pages.push(<span key="end-ellipsis" className="px-2" style={{color: '#7f8c8d'}}>...</span>);
                            }
                            pages.push(
                              <Button
                                key={totalPages}
                                variant="outline"
                                size="sm"
                                className="hover-lift h-9 w-9"
                                style={{borderColor: '#ecf0f1', color: '#2c3e50'}}
                                onClick={() => searchProperties(totalPages)}
                              >
                                {totalPages}
                              </Button>
                            );
                          }

                          return pages;
                        })()}
                      </div>

                      {/* Page Jump Input */}
                      <div className="flex items-center space-x-2 ml-2">
                        <span className="text-sm" style={{color: '#7f8c8d'}}>Go to:</span>
                        <input
                          type="number"
                          min="1"
                          max={totalPages}
                          placeholder={currentPage.toString()}
                          className="w-20 h-9 px-2 text-center border rounded-lg focus:outline-none focus:ring-2 focus:ring-[#d4af37]"
                          style={{borderColor: '#ecf0f1'}}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              const page = parseInt(e.currentTarget.value);
                              if (page >= 1 && page <= totalPages) {
                                searchProperties(page);
                                e.currentTarget.value = '';
                              }
                            }
                          }}
                        />
                      </div>

                      <Button
                        variant="outline"
                        disabled={currentPage >= totalPages}
                        className="hover-lift h-9 px-4"
                        style={{borderColor: '#ecf0f1'}}
                        onClick={() => searchProperties(currentPage + 1)}
                      >
                        <span style={{color: '#2c3e50'}}>Next</span>
                      </Button>

                      {/* Last Page Button */}
                      <Button
                        variant="outline"
                        disabled={currentPage >= totalPages}
                        className="hover-lift h-9 px-3"
                        style={{borderColor: '#ecf0f1'}}
                        onClick={() => searchProperties(totalPages)}
                        title="Last page"
                      >
                        <span style={{color: '#2c3e50'}}>»»</span>
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
              )}
            </>
          )
        )}
        </>
        )}
      </div>

      {/* AI Chatbox - Floating Assistant */}
      {/* Note: Backend service (port 8003) requires OpenAI billing to be active */}
      <AIChatbox
        position="bottom-right"
        initialOpen={false}
        onPropertySelect={(property) => handlePropertyClick(property)}
      />
    </div>
  );
}

export default PropertySearch;