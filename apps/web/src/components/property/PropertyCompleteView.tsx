/**
 * Complete Property View with Matplotlib/Seaborn Visualizations
 * Displays all property data across all tabs with charts
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Home, TrendingUp, DollarSign, FileText, Users, Building,
  MapPin, Calendar, Calculator, BarChart3, AlertCircle,
  RefreshCw, Download, Share2, Heart
} from 'lucide-react';

interface PropertyCompleteData {
  property: any;
  visualizations: {
    overview: { chart: string; data: any };
    sales_history: { chart: string; sales_history: any[] };
    analysis: { chart: string; metrics: any };
    tax_deed: { chart: string; tax_deed_data: any };
    comparables: { chart: string; comparables: any[] };
  };
  summary: {
    address: string;
    owner: string;
    value: number;
    sqft: number;
    bedrooms: number;
    bathrooms: number;
    year_built: number;
  };
}

export default function PropertyCompleteView() {
  const { city, address } = useParams<{ city: string; address: string }>();
  const [data, setData] = useState<PropertyCompleteData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isFavorite, setIsFavorite] = useState(false);

  useEffect(() => {
    fetchPropertyData();
  }, [city, address]);

  const fetchPropertyData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Use the working API on port 8005
      console.log('Using Property Analysis API on port 8005');

      const response = await fetch(`http://localhost:8005/api/property/${city}/${address}`);

      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`);
      }

      const result = await response.json();

      if (result.success && result.data) {
        // Transform the data to match expected format
        const apiData = result.data;

        // Combine property data from all sections
        const propertyData = {
          // Location data
          parcel_id: apiData.property_id,
          phy_addr1: apiData.address.street,
          phy_city: apiData.address.city,
          phy_state: apiData.address.state,
          phy_zipcd: apiData.address.zip,
          county: apiData.overview.property_location.county,

          // Property details
          year_built: apiData.overview.property_details.year_built,
          living_area: apiData.overview.property_details.living_area,
          land_sqft: apiData.overview.property_details.land_size,
          bedrooms: apiData.overview.property_details.bedrooms,
          bathrooms: apiData.overview.property_details.bathrooms,
          stories: apiData.overview.property_details.stories,
          property_use_code: apiData.overview.property_details.property_type,

          // Valuation data
          just_value: apiData.overview.valuation_summary.just_value,
          assessed_value: apiData.overview.valuation_summary.assessed_value,
          taxable_value: apiData.overview.valuation_summary.taxable_value,
          land_value: apiData.overview.valuation_summary.land_value,
          building_value: apiData.overview.valuation_summary.building_value,
          market_value: apiData.overview.valuation_summary.just_value,

          // Sale data
          sale_price: apiData.overview.recent_sale.sale_price,
          sale_date: apiData.overview.recent_sale.sale_date,

          // Tax information
          tax_amount: apiData.tax_information.annual_tax,

          // Owner information
          owner_name: apiData.core_property.ownership.owner_name,

          // Additional features
          pool: false, // Not provided in API, default to false
          subdivision: null, // Not provided in API
          zoning: null, // Not provided in API
        };

        setData({
          property: propertyData,
          visualizations: {
            overview: {
              chart: '', // No charts provided by this API endpoint
              data: apiData.overview
            },
            sales_history: {
              chart: '',
              sales_history: apiData.sales_history || []
            },
            analysis: {
              chart: '',
              metrics: apiData.investment_analysis?.metrics || {}
            },
            tax_deed: {
              chart: '',
              tax_deed_data: apiData.tax_information || {}
            },
            comparables: {
              chart: '',
              comparables: []
            }
          },
          summary: {
            address: apiData.address.formatted,
            owner: apiData.core_property.ownership.owner_name,
            value: apiData.overview.valuation_summary.just_value,
            sqft: apiData.overview.property_details.living_area,
            bedrooms: apiData.overview.property_details.bedrooms,
            bathrooms: apiData.overview.property_details.bathrooms,
            year_built: apiData.overview.property_details.year_built
          }
        });

        console.log('Successfully loaded property data from port 8005');
        return;
      } else {
        throw new Error('API returned invalid data structure');
      }
    } catch (err) {
      console.error('Error fetching property:', err);
      setError(err instanceof Error ? err.message : 'Failed to load property data');
    } finally {
      setLoading(false);
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

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="space-y-6">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Property not found'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header Section */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {data.summary.address}
            </h1>
            <p className="text-lg text-gray-600">
              Owner: {data.summary.owner}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setIsFavorite(!isFavorite)}
            >
              <Heart className={`h-4 w-4 ${isFavorite ? 'fill-red-500 text-red-500' : ''}`} />
            </Button>
            <Button variant="outline" size="icon">
              <Share2 className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon">
              <Download className="h-4 w-4" />
            </Button>
            <Button onClick={fetchPropertyData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Key Metrics Bar */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mt-6">
          <div className="text-center">
            <p className="text-sm text-gray-500">Property Value</p>
            <p className="text-xl font-bold text-blue-600">
              {formatCurrency(data.summary.value)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Living Area</p>
            <p className="text-xl font-bold">
              {formatNumber(data.summary.sqft)} sqft
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Price/Sqft</p>
            <p className="text-xl font-bold">
              ${Math.round(data.summary.value / data.summary.sqft)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Bedrooms</p>
            <p className="text-xl font-bold">{data.summary.bedrooms}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Bathrooms</p>
            <p className="text-xl font-bold">{data.summary.bathrooms}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-500">Year Built</p>
            <p className="text-xl font-bold">{data.summary.year_built}</p>
          </div>
        </div>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-3 lg:grid-cols-6 w-full mb-6">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Home className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="sales" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Sales History
          </TabsTrigger>
          <TabsTrigger value="analysis" className="flex items-center gap-2">
            <Calculator className="h-4 w-4" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="taxdeed" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Tax Deed
          </TabsTrigger>
          <TabsTrigger value="comparables" className="flex items-center gap-2">
            <Building className="h-4 w-4" />
            Comparables
          </TabsTrigger>
          <TabsTrigger value="details" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Details
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Property Overview</CardTitle>
            </CardHeader>
            <CardContent>
              {data.visualizations.overview?.chart ? (
                <img
                  src={`data:image/png;base64,${data.visualizations.overview.chart}`}
                  alt="Property Overview"
                  className="w-full h-auto rounded-lg shadow-md"
                />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold mb-3">Property Information</h3>
                    <dl className="space-y-2">
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Parcel ID:</dt>
                        <dd className="font-medium">{data.property.parcel_id}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Property Type:</dt>
                        <dd className="font-medium">{data.property.property_use_code}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Zoning:</dt>
                        <dd className="font-medium">{data.property.zoning || 'N/A'}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Subdivision:</dt>
                        <dd className="font-medium">{data.property.subdivision || 'N/A'}</dd>
                      </div>
                    </dl>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-3">Valuation Details</h3>
                    <dl className="space-y-2">
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Just Value:</dt>
                        <dd className="font-medium">{formatCurrency(data.property.just_value)}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Assessed Value:</dt>
                        <dd className="font-medium">{formatCurrency(data.property.assessed_value)}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Taxable Value:</dt>
                        <dd className="font-medium">{formatCurrency(data.property.taxable_value)}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-gray-600">Tax Amount:</dt>
                        <dd className="font-medium">{formatCurrency(data.property.tax_amount)}</dd>
                      </div>
                    </dl>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sales History Tab */}
        <TabsContent value="sales">
          <Card>
            <CardHeader>
              <CardTitle>Sales History Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              {data.visualizations.sales_history?.chart ? (
                <img
                  src={`data:image/png;base64,${data.visualizations.sales_history.chart}`}
                  alt="Sales History"
                  className="w-full h-auto rounded-lg shadow-md"
                />
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No sales history visualization available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis">
          <Card>
            <CardHeader>
              <CardTitle>Investment Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              {data.visualizations.analysis?.chart ? (
                <>
                  <img
                    src={`data:image/png;base64,${data.visualizations.analysis.chart}`}
                    alt="Investment Analysis"
                    className="w-full h-auto rounded-lg shadow-md mb-6"
                  />
                  {data.visualizations.analysis.metrics && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">Cap Rate</p>
                        <p className="text-2xl font-bold text-green-600">
                          {data.visualizations.analysis.metrics.cap_rate?.toFixed(2)}%
                        </p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">Monthly Cash Flow</p>
                        <p className="text-2xl font-bold text-blue-600">
                          {formatCurrency(data.visualizations.analysis.metrics.monthly_cash_flow)}
                        </p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">GRM</p>
                        <p className="text-2xl font-bold">
                          {data.visualizations.analysis.metrics.gross_rent_multiplier?.toFixed(2)}
                        </p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">NOI</p>
                        <p className="text-2xl font-bold">
                          {formatCurrency(data.visualizations.analysis.metrics.net_operating_income)}
                        </p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">10-Year ROI</p>
                        <p className="text-2xl font-bold text-purple-600">
                          {data.visualizations.analysis.metrics.total_roi_10_year?.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No investment analysis visualization available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tax Deed Tab */}
        <TabsContent value="taxdeed">
          <Card>
            <CardHeader>
              <CardTitle>Tax Deed & Foreclosure Information</CardTitle>
            </CardHeader>
            <CardContent>
              {data.visualizations.tax_deed?.chart ? (
                <>
                  <img
                    src={`data:image/png;base64,${data.visualizations.tax_deed.chart}`}
                    alt="Tax Deed Analysis"
                    className="w-full h-auto rounded-lg shadow-md"
                  />
                  {data.visualizations.tax_deed.tax_deed_data && (
                    <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <h4 className="font-semibold mb-3">Tax Deed Details</h4>
                      <dl className="grid grid-cols-2 gap-4">
                        <div>
                          <dt className="text-gray-600">Certificate #:</dt>
                          <dd className="font-medium">
                            {data.visualizations.tax_deed.tax_deed_data.certificate_number}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-gray-600">Tax Amount:</dt>
                          <dd className="font-medium">
                            {formatCurrency(data.visualizations.tax_deed.tax_deed_data.tax_amount)}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-gray-600">Interest Rate:</dt>
                          <dd className="font-medium">
                            {data.visualizations.tax_deed.tax_deed_data.interest_rate}%
                          </dd>
                        </div>
                        <div>
                          <dt className="text-gray-600">Minimum Bid:</dt>
                          <dd className="font-medium">
                            {formatCurrency(data.visualizations.tax_deed.tax_deed_data.minimum_bid)}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No tax deed information available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Comparables Tab */}
        <TabsContent value="comparables">
          <Card>
            <CardHeader>
              <CardTitle>Comparable Properties</CardTitle>
            </CardHeader>
            <CardContent>
              {data.visualizations.comparables?.chart ? (
                <img
                  src={`data:image/png;base64,${data.visualizations.comparables.chart}`}
                  alt="Comparable Properties"
                  className="w-full h-auto rounded-lg shadow-md"
                />
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No comparable properties visualization available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Details Tab */}
        <TabsContent value="details">
          <Card>
            <CardHeader>
              <CardTitle>Complete Property Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    Location Details
                  </h3>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Address:</dt>
                      <dd className="font-medium">{data.property.phy_addr1}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">City:</dt>
                      <dd className="font-medium">{data.property.phy_city}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">State:</dt>
                      <dd className="font-medium">{data.property.phy_state}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">ZIP:</dt>
                      <dd className="font-medium">{data.property.phy_zipcd}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">County:</dt>
                      <dd className="font-medium">{data.property.county || 'BROWARD'}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <Building className="h-4 w-4" />
                    Building Details
                  </h3>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Living Area:</dt>
                      <dd className="font-medium">{formatNumber(data.property.living_area)} sqft</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Land Size:</dt>
                      <dd className="font-medium">{formatNumber(data.property.land_sqft)} sqft</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Bedrooms:</dt>
                      <dd className="font-medium">{data.property.bedrooms}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Bathrooms:</dt>
                      <dd className="font-medium">{data.property.bathrooms}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Pool:</dt>
                      <dd className="font-medium">
                        {data.property.pool ? (
                          <Badge variant="default">Yes</Badge>
                        ) : (
                          <Badge variant="secondary">No</Badge>
                        )}
                      </dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Financial Details
                  </h3>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Land Value:</dt>
                      <dd className="font-medium">{formatCurrency(data.property.land_value)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Building Value:</dt>
                      <dd className="font-medium">{formatCurrency(data.property.building_value)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Market Value:</dt>
                      <dd className="font-medium">{formatCurrency(data.property.market_value)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Last Sale:</dt>
                      <dd className="font-medium">{formatCurrency(data.property.sale_price)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-600">Sale Date:</dt>
                      <dd className="font-medium">{data.property.sale_date || 'N/A'}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Alert for sample data */}
      {error && (
        <Alert className="mt-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}