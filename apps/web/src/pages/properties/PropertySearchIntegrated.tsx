import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MiniPropertyCard } from '@/components/property/MiniPropertyCard';
import { usePropertyAppraiser } from '@/hooks/usePropertyAppraiser';
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
  Loader2,
  Database,
  DollarSign
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface PropertySearchIntegratedProps {}

export function PropertySearchIntegrated({}: PropertySearchIntegratedProps) {
  const navigate = useNavigate();
  const { 
    loading, 
    error, 
    searchProperties, 
    getCounties, 
    getTopProperties,
    getStatistics 
  } = usePropertyAppraiser();

  const [properties, setProperties] = useState<any[]>([]);
  const [counties, setCounties] = useState<any[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [activeTab, setActiveTab] = useState('search');
  const [statistics, setStatistics] = useState<any>(null);
  
  // Search filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCounty, setSelectedCounty] = useState('');
  const [minValue, setMinValue] = useState('');
  const [maxValue, setMaxValue] = useState('');
  const [propertyType, setPropertyType] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(50);

  // Load counties on mount
  useEffect(() => {
    loadCounties();
    loadTopProperties();
  }, []);

  const loadCounties = async () => {
    const countyList = await getCounties();
    setCounties(countyList);
  };

  const loadTopProperties = async () => {
    const topProps = await getTopProperties(selectedCounty, 10);
    if (activeTab === 'top' && topProps.length > 0) {
      setProperties(topProps);
    }
  };

  const handleSearch = async () => {
    const results = await searchProperties({
      q: searchQuery,
      county: selectedCounty,
      minValue: minValue ? parseFloat(minValue) : undefined,
      maxValue: maxValue ? parseFloat(maxValue) : undefined,
      propertyType: propertyType || undefined,
      limit: pageSize,
      offset: currentPage * pageSize
    });
    setProperties(results);
  };

  const handlePropertyClick = (property: any) => {
    // Navigate to property details
    navigate(`/property/${property.parcel_id}`, { 
      state: { property, fromAppraiser: true } 
    });
  };

  const loadStatistics = async () => {
    const stats = await getStatistics(selectedCounty);
    setStatistics(stats);
  };

  // Property type codes
  const propertyTypes = [
    { code: '001', label: 'Single Family' },
    { code: '002', label: 'Mobile Home' },
    { code: '003', label: 'Multi-Family' },
    { code: '004', label: 'Condominium' },
    { code: '101', label: 'Retail Store' },
    { code: '102', label: 'Office Building' },
    { code: '103', label: 'Industrial' },
    { code: '104', label: 'Warehouse' },
    { code: '201', label: 'Agricultural' },
    { code: '202', label: 'Vacant Land' }
  ];

  return (
    <div className="container mx-auto p-4 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Florida Property Search</h1>
          <p className="text-muted-foreground">
            Search {statistics?.total_properties?.toLocaleString() || '121,477'} properties from Property Appraiser data
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          >
            <SlidersHorizontal className="h-4 w-4 mr-2" />
            {showAdvancedFilters ? 'Hide' : 'Show'} Filters
          </Button>
          <Button
            variant="outline"
            onClick={loadStatistics}
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            Statistics
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="search">
            <Search className="h-4 w-4 mr-2" />
            Search
          </TabsTrigger>
          <TabsTrigger value="top">
            <TrendingUp className="h-4 w-4 mr-2" />
            Top Properties
          </TabsTrigger>
          <TabsTrigger value="counties">
            <MapPin className="h-4 w-4 mr-2" />
            By County
          </TabsTrigger>
          <TabsTrigger value="statistics">
            <Database className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Search Tab */}
        <TabsContent value="search" className="space-y-4">
          <Card>
            <CardContent className="pt-6">
              <div className="grid gap-4">
                {/* Main Search Bar */}
                <div className="flex gap-2">
                  <Input
                    placeholder="Search by address, owner name, or parcel ID..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="flex-1"
                  />
                  <Button onClick={handleSearch} disabled={loading}>
                    {loading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Search className="h-4 w-4" />
                    )}
                    Search
                  </Button>
                </div>

                {/* Filters */}
                {showAdvancedFilters && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Select value={selectedCounty} onValueChange={setSelectedCounty}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select County" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All Counties</SelectItem>
                        {counties.map(county => (
                          <SelectItem 
                            key={county.county_code} 
                            value={county.county_code}
                          >
                            {county.county_name} ({county.property_count?.toLocaleString() || 0})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Select value={propertyType} onValueChange={setPropertyType}>
                      <SelectTrigger>
                        <SelectValue placeholder="Property Type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All Types</SelectItem>
                        {propertyTypes.map(type => (
                          <SelectItem key={type.code} value={type.code}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Input
                      type="number"
                      placeholder="Min Value"
                      value={minValue}
                      onChange={(e) => setMinValue(e.target.value)}
                    />

                    <Input
                      type="number"
                      placeholder="Max Value"
                      value={maxValue}
                      onChange={(e) => setMaxValue(e.target.value)}
                    />
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          {properties.length > 0 && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <p className="text-sm text-muted-foreground">
                  Found {properties.length} properties
                </p>
                <div className="flex gap-2">
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('grid')}
                  >
                    <Grid3X3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setViewMode('list')}
                  >
                    <List className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {viewMode === 'grid' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {properties.map((property) => (
                    <Card 
                      key={property.parcel_id}
                      className="cursor-pointer hover:shadow-lg transition-shadow"
                      onClick={() => handlePropertyClick(property)}
                    >
                      <CardContent className="p-4">
                        <div className="space-y-2">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-semibold text-sm">
                                {property.property_address || 'Address Not Available'}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {property.property_city}, FL {property.property_zip}
                              </p>
                            </div>
                            <Badge variant="secondary">
                              {property.county_name}
                            </Badge>
                          </div>
                          
                          <div className="text-xs space-y-1">
                            <p><span className="font-medium">Owner:</span> {property.owner_name}</p>
                            <p><span className="font-medium">Parcel:</span> {property.parcel_id}</p>
                            {property.year_built > 0 && (
                              <p><span className="font-medium">Year Built:</span> {property.year_built}</p>
                            )}
                          </div>

                          <div className="flex justify-between items-center pt-2 border-t">
                            <div>
                              <p className="text-xs text-muted-foreground">Taxable Value</p>
                              <p className="font-bold text-lg">
                                <DollarSign className="inline h-4 w-4" />
                                {property.taxable_value?.toLocaleString() || 'N/A'}
                              </p>
                            </div>
                            {property.total_sq_ft > 0 && (
                              <div className="text-right">
                                <p className="text-xs text-muted-foreground">Sq Ft</p>
                                <p className="font-semibold">
                                  {property.total_sq_ft?.toLocaleString()}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  {properties.map((property) => (
                    <Card 
                      key={property.parcel_id}
                      className="cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => handlePropertyClick(property)}
                    >
                      <CardContent className="p-4">
                        <div className="flex justify-between items-center">
                          <div className="flex-1">
                            <div className="flex items-center gap-4">
                              <div className="flex-1">
                                <p className="font-semibold">
                                  {property.property_address || 'Address Not Available'}
                                </p>
                                <p className="text-sm text-muted-foreground">
                                  {property.property_city}, FL {property.property_zip} • {property.county_name}
                                </p>
                              </div>
                              <div className="text-right">
                                <p className="text-sm text-muted-foreground">Owner</p>
                                <p className="font-medium">{property.owner_name}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-sm text-muted-foreground">Taxable Value</p>
                                <p className="font-bold text-lg">
                                  ${property.taxable_value?.toLocaleString() || 'N/A'}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {/* Pagination */}
              <div className="flex justify-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                  disabled={currentPage === 0 || loading}
                >
                  Previous
                </Button>
                <span className="flex items-center px-4">
                  Page {currentPage + 1}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={properties.length < pageSize || loading}
                >
                  Next
                </Button>
              </div>
            </div>
          )}

          {error && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <p className="text-red-600">Error: {error}</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Top Properties Tab */}
        <TabsContent value="top">
          <Card>
            <CardHeader>
              <CardTitle>Highest Value Properties</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {properties.map((property, index) => (
                  <div 
                    key={property.parcel_id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                    onClick={() => handlePropertyClick(property)}
                  >
                    <div className="flex items-center gap-4">
                      <div className="text-2xl font-bold text-gray-400">
                        #{index + 1}
                      </div>
                      <div>
                        <p className="font-semibold">
                          {property.property_address || 'Address Not Available'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {property.property_city} • {property.county_name}
                        </p>
                        <p className="text-sm">
                          Owner: {property.owner_name}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold">
                        ${property.taxable_value?.toLocaleString()}
                      </p>
                      {property.total_sq_ft > 0 && (
                        <p className="text-sm text-muted-foreground">
                          {property.total_sq_ft?.toLocaleString()} sq ft
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Counties Tab */}
        <TabsContent value="counties">
          <Card>
            <CardHeader>
              <CardTitle>Properties by County</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {counties.map(county => (
                  <Card 
                    key={county.county_code}
                    className="cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => {
                      setSelectedCounty(county.county_code);
                      setActiveTab('search');
                      handleSearch();
                    }}
                  >
                    <CardContent className="p-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-semibold">{county.county_name}</p>
                          <p className="text-sm text-muted-foreground">
                            Code: {county.county_code}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold">
                            {county.property_count?.toLocaleString() || 0}
                          </p>
                          <p className="text-xs text-muted-foreground">properties</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Statistics Tab */}
        <TabsContent value="statistics">
          <Card>
            <CardHeader>
              <CardTitle>Property Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              {statistics ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Total Properties</p>
                          <p className="text-3xl font-bold">
                            {statistics.total_properties?.toLocaleString()}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Total Value</p>
                          <p className="text-3xl font-bold">
                            ${(statistics.total_value / 1000000000).toFixed(1)}B
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Average Value</p>
                          <p className="text-3xl font-bold">
                            ${statistics.average_value?.toLocaleString()}
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {statistics.by_county && (
                    <div>
                      <h3 className="font-semibold mb-4">By County</h3>
                      <div className="space-y-2">
                        {Object.entries(statistics.by_county).map(([county, stats]: [string, any]) => (
                          <div key={county} className="flex justify-between items-center p-3 border rounded">
                            <span className="font-medium">{county}</span>
                            <div className="flex gap-4">
                              <span className="text-sm">
                                {stats.count?.toLocaleString()} properties
                              </span>
                              <span className="text-sm font-semibold">
                                Avg: ${stats.average_value?.toLocaleString()}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Button onClick={loadStatistics}>
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Load Statistics
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}