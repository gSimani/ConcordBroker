import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import '@/styles/elegant-property.css';
import { 
  MapPin, Building, Calendar, DollarSign, TrendingUp, TrendingDown,
  AlertTriangle, CheckCircle2, User, Briefcase, Home, Scale,
  Activity, FileText, Shield, BarChart3, Clock, Phone, Mail,
  TreePine, Ruler, Receipt, Star, Eye, Download, Share2,
  AlertCircle, Info, ChevronRight, ArrowUpRight, ArrowDownRight,
  Banknote, PiggyBank, Landmark, Calculator, Search, RefreshCw
} from 'lucide-react';

// Import custom hooks and components
import { usePropertyData } from '@/hooks/usePropertyData';
import { OverviewTab } from '@/components/property/tabs/OverviewTab';
import { CorePropertyTab } from '@/components/property/tabs/CorePropertyTab';
import { SunbizTab } from '@/components/property/tabs/SunbizTab';
import { TaxesTab } from '@/components/property/tabs/TaxesTab';
import { AnalysisTabSimple } from '@/components/property/tabs/AnalysisTabSimple';
import { PermitTab } from '@/components/property/tabs/PermitTab';
import { ForeclosureTab } from '@/components/property/tabs/ForeclosureTab';
import { SalesTaxDeedTab } from '@/components/property/tabs/SalesTaxDeedTab';
import { TaxLienTab } from '@/components/property/tabs/TaxLienTab';
import { TaxDeedSalesTab } from '@/components/property/tabs/TaxDeedSalesTab';

export default function EnhancedPropertyProfile() {
  const { city, address, folio } = useParams<{ city?: string; address?: string; folio?: string }>();
  const navigate = useNavigate();
  
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Use the custom hook for data fetching - handle both address-based and folio-based URLs
  const { data: propertyData, loading, error, refetch } = usePropertyData(
    folio || address?.replace(/-/g, ' ') || '', 
    city?.replace(/-/g, ' ') || ''
  );

  const refreshData = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <div className="executive-header text-white">
          <div className="px-8 py-12">
            <div className="max-w-7xl mx-auto">
              <div className="animate-pulse space-y-4">
                <div className="h-8 bg-white bg-opacity-20 rounded w-1/2"></div>
                <div className="h-4 bg-white bg-opacity-20 rounded w-1/4"></div>
              </div>
            </div>
          </div>
        </div>
        <div className="flex-1 px-8 py-6 max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-white">
        <div className="executive-header text-white">
          <div className="px-8 py-12">
            <div className="max-w-7xl mx-auto">
              <h1 className="text-3xl elegant-heading text-white mb-2 gold-accent">Error Loading Property</h1>
              <p className="text-lg font-light opacity-90">{error}</p>
            </div>
          </div>
        </div>
        <div className="flex-1 px-8 py-6 max-w-7xl mx-auto">
          <Button onClick={refreshData} className="btn-executive">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry Loading Property
          </Button>
        </div>
      </div>
    );
  }

  if (!propertyData) {
    return (
      <div className="min-h-screen bg-white">
        <div className="executive-header text-white">
          <div className="px-8 py-12">
            <div className="max-w-7xl mx-auto text-center">
              <h1 className="text-3xl elegant-heading text-white mb-2 gold-accent">Property Not Found</h1>
              <p className="text-lg font-light opacity-90">
                {address?.replace(/-/g, ' ')} in {city?.replace(/-/g, ' ')}
              </p>
            </div>
          </div>
        </div>
        <div className="flex-1 px-8 py-6 max-w-7xl mx-auto text-center">
          <Home className="h-16 w-16 mx-auto text-gray-400 mb-4" />
          <Button onClick={() => navigate('/properties')} className="btn-executive">
            <Search className="h-4 w-4 mr-2" />
            Search Properties
          </Button>
        </div>
      </div>
    );
  }

  const { bcpaData, lastSale, investmentScore, opportunities, riskFactors, dataQuality } = propertyData;
  const formattedAddress = address?.replace(/-/g, ' ') || '';
  const formattedCity = city?.replace(/-/g, ' ') || '';

  return (
    <div className="min-h-screen bg-white">
      {/* Executive Header */}
      <div className="executive-header text-white">
        <div className="px-8 py-12">
          <div className="max-w-7xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="animate-elegant"
            >
              <h1 className="text-3xl elegant-heading text-white mb-2 gold-accent">
                {bcpaData?.property_address_street || formattedAddress || 'Property Details'}
              </h1>
              <p className="text-lg font-light opacity-90">
                {bcpaData?.property_address_city || formattedCity || 'Broward County'}, Florida {bcpaData?.property_address_zip || ''}
              </p>
            </motion.div>
            
            <div className="flex items-center justify-between mt-8">
              <div className="flex items-center space-x-4">
                <span className="badge-elegant badge-gold">
                  {bcpaData?.property_type || bcpaData?.property_use_code || 'Property'}
                </span>
                <span className="text-sm font-light opacity-75">
                  Investment Score: {investmentScore}/100
                </span>
                {bcpaData?.parcel_id && (
                  <span className="text-sm font-light opacity-75">
                    Parcel: {bcpaData.parcel_id}
                  </span>
                )}
              </div>
              
              <div className="flex space-x-3">
                <button className="btn-outline-executive text-white border-white hover:bg-white hover:text-navy">
                  <Star className="w-4 h-4 inline mr-2" />
                  <span>Watch</span>
                </button>
                <button 
                  onClick={refreshData}
                  disabled={refreshing}
                  className="btn-outline-executive text-white border-white hover:bg-white hover:text-navy"
                >
                  <RefreshCw className={`w-4 h-4 inline mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Elegant Layout */}
      <div className="flex-1 px-8 py-6 max-w-7xl mx-auto">
        {/* Key Metrics Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8"
        >
          <div className="card-executive">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-light">Market Value</p>
                <p className="text-2xl font-light elegant-text text-navy">
                  {bcpaData?.market_value ? formatCurrency(parseInt(bcpaData.market_value)) : 'N/A'}
                </p>
              </div>
              <Home className="h-8 w-8 text-gold" />
            </div>
          </div>

          <div className="card-executive">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-light">Last Sale</p>
                <p className="text-2xl font-light elegant-text text-navy">
                  {lastSale?.sale_price ? formatCurrency(parseInt(lastSale.sale_price)) : 'N/A'}
                </p>
                {lastSale?.sale_date && (
                  <p className="text-xs text-gray-400 font-light">
                    {new Date(lastSale.sale_date).toLocaleDateString()}
                  </p>
                )}
              </div>
              <DollarSign className="h-8 w-8 text-gold" />
            </div>
          </div>

          <div className="card-executive">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-light">Property Type</p>
                <p className="text-lg font-light elegant-text text-navy">
                  {bcpaData?.property_type || bcpaData?.property_use_code || 'Unknown'}
                </p>
                <p className="text-xs text-gray-400 font-light">
                  Built {bcpaData?.year_built || bcpaData?.eff_year_built || 'Unknown'}
                </p>
              </div>
              <Building className="h-8 w-8 text-gold" />
            </div>
          </div>

          <div className="card-executive">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm font-light">Living Area</p>
                <p className="text-lg font-light elegant-text text-navy">
                  {bcpaData?.living_area ? `${parseInt(bcpaData.living_area).toLocaleString()} sqft` : 'N/A'}
                </p>
                <p className="text-xs text-gray-400 font-light">
                  {bcpaData?.bedrooms || '?'} bed • {bcpaData?.bathrooms || '?'} bath
                </p>
              </div>
              <Ruler className="h-8 w-8 text-gold" />
            </div>
          </div>
        </motion.div>

        {/* Investment Overview Cards */}
        {opportunities.length > 0 && (
          <div className="grid md:grid-cols-1 gap-6 mb-8">
            <div className="card-executive border-l-4 border-gold">
              <h3 className="text-lg elegant-heading text-navy mb-3 flex items-center">
                <CheckCircle2 className="h-5 w-5 mr-2 text-gold" />
                Investment Opportunities
              </h3>
              <ul className="space-y-2">
                {opportunities.map((opp, index) => (
                  <li key={index} className="text-sm elegant-text text-navy-dark bg-gray-light p-2 rounded">
                    {opp}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Executive Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="h-full"
        >
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
            <TabsList className="tabs-executive flex justify-center mb-8 bg-transparent border-0 flex-wrap">
              <TabsTrigger value="overview" className="tab-executive">
                Overview
              </TabsTrigger>
              <TabsTrigger value="core" className="tab-executive">
                Core Property Info
              </TabsTrigger>
              <TabsTrigger value="sunbiz" className="tab-executive">
                Sunbiz Info
              </TabsTrigger>
              <TabsTrigger value="taxes" className="tab-executive">
                Property Tax Info
              </TabsTrigger>
              <TabsTrigger value="permit" className="tab-executive">
                Permit
              </TabsTrigger>
              <TabsTrigger value="foreclosure" className="tab-executive">
                Foreclosure
              </TabsTrigger>
              <TabsTrigger value="salestaxdeed" className="tab-executive">
                Sales Tax Deed
              </TabsTrigger>
              <TabsTrigger value="taxdeedsales" className="tab-executive">
                Tax Deed Sales
              </TabsTrigger>
              <TabsTrigger value="taxlien" className="tab-executive">
                Tax Lien
              </TabsTrigger>
              <TabsTrigger value="analysis" className="tab-executive">
                Analysis
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="mt-0">
              <OverviewTab data={propertyData} />
            </TabsContent>

            <TabsContent value="core" className="mt-0">
              <CorePropertyTab propertyData={propertyData} />
            </TabsContent>

            <TabsContent value="sunbiz" className="mt-0">
              <SunbizTab propertyData={propertyData} />
            </TabsContent>

            <TabsContent value="taxes" className="mt-0">
              <TaxesTab data={propertyData} />
            </TabsContent>

            <TabsContent value="permit" className="mt-0">
              <PermitTab propertyData={propertyData} />
            </TabsContent>

            <TabsContent value="foreclosure" className="mt-0">
              <ForeclosureTab propertyData={propertyData} />
            </TabsContent>

            <TabsContent value="salestaxdeed" className="mt-0">
              <SalesTaxDeedTab propertyData={propertyData} />
            </TabsContent>

            <TabsContent value="taxlien" className="mt-0">
              <TaxLienTab propertyData={propertyData} />
            </TabsContent>

            <TabsContent value="taxdeedsales" className="mt-0">
              <TaxDeedSalesTab parcelNumber={propertyData?.parcel_number || propertyData?.parcel_id || folio || ''} />
            </TabsContent>

            <TabsContent value="analysis" className="mt-0">
              <AnalysisTabSimple data={propertyData} />
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}