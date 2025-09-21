import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Home, MapPin, DollarSign, TrendingUp, Calendar, Building,
  Users, FileText, AlertTriangle, Star, ArrowLeft, RefreshCw,
  Bed, Bath, Ruler, TreePine, Receipt, Shield, BarChart3
} from 'lucide-react';
import axios from 'axios';

interface PropertyData {
  id: string;
  parcel_id: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  owner: string;
  propertyType: string;
  yearBuilt: number;
  bedrooms: number;
  bathrooms: number;
  buildingSqFt: number;
  landSqFt: number;
  marketValue: number;
  assessedValue: number;
  taxableValue: number;
  landValue: number;
  buildingValue: number;
  investmentScore: number;
  capRate: number;
  pricePerSqFt: number;
  county: string;
  subdivision: string;
  homesteadExemption: boolean;
  taxAmount: number;
  lastSalePrice: number;
  lastSaleDate: string;
}

export default function SimplePropertyPage() {
  const { city, address } = useParams<{ city: string; address: string }>();
  const navigate = useNavigate();
  const [property, setProperty] = useState<PropertyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProperty = async () => {
      if (!city || !address) {
        setError('Invalid URL parameters');
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Convert URL slugs to search terms
        const cityName = city.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        const addressSearch = address.replace(/-/g, ' ').toUpperCase();

        console.log('Searching for:', { addressSearch, cityName });

        const response = await axios.get('http://localhost:8000/api/properties/search', {
          params: {
            address: addressSearch,
            city: cityName,
            limit: 1
          }
        });

        console.log('API Response:', response.data);

        if (response.data.success && response.data.properties && response.data.properties.length > 0) {
          const prop = response.data.properties[0];
          setProperty(prop);

          // Update page title
          document.title = `${prop.address}, ${prop.city} - ConcordBroker`;
        } else {
          setError('Property not found');
        }
      } catch (err: any) {
        console.error('Error fetching property:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to load property');
      } finally {
        setLoading(false);
      }
    };

    fetchProperty();
  }, [city, address]);

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

          <Alert>
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>
              {error || 'Property not found'}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => navigate(-1)}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div className="text-sm text-gray-500">
              {property.county} County, {property.state}
            </div>
          </div>
        </div>
      </div>

      {/* Property Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Home className="w-6 h-6 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">{property.address}</h1>
                {property.homesteadExemption && (
                  <Badge variant="secondary" className="bg-green-100 text-green-700">
                    <Shield className="w-3 h-3 mr-1" />
                    Homestead
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-4 text-gray-600">
                <div className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  <span>{property.city}, {property.state} {property.zipCode}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>Built {property.yearBuilt}</span>
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                ${property.marketValue?.toLocaleString()}
              </div>
              <div className="text-sm text-gray-500">Market Value</div>
              {property.investmentScore && (
                <div className="flex items-center gap-1 mt-2">
                  <Star className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium">
                    {property.investmentScore}/100 Investment Score
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Property Details Tabs */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="financial">Financial</TabsTrigger>
            <TabsTrigger value="owner">Owner</TabsTrigger>
            <TabsTrigger value="taxes">Taxes</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3">
                    <Bed className="w-5 h-5 text-blue-600" />
                    <div>
                      <div className="text-2xl font-bold">{property.bedrooms}</div>
                      <div className="text-sm text-gray-600">Bedrooms</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3">
                    <Bath className="w-5 h-5 text-blue-600" />
                    <div>
                      <div className="text-2xl font-bold">{property.bathrooms}</div>
                      <div className="text-sm text-gray-600">Bathrooms</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3">
                    <Ruler className="w-5 h-5 text-blue-600" />
                    <div>
                      <div className="text-2xl font-bold">{property.buildingSqFt?.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Building Sq Ft</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3">
                    <TreePine className="w-5 h-5 text-blue-600" />
                    <div>
                      <div className="text-2xl font-bold">{property.landSqFt?.toLocaleString()}</div>
                      <div className="text-sm text-gray-600">Land Sq Ft</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="details" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Property Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Property Type</label>
                    <div className="text-lg">{property.propertyType}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Year Built</label>
                    <div className="text-lg">{property.yearBuilt}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Subdivision</label>
                    <div className="text-lg">{property.subdivision || 'N/A'}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Parcel ID</label>
                    <div className="text-lg font-mono">{property.parcel_id}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="financial" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Property Values</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Market Value</span>
                      <span className="font-semibold">${property.marketValue?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Assessed Value</span>
                      <span>${property.assessedValue?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Land Value</span>
                      <span>${property.landValue?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Building Value</span>
                      <span>${property.buildingValue?.toLocaleString()}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Investment Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Price per Sq Ft</span>
                      <span className="font-semibold">${property.pricePerSqFt?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cap Rate</span>
                      <span>{property.capRate?.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Investment Score</span>
                      <span>{property.investmentScore}/100</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="owner" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Owner Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Owner Name</label>
                    <div className="text-lg">{property.owner}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Homestead Exemption</label>
                    <div className="text-lg">
                      {property.homesteadExemption ? (
                        <Badge className="bg-green-100 text-green-700">Yes</Badge>
                      ) : (
                        <Badge variant="secondary">No</Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="taxes" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Tax Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Taxable Value</span>
                    <span className="font-semibold">${property.taxableValue?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Annual Tax Amount</span>
                    <span className="font-semibold">${property.taxAmount?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tax Rate (Estimated)</span>
                    <span>2.0%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analysis" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Investment Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <h4 className="font-semibold mb-2">Investment Score: {property.investmentScore}/100</h4>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${property.investmentScore}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium text-green-700 mb-2">Opportunities</h5>
                      <ul className="text-sm space-y-1">
                        <li>• Good location in {property.city}</li>
                        <li>• Decent price per square foot</li>
                        <li>• Potential for appreciation</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-red-700 mb-2">Risk Factors</h5>
                      <ul className="text-sm space-y-1">
                        <li>• Property age: {new Date().getFullYear() - property.yearBuilt} years</li>
                        <li>• Market conditions</li>
                        <li>• Local regulations</li>
                      </ul>
                    </div>
                  </div>

                  {property.lastSalePrice && (
                    <div>
                      <h5 className="font-medium mb-2">Sales History</h5>
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="flex justify-between">
                          <span>Last Sale</span>
                          <span>${property.lastSalePrice?.toLocaleString()} on {property.lastSaleDate}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}