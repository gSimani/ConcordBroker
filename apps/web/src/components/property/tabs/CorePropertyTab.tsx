import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  MapPin, User, Hash, Building, DollarSign, Calendar, 
  FileText, Home, Calculator, Ruler, Shield, TrendingUp,
  ExternalLink, CheckCircle, XCircle, Info, Eye, RefreshCw
} from 'lucide-react';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

interface CorePropertyTabProps {
  propertyData: any;
}

export function CorePropertyTab({ propertyData }: CorePropertyTabProps) {
  const { bcpaData, sdfData, navData } = propertyData || {};
  const [salesHistory, setSalesHistory] = useState<any[]>([]);
  const [loadingSales, setLoadingSales] = useState(false);

  // Debug logging to check data availability
  console.log('CorePropertyTab - propertyData:', propertyData);
  console.log('CorePropertyTab - bcpaData:', bcpaData);
  console.log('CorePropertyTab - sdfData:', sdfData);

  // Fetch comprehensive sales history
  useEffect(() => {
    const fetchSalesHistory = async () => {
      if (!bcpaData?.parcel_id && !propertyData?.parcel_id) {
        console.log('No parcel_id available to fetch sales history');
        return;
      }
      
      const parcelId = bcpaData?.parcel_id || propertyData?.parcel_id;
      
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
          
          // Check if propertyData has direct sales information
          if (propertyData?.sale_prc1 || propertyData?.sale_price) {
            console.log('Using propertyData sales info:', {
              sale_prc1: propertyData.sale_prc1,
              sale_yr1: propertyData.sale_yr1,
              sale_mo1: propertyData.sale_mo1
            });
            
            combinedSales.push({
              sale_date: propertyData.sale_yr1 && propertyData.sale_mo1 ? 
                `${propertyData.sale_yr1}-${String(propertyData.sale_mo1).padStart(2, '0')}-01` : 
                propertyData.sale_date || new Date().toISOString(),
              sale_price: propertyData.sale_prc1 || propertyData.sale_price || 0,
              sale_type: propertyData.qual_cd1 === 'Q' ? 'Warranty Deed' : 
                propertyData.deed_type || propertyData.sale_type || 'Standard Sale',
              sale_qualification: propertyData.qual_cd1 === 'Q' ? 'Qualified' : 'Unqualified',
              book_page: propertyData.book_page || propertyData.or_book_page,
              cin: propertyData.cin || propertyData.clerk_no,
              instrument_number: propertyData.vi_doc_no || propertyData.instrument_number,
              grantor_name: propertyData.grantor_name,
              grantee_name: propertyData.own_name || propertyData.owner_name,
              price_per_sqft: propertyData.sale_prc1 && propertyData.tot_lvg_area ? 
                Math.round(propertyData.sale_prc1 / propertyData.tot_lvg_area) : null
            });
          }
          
          // Use sdfData if available
          if (sdfData && sdfData.length > 0) {
            sdfData.forEach((sale: any) => {
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
                grantee_name: sale.grantee_name || sale.buyer_name || bcpaData.owner_name,
                is_arms_length: sale.is_arms_length !== false,
                is_distressed: sale.is_distressed || false,
                is_foreclosure: sale.is_foreclosure || sale.sale_type?.includes('Foreclosure') || false,
                is_qualified_sale: sale.qualified_sale !== false,
                record_link: sale.record_link || `https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx`,
                subdivision_name: sale.subdivision_name || bcpaData.subdivision,
                price_per_sqft: sale.sale_price && bcpaData.living_area ? 
                  Math.round(sale.sale_price / bcpaData.living_area) : null
              });
            });
          }
          
          // Add current sale from bcpaData if not already included
          if (bcpaData.sale_date && bcpaData.sale_price) {
            const currentSaleExists = combinedSales.some((s: any) => 
              s.sale_date === bcpaData.sale_date && s.sale_price == bcpaData.sale_price
            );
            
            if (!currentSaleExists) {
              combinedSales.unshift({
                sale_date: bcpaData.sale_date,
                sale_price: bcpaData.sale_price,
                sale_type: bcpaData.sale_type || 'Warranty Deed',
                sale_qualification: 'Qualified',
                book_page: bcpaData.book_page,
                cin: bcpaData.cin,
                grantor_name: null,
                grantee_name: bcpaData.owner_name,
                is_arms_length: true,
                is_qualified_sale: true,
                record_link: `https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx`,
                subdivision_name: bcpaData.subdivision,
                price_per_sqft: bcpaData.sale_price && bcpaData.living_area ? 
                  Math.round(bcpaData.sale_price / bcpaData.living_area) : null
              });
            }
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
  }, [bcpaData, sdfData]);

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

      {/* Exemptions */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
            <Shield className="w-5 h-5 mr-2 text-gold" />
            Exemptions
          </h3>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Home className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-600">Homestead Exemption</span>
            </div>
            {bcpaData?.homestead_exemption ? (
              <Badge className="bg-green-100 text-green-800 flex items-center">
                <CheckCircle className="w-3 h-3 mr-1" />
                Active
              </Badge>
            ) : (
              <Badge variant="outline" className="flex items-center">
                <XCircle className="w-3 h-3 mr-1" />
                None
              </Badge>
            )}
          </div>
          
          {bcpaData?.other_exemptions && (
            <div className="mt-3 pt-3 border-t">
              <span className="text-sm text-gray-600">Other Exemptions:</span>
              <span className="text-sm font-medium text-navy ml-2">
                {bcpaData.other_exemptions}
              </span>
            </div>
          )}
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
                  Subdivision Sales
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
                    {salesHistory
                      .map((sale: any, index: number) => (
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
                            {(sale.sale_qualification && !sale.sale_qualification.includes('Deed')) && (
                              <span className="block text-xs text-gray-500">
                                {sale.sale_qualification}
                              </span>
                            )}
                            {sale.is_foreclosure && (
                              <span className="inline-block mt-1 px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded-full">
                                Foreclosure
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <span className={`text-sm font-semibold ${
                              (typeof sale.sale_price === 'string' ? parseFloat(sale.sale_price) : sale.sale_price) > 0 ? 'text-green-600' : 'text-gray-500'
                            }`}>
                              {(typeof sale.sale_price === 'string' ? parseFloat(sale.sale_price) : sale.sale_price) > 0 ? 
                                formatCurrency(typeof sale.sale_price === 'string' ? parseFloat(sale.sale_price) : sale.sale_price) : 'N/A'}
                            </span>
                            {/* Price per sq ft if available - BIGGER TEXT */}
                            {sale.price_per_sqft ? (
                              <span className="block text-sm font-medium text-gray-700 mt-1">
                                ${sale.price_per_sqft}/sq ft
                              </span>
                            ) : (
                              (typeof sale.sale_price === 'string' ? parseFloat(sale.sale_price) : sale.sale_price) > 0 && bcpaData?.living_area && (
                                <span className="block text-sm font-medium text-gray-700 mt-1">
                                  ${Math.round((typeof sale.sale_price === 'string' ? parseFloat(sale.sale_price) : sale.sale_price) / bcpaData.living_area)}/sq ft
                                </span>
                              )
                            )}
                          </td>
                          <td className="py-3 px-3">
                            {sale.book_page || sale.cin || sale.instrument_number || sale.doc_number ? (
                              <div className="space-y-1">
                                {/* Book/Page */}
                                {sale.book_page && (
                                  <div className="flex items-center">
                                    <div className="flex items-center">
                                      <span className="text-xs text-gray-500 mr-1">Book/Page:</span>
                                      <a
                                        href={`https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?book=${sale.book || sale.book_page.split('/')[0]}&page=${sale.page || sale.book_page.split('/')[1]}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline flex items-center font-mono"
                                      >
                                        {sale.book_page}
                                        <ExternalLink className="w-3 h-3 ml-1" />
                                      </a>
                                    </div>
                                    {sale.record_link && (
                                      <a 
                                        href={sale.record_link}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="ml-2 text-blue-600 hover:text-blue-800"
                                      >
                                        <ExternalLink className="w-3 h-3" />
                                      </a>
                                    )}
                                  </div>
                                )}
                                
                                {/* CIN */}
                                {sale.cin && (
                                  <div className="flex items-center">
                                    <span className="text-xs text-gray-500 mr-1">CIN:</span>
                                    <a
                                      href={`https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?cin=${sale.cin}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline flex items-center font-mono"
                                    >
                                      {sale.cin}
                                      <ExternalLink className="w-3 h-3 ml-1" />
                                    </a>
                                  </div>
                                )}

                                {/* Instrument Number */}
                                {sale.instrument_number && !sale.book_page && !sale.cin && (
                                  <div className="flex items-center">
                                    <span className="text-xs text-gray-500 mr-1">Inst:</span>
                                    <a
                                      href={`https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?instrument=${sale.instrument_number}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline flex items-center font-mono"
                                    >
                                      {sale.instrument_number}
                                      <ExternalLink className="w-3 h-3 ml-1" />
                                    </a>
                                  </div>
                                )}

                                {/* Document Number fallback */}
                                {sale.doc_number && !sale.book_page && !sale.cin && !sale.instrument_number && (
                                  <div className="flex items-center">
                                    <span className="text-xs text-gray-500 mr-1">Doc:</span>
                                    <a
                                      href={`https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?doc=${sale.doc_number}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline flex items-center font-mono"
                                    >
                                      {sale.doc_number}
                                      <ExternalLink className="w-3 h-3 ml-1" />
                                    </a>
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

              {/* Sales Summary */}
              {salesHistory.length > 1 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <span className="text-xs text-gray-500 block">Total Sales</span>
                      <span className="text-lg font-semibold text-navy">
                        {salesHistory.length}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block">Avg Price</span>
                      <span className="text-lg font-semibold text-green-600">
                        {formatCurrency(
                          salesHistory
                            .filter((s: any) => s.sale_price > 0)
                            .reduce((sum: number, s: any) => sum + (typeof s.sale_price === 'string' ? parseFloat(s.sale_price) : s.sale_price), 0) / 
                          salesHistory.filter((s: any) => s.sale_price > 0).length || 0
                        )}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block">Highest Price</span>
                      <span className="text-lg font-semibold text-green-700">
                        {formatCurrency(
                          Math.max(...salesHistory.map((s: any) => {
                            const price = typeof s.sale_price === 'string' ? parseFloat(s.sale_price) : s.sale_price;
                            return price || 0;
                          }))
                        )}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block">Date Range</span>
                      <span className="text-sm font-medium text-navy">
                        {salesHistory.length > 1 ? (
                          <>
                            {new Date(Math.min(...salesHistory.map((s: any) => new Date(s.sale_date).getTime()))).getFullYear()} - {' '}
                            {new Date(Math.max(...salesHistory.map((s: any) => new Date(s.sale_date).getTime()))).getFullYear()}
                          </>
                        ) : (
                          formatDate(salesHistory[0].sale_date)
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              )}
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

      {/* Land Calculations & Building Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Land Calculations */}
        <Card className="elegant-card">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
              <Ruler className="w-5 h-5 mr-2 text-gold" />
              Land Calculations
            </h3>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Land Area</span>
                <span className="text-sm font-semibold text-navy">
                  {formatSqFt(bcpaData?.lot_size_sqft)}
                </span>
              </div>
              
              {bcpaData?.land_factors && (
                <div className="mt-3 pt-3 border-t space-y-2">
                  <span className="text-xs text-gray-600 uppercase tracking-wider">Factors:</span>
                  {bcpaData.land_factors.map((factor: any, index: number) => (
                    <div key={index} className="flex justify-between items-center pl-3">
                      <span className="text-xs text-gray-500">{factor.description}</span>
                      <span className="text-xs font-medium">{formatSqFt(factor.size)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Building Details */}
        <Card className="elegant-card">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
              <Home className="w-5 h-5 mr-2 text-gold" />
              Building Details
            </h3>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Adj. Bldg. S.F.</span>
                <span className="text-sm font-semibold text-navy">
                  {formatSqFt(bcpaData?.living_area)}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Units/Beds/Baths</span>
                <span className="text-sm font-medium text-navy">
                  {bcpaData?.units || '1'} / {bcpaData?.bedrooms || '?'} / {bcpaData?.bathrooms || '?'}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Eff./Act. Year Built</span>
                <span className="text-sm font-medium text-navy">
                  {bcpaData?.eff_year_built || bcpaData?.year_built || 'N/A'} / {bcpaData?.year_built || 'N/A'}
                </span>
              </div>
              
              {bcpaData?.property_sketch_link && (
                <div className="mt-3 pt-3 border-t">
                  <a 
                    href={bcpaData.property_sketch_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-blue-600 hover:underline flex items-center"
                  >
                    <FileText className="w-3 h-3 mr-1" />
                    View Property Sketch
                    <ExternalLink className="w-3 h-3 ml-1" />
                  </a>
                </div>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Additional NAV Assessments if available */}
      {navData && navData.length > 0 && (
        <Card className="elegant-card">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
              <Info className="w-5 h-5 mr-2 text-gold" />
              Non-Ad Valorem Assessments
            </h3>
            <div className="text-sm text-gray-600">
              Total Annual Assessment: 
              <span className="font-semibold text-navy ml-2">
                {formatCurrency(navData.reduce((sum: number, nav: any) => sum + (parseFloat(nav.total_assessment) || 0), 0))}
              </span>
            </div>
          </div>
        </Card>
      )}

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

          {/* Additional Links Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {/* Street View Link */}
            <a
              href={`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${encodeURIComponent(
                `${bcpaData?.property_address_street || ''} ${bcpaData?.property_address_city || ''} FL`
              )}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-gold hover:bg-gold-light transition-all group"
            >
              <div className="flex items-center">
                <Eye className="w-5 h-5 mr-3 text-gold" />
                <div>
                  <span className="text-sm font-semibold text-navy block">Street View</span>
                  <span className="text-xs text-gray-600">View property from street level</span>
                </div>
              </div>
              <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-gold" />
            </a>

            {/* Tax Collector Link */}
            <a
              href={`https://broward.county-taxes.com/public/real_estate/parcels/${bcpaData?.parcel_id || ''}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-gold hover:bg-gold-light transition-all group"
            >
              <div className="flex items-center">
                <Calculator className="w-5 h-5 mr-3 text-gold" />
                <div>
                  <span className="text-sm font-semibold text-navy block">Tax Collector</span>
                  <span className="text-xs text-gray-600">View tax bills and payment history</span>
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