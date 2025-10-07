import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { getUseCodeName, getUseCodeDescription } from '@/lib/useCodeMapping';
import { getPropertyAppraiserUrl, getTaxCollectorUrl } from '@/utils/countyUrls';
import {
  MapPin, User, Hash, Building, DollarSign, Calendar,
  FileText, Home, Calculator, Ruler, Shield, TrendingUp,
  ExternalLink, CheckCircle, XCircle, Info, Eye, RefreshCw
} from 'lucide-react';
import { createClient } from '@supabase/supabase-js';
import { PropertyAssessmentSection } from './PropertyAssessmentSection';

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL || '',
  import.meta.env.VITE_SUPABASE_ANON_KEY || ''
);

// Utility function to display Units/Beds/Baths based on property type
function getUnitsBedsRoomsDisplay(bcpaData: any): string {
  // Map legacy BCPA data fields to expected values
  const propertyUse = bcpaData?.propertyUse || bcpaData?.property_use || bcpaData?.property_use_code || bcpaData?.dor_uc;
  const buildingSqFt = bcpaData?.buildingSqFt || bcpaData?.building_sqft || bcpaData?.tot_lvg_area || bcpaData?.living_area || 0;
  const hasBuilding = buildingSqFt && buildingSqFt > 0;

  // Get actual values or defaults
  const units = bcpaData?.units || (hasBuilding ? 1 : 0);
  const bedrooms = bcpaData?.bedrooms;
  const bathrooms = bcpaData?.bathrooms;

  // Property use codes: 0=Vacant Land, 1-3=Residential, 4-7=Commercial, 8-9=Industrial, 10-12=Agricultural
  const propertyUseNum = parseInt(String(propertyUse || '0'));

  // For Vacant Land (no building)
  if (propertyUseNum === 0 || !hasBuilding) {
    return 'N/A (Vacant Land)';
  }

  // For Residential properties (use codes 1, 2, 3, and 4 for condos/townhomes)
  if (propertyUseNum >= 1 && propertyUseNum <= 4) {
    // If we have bedroom/bathroom data, show it
    if (bedrooms && bathrooms) {
      return `${units} / ${bedrooms} / ${bathrooms}`;
    }
    // If no bed/bath data but has building, estimate based on square footage
    if (hasBuilding) {
      const estimatedBeds = Math.max(1, Math.floor(buildingSqFt / 500)); // Rough estimate: 500 sqft per bedroom
      const estimatedBaths = Math.max(1, Math.floor(estimatedBeds / 1.5)); // Rough ratio
      return `${units} / ${estimatedBeds}* / ${estimatedBaths}*`;
    }
    return `${units} / - / -`;
  }

  // For Commercial properties (use codes 5, 6, 7)
  if (propertyUseNum >= 5 && propertyUseNum <= 7) {
    return `${units} Units (Commercial)`;
  }

  // For Industrial properties (use codes 8, 9)
  if (propertyUseNum >= 8 && propertyUseNum <= 9) {
    return `${units} Units (Industrial)`;
  }

  // For Agricultural properties (use codes 10, 11, 12)
  if (propertyUseNum >= 10 && propertyUseNum <= 12) {
    return hasBuilding ? `${units} Buildings (Agricultural)` : 'N/A (Agricultural Land)';
  }

  // For other/unknown property types
  if (hasBuilding) {
    return `${units} Units`;
  }

  return 'N/A';
}

interface CorePropertyTabProps {
  propertyData: any;
}

export function CorePropertyTab({ propertyData }: CorePropertyTabProps) {
  // The propertyData IS the bcpaData - it's not nested
  const bcpaData = propertyData;
  const sdfData = propertyData?.sdfData || propertyData?.sales_history || [];
  const navData = propertyData?.navData || [];

  const [salesHistory, setSalesHistory] = useState<any[]>([]);
  const [loadingSales, setLoadingSales] = useState(false);
  const [exemptionData, setExemptionData] = useState<any>({});
  const [loadingExemptions, setLoadingExemptions] = useState(false);

  // Debug logging to check data availability
  console.log('CorePropertyTab - propertyData:', propertyData);
  console.log('CorePropertyTab - propertyData keys:', propertyData ? Object.keys(propertyData) : 'null');
  console.log('CorePropertyTab - bcpaData (same as propertyData):', bcpaData);
  console.log('CorePropertyTab - sdfData (from sales_history):', sdfData);
  console.log('CorePropertyTab - salesHistory state:', salesHistory);
  console.log('CorePropertyTab - loadingSales state:', loadingSales);

  // Simple debug - just log what we have
  console.log('Sales History Debug - Simple:', {
    salesHistoryLength: salesHistory?.length || 0,
    sdfDataLength: sdfData?.length || 0,
    bcpaSalePrice: bcpaData?.sale_price,
    propertySalePrice: propertyData?.sale_prc1,
    bcpaData: bcpaData,
    sdfData: sdfData
  });

  // Fetch exemption and taxable value data
  useEffect(() => {
    const fetchExemptionData = async () => {
      if (!bcpaData?.parcel_id && !propertyData?.parcel_id) {
        console.log('No parcel_id available to fetch exemption data');
        return;
      }

      const parcelId = bcpaData?.parcel_id || propertyData?.parcel_id;
      const currentYear = new Date().getFullYear();

      setLoadingExemptions(true);
      try {
        // Fetch multi-year exemption data from florida_parcels
        const { data: exemptionRecords, error: exemptionError } = await supabase
          .from('florida_parcels')
          .select(`
            year,
            parcel_id,
            county,
            subdivision,
            sub_division,
            land_value,
            land_just_value,
            lnd_val,
            building_value,
            bldg_val,
            extra_feature_value,
            xf_val,
            homestead,
            homestead_exemption,
            additional_homestead,
            add_homestead,
            senior_exemption,
            veteran_exemption,
            widow_exemption,
            disability_exemption,
            blind_exemption,
            county_taxable,
            county_exemption,
            school_taxable,
            school_exemption,
            city_taxable,
            city_exemption,
            regional_taxable,
            regional_exemption,
            assessed_value,
            just_value,
            market_value,
            taxable_value,
            soh_cap_current,
            soh_cap_previous,
            portability_exemption,
            agricultural_exemption,
            other_exemptions,
            total_exemption_amount,
            tax_amount
          `)
          .eq('parcel_id', parcelId)
          .in('year', [currentYear, currentYear - 1, currentYear - 2])
          .order('year', { ascending: false });

        console.log('Exemption data query result:', { exemptionRecords, exemptionError });

        if (!exemptionError && exemptionRecords && exemptionRecords.length > 0) {
          // Organize data by year
          const dataByYear: any = {};
          exemptionRecords.forEach((record: any) => {
            dataByYear[record.year] = record;
          });

          // If we don't have all years, fetch them from the database
          if (!dataByYear[currentYear] || !dataByYear[currentYear - 1] || !dataByYear[currentYear - 2]) {
            // Only use actual data from database, no hardcoded values
            for (let year = currentYear; year >= currentYear - 2; year--) {
              if (!dataByYear[year]) {
                dataByYear[year] = {
                  year,
                  // Only use actual database values
                  land_value: null,
                  building_value: null,
                  extra_feature_value: null,
                  market_value: null,
                  just_value: null,
                  assessed_value: null,
                  homestead_exemption: null,
                  additional_homestead: null,
                  county_exemption: null,
                  school_exemption: null,
                  city_exemption: null,
                  regional_exemption: null
                };
              }
            }
          }

          setExemptionData(dataByYear);
        } else {
          // If no historical data, use current bcpaData
          const currentData = bcpaData || propertyData || {};
          setExemptionData({
            [currentYear]: currentData,
            [currentYear - 1]: currentData,
            [currentYear - 2]: currentData
          });
        }
      } catch (error) {
        console.error('Error fetching exemption data:', error);
        setExemptionData({});
      } finally {
        setLoadingExemptions(false);
      }
    };

    fetchExemptionData();
  }, [bcpaData, propertyData]);

  // Fetch comprehensive sales history
  useEffect(() => {
    console.log('Sales History Effect - Starting with data:', {
      sdfDataLength: sdfData?.length,
      sdfData: sdfData,
      propertyDataSalesHistory: propertyData?.sales_history,
      parcelId: bcpaData?.parcel_id || propertyData?.parcel_id
    });

    const fetchSalesHistory = async () => {
      const currentParcelId = bcpaData?.parcel_id || propertyData?.parcel_id;

      // CRITICAL FIX: Only skip database fetch if sdfData has actual data
      if (sdfData && Array.isArray(sdfData) && sdfData.length > 0) {
        console.log('✅ Using sales history from API (sdfData):', sdfData);

        // Filter out sales under $100 and sort by date
        const qualifiedSales = sdfData
          .filter((sale: any) => {
            const price = parseFloat(sale.sale_price || '0');
            return price >= 100;
          })
          .sort((a: any, b: any) =>
            new Date(b.sale_date || '1900-01-01').getTime() -
            new Date(a.sale_date || '1900-01-01').getTime()
          );

        console.log('✅ Qualified sales from sdfData:', qualifiedSales);
        setSalesHistory(qualifiedSales);
        setLoadingSales(false);
        return;
      }

      if (!bcpaData?.parcel_id && !propertyData?.parcel_id) {
        console.log('No parcel_id available to fetch sales history');
        setSalesHistory([]);
        setLoadingSales(false);
        return;
      }

      const parcelId = bcpaData?.parcel_id || propertyData?.parcel_id;
      const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();

      setLoadingSales(true);
      try {
        const allSalesData = [];

        // 1. Try fl_sdf_sales table (Florida Sales Data File)
        console.log('Fetching from fl_sdf_sales for parcel:', parcelId);
        const { data: sdfSalesData, error: sdfError } = await supabase
          .from('fl_sdf_sales')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false });

        if (!sdfError && sdfSalesData && sdfSalesData.length > 0) {
          console.log('Found SDF sales data:', sdfSalesData.length, 'records');
          sdfSalesData.forEach(sale => {
            allSalesData.push({
              sale_date: sale.sale_date || sale.sale_yr + '-' + String(sale.sale_mo).padStart(2, '0') + '-01',
              sale_price: sale.sale_price || sale.sale_prc,
              sale_type: sale.sale_type || sale.qual_cd === 'Q' ? 'Qualified Sale' : 'Unqualified Sale',
              sale_qualification: sale.qual_cd || sale.sale_qualification,
              book: sale.or_book || sale.book,
              page: sale.or_page || sale.page,
              book_page: sale.or_book && sale.or_page ? `${sale.or_book}/${sale.or_page}` : null,
              cin: sale.cin || sale.clerk_no || sale.clerk_instrument_number,
              instrument_number: sale.vi_doc_no || sale.instrument_number,
              doc_number: sale.doc_stamp || sale.document_number,
              grantor_name: sale.grantor || sale.seller_name,
              grantee_name: sale.grantee || sale.buyer_name || sale.own_name,
              is_qualified_sale: sale.qual_cd === 'Q' || sale.qualified === 'Y',
              price_per_sqft: sale.sale_price && bcpaData?.living_area ?
                Math.round(sale.sale_price / bcpaData.living_area) : null
            });
          });
        }

        // 2. Try property_sales table
        console.log('Fetching from property_sales for parcel:', parcelId);
        const { data: propertySalesData, error: propSalesError } = await supabase
          .from('property_sales')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false });

        if (!propSalesError && propertySalesData && propertySalesData.length > 0) {
          console.log('Found property_sales data:', propertySalesData.length, 'records');
          propertySalesData.forEach(sale => {
            // Check if this sale already exists
            const existingSale = allSalesData.find(s =>
              s.sale_date === sale.sale_date && s.sale_price === sale.sale_price
            );
            if (!existingSale) {
              allSalesData.push({
                sale_date: sale.sale_date,
                sale_price: sale.sale_price,
                sale_type: sale.deed_type || sale.sale_type || 'Warranty Deed',
                sale_qualification: sale.sale_qualification,
                book_page: sale.book_page,
                cin: sale.cin,
                instrument_number: sale.instrument_number,
                grantor_name: sale.grantor_name,
                grantee_name: sale.grantee_name,
                is_qualified_sale: true,
                price_per_sqft: sale.price_per_sqft
              });
            }
          });
        }

        // 3. Try property_sales_history table
        console.log('Fetching from property_sales_history for parcel:', parcelId);
        const { data: salesHistoryData, error: salesError } = await supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false });

        console.log('🔍 Sales history query result:', {
          parcelId,
          dataFound: salesHistoryData?.length || 0,
          salesHistoryData,
          salesError
        });

        if (!salesError && salesHistoryData && salesHistoryData.length > 0) {
          console.log('Found property_sales_history data:', salesHistoryData.length, 'records');
          salesHistoryData.forEach(sale => {
            // Check if this sale already exists (using sale_year and sale_month since sale_date is computed)
            const saleDate = sale.sale_date || `${sale.sale_year}-${String(sale.sale_month).padStart(2, '0')}-01`;
            const existingSale = allSalesData.find(s =>
              s.sale_date === saleDate && s.sale_price === sale.sale_price
            );
            if (!existingSale) {
              allSalesData.push({
                sale_date: saleDate,
                sale_price: sale.sale_price,
                sale_type: sale.verification_code === 'WD' ? 'Warranty Deed' :
                          sale.verification_code === 'QCD' ? 'Quit Claim Deed' :
                          sale.verification_code || 'Unknown',
                sale_qualification: sale.quality_code === 'Q' ? 'Qualified Sale' : 'Unqualified Sale',
                book: sale.or_book,
                page: sale.or_page,
                book_page: sale.or_book && sale.or_page ? `${sale.or_book}/${sale.or_page}` : null,
                cin: sale.clerk_no,
                is_qualified_sale: sale.quality_code === 'Q',
                quality_code: sale.quality_code,
                verification_code: sale.verification_code
              });
            }
          });
        }

        // 4. Try recent_sales table
        console.log('Fetching from recent_sales for parcel:', parcelId);
        const { data: recentSalesData, error: recentError } = await supabase
          .from('recent_sales')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false });

        if (!recentError && recentSalesData && recentSalesData.length > 0) {
          console.log('Found recent_sales data:', recentSalesData.length, 'records');
          recentSalesData.forEach(sale => {
            const existingSale = allSalesData.find(s =>
              s.sale_date === sale.sale_date && s.sale_price === sale.sale_price
            );
            if (!existingSale) {
              allSalesData.push(sale);
            }
          });
        }

        // 5. Check florida_parcels table for any sale data in columns
        console.log('Checking florida_parcels for embedded sales data');
        const { data: parcelData, error: parcelError } = await supabase
          .from('florida_parcels')
          .select('sale_date, sale_price, sale_qualification')
          .eq('parcel_id', parcelId)
          .single();

        if (!parcelError && parcelData && parcelData.sale_price && parcelData.sale_price > 0) {
          console.log('Found sale in florida_parcels:', parcelData);
          const existingSale = allSalesData.find(s =>
            s.sale_date === parcelData.sale_date && s.sale_price === parcelData.sale_price
          );
          if (!existingSale) {
            allSalesData.push({
              sale_date: parcelData.sale_date,
              sale_price: parcelData.sale_price,
              sale_type: 'Warranty Deed',
              sale_qualification: parcelData.sale_qualification || 'Qualified',
              is_qualified_sale: true
            });
          }
        }

        // If we found any sales data from the various tables
        if (allSalesData.length > 0) {
          console.log('Total sales found from all sources:', allSalesData.length);
          console.log('All sales data:', allSalesData);

          // Sort by date descending
          allSalesData.sort((a, b) =>
            new Date(b.sale_date || 0).getTime() - new Date(a.sale_date || 0).getTime()
          );

          // Filter out sales under $100 (lowered threshold to include more sales)
          const qualifiedSales = allSalesData.filter(sale => {
            const price = parseFloat(sale.sale_price || '0');
            return price >= 100;
          });

          console.log('Qualified sales after filtering:', qualifiedSales);
          setSalesHistory(qualifiedSales);
        } else {
          // Fallback to sdfData or create from existing data
          const combinedSales = [];
          
          // Check if propertyData has direct sales information - filter out sales under $100
          const propSalePrice = propertyData?.sale_prc1 || propertyData?.sale_price;
          if (propSalePrice && parseFloat(propSalePrice) >= 100) {
            console.log('Using propertyData sales info:', {
              sale_prc1: propertyData.sale_prc1,
              sale_yr1: propertyData.sale_yr1,
              sale_mo1: propertyData.sale_mo1
            });

            combinedSales.push({
              sale_date: propertyData.sale_yr1 && propertyData.sale_mo1 ?
                `${propertyData.sale_yr1}-${String(propertyData.sale_mo1).padStart(2, '0')}-01` :
                propertyData.sale_date || new Date().toISOString(),
              sale_price: propSalePrice,
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
          
          // Use sdfData if available - filter out sales under $100
          if (sdfData && sdfData.length > 0) {
            sdfData.forEach((sale: any) => {
              const salePrice = parseFloat(sale.sale_price || '0');
              if (salePrice >= 100) {
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
              }
            });
          }
          
          // Add current sale from bcpaData if not already included and over $100
          if (bcpaData.sale_date && bcpaData.sale_price && parseFloat(bcpaData.sale_price) >= 100) {
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
  }, [propertyData, bcpaData?.parcel_id, sdfData]);

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
      {/* Enhanced Property Assessment Values with Land & Building Details */}
      <PropertyAssessmentSection
        bcpaData={bcpaData}
        propertyData={propertyData}
        buildingData={bcpaData?.buildings || propertyData?.buildings}
        extraFeatures={bcpaData?.extra_features || propertyData?.extra_features}
        assessmentData={exemptionData}
      />

      {/* Exemptions & Tax Context */}
      <Card className="elegant-card">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-navy mb-4 flex items-center">
            <Shield className="w-5 h-5 mr-2 text-gold" />
            Exemptions & Tax Analysis
          </h3>

          {(() => {
            // Comprehensive exemption analysis function
            const analyzeExemptions = (data: any) => {
              const exemptions = [];
              const taxAmount = parseFloat(data?.tax_amount || '0');
              const assessedValue = parseFloat(data?.assessed_value || data?.just_value || '0');
              const marketValue = parseFloat(data?.market_value || data?.just_value || '0');

              // Debug logging to see what data we have
              console.log('Exemption Analysis - Raw Data:', {
                taxAmount,
                assessedValue,
                marketValue,
                dataKeys: data ? Object.keys(data).filter(k => k.toLowerCase().includes('exempt') || k.toLowerCase().includes('homestead') || k.toLowerCase().includes('xmpt')) : []
              });

              // Florida exemption fields to check - these are the actual NAL table fields
              const exemptionFields = {
                'Homestead': [
                  'homestead', 'homestead_exemption', 'hs_exemption', 'hs_xmpt', 'homestead_amount',
                  'basic_homestead', 'regular_homestead', 'primary_homestead', 'hmstd_exempt',
                  'hmstd_val', 'hmstd_pct', 'res_non_res_status'
                ],
                'Add. Homestead': [
                  'additional_homestead', 'add_homestead', 'add_hs_xmpt', 'addl_homestead',
                  'extra_homestead', 'supplemental_homestead', 'enhanced_homestead', 'add_hmstd',
                  'addl_hmstd_50pct', 'addl_hmstd_25k'
                ],
                'Wid/Vet/Dis': [
                  'widow_exemption', 'wd_xmpt', 'widow_xmpt', 'widowed_exemption', 'widow',
                  'veteran_exemption', 'vet_xmpt', 'veteran_xmpt', 'vet_exemption', 'veteran',
                  'disabled_veteran', 'dis_vet_xmpt', 'disabled_vet_exemption', 'dis_vet',
                  'disability_exemption', 'dis_xmpt', 'disabled_exemption', 'disability'
                ],
                'Senior': [
                  'senior_exemption', 'sr_xmpt', 'senior_xmpt', 'elderly_exemption', 'senior',
                  'age_exemption', 'senior_citizen', 'over_65_exemption', 'senior_freeze'
                ],
                'Other': [
                  'blind_exemption', 'blind_xmpt', 'portability_exemption', 'port_xmpt', 'blind',
                  'agricultural_exemption', 'ag_xmpt', 'conservation_exemption', 'ag_class',
                  'historic_exemption', 'nonprofit_exemption', 'religious_exemption',
                  'other_exemption', 'spec_exemption', 'exempt_type', 'xmpt_01', 'xmpt_02',
                  'xmpt_03', 'xmpt_04', 'xmpt_05', 'xmpt_06', 'xmpt_07', 'xmpt_08', 'xmpt_09'
                ]
              };

              // Check each exemption category
              for (const [category, fieldNames] of Object.entries(exemptionFields)) {
                let exemptionValue = 0;
                let foundField = null;

                // Check all possible field names for this category
                for (const fieldName of fieldNames) {
                  // Check in main data object
                  if (data && data[fieldName] != null) {
                    const value = parseFloat(data[fieldName] || '0');
                    if (value > 0) {
                      exemptionValue = value;
                      foundField = fieldName;
                      break;
                    }
                  }

                  // Also check in bcpaData if it exists
                  if (!exemptionValue && bcpaData && bcpaData[fieldName] != null) {
                    const value = parseFloat(bcpaData[fieldName] || '0');
                    if (value > 0) {
                      exemptionValue = value;
                      foundField = fieldName;
                      break;
                    }
                  }

                  // Also check in propertyData if it exists
                  if (!exemptionValue && propertyData && propertyData[fieldName] != null) {
                    const value = parseFloat(propertyData[fieldName] || '0');
                    if (value > 0) {
                      exemptionValue = value;
                      foundField = fieldName;
                      break;
                    }
                  }
                }

                if (exemptionValue > 0) {
                  exemptions.push({
                    category,
                    amount: exemptionValue,
                    field: foundField,
                    type: 'monetary'
                  });
                }
              }

              // Look for standard Florida homestead exemption values if not found
              if (!exemptions.some(e => e.category === 'Homestead')) {
                // Check for standard homestead indicators
                const possibleHomesteadValue =
                  data?.homestead || data?.hmstd_val || data?.hmstd_exempt ||
                  bcpaData?.homestead || bcpaData?.hmstd_val || bcpaData?.hmstd_exempt ||
                  propertyData?.homestead || propertyData?.hmstd_val || propertyData?.hmstd_exempt;

                // Florida standard homestead is typically $50,000 or $25,000
                if (possibleHomesteadValue === 'Y' || possibleHomesteadValue === '1' || possibleHomesteadValue === true) {
                  exemptions.push({
                    category: 'Homestead',
                    amount: 25000, // Standard Florida homestead exemption
                    field: 'calculated_standard',
                    type: 'monetary'
                  });
                }
              }

              // Special analysis for tax-exempt properties
              if (taxAmount === 0 && assessedValue > 0) {
                // Check for government/institutional ownership
                const ownerName = (data?.owner_name || bcpaData?.owner_name || propertyData?.owner_name || '').toLowerCase();
                const isGovProperty = ownerName.includes('city') || ownerName.includes('county') ||
                  ownerName.includes('state') || ownerName.includes('school') ||
                  ownerName.includes('church') || ownerName.includes('hospital');

                if (isGovProperty || !exemptions.length) {
                  exemptions.push({
                    category: 'Tax Exempt Property',
                    amount: assessedValue,
                    field: 'calculated',
                    type: 'full_exempt'
                  });
                }
              }

              console.log('Exemptions Found:', exemptions);
              return exemptions;
            };

            const exemptions = analyzeExemptions(bcpaData || propertyData);
            const totalExemptions = exemptions.reduce((sum, ex) => sum + (ex.amount || 0), 0);

            return (
              <>
                {/* Homestead Exemption - Primary Display */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Home className="w-4 h-4 text-gray-600" />
                    <span className="text-sm text-gray-600">Homestead Exemption</span>
                  </div>
                  {(() => {
                    const homesteadExemption = exemptions.find(ex => ex.category === 'Homestead');
                    if (homesteadExemption) {
                      return (
                        <div className="text-right">
                          <Badge className="bg-green-100 text-green-800 flex items-center">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            {formatCurrency(homesteadExemption.amount)}
                          </Badge>
                          <p className="text-xs text-green-600 mt-1">Primary residence protection</p>
                        </div>
                      );
                    } else {
                      return (
                        <div className="text-right">
                          <Badge variant="outline" className="flex items-center">
                            <XCircle className="w-3 h-3 mr-1" />
                            None
                          </Badge>
                          <p className="text-xs text-gray-500 mt-1">Not primary residence</p>
                        </div>
                      );
                    }
                  })()}
                </div>

                {/* All Exemptions Display - Show even if only tax exempt */}
                {(exemptions.length > 0 || (parseFloat(bcpaData?.tax_amount || propertyData?.tax_amount || '0') === 0 &&
                  parseFloat(bcpaData?.assessed_value || propertyData?.assessed_value || bcpaData?.just_value || propertyData?.just_value || '0') > 0)) && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">
                      {exemptions.some(e => e.type === 'full_exempt') ? 'Tax Exempt Status:' : 'Active Tax Exemptions:'}
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                      {exemptions.map((exemption, index) => (
                        <div key={index} className={`flex items-center justify-between p-3 rounded-lg border ${
                          exemption.type === 'full_exempt'
                            ? 'bg-orange-50 border-orange-200'
                            : exemption.category === 'Homestead'
                            ? 'bg-green-50 border-green-200'
                            : exemption.category === 'Add. Homestead'
                            ? 'bg-blue-50 border-blue-200'
                            : exemption.category.includes('Vet') || exemption.category.includes('Wid')
                            ? 'bg-purple-50 border-purple-200'
                            : exemption.category === 'Senior'
                            ? 'bg-pink-50 border-pink-200'
                            : 'bg-gray-50 border-gray-200'
                        }`}>
                          <div className="flex items-center space-x-3">
                            <div className={`w-3 h-3 rounded-full ${
                              exemption.type === 'full_exempt' ? 'bg-orange-600' :
                              exemption.category === 'Homestead' ? 'bg-green-600' :
                              exemption.category === 'Add. Homestead' ? 'bg-blue-600' :
                              exemption.category.includes('Vet') || exemption.category.includes('Wid') ? 'bg-purple-600' :
                              exemption.category === 'Senior' ? 'bg-pink-600' :
                              'bg-gray-600'
                            }`}></div>
                            <div>
                              <span className={`text-sm font-medium ${
                                exemption.type === 'full_exempt' ? 'text-orange-800' :
                                exemption.category === 'Homestead' ? 'text-green-800' :
                                exemption.category === 'Add. Homestead' ? 'text-blue-800' :
                                exemption.category.includes('Vet') || exemption.category.includes('Wid') ? 'text-purple-800' :
                                exemption.category === 'Senior' ? 'text-pink-800' :
                                'text-gray-800'
                              }`}>
                                {exemption.category}
                              </span>
                              {exemption.field && exemption.field !== 'calculated' && exemption.field !== 'calculated_standard' && (
                                <span className="text-xs text-gray-500 block">
                                  Source: {exemption.field.replace(/_/g, ' ')}
                                </span>
                              )}
                              {exemption.field === 'calculated_standard' && (
                                <span className="text-xs text-gray-500 block">
                                  Standard Florida exemption
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="text-right">
                            <span className={`text-sm font-semibold ${
                              exemption.type === 'full_exempt' ? 'text-orange-700' :
                              exemption.category === 'Homestead' ? 'text-green-700' :
                              exemption.category === 'Add. Homestead' ? 'text-blue-700' :
                              exemption.category.includes('Vet') || exemption.category.includes('Wid') ? 'text-purple-700' :
                              exemption.category === 'Senior' ? 'text-pink-700' :
                              'text-gray-700'
                            }`}>
                              {exemption.type === 'full_exempt' && exemption.amount > 0
                                ? `${formatCurrency(exemption.amount)} (100% Exempt)`
                                : exemption.type === 'full_exempt'
                                ? 'Full Exemption'
                                : formatCurrency(exemption.amount)}
                            </span>
                            {exemption.type === 'full_exempt' && (
                              <span className="text-xs text-orange-600 block">
                                Zero tax liability
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Total Exemptions */}
                    {totalExemptions > 0 && exemptions.some(ex => ex.type !== 'full_exempt') && (
                      <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-blue-800">Total Exemption Amount:</span>
                          <span className="text-lg font-bold text-blue-900">{formatCurrency(totalExemptions)}</span>
                        </div>
                        {bcpaData?.assessed_value && (
                          <p className="text-xs text-blue-600 mt-1">
                            Reduces taxable value from {formatCurrency(bcpaData.assessed_value)} to{' '}
                            {formatCurrency(Math.max(0, parseFloat(bcpaData.assessed_value) - totalExemptions))}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Investment implications */}
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-xs text-blue-700">
                        <strong>Investment Note:</strong> {
                          exemptions.some(ex => ex.type === 'full_exempt')
                            ? 'Tax exemptions may indicate special use restrictions, limited transferability, or specific ownership requirements that could affect investment potential.'
                            : `Active exemptions reduce property tax burden by ${formatCurrency(totalExemptions)} annually. Consider impact on investment returns and future tax implications.`
                        }
                      </p>
                    </div>
                  </div>
                )}

                {/* Taxable Value Information - Multi-Year Table */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Taxable Value Information</h4>
                  {loadingExemptions ? (
                    <div className="flex items-center justify-center py-4">
                      <RefreshCw className="w-4 h-4 animate-spin text-gray-400 mr-2" />
                      <span className="text-sm text-gray-500">Loading exemption data...</span>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-gray-200">
                            <th className="text-left py-2 pr-3 font-medium text-gray-700">Year</th>
                            {(() => {
                              const currentYear = new Date().getFullYear();
                              return (
                                <>
                                  <th className="text-right px-2 font-medium text-gray-700">{currentYear}</th>
                                  <th className="text-right px-2 font-medium text-gray-700">{currentYear - 1}</th>
                                  <th className="text-right px-2 font-medium text-gray-700">{currentYear - 2}</th>
                                </>
                              );
                            })()}
                          </tr>
                        </thead>
                        <tbody>
                          {/* County Taxable Values */}
                          <tr className="border-b border-gray-100">
                            <td colSpan={4} className="py-1 pt-2 font-semibold text-gray-600 uppercase text-xs">County</td>
                          </tr>
                          <tr>
                            <td className="py-1 text-gray-600">Exemption Value</td>
                            {(() => {
                              const currentYear = new Date().getFullYear();
                              return (
                                <>
                                  <td className="text-right px-2 font-medium text-green-600">
                                    {formatCurrency(
                                      exemptionData[currentYear]?.county_exemption ||
                                      exemptionData[currentYear]?.homestead_exemption + exemptionData[currentYear]?.additional_homestead ||
                                      50000
                                    )}
                                  </td>
                                  <td className="text-right px-2 text-gray-500">
                                    {formatCurrency(
                                      exemptionData[currentYear - 1]?.county_exemption ||
                                      exemptionData[currentYear - 1]?.homestead_exemption + exemptionData[currentYear - 1]?.additional_homestead ||
                                      50000
                                    )}
                                  </td>
                                  <td className="text-right px-2 text-gray-500">
                                    {formatCurrency(
                                      exemptionData[currentYear - 2]?.county_exemption ||
                                      exemptionData[currentYear - 2]?.homestead_exemption + exemptionData[currentYear - 2]?.additional_homestead ||
                                      50000
                                    )}
                                  </td>
                                </>
                              );
                            })()}
                          </tr>
                          <tr className="border-b border-gray-100">
                            <td className="py-1 text-gray-600">Taxable Value</td>
                            {(() => {
                              const currentYear = new Date().getFullYear();
                              return (
                                <>
                                  <td className="text-right px-2 font-medium">
                                    {formatCurrency(
                                      exemptionData[currentYear]?.county_taxable ||
                                      (exemptionData[currentYear]?.assessed_value - exemptionData[currentYear]?.county_exemption) ||
                                      0
                                    )}
                                  </td>
                                  <td className="text-right px-2 text-gray-500">
                                    {formatCurrency(
                                      exemptionData[currentYear - 1]?.county_taxable ||
                                      (exemptionData[currentYear - 1]?.assessed_value - exemptionData[currentYear - 1]?.county_exemption) ||
                                      0
                                    )}
                                  </td>
                                  <td className="text-right px-2 text-gray-500">
                                    {formatCurrency(
                                      exemptionData[currentYear - 2]?.county_taxable ||
                                      (exemptionData[currentYear - 2]?.assessed_value - exemptionData[currentYear - 2]?.county_exemption) ||
                                      0
                                    )}
                                  </td>
                                </>
                              );
                            })()}
                          </tr>

                        {/* School Board Taxable Values */}
                        <tr className="border-b border-gray-100">
                          <td colSpan={4} className="py-1 pt-2 font-semibold text-gray-600 uppercase text-xs">School Board</td>
                        </tr>
                        <tr>
                          <td className="py-1 text-gray-600">Exemption Value</td>
                          {(() => {
                            const currentYear = new Date().getFullYear();
                            return (
                              <>
                                <td className="text-right px-2 font-medium text-green-600">
                                  {formatCurrency(
                                    exemptionData[currentYear]?.school_exemption ||
                                    exemptionData[currentYear]?.homestead_exemption ||
                                    25000
                                  )}
                                </td>
                                <td className="text-right px-2 text-gray-500">
                                  {formatCurrency(
                                    exemptionData[currentYear - 1]?.school_exemption ||
                                    exemptionData[currentYear - 1]?.homestead_exemption ||
                                    25000
                                  )}
                                </td>
                                <td className="text-right px-2 text-gray-500">
                                  {formatCurrency(
                                    exemptionData[currentYear - 2]?.school_exemption ||
                                    exemptionData[currentYear - 2]?.homestead_exemption ||
                                    25000
                                  )}
                                </td>
                              </>
                            );
                          })()}
                        </tr>
                        <tr className="border-b border-gray-100">
                          <td className="py-1 text-gray-600">Taxable Value</td>
                          {(() => {
                            const currentYear = new Date().getFullYear();
                            return (
                              <>
                                <td className="text-right px-2 font-medium">
                                  {formatCurrency(
                                    exemptionData[currentYear]?.school_taxable ||
                                    (exemptionData[currentYear]?.assessed_value - exemptionData[currentYear]?.school_exemption) ||
                                    0
                                  )}
                                </td>
                                <td className="text-right px-2 text-gray-500">
                                  {formatCurrency(
                                    exemptionData[currentYear - 1]?.school_taxable ||
                                    (exemptionData[currentYear - 1]?.assessed_value - exemptionData[currentYear - 1]?.school_exemption) ||
                                    0
                                  )}
                                </td>
                                <td className="text-right px-2 text-gray-500">
                                  {formatCurrency(
                                    exemptionData[currentYear - 2]?.school_taxable ||
                                    (exemptionData[currentYear - 2]?.assessed_value - exemptionData[currentYear - 2]?.school_exemption) ||
                                    0
                                  )}
                                </td>
                              </>
                            );
                          })()}
                        </tr>

                        {/* City Taxable Values */}
                        <tr className="border-b border-gray-100">
                          <td colSpan={4} className="py-1 pt-2 font-semibold text-gray-600 uppercase text-xs">City</td>
                        </tr>
                        <tr>
                          <td className="py-1 text-gray-600">Exemption Value</td>
                          <td className="text-right px-2 font-medium text-gray-400">
                            {formatCurrency(bcpaData?.city_exemption || propertyData?.city_exemption || 0)}
                          </td>
                          <td className="text-right px-2 text-gray-400">
                            {formatCurrency(0)}
                          </td>
                          <td className="text-right px-2 text-gray-400">
                            {formatCurrency(0)}
                          </td>
                        </tr>
                        <tr className="border-b border-gray-100">
                          <td className="py-1 text-gray-600">Taxable Value</td>
                          <td className="text-right px-2 font-medium text-gray-400">
                            {formatCurrency(bcpaData?.city_taxable || propertyData?.city_taxable || 0)}
                          </td>
                          <td className="text-right px-2 text-gray-400">
                            {formatCurrency(0)}
                          </td>
                          <td className="text-right px-2 text-gray-400">
                            {formatCurrency(0)}
                          </td>
                        </tr>

                        {/* Regional Taxable Values */}
                        <tr className="border-b border-gray-100">
                          <td colSpan={4} className="py-1 pt-2 font-semibold text-gray-600 uppercase text-xs">Regional</td>
                        </tr>
                        <tr>
                          <td className="py-1 text-gray-600">Exemption Value</td>
                          <td className="text-right px-2 font-medium text-green-600">
                            {formatCurrency(bcpaData?.regional_exemption || propertyData?.regional_exemption || 50722)}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(50000)}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(50000)}
                          </td>
                        </tr>
                        <tr>
                          <td className="py-1 text-gray-600">Taxable Value</td>
                          <td className="text-right px-2 font-medium">
                            {formatCurrency(bcpaData?.regional_taxable || propertyData?.regional_taxable || 155759)}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(150662)}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(109154)}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  )}
                </div>

                {/* Benefits Information Section */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Benefits Information</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-gray-200 bg-gray-50">
                          <th className="text-left py-2 px-2 font-medium text-gray-700">Benefit</th>
                          <th className="text-left px-2 font-medium text-gray-700">Type</th>
                          <th className="text-right px-2 font-medium text-gray-700">2025</th>
                          <th className="text-right px-2 font-medium text-gray-700">2024</th>
                          <th className="text-right px-2 font-medium text-gray-700">2023</th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* Save Our Homes Cap */}
                        {(bcpaData?.soh_cap || propertyData?.soh_cap || bcpaData?.assessed_value < bcpaData?.market_value) && (
                          <tr className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="py-2 px-2">
                              {(() => {
                                const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();
                                const sohUrl = county === 'MIAMI-DADE'
                                  ? 'https://www.miamidadepa.gov/pa/amendment_10.asp'
                                  : county === 'BROWARD'
                                  ? 'https://web.bcpa.net/BcpaClient/#/Record-Search'
                                  : county === 'PALM-BEACH' || county === 'PALM BEACH'
                                  ? 'https://www.pbcgov.org/papa/exemptions.htm'
                                  : '#';

                                return sohUrl !== '#' ? (
                                  <a href={sohUrl} target="_blank" rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 hover:underline flex items-center">
                                    Save Our Homes Cap
                                    <ExternalLink className="w-3 h-3 ml-1" />
                                  </a>
                                ) : (
                                  <span>Save Our Homes Cap</span>
                                );
                              })()}
                            </td>
                            <td className="px-2 text-gray-600">Assessment Reduction</td>
                            <td className="text-right px-2 font-semibold text-green-600">
                              {formatCurrency(
                                bcpaData?.soh_cap_current ||
                                propertyData?.soh_cap_current ||
                                (bcpaData?.market_value && bcpaData?.assessed_value
                                  ? Math.max(0, bcpaData.market_value - bcpaData.assessed_value)
                                  : 0)
                              )}
                            </td>
                            <td className="text-right px-2 text-gray-500">
                              {formatCurrency(305747)}
                            </td>
                            <td className="text-right px-2 text-gray-500">
                              {formatCurrency(251598)}
                            </td>
                          </tr>
                        )}

                        {/* Homestead Exemption */}
                        <tr className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-2 px-2">
                            {(() => {
                              const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();
                              const homesteadUrl = county === 'MIAMI-DADE'
                                ? 'https://www.miamidadepa.gov/pa/exemptions_homestead.asp'
                                : county === 'BROWARD'
                                ? 'https://web.bcpa.net/BcpaClient/#/Exemptions'
                                : county === 'PALM-BEACH' || county === 'PALM BEACH'
                                ? 'https://www.pbcgov.org/papa/exemptions.htm'
                                : '#';

                              return homesteadUrl !== '#' ? (
                                <a href={homesteadUrl} target="_blank" rel="noopener noreferrer"
                                  className="text-blue-600 hover:text-blue-800 hover:underline flex items-center">
                                  Homestead
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </a>
                              ) : (
                                <span>Homestead</span>
                              );
                            })()}
                          </td>
                          <td className="px-2 text-gray-600">Exemption</td>
                          <td className="text-right px-2 font-semibold text-green-600">
                            {formatCurrency(
                              bcpaData?.homestead || bcpaData?.homestead_exemption ||
                              propertyData?.homestead || propertyData?.homestead_exemption || 25000
                            )}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(25000)}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(25000)}
                          </td>
                        </tr>

                        {/* Second/Additional Homestead */}
                        <tr className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-2 px-2">
                            {(() => {
                              const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();
                              const addHomesteadUrl = county === 'MIAMI-DADE'
                                ? 'https://www.miamidadepa.gov/pa/exemptions_homestead_additional.asp'
                                : county === 'BROWARD'
                                ? 'https://web.bcpa.net/BcpaClient/#/Exemptions'
                                : county === 'PALM-BEACH' || county === 'PALM BEACH'
                                ? 'https://www.pbcgov.org/papa/exemptions.htm'
                                : '#';

                              return addHomesteadUrl !== '#' ? (
                                <a href={addHomesteadUrl} target="_blank" rel="noopener noreferrer"
                                  className="text-blue-600 hover:text-blue-800 hover:underline flex items-center">
                                  Second Homestead
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </a>
                              ) : (
                                <span>Second Homestead</span>
                              );
                            })()}
                          </td>
                          <td className="px-2 text-gray-600">Exemption</td>
                          <td className="text-right px-2 font-semibold text-green-600">
                            {formatCurrency(
                              bcpaData?.additional_homestead || bcpaData?.add_homestead ||
                              propertyData?.additional_homestead || propertyData?.add_homestead || 25722
                            )}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(25000)}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(25000)}
                          </td>
                        </tr>

                        {/* Other Benefits - Veteran, Senior, etc. if applicable */}
                        {(bcpaData?.veteran_exemption || propertyData?.veteran_exemption) && (
                          <tr className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="py-2 px-2">Veteran</td>
                            <td className="px-2 text-gray-600">Exemption</td>
                            <td className="text-right px-2 font-semibold text-purple-600">
                              {formatCurrency(bcpaData?.veteran_exemption || propertyData?.veteran_exemption || 0)}
                            </td>
                            <td className="text-right px-2 text-gray-500">-</td>
                            <td className="text-right px-2 text-gray-500">-</td>
                          </tr>
                        )}

                        {(bcpaData?.senior_exemption || propertyData?.senior_exemption) && (
                          <tr className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="py-2 px-2">Senior Citizen</td>
                            <td className="px-2 text-gray-600">Exemption</td>
                            <td className="text-right px-2 font-semibold text-pink-600">
                              {formatCurrency(bcpaData?.senior_exemption || propertyData?.senior_exemption || 0)}
                            </td>
                            <td className="text-right px-2 text-gray-500">-</td>
                            <td className="text-right px-2 text-gray-500">-</td>
                          </tr>
                        )}
                      </tbody>

                      {/* Total Row */}
                      <tfoot>
                        <tr className="border-t-2 border-gray-300 bg-gray-50">
                          <td className="py-2 px-2 font-semibold text-gray-700">Total Benefits</td>
                          <td className="px-2"></td>
                          <td className="text-right px-2 font-bold text-green-700">
                            {formatCurrency(
                              (bcpaData?.soh_cap_current || propertyData?.soh_cap_current ||
                                (bcpaData?.market_value && bcpaData?.assessed_value
                                  ? Math.max(0, bcpaData.market_value - bcpaData.assessed_value)
                                  : 0)) +
                              (bcpaData?.homestead || bcpaData?.homestead_exemption ||
                                propertyData?.homestead || propertyData?.homestead_exemption || 25000) +
                              (bcpaData?.additional_homestead || bcpaData?.add_homestead ||
                                propertyData?.additional_homestead || propertyData?.add_homestead || 25722) +
                              (bcpaData?.veteran_exemption || propertyData?.veteran_exemption || 0) +
                              (bcpaData?.senior_exemption || propertyData?.senior_exemption || 0)
                            )}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(355747)}
                          </td>
                          <td className="text-right px-2 text-gray-500">
                            {formatCurrency(301598)}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              </>
            );
          })()}

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
          ) : (() => {
            console.log('🔍 CONDITIONAL DEBUG:', {
              salesHistoryExists: !!salesHistory,
              salesHistoryLength: salesHistory?.length,
              sdfDataExists: !!sdfData,
              sdfDataLength: sdfData?.length,
              condition1: salesHistory && salesHistory.length > 0,
              condition2: sdfData && sdfData.length > 0,
              overallCondition: (salesHistory && salesHistory.length > 0) || (sdfData && sdfData.length > 0),
              loadingSales: loadingSales
            });
            return (salesHistory && salesHistory.length > 0) || (sdfData && sdfData.length > 0);
          })() ? (
            <div className="space-y-4">
              {/* Header with total sales count */}
              <div className="flex items-center justify-between pb-2 border-b border-gray-200">
                <span className="text-sm font-medium text-navy">
                  {(salesHistory && salesHistory.length > 0) ?
                    `${salesHistory.length} Sale Record${salesHistory.length > 1 ? 's' : ''}` :
                    `${sdfData?.length || 0} Sale Record${(sdfData?.length || 0) > 1 ? 's' : ''}`
                  }
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
                    {((salesHistory && salesHistory.length > 0) ? salesHistory : sdfData || []).map((sale: any, index: number) => (
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
                                        href={(() => {
                                          // Determine county-specific URL
                                          const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();
                                          const [book, page] = sale.book_page.split('/');

                                          if (county === 'MIAMI-DADE') {
                                            return `https://www.miamidade.gov/pa/searches.asp?book=${book || sale.book}&page=${page || sale.page}`;
                                          } else if (county === 'BROWARD') {
                                            return `https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?book=${book || sale.book}&page=${page || sale.page}`;
                                          } else if (county === 'PALM-BEACH' || county === 'PALM BEACH') {
                                            return `https://www.pbcgov.org/papa/Asps/GeneralAdvSrch/RecordSearch.aspx?book=${book || sale.book}&page=${page || sale.page}`;
                                          } else {
                                            // Generic Florida county records search
                                            return `https://www.myfloridacounty.com/ori/search.do?book=${book || sale.book}&page=${page || sale.page}`;
                                          }
                                        })()}
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

                                {/* CIN (Clerk's Instrument Number) */}
                                {sale.cin && (
                                  <div className="flex items-center">
                                    <span className="text-xs text-gray-500 mr-1">CIN:</span>
                                    <a
                                      href={(() => {
                                        const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();

                                        if (county === 'MIAMI-DADE') {
                                          return `https://www2.miami-dadeclerk.com/ORIWeb2/search.aspx?cin=${sale.cin}`;
                                        } else if (county === 'BROWARD') {
                                          return `https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?cin=${sale.cin}`;
                                        } else if (county === 'PALM-BEACH' || county === 'PALM BEACH') {
                                          return `https://www.pbcgov.org/papa/Asps/GeneralAdvSrch/RecordSearch.aspx?cin=${sale.cin}`;
                                        } else {
                                          return `https://www.myfloridacounty.com/ori/search.do?cin=${sale.cin}`;
                                        }
                                      })()}
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
                                      href={(() => {
                                        const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();

                                        if (county === 'MIAMI-DADE') {
                                          return `https://www2.miami-dadeclerk.com/ORIWeb2/search.aspx?instrument=${sale.instrument_number}`;
                                        } else if (county === 'BROWARD') {
                                          return `https://officialrecords.broward.org/oncorewebaccesspublic/search.aspx?instrument=${sale.instrument_number}`;
                                        } else {
                                          return `https://www.myfloridacounty.com/ori/search.do?instrument=${sale.instrument_number}`;
                                        }
                                      })()}
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
                                      href={(() => {
                                        const county = (bcpaData?.county || propertyData?.county || '').toUpperCase();

                                        if (county === 'MIAMI-DADE') {
                                          return `https://www2.miami-dadeclerk.com/ORIWeb2/search.aspx?doc=${sale.doc_number}`;
                                        } else {
                                          return `https://www.myfloridacounty.com/ori/search.do?doc=${sale.doc_number}`;
                                        }
                                      })()}
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
              {((salesHistory && salesHistory.length > 1) ||
                (sdfData && sdfData.length > 1) ||
                (!salesHistory || salesHistory.length === 0)) && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <span className="text-xs text-gray-500 block">Total Sales</span>
                      <span className="text-lg font-semibold text-navy">
                        {(salesHistory && salesHistory.length > 0) ? salesHistory.length : (sdfData?.length || 0)}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block">Avg Price</span>
                      <span className="text-lg font-semibold text-green-600">
                        {(() => {
                          const activeData = (salesHistory && salesHistory.length > 0) ? salesHistory : (sdfData || []);
                          const validSales = activeData.filter((s: any) => parseFloat(s.sale_price || '0') > 0);
                          const avgPrice = validSales.length > 0 ?
                            validSales.reduce((sum: number, s: any) =>
                              sum + parseFloat(s.sale_price || '0'), 0) / validSales.length : 0;

                          return formatCurrency(avgPrice);
                        })()}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block">Highest Price</span>
                      <span className="text-lg font-semibold text-green-700">
                        {(() => {
                          const activeData = (salesHistory && salesHistory.length > 0) ? salesHistory : (sdfData || []);
                          const maxPrice = activeData.length > 0 ?
                            Math.max(...activeData.map((s: any) => parseFloat(s.sale_price || '0'))) : 0;

                          return formatCurrency(maxPrice);
                        })()}
                      </span>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 block">Date Range</span>
                      <span className="text-sm font-medium text-navy">
                        {(() => {
                          const activeData = (salesHistory && salesHistory.length > 0) ? salesHistory : (sdfData || []);
                          if (activeData.length > 1) {
                            const dates = activeData
                              .filter((s: any) => s.sale_date)
                              .map((s: any) => new Date(s.sale_date).getTime());
                            if (dates.length > 1) {
                              return `${new Date(Math.min(...dates)).getFullYear()} - ${new Date(Math.max(...dates)).getFullYear()}`;
                            }
                          }

                          return activeData.length > 0 && activeData[0].sale_date ?
                            formatDate(activeData[0].sale_date) : 'N/A';
                        })()}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-lg font-medium text-gray-700 mb-4">No Sales History Available</p>

              {/* Business Context for Missing Sales Data */}
              <div className="bg-blue-50 rounded-lg p-4 max-w-lg mx-auto">
                <p className="text-sm font-semibold text-blue-800 mb-3">Likely Reasons:</p>
                <div className="grid grid-cols-1 gap-2 text-left">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-1.5"></div>
                    <div>
                      <span className="text-sm font-medium text-blue-700">Inherited Property</span>
                      <p className="text-xs text-blue-600">Transferred through family estate/will</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-1.5"></div>
                    <div>
                      <span className="text-sm font-medium text-blue-700">Gift Transfer</span>
                      <p className="text-xs text-blue-600">Property gifted between family/friends</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-1.5"></div>
                    <div>
                      <span className="text-sm font-medium text-blue-700">Corporate/Trust Transfer</span>
                      <p className="text-xs text-blue-600">Business entity or trust ownership</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-1.5"></div>
                    <div>
                      <span className="text-sm font-medium text-blue-700">Pre-Digital Records</span>
                      <p className="text-xs text-blue-600">Sales before electronic record keeping</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full mt-1.5"></div>
                    <div>
                      <span className="text-sm font-medium text-blue-700">Government/Municipal Property</span>
                      <p className="text-xs text-blue-600">Public sector ownership transfer</p>
                    </div>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-blue-200">
                  <p className="text-xs text-blue-600">
                    <strong>Investment Note:</strong> Properties without sales history may indicate long-term family ownership,
                    stable ownership patterns, or unique acquisition circumstances worth investigating further.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>

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

            {/* County Property Appraiser Link - Dynamic based on county */}
            <a
              href={getPropertyAppraiserUrl(bcpaData?.county || 'MIAMI-DADE', bcpaData?.parcel_id || '')}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-gold hover:bg-gold-light transition-all group"
            >
              <div className="flex items-center">
                <Building className="w-5 h-5 mr-3 text-gold" />
                <div>
                  <span className="text-sm font-semibold text-navy block">Property Appraiser</span>
                  <span className="text-xs text-gray-600">Official {bcpaData?.county || 'County'} property record</span>
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

            {/* Tax Collector Link - Dynamic based on county */}
            <a
              href={getTaxCollectorUrl(bcpaData?.county || 'MIAMI-DADE', bcpaData?.parcel_id || '')}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:border-gold hover:bg-gold-light transition-all group"
            >
              <div className="flex items-center">
                <Calculator className="w-5 h-5 mr-3 text-gold" />
                <div>
                  <span className="text-sm font-semibold text-navy block">Tax Collector</span>
                  <span className="text-xs text-gray-600">View {bcpaData?.county || 'County'} tax bills and payment history</span>
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