import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useOptimizedSupabase } from '@/hooks/useOptimizedSupabase';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Building,
  MapPin,
  DollarSign,
  RefreshCw,
  Home,
  Briefcase,
  TreePine,
  Factory,
  Wheat,
  Package
} from 'lucide-react';

export default function LivePropertySearch() {
  const navigate = useNavigate();
  const [searchAddress, setSearchAddress] = useState('');
  const [searchCity, setSearchCity] = useState('');
  const [selectedCounty, setSelectedCounty] = useState('BROWARD');
  const [propertyType, setPropertyType] = useState('All Properties');
  const [minPrice, setMinPrice] = useState<number | undefined>();
  const [maxPrice, setMaxPrice] = useState<number | undefined>();

  const {
    properties,
    loading,
    error,
    total,
    fetchOptimized,
    prefetchNext,
    clearCache
  } = useOptimizedSupabase({
    county: selectedCounty,
    limit: 50 // Reduced for faster loading
  });

  const handleSearch = () => {
    fetchOptimized({
      county: selectedCounty,
      city: searchCity || searchAddress,
      propertyType: propertyType !== 'All Properties' ? propertyType : undefined,
      minPrice,
      maxPrice,
      limit: 50,
      offset: 0
    });
  };

  const handlePropertyClick = (parcelId: string) => {
    navigate(`/property/${parcelId}`);
  };

  const getPropertyIcon = (type: string) => {
    switch(type) {
      case 'Residential': return <Home className="w-4 h-4" />;
      case 'Commercial': return <Building className="w-4 h-4" />;
      case 'Industrial': return <Factory className="w-4 h-4" />;
      case 'Agricultural': return <Wheat className="w-4 h-4" />;
      case 'Vacant': return <TreePine className="w-4 h-4" />;
      default: return <Package className="w-4 h-4" />;
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Florida Property Search</h1>
        <p className="text-gray-600">
          Searching {total.toLocaleString()} properties in {selectedCounty} County
        </p>
      </div>

      {/* Search Controls */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search Properties</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* County Selection */}
            <Select value={selectedCounty} onValueChange={setSelectedCounty}>
              <SelectTrigger>
                <SelectValue placeholder="Select County" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BROWARD">Broward</SelectItem>
                <SelectItem value="MIAMI-DADE">Miami-Dade</SelectItem>
                <SelectItem value="PALM BEACH">Palm Beach</SelectItem>
                <SelectItem value="HILLSBOROUGH">Hillsborough</SelectItem>
                <SelectItem value="ORANGE">Orange</SelectItem>
                <SelectItem value="DUVAL">Duval</SelectItem>
                <SelectItem value="PINELLAS">Pinellas</SelectItem>
              </SelectContent>
            </Select>

            {/* Property Type */}
            <Select value={propertyType} onValueChange={setPropertyType}>
              <SelectTrigger>
                <SelectValue placeholder="Property Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="All Properties">All Properties</SelectItem>
                <SelectItem value="Residential">Residential</SelectItem>
                <SelectItem value="Commercial">Commercial</SelectItem>
                <SelectItem value="Industrial">Industrial</SelectItem>
                <SelectItem value="Agricultural">Agricultural</SelectItem>
                <SelectItem value="Vacant">Vacant Land</SelectItem>
              </SelectContent>
            </Select>

            {/* Address Search */}
            <Input
              placeholder="Search by address..."
              value={searchAddress}
              onChange={(e) => setSearchAddress(e.target.value)}
              className="flex-1"
            />

            {/* City Search */}
            <Input
              placeholder="City..."
              value={searchCity}
              onChange={(e) => setSearchCity(e.target.value)}
            />

            {/* Price Range */}
            <Input
              type="number"
              placeholder="Min Price"
              value={minPrice || ''}
              onChange={(e) => setMinPrice(e.target.value ? parseInt(e.target.value) : undefined)}
            />

            <Input
              type="number"
              placeholder="Max Price"
              value={maxPrice || ''}
              onChange={(e) => setMaxPrice(e.target.value ? parseInt(e.target.value) : undefined)}
            />

            {/* Action Buttons */}
            <Button onClick={handleSearch} className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              Search
            </Button>

            <Button onClick={() => {
              clearCache();
              handleSearch();
            }} variant="outline" className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
          </div>

          {/* Quick Actions */}
          <div className="mt-4 flex gap-2">
            <Button size="sm" variant="outline" onClick={() => fetchOptimized({
              county: selectedCounty,
              limit: 50,
              offset: 0
            })}>
              Recent Sales
            </Button>
            <Button size="sm" variant="outline" onClick={() => fetchOptimized({
              county: selectedCounty,
              minPrice: 1000000,
              limit: 50
            })}>
              High Value ($1M+)
            </Button>
            <Button size="sm" variant="outline" onClick={() => fetchOptimized({
              county: selectedCounty,
              minPrice: 5000000,
              limit: 50
            })}>
              Luxury ($5M+)
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
            <p>Loading properties...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
          <p>Error: {error}</p>
        </div>
      )}

      {/* Results */}
      {!loading && !error && properties.length > 0 && (
        <div>
          <div className="mb-4 flex justify-between items-center">
            <p className="text-sm text-gray-600">
              Showing {properties.length} of {total.toLocaleString()} properties
            </p>
            <Badge variant="secondary">
              Live Data from Supabase
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {properties.map((property) => (
              <Card
                key={property.id}
                className="hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => handlePropertyClick(property.parcel_id)}
              >
                <CardContent className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      {getPropertyIcon(property.property_use_desc || 'Residential')}
                      <Badge variant="outline" className="text-xs">
                        {property.property_use_desc || 'Residential'}
                      </Badge>
                    </div>
                    {property.sale_date && (
                      <Badge variant="secondary" className="text-xs">
                        Sold {new Date(property.sale_date).getFullYear()}
                      </Badge>
                    )}
                  </div>

                  <h3 className="font-semibold mb-1">
                    {property.phy_addr1 || 'Address Not Available'}
                  </h3>

                  <div className="flex items-center gap-1 text-sm text-gray-600 mb-2">
                    <MapPin className="w-3 h-3" />
                    <span>
                      {property.phy_city || 'City N/A'}, FL {property.phy_zipcd || ''}
                    </span>
                  </div>

                  <p className="text-sm text-gray-600 mb-3">
                    Owner: {property.owner_name || 'N/A'}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-gray-500">Taxable Value</p>
                      <p className="font-semibold text-green-600">
                        {property.taxable_value ? formatCurrency(property.taxable_value) : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Just Value</p>
                      <p className="font-semibold">
                        {property.just_value ? formatCurrency(property.just_value) : 'N/A'}
                      </p>
                    </div>
                  </div>

                  {property.sale_price && property.sale_price > 0 && (
                    <div className="mt-2 pt-2 border-t">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Last Sale</span>
                        <span className="font-semibold text-blue-600">
                          {formatCurrency(property.sale_price)}
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="mt-3 flex gap-2 text-xs">
                    <Badge variant="outline">
                      Parcel: {property.parcel_id}
                    </Badge>
                    {property.year_built && (
                      <Badge variant="outline">
                        Built: {property.year_built}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Load More */}
          {properties.length < total && (
            <div className="mt-8 text-center">
              <Button
                onClick={() => {
                  const nextOffset = properties.length;
                  fetchOptimized({
                    county: selectedCounty,
                    city: searchCity,
                    propertyType: propertyType !== 'All Properties' ? propertyType : undefined,
                    minPrice,
                    maxPrice,
                    limit: 50,
                    offset: nextOffset
                  });
                  // Prefetch next page for smoother experience
                  prefetchNext(nextOffset, 50);
                }}
                variant="outline"
              >
                Load More Properties
              </Button>
            </div>
          )}
        </div>
      )}

      {/* No Results */}
      {!loading && !error && properties.length === 0 && (
        <Card className="p-12 text-center">
          <Building className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-semibold mb-2">No Properties Found</h3>
          <p className="text-gray-600">
            Try adjusting your search filters or selecting a different county
          </p>
        </Card>
      )}
    </div>
  );
}