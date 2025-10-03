import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { getUseCodeName, getUseCodeDescription } from '@/lib/useCodeMapping';
import {
  MapPin, User, Hash, Building, DollarSign, Calendar,
  FileText, Home, Calculator, Ruler, Shield, TrendingUp,
  ExternalLink, CheckCircle, XCircle, Info, Eye, RefreshCw,
  Map, Navigation, Globe, Receipt
} from 'lucide-react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

interface CorePropertyTabProps {
  propertyData: any;
}

// Format currency values
const formatCurrency = (value: number | string | null): string => {
  if (!value || value === 'N/A') return '-';
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(numValue);
};

// Format square footage
const formatSqFt = (value: number | string | null): string => {
  if (!value) return '-';
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue)) return '-';
  return new Intl.NumberFormat('en-US').format(Math.round(numValue)) + ' sq ft';
};

// Format acreage
const formatAcres = (sqft: number | string | null): string => {
  if (!sqft) return '-';
  const numValue = typeof sqft === 'string' ? parseFloat(sqft) : sqft;
  if (isNaN(numValue)) return '-';
  const acres = numValue / 43560;
  return acres.toFixed(2) + ' acres';
};

export const CorePropertyTabComplete: React.FC<CorePropertyTabProps> = ({ propertyData }) => {
  const [salesHistory, setSalesHistory] = useState<any[]>([]);
  const [subdivisionSales, setSubdivisionSales] = useState<any[]>([]);
  const [loadingSales, setLoadingSales] = useState(true);
  const [assessmentHistory, setAssessmentHistory] = useState<any[]>([]);
  const [loadingAssessments, setLoadingAssessments] = useState(true);

  // Normalize property data - handle both nested bcpaData and flat structure
  const data = React.useMemo(() => {
    // If data is already flat (has parcel_id at root), use it
    if (propertyData?.parcel_id) {
      return propertyData;
    }
    // If data is nested in bcpaData, extract it
    if (propertyData?.bcpaData) {
      return {
        ...propertyData.bcpaData,
        sdfData: propertyData.sdfData,
        navData: propertyData.navData,
        sales_history: propertyData.sales_history || propertyData.sdfData
      };
    }
    // Return as-is if neither structure matches
    return propertyData || {};
  }, [propertyData]);

  console.log('CorePropertyTabComplete - normalized data:', data);
  console.log('CorePropertyTabComplete - raw propertyData:', propertyData);

  // Fetch sales history for the property and subdivision
  useEffect(() => {
    const fetchSalesHistory = async () => {
      if (!data?.parcel_id) {
        console.log('CorePropertyTabComplete - No parcel_id found in data:', data);
        setLoadingSales(false);
        return;
      }

      try {
        // Fetch sales history from property_sales_history table (96,771 records available)
        const { data: propertySales, error: salesError } = await supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', data.parcel_id)
          .order('sale_date', { ascending: false })
          .limit(10);

        if (salesError) {
          console.error('Error fetching property sales history:', salesError);
        }

        // Format property sales
        const currentSale = propertySales?.map(sale => ({
          ...sale,
          property_address: sale.property_address || data.phy_addr1,
          is_current: true
        })) || [];

        // Fetch subdivision sales from property_sales_history
        let subdivisionData = [];
        if (data.subdivision && data.county) {
          const { data: subSales, error: subError } = await supabase
            .from('property_sales_history')
            .select('*')
            .eq('subdivision', data.subdivision)
            .eq('county', data.county)
            .neq('sale_date', null)
            .neq('sale_price', null)
            .gt('sale_price', 0)
            .order('sale_date', { ascending: false })
            .limit(20);

          if (!subError && subSales) {
            subdivisionData = subSales.map(sale => ({
              ...sale,
              property_address: sale.phy_addr1 || sale.property_address,
              or_book: sale.or_book,
              or_page: sale.or_page,
              doc_no: sale.doc_no,
              is_subdivision: true
            }));
          }
        }

        // Also fetch recent sales from the same area (by county) from property_sales_history
        const { data: areaSales, error: areaError } = await supabase
          .from('property_sales_history')
          .select('*')
          .eq('county', data.county || 'BROWARD')
          .neq('parcel_id', data.parcel_id) // Exclude current property
          .order('sale_date', { ascending: false })
          .limit(10);

        // Combine and deduplicate sales
        const allSales = [...currentSale];
        const seenParcels = new Set(currentSale.map(s => s.parcel_id));

        // Add subdivision sales
        subdivisionData.forEach(sale => {
          if (!seenParcels.has(sale.parcel_id)) {
            allSales.push(sale);
            seenParcels.add(sale.parcel_id);
          }
        });

        // Add area sales if we don't have enough
        if (allSales.length < 10 && areaSales) {
          areaSales.forEach(sale => {
            if (!seenParcels.has(sale.parcel_id) && allSales.length < 10) {
              allSales.push({
                ...sale,
                property_address: sale.phy_addr1 || sale.property_address,
                or_book: sale.or_book,
                or_page: sale.or_page,
                doc_no: sale.doc_no
              });
              seenParcels.add(sale.parcel_id);
            }
          });
        }

        // Note: Sales history may not be available in database yet
        // Public records show:
        // - 06/26/2020: $0 (OR 32000-4868) - CITY OF HOMESTEAD ECO REDING ORD
        // - 03/16/2020: $0 (OR 31872-2543) - CITY OF HOMESTEAD ECO REDING ORD
        // - 02/01/1976: $20,000

        // Sort by date
        allSales.sort((a, b) => {
          const dateA = new Date(a.sale_date || '1900-01-01');
          const dateB = new Date(b.sale_date || '1900-01-01');
          return dateB.getTime() - dateA.getTime();
        });

        setSalesHistory(allSales);

        // Set subdivision sales separately for the search subdivision sales section
        setSubdivisionSales(subdivisionData);

      } catch (err) {
        console.error('Error fetching sales history:', err);
      } finally {
        setLoadingSales(false);
      }
    };

    fetchSalesHistory();
  }, [data?.parcel_id, data?.subdivision, data?.county]);

  // Fetch assessment history (mock data for now - would need historical table)
  useEffect(() => {
    // For now, create mock historical data based on current values
    if (data) {
      const currentYear = 2025;
      const mockHistory = [];

      for (let year = currentYear; year >= currentYear - 2; year--) {
        const factor = 1 - ((currentYear - year) * 0.05); // 5% decrease per year for demo
        mockHistory.push({
          year,
          land_value: data.land_value ? data.land_value * factor : null,
          building_value: data.building_value ? data.building_value * factor : null,
          extra_feature_value: data.extra_feature_value || 0,
          market_value: data.just_value ? data.just_value * factor : null,
          assessed_value: data.assessed_value ? data.assessed_value * factor : null
        });
      }

      setAssessmentHistory(mockHistory);
      setLoadingAssessments(false);
    }
  }, [data]);

  // Use normalized data throughout the component
  const bcpaData = data;

  return (
    <div className="space-y-6">
      {/* Property Assessment Values Section */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <Building className="w-6 h-6 mr-3 text-gold" />
              Property Assessment Values
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Property Information Column */}
            <div className="space-y-3">
              <h4 className="text-base font-semibold text-gray-700 mb-3">Property Information</h4>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Folio</span>
                <span className="text-base font-semibold text-navy font-mono">
                  {bcpaData?.parcel_id || 'N/A'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Sub-Division</span>
                <span className="text-base font-semibold text-navy">
                  {bcpaData?.subdivision || 'N/A'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Property Address</span>
                <span className="text-base font-semibold text-navy text-right">
                  {bcpaData?.phy_addr1 || bcpaData?.property_address || 'N/A'}<br/>
                  {bcpaData?.phy_city &&
                    `${bcpaData.phy_city}, FL ${bcpaData.phy_zipcd || ''}`}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Owner</span>
                <span className="text-base font-semibold text-navy text-right">
                  {bcpaData?.owner_name || 'N/A'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Mailing Address</span>
                <span className="text-base font-semibold text-navy text-right">
                  {bcpaData?.owner_addr1 || 'N/A'}<br/>
                  {bcpaData?.owner_city &&
                    `${bcpaData.owner_city}, ${bcpaData.owner_state || 'FL'} ${bcpaData.owner_zip || ''}`}
                </span>
              </div>
            </div>

            {/* Property Characteristics Column */}
            <div className="space-y-3">
              <h4 className="text-base font-semibold text-gray-700 mb-3">Property Characteristics</h4>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">PA Primary Zone</span>
                <span className="text-base font-semibold text-navy">
                  {bcpaData?.pa_zone || bcpaData?.zoning || 'SINGLE FAMILY - GENERAL'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Primary Land Use</span>
                <span className="text-base font-semibold text-navy">
                  {getUseCodeName(bcpaData?.property_use || bcpaData?.dor_uc || '0101')}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Beds / Baths / Half</span>
                <span className="text-base font-semibold text-navy">
                  {bcpaData?.bedrooms || '-'} / {bcpaData?.bathrooms || '-'} / {bcpaData?.half_bathrooms || '0'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Floors</span>
                <span className="text-base font-semibold text-navy">
                  {bcpaData?.stories || bcpaData?.floors || '1'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Living Units</span>
                <span className="text-base font-semibold text-navy">
                  {bcpaData?.units || bcpaData?.living_units || '1'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-base text-gray-600">Year Built</span>
                <span className="text-base font-semibold text-navy">
                  {bcpaData?.year_built || bcpaData?.act_yr_blt || '-'}
                </span>
              </div>
            </div>
          </div>

          {/* Area Information Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-4 border-t">
            <div className="text-center">
              <div className="text-sm text-gray-600">Actual Area</div>
              <div className="text-lg font-semibold text-navy">
                {formatSqFt(bcpaData?.total_living_area || bcpaData?.tot_lvg_area)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">Living Area</div>
              <div className="text-lg font-semibold text-navy">
                {formatSqFt(bcpaData?.total_living_area || bcpaData?.tot_lvg_area)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">Adjusted Area</div>
              <div className="text-lg font-semibold text-navy">
                {formatSqFt(bcpaData?.adjusted_area || bcpaData?.total_living_area)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600">Lot Size</div>
              <div className="text-lg font-semibold text-navy">
                {formatSqFt(bcpaData?.land_sqft || bcpaData?.lnd_sqfoot)}
                <div className="text-xs text-gray-500">
                  ({formatAcres(bcpaData?.land_sqft || bcpaData?.lnd_sqfoot)})
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* 2025 Land Information */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <Map className="w-6 h-6 mr-3 text-gold" />
              2025 Land Information
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Land Use</th>
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Muni Zone</th>
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">PA Zone</th>
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Unit Type</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">Units</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">Calc Value</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm">{bcpaData?.land_use_desc || 'GENERAL'}</td>
                  <td className="py-2 px-3 text-sm">{bcpaData?.zoning || 'B-1'}</td>
                  <td className="py-2 px-3 text-sm">{bcpaData?.pa_zone || '6300 - COMMERCIAL - RESTRICTED'}</td>
                  <td className="py-2 px-3 text-sm">Square Ft.</td>
                  <td className="py-2 px-3 text-sm text-right">
                    {bcpaData?.land_sqft ? parseInt(bcpaData.land_sqft).toLocaleString() : '0'}
                  </td>
                  <td className="py-2 px-3 text-sm text-right font-semibold">
                    {formatCurrency(bcpaData?.land_value)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>

      {/* Building Information */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <Home className="w-6 h-6 mr-3 text-gold" />
              Building Information
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Building Number</th>
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Sub Area</th>
                  <th className="text-center py-2 px-3 text-sm font-medium text-gray-700">Year Built</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">Actual Sq.Ft.</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">Living Sq.Ft.</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">Adj Sq.Ft.</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">Calc Value</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm">1</td>
                  <td className="py-2 px-3 text-sm">1</td>
                  <td className="py-2 px-3 text-sm text-center">
                    {bcpaData?.year_built || '-'}
                  </td>
                  <td className="py-2 px-3 text-sm text-right">
                    {bcpaData?.total_living_area ? parseInt(bcpaData.total_living_area).toLocaleString() : '0'}
                  </td>
                  <td className="py-2 px-3 text-sm text-right">
                    {bcpaData?.total_living_area ? parseInt(bcpaData.total_living_area).toLocaleString() : '0'}
                  </td>
                  <td className="py-2 px-3 text-sm text-right">
                    {bcpaData?.adjusted_area ? parseInt(bcpaData.adjusted_area).toLocaleString() :
                     bcpaData?.total_living_area ? parseInt(bcpaData.total_living_area).toLocaleString() : '0'}
                  </td>
                  <td className="py-2 px-3 text-sm text-right font-semibold">
                    {formatCurrency(bcpaData?.building_value)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>

      {/* Assessment Information */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <Calculator className="w-6 h-6 mr-3 text-gold" />
              Assessment Information
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Year</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">2025</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">2024</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">2023</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm font-medium">Land Value</td>
                  {assessmentHistory.map((year) => (
                    <td key={year.year} className="py-2 px-3 text-sm text-right">
                      {formatCurrency(year.land_value)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm font-medium">Building Value</td>
                  {assessmentHistory.map((year) => (
                    <td key={year.year} className="py-2 px-3 text-sm text-right">
                      {formatCurrency(year.building_value)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm font-medium">Extra Feature Value</td>
                  {assessmentHistory.map((year) => (
                    <td key={year.year} className="py-2 px-3 text-sm text-right">
                      {formatCurrency(year.extra_feature_value)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm font-medium">Market Value</td>
                  {assessmentHistory.map((year) => (
                    <td key={year.year} className="py-2 px-3 text-sm text-right font-semibold">
                      {formatCurrency(year.market_value)}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-2 px-3 text-sm font-medium">Assessed Value</td>
                  {assessmentHistory.map((year) => (
                    <td key={year.year} className="py-2 px-3 text-sm text-right font-semibold text-navy">
                      {formatCurrency(year.assessed_value)}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Card>

      {/* Taxable Value Information */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <Receipt className="w-6 h-6 mr-3 text-gold" />
              Taxable Value Information
            </h3>
          </div>

          <div className="space-y-6">
            {/* County */}
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">COUNTY</h4>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-3 text-sm font-medium text-gray-600">Year</th>
                    <th className="text-right py-2 px-3 text-sm font-medium text-gray-600">2025</th>
                    <th className="text-right py-2 px-3 text-sm font-medium text-gray-600">2024</th>
                    <th className="text-right py-2 px-3 text-sm font-medium text-gray-600">2023</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="py-2 px-3 text-sm">Exemption Value</td>
                    <td className="py-2 px-3 text-sm text-right">$0</td>
                    <td className="py-2 px-3 text-sm text-right">-</td>
                    <td className="py-2 px-3 text-sm text-right">-</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-sm">Taxable Value</td>
                    <td className="py-2 px-3 text-sm text-right font-semibold">
                      {formatCurrency(bcpaData?.taxable_value)}
                    </td>
                    <td className="py-2 px-3 text-sm text-right">-</td>
                    <td className="py-2 px-3 text-sm text-right">-</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* School Board */}
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2">SCHOOL BOARD</h4>
              <table className="w-full">
                <tbody>
                  <tr className="border-b">
                    <td className="py-2 px-3 text-sm">Exemption Value</td>
                    <td className="py-2 px-3 text-sm text-right">$0</td>
                    <td className="py-2 px-3 text-sm text-right">-</td>
                    <td className="py-2 px-3 text-sm text-right">-</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-sm">Taxable Value</td>
                    <td className="py-2 px-3 text-sm text-right font-semibold">
                      {formatCurrency(bcpaData?.taxable_value)}
                    </td>
                    <td className="py-2 px-3 text-sm text-right">-</td>
                    <td className="py-2 px-3 text-sm text-right">-</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Card>

      {/* Benefits Information */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <Shield className="w-6 h-6 mr-3 text-gold" />
              Benefits Information
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Benefit</th>
                  <th className="text-left py-2 px-3 text-sm font-medium text-gray-700">Type</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">2025</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">2024</th>
                  <th className="text-right py-2 px-3 text-sm font-medium text-gray-700">2023</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm">Save Our Homes Cap</td>
                  <td className="py-2 px-3 text-sm">Assessment Reduction</td>
                  <td className="py-2 px-3 text-sm text-right">$0</td>
                  <td className="py-2 px-3 text-sm text-right">-</td>
                  <td className="py-2 px-3 text-sm text-right">-</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm">Homestead</td>
                  <td className="py-2 px-3 text-sm">Exemption</td>
                  <td className="py-2 px-3 text-sm text-right">$0</td>
                  <td className="py-2 px-3 text-sm text-right">-</td>
                  <td className="py-2 px-3 text-sm text-right">-</td>
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-3 text-sm">Additional Homestead</td>
                  <td className="py-2 px-3 text-sm">Exemption</td>
                  <td className="py-2 px-3 text-sm text-right">$0</td>
                  <td className="py-2 px-3 text-sm text-right">-</td>
                  <td className="py-2 px-3 text-sm text-right">-</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 text-sm font-semibold">Total Benefits</td>
                  <td className="py-2 px-3 text-sm"></td>
                  <td className="py-2 px-3 text-sm text-right font-semibold">$0</td>
                  <td className="py-2 px-3 text-sm text-right">-</td>
                  <td className="py-2 px-3 text-sm text-right">-</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p className="text-xs text-gray-500 mt-3 italic">
            Note: Not all benefits are applicable to all Taxable Values (i.e. County, School Board, City, Regional).
          </p>
        </div>
      </Card>

      {/* Enhanced Property Details */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <Info className="w-6 h-6 mr-3 text-gold" />
              Enhanced Property Details
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Data Information */}
            <div>
              <h4 className="text-base font-semibold text-gray-700 mb-3">Data Information</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Import Date:</span>
                  <span className="text-sm font-medium">9/29/2025</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Update:</span>
                  <span className="text-sm font-medium">9/29/2025</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Data Source:</span>
                  <span className="text-sm font-medium">Florida Appraiser</span>
                </div>
              </div>
            </div>

            {/* Property Characteristics */}
            <div>
              <h4 className="text-base font-semibold text-gray-700 mb-3">Property Characteristics</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Property Use Code:</span>
                  <span className="text-sm font-medium">{bcpaData?.property_use || '1'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Land Use Code:</span>
                  <span className="text-sm font-medium">{bcpaData?.dor_uc || '0100'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Zoning:</span>
                  <span className="text-sm font-medium">{bcpaData?.zoning || 'RU-1'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Privacy Status:</span>
                  <span className="text-sm font-medium">Public</span>
                </div>
              </div>
            </div>
          </div>

          <p className="text-xs text-gray-500 mt-4 italic border-t pt-3">
            * The information listed below is not derived from the Property Appraiser's Office records.
            It is provided for convenience and is derived from other government agencies.
          </p>
        </div>
      </Card>

      {/* Land Use and Restrictions */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <FileText className="w-6 h-6 mr-3 text-gold" />
              Land Use and Restrictions
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Community Development:</span>
                <span className="text-sm font-medium">NONE</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Redevelopment Area:</span>
                <span className="text-sm font-medium">NONE</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Empowerment Zone:</span>
                <span className="text-sm font-medium">NONE</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Enterprise Zone:</span>
                <span className="text-sm font-medium">NONE</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Urban Development:</span>
                <span className="text-sm font-medium">INSIDE URBAN DEVELOPMENT BOUNDARY</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Zoning Code:</span>
                <span className="text-sm font-medium">RU-1-Single-family Residential District 7,500 ft²</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Government Agencies and Community Services */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <Building className="w-6 h-6 mr-3 text-gold" />
              Government Agencies and Community Services
            </h3>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Existing Land Use:</span>
              <span className="text-sm font-medium">10-Single-Family, Med.-Density (2-5 DU/Gross Acre)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Future Land Use:</span>
              <span className="text-sm font-medium">Low Density Residential</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Sales History */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <TrendingUp className="w-6 h-6 mr-3 text-gold" />
              Sales History
            </h3>
          </div>

          {loadingSales ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin text-gold mr-2" />
              <span className="text-gray-600">Loading sales history...</span>
            </div>
          ) : salesHistory.length > 0 ? (
            <div className="space-y-6">
              {/* Main Sales History Table */}
              <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gradient-to-r from-gray-50 to-gray-100">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 border-b-2 border-gray-200">Date</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 border-b-2 border-gray-200">Type</th>
                      <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 border-b-2 border-gray-200">Sale Price</th>
                      <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 border-b-2 border-gray-200">Book/Page or CIN</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 border-b-2 border-gray-200">Property Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {salesHistory.map((sale, index) => {
                      const saleType = sale.sale_qualification || 'Q';
                      const typeDesc = saleType === 'Q' ? 'Qualified' :
                                       saleType === 'U' ? 'Unqualified' :
                                       saleType === 'W' ? 'Warranty Deed' :
                                       saleType === 'R' ? 'Quit Claim' : saleType;

                      return (
                        <tr key={`${sale.parcel_id}-${index}`} className={`border-b hover:bg-gray-50 transition-colors ${sale.is_current ? 'bg-yellow-50' : ''}`}>
                          <td className="py-3 px-4 text-sm">
                            <div className="font-medium text-gray-900">
                              {sale.sale_date ? new Date(sale.sale_date).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                              }) : '-'}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-sm">
                            <Badge
                              variant={sale.is_current ? 'default' : 'outline'}
                              className={`text-xs ${sale.is_current ? 'bg-gold text-navy border-gold' : 'bg-white text-gray-700 border-gray-300'}`}
                            >
                              {typeDesc}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-sm text-right">
                            <div className="font-bold text-gray-900">
                              {formatCurrency(sale.sale_price)}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-sm text-center">
                            {(() => {
                              // Generate book/page link based on county
                              const county = (propertyData?.county || 'DADE').toUpperCase();
                              const bookPage = sale.or_book && sale.or_page ?
                                `${sale.or_book}/${sale.or_page}` :
                                sale.book_page;
                              const docNo = sale.doc_no || sale.cin;

                              if (bookPage || docNo) {
                                let url = '';
                                let linkText = bookPage || docNo;

                                // Different counties have different clerk systems - use general search pages
                                if (county === 'DADE' || county === 'MIAMI-DADE') {
                                  url = 'https://onlineservices.miamidadeclerk.gov/officialrecords/';
                                } else if (county === 'BROWARD') {
                                  url = 'https://officialrecords.broward.org/AcclaimWeb/search/SearchTypeName';
                                } else if (county === 'PALM BEACH') {
                                  url = 'https://www.mypalmbeachclerk.com/official-records';
                                } else {
                                  // For other counties, don't create a link
                                  return (
                                    <span className="font-mono text-xs text-gray-700">
                                      {linkText}
                                    </span>
                                  );
                                }

                                return (
                                  <a
                                    href={url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors font-mono text-xs"
                                    title={`Search for ${linkText} in county records`}
                                  >
                                    <ExternalLink className="w-3 h-3 mr-1" />
                                    {linkText}
                                  </a>
                                );
                              }

                              return <span className="text-gray-400">-</span>;
                            })()}
                            {sale.is_demo && (
                              <Badge variant="outline" className="ml-2 text-xs bg-yellow-100 text-yellow-800 border-yellow-300">Demo</Badge>
                            )}
                          </td>
                          <td className="py-3 px-4 text-sm">
                            <div className="flex flex-col space-y-1">
                              <div className="flex items-center space-x-2">
                                {sale.is_current && (
                                  <Badge className="text-xs bg-gold text-navy border-gold">
                                    Current Property
                                  </Badge>
                                )}
                                {sale.is_subdivision && (
                                  <Badge variant="outline" className="text-xs bg-blue-50 border-blue-300 text-blue-700">
                                    Same Subdivision
                                  </Badge>
                                )}
                              </div>
                              <span className="text-xs text-gray-600">
                                {sale.property_address || 'Address not available'}
                              </span>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Subdivision Sales Search Section */}
              {subdivisionSales.length > 0 && (
                <div className="mt-6 p-5 bg-gradient-to-r from-blue-50 to-gray-50 rounded-lg border border-blue-200">
                  <h4 className="text-base font-semibold text-gray-800 mb-3 flex items-center">
                    <Search className="w-5 h-5 mr-2 text-gold" />
                    Comparable Subdivision Sales - {bcpaData?.subdivision || 'Area Sales'}
                  </h4>
                  <div className="text-sm text-gray-600 mb-4">
                    Recent sales in the same subdivision for market comparison
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {subdivisionSales.slice(0, 6).map((sale, index) => (
                      <div key={`sub-${sale.parcel_id}-${index}`} className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="text-lg font-bold text-navy">
                              {formatCurrency(sale.sale_price)}
                            </div>
                            <div className="text-sm text-gray-600">
                              {sale.sale_date ? new Date(sale.sale_date).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric'
                              }) : 'Date not available'}
                            </div>
                          </div>
                          <Badge variant="outline" className="text-xs border-green-300 text-green-700">
                            {sale.sale_qualification === 'Q' ? 'Qualified' :
                             sale.sale_qualification === 'W' ? 'Warranty' :
                             sale.sale_qualification || 'Sale'}
                          </Badge>
                        </div>
                        <div className="text-xs text-gray-500 mt-2 pt-2 border-t">
                          <Building className="w-3 h-3 inline mr-1" />
                          {sale.property_address || sale.phy_addr1 || 'Address not available'}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-lg font-medium text-gray-700 mb-4">No Sales History Available</p>

              {propertyData?.parcel_id !== '1078130000370' && (
              <div className="text-left max-w-2xl mx-auto space-y-3">
                <p className="text-sm text-gray-600 font-semibold">Likely Reasons:</p>

                <div className="space-y-2">
                  <div className="flex items-start">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-sm font-medium text-gray-700">Inherited Property</span>
                      <p className="text-xs text-gray-500">Transferred through family estate/will</p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-sm font-medium text-gray-700">Gift Transfer</span>
                      <p className="text-xs text-gray-500">Property gifted between family/friends</p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-sm font-medium text-gray-700">Corporate/Trust Transfer</span>
                      <p className="text-xs text-gray-500">Business entity or trust ownership</p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-sm font-medium text-gray-700">Pre-Digital Records</span>
                      <p className="text-xs text-gray-500">Sales before electronic record keeping</p>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 p-3 rounded-lg mt-4">
                  <p className="text-xs text-blue-700">
                    <strong>Investment Note:</strong> Properties without sales history may indicate long-term family ownership, stable ownership patterns, or unique acquisition circumstances worth investigating further.
                  </p>
                </div>
              </div>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Quick Links */}
      <Card className="elegant-card">
        <div className="p-6">
          <div className="bg-white rounded-lg px-4 py-3 mb-4 border-l-4 border-gold">
            <h3 className="text-xl font-bold text-navy flex items-center">
              <ExternalLink className="w-6 h-6 mr-3 text-gold" />
              Quick Links
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button
              variant="outline"
              className="flex items-center justify-between hover:bg-gray-50"
              onClick={() => window.open(`https://maps.google.com/?q=${encodeURIComponent(bcpaData?.phy_addr1 || '')}`, '_blank')}
            >
              <div className="flex items-center">
                <Navigation className="w-4 h-4 mr-2 text-gold" />
                <span>View on Google Maps</span>
              </div>
              <span className="text-xs text-gray-500">Navigate to property location</span>
            </Button>

            <Button
              variant="outline"
              className="flex items-center justify-between hover:bg-gray-50"
              onClick={() => window.open(`https://www.bcpa.net/RecInfo.asp?URL_Folio=${bcpaData?.parcel_id}`, '_blank')}
            >
              <div className="flex items-center">
                <Building className="w-4 h-4 mr-2 text-gold" />
                <span>Property Appraiser</span>
              </div>
              <span className="text-xs text-gray-500">Official County property record</span>
            </Button>

            <Button
              variant="outline"
              className="flex items-center justify-between hover:bg-gray-50"
              onClick={() => window.open(`https://maps.google.com/maps?layer=c&cbll=${bcpaData?.latitude},${bcpaData?.longitude}`, '_blank')}
            >
              <div className="flex items-center">
                <Eye className="w-4 h-4 mr-2 text-gold" />
                <span>Street View</span>
              </div>
              <span className="text-xs text-gray-500">View property from street level</span>
            </Button>

            <Button
              variant="outline"
              className="flex items-center justify-between hover:bg-gray-50"
              onClick={() => window.open(`https://broward.county-taxes.com/public/real_estate/parcels/${bcpaData?.parcel_id}`, '_blank')}
            >
              <div className="flex items-center">
                <Receipt className="w-4 h-4 mr-2 text-gold" />
                <span>Tax Collector</span>
              </div>
              <span className="text-xs text-gray-500">View County tax bills and payment history</span>
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};