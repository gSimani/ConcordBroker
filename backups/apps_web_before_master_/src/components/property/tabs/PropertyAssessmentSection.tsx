import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Building, MapPin, User, Hash, Home, Ruler, ExternalLink, Info, CheckCircle, Star } from 'lucide-react';
import { getUseCodeName, getUseCodeDescription } from '@/lib/useCodeMapping';

interface PropertyAssessmentSectionProps {
  bcpaData: any;
  propertyData: any;
  buildingData?: any[];
  extraFeatures?: any[];
  assessmentData?: any; // Multi-year assessment data
}

// Helper function to format square feet - show zero as valid, null/undefined as dash
const formatSqFt = (value: any): string => {
  if (value === null || value === undefined || value === '') return '-';
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) return '-';
  return `${numValue.toLocaleString()} Sq.Ft`;
};

// Helper function to format currency - show zero as valid, null/undefined as dash
const formatCurrency = (value: any): string => {
  if (value === null || value === undefined || value === '') return '-';
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) return '-';
  return `$${numValue.toLocaleString()}`;
};

export function PropertyAssessmentSection({ bcpaData, propertyData, buildingData, extraFeatures, assessmentData }: PropertyAssessmentSectionProps) {
  // Use propertyData._raw if available for direct Supabase fields
  const rawData = propertyData?._raw || propertyData || {};
  const values = propertyData?.values || {};
  const characteristics = propertyData?.characteristics || {};

  console.log('PropertyAssessmentSection rendering with data:', { bcpaData, propertyData, rawData, buildingData, extraFeatures, assessmentData });
  console.log('PropertyAssessmentSection - Key real data check:', {
    parcel_id: rawData?.parcel_id,
    owner_name: rawData?.owner_name,
    phy_addr1: rawData?.phy_addr1,
    land_value: rawData?.land_value || values?.land_value,
    building_value: rawData?.building_value || values?.building_value,
    just_value: rawData?.just_value || values?.market_value,
    assessed_value: rawData?.assessed_value || values?.assessed_value,
    year_built: rawData?.year_built || characteristics?.year_built,
    total_living_area: rawData?.total_living_area || characteristics?.living_area
  });
  const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();
  const currentYear = new Date().getFullYear();

  // Get subdivision name
  const subdivision = bcpaData?.subdivision || propertyData?.subdivision || propertyData?.sub_division || '';

  // Get building sketch URL based on county
  const getBuildingSketchUrl = () => {
    const parcelId = bcpaData?.parcel_id || propertyData?.parcel_id;
    if (!parcelId) return null;

    if (county === 'MIAMI-DADE') {
      return `https://www.miamidadepa.gov/pa/property_sketches.asp?parcel=${parcelId}`;
    } else if (county === 'BROWARD') {
      return `https://web.bcpa.net/BcpaClient/#/Property-Search/Result/${parcelId}`;
    } else if (county === 'PALM-BEACH' || county === 'PALM BEACH') {
      return `https://www.pbcgov.org/papa/Asps/PropertyDetail/PropertySketch.aspx?parcel=${parcelId}`;
    }
    return null;
  };

  const sketchUrl = getBuildingSketchUrl();

  // Check if property data has been enhanced with NAP or NAL data
  const isNAPEnhanced = rawData?.data_source === 'NAP_Enhanced';
  const isNALEnhanced = rawData?.data_source === 'NAL_Enhanced';
  const isRecentlyUpdated = rawData?.import_date && new Date(rawData.import_date) > new Date('2025-09-26');

  // Check if we have comprehensive ownership data (indicator of NAP enhancement)
  const hasEnhancedOwnerData = rawData?.owner_name && rawData?.owner_addr1 && rawData?.owner_city && rawData?.owner_state;

  // Check if we have enhanced property address data
  const hasEnhancedAddressData = rawData?.phy_addr1 && rawData?.phy_city && rawData?.phy_zipcd;

  // Check if we have enhanced valuation data
  const hasEnhancedValuationData = rawData?.just_value && rawData?.assessed_value && rawData?.taxable_value;

  // Check if we have enhanced property characteristics (NAL specific)
  const hasEnhancedPropertyData = rawData?.year_built && (rawData?.total_living_area || rawData?.land_sqft);

  const isEnhanced = isNAPEnhanced || isNALEnhanced || isRecentlyUpdated ||
                    (hasEnhancedOwnerData && hasEnhancedAddressData && hasEnhancedValuationData);

  // Determine enhancement type for badge text
  const getEnhancementType = () => {
    if (isNALEnhanced) return 'NAL Enhanced Data';
    if (isNAPEnhanced) return 'NAP Enhanced Data';
    if (isRecentlyUpdated) return 'Recently Updated Data';
    if (hasEnhancedPropertyData) return 'Enhanced Data';
    return 'Enhanced Data';
  };

  return (
    <Card className="elegant-card">
      <div className="p-6">
        <h3 className="text-lg font-semibold text-navy mb-4 flex items-center justify-between">
          <div className="flex items-center">
            <Building className="w-5 h-5 mr-2 text-gold" />
            Property Assessment Values
          </div>
          {isEnhanced && (
            <Badge variant="secondary" className="bg-emerald-50 text-emerald-700 border-emerald-200 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              Enhanced Data
            </Badge>
          )}
        </h3>

        {/* Property Information Grid */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Property Information</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div className="flex justify-between py-1">
              <span className="text-gray-600">Folio:</span>
              <span className="font-medium text-navy">{rawData?.parcel_id || propertyData?.parcel_id || ''}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-gray-600">Sub-Division:</span>
              <span className="font-medium text-navy">
                {rawData?.subdivision || propertyData?.legal?.subdivision || ''}
              </span>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-gray-200">
            <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Property Address</h5>
            <p className="text-sm text-navy font-medium mb-3">
              {rawData?.phy_addr1 || propertyData?.address?.street || ''}
              {(rawData?.phy_addr2 || propertyData?.address?.street2) && <br />}
              {rawData?.phy_addr2 || propertyData?.address?.street2 || ''}
              {(rawData?.phy_city || propertyData?.address?.city) && (rawData?.phy_city || propertyData?.address?.city) !== 'Unincorporated County' && (
                <>
                  <br />
                  {rawData?.phy_city || propertyData?.address?.city}, {rawData?.phy_state || propertyData?.address?.state || 'FL'} {rawData?.phy_zipcd?.toString().replace('.0', '') || propertyData?.address?.zip || ''}
                </>
              )}
            </p>
          </div>

          <div className="mt-3 pt-3 border-t border-gray-200">
            <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Owner</h5>
            <p className="text-sm text-navy font-medium mb-3">
              {rawData?.owner_name || propertyData?.owner?.name || ''}
              {(rawData?.owner_name2 || propertyData?.owner?.name2) && (
                <><br />{rawData?.owner_name2 || propertyData?.owner?.name2}</>
              )}
            </p>
          </div>

          <div className="mt-3 pt-3 border-t border-gray-200">
            <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Mailing Address</h5>
            <p className="text-sm text-navy font-medium">
              {rawData?.owner_addr1 || propertyData?.owner?.address || ''}
              {(rawData?.owner_addr2 || propertyData?.owner?.address2) && <br />}
              {rawData?.owner_addr2 || propertyData?.owner?.address2 || ''}
              <br />
              {rawData?.owner_city || propertyData?.owner?.city || ''}{(rawData?.owner_state || propertyData?.owner?.state) ? `, ${rawData?.owner_state || propertyData?.owner?.state}` : ''} {rawData?.owner_zip || propertyData?.owner?.zip || ''}
            </p>
          </div>

          {/* Legal Description */}
          {propertyData?.legal_desc && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Legal Description</h5>
              <p className="text-sm text-navy font-medium">
                {propertyData.legal_desc}
                {propertyData?.lot && propertyData?.block && (
                  <><br />LOT {propertyData.lot} BLK {propertyData.block}</>
                )}
              </p>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h5 className="text-xs font-semibold text-gray-700 uppercase mb-1">PA Primary Zone</h5>
                <p className="text-sm text-navy font-medium">
                  {bcpaData?.pa_primary_zone || bcpaData?.pa_zone || bcpaData?.zoning || '0100'} SINGLE FAMILY - GENERAL
                </p>
              </div>
              <div>
                <h5 className="text-xs font-semibold text-gray-700 uppercase mb-1">Primary Land Use</h5>
                <p className="text-sm text-navy font-medium">
                  {bcpaData?.property_use || bcpaData?.land_use_code || bcpaData?.dor_uc || '0101'} RESIDENTIAL - SINGLE FAMILY : 1 UNIT
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-4 border-t border-gray-200">
            <div>
              <span className="text-xs text-gray-600 uppercase">Beds / Baths / Half</span>
              <p className="text-sm font-semibold text-navy">
                {rawData?.bedrooms || characteristics?.bedrooms || rawData?.no_beds || '-'} /
                {rawData?.bathrooms || characteristics?.bathrooms || rawData?.no_baths || '-'} /
                {rawData?.half_bathrooms || characteristics?.half_bathrooms || rawData?.half_bath || '0'}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-600 uppercase">Floors</span>
              <p className="text-sm font-semibold text-navy">
                {rawData?.stories || characteristics?.stories || rawData?.no_stories || rawData?.floors || '1'}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-600 uppercase">Living Units</span>
              <p className="text-sm font-semibold text-navy">
                {rawData?.units || characteristics?.units || rawData?.no_units || rawData?.living_units || '1'}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-600 uppercase">Year Built</span>
              <p className="text-sm font-semibold text-navy">
                {rawData?.year_built || characteristics?.year_built || (buildingData && buildingData.length > 1 ? 'Multiple (See Building Info.)' : '-')}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
            <div>
              <span className="text-xs text-gray-600 uppercase">Actual Area</span>
              <p className="text-sm font-semibold text-navy">
                {formatSqFt(rawData?.actual_area || rawData?.actual_sqft || rawData?.total_living_area || characteristics?.living_area)}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-600 uppercase">Living Area</span>
              <p className="text-sm font-semibold text-navy">
                {formatSqFt(rawData?.total_living_area || characteristics?.living_area || propertyData?.living_area)}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-600 uppercase">Adjusted Area</span>
              <p className="text-sm font-semibold text-navy">
                {formatSqFt(rawData?.adjusted_area || rawData?.tot_adj_area || rawData?.adjusted_sqft || rawData?.total_living_area || characteristics?.adjusted_area || characteristics?.living_area)}
              </p>
            </div>
            <div>
              <span className="text-xs text-gray-600 uppercase">Lot Size</span>
              <p className="text-sm font-semibold text-navy">
                {formatSqFt(rawData?.land_sqft || characteristics?.lot_size || rawData?.area_sqft)}
                {(rawData?.land_acres || (rawData?.land_sqft && rawData.land_sqft > 0 ? (rawData.land_sqft / 43560).toFixed(2) : null)) && <><br />({rawData?.land_acres || (rawData?.land_sqft / 43560).toFixed(2)} acres)</>}
              </p>
            </div>
          </div>
        </div>

        {/* Land Information Table */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">{currentYear} Land Information</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-2 px-2 font-medium text-gray-700">Land Use</th>
                  <th className="text-left px-2 font-medium text-gray-700">Muni Zone</th>
                  <th className="text-left px-2 font-medium text-gray-700">PA Zone</th>
                  <th className="text-left px-2 font-medium text-gray-700">Unit Type</th>
                  <th className="text-right px-2 font-medium text-gray-700">Units</th>
                  <th className="text-right px-2 font-medium text-gray-700">Calc Value</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-2">
                    {propertyData?.land_use_code || propertyData?.zoning || 'GENERAL'}
                  </td>
                  <td className="px-2">
                    {propertyData?.zoning || 'RU-1'}
                  </td>
                  <td className="px-2">
                    {propertyData?.property_use === '1' ? '0100 - SINGLE FAMILY - GENERAL' :
                     (propertyData?.property_use_desc || 'SINGLE FAMILY - GENERAL')}
                  </td>
                  <td className="px-2">Square Ft.</td>
                  <td className="text-right px-2">
                    {(propertyData?.land_sqft || propertyData?.area_sqft || 0).toLocaleString()}
                  </td>
                  <td className="text-right px-2 font-semibold text-green-600">
                    {formatCurrency(rawData?.land_value || values?.land_value)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Building Information Table */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Building Information</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-2 px-2 font-medium text-gray-700">Building Number</th>
                  <th className="text-left px-2 font-medium text-gray-700">Sub Area</th>
                  <th className="text-center px-2 font-medium text-gray-700">Year Built</th>
                  <th className="text-right px-2 font-medium text-gray-700">Actual Sq.Ft.</th>
                  <th className="text-right px-2 font-medium text-gray-700">Living Sq.Ft.</th>
                  <th className="text-right px-2 font-medium text-gray-700">Adj Sq.Ft.</th>
                  <th className="text-right px-2 font-medium text-gray-700">Calc Value</th>
                </tr>
              </thead>
              <tbody>
                {buildingData && buildingData.length > 0 ? (
                  buildingData.map((building, index) => (
                    <tr key={index} className="border-b border-gray-100">
                      <td className="py-2 px-2">{building.building_number || index + 1}</td>
                      <td className="px-2">{building.sub_area || building.sub_number || '1'}</td>
                      <td className="text-center px-2">{building.year_built || rawData?.year_built || characteristics?.year_built || '-'}</td>
                      <td className="text-right px-2">{(building.actual_area || building.actual_sqft || '0').toLocaleString()}</td>
                      <td className="text-right px-2">{(building.living_area || building.living_sqft || '0').toLocaleString()}</td>
                      <td className="text-right px-2">{(building.adjusted_area || building.adjusted_sqft || '0').toLocaleString()}</td>
                      <td className="text-right px-2 font-semibold text-green-600">
                        {formatCurrency(building.calculated_value || building.building_value)}
                      </td>
                    </tr>
                  ))
                ) : (
                  // Single building from propertyData
                  <tr className="border-b border-gray-100">
                    <td className="py-2 px-2">1</td>
                    <td className="px-2">1</td>
                    <td className="text-center px-2">{rawData?.year_built || characteristics?.year_built || '-'}</td>
                    <td className="text-right px-2">
                      {(rawData?.actual_area || rawData?.actual_sqft || rawData?.total_living_area || characteristics?.living_area || 0).toLocaleString()}
                    </td>
                    <td className="text-right px-2">
                      {(rawData?.total_living_area || characteristics?.living_area || 0).toLocaleString()}
                    </td>
                    <td className="text-right px-2">
                      {(rawData?.adjusted_area || rawData?.tot_adj_area || rawData?.adjusted_sqft || rawData?.total_living_area || characteristics?.adjusted_area || characteristics?.living_area || 0).toLocaleString()}
                    </td>
                    <td className="text-right px-2 font-semibold text-green-600">
                      {formatCurrency(rawData?.building_value || values?.building_value)}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Building Sketches Link */}
          {sketchUrl && (
            <div className="mt-3">
              <a
                href={sketchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 hover:underline"
              >
                <Home className="w-4 h-4 mr-1" />
                Current Building Sketches Available
                <ExternalLink className="w-3 h-3 ml-1" />
              </a>
            </div>
          )}
        </div>

        {/* Extra Features Table */}
        {(extraFeatures && extraFeatures.length > 0) || bcpaData?.pool || bcpaData?.patio || bcpaData?.fence ? (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Extra Features</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left py-2 px-2 font-medium text-gray-700">Description</th>
                    <th className="text-center px-2 font-medium text-gray-700">Year Built</th>
                    <th className="text-right px-2 font-medium text-gray-700">Units</th>
                    <th className="text-right px-2 font-medium text-gray-700">Calc Value</th>
                  </tr>
                </thead>
                <tbody>
                  {extraFeatures && extraFeatures.length > 0 ? (
                    extraFeatures.map((feature, index) => (
                      <tr key={index} className="border-b border-gray-100">
                        <td className="py-2 px-2">{feature.description || feature.feature_desc}</td>
                        <td className="text-center px-2">{feature.year_built || '-'}</td>
                        <td className="text-right px-2">{feature.units || feature.quantity || '1'}</td>
                        <td className="text-right px-2 font-semibold text-green-600">
                          {formatCurrency(feature.calculated_value || feature.feature_value)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <>
                      {bcpaData?.pool && (
                        <tr className="border-b border-gray-100">
                          <td className="py-2 px-2">Swimming Pool</td>
                          <td className="text-center px-2">-</td>
                          <td className="text-right px-2">1</td>
                          <td className="text-right px-2 font-semibold text-green-600">
                            {formatCurrency(bcpaData.pool_value || 15000)}
                          </td>
                        </tr>
                      )}
                      {bcpaData?.patio && (
                        <tr className="border-b border-gray-100">
                          <td className="py-2 px-2">Patio</td>
                          <td className="text-center px-2">-</td>
                          <td className="text-right px-2">1</td>
                          <td className="text-right px-2 font-semibold text-green-600">
                            {formatCurrency(bcpaData.patio_value || 5000)}
                          </td>
                        </tr>
                      )}
                    </>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : null}

        {/* Sales Information */}
        {(propertyData?.sale_date || propertyData?.sale_price) && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Sales Information</h4>
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Sale Date:</span>
                  <p className="font-semibold text-navy">
                    {propertyData.sale_date ? new Date(propertyData.sale_date).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Sale Price:</span>
                  <p className="font-semibold text-navy">
                    {formatCurrency(propertyData.sale_price)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Qualification:</span>
                  <p className="font-semibold text-navy">
                    {propertyData.sale_qualification || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Assessment Information Table */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Assessment Information</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-2 px-3 font-medium text-gray-700">Year</th>
                  <th className="text-right px-3 font-medium text-gray-700">2025</th>
                  <th className="text-right px-3 font-medium text-gray-700">2024</th>
                  <th className="text-right px-3 font-medium text-gray-700">2023</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Land Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.land_value || rawData?.land_value || values?.land_value)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.land_value)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.land_value)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Building Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.building_value || rawData?.building_value || values?.building_value)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.building_value)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.building_value)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Extra Feature Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.extra_feature_value || propertyData?.extra_feature_value)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.extra_feature_value)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.extra_feature_value)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100 bg-blue-50">
                  <td className="py-2 px-3 font-semibold">Market Value</td>
                  <td className="text-right px-3 font-semibold text-blue-600">
                    {formatCurrency(assessmentData?.['2025']?.just_value || rawData?.just_value || values?.market_value)}
                  </td>
                  <td className="text-right px-3 font-semibold text-blue-600">
                    {formatCurrency(assessmentData?.['2024']?.just_value)}
                  </td>
                  <td className="text-right px-3 font-semibold text-blue-600">
                    {formatCurrency(assessmentData?.['2023']?.just_value)}
                  </td>
                </tr>
                <tr className="border-b border-gray-200 bg-green-50">
                  <td className="py-2 px-3 font-semibold">Assessed Value</td>
                  <td className="text-right px-3 font-semibold text-green-600">
                    {formatCurrency(assessmentData?.['2025']?.assessed_value || rawData?.assessed_value || values?.assessed_value)}
                  </td>
                  <td className="text-right px-3 font-semibold text-green-600">
                    {formatCurrency(assessmentData?.['2024']?.assessed_value)}
                  </td>
                  <td className="text-right px-3 font-semibold text-green-600">
                    {formatCurrency(assessmentData?.['2023']?.assessed_value)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Taxable Value Information Table */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Taxable Value Information</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-2 px-3 font-medium text-gray-700">Year</th>
                  <th className="text-right px-3 font-medium text-gray-700">2025</th>
                  <th className="text-right px-3 font-medium text-gray-700">2024</th>
                  <th className="text-right px-3 font-medium text-gray-700">2023</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100 bg-blue-50">
                  <td className="py-2 px-3 font-semibold text-blue-800" colSpan={4}>COUNTY</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Exemption Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.county_exemption || (propertyData?.tax?.exemptions?.homestead || 0) + (propertyData?.tax?.exemptions?.additional_homestead || 0))}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.county_exemption)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.county_exemption)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Taxable Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.county_taxable || propertyData?.tax?.county_taxable_value || rawData?.taxable_value || values?.taxable_value)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.county_taxable)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.county_taxable)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100 bg-green-50">
                  <td className="py-2 px-3 font-semibold text-green-800" colSpan={4}>SCHOOL BOARD</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Exemption Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.school_exemption || propertyData?.tax?.exemptions?.homestead || 0)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.school_exemption)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.school_exemption)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Taxable Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.school_taxable || propertyData?.tax?.school_taxable_value)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.school_taxable)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.school_taxable)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100 bg-yellow-50">
                  <td className="py-2 px-3 font-semibold text-yellow-800" colSpan={4}>CITY</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Exemption Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.city_exemption)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.city_exemption)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.city_exemption)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Taxable Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.city_taxable)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.city_taxable)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.city_taxable)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100 bg-purple-50">
                  <td className="py-2 px-3 font-semibold text-purple-800" colSpan={4}>REGIONAL</td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Exemption Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.regional_exemption)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.regional_exemption)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.regional_exemption)}
                  </td>
                </tr>
                <tr className="border-b border-gray-200">
                  <td className="py-2 px-3 font-medium">Taxable Value</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.regional_taxable)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.regional_taxable)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.regional_taxable)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Benefits Information Table */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Benefits Information</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-2 px-3 font-medium text-gray-700">Benefit</th>
                  <th className="text-left px-3 font-medium text-gray-700">Type</th>
                  <th className="text-right px-3 font-medium text-gray-700">2025</th>
                  <th className="text-right px-3 font-medium text-gray-700">2024</th>
                  <th className="text-right px-3 font-medium text-gray-700">2023</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Save Our Homes Cap</td>
                  <td className="px-3 text-gray-600">Assessment Reduction</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.soh_cap_current || rawData?.soh_value || values?.soh_value || 0)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.soh_cap_current)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.soh_cap_current)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Homestead</td>
                  <td className="px-3 text-gray-600">Exemption</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.homestead_exemption || propertyData?.tax?.exemptions?.homestead || 0)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.homestead_exemption)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.homestead_exemption)}
                  </td>
                </tr>
                <tr className="border-b border-gray-100">
                  <td className="py-2 px-3 font-medium">Additional Homestead</td>
                  <td className="px-3 text-gray-600">Exemption</td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2025']?.additional_homestead || propertyData?.tax?.exemptions?.additional_homestead || 0)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2024']?.additional_homestead)}
                  </td>
                  <td className="text-right px-3">
                    {formatCurrency(assessmentData?.['2023']?.additional_homestead)}
                  </td>
                </tr>
                {propertyData?.tax?.exemptions?.senior > 0 && (
                  <tr className="border-b border-gray-100">
                    <td className="py-2 px-3 font-medium">Senior</td>
                    <td className="px-3 text-gray-600">Exemption</td>
                    <td className="text-right px-3">{formatCurrency(propertyData?.tax?.exemptions?.senior)}</td>
                    <td className="text-right px-3">-</td>
                    <td className="text-right px-3">-</td>
                  </tr>
                )}
                {propertyData?.tax?.exemptions?.veteran > 0 && (
                  <tr className="border-b border-gray-100">
                    <td className="py-2 px-3 font-medium">Veteran</td>
                    <td className="px-3 text-gray-600">Exemption</td>
                    <td className="text-right px-3">{formatCurrency(propertyData?.tax?.exemptions?.veteran)}</td>
                    <td className="text-right px-3">-</td>
                    <td className="text-right px-3">-</td>
                  </tr>
                )}
                {propertyData?.tax?.exemptions?.disability > 0 && (
                  <tr className="border-b border-gray-100">
                    <td className="py-2 px-3 font-medium">Disability</td>
                    <td className="px-3 text-gray-600">Exemption</td>
                    <td className="text-right px-3">{formatCurrency(propertyData?.tax?.exemptions?.disability)}</td>
                    <td className="text-right px-3">-</td>
                    <td className="text-right px-3">-</td>
                  </tr>
                )}
                {propertyData?.tax?.exemptions?.widow > 0 && (
                  <tr className="border-b border-gray-100">
                    <td className="py-2 px-3 font-medium">Widow/Widower</td>
                    <td className="px-3 text-gray-600">Exemption</td>
                    <td className="text-right px-3">{formatCurrency(propertyData?.tax?.exemptions?.widow)}</td>
                    <td className="text-right px-3">-</td>
                    <td className="text-right px-3">-</td>
                  </tr>
                )}
                {propertyData?.tax?.exemptions?.portability > 0 && (
                  <tr className="border-b border-gray-100">
                    <td className="py-2 px-3 font-medium">Portability</td>
                    <td className="px-3 text-gray-600">Transfer Benefit</td>
                    <td className="text-right px-3">{formatCurrency(propertyData?.tax?.exemptions?.portability)}</td>
                    <td className="text-right px-3">-</td>
                    <td className="text-right px-3">-</td>
                  </tr>
                )}
                {propertyData?.tax?.exemptions?.agricultural > 0 && (
                  <tr className="border-b border-gray-100">
                    <td className="py-2 px-3 font-medium">Agricultural</td>
                    <td className="px-3 text-gray-600">Classification</td>
                    <td className="text-right px-3">{formatCurrency(propertyData?.tax?.exemptions?.agricultural)}</td>
                    <td className="text-right px-3">-</td>
                    <td className="text-right px-3">-</td>
                  </tr>
                )}
                <tr className="border-t-2 border-gray-300 bg-gray-50">
                  <td className="py-2 px-3 font-bold">Total Benefits</td>
                  <td className="px-3 text-gray-600"></td>
                  <td className="text-right px-3 font-bold text-green-600">
                    {formatCurrency(propertyData?.tax?.exemptions?.total_exemptions || 0)}
                  </td>
                  <td className="text-right px-3">-</td>
                  <td className="text-right px-3">-</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-500 mt-2 italic">
            Note: Not all benefits are applicable to all Taxable Values (i.e. County, School Board, City, Regional).
          </p>
        </div>

        {/* Enhanced Property Details */}
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Enhanced Property Details</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">

            {/* Data Source Information */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Data Information</h5>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600">Import Date:</span>
                  <span className="font-medium">
                    {rawData?.import_date || propertyData?.import_date ?
                      new Date(rawData?.import_date || propertyData.import_date).toLocaleDateString() : new Date().toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Update:</span>
                  <span className="font-medium">
                    {rawData?.update_date || propertyData?.update_date ?
                      new Date(rawData?.update_date || propertyData.update_date).toLocaleDateString() : new Date().toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Data Source:</span>
                  <span className="font-medium">{propertyData?.data_source || 'Florida Appraiser'}</span>
                </div>
              </div>
            </div>

            {/* Property Characteristics */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Property Characteristics</h5>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-600">Property Use Code:</span>
                  <span className="font-medium">{rawData?.property_use || characteristics?.use_code || propertyData?.property_use || '1'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Land Use Code:</span>
                  <span className="font-medium">{rawData?.land_use_code || propertyData?.land_use_code || '0100'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Zoning:</span>
                  <span className="font-medium">{rawData?.zoning || propertyData?.legal?.zoning || propertyData?.zoning || 'RU-1'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Privacy Status:</span>
                  <span className="font-medium">{propertyData?.is_redacted ? 'Redacted' : 'Public'}</span>
                </div>
              </div>
            </div>

            {/* Location Details */}
            {(propertyData?.geometry || propertyData?.centroid || propertyData?.area_sqft) && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Location Details</h5>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Area (sq ft):</span>
                    <span className="font-medium">
                      {propertyData?.area_sqft ? propertyData.area_sqft.toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Perimeter (ft):</span>
                    <span className="font-medium">
                      {propertyData?.perimeter_ft ? propertyData.perimeter_ft.toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Geometry:</span>
                    <span className="font-medium">{propertyData?.geometry ? 'Available' : 'N/A'}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Additional Information Section */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
            <Info className="w-4 h-4 mr-2" />
            Additional Information
          </h4>
          <p className="text-xs text-gray-600 mb-3 italic">
            * The information listed below is not derived from the Property Appraiser's Office records.
            It is provided for convenience and is derived from other government agencies.
          </p>

          <div className="space-y-3">
            <div>
              <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Land Use and Restrictions</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                <div className="flex">
                  <span className="text-gray-600 min-w-[140px]">Community Development:</span>
                  <span className="font-medium">NONE</span>
                </div>
                <div className="flex">
                  <span className="text-gray-600 min-w-[140px]">Redevelopment Area:</span>
                  <span className="font-medium">NONE</span>
                </div>
                <div className="flex">
                  <span className="text-gray-600 min-w-[140px]">Empowerment Zone:</span>
                  <span className="font-medium">NONE</span>
                </div>
                <div className="flex">
                  <span className="text-gray-600 min-w-[140px]">Enterprise Zone:</span>
                  <span className="font-medium">NONE</span>
                </div>
                <div className="flex">
                  <span className="text-gray-600 min-w-[140px]">Urban Development:</span>
                  <span className="font-medium">INSIDE URBAN DEVELOPMENT BOUNDARY</span>
                </div>
                <div className="flex">
                  <span className="text-gray-600 min-w-[140px]">Zoning Code:</span>
                  <span className="font-medium">
                    {propertyData?.zoning || 'RU-1-Single-family Residential District 7,500 ft²'}
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h5 className="text-xs font-semibold text-gray-700 uppercase mb-2">Government Agencies and Community Services</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                <div className="flex">
                  <span className="text-gray-600 min-w-[140px]">Existing Land Use:</span>
                  <span className="font-medium">10-Single-Family, Med.-Density (2-5 DU/Gross Acre)</span>
                </div>
                <div className="flex">
                  <span className="text-gray-600 min-w-[140px]">Future Land Use:</span>
                  <span className="font-medium">Low Density Residential</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}// Force refresh Thu, Sep 25, 2025  9:09:16 AM
