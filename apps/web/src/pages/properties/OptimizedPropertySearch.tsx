import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { OptimizedSearchBar } from '@/components/OptimizedSearchBar';
import { VirtualizedPropertyList } from '@/components/property/VirtualizedPropertyList';
import { useInfinitePropertySearch, usePrefetchCommonSearches } from '@/hooks/useOptimizedPropertySearchV2';
import { getPropertyTypeFilter } from '@/lib/dorUseCodes';
import '@/styles/elegant-property.css';

// Lazy-loaded components
import {
  LazyPropertyMap,
  LazyTaxDeedSalesTab,
  LazyAISearchEnhanced
} from '@/components/lazy/LazyLoadedComponents';

import {
  Search,
  Filter,
  Grid3X3,
  List,
  SlidersHorizontal,
  RefreshCw,
  Map,
  Brain,
  Gavel,
  Settings,
  Download,
  Info
} from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

// Optimized search filters interface
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
  usageCode: string;
  subUsageCode: string;
  taxDelinquent: boolean;
}

const INITIAL_FILTERS: SearchFilters = {
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
  usageCode: '',
  subUsageCode: '',
  taxDelinquent: false,
};

const FLORIDA_COUNTIES = [
  'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
  'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'MIAMI-DADE', 'DESOTO',
  'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST',
  'GLADES', 'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS',
  'HILLSBOROUGH', 'HOLMES', 'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE',
  'LAKE', 'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION',
  'MARTIN', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA',
  'PALM BEACH', 'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA',
  'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION',
  'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
];

export function OptimizedPropertySearch() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // UI state
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [showMapView, setShowMapView] = useState(false);
  const [showAISearch, setShowAISearch] = useState(false);
  const [showTaxDeedSales, setShowTaxDeedSales] = useState(false);
  const [selectedProperties, setSelectedProperties] = useState<Set<string>>(new Set());

  // Search filters state
  const [filters, setFilters] = useState<SearchFilters>(INITIAL_FILTERS);

  // Initialize search options from URL params
  const searchOptions = useMemo(() => {
    const options: any = {};

    if (filters.address) options.address = filters.address;
    if (filters.city) options.city = filters.city;
    if (filters.county) options.county = filters.county;
    if (filters.zipCode) options.zip_code = filters.zipCode;
    if (filters.owner) options.owner = filters.owner;
    if (filters.minValue) options.min_value = parseInt(filters.minValue);
    if (filters.maxValue) options.max_value = parseInt(filters.maxValue);

    return options;
  }, [filters]);

  // Use optimized infinite search hook
  const {
    properties,
    total,
    loading,
    error,
    hasNextPage,
    isLoadingMore,
    loadMore,
    refetch,
    cached
  } = useInfinitePropertySearch(searchOptions);

  // Prefetch common searches
  const { prefetchCommonSearches } = usePrefetchCommonSearches();

  // Initialize prefetching on mount
  useEffect(() => {
    prefetchCommonSearches().catch(console.error);
  }, [prefetchCommonSearches]);

  // Update URL when filters change
  useEffect(() => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== '' && value !== false) {
        params.set(key, String(value));
      }
    });

    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  // Load filters from URL on mount
  useEffect(() => {
    const urlFilters = { ...INITIAL_FILTERS };

    searchParams.forEach((value, key) => {
      if (key in urlFilters) {
        if (key === 'taxDelinquent') {
          urlFilters[key as keyof SearchFilters] = value === 'true';
        } else {
          (urlFilters as any)[key] = value;
        }
      }
    });

    setFilters(urlFilters);
  }, [searchParams]);

  // Memoized event handlers
  const handlePropertyClick = useCallback((property: any) => {
    navigate(`/properties/${property.parcel_id}`);
  }, [navigate]);

  const handleToggleSelection = useCallback((parcelId: string) => {
    setSelectedProperties(prev => {
      const newSet = new Set(prev);
      if (newSet.has(parcelId)) {
        newSet.delete(parcelId);
      } else {
        newSet.add(parcelId);
      }
      return newSet;
    });
  }, []);

  const handleFilterChange = useCallback((key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilters(INITIAL_FILTERS);
    setSelectedProperties(new Set());
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Memoized property type options
  const propertyTypeOptions = useMemo(() => [
    { value: '', label: 'All Property Types' },
    { value: 'residential', label: 'Residential' },
    { value: 'commercial', label: 'Commercial' },
    { value: 'industrial', label: 'Industrial' },
    { value: 'agricultural', label: 'Agricultural' },
    { value: 'vacant', label: 'Vacant Land' },
  ], []);

  // Performance monitoring
  const performanceStats = useMemo(() => {
    return {
      totalProperties: total,
      loadedProperties: properties.length,
      loadingProgress: total > 0 ? (properties.length / total) * 100 : 0,
      cached,
      selectedCount: selectedProperties.size
    };
  }, [total, properties.length, cached, selectedProperties.size]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold text-slate-900">
                Property Search
              </h1>
              {performanceStats.totalProperties > 0 && (
                <Badge variant="outline" className="text-xs">
                  {performanceStats.loadedProperties.toLocaleString()} / {performanceStats.totalProperties.toLocaleString()} properties
                  {cached && ' (cached)'}
                </Badge>
              )}
              {loading && (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  <span className="text-sm text-slate-500">Loading...</span>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {/* View Mode Toggle */}
              <div className="flex bg-slate-100 rounded-lg p-1">
                <Button
                  size="sm"
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  onClick={() => setViewMode('grid')}
                  className="h-8 px-3"
                >
                  <Grid3X3 className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  onClick={() => setViewMode('list')}
                  className="h-8 px-3"
                >
                  <List className="w-4 h-4" />
                </Button>
              </div>

              {/* Action Buttons */}
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowMapView(!showMapView)}
                className="h-8"
              >
                <Map className="w-4 h-4 mr-2" />
                Map
              </Button>

              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowAISearch(!showAISearch)}
                className="h-8"
              >
                <Brain className="w-4 h-4 mr-2" />
                AI Search
              </Button>

              <Button
                size="sm"
                variant="outline"
                onClick={handleRefresh}
                disabled={loading}
                className="h-8"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Search Filters */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="space-y-4">
            {/* Primary Search Bar */}
            <div className="flex space-x-4">
              <div className="flex-1">
                <OptimizedSearchBar
                  value={filters.address}
                  onChange={(value) => handleFilterChange('address', value)}
                  placeholder="Search by address, owner, or property..."
                  className="w-full"
                />
              </div>

              <Select
                value={filters.county}
                onValueChange={(value) => handleFilterChange('county', value)}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="County" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Counties</SelectItem>
                  {FLORIDA_COUNTIES.map(county => (
                    <SelectItem key={county} value={county}>{county}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                variant="outline"
                onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                className="flex items-center space-x-2"
              >
                <SlidersHorizontal className="w-4 h-4" />
                <span>Filters</span>
              </Button>
            </div>

            {/* Advanced Filters */}
            {showAdvancedFilters && (
              <Card className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      City
                    </label>
                    <Input
                      value={filters.city}
                      onChange={(e) => handleFilterChange('city', e.target.value)}
                      placeholder="Enter city"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Zip Code
                    </label>
                    <Input
                      value={filters.zipCode}
                      onChange={(e) => handleFilterChange('zipCode', e.target.value)}
                      placeholder="Enter zip code"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Property Type
                    </label>
                    <Select
                      value={filters.propertyType}
                      onValueChange={(value) => handleFilterChange('propertyType', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All Types" />
                      </SelectTrigger>
                      <SelectContent>
                        {propertyTypeOptions.map(option => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Owner Name
                    </label>
                    <Input
                      value={filters.owner}
                      onChange={(e) => handleFilterChange('owner', e.target.value)}
                      placeholder="Enter owner name"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Min Value ($)
                    </label>
                    <Input
                      type="number"
                      value={filters.minValue}
                      onChange={(e) => handleFilterChange('minValue', e.target.value)}
                      placeholder="Min value"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Max Value ($)
                    </label>
                    <Input
                      type="number"
                      value={filters.maxValue}
                      onChange={(e) => handleFilterChange('maxValue', e.target.value)}
                      placeholder="Max value"
                    />
                  </div>
                </div>

                <div className="flex justify-between items-center mt-4 pt-4 border-t border-slate-200">
                  <div className="text-sm text-slate-500">
                    {performanceStats.totalProperties > 0 && (
                      <span>
                        Found {performanceStats.totalProperties.toLocaleString()} properties
                        {selectedProperties.size > 0 && (
                          <span> • {selectedProperties.size} selected</span>
                        )}
                      </span>
                    )}
                  </div>

                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleClearFilters}
                    >
                      Clear All
                    </Button>
                    {selectedProperties.size > 0 && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          // Export selected properties
                          console.log('Exporting selected properties:', selectedProperties);
                        }}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export Selected
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs defaultValue="properties" className="space-y-6">
          <TabsList className="bg-white border border-slate-200">
            <TabsTrigger value="properties" className="flex items-center space-x-2">
              <Search className="w-4 h-4" />
              <span>Properties</span>
            </TabsTrigger>
            {showMapView && (
              <TabsTrigger value="map" className="flex items-center space-x-2">
                <Map className="w-4 h-4" />
                <span>Map View</span>
              </TabsTrigger>
            )}
            {showAISearch && (
              <TabsTrigger value="ai-search" className="flex items-center space-x-2">
                <Brain className="w-4 h-4" />
                <span>AI Search</span>
              </TabsTrigger>
            )}
            {showTaxDeedSales && (
              <TabsTrigger value="tax-deeds" className="flex items-center space-x-2">
                <Gavel className="w-4 h-4" />
                <span>Tax Deed Sales</span>
              </TabsTrigger>
            )}
          </TabsList>

          {/* Properties Tab */}
          <TabsContent value="properties" className="space-y-6">
            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-2 text-red-700">
                    <Info className="w-4 h-4" />
                    <span>Error loading properties: {error}</span>
                  </div>
                </CardContent>
              </Card>
            )}

            {!loading && !error && properties.length === 0 && (
              <Card>
                <CardContent className="p-8 text-center">
                  <div className="text-slate-500">
                    <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium mb-2">No properties found</h3>
                    <p>Try adjusting your search criteria or clearing filters.</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {properties.length > 0 && (
              <VirtualizedPropertyList
                properties={properties}
                hasNextPage={hasNextPage}
                isNextPageLoading={isLoadingMore}
                loadNextPage={loadMore}
                onPropertyClick={handlePropertyClick}
                viewMode={viewMode}
                height={800}
                selectedProperties={selectedProperties}
                onToggleSelection={handleToggleSelection}
              />
            )}
          </TabsContent>

          {/* Map Tab */}
          {showMapView && (
            <TabsContent value="map">
              <Card>
                <CardContent className="p-0">
                  <LazyPropertyMap
                    properties={properties}
                    height={600}
                    onPropertyClick={handlePropertyClick}
                  />
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* AI Search Tab */}
          {showAISearch && (
            <TabsContent value="ai-search">
              <LazyAISearchEnhanced
                onSearch={(query) => {
                  // Handle AI search
                  console.log('AI Search:', query);
                }}
              />
            </TabsContent>
          )}

          {/* Tax Deed Sales Tab */}
          {showTaxDeedSales && (
            <TabsContent value="tax-deeds">
              <LazyTaxDeedSalesTab />
            </TabsContent>
          )}
        </Tabs>
      </div>
    </div>
  );
}