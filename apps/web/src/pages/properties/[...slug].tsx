import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PropertyCompleteView from '@/components/property/PropertyCompleteView';
import EnhancedPropertyProfile from '../property/EnhancedPropertyProfile';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, ArrowLeft, MapPin, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * Dynamic property page with address-based routing
 * Routes:
 * /properties/fort-lauderdale/123-main-st
 * /properties/parcel/1234567890123
 * /properties/12345 (property ID)
 */

interface PropertyData {
  id: number;
  parcel_id: string;
  phy_addr1: string;
  phy_city: string;
  phy_zipcd: string;
  own_name: string;
  property_type: string;
  jv: number;
  tv_sd: number;
  lnd_val: number;
  tot_lvg_area: number;
  lnd_sqfoot: number;
  act_yr_blt: number;
  dor_uc: string;
  // ... all other NAL fields
}

export default function PropertyPage() {
  const navigate = useNavigate();
  const params = useParams();

  // Check if we have city and address params for complete view
  if (params.city && params.address) {
    return <PropertyCompleteView />;
  }

  const [property, setProperty] = useState<PropertyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch property data based on URL structure
  const fetchProperty = async () => {
    console.log('fetchProperty called with params:', params);
    console.log('params.city:', params.city, 'params.address:', params.address);
    setLoading(true);
    setError(null);
    
    try {
      let url = '';
      
      // Check if we have city and address params (for /properties/:city/:address route)
      if (params.city && params.address) {
        // Two params - city and address - use search API
        const citySlug = params.city;
        const addressSlug = params.address;
        console.log('Using city/address route:', citySlug, addressSlug);
        
        // Convert slugs back to readable format
        const city = citySlug
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
        
        const addressSearch = addressSlug
          .replace(/-/g, ' ')
          .replace(/\b\w/g, l => l.toUpperCase());
        
        // Use the working search endpoint
        url = `http://localhost:8000/api/properties/search?address=${encodeURIComponent(addressSearch)}&city=${encodeURIComponent(city)}&limit=1`;
        console.log('API URL:', url);
      } else if (params.slug) {
        // Single param - could be property ID or parcel ID
        const singleParam = params.slug;

        if (/^\d+$/.test(singleParam)) {
          if (singleParam.length > 10) {
            // Likely parcel ID - search by parcel ID
            url = `http://localhost:8000/api/properties/search?q=${singleParam}&limit=1`;
          } else {
            // Likely property ID - search by ID (will need to handle differently)
            // For now, treat as a general search
            url = `http://localhost:8000/api/properties/search?q=${singleParam}&limit=1`;
          }
        } else {
          // Could be city name for city overview
          navigate(`/properties?city=${singleParam}`);
          return;
        }
      } else {
        setError('Invalid property URL format');
        return;
      }
      
      console.log('Fetching from URL:', url);
      const response = await fetch(url);
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        if (response.status === 404) {
          setError('Property not found');
        } else {
          setError('Failed to load property');
        }
        return;
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      
      // Handle different response formats based on URL type
      let propertyData;
      if (url.includes('/search?')) {
        // Search endpoint returns {properties: [...], total, ...}
        if (data.properties && data.properties.length > 0) {
          propertyData = data.properties[0]; // Take the first (most relevant) result

          // Transform data structure to match PropertyProfile expectations
          const transformedData = {
            id: propertyData.id,
            parcel_id: propertyData.parcel_id,
            phy_addr1: propertyData.property_address || propertyData.phy_addr1,
            phy_city: propertyData.property_city || propertyData.phy_city,
            phy_zipcd: propertyData.property_zip || propertyData.phy_zipcd,
            phy_state: 'FL',
            own_name: propertyData.owner_name || propertyData.own_name,
            own_addr1: propertyData.owner_address || propertyData.own_addr1,
            dor_uc: propertyData.property_use_code || propertyData.dor_uc,
            jv: propertyData.just_value || propertyData.jv,
            tv_sd: propertyData.taxable_value || propertyData.tv_sd,
            lnd_val: propertyData.land_value || propertyData.lnd_val,
            tot_lvg_area: propertyData.living_area || propertyData.tot_lvg_area,
            lnd_sqfoot: propertyData.total_sq_ft || propertyData.lnd_sqfoot,
            act_yr_blt: propertyData.year_built || propertyData.act_yr_blt,
            bedroom_cnt: propertyData.bedrooms || propertyData.bedroom_cnt,
            bathroom_cnt: propertyData.bathrooms || propertyData.bathroom_cnt
          };

          setProperty(transformedData as unknown as PropertyData);
          propertyData = transformedData; // For browser title update
        } else {
          setError('Property not found');
          return;
        }
      } else {
        // Direct property endpoints return the property object directly
        propertyData = data;
        setProperty(data);
      }

      // Update browser title with address
      if (propertyData.phy_addr1 && propertyData.phy_city) {
        document.title = `${propertyData.phy_addr1}, ${propertyData.phy_city} - ConcordBroker`;
      }
      
    } catch (err) {
      console.error('Error fetching property:', err);
      setError('Failed to load property data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProperty();
  }, [params.city, params.address, params.slug]);

  // Generate breadcrumb
  const generateBreadcrumb = () => {
    if (!property) return null;
    
    return (
      <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
        <Link to="/properties" className="hover:text-blue-600">
          Properties
        </Link>
        <span>/</span>
        {property.phy_city && (
          <>
            <Link 
              to={`/properties?city=${encodeURIComponent(property.phy_city)}`}
              className="hover:text-blue-600"
            >
              {property.phy_city}
            </Link>
            <span>/</span>
          </>
        )}
        <span className="font-medium text-gray-900">
          {property.phy_addr1 || property.parcel_id}
        </span>
      </nav>
    );
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <h2 className="text-lg font-semibold mb-2">Loading Property</h2>
          <p className="text-gray-600">Fetching property details...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !property) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="mb-6">
            <Button variant="ghost" onClick={() => navigate(-1)}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Search
            </Button>
          </div>
          
          <Card>
            <CardContent className="text-center py-12">
              <AlertCircle className="w-16 h-16 mx-auto mb-4 text-gray-400" />
              <h2 className="text-2xl font-bold mb-4">Property Not Found</h2>
              <p className="text-gray-600 mb-6">
                {error || 'The property you\'re looking for doesn\'t exist or may have been removed.'}
              </p>
              
              <div className="space-y-3">
                <div className="text-sm text-gray-500">
                  <strong>Searching for:</strong> {params.city && params.address ? `${params.city} / ${params.address}` : params.slug}
                </div>
                
                <div className="flex justify-center space-x-3">
                  <Button variant="outline" onClick={() => navigate('/properties')}>
                    Browse All Properties
                  </Button>
                  <Button variant="outline" onClick={() => navigate(-1)}>
                    Go Back
                  </Button>
                </div>
              </div>
              
              {/* Suggestions */}
              <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                <h3 className="font-semibold mb-2">Suggestions:</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Check the address spelling</li>
                  <li>• Try searching by parcel ID</li>
                  <li>• Use the main search page</li>
                  <li>• Browse by city or ZIP code</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Success state - render property profile
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-full">
        {/* Back Navigation */}
        <div className="bg-white border-b px-6 py-3">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Button variant="ghost" onClick={() => navigate(-1)}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                {generateBreadcrumb()}
              </div>
              
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <MapPin className="w-4 h-4" />
                <span>Broward County, FL</span>
              </div>
            </div>
          </div>
        </div>

        {/* Property Profile Component */}
        <EnhancedPropertyProfile 
          parcelId={property.parcel_id}
          data={property}
        />
      </div>
    </div>
  );
}

