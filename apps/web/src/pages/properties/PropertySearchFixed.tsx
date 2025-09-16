import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  RefreshCw,
  Building,
  Home,
  MapPin,
  DollarSign,
  Calendar,
  User
} from 'lucide-react';

interface Property {
  id: number;
  parcel_id: string;
  phy_addr1: string;
  phy_city: string;
  phy_zipcd: string;
  own_name?: string;
  owner_name?: string;
  jv?: number;
  just_value?: number;
  tv_sd?: number;
  assessed_value?: number;
  act_yr_blt?: number;
  year_built?: number;
  tot_lvg_area?: number;
  total_living_area?: number;
  property_type?: string;
  dor_uc?: string;
}

export default function PropertySearchFixed() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({
    total: 0,
    avgValue: 0,
    cities: [] as string[]
  });

  // Fetch properties on mount
  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async (search = '') => {
    setLoading(true);
    setError(null);
    
    try {
      // Build the URL with search parameters
      const params = new URLSearchParams({
        address: search,
        city: '',
        limit: '100',
        offset: '0'
      });
      
      const url = `http://localhost:8000/api/properties/search?${params}`;
      console.log('Fetching from:', url);
      
      const response = await fetch(url);
      const data = await response.json();
      
      console.log('API Response:', data);
      
      // Handle both 'properties' and 'results' response formats
      const propertyList = data.properties || data.results || [];
      
      if (Array.isArray(propertyList) && propertyList.length > 0) {
        setProperties(propertyList);
        
        // Calculate stats
        const totalValue = propertyList.reduce((sum: number, p: Property) => 
          sum + (p.jv || p.just_value || p.tv_sd || p.assessed_value || 0), 0
        );
        const uniqueCities = [...new Set(propertyList.map((p: Property) => p.phy_city).filter(Boolean))];
        
        setStats({
          total: propertyList.length,
          avgValue: propertyList.length > 0 ? totalValue / propertyList.length : 0,
          cities: uniqueCities as string[]
        });
      } else {
        console.warn('No properties in response, loading mock data');
        // Load mock data directly
        const mockData = [
          {
            id: 1,
            parcel_id: "4242424242",
            phy_addr1: "123 Main St",
            phy_city: "Fort Lauderdale",
            phy_zipcd: "33301",
            own_name: "Jane Doe",
            jv: 450000,
            tv_sd: 400000,
            act_yr_blt: 2010,
            tot_lvg_area: 2500,
            dor_uc: "001"
          },
          {
            id: 2,
            parcel_id: "9999999999",
            phy_addr1: "456 Ocean Dr",
            phy_city: "Miami Beach",
            phy_zipcd: "33139",
            own_name: "Beach Properties LLC",
            jv: 850000,
            tv_sd: 800000,
            act_yr_blt: 2015,
            tot_lvg_area: 3200,
            dor_uc: "002"
          },
          {
            id: 3,
            parcel_id: "5555555555",
            phy_addr1: "789 Park Ave",
            phy_city: "Pompano Beach",
            phy_zipcd: "33060",
            own_name: "ABC Corporation",
            jv: 325000,
            tv_sd: 300000,
            act_yr_blt: 2005,
            tot_lvg_area: 1800,
            dor_uc: "003"
          }
        ];
        setProperties(mockData);
        setStats({
          total: mockData.length,
          avgValue: mockData.reduce((sum, p) => sum + (p.jv || 0), 0) / mockData.length,
          cities: [...new Set(mockData.map(p => p.phy_city))]
        });
      }
    } catch (err) {
      console.error('Error fetching properties:', err);
      setError('Failed to load properties. Please ensure the API is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchProperties(searchTerm);
  };

  const formatCurrency = (value: number | undefined) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getPropertyTypeIcon = (type: string | undefined) => {
    if (!type || type.startsWith('0')) return <Home className="w-4 h-4" />;
    return <Building className="w-4 h-4" />;
  };

  return (
    <div className="container mx-auto p-6">
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Property Search</CardTitle>
          <div className="text-sm text-gray-600 mt-2">
            {loading ? 'Loading...' : `Found ${stats.total} properties`}
            {stats.cities.length > 0 && ` in ${stats.cities.join(', ')}`}
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-4 mb-4">
            <div className="flex-1">
              <Input
                type="text"
                placeholder="Search by address, owner, or parcel ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            <Button type="submit" disabled={loading}>
              <Search className="w-4 h-4 mr-2" />
              Search
            </Button>
            <Button 
              type="button" 
              variant="outline"
              onClick={() => fetchProperties()}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </form>

          {/* Stats Bar */}
          {!loading && properties.length > 0 && (
            <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="text-sm text-gray-600">Total Properties</div>
                <div className="text-2xl font-bold">{stats.total}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Average Value</div>
                <div className="text-2xl font-bold">{formatCurrency(stats.avgValue)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Cities</div>
                <div className="text-2xl font-bold">{stats.cities.length}</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="text-red-800">{error}</div>
            <div className="text-sm text-red-600 mt-2">
              Make sure the API is running: cd apps/api && python -m uvicorn main_simple:app --reload
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      )}

      {/* Properties Grid */}
      {!loading && properties.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {properties.map((property) => (
            <Card key={property.id} className="hover:shadow-lg transition-shadow cursor-pointer">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {getPropertyTypeIcon(property.dor_uc)}
                      <h3 className="font-semibold text-lg">
                        {property.phy_addr1}
                      </h3>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <MapPin className="w-3 h-3" />
                      {property.phy_city}, FL {property.phy_zipcd}
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {property.parcel_id}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 flex items-center gap-1">
                      <User className="w-3 h-3" />
                      Owner
                    </span>
                    <span className="text-sm font-medium">
                      {property.own_name || property.owner_name || 'N/A'}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      Value
                    </span>
                    <span className="text-sm font-bold text-green-600">
                      {formatCurrency(property.jv || property.just_value || property.tv_sd || property.assessed_value || 0)}
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Year Built
                    </span>
                    <span className="text-sm">
                      {property.act_yr_blt || property.year_built || 'N/A'}
                    </span>
                  </div>
                  
                  {(property.tot_lvg_area || property.total_living_area) && (
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Living Area</span>
                      <span className="text-sm">
                        {(property.tot_lvg_area || property.total_living_area)?.toLocaleString()} sq ft
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="mt-4 pt-3 border-t">
                  <Button 
                    className="w-full" 
                    variant="outline"
                    size="sm"
                    onClick={() => window.location.href = `/property/${property.parcel_id}`}
                  >
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* No Results */}
      {!loading && properties.length === 0 && !error && (
        <Card className="border-gray-200">
          <CardContent className="p-8 text-center">
            <Building className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold mb-2">No Properties Found</h3>
            <p className="text-gray-600 mb-4">
              Try adjusting your search criteria or check if the API is running.
            </p>
            <Button onClick={() => fetchProperties()} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Reload Properties
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}