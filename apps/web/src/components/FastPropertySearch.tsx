import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MiniPropertyCard } from '@/components/property/MiniPropertyCard';
import { useOptimizedSearch } from '@/hooks/useOptimizedSearch';
import {
  Search,
  Filter,
  Grid3X3,
  List,
  RefreshCw,
  MapPin,
  Home,
  Building,
  Building2,
  Briefcase,
  TreePine,
  Loader2
} from 'lucide-react';

interface FastSearchFilters {
  q?: string;
  city?: string;
  county?: string;
  owner?: string;
  propertyType?: string;
  minValue?: number;
  maxValue?: number;
  minYear?: number;
  maxYear?: number;
}

export function FastPropertySearch() {
  const [filters, setFilters] = useState<FastSearchFilters>({});
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

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

  // Property type quick filters
  const propertyTypes = [
    { value: '', label: 'All Properties', icon: Grid3X3, color: '#d4af37' },
    { value: 'residential', label: 'Residential', icon: Home, color: '#22c55e' },
    { value: 'commercial', label: 'Commercial', icon: Building, color: '#3b82f6' },
    { value: 'industrial', label: 'Industrial', icon: Briefcase, color: '#fb923c' },
    { value: 'agricultural', label: 'Agricultural', icon: TreePine, color: '#f59e0b' },
    { value: 'vacant', label: 'Vacant Land', icon: MapPin, color: '#6b7280' },
    { value: 'government', label: 'Government', icon: Building2, color: '#ef4444' }
  ];

  const currentMetrics = metrics();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Property Search</h1>
              <p className="mt-1 text-sm text-gray-500">
                Fast search across 6.4M Florida properties
              </p>
            </div>

            {/* Performance Metrics */}
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <span>Cache Hit Rate:</span>
                <Badge variant="outline">
                  {currentMetrics.cacheHitRate.toFixed(1)}%
                </Badge>
              </div>
              <div className="flex items-center space-x-1">
                <span>Avg Response:</span>
                <Badge variant="outline">
                  {currentMetrics.avgResponseTime.toFixed(0)}ms
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearCache}
                className="h-8"
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Search Controls */}
        <Card className="mb-6">
          <CardHeader className="pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Search Filters</CardTitle>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                >
                  <Filter className="w-4 h-4 mr-2" />
                  Advanced
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearFilters}
                >
                  Clear All
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Main Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search by address, city, owner, or parcel ID..."
                value={filters.q || ''}
                onChange={(e) => handleFilterChange('q', e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Property Type Quick Filters */}
            <div className="flex flex-wrap gap-2">
              {propertyTypes.map((type) => {
                const Icon = type.icon;
                const isSelected = filters.propertyType === type.value;

                return (
                  <button
                    key={type.value}
                    onClick={() => handleFilterChange('propertyType',
                      isSelected ? '' : type.value)}
                    className="inline-flex items-center rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105 cursor-pointer"
                    style={{
                      backgroundColor: isSelected ? type.color : 'white',
                      color: isSelected ? 'white' : type.color,
                      borderColor: type.color
                    }}
                  >
                    <Icon className="w-4 h-4 mr-1.5" />
                    {type.label}
                  </button>
                );
              })}
            </div>

            {/* Advanced Filters */}
            {showAdvancedFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    City
                  </label>
                  <Input
                    placeholder="Enter city name"
                    value={filters.city || ''}
                    onChange={(e) => handleFilterChange('city', e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Owner Name
                  </label>
                  <Input
                    placeholder="Enter owner name"
                    value={filters.owner || ''}
                    onChange={(e) => handleFilterChange('owner', e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    County
                  </label>
                  <Select
                    value={filters.county || 'all'}
                    onValueChange={(value) => handleFilterChange('county', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select county" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Counties</SelectItem>
                      <SelectItem value="BROWARD">Broward</SelectItem>
                      <SelectItem value="MIAMI-DADE">Miami-Dade</SelectItem>
                      <SelectItem value="PALM BEACH">Palm Beach</SelectItem>
                      <SelectItem value="ORANGE">Orange</SelectItem>
                      <SelectItem value="HILLSBOROUGH">Hillsborough</SelectItem>
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
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
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

          <div className="flex items-center space-x-2">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('grid')}
            >
              <Grid3X3 className="w-4 h-4" />
            </Button>
            <Button
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
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          </div>
        )}

        {!loading && results && results.properties.length > 0 && (
          <div className={viewMode === 'grid'
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
                  propertyType: property.propertyType,
                  propertyUseDesc: property.propertyUseDesc,
                  sale_prc1: property.lastSalePrice,
                  sale_yr1: property.lastSaleDate ? new Date(property.lastSaleDate).getFullYear() : null,
                  sale_date: property.lastSaleDate,
                  assessed_value: property.assessedValue,
                  taxable_value: property.taxableValue,
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
                } as any}
                variant={viewMode}
                showQuickActions={false}
              />
            ))}
          </div>
        )}

        {!loading && results && results.properties.length === 0 && (
          <Card className="p-8 text-center">
            <div className="text-gray-500">
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
