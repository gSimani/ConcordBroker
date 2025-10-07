import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { FormattedInput } from '@/components/ui/formatted-input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { SearchableSelect } from '@/components/ui/searchable-select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MiniPropertyCard } from '@/components/property/MiniPropertyCard';
import { PropertyMap } from '@/components/property/PropertyMap';
import { AISearchEnhanced } from '@/components/ai/AISearchEnhanced';
import { TaxDeedSalesTab } from '@/components/property/tabs/TaxDeedSalesTab';
import { useDataPipeline } from '@/lib/data-pipeline';
import { useOptimizedPropertySearch } from '@/hooks/useOptimizedPropertySearch';
import { api } from '@/api/client';
import { OptimizedSearchBar } from '@/components/OptimizedSearchBar';
import { AutocompleteSearchBar } from '@/components/AutocompleteSearchBar';
import { getPropertyTypeFilter, matchesPropertyTypeFilter } from '@/lib/dorUseCodes';
import { getAllUseCategories, UseIcon } from '@/lib/icons/useIcons';
import {
  getDORCodeSuggestions,
  getSubCodeSuggestions,
  getDORCodesForPropertyType,
  mapPropertyTypeToUseCategories,
  getPropertyUseValuesForType,
  mapPropertyTypeToPropertyUseValues
} from '@/services/dorCodeService';
import { DOR_USE_CODES } from '@/lib/dorUseCodes';
import '@/styles/elegant-property.css';
import {
  Search,
  Filter,
  MapPin,
  Grid3X3,
  List,
  SlidersHorizontal,
  TrendingUp,
  Building,
  Building2,
  Home,
  RefreshCw,
  Download,
  Map,
  CheckSquare,
  Square,
  CheckCircle2,
  Circle,
  Briefcase,
  TreePine,
  AlertTriangle,
  Info,
  Brain,
  Sparkles,
  Gavel
} from 'lucide-react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';

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
}

export function PropertySearch({}: PropertySearchProps) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [searchResults, setSearchResults] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50); // Optimized for 6.4M properties
  const [totalPages, setTotalPages] = useState(0);
  const [pagination, setPagination] = useState<any>(null);
  const [showMapView, setShowMapView] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<any>(null);
  const [selectedProperties, setSelectedProperties] = useState<Set<string>>(new Set());
  const [mapButtonHovered, setMapButtonHovered] = useState(false);
  const [showAISearch, setShowAISearch] = useState(false);
  const [showTaxDeedSales, setShowTaxDeedSales] = useState(false);
  const [diagStatus, setDiagStatus] = useState<'pending' | 'ok' | 'fail'>('pending');

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
    taxDelinquent: false
  });

  // Autocomplete state
  const [addressSuggestions, setAddressSuggestions] = useState<string[]>([]);
  const [showAddressSuggestions, setShowAddressSuggestions] = useState(false);
  const [citySuggestions, setCitySuggestions] = useState<string[]>([]);
  const [showCitySuggestions, setShowCitySuggestions] = useState(false);
  const [ownerSuggestions, setOwnerSuggestions] = useState<string[]>([]);
  const [showOwnerSuggestions, setShowOwnerSuggestions] = useState(false);
  const [mainSearchSuggestions, setMainSearchSuggestions] = useState<any[]>([]);
  const [showMainSearchSuggestions, setShowMainSearchSuggestions] = useState(false);
  const [usageCodeSuggestions, setUsageCodeSuggestions] = useState<any[]>([]);
  const [showUsageCodeSuggestions, setShowUsageCodeSuggestions] = useState(false);
  const [subUsageCodeSuggestions, setSubUsageCodeSuggestions] = useState<any[]>([]);
  const [showSubUsageCodeSuggestions, setShowSubUsageCodeSuggestions] = useState(false);
  const addressInputRef = useRef<HTMLInputElement>(null);
  const cityInputRef = useRef<HTMLInputElement>(null);
  const ownerInputRef = useRef<HTMLInputElement>(null);
  const usageCodeInputRef = useRef<HTMLInputElement>(null);
  const subUsageCodeInputRef = useRef<HTMLInputElement>(null);
  const autocompleteTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isInitialMount = useRef(true);
  const pipeline = useDataPipeline();
  const optimizedSearch = useOptimizedPropertySearch();

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

  // Fetch usage code suggestions using DOR code service
  const fetchUsageCodeSuggestions = async (query: string) => {
    try {
      const suggestions = getDORCodeSuggestions(query, filters.propertyType);
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
      const suggestions = getSubCodeSuggestions(mainUsageCode, query);
      setSubUsageCodeSuggestions(suggestions);
      setShowSubUsageCodeSuggestions(suggestions.length > 0);
    } catch (error) {
      console.error('Error fetching sub-usage code suggestions:', error);
    }
  };

  // Initial load effect with optimized search
  useEffect(() => {
    console.log('Initial mount - loading properties...');
    // Use optimized search for initial load
    searchProperties();
  }, []); // Only run once on mount

  // Lightweight diagnostics: ping health and search endpoints on 8001
  useEffect(() => {
    const controller = new AbortController();
    const runQuickDiagnostics = async () => {
      setDiagStatus('pending');
      const timeout = (ms: number) => new Promise((_, r) => setTimeout(() => r(new Error('timeout')), ms));
      try {
        const health = fetch('http://localhost:8001/health', { signal: controller.signal });
        const search = fetch('http://localhost:8001/api/properties/search?limit=1', { signal: controller.signal });
        const res = await Promise.race([
          Promise.all([health, search]),
          timeout(4000)
        ]) as Response[];
        if (Array.isArray(res) && res.length === 2 && res.every(r => (r as any).ok)) {
          setDiagStatus('ok');
        } else {
          setDiagStatus('fail');
        }
      } catch {
        setDiagStatus('fail');
      }
    };
    runQuickDiagnostics();
    return () => controller.abort();
  }, []);

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

    // Immediate search for category toggles (no debounce needed)
    if (filters.propertyType !== '' || filters.hasPool || filters.hasWaterfront) {
      console.log('Category filter changed - immediate search:', {
        propertyType: filters.propertyType,
        hasPool: filters.hasPool,
        hasWaterfront: filters.hasWaterfront
      });
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
        console.log('Debounced auto-search triggered with filters:', filters);
        searchProperties(1);
      }, 300); // Debounce for comprehensive search
    } else {
      // No filters applied - show default results
      console.log('No filters applied - showing default results');
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

  // Use centralized icon mapping for property types
  const propertyTypes = getAllUseCategories()
    .filter(cat => cat.value) // Only include categories with a value (exclude 'All')
    .map(cat => ({
      value: cat.label,
      label: cat.label,
      icon: cat.config.icon,
      color: cat.config.color
    }));

  // Optimized search with data pipeline - using ref to avoid stale closure
  const searchPropertiesRef = useRef<(page?: number) => Promise<void>>();
  
  const searchProperties = useCallback(async (page = 1) => {
    console.log('searchProperties called with page:', page);
    setLoading(true);
    try {
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
        subUsageCode: 'sub_usage_code'
      };

      Object.entries(filters).forEach(([key, value]) => {
        // Handle propertyType separately since it can be empty string for "All Properties"
        if (key === 'propertyType') {
          if (value && value !== '') {
            // NEW: Use actual database property_use values for filtering
            const propertyUseValues = getPropertyUseValuesForType(value as string);

            if (propertyUseValues.length > 0) {
              // Send property_use values as comma-separated string
              // The API will filter on property_use field with these integer values
              apiFilters['property_use_values'] = propertyUseValues.join(',');
            }

            // LEGACY: Convert property type to use categories for backward compatibility
            const useCategories = mapPropertyTypeToUseCategories(value as string);
            const dorCodes = getDORCodesForPropertyType(value as string);

            if (useCategories.length > 0) {
              // Send use categories as 'use' parameter (what API expects)
              apiFilters['use'] = useCategories.join(',');
            }

            if (dorCodes.length > 0) {
              // Send first DOR code as 'usage_code' parameter (what API expects)
              apiFilters['usage_code'] = dorCodes[0];
            }

            // Keep property type for backward compatibility
            apiFilters['property_type'] = value;
          }
          // If propertyType is empty, don't add any filtering (show all properties)
        } else if (value && value !== 'all-cities' && value !== 'all-types' && value !== '') {
          // Skip taxDelinquent as it needs special handling
          if (key === 'taxDelinquent') {
            if (value === true) {
              apiFilters['has_tax_certificates'] = true;
              apiFilters['certificate_years'] = 7; // Look back 7 years
            }
          } else {
            const apiKey = keyMap[key] || key;
            // Parse numeric values for min/max filters
            if (key.startsWith('min') || key.startsWith('max')) {
              const numValue = parseFloat(value.toString().replace(/[$,]/g, ''));
              if (!isNaN(numValue)) {
                apiFilters[apiKey] = numValue;
              }
            } else {
              apiFilters[apiKey] = value;
            }
          }
        }
      });
      
      apiFilters.limit = pageSize.toString();
      apiFilters.offset = ((page - 1) * pageSize).toString();
      
      console.log('Fast pipeline search:', apiFilters);
      
      // Use API client for property search
      const params = new URLSearchParams();
      Object.entries(apiFilters).forEach(([key, value]) => {
        if (value && value !== '' && value !== 'all-cities' && value !== 'all-types') {
          params.append(key, value.toString());
        }
      });

      let data;
      try {
        // Direct fetch to fast API to bypass any axios issues
        const queryString = params.toString() || 'limit=50';
        const response = await fetch(`http://localhost:8001/api/properties/search?${queryString}`);

        if (response.ok) {
          const jsonData = await response.json();
          console.log('Direct API response:', jsonData);

          // Transform to expected format - handle both old and new API response formats
          data = {
            properties: jsonData.properties || jsonData.data || [],
            data: jsonData.data || jsonData.properties || [],
            total: jsonData.total || jsonData.pagination?.total || jsonData.total_found || 0,
            pagination: jsonData.pagination
          };
        } else {
          throw new Error(`API returned ${response.status}`);
        }
      } catch (apiError) {
        console.log('Direct fetch failed, trying axios client:', apiError);

        // Try the axios client as fallback
        try {
          data = await api.searchProperties(params);
          console.log('Axios API response received:', data);
        } catch (axiosError) {
          console.log('Axios also failed, using empty fallback:', axiosError);
          // Return empty result as final fallback
          data = {
            properties: [],
            total: 0,
            source: 'fallback'
          };
        }
      }

      console.log('Pipeline results:', data);
      // Handle both data.properties and data.data formats
      let propertyList = data.properties || data.data || [];

      // DISABLED: Client-side filtering - API should handle all filtering
      if (false && filters.propertyType && filters.propertyType !== 'all-types') {
        console.log('Applying client-side DOR code filtering for:', filters.propertyType);
        const filteredList = propertyList.filter((property: any) => {
          const dorCode = property.dor_uc || property.propertyUse || property.property_use_code;
          const ownerName = (property.owner || property.owner_name || '').toUpperCase();

          // First check DOR code
          if (dorCode && matchesPropertyTypeFilter(dorCode, filters.propertyType)) {
            return true;
          }

          // For properties without DOR codes, check owner-based categorization
          if (!dorCode || dorCode === '') {
            const propertyTypeUpper = filters.propertyType.toUpperCase();

            // Government properties
            if (propertyTypeUpper === 'GOVERNMENT' || propertyTypeUpper === 'GOVERNMENTAL') {
              if (ownerName.includes('TRUSTEE') || ownerName.includes('BRD OF') ||
                  ownerName.includes('BOARD OF') || ownerName.includes('STATE OF') ||
                  ownerName.includes('COUNTY') || ownerName.includes('CITY OF')) {
                return true;
              }
            }

            // Religious properties
            if (propertyTypeUpper === 'RELIGIOUS') {
              if (ownerName.includes('CHURCH') || ownerName.includes('BAPTIST') ||
                  ownerName.includes('METHODIST') || ownerName.includes('CATHOLIC') ||
                  ownerName.includes('SYNAGOGUE') || ownerName.includes('TEMPLE') ||
                  ownerName.includes('MOSQUE')) {
                return true;
              }
            }

            // Conservation properties
            if (propertyTypeUpper === 'CONSERVATION') {
              if (ownerName.includes('CONSERVANCY') || ownerName.includes('NATURE') ||
                  ownerName.includes('FORESTRY') || ownerName.includes('PARK') ||
                  ownerName.includes('PRESERVE') || ownerName.includes('WILDLIFE') ||
                  ownerName.includes('AG FORESTRY') || ownerName.includes('TIITF/AG')) {
                return true;
              }
            }

            // Residential properties - individual names (not corporations/government/institutions)
            if (propertyTypeUpper === 'RESIDENTIAL') {
              const isIndividual = !ownerName.includes('CORP') && !ownerName.includes('LLC') &&
                                 !ownerName.includes('INC') && !ownerName.includes('COMPANY') &&
                                 !ownerName.includes('TRUSTEE') && !ownerName.includes('BRD OF') &&
                                 !ownerName.includes('CHURCH') && !ownerName.includes('BAPTIST') &&
                                 !ownerName.includes('TIITF') && !ownerName.includes('CONSERVANCY') &&
                                 !ownerName.includes('FORESTRY') && !ownerName.includes('STATE OF') &&
                                 !ownerName.includes('COUNTY') && !ownerName.includes('CITY OF') &&
                                 ownerName.includes(' ') && ownerName.length > 5 &&
                                 // Must contain typical individual name patterns
                                 (ownerName.includes(' & ') || ownerName.match(/[A-Z]+ [A-Z]+/));
              console.log(`  Residential check: isIndividual=${isIndividual}, ownerName="${ownerName}"`);
              return isIndividual;
            }

            // Commercial properties - corporations, LLCs, businesses
            if (propertyTypeUpper === 'COMMERCIAL') {
              const isBusiness = ownerName.includes('CORP') || ownerName.includes('LLC') ||
                                ownerName.includes('INC') || ownerName.includes('COMPANY') ||
                                ownerName.includes('PROPERTIES') || ownerName.includes('ENTERPRISES') ||
                                ownerName.includes('DEVELOPMENT') || ownerName.includes('INVESTMENTS');
              console.log(`  Commercial check: ${isBusiness}`);
              return isBusiness;
            }

            // Industrial properties - manufacturing, warehouse terms
            if (propertyTypeUpper === 'INDUSTRIAL') {
              const isIndustrial = ownerName.includes('MANUFACTURING') || ownerName.includes('INDUSTRIAL') ||
                                 ownerName.includes('WAREHOUSE') || ownerName.includes('LOGISTICS') ||
                                 ownerName.includes('DISTRIBUTION') || ownerName.includes('FACTORY');
              console.log(`  Industrial check: ${isIndustrial}`);
              return isIndustrial;
            }

            // Agricultural properties - farming, agriculture
            if (propertyTypeUpper === 'AGRICULTURAL') {
              const isAgricultural = ownerName.includes('FARM') || ownerName.includes('RANCH') ||
                                   ownerName.includes('AGRICULTURE') || ownerName.includes('GROVE') ||
                                   ownerName.includes('NURSERY') || ownerName.includes('AG ');
              console.log(`  Agricultural check: ${isAgricultural}`);
              return isAgricultural;
            }

            // Vacant Land - no address but has value, not government/institutional
            if (propertyTypeUpper === 'VACANT' || propertyTypeUpper === 'VACANT LAND') {
              const address = property.address || property.phy_addr1 || '';
              const noAddress = !address || address === '-' || address.trim() === '';
              const marketValue = property.marketValue || property.just_value || property.jv || 0;
              const notGovernment = !ownerName.includes('TRUSTEE') && !ownerName.includes('BRD OF') &&
                                  !ownerName.includes('TIITF') && !ownerName.includes('CONSERVANCY');
              const notReligious = !ownerName.includes('CHURCH') && !ownerName.includes('BAPTIST');
              const isVacant = noAddress && marketValue > 0 && notGovernment && notReligious;
              console.log(`  Vacant check: noAddress=${noAddress}, hasValue=${marketValue > 0}, notGov=${notGovernment}, result=${isVacant}`);
              return isVacant;
            }

            // Vacant/Special - properties with value but no use code
            if (propertyTypeUpper === 'VACANT/SPECIAL') {
              if (property.just_value || property.marketValue || property.jv) {
                return true;
              }
            }
          }

          return false;
        });
        console.log(`Filtered from ${propertyList.length} to ${filteredList.length} properties`);
        propertyList = filteredList;
      }

      console.log('Setting properties:', propertyList.length, 'items');
      if (propertyList.length > 0) {
        console.log('First property sample:', {
          parcel_id: propertyList[0]?.parcel_id,
          owner: propertyList[0]?.owner,
          address: propertyList[0]?.address,
          marketValue: propertyList[0]?.marketValue,
          // Debug sales data fields
          last_qualified_sale: propertyList[0]?.last_qualified_sale,
          has_qualified_sale: propertyList[0]?.has_qualified_sale,
          sale_price: propertyList[0]?.sale_price,
          sale_date: propertyList[0]?.sale_date,
          // Show all available keys for debugging
          available_keys: Object.keys(propertyList[0] || {}).filter(key =>
            key.toLowerCase().includes('sale') || key.toLowerCase().includes('price')
          )
        });
      }
      setProperties(propertyList);

      // Handle pagination metadata from optimized API
      if (data.pagination) {
        setTotalResults(data.pagination.total || propertyList.length);
        setTotalPages(data.pagination.total_pages || Math.ceil((data.pagination.total || propertyList.length) / pageSize));
        setPagination(data.pagination);
      } else {
        setTotalResults(data.total || propertyList.length);
        setTotalPages(Math.ceil((data.total || propertyList.length) / pageSize));
      }
      setCurrentPage(page);
      
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Search error:', error);
      }
    } finally {
      setLoading(false);
    }
  }, [filters, pipeline, pageSize]);
  
  searchPropertiesRef.current = searchProperties;

  // Handle regular search from autocomplete
  const handleSearch = () => {
    searchProperties(1);
  };

  // Handle search with suggestion data
  const handleSearchWithSuggestion = (suggestion: any) => {
    // Set filters based on suggestion data
    setFilters(prev => ({
      ...prev,
      address: suggestion.address || '',
      city: suggestion.city || prev.city,
      owner: suggestion.owner_name || prev.owner
    }));
    // Trigger search
    searchProperties(1);
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof SearchFilters, value: string | boolean) => {
    console.log(`handleFilterChange: ${key} = ${value}`); // Debug log
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));

    // Clear existing timeout
    if (autocompleteTimeoutRef.current) {
      clearTimeout(autocompleteTimeoutRef.current);
    }

    // Trigger autocomplete with debouncing
    if (key === 'address' || key === 'city' || key === 'owner' || key === 'usageCode' || key === 'subUsageCode') {
      autocompleteTimeoutRef.current = setTimeout(() => {
        if (key === 'address') {
          fetchAddressSuggestions(value);
          // Also trigger main search suggestions
          fetchMainSearchSuggestions(value);
        } else if (key === 'city') {
          fetchCitySuggestions(value);
        } else if (key === 'owner') {
          fetchOwnerSuggestions(value);
        } else if (key === 'usageCode') {
          fetchUsageCodeSuggestions(value);
        } else if (key === 'subUsageCode') {
          fetchSubUsageCodeSuggestions(value, filters.usageCode);
        }
      }, 300); // 300ms debounce
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
      if (addressData && addressData.properties) {
        const addresses = [...new Set(addressData.properties.map((p: any) => p.phy_addr1).filter(Boolean) || [])].slice(0, 5);
        addresses.forEach((addr: string) => suggestions.push({ type: 'address', value: addr, display: `📍 ${addr}` }));
      }

      // Process city results
      if (cityData && cityData.properties) {
        const cities = [...new Set(cityData.properties.map((p: any) => p.phy_city).filter(Boolean) || [])].slice(0, 3);
        cities.forEach((city: string) => suggestions.push({ type: 'city', value: city, display: `🏘️ ${city}` }));
      }

      // Process owner results
      if (ownerData && ownerData.properties) {
        const owners = [...new Set(ownerData.properties.map((p: any) => p.own_name).filter(Boolean) || [])].slice(0, 5);
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

  // Quick address search
  const handleQuickSearch = (searchTerm: string) => {
    // Determine if it's an address, city, or parcel ID
    if (searchTerm.match(/^\d+\s/)) {
      // Starts with number - likely address
      handleFilterChange('address', searchTerm);
    } else if (searchTerm.match(/^\d{12}$/)) {
      // 12 digits - parcel ID
      navigate(`/properties/parcel/${searchTerm}`);
      return;
    } else {
      // Likely city or owner name
      handleFilterChange('city', searchTerm);
    }
    
    searchProperties();
  };

  // Comprehensive data transformation for all 7.3M properties
  const transformPropertyData = (property: any) => {
    // Debug logging to check incoming sales data (only when found)
    if (property.last_qualified_sale || property.has_qualified_sale) {
      console.log(`[transformPropertyData] Sales data found for ${property.parcel_id}:`, {
        last_qualified_sale: property.last_qualified_sale,
        has_qualified_sale: property.has_qualified_sale
      });
    }

    // Clean up address - remove leading dash if present
    const cleanAddress = (addr: string) => {
      if (!addr) return null;
      // Remove leading dash and trim
      return addr.replace(/^-+/, '').trim() || null;
    };

    // Convert numeric strings to numbers for proper calculations
    const toNumber = (value: any) => {
      if (typeof value === 'number') return value;
      if (typeof value === 'string') {
        const num = parseFloat(value);
        return isNaN(num) ? undefined : num;
      }
      return undefined;
    };

    const transformedData = {
      ...property,
      // === CORE IDENTIFIERS ===
      parcel_id: property.parcel_id || property.id || property.property_id,

      // === PROPERTY ADDRESS ===
      phy_addr1: cleanAddress(property.address) ||
                 cleanAddress(property.phy_addr1) ||
                 cleanAddress(property.property_address) ||
                 cleanAddress(property.street_address),
      phy_city: property.city || property.phy_city || property.property_city || property.municipality,
      phy_zipcd: property.zipCode || property.phy_zipcd || property.property_zip || property.zip_code,

      // === OWNER INFORMATION (Production API format first) ===
      own_name: property.owner_name || property.owner || property.own_name || property.property_owner,
      owner_name: property.owner_name || property.owner || property.own_name || property.property_owner,
      owner_addr1: property.ownerAddress || property.owner_addr1 || property.owner_address,

      // === APPRAISED VALUES (Production API format first) ===
      jv: toNumber(property.market_value) ||
          toNumber(property.justValue) ||
          toNumber(property.marketValue) ||
          toNumber(property.jv) ||
          toNumber(property.just_value) ||
          toNumber(property.appraised_value) ||
          toNumber(property.total_value) ||
          toNumber(property.current_value) ||
          toNumber(property.property_value),
      just_value: toNumber(property.market_value) ||
                  toNumber(property.justValue) ||
                  toNumber(property.marketValue) ||
                  toNumber(property.jv) ||
                  toNumber(property.just_value) ||
                  toNumber(property.appraised_value),

      // === TAXABLE VALUES (Production API format first) ===
      tv_sd: toNumber(property.assessed_value) ||
             toNumber(property.taxableValue) ||
             toNumber(property.tv_sd) ||
             toNumber(property.taxable_value) ||
             toNumber(property.tax_value),

      // === LAND VALUES ===
      lnd_val: toNumber(property.landValue) ||
               toNumber(property.lnd_val) ||
               toNumber(property.land_value),

      // === BUILDING SQUARE FOOTAGE (Production API format first) ===
      tot_lvg_area: toNumber(property.living_area) ||
                    toNumber(property.building_sqft) ||
                    toNumber(property.buildingSqFt) ||
                    toNumber(property.tot_lvg_area) ||
                    toNumber(property.building_area) ||
                    toNumber(property.heated_area),

      // === LAND SQUARE FOOTAGE (Production API format first) ===
      lnd_sqfoot: toNumber(property.lot_size) ||
                  toNumber(property.landSqFt) ||
                  toNumber(property.lnd_sqfoot) ||
                  toNumber(property.total_sq_ft) ||
                  toNumber(property.land_sqft),

      // === YEAR BUILT (Production API format first) ===
      act_yr_blt: toNumber(property.year_built) ||
                  toNumber(property.yearBuilt) ||
                  toNumber(property.act_yr_blt) ||
                  toNumber(property.built_year) ||
                  toNumber(property.construction_year) ||
                  toNumber(property.yr_built),

      // === DOR USE CODES ===
      dor_uc: property.propertyUse ||
              property.dor_uc ||
              property.property_use_code ||
              property.use_code ||
              property.land_use_code,

      // === PROPERTY TYPE ===
      property_type: property.propertyType ||
                     property.property_type ||
                     property.type ||
                     property.property_use_desc,

      // === PROPERTY USE DESCRIPTION ===
      propertyUseDesc: property.propertyUseDesc ||
                       property.property_use_desc ||
                       property.use_description ||
                       property.description,

      // === SERVER-SIDE CATEGORIZATION (if available) ===
      use_category: property.use_category,
      use_subcategory: property.use_subcategory,
      use_description: property.use_description,

      // === SALES DATA (Real data only) ===
      sale_prc1: property.last_qualified_sale?.sale_price ||
                 toNumber(property.lastSalePrice) ||
                 toNumber(property.sale_prc1) ||
                 toNumber(property.last_sale_price) ||
                 toNumber(property.sale_price),
      sale_yr1: property.last_qualified_sale?.sale_date ? new Date(property.last_qualified_sale.sale_date).getFullYear() :
                property.lastSaleDate ? new Date(property.lastSaleDate).getFullYear() :
                toNumber(property.sale_yr1) ||
                toNumber(property.last_sale_year) ||
                toNumber(property.sale_year),
      sale_date: property.last_qualified_sale?.sale_date ||
                 property.lastSaleDate ||
                 property.sale_date ||
                 property.last_sale_date,
      sale_month: property.last_qualified_sale?.sale_date ? new Date(property.last_qualified_sale.sale_date).getMonth() + 1 :
                  toNumber(property.sale_month) || toNumber(property.sale_mo1),
      // Add qualified sale data
      last_qualified_sale: property.last_qualified_sale,
      has_qualified_sale: property.has_qualified_sale || false,

      // === ADDITIONAL TAX INFORMATION ===
      tax_amount: toNumber(property.taxAmount) ||
                  toNumber(property.tax_amount) ||
                  toNumber(property.annual_tax),
      assessed_value: toNumber(property.assessedValue) ||
                      toNumber(property.assessed_value),

      // === CRITICAL TAX FIELDS FOR 100% REAL DATA ===
      taxable_value: toNumber(property.taxable_value) ||
                     toNumber(property.tv_sd),
      annual_tax: toNumber(property.annual_tax),
      tax_millage: toNumber(property.tax_millage),
      has_homestead: property.has_homestead || false,

      // === PROPERTY CHARACTERISTICS ===
      bedrooms: toNumber(property.bedrooms) || toNumber(property.beds),
      bathrooms: toNumber(property.bathrooms) || toNumber(property.baths),
      stories: toNumber(property.stories) || toNumber(property.floors),
      pool: property.pool || property.has_pool,

      // === COUNTY INFORMATION ===
      county: property.county || property.county_name,

      // === TAX CERTIFICATE INFORMATION ===
      has_tax_certificates: property.has_tax_certificates || property.tax_certificates,
      certificate_count: toNumber(property.certificate_count),
      total_certificate_amount: toNumber(property.total_certificate_amount),

      // === TAX DEED AUCTION INFORMATION ===
      auction_date: property.auction_date,
      opening_bid: toNumber(property.opening_bid),
      tax_deed_number: property.tax_deed_number,
      auction_url: property.auction_url,

      // === PARCEL ID (Direct pass-through) ===
      parcel_id: property.parcel_id || property.parcelId || property.id,
      parcelId: property.parcel_id || property.parcelId || property.id
    };

    // Debug final transformed data for sales (only when transformed)
    if (transformedData.last_qualified_sale) {
      console.log(`[transformPropertyData] Transformed sales data for ${transformedData.parcel_id}:`, {
        sale_price: transformedData.last_qualified_sale.sale_price,
        sale_date: transformedData.last_qualified_sale.sale_date,
        has_qualified_sale: transformedData.has_qualified_sale
      });
    }

    return transformedData;
  };

  // Navigate to property detail
  const handlePropertyClick = (property: any) => {
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

  // Debug: Log filters state changes
  useEffect(() => {
    console.log('Filters state changed:', filters);
  }, [filters]);

  // Trigger search when propertyType filter changes
  useEffect(() => {
    console.log('Property type changed to:', filters.propertyType);
    searchProperties(1);
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
        const allIds = propertyList.map((p: any) => String(p.parcel_id || p.id));
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
    <div className="min-h-screen bg-gray-50">
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
                  <Map className="w-4 h-4 inline mr-2" style={{pointerEvents: 'none'}} />
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
            padding: '1.5rem',
            position: 'relative'
          }}>
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
            <div style={{ position: 'absolute', right: '1.5rem', top: '1.5rem' }}>
              <Link
                to="/diagnostics/properties"
                className="text-xs font-medium"
                style={{
                  color: '#2c3e50',
                  border: '1px solid #d4af37',
                  padding: '6px 10px',
                  borderRadius: '4px',
                  textDecoration: 'none',
                  background: '#fff'
                }}
                title="Open diagnostics for Property Search backend"
              >
                Diagnostics
              </Link>
            </div>
          </div>
          <div className="p-8">
            <div className="space-y-6">
              {/* Enhanced Autocomplete Search Bar */}
              <AutocompleteSearchBar
                onSearch={(value, suggestion) => {
                  console.log('AutocompleteSearchBar search:', value, suggestion);
                  // Update filters based on the search
                  if (suggestion) {
                    setFilters(prev => ({
                      ...prev,
                      address: suggestion.address || value,
                      city: suggestion.city || prev.city,
                      owner: suggestion.owner_name || prev.owner
                    }));
                    // Trigger search with the suggestion data
                    handleSearchWithSuggestion(suggestion);
                  } else {
                    // Regular search with the input value
                    setFilters(prev => ({ ...prev, address: value }));
                    handleSearch();
                  }
                }}
                onSelect={(suggestion) => {
                  console.log('AutocompleteSearchBar selected:', suggestion);
                  // Navigate to property detail if parcel_id is available
                  if (suggestion.parcel_id) {
                    navigate(`/property/${suggestion.parcel_id}`);
                  }
                }}
                placeholder="Search by address (e.g. '123 Main St'), city, or owner name..."
                apiUrl={typeof window !== 'undefined' && window.location.hostname === 'localhost' ? 'http://localhost:8003' : '/api/autocomplete-ultra'}
              />

              {/* Floating Diagnostics Badge */}
              <div style={{ position: 'fixed', right: '16px', bottom: '16px', zIndex: 2000 }}>
                <Link
                  to="/diagnostics/properties"
                  className="text-xs font-medium"
                  style={{
                    color: diagStatus === 'ok' ? '#065f46' : diagStatus === 'pending' ? '#374151' : '#7f1d1d',
                    background: diagStatus === 'ok' ? '#d1fae5' : diagStatus === 'pending' ? '#f3f4f6' : '#fee2e2',
                    border: '1px solid',
                    borderColor: diagStatus === 'ok' ? '#10b981' : diagStatus === 'pending' ? '#d1d5db' : '#fca5a5',
                    padding: '6px 10px',
                    borderRadius: '16px',
                    textDecoration: 'none',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                  title="Open diagnostics for Property Search backend"
                >
                  <span style={{ width: 8, height: 8, borderRadius: 9999, display: 'inline-block', background: diagStatus === 'ok' ? '#10b981' : diagStatus === 'pending' ? '#9ca3af' : '#ef4444' }} />
                  Diagnostics: {diagStatus === 'ok' ? 'OK' : diagStatus === 'pending' ? '…' : 'Issues'}
                </Link>
              </div>

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
                    className="hover-lift flex items-center space-x-2 h-10 px-4"
                    style={{
                      borderColor: showAdvancedFilters ? '#d4af37' : '#ecf0f1',
                      color: showAdvancedFilters ? '#d4af37' : '#2c3e50',
                      background: showAdvancedFilters ? 'rgba(212, 175, 55, 0.05)' : 'white'
                    }}
                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  >
                    <SlidersHorizontal className="w-4 h-4" />
                    <span>Advanced Filters</span>
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
                        format="number"
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
                        format="number"
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
                        placeholder="MM/DD/YYYY"
                        type="date"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minSaleDate}
                        onChange={(e) => handleFilterChange('minSaleDate', e.target.value)}
                      />
                      <p className="text-xs" style={{color: '#95a5a6'}}>Purchase date from</p>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Sale Date</label>
                      <Input
                        placeholder="MM/DD/YYYY"
                        type="date"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxSaleDate}
                        onChange={(e) => handleFilterChange('maxSaleDate', e.target.value)}
                      />
                      <p className="text-xs" style={{color: '#95a5a6'}}>Purchase date to</p>
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
                      className="h-12 px-6 hover-lift"
                      style={{background: '#d4af37', borderColor: '#d4af37'}}
                      onClick={() => searchProperties(1)}
                    >
                      Apply Filters
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

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
              backgroundColor: filters.propertyType === 'Residential' ? 'rgb(240, 253, 244)' : 'rgb(240, 253, 244)',
              color: filters.propertyType === 'Residential' ? 'rgb(34, 197, 94)' : 'rgb(34, 197, 94)',
              borderColor: filters.propertyType === 'Residential' ? 'rgb(34, 197, 94)' : 'rgb(187, 247, 208)'
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
              backgroundColor: filters.propertyType === 'Commercial' ? 'rgb(239, 246, 255)' : 'rgb(239, 246, 255)',
              color: filters.propertyType === 'Commercial' ? 'rgb(59, 130, 246)' : 'rgb(59, 130, 246)',
              borderColor: filters.propertyType === 'Commercial' ? 'rgb(59, 130, 246)' : 'rgb(191, 219, 254)'
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
              backgroundColor: filters.propertyType === 'Industrial' ? 'rgb(255, 247, 237)' : 'rgb(255, 247, 237)',
              color: filters.propertyType === 'Industrial' ? 'rgb(251, 146, 60)' : 'rgb(251, 146, 60)',
              borderColor: filters.propertyType === 'Industrial' ? 'rgb(251, 146, 60)' : 'rgb(254, 215, 170)'
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
              backgroundColor: filters.propertyType === 'Agricultural' ? 'rgb(255, 251, 235)' : 'rgb(255, 251, 235)',
              color: filters.propertyType === 'Agricultural' ? 'rgb(245, 158, 11)' : 'rgb(245, 158, 11)',
              borderColor: filters.propertyType === 'Agricultural' ? 'rgb(245, 158, 11)' : 'rgb(253, 230, 138)'
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
              backgroundColor: filters.propertyType === 'Vacant' ? 'rgb(249, 250, 251)' : 'rgb(249, 250, 251)',
              color: filters.propertyType === 'Vacant' ? 'rgb(107, 114, 128)' : 'rgb(107, 114, 128)',
              borderColor: filters.propertyType === 'Vacant' ? 'rgb(107, 114, 128)' : 'rgb(209, 213, 219)'
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
              backgroundColor: filters.propertyType === 'Government' ? 'rgb(254, 242, 242)' : 'rgb(254, 242, 242)',
              color: filters.propertyType === 'Government' ? 'rgb(239, 68, 68)' : 'rgb(239, 68, 68)',
              borderColor: filters.propertyType === 'Government' ? 'rgb(239, 68, 68)' : 'rgb(254, 202, 202)'
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
              backgroundColor: filters.propertyType === 'Conservation' ? 'rgb(236, 253, 245)' : 'rgb(236, 253, 245)',
              color: filters.propertyType === 'Conservation' ? 'rgb(16, 185, 129)' : 'rgb(16, 185, 129)',
              borderColor: filters.propertyType === 'Conservation' ? 'rgb(16, 185, 129)' : 'rgb(167, 243, 208)'
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
              backgroundColor: filters.propertyType === 'Religious' ? 'rgb(250, 245, 255)' : 'rgb(250, 245, 255)',
              color: filters.propertyType === 'Religious' ? 'rgb(168, 85, 247)' : 'rgb(168, 85, 247)',
              borderColor: filters.propertyType === 'Religious' ? 'rgb(168, 85, 247)' : 'rgb(233, 213, 255)'
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
              backgroundColor: filters.propertyType === 'Vacant/Special' ? 'rgb(255, 251, 235)' : 'rgb(255, 251, 235)',
              color: filters.propertyType === 'Vacant/Special' ? 'rgb(217, 119, 6)' : 'rgb(217, 119, 6)',
              borderColor: filters.propertyType === 'Vacant/Special' ? 'rgb(217, 119, 6)' : 'rgb(253, 230, 138)'
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
            <div className="text-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">Searching properties...</p>
            </div>
          ) : (
            <>
              {console.log('Render - Properties count:', properties.length, 'Loading:', loading, 'Properties:', properties)}
              {properties.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <Search className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium mb-2">No Properties Found</h3>
                  <p className="text-gray-600 mb-4">
                    Try adjusting your search criteria or browse by city
                  </p>
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
              <div className={
                viewMode === 'grid' 
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'
                  : 'space-y-2'
              }>
                {properties.map((property) => {
                  const transformedProperty = transformPropertyData(property);
                  return (
                    <MiniPropertyCard
                      key={transformedProperty.parcel_id || transformedProperty.id}
                      parcelId={transformedProperty.parcel_id}
                      data={transformedProperty}
                      variant={viewMode}
                      onClick={() => handlePropertyClick(property)}
                      isWatched={property.is_watched}
                      hasNotes={property.note_count > 0}
                      priority={property.note_count > 5 ? 'high' : property.note_count > 2 ? 'medium' : 'low'}
                      isSelected={selectedProperties.has(String(transformedProperty.parcel_id || transformedProperty.id))}
                      onToggleSelection={() => togglePropertySelection(transformedProperty.parcel_id || transformedProperty.id)}
                    />
                  );
                })}
              </div>
            )}

            {/* Elegant Pagination Footer */}
            {totalResults > pageSize && (
              <div className="elegant-card hover-lift animate-in mt-8">
                <div className="p-6">
                  <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
                    {/* Page Info and Size Selector */}
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-medium" style={{color: '#2c3e50'}}>
                        Page {currentPage.toLocaleString()} of {totalPages.toLocaleString()}
                      </span>
                      <span style={{color: '#95a5a6'}}>|</span>
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
                        {/* First page */}
                        {currentPage > 3 && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              className="hover-lift h-9 w-9"
                              style={{borderColor: '#ecf0f1', color: '#2c3e50'}}
                              onClick={() => searchProperties(1)}
                            >
                              1
                            </Button>
                            {currentPage > 4 && (
                              <span className="px-1" style={{color: '#7f8c8d'}}>...</span>
                            )}
                          </>
                        )}

                        {/* Page numbers */}
                        {(() => {
                          const pagesToShow = 7; // Show 7 page numbers at a time
                          let startPage = Math.max(1, currentPage - 3);
                          let endPage = Math.min(totalPages, currentPage + 3);

                          // Adjust range if near beginning or end
                          if (currentPage <= 3) {
                            endPage = Math.min(totalPages, pagesToShow);
                          }
                          if (currentPage >= totalPages - 3) {
                            startPage = Math.max(1, totalPages - pagesToShow + 1);
                          }

                          const pages = [];
                          for (let page = startPage; page <= endPage; page++) {
                            pages.push(
                              <Button
                                key={page}
                                variant={currentPage === page ? 'default' : 'outline'}
                                size="sm"
                                className="hover-lift h-9 min-w-[36px] px-2"
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
                          return pages;
                        })()}

                        {/* Last page */}
                        {currentPage < totalPages - 3 && (
                          <>
                            {currentPage < totalPages - 4 && (
                              <span className="px-1" style={{color: '#7f8c8d'}}>...</span>
                            )}
                            <Button
                              variant="outline"
                              size="sm"
                              className="hover-lift h-9 min-w-[36px] px-2"
                              style={{borderColor: '#ecf0f1', color: '#2c3e50'}}
                              onClick={() => searchProperties(totalPages)}
                            >
                              {totalPages}
                            </Button>
                          </>
                        )}
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
    </div>
  );
}

export default PropertySearch;
