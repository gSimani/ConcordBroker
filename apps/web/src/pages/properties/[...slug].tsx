import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { PropertyProfile } from './PropertyProfile';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, ArrowLeft, MapPin, AlertCircle } from 'lucide-react';
import Link from 'next/link';

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
  const router = useRouter();
  const { slug } = router.query;
  
  const [property, setProperty] = useState<PropertyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch property data based on URL structure
  const fetchProperty = async () => {
    if (!slug || !Array.isArray(slug)) return;
    
    setLoading(true);
    setError(null);
    
    try {
      let url = '';
      
      if (slug.length === 1) {
        // Single slug - could be property ID or parcel ID
        const singleParam = slug[0];
        
        if (/^\d+$/.test(singleParam)) {
          if (singleParam.length > 10) {
            // Likely parcel ID
            url = `/api/properties/parcel/${singleParam}`;
          } else {
            // Likely property ID
            url = `/api/properties/${singleParam}`;
          }
        } else {
          // Could be city name for city overview
          router.push(`/properties?city=${singleParam}`);
          return;
        }
      } else if (slug.length === 2) {
        // Two slugs - city and address
        const [citySlug, addressSlug] = slug;
        
        // Convert slugs back to readable format
        const city = citySlug
          .split('-')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
        
        const addressSearch = addressSlug
          .replace(/-/g, ' ')
          .replace(/\b\w/g, l => l.toUpperCase());
        
        url = `/api/properties/address/${encodeURIComponent(addressSearch)}?city=${encodeURIComponent(city)}`;
      } else {
        setError('Invalid property URL format');
        return;
      }
      
      const response = await fetch(url);
      if (!response.ok) {
        if (response.status === 404) {
          setError('Property not found');
        } else {
          setError('Failed to load property');
        }
        return;
      }
      
      const data = await response.json();
      setProperty(data);
      
      // Update browser title with address
      if (data.phy_addr1 && data.phy_city) {
        document.title = `${data.phy_addr1}, ${data.phy_city} - ConcordBroker`;
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
  }, [slug]);

  // Generate breadcrumb
  const generateBreadcrumb = () => {
    if (!property) return null;
    
    return (
      <nav className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
        <Link href="/properties" className="hover:text-blue-600">
          Properties
        </Link>
        <span>/</span>
        {property.phy_city && (
          <>
            <Link 
              href={`/properties?city=${encodeURIComponent(property.phy_city)}`}
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
            <Button variant="ghost" onClick={() => router.back()}>
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
                  <strong>Searching for:</strong> {Array.isArray(slug) ? slug.join(' / ') : slug}
                </div>
                
                <div className="flex justify-center space-x-3">
                  <Button variant="outline" onClick={() => router.push('/properties')}>
                    Browse All Properties
                  </Button>
                  <Button variant="outline" onClick={() => router.back()}>
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
                <Button variant="ghost" onClick={() => router.back()}>
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
        <PropertyProfile 
          parcelId={property.parcel_id}
          data={property}
        />
      </div>
    </div>
  );
}

// Generate static paths for popular properties (optional optimization)
export async function getStaticPaths() {
  return {
    paths: [],
    fallback: 'blocking'
  };
}

// This could be used for static generation if needed
export async function getStaticProps({ params }: { params: { slug: string[] } }) {
  // For now, return props to enable dynamic rendering
  return {
    props: {},
    // Revalidate every hour
    revalidate: 3600
  };
}

// Helper function to generate SEO-friendly slugs
export function createPropertySlug(address: string, city: string): string {
  const addressSlug = address
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, '-')
    .replace(/^-|-$/g, '');
  
  const citySlug = city
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, '-');
  
  return `${citySlug}/${addressSlug}`;
}

// Helper to parse slug back to search terms
export function parsePropertySlug(slug: string[]): {
  city?: string;
  address?: string;
  type: 'address' | 'parcel' | 'id';
} {
  if (slug.length === 1) {
    const param = slug[0];
    if (/^\d{10,}$/.test(param)) {
      return { type: 'parcel' };
    }
    return { type: 'id' };
  }
  
  if (slug.length === 2) {
    const [citySlug, addressSlug] = slug;
    
    const city = citySlug
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
    
    const address = addressSlug
      .replace(/-/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
    
    return { city, address, type: 'address' };
  }
  
  return { type: 'address' };
}