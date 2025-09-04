import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MiniPropertyCard } from '@/components/property/MiniPropertyCard';
import { 
  Search, 
  Filter, 
  MapPin, 
  Grid3X3, 
  List,
  SlidersHorizontal,
  TrendingUp,
  Building,
  Home,
  RefreshCw,
  Download,
  Map
} from 'lucide-react';
import { useRouter } from 'next/router';

interface PropertySearchProps {}

interface SearchFilters {
  address: string;
  city: string;
  zipCode: string;
  owner: string;
  propertyType: string;
  minValue: string;
  maxValue: string;
  minYear: string;
  maxYear: string;
}

export function PropertySearch({}: PropertySearchProps) {
  const router = useRouter();
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  
  const [filters, setFilters] = useState<SearchFilters>({
    address: '',
    city: '',
    zipCode: '',
    owner: '',
    propertyType: '',
    minValue: '',
    maxValue: '',
    minYear: '',
    maxYear: ''
  });

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
    { value: 'Residential', label: 'Residential' },
    { value: 'Commercial', label: 'Commercial' },
    { value: 'Industrial', label: 'Industrial' },
    { value: 'Agricultural', label: 'Agricultural' },
    { value: 'Government', label: 'Government' }
  ];

  // Search function
  const searchProperties = async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      // Add filters
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          // Map frontend keys to API keys
          const apiKey = {
            address: 'address',
            city: 'city',
            zipCode: 'zip_code',
            owner: 'owner',
            propertyType: 'property_type',
            minValue: 'min_value',
            maxValue: 'max_value'
          }[key] || key;
          
          params.append(apiKey, value);
        }
      });
      
      params.append('limit', '20');
      params.append('offset', ((page - 1) * 20).toString());
      
      const response = await fetch(`/api/properties/search?${params}`);
      const data = await response.json();
      
      setProperties(data.properties);
      setTotalResults(data.total);
      setCurrentPage(page);
      
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof SearchFilters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Quick address search
  const handleQuickSearch = (searchTerm: string) => {
    // Determine if it's an address, city, or parcel ID
    if (searchTerm.match(/^\d+\s/)) {
      // Starts with number - likely address
      handleFilterChange('address', searchTerm);
    } else if (searchTerm.match(/^\d{12}$/)) {
      // 12 digits - parcel ID
      router.push(`/properties/parcel/${searchTerm}`);
      return;
    } else {
      // Likely city or owner name
      handleFilterChange('city', searchTerm);
    }
    
    searchProperties();
  };

  // Navigate to property detail
  const handlePropertyClick = (property: any) => {
    // Use address-based routing
    const addressSlug = property.phy_addr1
      ?.toLowerCase()
      .replace(/[^a-z0-9]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');
    
    const citySlug = property.phy_city
      ?.toLowerCase()
      .replace(/[^a-z0-9]/g, '-');
    
    if (addressSlug && citySlug) {
      router.push(`/properties/${citySlug}/${addressSlug}`);
    } else {
      router.push(`/properties/${property.id}`);
    }
  };

  // Load initial data
  useEffect(() => {
    searchProperties();
  }, []);

  // Load data from URL params
  useEffect(() => {
    const { address, city, type } = router.query;
    if (address || city || type) {
      setFilters(prev => ({
        ...prev,
        address: address as string || '',
        city: city as string || '',
        propertyType: type as string || ''
      }));
      searchProperties();
    }
  }, [router.query]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Property Search</h1>
              <p className="text-gray-600 mt-1">
                Search Broward County properties by address, owner, or criteria
              </p>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-1" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <Map className="w-4 h-4 mr-1" />
                Map View
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Search Bar */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="space-y-4">
              {/* Primary Search */}
              <div className="flex space-x-2">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search by address (e.g. '123 Main St'), city, or owner name..."
                    className="pl-10 h-12 text-lg"
                    value={filters.address}
                    onChange={(e) => handleFilterChange('address', e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        searchProperties();
                      }
                    }}
                  />
                </div>
                <Button 
                  onClick={() => searchProperties()}
                  className="h-12 px-8"
                  disabled={loading}
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  Search
                </Button>
              </div>

              {/* Quick Filters */}
              <div className="flex flex-wrap gap-2">
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-gray-500" />
                  <Select 
                    value={filters.city} 
                    onValueChange={(value) => handleFilterChange('city', value)}
                  >
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="Select City" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Cities</SelectItem>
                      {popularCities.map(city => (
                        <SelectItem key={city} value={city}>{city}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center space-x-2">
                  <Building className="w-4 h-4 text-gray-500" />
                  <Select 
                    value={filters.propertyType} 
                    onValueChange={(value) => handleFilterChange('propertyType', value)}
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Property Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">All Types</SelectItem>
                      {propertyTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                >
                  <SlidersHorizontal className="w-4 h-4 mr-1" />
                  Advanced
                </Button>
              </div>

              {/* Advanced Filters */}
              {showAdvancedFilters && (
                <div className="border-t pt-4 mt-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <label className="text-sm text-gray-600 mb-1 block">ZIP Code</label>
                      <Input
                        placeholder="33301"
                        value={filters.zipCode}
                        onChange={(e) => handleFilterChange('zipCode', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-600 mb-1 block">Owner Name</label>
                      <Input
                        placeholder="Smith"
                        value={filters.owner}
                        onChange={(e) => handleFilterChange('owner', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-600 mb-1 block">Min Value</label>
                      <Input
                        placeholder="100000"
                        type="number"
                        value={filters.minValue}
                        onChange={(e) => handleFilterChange('minValue', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-sm text-gray-600 mb-1 block">Max Value</label>
                      <Input
                        placeholder="1000000"
                        type="number"
                        value={filters.maxValue}
                        onChange={(e) => handleFilterChange('maxValue', e.target.value)}
                      />
                    </div>
                  </div>
                  
                  <div className="flex justify-end mt-4 space-x-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        setFilters({
                          address: '',
                          city: '',
                          zipCode: '',
                          owner: '',
                          propertyType: '',
                          minValue: '',
                          maxValue: '',
                          minYear: '',
                          maxYear: ''
                        });
                        setCurrentPage(1);
                      }}
                    >
                      Clear All
                    </Button>
                    <Button 
                      size="sm"
                      onClick={() => searchProperties(1)}
                    >
                      Apply Filters
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Search Suggestions */}
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Quick Searches:</h3>
          <div className="flex flex-wrap gap-2">
            {[
              'High Value Properties ($1M+)',
              'Fort Lauderdale Waterfront',
              'Commercial Properties',
              'Recent Sales',
              'Government Owned'
            ].map(suggestion => (
              <Button
                key={suggestion}
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => {
                  if (suggestion.includes('$1M+')) {
                    handleFilterChange('minValue', '1000000');
                  } else if (suggestion.includes('Fort Lauderdale')) {
                    handleFilterChange('city', 'Fort Lauderdale');
                  } else if (suggestion.includes('Commercial')) {
                    handleFilterChange('propertyType', 'Commercial');
                  }
                  searchProperties();
                }}
              >
                {suggestion}
              </Button>
            ))}
          </div>
        </div>

        {/* Results Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold">
              {totalResults.toLocaleString()} Properties Found
            </h2>
            {filters.city && (
              <Badge variant="secondary">
                <MapPin className="w-3 h-3 mr-1" />
                {filters.city}
              </Badge>
            )}
            {filters.propertyType && (
              <Badge variant="secondary">
                <Building className="w-3 h-3 mr-1" />
                {filters.propertyType}
              </Badge>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex border rounded-lg">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('grid')}
              >
                <Grid3X3 className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === 'list' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('list')}
              >
                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">Searching properties...</p>
          </div>
        ) : (
          <>
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
                {properties.map((property) => (
                  <MiniPropertyCard
                    key={property.id}
                    parcelId={property.parcel_id}
                    data={property}
                    variant={viewMode}
                    onClick={() => handlePropertyClick(property)}
                    isWatched={property.is_watched}
                    hasNotes={property.note_count > 0}
                    priority={property.note_count > 5 ? 'high' : property.note_count > 2 ? 'medium' : 'low'}
                  />
                ))}
              </div>
            )}

            {/* Pagination */}
            {totalResults > 20 && (
              <div className="flex items-center justify-center space-x-2 mt-8">
                <Button
                  variant="outline"
                  disabled={currentPage === 1}
                  onClick={() => searchProperties(currentPage - 1)}
                >
                  Previous
                </Button>
                
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(5, Math.ceil(totalResults / 20)) }, (_, i) => {
                    const page = i + 1;
                    return (
                      <Button
                        key={page}
                        variant={currentPage === page ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => searchProperties(page)}
                      >
                        {page}
                      </Button>
                    );
                  })}
                </div>

                <Button
                  variant="outline"
                  disabled={currentPage >= Math.ceil(totalResults / 20)}
                  onClick={() => searchProperties(currentPage + 1)}
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