import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { MiniPropertyCard } from '@/components/property/MiniPropertyCard';
import { propertyService, Property } from '@/services/propertyService';
import { useNavigate } from 'react-router-dom';
import '@/styles/elegant-property.css';
import {
  Search,
  Filter,
  MapPin,
  Grid3X3,
  List,
  SlidersHorizontal,
  Building,
  Home,
  RefreshCw,
  Briefcase,
  TreePine,
  Factory,
  Wheat,
  DollarSign,
  Brain,
  Map,
  Gavel,
  Info
} from 'lucide-react';

interface PropertySearchProps {}

interface SearchFilters {
  address: string;
  city: string;
  owner: string;
  propertyType: string;
  minValue: string;
  maxValue: string;
  county: string;
}

export function PropertySearch({}: PropertySearchProps) {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const [filters, setFilters] = useState<SearchFilters>({
    address: '',
    city: '',
    owner: '',
    propertyType: 'Residential',
    minValue: '',
    maxValue: '',
    county: 'BROWARD'
  });

  // State for properties
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

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

  const propertyTypes = [
    { value: 'Residential', label: 'Residential', icon: Home },
    { value: 'Commercial', label: 'Commercial', icon: Building },
    { value: 'Industrial', label: 'Industrial', icon: Factory },
    { value: 'Agricultural', label: 'Agricultural', icon: Wheat },
    { value: 'Vacant', label: 'Vacant Land', icon: TreePine }
  ];

  const floridaCounties = [
    'BROWARD', 'MIAMI-DADE', 'PALM BEACH', 'ORANGE', 'HILLSBOROUGH',
    'PINELLAS', 'DUVAL', 'LEE', 'POLK', 'VOLUSIA'
  ];

  // Handle filter changes and trigger search
  const handleFilterChange = (key: keyof SearchFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Perform search with current filters
  const searchProperties = async () => {
    setLoading(true);
    setError(null);

    try {
      const searchParams: any = {
        county: filters.county,
        limit: pageSize,
        offset: (currentPage - 1) * pageSize
      };

      // Add filters if they have values
      if (filters.city && filters.city !== 'all-cities') {
        searchParams.city = filters.city;
      }
      if (filters.address) {
        searchParams.address = filters.address;
      }
      if (filters.owner) {
        searchParams.owner = filters.owner;
      }
      if (filters.propertyType && filters.propertyType !== 'All Properties') {
        searchParams.propertyType = filters.propertyType;
      }
      if (filters.minValue) {
        searchParams.minPrice = parseInt(filters.minValue);
      }
      if (filters.maxValue) {
        searchParams.maxPrice = parseInt(filters.maxValue);
      }

      const result = await propertyService.searchProperties(searchParams);
      console.log('PropertySearchRestored - searchProperties result:', result);
      console.log('PropertySearchRestored - first property from result:', result.properties[0]);
      console.log('PropertySearchRestored - first property jv field:', result.properties[0]?.jv);
      setProperties(result.properties);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search properties');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    searchProperties();
  }, []);

  // Auto-search when filters change (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchProperties();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [filters, currentPage, pageSize]);

  // Navigate to property detail
  const handlePropertyClick = (property: any) => {
    const parcelId = property.parcel_id || property.id;
    navigate(`/property/${parcelId}`);
  };

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

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
                Search {total.toLocaleString()} properties across Florida counties
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Elegant Tabs for Property Types */}
        <div className="tabs-executive flex justify-center mb-8" style={{borderBottom: '1px solid #ecf0f1'}}>
          {propertyTypes.map((type) => {
            const IconComponent = type.icon;
            return (
              <button
                key={type.value}
                onClick={() => handleFilterChange('propertyType', type.value)}
                className={`tab-executive ${filters.propertyType === type.value ? 'active' : ''}`}
                style={{
                  background: 'transparent',
                  color: filters.propertyType === type.value ? '#2c3e50' : '#7f8c8d',
                  border: 'none',
                  borderBottom: filters.propertyType === type.value ? '2px solid #d4af37' : '2px solid transparent',
                  fontWeight: '300',
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                  fontSize: '0.875rem',
                  padding: '1rem 1.5rem',
                  transition: 'all 0.3s ease',
                  cursor: 'pointer'
                }}
              >
                <IconComponent className="w-4 h-4 inline mr-2" />
                {type.label}
              </button>
            );
          })}
        </div>

        {/* Search Card */}
        <div className="elegant-card hover-lift animate-in mb-6" style={{
          background: '#ffffff',
          borderRadius: '12px',
          boxShadow: '0 10px 30px rgba(44, 62, 80, 0.1)',
          borderLeft: '3px solid #d4af37',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
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
              letterSpacing: '0.5px'
            }}>
              <Search className="w-5 h-5 mr-2" style={{color: '#2c3e50'}} />
              Search {filters.propertyType} Properties
            </h3>
            <p className="text-sm mt-3" style={{ color: '#7f8c8d' }}>
              Find properties in {filters.county} County with advanced search options
            </p>
          </div>

          <div className="p-8">
            {/* Main Search Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>
                  County
                </label>
                <Select value={filters.county} onValueChange={(value) => handleFilterChange('county', value)}>
                  <SelectTrigger className="h-12 rounded-lg" style={{borderColor: '#ecf0f1'}}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {floridaCounties.map(county => (
                      <SelectItem key={county} value={county}>{county}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>
                  City
                </label>
                <Select value={filters.city} onValueChange={(value) => handleFilterChange('city', value)}>
                  <SelectTrigger className="h-12 rounded-lg" style={{borderColor: '#ecf0f1'}}>
                    <SelectValue placeholder="Select City" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all-cities">All Cities</SelectItem>
                    {popularCities.map(city => (
                      <SelectItem key={city} value={city}>{city}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>
                  Address
                </label>
                <Input
                  placeholder="123 Main St"
                  className="h-12 rounded-lg"
                  style={{borderColor: '#ecf0f1'}}
                  value={filters.address}
                  onChange={(e) => handleFilterChange('address', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>
                  Owner Name
                </label>
                <Input
                  placeholder="John Smith"
                  className="h-12 rounded-lg"
                  style={{borderColor: '#ecf0f1'}}
                  value={filters.owner}
                  onChange={(e) => handleFilterChange('owner', e.target.value)}
                />
              </div>
            </div>

            {/* Advanced Filters Toggle */}
            <div className="flex justify-between items-center">
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

              <Button
                className="h-10 px-6 hover-lift"
                style={{background: '#d4af37', borderColor: '#d4af37'}}
                onClick={searchProperties}
                disabled={loading}
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
                Search Properties
              </Button>
            </div>

            {/* Advanced Filters */}
            {showAdvancedFilters && (
              <div className="border-t-2 pt-6 mt-6" style={{borderColor: '#d4af37'}}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>
                      Min Value
                    </label>
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
                    <label className="text-xs uppercase tracking-wider font-medium" style={{color: '#95a5a6'}}>
                      Max Value
                    </label>
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
              </div>
            )}
          </div>
        </div>

        {/* Results Header */}
        <div className="elegant-card hover-lift animate-in mb-6">
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h3 className="text-xl font-semibold" style={{color: '#2c3e50'}}>
                  {total.toLocaleString()} Properties Found
                </h3>
                {filters.city && filters.city !== 'all-cities' && (
                  <Badge className="bg-blue-100 text-blue-800 border-blue-200">
                    <MapPin className="w-3 h-3 mr-1" />
                    {filters.city}
                  </Badge>
                )}
                {filters.propertyType && (
                  <Badge className="bg-purple-100 text-purple-800 border-purple-200">
                    <Building className="w-3 h-3 mr-1" />
                    {filters.propertyType}
                  </Badge>
                )}
              </div>

              <div className="flex items-center space-x-3">
                <div className="flex border rounded-lg" style={{borderColor: '#ecf0f1'}}>
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    size="sm"
                    style={viewMode === 'grid' ? {background: '#d4af37', borderColor: '#d4af37'} : {}}
                    onClick={() => setViewMode('grid')}
                  >
                    <Grid3X3 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'ghost'}
                    size="sm"
                    style={viewMode === 'list' ? {background: '#d4af37', borderColor: '#d4af37'} : {}}
                    onClick={() => setViewMode('list')}
                  >
                    <List className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-red-200 bg-red-50">
            <CardContent className="p-6">
              <div className="flex items-center space-x-2 text-red-700">
                <Info className="w-5 h-5" />
                <span>Error loading properties: {error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">Searching properties...</p>
          </div>
        ) : properties.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <Search className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium mb-2">No Properties Found</h3>
              <p className="text-gray-600 mb-4">
                Try adjusting your search criteria or browse popular cities
              </p>
              <div className="flex justify-center space-x-2">
                {popularCities.slice(0, 3).map(city => (
                  <Button
                    key={city}
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      handleFilterChange('city', city);
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
            {properties.map((property: any, index: number) => {
              console.log(`PropertySearchRestored - rendering property ${index}:`, property);
              console.log(`PropertySearchRestored - property ${index} jv field:`, property.jv);
              return (
                <MiniPropertyCard
                  key={property.parcel_id || property.id}
                  parcelId={property.parcel_id}
                  data={property}
                  variant={viewMode}
                  onClick={() => handlePropertyClick(property)}
                  isWatched={false}
                  hasNotes={false}
                  priority="low"
                  isSelected={false}
                  onToggleSelection={() => {}}
                />
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {total > pageSize && !loading && (
          <div className="elegant-card hover-lift animate-in mt-8">
            <div className="p-6">
              <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
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
                      <SelectItem value="25">25</SelectItem>
                      <SelectItem value="50">50</SelectItem>
                      <SelectItem value="100">100</SelectItem>
                    </SelectContent>
                  </Select>
                  <span className="text-sm" style={{color: '#7f8c8d'}}>
                    Showing {((currentPage - 1) * pageSize) + 1} - {Math.min(currentPage * pageSize, total)} of {total.toLocaleString()} properties
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    disabled={currentPage === 1}
                    className="hover-lift h-9 px-4"
                    style={{borderColor: '#ecf0f1'}}
                    onClick={() => setCurrentPage(currentPage - 1)}
                  >
                    Previous
                  </Button>

                  <div className="flex items-center space-x-1">
                    {Array.from({ length: Math.min(5, Math.ceil(total / pageSize)) }, (_, i) => {
                      const page = i + 1;
                      const totalPages = Math.ceil(total / pageSize);
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
                          onClick={() => setCurrentPage(page)}
                        >
                          {page}
                        </Button>
                      );
                    })}
                  </div>

                  <Button
                    variant="outline"
                    disabled={currentPage >= Math.ceil(total / pageSize)}
                    className="hover-lift h-9 px-4"
                    style={{borderColor: '#ecf0f1'}}
                    onClick={() => setCurrentPage(currentPage + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PropertySearch;