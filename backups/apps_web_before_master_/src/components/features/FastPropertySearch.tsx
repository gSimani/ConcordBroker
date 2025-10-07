import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MiniPropertyCard } from '@/components/property/MiniPropertyCard';
import { useOptimizedSearch } from '@/hooks/useOptimizedSearch';
import { useElementId } from '@/utils/generateElementId';
import { ConcordBemPatterns } from '@/utils/bemClassNames';
import { getAllUseCategories, UseIcon } from '@/lib/icons/useIcons';
import searchStyles from '@/styles/components/search-form.module.css';
import layoutStyles from '@/styles/components/layout.module.css';
import {
  Search,
  Filter,
  Grid3X3,
  List,
  RefreshCw,
  Loader2
} from 'lucide-react';

interface FastSearchFilters {
  q?: string;
  city?: string;
  county?: string;
  owner?: string;
  propertyType?: string;
  use?: string;
  minValue?: number;
  maxValue?: number;
  minYear?: number;
  maxYear?: number;
}

export function FastPropertySearch() {
  const [filters, setFilters] = useState<FastSearchFilters>({});
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // Generate IDs for this page
  const { generateId, generateTestId } = useElementId('property-search');

  // BEM class generators
  const searchForm = ConcordBemPatterns.searchForm;
  const layout = ConcordBemPatterns.layout;

  const {
    search,
    loading,
    results,
    suggestions,
    getSuggestions,
    metrics,
    clearCache
  } = useOptimizedSearch();

  // Auto-search when filters change with debouncing
  // Also do initial search on component mount
  useEffect(() => {
    search(filters); // Search with current filters (even if empty)
  }, [filters, search]);

  const handleFilterChange = useCallback((key: keyof FastSearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === 'all' ? undefined : value
    }));
  }, []);

  const handleQuickSearch = useCallback((searchTerm: string) => {
    setFilters({ q: searchTerm });
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilters({});
  }, []);

  // Get use categories from centralized icon mapping
  const useCategories = getAllUseCategories();

  const currentMetrics = metrics();

  return (
    <div
      id={generateId('main', 'container', 1)}
      data-testid="property-search"
      className={layout.block(null, 'min-h-screen bg-gray-50')}
    >
      {/* Header */}
      <div
        id={generateId('header', 'section', 1)}
        className={layout.element('header', null, 'bg-white border-b')}
      >
        <div
          id={generateId('header', 'content-wrapper', 1)}
          className={layout.element('header-container', null, 'max-w-7xl mx-auto px-4 py-6')}
        >
          <div
            id={generateId('header', 'flex-container', 1)}
            className={layout.element('header-content', null, 'flex items-center justify-between')}
          >
            <div id={generateId('header', 'title-group', 1)} className={layout.element('header-left')}>
              <h1 className={layout.element('title', 'large', 'text-3xl font-bold text-gray-900')}>
                Property Search
              </h1>
              <p className={layout.element('subtitle', null, 'mt-1 text-sm text-gray-500')}>
                Fast search across 6.4M Florida properties
              </p>
            </div>

            {/* Performance Metrics */}
            <div
              id={generateId('header', 'metrics-container', 1)}
              className={layout.element('header-right', null, 'flex items-center space-x-4 text-sm text-gray-500')}
            >
              <div
                id={generateId('header', 'cache-metric', 1)}
                className={layout.element('metric', null, 'flex items-center space-x-1')}
              >
                <span>Cache Hit Rate:</span>
                <Badge variant="outline">
                  {currentMetrics.cacheHitRate.toFixed(1)}%
                </Badge>
              </div>
              <div
                id={generateId('header', 'response-metric', 1)}
                className={layout.element('metric', null, 'flex items-center space-x-1')}
              >
                <span>Avg Response:</span>
                <Badge variant="outline">
                  {currentMetrics.avgResponseTime.toFixed(0)}ms
                </Badge>
              </div>
              <Button
                id={generateId('header', 'clear-cache-button', 1)}
                data-testid={generateTestId('clear-cache', 'button')}
                variant="ghost"
                size="sm"
                onClick={clearCache}
                className={layout.element('action-button', null, 'h-8')}
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div
        id={generateId('content', 'main-wrapper', 1)}
        className={layout.element('main-container', null, 'max-w-7xl mx-auto px-4 py-6')}
      >
        {/* Search Controls */}
        <Card
          id={generateId('filters', 'card-container', 1)}
          className={searchForm.block(showAdvancedFilters ? 'expanded' : null, 'mb-6')}
        >
          <CardHeader className={searchForm.element('header')}>
            <div
              id={generateId('filters', 'header-container', 1)}
              className={searchForm.element('header-container')}
            >
              <CardTitle className={searchForm.element('title')}>Search Filters</CardTitle>
              <div
                id={generateId('filters', 'button-group', 1)}
                className={searchForm.element('actions')}
              >
                <Button
                  id={generateId('filters', 'advanced-toggle', 1)}
                  data-testid={generateTestId('filters', 'toggle-advanced')}
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  className={searchForm.element('toggle-button', showAdvancedFilters ? 'active' : null)}
                >
                  <Filter className={searchForm.element('toggle-icon')} />
                  Advanced
                </Button>
                <Button
                  id={generateId('filters', 'clear-all-button', 1)}
                  data-testid={generateTestId('filters', 'clear-all')}
                  variant="ghost"
                  size="sm"
                  onClick={handleClearFilters}
                  className={searchForm.element('clear-button')}
                >
                  Clear All
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className={searchForm.element('content')}>
            {/* Main Search */}
            <div
              id={generateId('filters', 'search-container', 1)}
              className={searchForm.element('main-search')}
            >
              <Search className={searchForm.element('search-icon')} />
              <Input
                id={generateId('filters', 'search-input', 1)}
                data-testid={generateTestId('search', 'input', 'main')}
                placeholder="Search by address, city, owner, or parcel ID..."
                value={filters.q || ''}
                onChange={(e) => handleFilterChange('q', e.target.value)}
                className={searchForm.element('search-input')}
              />
            </div>

            {/* Property Use Category Quick Filters */}
            <div
              id={generateId('filters', 'use-category-container', 1)}
              className={searchForm.element('quick-filters')}
            >
              {useCategories.map((category) => {
                const isSelected = filters.use === category.value;
                const Icon = category.config.icon;

                return (
                  <button
                    id={generateId('filters', `use-category-${category.value || 'all'}`, 1)}
                    data-testid={`filter-chip-${category.value || 'all'}`}
                    key={category.value}
                    onClick={() => handleFilterChange('use',
                      isSelected ? '' : category.value)}
                    className={searchForm.element('filter-button', isSelected ? 'selected' : 'unselected') + (isSelected ? ' active selected' : '')}
                    style={{
                      backgroundColor: isSelected ? category.config.color : 'white',
                      color: isSelected ? 'white' : category.config.color,
                      borderColor: category.config.color
                    }}
                  >
                    <Icon className={searchForm.element('filter-icon')} />
                    {category.label}
                  </button>
                );
              })}
            </div>

            {/* Advanced Filters */}
            {showAdvancedFilters && (
              <div
                id={generateId('filters', 'advanced-section', 1)}
                className={searchForm.element('advanced-section', 'expanded')}
              >
                <div
                  id={generateId('filters', 'city-field', 1)}
                  className={searchForm.element('field-group')}
                >
                  <label className={searchForm.element('field-label')}>
                    City
                  </label>
                  <Input
                    id={generateId('filters', 'city-input', 1)}
                    data-testid={generateTestId('filters', 'input', 'city')}
                    placeholder="Enter city name"
                    value={filters.city || ''}
                    onChange={(e) => handleFilterChange('city', e.target.value)}
                    className={searchForm.element('field-input')}
                  />
                </div>

                <div
                  id={generateId('filters', 'owner-field', 1)}
                  className={searchForm.element('field-group')}
                >
                  <label className={searchForm.element('field-label')}>
                    Owner Name
                  </label>
                  <Input
                    id={generateId('filters', 'owner-input', 1)}
                    data-testid={generateTestId('filters', 'input', 'owner')}
                    placeholder="Enter owner name"
                    value={filters.owner || ''}
                    onChange={(e) => handleFilterChange('owner', e.target.value)}
                    className={searchForm.element('field-input')}
                  />
                </div>

                <div
                  id={generateId('filters', 'county-field', 1)}
                  className={searchForm.element('field-group')}
                >
                  <label className={searchForm.element('field-label')}>
                    County
                  </label>
                  <Select
                    value={filters.county || 'all'}
                    onValueChange={(value) => handleFilterChange('county', value)}
                  >
                    <SelectTrigger className={searchForm.element('field-select')}>
                      <SelectValue placeholder="Select county" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Counties</SelectItem>
                      <SelectItem value="HILLSBOROUGH">Hillsborough</SelectItem>
                      <SelectItem value="ORANGE">Orange</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Min Value
                  </label>
                  <Input
                    type="number"
                    placeholder="$0"
                    value={filters.minValue || ''}
                    onChange={(e) => handleFilterChange('minValue',
                      e.target.value ? parseInt(e.target.value) : undefined)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Value
                  </label>
                  <Input
                    type="number"
                    placeholder="No limit"
                    value={filters.maxValue || ''}
                    onChange={(e) => handleFilterChange('maxValue',
                      e.target.value ? parseInt(e.target.value) : undefined)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Year Built (Min)
                  </label>
                  <Input
                    type="number"
                    placeholder="Any year"
                    value={filters.minYear || ''}
                    onChange={(e) => handleFilterChange('minYear',
                      e.target.value ? parseInt(e.target.value) : undefined)}
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Header */}
        <div id={generateId('results', 'header-container', 1)} className="flex items-center justify-between mb-4">
          <div id={generateId('results', 'count-container', 1)} className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold">
              {loading && (
                <div className="flex items-center">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Searching...
                </div>
              )}
              {!loading && results && (
                <>
                  {results.total.toLocaleString()} Properties Found
                  {results.cached && (
                    <Badge variant="secondary" className="ml-2">
                      Cached ({results.responseTime.toFixed(0)}ms)
                    </Badge>
                  )}
                </>
              )}
            </h2>
          </div>

          <div id={generateId('results', 'view-toggle', 1)} className="flex items-center space-x-2">
            <Button
              id={generateId('results', 'grid-view-button', 1)}
              data-testid={generateTestId('view', 'toggle', 'grid')}
              variant={viewMode === 'grid' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('grid')}
            >
              <Grid3X3 className="w-4 h-4" />
            </Button>
            <Button
              id={generateId('results', 'list-view-button', 1)}
              data-testid={generateTestId('view', 'toggle', 'list')}
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Results Grid */}
        {loading && (
          <div id={generateId('results', 'loading-container', 1)} data-testid="loading" className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          </div>
        )}

        {!loading && results && results.properties.length > 0 && (
          <div
            id={generateId('results', 'properties-container', 1)}
            className={viewMode === 'grid'
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'
            : 'space-y-4'
          }>
            {results.properties.map((property) => (
              <MiniPropertyCard
                key={property.id || property.parcel_id}
                parcelId={property.parcel_id || property.id}
                data={{
                  phy_addr1: property.address,
                  phy_city: property.city,
                  phy_zipcd: property.zipCode,
                  own_name: property.owner,
                  owner_name: property.owner,
                  jv: property.marketValue || property.justValue,
                  tv_sd: property.taxableValue || property.assessedValue,
                  lnd_val: property.landValue || 0,
                  tot_lvg_area: property.buildingSqFt,
                  lnd_sqfoot: property.landSqFt,
                  act_yr_blt: property.yearBuilt,
                  dor_uc: property.propertyUse,
                  property_use: property.propertyUse,
                  propertyType: property.propertyType,
                  propertyUseDesc: property.propertyUseDesc,
                  use_category: property.use_category,
                  sale_prc1: property.lastSalePrice,
                  sale_yr1: property.lastSaleDate ? new Date(property.lastSaleDate).getFullYear() : null,
                  sale_date: property.lastSaleDate,
                  assessed_value: property.assessedValue,
                  taxable_value: property.taxableValue,
                  bedrooms: property.bedrooms,
                  bathrooms: property.bathrooms,
                  co_no: property.county,
                  owner_addr1: property.ownerAddress,
                  // Investment indicators
                  investmentScore: property.investmentScore,
                  capRate: property.capRate,
                  pricePerSqFt: property.pricePerSqFt,
                  isDistressed: property.isDistressed,
                  isTaxDelinquent: property.isTaxDelinquent,
                  hasHomestead: property.hasHomestead,
                  // Tax information
                  taxAmount: property.taxAmount,
                  millageRate: property.millageRate,
                  exemptions: property.exemptions,
                  // Location data
                  latitude: property.latitude,
                  longitude: property.longitude,
                  neighborhood: property.neighborhood
                }}
                variant={viewMode}
                showQuickActions={false}
              />
            ))}
          </div>
        )}

        {!loading && results && results.properties.length === 0 && (
          <Card id={generateId('results', 'no-results-card', 1)} data-testid="no-results" className="p-8 text-center">
            <div id={generateId('results', 'no-results-content', 1)} className="text-gray-500">
              <Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium mb-2">No properties found</h3>
              <p>Try adjusting your search filters or search terms.</p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

export default FastPropertySearch;