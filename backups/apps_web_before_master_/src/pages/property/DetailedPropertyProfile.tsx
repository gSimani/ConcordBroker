import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { api } from '@/api/client';
import { useSalesData, formatSalesForSdfData } from '@/hooks/useSalesData';
import { ComprehensiveSalesHistorySection } from '@/components/property/tabs/ComprehensiveSalesHistorySection';
import {
  MapPin, Home, DollarSign, User, Calendar, Square, Bed, Bath,
  Building, TreePine, Briefcase, FileText, TrendingUp, Info,
  ExternalLink, Mail, Phone, Clock, AlertCircle, CheckCircle,
  Download, Share2, Star, Map, Camera, Calculator, Gavel,
  Shield, Landmark, Receipt, PieChart, BarChart, Activity
} from 'lucide-react';

export function DetailedPropertyProfile() {
  const { parcelId } = useParams();
  const [property, setProperty] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const salesHook = useSalesData((parcelId as string) || null);

  useEffect(() => {
    if (parcelId) {
      fetchPropertyDetails(parcelId);
    }
  }, [parcelId]);

  const fetchPropertyDetails = async (id: string) => {
    try {
      setLoading(true);
      // Try enhanced API first
      try {
        const enhancedResponse = await api.getEnhancedPropertyDetail(id);
        if (enhancedResponse && enhancedResponse.data) {
          setProperty(enhancedResponse.data);
          setLoading(false);
          return;
        }
      } catch (enhancedErr) {
        console.log('Enhanced API not available, falling back to standard API');
      }

      // Fallback to standard API
      const response = await fetch(`/api/properties/${id}`);
      if (!response.ok) throw new Error('Failed to fetch property details');
      const data = await response.json();
      setProperty(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Format functions
  const formatCurrency = (value: number | null | undefined) => {
    if (!value || value === 0) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatNumber = (value: number | null | undefined) => {
    if (!value) return '0';
    return new Intl.NumberFormat('en-US').format(value);
  };

  const formatDate = (date: string | null | undefined) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading property details...</p>
        </div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="container mx-auto p-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Property not found'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl" id={`property-profile-${parcelId}`}>
      {/* Header Section */}
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              {property.overview?.address?.full || property.address || `${property.phy_addr1 || ''} ${property.phy_addr2 || ''}`.trim()}
            </h1>
            <p className="text-lg text-muted-foreground">
              {property.overview?.location?.city || property.city}, {property.overview?.location?.state || property.state || 'FL'} {property.overview?.location?.zip || property.zip_code}
            </p>
            <div className="flex gap-2 mt-2">
              <Badge variant="secondary">
                {property.overview?.property_type || property.property_type || property.use_category || 'Unknown'}
              </Badge>
              <Badge variant="outline">
                Parcel: {property.overview?.parcel_id || property.parcel_id}
              </Badge>
              <Badge variant="outline">
                {property.overview?.location?.county || property.county} County
              </Badge>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Download className="w-4 w-4 mr-1" />
              Export
            </Button>
            <Button variant="outline" size="sm">
              <Star className="w-4 h-4 mr-1" />
              Save
            </Button>
          </div>
        </div>

        {/* Key Metrics Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">Market Value</div>
              <div className="text-2xl font-bold">
                {formatCurrency(property.overview?.values?.market_value || property.values?.market_value || property.just_value)}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">Annual Tax</div>
              <div className="text-2xl font-bold">
                {formatCurrency(property.property_tax?.annual_tax || property.annual_tax || property.tax_amount || 0)}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">Living Area</div>
              <div className="text-2xl font-bold">
                {formatNumber(property.core_property?.characteristics?.living_area || property.characteristics?.living_area || property.living_area)} sq ft
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-sm text-muted-foreground">Year Built</div>
              <div className="text-2xl font-bold">
                {property.core_property?.characteristics?.year_built || property.characteristics?.year_built || property.year_built || 'N/A'}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Detailed Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-5 w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="core">Core Property Info</TabsTrigger>
          <TabsTrigger value="sunbiz">Sunbiz Info</TabsTrigger>
          <TabsTrigger value="tax">Property Tax Info</TabsTrigger>
          <TabsTrigger value="sales">Sales History</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="w-5 h-5" />
                Property Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Basic Information */}
              <div>
                <h3 className="font-semibold mb-3">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Parcel ID</label>
                    <p className="font-medium">{property.overview?.parcel_id || property.parcel_id}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Property Type</label>
                    <p className="font-medium">{property.overview?.property_type || property.property_type || property.use_category || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">County</label>
                    <p className="font-medium">{property.overview?.location?.county || property.county}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Municipality</label>
                    <p className="font-medium">{property.overview?.location?.municipality || property.municipality || property.city || 'Unincorporated'}</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Quick Stats */}
              <div>
                <h3 className="font-semibold mb-3">Quick Statistics</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <DollarSign className="w-8 h-8 mx-auto mb-2 text-green-600" />
                    <p className="text-2xl font-bold">{formatCurrency(property.overview?.values?.market_value || property.values?.market_value || property.just_value)}</p>
                    <p className="text-sm text-muted-foreground">Market Value</p>
                  </div>
                  <div className="text-center">
                    <Square className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                    <p className="text-2xl font-bold">{formatNumber(property.overview?.characteristics?.lot_size || property.characteristics?.lot_size || property.land_sqft)} </p>
                    <p className="text-sm text-muted-foreground">Lot Size (sq ft)</p>
                  </div>
                  <div className="text-center">
                    <Calendar className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                    <p className="text-2xl font-bold">{property.overview?.characteristics?.year_built || property.characteristics?.year_built || property.year_built || 'N/A'}</p>
                    <p className="text-sm text-muted-foreground">Year Built</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sales History Tab */}
        <TabsContent value="sales" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Sales History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {salesHook.isLoading ? (
                <div className="text-center text-sm text-muted-foreground py-6">Loading sales history…</div>
              ) : (
                <ComprehensiveSalesHistorySection
                  salesHistory={(formatSalesForSdfData(salesHook.salesData) || []).map((s: any) => ({
                    sale_date: s.sale_date,
                    sale_price: parseFloat(s.sale_price) || 0,
                    book_page: s.book && s.page ? `${s.book}/${s.page}` : undefined,
                    instrument_type: s.document_type,
                    qualification: s.qualified_sale ? 'Qualified' : 'Unqualified',
                  }))}
                  parcelId={(parcelId as string) || ''}
                  county={(property?.county || property?.overview?.location?.county || 'Florida')}
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Core Property Info Tab */}
        <TabsContent value="core" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building className="w-5 h-5" />
                Core Property Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Property Characteristics */}
              <div>
                <h3 className="font-semibold mb-3">Property Characteristics</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Living Area</label>
                    <p className="font-medium">{formatNumber(property.core_property?.characteristics?.living_area || property.living_area)} sq ft</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Total Area</label>
                    <p className="font-medium">{formatNumber(property.core_property?.characteristics?.total_area || property.total_area || property.gross_area)} sq ft</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Bedrooms</label>
                    <p className="font-medium">{property.core_property?.characteristics?.bedrooms || property.bedrooms || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Bathrooms</label>
                    <p className="font-medium">{property.core_property?.characteristics?.bathrooms || property.bathrooms || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Year Built</label>
                    <p className="font-medium">{property.core_property?.characteristics?.year_built || property.year_built || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Land Square Feet</label>
                    <p className="font-medium">{formatNumber(property.core_property?.characteristics?.lot_size || property.land_sqft)}</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Owner Information */}
              <div>
                <h3 className="font-semibold mb-3">Owner Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-muted-foreground">Owner Name</label>
                    <p className="font-medium">{property.core_property?.owner?.name || property.owner_name || 'N/A'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-muted-foreground">Mailing Address</label>
                    <p className="font-medium">
                      {property.core_property?.owner?.mailing_address || property.owner_address || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Values */}
              <div>
                <h3 className="font-semibold mb-3">Property Values</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-3 bg-muted rounded-lg">
                    <label className="text-sm text-muted-foreground">Just Value</label>
                    <p className="text-xl font-bold">{formatCurrency(property.core_property?.values?.just_value || property.just_value)}</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <label className="text-sm text-muted-foreground">Assessed Value</label>
                    <p className="text-xl font-bold">{formatCurrency(property.core_property?.values?.assessed_value || property.assessed_value)}</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <label className="text-sm text-muted-foreground">Taxable Value</label>
                    <p className="text-xl font-bold">{formatCurrency(property.core_property?.values?.taxable_value || property.taxable_value)}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sunbiz Info Tab */}
        <TabsContent value="sunbiz" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5" />
                Sunbiz Business Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {property.sunbiz_info ? (
                <>
                  <div>
                    <h3 className="font-semibold mb-3">Business Entity Details</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm text-muted-foreground">Entity Name</label>
                        <p className="font-medium">{property.sunbiz_info.entity_name || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm text-muted-foreground">Entity Type</label>
                        <p className="font-medium">{property.sunbiz_info.entity_type || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm text-muted-foreground">Document Number</label>
                        <p className="font-medium">{property.sunbiz_info.document_number || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm text-muted-foreground">Status</label>
                        <p className="font-medium">
                          <Badge variant={property.sunbiz_info.status === 'Active' ? 'default' : 'secondary'}>
                            {property.sunbiz_info.status || 'Unknown'}
                          </Badge>
                        </p>
                      </div>
                      <div>
                        <label className="text-sm text-muted-foreground">Filing Date</label>
                        <p className="font-medium">{formatDate(property.sunbiz_info.filing_date)}</p>
                      </div>
                      <div>
                        <label className="text-sm text-muted-foreground">State of Incorporation</label>
                        <p className="font-medium">{property.sunbiz_info.state_of_incorporation || 'FL'}</p>
                      </div>
                    </div>
                  </div>

                  {property.sunbiz_info.registered_agent && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="font-semibold mb-3">Registered Agent</h3>
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="font-medium">{property.sunbiz_info.registered_agent.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {property.sunbiz_info.registered_agent.address}
                          </p>
                        </div>
                      </div>
                    </>
                  )}

                  {property.sunbiz_info.officers && property.sunbiz_info.officers.length > 0 && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="font-semibold mb-3">Officers</h3>
                        <div className="space-y-2">
                          {property.sunbiz_info.officers.map((officer: any, index: number) => (
                            <div key={index} className="p-3 bg-muted rounded-lg">
                              <p className="font-medium">{officer.name}</p>
                              <p className="text-sm text-muted-foreground">{officer.title}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </>
              ) : (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    No Sunbiz business information found for this property owner.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Property Tax Info Tab */}
        <TabsContent value="tax" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Receipt className="w-5 h-5" />
                Property Tax Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Current Tax Year */}
              <div>
                <h3 className="font-semibold mb-3">Current Tax Assessment (2025)</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-3 bg-muted rounded-lg">
                    <label className="text-sm text-muted-foreground">Annual Tax</label>
                    <p className="text-xl font-bold">{formatCurrency(property.property_tax?.annual_tax || 0)}</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <label className="text-sm text-muted-foreground">Taxable Value</label>
                    <p className="text-xl font-bold">{formatCurrency(property.property_tax?.taxable_value || property.taxable_value)}</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <label className="text-sm text-muted-foreground">Effective Rate</label>
                    <p className="text-xl font-bold">{(property.property_tax?.effective_rate * 100 || 0).toFixed(3)}%</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Exemptions */}
              {property.property_tax?.exemptions && property.property_tax.exemptions.length > 0 && (
                <>
                  <div>
                    <h3 className="font-semibold mb-3">Tax Exemptions</h3>
                    <div className="flex flex-wrap gap-2">
                      {property.property_tax.exemptions.map((exemption: any, index: number) => (
                        <Badge key={index} variant="outline">
                          {exemption.type}: {formatCurrency(exemption.amount)}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Tax Districts */}
              {property.property_tax?.tax_districts && property.property_tax.tax_districts.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-3">Tax Districts & Millage Rates</h3>
                  <div className="space-y-2">
                    {property.property_tax.tax_districts.map((district: any, index: number) => (
                      <div key={index} className="flex justify-between items-center p-3 bg-muted rounded-lg">
                        <div>
                          <p className="font-medium">{district.name}</p>
                          <p className="text-sm text-muted-foreground">{district.type}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-medium">{district.millage_rate} mills</p>
                          <p className="text-sm text-muted-foreground">{formatCurrency(district.tax_amount)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Payment Status */}
              {property.property_tax?.payment_status && (
                <>
                  <Separator />
                  <div>
                    <h3 className="font-semibold mb-3">Payment Status</h3>
                    <div className="p-3 bg-muted rounded-lg">
                      <div className="flex justify-between items-center">
                        <span>Status</span>
                        <Badge variant={property.property_tax.payment_status === 'Paid' ? 'default' : 'destructive'}>
                          {property.property_tax.payment_status}
                        </Badge>
                      </div>
                      {property.property_tax.payment_date && (
                        <div className="flex justify-between items-center mt-2">
                          <span>Payment Date</span>
                          <span>{formatDate(property.property_tax.payment_date)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Footer with Data Source */}
      <div className="mt-8 text-center text-sm text-muted-foreground">
        <p>Data Source: {property._metadata?.source || 'enhanced_property_api'} |
           Production: {property._metadata?.is_production ? 'Yes' : 'No'} |
           Last Updated: {formatDate(property._metadata?.timestamp)}
        </p>
      </div>
    </div>
  );
}

export default DetailedPropertyProfile;
