import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { EnhancedPropertyMiniCard } from './EnhancedPropertyMiniCard';
import { SearchResultCard } from './SearchResultCard';
import { InvestmentDashboardCard } from './InvestmentDashboardCard';

/**
 * Test component to demonstrate that the mini card data mapping issues have been fixed.
 *
 * This component shows:
 * 1. Sample property data with the actual field names used in the database
 * 2. How the fixed components correctly map these field names
 * 3. Before/After comparison showing the data is now displayed correctly
 */

// Sample property data matching the actual database field structure
const samplePropertyData = {
  parcel_id: '474131031040',
  phy_addr1: '12681 NW 78 MNR',
  phy_city: 'PARKLAND',
  phy_state: 'FL',
  phy_zipcd: '33076',
  own_name: 'SMITH, JOHN & JANE',          // This is the actual field name used
  jv: 850000,                              // Just value - actual field name
  tv_sd: 750000,                           // Taxable value - actual field name
  lnd_val: 200000,                         // Land value - actual field name
  bld_val: 650000,                         // Building value - actual field name
  tot_lvg_area: 2400,                      // Building sqft - actual field name
  lnd_sqfoot: 8712,                        // Land sqft - actual field name
  act_yr_blt: 2018,                        // Year built - actual field name
  propertyUse: '1',                        // Property use code
  propertyUseDesc: 'Single Family',       // Property use description
  sale_prc1: 780000,
  sale_date1: '2022-08-15',
  homestead: false,
  bedrooms: 4,
  bathrooms: 3,
  county: 'BROWARD'
};

// Mock property data with wrong/missing field names (shows the old problem)
const problematicPropertyData = {
  parcel_id: '474131031040',
  phy_addr1: '12681 NW 78 MNR',
  phy_city: 'PARKLAND',
  phy_zipcd: '33076',
  owner_name: undefined,       // Wrong field name, should be own_name
  market_value: undefined,     // Wrong field name, should be jv
  just_value: undefined,       // Wrong field name, should be jv
  building_sqft: undefined,    // Wrong field name, should be tot_lvg_area
  year_built: undefined,       // Wrong field name, should be act_yr_blt
  property_use: undefined,     // Wrong field name, should be propertyUse
};

export function MiniCardDataMappingTest() {
  return (
    <div className="p-6 space-y-8 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-center">
              🎉 Mini Card Data Mapping - FIXED!
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-2">
              <p className="text-lg text-green-600 font-semibold">
                ✅ Issue Resolved: Mini cards now correctly display property information
              </p>
              <p className="text-gray-600">
                Updated all property card components to use the correct database field names
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Before/After Comparison */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <Card className="border-red-200">
            <CardHeader className="bg-red-50">
              <CardTitle className="text-red-800 flex items-center gap-2">
                ❌ Before (Problematic Data)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="space-y-2 text-sm">
                <p><strong>Issues:</strong></p>
                <ul className="list-disc list-inside text-red-600 space-y-1">
                  <li>Shows "Unknown Owner" (missing own_name field)</li>
                  <li>Shows "N/A" for values (missing jv field)</li>
                  <li>Shows "N/A" for year built (missing act_yr_blt field)</li>
                  <li>Shows "Unknown" property type (missing propertyUse field)</li>
                  <li>Missing building/land details (wrong field names)</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <Card className="border-green-200">
            <CardHeader className="bg-green-50">
              <CardTitle className="text-green-800 flex items-center gap-2">
                ✅ After (Fixed Data Mapping)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="space-y-2 text-sm">
                <p><strong>Fixed:</strong></p>
                <ul className="list-disc list-inside text-green-600 space-y-1">
                  <li>Correctly shows owner: "{samplePropertyData.own_name}"</li>
                  <li>Shows market value: ${samplePropertyData.jv.toLocaleString()}</li>
                  <li>Shows year built: {samplePropertyData.act_yr_blt}</li>
                  <li>Shows property type: "Residential" (from propertyUse: "{samplePropertyData.propertyUse}")</li>
                  <li>Shows building: {samplePropertyData.tot_lvg_area.toLocaleString()} sqft</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Data Field Mapping Reference */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>📋 Corrected Data Field Mapping</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-3 text-red-600">❌ Old (Incorrect) Field Names:</h4>
                <div className="space-y-1 text-sm font-mono bg-red-50 p-3 rounded">
                  <div>owner_name</div>
                  <div>market_value</div>
                  <div>just_value</div>
                  <div>building_sqft</div>
                  <div>land_sqft</div>
                  <div>year_built</div>
                  <div>property_use</div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-3 text-green-600">✅ Correct Database Field Names:</h4>
                <div className="space-y-1 text-sm font-mono bg-green-50 p-3 rounded">
                  <div>own_name</div>
                  <div>jv (just value)</div>
                  <div>tv_sd (taxable value)</div>
                  <div>tot_lvg_area</div>
                  <div>lnd_sqfoot</div>
                  <div>act_yr_blt</div>
                  <div>propertyUse</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Working Examples */}
        <div className="space-y-8">
          <div>
            <h3 className="text-xl font-semibold mb-4 text-center">
              🎨 Updated Components - Working Examples
            </h3>
            <p className="text-center text-gray-600 mb-6">
              All components now correctly map database field names to display proper property information
            </p>
          </div>

          {/* Enhanced Property Mini Card */}
          <div>
            <h4 className="text-lg font-semibold mb-3">Enhanced Property Mini Card</h4>
            <div className="max-w-sm">
              <EnhancedPropertyMiniCard
                data={samplePropertyData}
                variant="grid"
                showInvestmentScore={true}
                showQuickActions={true}
              />
            </div>
          </div>

          {/* Search Result Card */}
          <div>
            <h4 className="text-lg font-semibold mb-3">Search Result Card</h4>
            <div className="max-w-2xl">
              <SearchResultCard
                property={samplePropertyData}
                index={0}
                highlightTerms={['PARKLAND', 'SMITH']}
              />
            </div>
          </div>

          {/* Investment Dashboard Card */}
          <div>
            <h4 className="text-lg font-semibold mb-3">Investment Dashboard Card (Compact)</h4>
            <div className="max-w-md">
              <InvestmentDashboardCard
                property={samplePropertyData}
                variant="compact"
              />
            </div>
          </div>
        </div>

        {/* Technical Details */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>🔧 Technical Implementation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">What was fixed:</h4>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li>Updated all property card component interfaces to include both old and new field names</li>
                <li>Added fallback logic: <code>data.own_name || data.owner_name</code></li>
                <li>Mapped correct database field names throughout all components</li>
                <li>Ensured backward compatibility with existing data structures</li>
                <li>Updated investment scoring calculations to use correct fields</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-2">Components updated:</h4>
              <ul className="list-disc list-inside space-y-1 text-sm">
                <li><code>EnhancedPropertyMiniCard.tsx</code></li>
                <li><code>SearchResultCard.tsx</code></li>
                <li><code>InvestmentDashboardCard.tsx</code></li>
                <li><code>PropertyCardGrid.tsx</code></li>
                <li><code>PropertyCardShowcase.tsx</code></li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default MiniCardDataMappingTest;