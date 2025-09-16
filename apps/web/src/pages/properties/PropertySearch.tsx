import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
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
import { OptimizedSearchBar } from '@/components/OptimizedSearchBar';
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
  const [pageSize, setPageSize] = useState(100); // Increased for better performance with 789k properties
  const [showMapView, setShowMapView] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<any>(null);
  const [selectedProperties, setSelectedProperties] = useState<Set<string>>(new Set());
  const [mapButtonHovered, setMapButtonHovered] = useState(false);
  const [showAISearch, setShowAISearch] = useState(false);
  const [showTaxDeedSales, setShowTaxDeedSales] = useState(false);

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

  // Initial load effect with optimized search
  useEffect(() => {
    console.log('Initial mount - loading properties...');
    // Use optimized search for initial load
    searchProperties();
  }, []); // Only run once on mount

  // Auto-filter with optimized pipeline
  useEffect(() => {
    if (isInitialMount.current) {
      // Skip first render since we handle it above
      isInitialMount.current = false;
      return;
    }

    // Clear any existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Fast debounce with pipeline caching
    searchTimeoutRef.current = setTimeout(() => {
      console.log('Fast auto-filter:', filters);
      searchProperties(1);
    }, 150); // Reduced to 150ms with caching

    // Cleanup
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [filters]); // Only depend on filters

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

  const propertyTypes = [
    { value: 'Residential', label: 'Residential' },
    { value: 'Commercial', label: 'Commercial' },
    { value: 'Industrial', label: 'Industrial' },
    { value: 'Agricultural', label: 'Agricultural' },
    { value: 'Government', label: 'Government' }
  ];

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
        if (value && value !== 'all-cities' && value !== 'all-types' && value !== '') {
          // Skip taxDelinquent as it needs special handling
          if (key === 'taxDelinquent') {
            if (value === true) {
              apiFilters['has_tax_certificates'] = true;
              apiFilters['certificate_years'] = 7; // Look back 7 years
            }
          } else {
            const apiKey = keyMap[key] || key;
            apiFilters[apiKey] = value;
          }
        }
      });
      
      apiFilters.limit = pageSize.toString();
      apiFilters.offset = ((page - 1) * pageSize).toString();
      
      console.log('Fast pipeline search:', apiFilters);
      
      // Use cached pipeline for instant results
      const data = await pipeline.fetchWithCache(
        'http://localhost:8001/api/properties/search',
        apiFilters
      );
      
      console.log('Pipeline results:', data);
      console.log('Setting properties:', data.properties?.length || 0, 'items');
      console.log('First property:', data.properties?.[0]);
      setProperties(data.properties || []);
      setTotalResults(data.total || 0);
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
      // Fetch from search API for all types
      const [addressRes, cityRes, ownerRes] = await Promise.all([
        fetch(`http://localhost:8002/api/properties/search?address=${encodeURIComponent(query)}&limit=10`),
        fetch(`http://localhost:8002/api/properties/search?city=${encodeURIComponent(query)}&limit=10`),
        fetch(`http://localhost:8002/api/properties/search?owner=${encodeURIComponent(query)}&limit=10`)
      ]);
      
      const suggestions = [];
      
      // Process address results
      if (addressRes.ok) {
        const data = await addressRes.json();
        const addresses = [...new Set(data.properties?.map((p: any) => p.phy_addr1).filter(Boolean) || [])].slice(0, 5);
        addresses.forEach((addr: string) => suggestions.push({ type: 'address', value: addr, display: `📍 ${addr}` }));
      }
      
      // Process city results
      if (cityRes.ok) {
        const data = await cityRes.json();
        const cities = [...new Set(data.properties?.map((p: any) => p.phy_city).filter(Boolean) || [])].slice(0, 3);
        cities.forEach((city: string) => suggestions.push({ type: 'city', value: city, display: `🏘️ ${city}` }));
      }
      
      // Process owner results
      if (ownerRes.ok) {
        const data = await ownerRes.json();
        const owners = [...new Set(data.properties?.map((p: any) => p.own_name).filter(Boolean) || [])].slice(0, 5);
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

  // Transform property data for compatibility
  const transformPropertyData = (property: any) => {
    return {
      ...property,
      // Ensure compatibility with MiniPropertyCard expectations
      phy_addr1: property.phy_addr1 || property.property_address,
      phy_city: property.phy_city || property.property_city,
      phy_zipcd: property.phy_zipcd || property.property_zip,
      own_name: property.own_name || property.owner_name,
      jv: property.jv || property.just_value,
      tv_sd: property.tv_sd || property.taxable_value,
      lnd_val: property.lnd_val || property.land_value,
      tot_lvg_area: property.tot_lvg_area || property.living_area,
      lnd_sqfoot: property.lnd_sqfoot || property.total_sq_ft,
      act_yr_blt: property.act_yr_blt || property.year_built,
      dor_uc: property.dor_uc || property.property_use_code
    };
  };

  // Navigate to property detail
  const handlePropertyClick = (property: any) => {
    // Use address-based routing - handle both data structures
    const address = property.phy_addr1 || property.property_address;
    const city = property.phy_city || property.property_city;

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
      // Fallback to property ID
      navigate(`/properties/${property.id}`);
    }
  };

  // Debug: Log filters state changes
  useEffect(() => {
    console.log('Filters state changed:', filters);
  }, [filters]);

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
        
        const data = await pipeline.fetchWithCache(
          'http://localhost:8001/api/properties/search',
          apiFilters
        );
        
        const allIds = (data.properties || []).map((p: any) => String(p.parcel_id || p.id));
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
        {/* Elegant Tabs for Search Modes - Beautiful Executive Design */}
        <div className="tabs-executive flex justify-center mb-8" style={{borderBottom: '1px solid #ecf0f1', background: 'transparent'}}>
          <button
            onClick={() => {
              setShowAdvancedFilters(false);
              handleFilterChange('propertyType', 'Residential');
            }}
            className={`tab-executive ${filters.propertyType === 'Residential' && !showAdvancedFilters ? 'active' : ''}`}
            style={{
              background: 'transparent',
              color: filters.propertyType === 'Residential' && !showAdvancedFilters ? '#2c3e50' : '#7f8c8d',
              border: 'none',
              borderBottom: filters.propertyType === 'Residential' && !showAdvancedFilters ? '2px solid #d4af37' : '2px solid transparent',
              fontWeight: '300',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              fontSize: '0.875rem',
              padding: '1rem 1.5rem',
              transition: 'all 0.3s ease',
              position: 'relative',
              cursor: 'pointer'
            }}
          >
            <Home className="w-4 h-4 inline mr-2" />
            Residential
          </button>
          <button
            onClick={() => {
              setShowAdvancedFilters(false);
              handleFilterChange('propertyType', 'Commercial');
            }}
            className={`tab-executive ${filters.propertyType === 'Commercial' && !showAdvancedFilters ? 'active' : ''}`}
            style={{
              background: 'transparent',
              color: filters.propertyType === 'Commercial' && !showAdvancedFilters ? '#2c3e50' : '#7f8c8d',
              border: 'none',
              borderBottom: filters.propertyType === 'Commercial' && !showAdvancedFilters ? '2px solid #d4af37' : '2px solid transparent',
              fontWeight: '300',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              fontSize: '0.875rem',
              padding: '1rem 1.5rem',
              transition: 'all 0.3s ease',
              position: 'relative',
              cursor: 'pointer'
            }}
          >
            <Building className="w-4 h-4 inline mr-2" />
            Commercial
          </button>
          <button
            onClick={() => {
              setShowAdvancedFilters(false);
              handleFilterChange('propertyType', 'Industrial');
            }}
            className={`tab-executive ${filters.propertyType === 'Industrial' && !showAdvancedFilters ? 'active' : ''}`}
            style={{
              background: 'transparent',
              color: filters.propertyType === 'Industrial' && !showAdvancedFilters ? '#2c3e50' : '#7f8c8d',
              border: 'none',
              borderBottom: filters.propertyType === 'Industrial' && !showAdvancedFilters ? '2px solid #d4af37' : '2px solid transparent',
              fontWeight: '300',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              fontSize: '0.875rem',
              padding: '1rem 1.5rem',
              transition: 'all 0.3s ease',
              position: 'relative',
              cursor: 'pointer'
            }}
          >
            <Briefcase className="w-4 h-4 inline mr-2" />
            Industrial
          </button>
          <button
            onClick={() => {
              setShowAdvancedFilters(false);
              handleFilterChange('propertyType', 'Agricultural');
            }}
            className={`tab-executive ${filters.propertyType === 'Agricultural' && !showAdvancedFilters ? 'active' : ''}`}
            style={{
              background: 'transparent',
              color: filters.propertyType === 'Agricultural' && !showAdvancedFilters ? '#2c3e50' : '#7f8c8d',
              border: 'none',
              borderBottom: filters.propertyType === 'Agricultural' && !showAdvancedFilters ? '2px solid #d4af37' : '2px solid transparent',
              fontWeight: '300',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              fontSize: '0.875rem',
              padding: '1rem 1.5rem',
              transition: 'all 0.3s ease',
              position: 'relative',
              cursor: 'pointer'
            }}
          >
            <TreePine className="w-4 h-4 inline mr-2" />
            Agricultural
          </button>
          <button
            onClick={() => {
              setShowAdvancedFilters(false);
              handleFilterChange('propertyType', 'Vacant');
            }}
            className={`tab-executive ${filters.propertyType === 'Vacant' && !showAdvancedFilters ? 'active' : ''}`}
            style={{
              background: 'transparent',
              color: filters.propertyType === 'Vacant' && !showAdvancedFilters ? '#2c3e50' : '#7f8c8d',
              border: 'none',
              borderBottom: filters.propertyType === 'Vacant' && !showAdvancedFilters ? '2px solid #d4af37' : '2px solid transparent',
              fontWeight: '300',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              fontSize: '0.875rem',
              padding: '1rem 1.5rem',
              transition: 'all 0.3s ease',
              position: 'relative',
              cursor: 'pointer'
            }}
          >
            <MapPin className="w-4 h-4 inline mr-2" />
            Vacant Land
          </button>
          <button
            onClick={() => {
              setShowTaxDeedSales(!showTaxDeedSales);
              setShowAdvancedFilters(false);
            }}
            className={`tab-executive ${showTaxDeedSales ? 'active' : ''}`}
            style={{
              background: 'transparent',
              color: showTaxDeedSales ? '#2c3e50' : '#7f8c8d',
              border: 'none',
              borderBottom: showTaxDeedSales ? '2px solid #d4af37' : '2px solid transparent',
              fontWeight: '300',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              fontSize: '0.875rem',
              padding: '1rem 1.5rem',
              transition: 'all 0.3s ease',
              position: 'relative',
              cursor: 'pointer'
            }}
          >
            <Gavel className="w-4 h-4 inline mr-2" />
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
          <div className="p-8">
            <div className="space-y-6">
              {/* Optimized Search Bar */}
              <OptimizedSearchBar
                onResults={(results) => {
                  console.log('OptimizedSearchBar results:', results);
                  setSearchResults(results);
                  setProperties(results.properties || []);
                  setTotalResults(results.total || 0);
                  setLoading(false);
                }}
                onFiltersChange={(newFilters) => {
                  console.log('OptimizedSearchBar filters:', newFilters);
                  setFilters(prev => ({ ...prev, ...newFilters }));
                }}
                placeholder="Search by address (e.g. '123 Main St'), city, or owner name..."
                showMetrics={true}
                enableVoiceSearch={true}
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
                      <Input
                        placeholder="100000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minValue}
                        onChange={(e) => handleFilterChange('minValue', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Value</label>
                      <Input
                        placeholder="1000000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxValue}
                        onChange={(e) => handleFilterChange('maxValue', e.target.value)}
                      />
                    </div>
                  </div>
                  
                  {/* Square Footage Filters */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Building SqFt</label>
                      <Input
                        placeholder="1000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minBuildingSqFt}
                        onChange={(e) => handleFilterChange('minBuildingSqFt', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Building SqFt</label>
                      <Input
                        placeholder="5000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxBuildingSqFt}
                        onChange={(e) => handleFilterChange('maxBuildingSqFt', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Land SqFt</label>
                      <Input
                        placeholder="5000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minLandSqFt}
                        onChange={(e) => handleFilterChange('minLandSqFt', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Land SqFt</label>
                      <Input
                        placeholder="20000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxLandSqFt}
                        onChange={(e) => handleFilterChange('maxLandSqFt', e.target.value)}
                      />
                    </div>
                  </div>
                  
                  {/* Year Built Filters (Missing from Interface) */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Year Built</label>
                      <Input
                        placeholder="1990"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minYear}
                        onChange={(e) => handleFilterChange('minYear', e.target.value)}
                        min="1800"
                        max="2025"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Year Built</label>
                      <Input
                        placeholder="2024"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxYear}
                        onChange={(e) => handleFilterChange('maxYear', e.target.value)}
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
                      <Input
                        placeholder="100000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minSalePrice}
                        onChange={(e) => handleFilterChange('minSalePrice', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Sale Price</label>
                      <Input
                        placeholder="500000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxSalePrice}
                        onChange={(e) => handleFilterChange('maxSalePrice', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Min Appraised Value</label>
                      <Input
                        placeholder="150000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.minAppraisedValue}
                        onChange={(e) => handleFilterChange('minAppraisedValue', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>Max Appraised Value</label>
                      <Input
                        placeholder="600000"
                        type="number"
                        className="h-12 rounded-lg"
                        style={{borderColor: '#ecf0f1'}}
                        value={filters.maxAppraisedValue}
                        onChange={(e) => handleFilterChange('maxAppraisedValue', e.target.value)}
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
                      key={property.parcel_id || property.id}
                      parcelId={property.parcel_id}
                      data={transformedProperty}
                      variant={viewMode}
                      onClick={() => handlePropertyClick(property)}
                      isWatched={property.is_watched}
                      hasNotes={property.note_count > 0}
                      priority={property.note_count > 5 ? 'high' : property.note_count > 2 ? 'medium' : 'low'}
                      isSelected={selectedProperties.has(String(property.parcel_id || property.id))}
                      onToggleSelection={() => togglePropertySelection(property.parcel_id || property.id)}
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
                    {/* Page Size Selector */}
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-medium" style={{color: '#2c3e50'}}>Show per page:</span>
                      <Select 
                        value={pageSize.toString()} 
                        onValueChange={(value) => {
                          setPageSize(parseInt(value));
                          setCurrentPage(1);
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
                        {Array.from({ length: Math.min(5, Math.ceil(totalResults / pageSize)) }, (_, i) => {
                          const page = i + 1;
                          const totalPages = Math.ceil(totalResults / pageSize);
                          let startPage = Math.max(1, currentPage - 2);
                          let endPage = Math.min(totalPages, startPage + 4);
                          
                          if (endPage - startPage < 4) {
                            startPage = Math.max(1, endPage - 4);
                          }
                          
                          if (page < startPage || page > endPage) return null;
                          
                          return (
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
                        })}
                      </div>

                      <Button
                        variant="outline"
                        disabled={currentPage >= Math.ceil(totalResults / pageSize)}
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