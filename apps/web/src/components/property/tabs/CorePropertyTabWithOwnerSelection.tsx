import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  MapPin, User, Hash, Building, DollarSign, Calendar,
  FileText, Home, Calculator, Ruler, Shield, TrendingUp,
  ExternalLink, CheckCircle, XCircle, Info, Eye, RefreshCw
} from 'lucide-react';
import { createClient } from '@supabase/supabase-js';
import { OwnerPropertiesSelector } from '../OwnerPropertiesSelector';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

interface CorePropertyTabProps {
  propertyData: any;
  onPropertyChange?: (newPropertyData: any) => void;
}

export function CorePropertyTabWithOwnerSelection({ propertyData, onPropertyChange }: CorePropertyTabProps) {
  const [currentPropertyData, setCurrentPropertyData] = useState(propertyData);
  const [salesHistory, setSalesHistory] = useState<any[]>([]);
  const [loadingSales, setLoadingSales] = useState(false);

  // Extract current data for easier access
  const { bcpaData, sdfData, navData } = currentPropertyData || {};

  // Handle property selection from OwnerPropertiesSelector
  const handlePropertySelect = async (selectedProperty: any) => {
    try {
      console.log('Switching to property:', selectedProperty.parcel_id);

      // Fetch full property data for the selected property
      const { data: fullPropertyData, error } = await supabase
        .from('florida_parcels')
        .select('*')
        .eq('parcel_id', selectedProperty.parcel_id)
        .single();

      if (!error && fullPropertyData) {
        // Transform the data to match the existing structure
        const transformedData = {
          bcpaData: {
            parcel_id: fullPropertyData.parcel_id,
            property_address_street: fullPropertyData.phy_addr1,
            property_address_city: fullPropertyData.phy_city,
            property_address_zip: fullPropertyData.phy_zipcd,
            owner_name: fullPropertyData.own_name,
            property_use_code: fullPropertyData.dor_uc,
            land_value: fullPropertyData.lnd_val,
            building_value: (fullPropertyData.jv || 0) - (fullPropertyData.lnd_val || 0),
            market_value: fullPropertyData.jv,
            just_value: fullPropertyData.jv,
            assessed_value: fullPropertyData.av_sd,
            taxable_value: fullPropertyData.tv_sd,
            tax_amount: fullPropertyData.tax_amount,
            homestead_exemption: fullPropertyData.homestead_exemption,
            other_exemptions: fullPropertyData.other_exemptions,
            lot_size_sqft: fullPropertyData.lnd_sqfoot,
            living_area: fullPropertyData.tot_lvg_area,
            units: fullPropertyData.no_res_unts || '1',
            bedrooms: fullPropertyData.bedroom_cnt,
            bathrooms: fullPropertyData.bathroom_cnt,
            year_built: fullPropertyData.act_yr_blt,
            eff_year_built: fullPropertyData.eff_yr_blt,
            sale_date: fullPropertyData.sale_yr1 && fullPropertyData.sale_mo1
              ? `${fullPropertyData.sale_yr1}-${String(fullPropertyData.sale_mo1).padStart(2, '0')}-01`
              : fullPropertyData.sale_date,
            sale_price: fullPropertyData.sale_prc1,
            sale_type: fullPropertyData.qual_cd1 === 'Q' ? 'Warranty Deed'
              : fullPropertyData.deed_type || fullPropertyData.sale_type || 'Standard Sale',
            book_page: fullPropertyData.book_page || fullPropertyData.or_book_page,
            cin: fullPropertyData.cin || fullPropertyData.clerk_no,
            subdivision: fullPropertyData.subdivision,
            property_sketch_link: fullPropertyData.property_sketch_link,
            ...fullPropertyData
          },
          sdfData: [], // Will be loaded separately if needed
          navData: [], // Will be loaded separately if needed
          ...fullPropertyData
        };

        setCurrentPropertyData(transformedData);

        // Notify parent component of property change
        if (onPropertyChange) {
          onPropertyChange(transformedData);
        }

        // Clear sales history to trigger reload
        setSalesHistory([]);
      }
    } catch (error) {
      console.error('Error fetching selected property data:', error);
    }
  };

  // Update currentPropertyData when propertyData prop changes
  useEffect(() => {
    setCurrentPropertyData(propertyData);
  }, [propertyData]);

  // Fetch comprehensive sales history
  useEffect(() => {
    const fetchSalesHistory = async () => {
      if (!bcpaData?.parcel_id && !currentPropertyData?.parcel_id) {
        console.log('No parcel_id available to fetch sales history');
        return;
      }

      const parcelId = bcpaData?.parcel_id || currentPropertyData?.parcel_id;

      setLoadingSales(true);
      try {
        // First try to get data from property_sales_history table
        console.log('Fetching sales history for parcel:', parcelId);
        const { data: salesHistoryData, error: salesError } = await supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false });

        console.log('Sales history query result:', { salesHistoryData, salesError });

        if (!salesError && salesHistoryData && salesHistoryData.length > 0) {
          setSalesHistory(salesHistoryData);
        } else {
          // Fallback to sdfData or create from existing data
          const combinedSales = [];

          // Check if propertyData has direct sales information - filter out sales under $1000
          const propSalePrice = currentPropertyData?.sale_prc1 || currentPropertyData?.sale_price;
          if (propSalePrice && parseFloat(propSalePrice) >= 1000) {
            console.log('Using propertyData sales info:', {
              sale_prc1: currentPropertyData.sale_prc1,
              sale_yr1: currentPropertyData.sale_yr1,
              sale_mo1: currentPropertyData.sale_mo1
            });

            combinedSales.push({
              sale_date: currentPropertyData.sale_yr1 && currentPropertyData.sale_mo1 ?
                `${currentPropertyData.sale_yr1}-${String(currentPropertyData.sale_mo1).padStart(2, '0')}-01` :
                currentPropertyData.sale_date || new Date().toISOString(),
              sale_price: propSalePrice,
              sale_type: currentPropertyData.qual_cd1 === 'Q' ? 'Warranty Deed' :
                currentPropertyData.deed_type || currentPropertyData.sale_type || 'Standard Sale',
              sale_qualification: currentPropertyData.qual_cd1 === 'Q' ? 'Qualified' : 'Unqualified',
              book_page: currentPropertyData.book_page || currentPropertyData.or_book_page,
              cin: currentPropertyData.cin || currentPropertyData.clerk_no,
              instrument_number: currentPropertyData.vi_doc_no || currentPropertyData.instrument_number,
              grantor_name: currentPropertyData.grantor_name,
              grantee_name: currentPropertyData.own_name || currentPropertyData.owner_name,
              price_per_sqft: currentPropertyData.sale_prc1 && currentPropertyData.tot_lvg_area ?
                Math.round(currentPropertyData.sale_prc1 / currentPropertyData.tot_lvg_area) : null
            });
          }

          // Use sdfData if available - filter out sales under $1000
          if (sdfData && sdfData.length > 0) {
            sdfData.forEach((sale: any) => {
              const salePrice = parseFloat(sale.sale_price || '0');
              if (salePrice >= 1000) {
                combinedSales.push({
                  sale_date: sale.sale_date,
                  sale_price: sale.sale_price,
                  sale_type: sale.sale_type || sale.deed_type || sale.sale_qualification || 'Warranty Deed',
                  sale_qualification: sale.sale_qualification || sale.qualified_sale || 'Qualified',
                  book: sale.book || sale.or_book,
                  page: sale.page || sale.or_page,
                  book_page: sale.book_page || (sale.book && sale.page ? `${sale.book}/${sale.page}` : null),
                  cin: sale.cin || sale.clerk_instrument_number,
                  instrument_number: sale.instrument_number || sale.instr_num,
                  doc_number: sale.doc_number || sale.document_number,
                  grantor_name: sale.grantor_name || sale.seller_name,
                  grantee_name: sale.grantee_name || sale.buyer_name || bcpaData?.owner_name,
                  is_arms_length: sale.is_arms_length !== false,
                  is_distressed: sale.is_distressed || false,
                  is_foreclosure: sale.is_foreclosure || sale.sale_type?.includes('Foreclosure') || false,
                  is_qualified_sale: sale.qualified_sale !== false,
                  record_link: sale.record_link || `https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx`,
                  subdivision_name: sale.subdivision_name || bcpaData?.subdivision,
                  price_per_sqft: sale.sale_price && bcpaData?.living_area ?
                    Math.round(sale.sale_price / bcpaData.living_area) : null
                });
              }
            });
          }

          // Sort by date descending
          combinedSales.sort((a: any, b: any) =>
            new Date(b.sale_date || 0).getTime() - new Date(a.sale_date || 0).getTime()
          );

          setSalesHistory(combinedSales);
        }
      } catch (error) {
        console.error('Error fetching sales history:', error);
        // Fallback to sdfData
        setSalesHistory(sdfData || []);
      } finally {
        setLoadingSales(false);
      }
    };

    fetchSalesHistory();
  }, [bcpaData, sdfData, currentPropertyData]);

  const formatCurrency = (value: number | string | undefined) => {
    if (!value) return 'N/A';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(num);
  };

  const formatDate = (date: string | undefined) => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatSqFt = (value: number | string | undefined) => {
    if (!value) return 'N/A';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return `${num.toLocaleString()} sq ft`;
  };

  // Get property use description
  const getPropertyUseDescription = (useCode: string | undefined) => {
    if (!useCode) return '';

    const useCodes: Record<string, string> = {
      '001': 'Single Family',
      '002': 'Mobile Home',
      '003': 'Multi-Family (2-9 units)',
      '004': 'Condominium',
      '008': 'Multi-Family (10+ units)',
      '100': 'Vacant Commercial',
      '101': 'Retail Store',
      '102': 'Office Building',
      // Add more as needed
    };

    return useCodes[useCode] || useCode;
  };

  return (
    <div className="space-y-6">
      {/* Owner Properties Selector */}
      {bcpaData?.owner_name && (
        <OwnerPropertiesSelector
          ownerName={bcpaData.owner_name}
          currentParcelId={bcpaData.parcel_id}
          onPropertySelect={handlePropertySelect}
        />
      )}

      {/* Property Assessment Values */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
            <Building className="w-5 h-5 mr-2 text-gold" />
            Property Assessment Values
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Left Column */}
            <div className="space-y-3">
              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600 flex items-center">
                  <MapPin className="w-3 h-3 mr-1" />
                  Site Address
                </span>
                <span className="text-sm font-medium text-navy text-right">
                  {bcpaData?.property_address_street || 'N/A'}<br/>
                  {bcpaData?.property_address_city &&
                    `${bcpaData.property_address_city}, FL ${bcpaData.property_address_zip || ''}`}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600 flex items-center">
                  <User className="w-3 h-3 mr-1" />
                  Property Owner
                </span>
                <span className="text-sm font-medium text-navy">
                  {bcpaData?.owner_name || 'N/A'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600 flex items-center">
                  <Hash className="w-3 h-3 mr-1" />
                  Parcel ID
                </span>
                <span className="text-sm font-medium text-navy font-mono">
                  {bcpaData?.parcel_id || 'N/A'}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600 flex items-center">
                  <Building className="w-3 h-3 mr-1" />
                  Property Use
                </span>
                <span className="text-sm font-medium text-navy">
                  {bcpaData?.property_use_code || 'N/A'}
                  {bcpaData?.property_use_code && (
                    <span className="text-xs text-gray-500 block">
                      {getPropertyUseDescription(bcpaData.property_use_code)}
                    </span>
                  )}
                </span>
              </div>
            </div>

            {/* Right Column - Values */}
            <div className="space-y-3">
              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600">Current Land Value</span>
                <span className="text-sm font-semibold text-green-600">
                  {formatCurrency(bcpaData?.land_value)}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600">Building/Improvement</span>
                <span className="text-sm font-semibold text-blue-600">
                  {formatCurrency(bcpaData?.building_value)}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600">Just/Market Value</span>
                <span className="text-sm font-semibold text-navy">
                  {formatCurrency(bcpaData?.market_value || bcpaData?.just_value)}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600">Assessed/SOH Value</span>
                <span className="text-sm font-semibold text-navy">
                  {formatCurrency(bcpaData?.assessed_value)}
                </span>
              </div>

              <div className="flex justify-between items-start border-b border-gray-100 pb-2">
                <span className="text-sm text-gray-600">Annual Tax</span>
                <span className="text-sm font-semibold text-red-600">
                  {formatCurrency(bcpaData?.tax_amount)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Sales History */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-gold" />
            Sales History
          </h3>

          {loadingSales ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin text-gold mr-2" />
              <span className="text-sm text-gray-500">Loading sales history...</span>
            </div>
          ) : salesHistory && salesHistory.length > 0 ? (
            <div className="space-y-4">
              {/* Header with total sales count */}
              <div className="flex items-center justify-between pb-2 border-b border-gray-200">
                <span className="text-sm font-medium text-navy">
                  {salesHistory.length} Sale Record{salesHistory.length > 1 ? 's' : ''}
                </span>
                <span className="text-xs text-gray-500 uppercase tracking-wider">
                  Sales History
                </span>
              </div>

              {/* Sales History Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="text-right py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-gray-600 uppercase tracking-wider">
                        Book/Page or CIN
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {salesHistory.map((sale: any, index: number) => (
                      <tr
                        key={index}
                        className={`border-b border-gray-50 hover:bg-gray-25 transition-colors ${
                          index === 0 ? 'bg-blue-25' : ''
                        }`}
                      >
                        <td className="py-3 px-3">
                          <div className="flex items-center">
                            <span className="text-sm font-medium text-navy">
                              {formatDate(sale.sale_date)}
                            </span>
                            {index === 0 && (
                              <Badge className="ml-2 bg-blue-100 text-blue-800 text-xs">
                                Most Recent
                              </Badge>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-3">
                          <span className="text-sm font-medium text-navy">
                            {sale.deed_type || sale.sale_type ||
                             (sale.sale_qualification?.includes('Deed') ? sale.sale_qualification : 'Warranty Deed')}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <span className="text-sm font-semibold text-green-600">
                            {formatCurrency(typeof sale.sale_price === 'string' ? parseFloat(sale.sale_price) : sale.sale_price)}
                          </span>
                          {sale.price_per_sqft && (
                            <span className="block text-sm font-medium text-gray-700 mt-1">
                              ${sale.price_per_sqft}/sq ft
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3">
                          {sale.book_page || sale.cin ? (
                            <div className="space-y-1">
                              {sale.book_page && (
                                <div className="flex items-center">
                                  <span className="text-xs text-gray-500 mr-1">Book/Page:</span>
                                  <span className="text-sm font-medium text-blue-600 font-mono">
                                    {sale.book_page}
                                  </span>
                                </div>
                              )}
                              {sale.cin && (
                                <div className="flex items-center">
                                  <span className="text-xs text-gray-500 mr-1">CIN:</span>
                                  <span className="text-sm font-medium text-blue-600 font-mono">
                                    {sale.cin}
                                  </span>
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="text-sm text-gray-500">N/A</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">No sales history available</p>
              <p className="text-xs text-gray-400 mt-1">
                Property may be newly constructed or have no recorded sales
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Quick Links */}
      <Card className="elegant-card border-l-4 border-gold">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
            <ExternalLink className="w-5 h-5 mr-2 text-gold" />
            Quick Links
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Google Maps Link */}
            <a
              href={`https://www.google.com/maps/search/${encodeURIComponent(
                `${bcpaData?.property_address_street || ''} ${bcpaData?.property_address_city || ''} FL ${bcpaData?.property_address_zip || ''}`
              )}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-gold hover:bg-gold-light transition-all group"
            >
              <div className="flex items-center">
                <MapPin className="w-5 h-5 mr-3 text-gold" />
                <div>
                  <span className="text-sm font-semibold text-navy block">View on Google Maps</span>
                  <span className="text-xs text-gray-600">Navigate to property location</span>
                </div>
              </div>
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-gold" />
            </a>

            {/* Broward County Property Appraiser Link */}
            <a
              href={`https://www.bcpa.net/RecInfo.asp?URL_Folio=${bcpaData?.parcel_id || ''}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-gold hover:bg-gold-light transition-all group"
            >
              <div className="flex items-center">
                <Building className="w-5 h-5 mr-3 text-gold" />
                <div>
                  <span className="text-sm font-semibold text-navy block">Property Appraiser</span>
                  <span className="text-xs text-gray-600">Official BCPA property record</span>
                </div>
              </div>
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-gold" />
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
}