import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ProductionDatasetBanner, ProductionDatasetIndicator } from '@/components/ProductionDatasetBanner';
import { unifiedSearchService, PropertyCard, SearchParams } from '@/services/unified_search_service';
import { parseQueryToFilters } from '@/lib/queryUnderstanding';
import MiniPropertyCard from '@/components/property/MiniPropertyCard';
import {
  Search,
  Filter,
  Grid3X3,
  List,
  RefreshCw,
  MapPin,
  Building2,
  Home,
  Factory,
  TreePine,
  AlertTriangle,
  Database,
  CheckCircle,
  Info
} from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

interface PropertySearchProps {}

const PROPERTY_TYPES = [
  { value: 'ALL', label: 'All Property Types' },
  { value: 'Residential', label: 'Residential' },
  { value: 'Commercial', label: 'Commercial' },
  { value: 'Industrial', label: 'Industrial' },
  { value: 'Agricultural', label: 'Agricultural' },
  { value: 'Vacant', label: 'Vacant Land' }
];

const FLORIDA_COUNTIES = [
  'ALL', 'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
  'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DESOTO', 'DIXIE', 'DUVAL',
  'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES', 'GULF',
  'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH', 'HOLMES',
  'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE', 'LEON', 'LEVY',
  'LIBERTY', 'MADISON', 'MANATEE', 'MARION', 'MARTIN', 'MIAMI-DADE', 'MONROE', 'NASSAU',
  'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS',
  'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA', 'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE',
  'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
];

export function ProductionPropertySearch({}: PropertySearchProps) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Search state
  const [query, setQuery] = useState('');
  const [county, setCounty] = useState('ALL');
  const [propertyType, setPropertyType] = useState('ALL');
  const [properties, setProperties] = useState<PropertyCard[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // UI state
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(50);
  const [totalResults, setTotalResults] = useState(0);

  // Numeric and inferred filters (AI-parsed)
  const [minValue, setMinValue] = useState<number | undefined>(undefined)
  const [maxValue, setMaxValue] = useState<number | undefined>(undefined)
  const [minBeds, setMinBeds] = useState<number | undefined>(undefined)
  const [minBaths, setMinBaths] = useState<number | undefined>(undefined)

  const [inferredFlags, setInferredFlags] = useState<{
    county?: boolean
    type?: boolean
    minValue?: boolean
    maxValue?: boolean
    minBeds?: boolean
    minBaths?: boolean
  }>({})

  // Suggested natural-language queries
  const suggestedQueries: string[] = [
    'residential broward under 600k',
    '3/2 weston over 300k',
    'condo miami-dade under 400k',
    'industrial orlando over 1m',
  ]

  const handleSuggestedQuery = (qStr: string) => {
    setQuery(qStr)
    // Trigger search with inferred filters
    performSearch({
      query: qStr,
      county: county !== 'ALL' ? county : undefined,
      use_categories: propertyType !== 'ALL' ? [propertyType] : undefined,
      limit: pageSize,
      offset: 0,
    })
  }

  // Initialize from URL params
  useEffect(() => {
    const queryParam = searchParams.get('q') || '';
    const countyParam = searchParams.get('county') || 'ALL';
    const typeParam = searchParams.get('type') || 'ALL';

    setQuery(queryParam);
    setCounty(countyParam);
    setPropertyType(typeParam);

    // Perform search if there are params
    if (queryParam || countyParam !== 'ALL' || typeParam !== 'ALL') {
      performSearch({
        query: queryParam,
        county: countyParam,
        use_categories: typeParam !== 'ALL' ? [typeParam] : undefined,
        limit: pageSize,
        offset: 0
      });
    }
  }, []);

  // Update URL when search params change
  const updateURL = useCallback((params: { query?: string; county?: string; propertyType?: string }) => {
    const newSearchParams = new URLSearchParams(searchParams);

    if (params.query) {
      newSearchParams.set('q', params.query);
    } else {
      newSearchParams.delete('q');
    }

    if (params.county && params.county !== 'ALL') {
      newSearchParams.set('county', params.county);
    } else {
      newSearchParams.delete('county');
    }

    if (params.propertyType && params.propertyType !== 'ALL') {
      newSearchParams.set('type', params.propertyType);
    } else {
      newSearchParams.delete('type');
    }

    setSearchParams(newSearchParams);
  }, [searchParams, setSearchParams]);

  // Perform search using unified service
  const performSearch = async (searchParams: SearchParams) => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔍 Performing search with params:', searchParams);

      // Apply AI-assisted query understanding for county/type/price/beds/baths
      if (searchParams.query) {
        const parsed = parseQueryToFilters(searchParams.query, FLORIDA_COUNTIES)
        if (parsed.county && !searchParams.county) {
          searchParams.county = parsed.county
          setCounty(parsed.county)
          setInferredFlags(prev => ({ ...prev, county: true }))
        }
        if (parsed.useCategory && (!searchParams.use_categories || searchParams.use_categories.length === 0)) {
          searchParams.use_categories = [parsed.useCategory]
          setPropertyType(parsed.useCategory)
          setInferredFlags(prev => ({ ...prev, type: true }))
        }
        if (parsed.maxValue) { setMaxValue(parsed.maxValue); setInferredFlags(prev => ({ ...prev, maxValue: true })) }
        if (parsed.minValue) { setMinValue(parsed.minValue); setInferredFlags(prev => ({ ...prev, minValue: true })) }
        if (parsed.minBeds) { setMinBeds(parsed.minBeds); setInferredFlags(prev => ({ ...prev, minBeds: true })) }
        if (parsed.minBaths) { setMinBaths(parsed.minBaths); setInferredFlags(prev => ({ ...prev, minBaths: true })) }
      }

      // Include numeric filters from state (inferred or user-set)
      const sp: any = { ...searchParams }
      if (typeof minValue === 'number') sp.minValue = minValue
      if (typeof maxValue === 'number') sp.maxValue = maxValue
      if (typeof minBeds === 'number') sp.minBeds = minBeds
      if (typeof minBaths === 'number') sp.minBaths = minBaths

      const response = await unifiedSearchService.searchProperties(sp);

      setProperties(response.properties);
      setTotalResults(response.total_found);

      console.log(`📊 Search completed: ${response.properties.length} properties found`);

      // Update URL
      updateURL({
        query: searchParams.query,
        county: searchParams.county,
        propertyType: searchParams.use_categories?.[0]
      });

    } catch (err) {
      console.error('Search failed:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
      setProperties([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  // Handle search form submission
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();

    setCurrentPage(1);

    performSearch({
      query: query.trim() || undefined,
      county: county !== 'ALL' ? county : undefined,
      use_categories: propertyType !== 'ALL' ? [propertyType] : undefined,
      limit: pageSize,
      offset: 0
    });
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);

    performSearch({
      query: query.trim() || undefined,
      county: county !== 'ALL' ? county : undefined,
      use_categories: propertyType !== 'ALL' ? [propertyType] : undefined,
      limit: pageSize,
      offset: (page - 1) * pageSize
    });
  };

  // Clear all filters
  const clearFilters = () => {
    setQuery('');
    setCounty('ALL');
    setPropertyType('ALL');
    setCurrentPage(1);
    setProperties([]);
    setTotalResults(0);
    setSearchParams(new URLSearchParams());
  };

  // Calculate pagination
  const totalPages = Math.ceil(totalResults / pageSize);
  const startIndex = (currentPage - 1) * pageSize + 1;
  const endIndex = Math.min(currentPage * pageSize, totalResults);

  return (
    <div className="min-h-screen bg-gray-50 property-search-page" id="property-search-page-1">
      <div className="container mx-auto px-4 py-6">
        {/* Production Dataset Banner */}
        <div className="mb-6">
          <ProductionDatasetBanner />
        </div>

        {/* Executive Search Header */}
        <div className="mb-6 rounded-xl p-6 shadow-lg" style={{background: 'linear-gradient(135deg, #2c3e50 0%, #1a252f 100%)'}}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Property Search</h1>
              <p className="text-yellow-100">
                Search all {' '}
                <span className="font-semibold text-yellow-300">7.31 million</span>
                {' '} Florida properties across all 67 counties
              </p>
            </div>
            <ProductionDatasetIndicator />
          </div>
        </div>

        {/* Search Form */}
        <Card className="mb-6 shadow-lg border-l-4 border-l-yellow-400" id="property-search-form-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-800">
              <Search className="w-5 h-5 text-yellow-600" />
              Search Properties
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="space-y-4">
              {/* Helper: Natural-language tips and examples */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-gray-600">
                  <Info className="w-4 h-4 text-gray-500" />
                  Try natural language: “3/2 weston over 300k”, “residential broward under 600k”
                </div>
                <div className="hidden md:flex items-center gap-1">
                  {suggestedQueries.map((s, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSuggestedQuery(s)}
                      className="text-xs px-2 py-1 rounded border border-gray-200 hover:border-blue-300 hover:text-blue-700 bg-white"
                      title={`Search: ${s}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
              {/* Inferred filters badges */}
              {(inferredFlags.county || inferredFlags.type || inferredFlags.minValue || inferredFlags.maxValue || inferredFlags.minBeds || inferredFlags.minBaths) && (
                <div className="flex flex-wrap gap-2 mb-2">
                  {inferredFlags.county && county !== 'ALL' && (
                    <button type="button" className="px-2 py-1 text-xs rounded-full border border-yellow-300 bg-yellow-50 text-yellow-800" onClick={() => { setCounty('ALL'); setInferredFlags(prev => ({ ...prev, county: false })); setCurrentPage(1); handleSearch(new Event('submit') as any) }}>County: {county} ×</button>
                  )}
                  {inferredFlags.type && propertyType !== 'ALL' && (
                    <button type="button" className="px-2 py-1 text-xs rounded-full border border-yellow-300 bg-yellow-50 text-yellow-800" onClick={() => { setPropertyType('ALL'); setInferredFlags(prev => ({ ...prev, type: false })); setCurrentPage(1); handleSearch(new Event('submit') as any) }}>Type: {propertyType} ×</button>
                  )}
                  {inferredFlags.maxValue && typeof maxValue === 'number' && (
                    <button type="button" className="px-2 py-1 text-xs rounded-full border border-yellow-300 bg-yellow-50 text-yellow-800" onClick={() => { setMaxValue(undefined); setInferredFlags(prev => ({ ...prev, maxValue: false })); setCurrentPage(1); handleSearch(new Event('submit') as any) }}>Max: ${maxValue.toLocaleString()} ×</button>
                  )}
                  {inferredFlags.minValue && typeof minValue === 'number' && (
                    <button type="button" className="px-2 py-1 text-xs rounded-full border border-yellow-300 bg-yellow-50 text-yellow-800" onClick={() => { setMinValue(undefined); setInferredFlags(prev => ({ ...prev, minValue: false })); setCurrentPage(1); handleSearch(new Event('submit') as any) }}>Min: ${minValue.toLocaleString()} ×</button>
                  )}
                  {inferredFlags.minBeds && typeof minBeds === 'number' && (
                    <button type="button" className="px-2 py-1 text-xs rounded-full border border-yellow-300 bg-yellow-50 text-yellow-800" onClick={() => { setMinBeds(undefined); setInferredFlags(prev => ({ ...prev, minBeds: false })); setCurrentPage(1); handleSearch(new Event('submit') as any) }}>Beds: {minBeds}+ ×</button>
                  )}
                  {inferredFlags.minBaths && typeof minBaths === 'number' && (
                    <button type="button" className="px-2 py-1 text-xs rounded-full border border-yellow-300 bg-yellow-50 text-yellow-800" onClick={() => { setMinBaths(undefined); setInferredFlags(prev => ({ ...prev, minBaths: false })); setCurrentPage(1); handleSearch(new Event('submit') as any) }}>Baths: {minBaths}+ ×</button>
                  )}
                </div>
              )}
              {/* Main Search Row */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-2">
                  <Input
                    placeholder="Search by address, city, zip, or owner name..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="h-11"
                    id="property-search-input-1"
                  />
                </div>

                <Select value={county} onValueChange={setCounty}>
                  <SelectTrigger className="h-11" id="county-filter-select-1">
                    <SelectValue placeholder="Select County" />
                  </SelectTrigger>
                  <SelectContent>
                    {FLORIDA_COUNTIES.map((countyName) => (
                      <SelectItem key={countyName} value={countyName}>
                        {countyName === 'ALL' ? 'All Counties' : countyName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={propertyType} onValueChange={setPropertyType}>
                  <SelectTrigger className="h-11" id="property-type-select-1">
                    <SelectValue placeholder="Property Type" />
                  </SelectTrigger>
                  <SelectContent>
                    {PROPERTY_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Button
                    type="submit"
                    disabled={loading}
                    className="h-11"
                    id="search-submit-button-1"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Searching...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4 mr-2" />
                        Search Properties
                      </>
                    )}
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    onClick={clearFilters}
                    className="h-11"
                    id="clear-filters-button-1"
                  >
                    Clear Filters
                  </Button>

                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                    className="h-11"
                    id="advanced-filters-button-1"
                  >
                    <Filter className="w-4 h-4 mr-2" />
                    Advanced
                  </Button>
                </div>

                {/* View Mode Toggle */}
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant={viewMode === 'grid' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('grid')}
                    id="grid-view-button-1"
                  >
                    <Grid3X3 className="w-4 h-4" />
                  </Button>
                  <Button
                    type="button"
                    variant={viewMode === 'list' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('list')}
                    id="list-view-button-1"
                  >
                    <List className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Search Results Summary */}
        {(properties.length > 0 || loading || error) && (
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              {error ? (
                <div className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="w-5 h-5" />
                  <span>Search failed: {error}</span>
                </div>
              ) : loading ? (
                <div className="flex items-center gap-2 text-blue-600">
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Searching properties...</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="text-gray-900 font-medium">
                    {totalResults.toLocaleString()} properties found
                  </span>
                  {totalResults > pageSize && (
                    <span className="text-gray-500">
                      (showing {startIndex}-{endIndex})
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Active Filters */}
            <div className="flex items-center gap-2">
              {query && (
                <Badge variant="secondary" className="gap-1">
                  Query: "{query}"
                </Badge>
              )}
              {county !== 'ALL' && (
                <Badge variant="secondary" className="gap-1">
                  County: {county}
                </Badge>
              )}
              {propertyType !== 'ALL' && (
                <Badge variant="secondary" className="gap-1">
                  Type: {propertyType}
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Property Results */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="property-results-loading-1">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : error ? (
          <Card className="p-8 text-center" id="property-results-error-1">
            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Search Error</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={() => handleSearch({ preventDefault: () => {} } as React.FormEvent)}>
              Try Again
            </Button>
          </Card>
        ) : properties.length === 0 ? (
          <Card className="p-8 text-center" id="property-results-empty-1">
            <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Properties Found</h3>
            <p className="text-gray-600 mb-4">
              Try adjusting your search criteria or removing some filters.
            </p>
            <Button variant="outline" onClick={clearFilters}>
              Clear All Filters
            </Button>
          </Card>
        ) : (
          <>
            {/* Property Grid with Enhanced Cards */}
            <div className={`grid gap-4 mb-6 ${
              viewMode === 'grid'
                ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
                : 'grid-cols-1'
            }`} id="property-results-grid-1">
              {properties.map((property, index) => {
                // Map the property data to the expected format for EnhancedPropertyMiniCard
                const mappedProperty = {
                  parcel_id: property.parcel_id,
                  phy_addr1: property.full_address || property.address,
                  phy_city: property.city,
                  phy_state: 'FL',
                  phy_zipcd: property.zip,
                  owner_name: property.owner_name,
                  just_value: property.market_value || property.just_value,
                  assessed_value: property.assessed_value,
                  land_value: property.land_value,
                  building_value: property.building_value || (property.market_value && property.land_value ? property.market_value - property.land_value : undefined),
                  building_sqft: property.living_area || property.building_sqft,
                  land_sqft: property.land_sqft,
                  year_built: property.year_built,
                  property_use: property.use_category || property.property_type,
                  county: property.county,
                  sale_prc1: property.last_sale_price,
                  sale_date1: property.last_sale_date,
                  homestead: property.homestead,
                  bedrooms: property.bedrooms,
                  bathrooms: property.bathrooms
                };

                return (
                  <MiniPropertyCard
                    key={property.parcel_id}
                    data={mappedProperty}
                    onClick={() => {
                      // Navigate to enhanced property profile with proper URL structure
                      const county = (property.county || 'UNKNOWN').toLowerCase().replace(/\s+/g, '-');
                      const addressSlug = (property.full_address || property.address || 'property')
                        .toLowerCase()
                        .replace(/[^a-z0-9]+/g, '-')
                        .replace(/^-+|-+$/g, '');
                      navigate(`/property/${county}/${property.parcel_id}/${addressSlug}`);
                    }}
                    variant={viewMode === 'grid' ? 'grid' : 'list'}
                  />
                );
              })}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2" id="property-pagination-1">
                <Button
                  variant="outline"
                  disabled={currentPage === 1}
                  onClick={() => handlePageChange(currentPage - 1)}
                >
                  Previous
                </Button>

                {[...Array(Math.min(totalPages, 10))].map((_, i) => {
                  const pageNum = i + 1;
                  return (
                    <Button
                      key={pageNum}
                      variant={currentPage === pageNum ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handlePageChange(pageNum)}
                    >
                      {pageNum}
                    </Button>
                  );
                })}

                <Button
                  variant="outline"
                  disabled={currentPage === totalPages}
                  onClick={() => handlePageChange(currentPage + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ProductionPropertySearch;
