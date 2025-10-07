import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  Grid3X3,
  List,
  LayoutDashboard,
  Search,
  Zap,
  Target,
  TrendingUp,
  Settings
} from 'lucide-react';
import EnhancedPropertyMiniCard from './EnhancedPropertyMiniCard';
import PropertyCardGrid from './PropertyCardGrid';
import SearchResultCard from './SearchResultCard';
import InvestmentDashboardCard from './InvestmentDashboardCard';
import { motion } from 'framer-motion';

// Sample property data for demonstration
const sampleProperties = [
  {
    parcel_id: '12345678901',
    phy_addr1: '123 Ocean Drive',
    phy_city: 'Miami Beach',
    phy_state: 'FL',
    phy_zipcd: '33139',
    owner_name: 'Miami Beach Properties LLC',
    market_value: 850000,
    just_value: 850000,
    assessed_value: 780000,
    land_value: 400000,
    building_value: 450000,
    building_sqft: 2200,
    land_sqft: 8712,
    year_built: 1995,
    property_use: '1',
    property_use_desc: 'Single Family Residential',
    county: 'MIAMI-DADE',
    sale_prc1: 720000,
    sale_date1: '2022-03-15',
    homestead: false,
    bedrooms: 4,
    bathrooms: 3
  },
  {
    parcel_id: '98765432109',
    phy_addr1: '456 Commercial Blvd',
    phy_city: 'Fort Lauderdale',
    phy_state: 'FL',
    phy_zipcd: '33304',
    owner_name: 'Broward Investment Group',
    market_value: 1250000,
    just_value: 1250000,
    assessed_value: 1180000,
    land_value: 800000,
    building_value: 450000,
    building_sqft: 5500,
    land_sqft: 21780,
    year_built: 1988,
    property_use: '4',
    property_use_desc: 'Commercial Office',
    county: 'BROWARD',
    sale_prc1: 950000,
    sale_date1: '2021-08-22',
    homestead: false
  },
  {
    parcel_id: '11223344556',
    phy_addr1: '789 Residential Way',
    phy_city: 'Orlando',
    phy_state: 'FL',
    phy_zipcd: '32801',
    owner_name: 'John & Mary Smith',
    market_value: 425000,
    just_value: 425000,
    assessed_value: 385000,
    land_value: 120000,
    building_value: 305000,
    building_sqft: 1800,
    land_sqft: 8712,
    year_built: 2010,
    property_use: '1',
    property_use_desc: 'Single Family Residential',
    county: 'ORANGE',
    sale_prc1: 380000,
    sale_date1: '2020-12-10',
    homestead: true,
    bedrooms: 3,
    bathrooms: 2
  },
  {
    parcel_id: '66778899001',
    phy_addr1: 'No Street Address',
    phy_city: 'Naples',
    phy_state: 'FL',
    phy_zipcd: '34102',
    owner_name: 'Development Trust Holdings',
    market_value: 2200000,
    just_value: 2200000,
    assessed_value: 2100000,
    land_value: 2200000,
    building_value: 0,
    building_sqft: 0,
    land_sqft: 87120, // 2 acres
    year_built: 0,
    property_use: '0',
    property_use_desc: 'Vacant Land',
    county: 'COLLIER',
    homestead: false
  }
];

export function PropertyCardShowcase() {
  const [selectedCard, setSelectedCard] = useState<string>('grid');
  const [watchedProperties, setWatchedProperties] = useState<Set<string>>(new Set());

  const handleToggleWatchlist = (parcelId: string) => {
    setWatchedProperties(prev => {
      const newSet = new Set(prev);
      if (newSet.has(parcelId)) {
        newSet.delete(parcelId);
      } else {
        newSet.add(parcelId);
      }
      return newSet;
    });
  };

  const handlePropertyClick = (property: any) => {
    console.log('Navigating to property:', property.parcel_id);
    // In a real app, this would navigate to the property detail page
  };

  return (
    <div className="space-y-8 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Property Mini Cards Showcase
        </h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          Explore our comprehensive property card components designed for different use cases,
          from search results to investment analysis dashboards.
        </p>
      </div>

      {/* Card Type Selector */}
      <div className="flex justify-center">
        <Tabs value={selectedCard} onValueChange={setSelectedCard} className="w-full max-w-4xl">
          <TabsList className="grid w-full grid-cols-5 mb-8">
            <TabsTrigger value="grid" className="flex items-center gap-2">
              <Grid3X3 className="w-4 h-4" />
              Enhanced Grid
            </TabsTrigger>
            <TabsTrigger value="list" className="flex items-center gap-2">
              <List className="w-4 h-4" />
              Property Grid
            </TabsTrigger>
            <TabsTrigger value="search" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              Search Results
            </TabsTrigger>
            <TabsTrigger value="investment" className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              Investment
            </TabsTrigger>
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </TabsTrigger>
          </TabsList>

          {/* Enhanced Grid Cards */}
          <TabsContent value="grid" className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Enhanced Property Cards</h2>
              <p className="text-gray-600">
                Modern, interactive cards with investment scoring, property details, and quick actions.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sampleProperties.map((property, index) => (
                <motion.div
                  key={property.parcel_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <EnhancedPropertyMiniCard
                    data={property}
                    variant="grid"
                    onClick={() => handlePropertyClick(property)}
                    showInvestmentScore={true}
                    isWatched={watchedProperties.has(property.parcel_id)}
                    onToggleWatchlist={() => handleToggleWatchlist(property.parcel_id)}
                  />
                </motion.div>
              ))}
            </div>
          </TabsContent>

          {/* Property Grid Component */}
          <TabsContent value="list" className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Property Grid Component</h2>
              <p className="text-gray-600">
                Full-featured property grid with filtering, sorting, pagination, and multiple layout options.
              </p>
            </div>

            <PropertyCardGrid
              properties={[...sampleProperties, ...sampleProperties]} // Duplicate for demo
              title="Investment Properties"
              subtitle="Curated selection of high-potential investment opportunities"
              onPropertyClick={handlePropertyClick}
              showInvestmentScore={true}
              allowFiltering={true}
              allowSorting={true}
              defaultLayout="grid"
              pageSize={6}
            />
          </TabsContent>

          {/* Search Result Cards */}
          <TabsContent value="search" className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Search Result Cards</h2>
              <p className="text-gray-600">
                Optimized for search results with highlighted terms, investment metrics, and quick insights.
              </p>
            </div>

            <div className="space-y-4">
              {sampleProperties.map((property, index) => (
                <SearchResultCard
                  key={property.parcel_id}
                  property={property}
                  index={index}
                  onClick={() => handlePropertyClick(property)}
                  onToggleWatchlist={() => handleToggleWatchlist(property.parcel_id)}
                  isWatched={watchedProperties.has(property.parcel_id)}
                  highlightTerms={['Miami', 'Commercial', 'Ocean']}
                />
              ))}
            </div>
          </TabsContent>

          {/* Investment Dashboard Cards */}
          <TabsContent value="investment" className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Investment Analysis Cards</h2>
              <p className="text-gray-600">
                Comprehensive investment analysis with scoring, metrics, opportunities, and risk assessment.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {sampleProperties.slice(0, 2).map((property, index) => (
                <motion.div
                  key={property.parcel_id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.4, delay: index * 0.2 }}
                >
                  <InvestmentDashboardCard
                    property={property}
                    variant="detailed"
                    onClick={() => handlePropertyClick(property)}
                    showFullAnalysis={true}
                  />
                </motion.div>
              ))}
            </div>

            {/* Compact Investment Cards */}
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Compact Investment Cards</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {sampleProperties.slice(2).map((property, index) => (
                  <InvestmentDashboardCard
                    key={property.parcel_id}
                    property={property}
                    variant="compact"
                    onClick={() => handlePropertyClick(property)}
                    showFullAnalysis={false}
                  />
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Dashboard Layout Demo */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Dashboard Layout</h2>
              <p className="text-gray-600">
                Mixed layout demonstration showing how different card types work together in a dashboard.
              </p>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">
                      {sampleProperties.length}
                    </p>
                    <p className="text-sm text-gray-600">Properties</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">78</p>
                    <p className="text-sm text-gray-600">Avg Score</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Zap className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">$1.2M</p>
                    <p className="text-sm text-gray-600">Avg Value</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-4 rounded-lg border border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <Settings className="w-5 h-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">
                      {watchedProperties.size}
                    </p>
                    <p className="text-sm text-gray-600">Watched</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Mixed Layout */}
            <div className="grid grid-cols-12 gap-6">
              {/* Large investment card */}
              <div className="col-span-12 lg:col-span-8">
                <InvestmentDashboardCard
                  property={sampleProperties[0]}
                  variant="detailed"
                  onClick={() => handlePropertyClick(sampleProperties[0])}
                  showFullAnalysis={true}
                />
              </div>

              {/* Compact cards sidebar */}
              <div className="col-span-12 lg:col-span-4 space-y-4">
                {sampleProperties.slice(1, 4).map((property) => (
                  <InvestmentDashboardCard
                    key={property.parcel_id}
                    property={property}
                    variant="compact"
                    onClick={() => handlePropertyClick(property)}
                    showFullAnalysis={false}
                  />
                ))}
              </div>
            </div>

            {/* Enhanced grid at bottom */}
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Recently Viewed</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {sampleProperties.slice(1).map((property) => (
                  <EnhancedPropertyMiniCard
                    key={property.parcel_id}
                    data={property}
                    variant="compact"
                    onClick={() => handlePropertyClick(property)}
                    showInvestmentScore={true}
                    isWatched={watchedProperties.has(property.parcel_id)}
                    onToggleWatchlist={() => handleToggleWatchlist(property.parcel_id)}
                  />
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Feature Highlights */}
      <div className="bg-white rounded-lg p-6 border border-gray-200">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Card Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-3 flex items-center justify-center">
              <Target className="w-6 h-6 text-blue-600" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Investment Scoring</h4>
            <p className="text-sm text-gray-600">
              Real-time investment scoring based on property characteristics, market data, and investment potential.
            </p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg mx-auto mb-3 flex items-center justify-center">
              <Zap className="w-6 h-6 text-green-600" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Interactive Features</h4>
            <p className="text-sm text-gray-600">
              Hover effects, animations, watchlist functionality, and quick actions for seamless user experience.
            </p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg mx-auto mb-3 flex items-center justify-center">
              <LayoutDashboard className="w-6 h-6 text-purple-600" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Flexible Layouts</h4>
            <p className="text-sm text-gray-600">
              Multiple variants (grid, list, compact) and layouts to fit different use cases and screen sizes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export { PropertyCardShowcase };
export default PropertyCardShowcase;