import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import { propertyApiClient } from '@/lib/property-api-client'

export interface PropertyData {
  bcpaData: any
  sdfData: any[]
  navData: any[]
  tppData: any[]
  sunbizData: any[]
  lastSale: any
  totalNavAssessment: number
  isInCDD: boolean
  investmentScore: number
  opportunities: string[]
  riskFactors: string[]
  dataQuality: {
    bcpa: boolean
    sdf: boolean
    nav: boolean
    tpp: boolean
    sunbiz: boolean
  }
}

export const usePropertyData = (addressOrParcelId: string, city: string = '') => {
  const [data, setData] = useState<PropertyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPropertyData = useCallback(async () => {
    console.log(`[usePropertyData] Starting fetch with:`, { addressOrParcelId, city });

    if (!addressOrParcelId) {
      console.log(`[usePropertyData] No addressOrParcelId provided, skipping fetch`);
      setLoading(false);
      return;
    }

    try {
      setLoading(true)
      setError(null)

      // Check if it's a parcel ID (numeric or alphanumeric pattern)
      const isParcelId = (/^\d+$/.test(addressOrParcelId) && addressOrParcelId.length >= 10) ||
                        (/^[A-Z0-9-]+$/i.test(addressOrParcelId.replace(/\s/g, '')) &&
                        addressOrParcelId.length > 8 &&
                        !/\b(st|street|rd|road|ave|avenue|ln|lane|ct|court|dr|drive|blvd|boulevard|pl|place|way|nw|ne|sw|se|north|south|east|west)\b/i.test(addressOrParcelId))

      console.log(`[usePropertyData] Processing:`, { addressOrParcelId, city, isParcelId });

      let parcelId = isParcelId ? addressOrParcelId : null
      let bcpaData: any = null
      let sdfData: any[] = []

      // Step 1: Get primary property data using API client
      if (isParcelId) {
        console.log(`[usePropertyData] Fetching by parcel ID: ${addressOrParcelId}`);
        try {
          // Use the property API client to fetch data
          const propertyDetail = await propertyApiClient.getPropertyDetail(addressOrParcelId, {
            includeSales: true,
            includeTax: true,
            includeSunbiz: true,
            includePermits: false,
            includeTaxDeeds: false,
            includeComparables: false
          });

          if (propertyDetail) {
            // Convert API response to bcpaData format
            bcpaData = {
              parcel_id: propertyDetail.parcel_id,
              phy_addr1: propertyDetail.address?.street,
              phy_city: propertyDetail.address?.city,
              phy_state: propertyDetail.address?.state,
              phy_zipcd: propertyDetail.address?.zip,
              owner_name: propertyDetail.owner?.name,
              owner_addr1: propertyDetail.owner?.address,
              owner_city: propertyDetail.owner?.city,
              owner_state: propertyDetail.owner?.state,
              owner_zip: propertyDetail.owner?.zip,
              just_value: propertyDetail.values?.market_value,
              assessed_value: propertyDetail.values?.assessed_value,
              taxable_value: propertyDetail.values?.taxable_value,
              land_value: propertyDetail.values?.land_value,
              building_value: propertyDetail.values?.building_value,
              year_built: propertyDetail.characteristics?.year_built,
              total_living_area: propertyDetail.characteristics?.living_area,
              bedrooms: propertyDetail.characteristics?.bedrooms,
              bathrooms: propertyDetail.characteristics?.bathrooms,
              land_sqft: propertyDetail.characteristics?.lot_size,
              sale_date: propertyDetail.sales?.last_sale_date,
              sale_price: propertyDetail.sales?.last_sale_price,
              sale_qualification: propertyDetail.sales?.sale_qualification,
              property_use: propertyDetail.characteristics?.use_code,
              county: propertyDetail.county,
              year: propertyDetail.year,
              ...propertyDetail._raw // Include raw data if available
            };
            parcelId = propertyDetail.parcel_id;
            console.log(`[usePropertyData] Found property via API:`, bcpaData);
          }
        } catch (error) {
          console.log(`[usePropertyData] API fetch error:`, error);
          // Fall back to direct Supabase query if API fails
          try {
            const { data: floridaData, error: floridaError } = await supabase
              .from('florida_parcels')
              .select('*')
              .eq('parcel_id', addressOrParcelId)
              .single();

            if (!floridaError && floridaData) {
              bcpaData = floridaData;
              parcelId = floridaData.parcel_id;
              console.log(`[usePropertyData] Found property in florida_parcels (fallback):`, floridaData);
            }
          } catch (fallbackError) {
            console.log(`[usePropertyData] Fallback error:`, fallbackError);
          }
        }
      } else {
        // Address-based lookup
        console.log(`[usePropertyData] Searching by address: ${addressOrParcelId}, ${city}`);
        try {
          const searchAddress = addressOrParcelId.replace(/-/g, ' ').trim().toUpperCase();

          let query = supabase
            .from('florida_parcels')
            .select('*')
            .ilike('phy_addr1', `%${searchAddress}%`);

          if (city) {
            query = query.ilike('phy_city', `%${city}%`);
          }

          const { data: floridaData, error: floridaError } = await query
            .limit(10);

          if (floridaError) {
            console.log(`[usePropertyData] Address search error: ${floridaError.message}`);
          } else if (floridaData && floridaData.length > 0) {
            // Find best match
            const upperAddress = searchAddress;
            bcpaData = floridaData.find(p =>
              p.phy_addr1?.toUpperCase().includes(upperAddress) ||
              p.phy_addr1?.toUpperCase() === upperAddress
            ) || floridaData[0];

            parcelId = bcpaData.parcel_id;
            console.log(`[usePropertyData] Found ${floridaData.length} properties, using:`, bcpaData);
          }
        } catch (error) {
          console.error(`[usePropertyData] Address search error:`, error);
        }
      }

      if (!bcpaData) {
        console.log(`[usePropertyData] Property not found for: ${addressOrParcelId}`);
        setError('Property not found in database');
        setData(null);
        setLoading(false);
        return;
      }

      // Step 2: Get comprehensive sales data (matching useSalesData pattern)
      console.log(`[usePropertyData] Fetching sales data for parcel: ${parcelId}`);
      const salesDataResults = await fetchSalesDataFromMultipleSources(parcelId);
      sdfData = salesDataResults;

      // Step 3: Get additional data sources
      const [navData, sunbizData] = await Promise.all([
        fetchNavData(parcelId),
        fetchSunbizDataForProperty(bcpaData.owner_name || '')
      ]);

      // Step 4: Process and calculate derived data
      const lastSale = findLastQualifiedSale(salesDataResults);
      const totalNavAssessment = navData.reduce((sum: number, nav: any) =>
        sum + (parseFloat(nav.total_assessment) || 0), 0);
      const isInCDD = totalNavAssessment > 1000;

      // Step 5: Calculate investment metrics
      const investmentScore = calculateInvestmentScore(
        bcpaData, lastSale, salesDataResults, navData
      );

      const { opportunities, riskFactors } = identifyOpportunitiesAndRisks(
        bcpaData, lastSale, salesDataResults, navData, sunbizData
      );

      // Step 6: Assemble final data structure
      const finalData: PropertyData = {
        bcpaData,
        sdfData: salesDataResults,
        navData,
        tppData: [],
        sunbizData,
        lastSale,
        totalNavAssessment,
        isInCDD,
        investmentScore,
        opportunities,
        riskFactors,
        dataQuality: {
          bcpa: !!bcpaData,
          sdf: salesDataResults.length > 0,
          nav: navData.length > 0,
          tpp: false,
          sunbiz: sunbizData.length > 0
        }
      };

      console.log(`[usePropertyData] Final data assembled for ${parcelId}:`, {
        salesCount: salesDataResults.length,
        navAssessment: totalNavAssessment,
        investmentScore,
        sunbizCount: sunbizData.length
      });

      setData(finalData);
    } catch (err) {
      console.error('[usePropertyData] Error fetching property data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch property data');
    } finally {
      setLoading(false);
    }
  }, [addressOrParcelId, city]);

  // Helper function to fetch sales data from multiple sources (matches useSalesData pattern)
  const fetchSalesDataFromMultipleSources = async (parcelId: string): Promise<any[]> => {
    const allSales: any[] = [];
    console.log(`[usePropertyData] Fetching sales from multiple sources for: ${parcelId}`);

    // Source 1: florida_parcels sales data
    try {
      const { data: parcelSales, error } = await supabase
        .from('florida_parcels')
        .select('sale_date, sale_price, sale_qualification')
        .eq('parcel_id', parcelId)
        .gte('sale_price', 1000)
        .not('sale_price', 'is', null);

      if (!error && parcelSales && parcelSales.length > 0) {
        const sales = parcelSales.map(sale => ({
          ...sale,
          data_source: 'florida_parcels',
          qualified_sale: sale.sale_qualification?.toLowerCase() === 'qualified'
        }));
        allSales.push(...sales);
        console.log(`[usePropertyData] Found ${sales.length} florida_parcels sales`);
      }
    } catch (error) {
      console.log(`[usePropertyData] Florida parcels sales error:`, error);
    }

    // Source 2: comprehensive_sales_data
    try {
      const { data: comprehensiveData, error } = await supabase
        .from('comprehensive_sales_data')
        .select('*')
        .eq('parcel_id', parcelId)
        .gte('sale_price', 1000)
        .order('sale_date', { ascending: false });

      if (!error && comprehensiveData && comprehensiveData.length > 0) {
        const sales = comprehensiveData.map(sale => ({
          ...sale,
          data_source: 'comprehensive_sales_data',
          qualified_sale: sale.sale_qualification?.toLowerCase() === 'qualified'
        }));
        allSales.push(...sales);
        console.log(`[usePropertyData] Found ${sales.length} comprehensive_sales_data sales`);
      }
    } catch (error) {
      console.log(`[usePropertyData] Comprehensive sales data error:`, error);
    }

    // Source 3: sdf_sales
    try {
      const { data: sdfData, error } = await supabase
        .from('sdf_sales')
        .select('*')
        .eq('parcel_id', parcelId)
        .gte('sale_price', 1000)
        .order('sale_date', { ascending: false });

      if (!error && sdfData && sdfData.length > 0) {
        const sales = sdfData.map(sale => ({
          ...sale,
          data_source: 'sdf_sales',
          qualified_sale: sale.qualified_sale === true
        }));
        allSales.push(...sales);
        console.log(`[usePropertyData] Found ${sales.length} sdf_sales records`);
      }
    } catch (error) {
      console.log(`[usePropertyData] SDF sales error:`, error);
    }

    // Source 4: sales_history
    try {
      const { data: historyData, error } = await supabase
        .from('sales_history')
        .select('*')
        .eq('parcel_id', parcelId)
        .gte('sale_price', 1000)
        .order('sale_date', { ascending: false });

      if (!error && historyData && historyData.length > 0) {
        const sales = historyData.map(sale => ({
          ...sale,
          data_source: 'sales_history',
          qualified_sale: sale.sale_type?.toLowerCase() === 'qualified'
        }));
        allSales.push(...sales);
        console.log(`[usePropertyData] Found ${sales.length} sales_history records`);
      }
    } catch (error) {
      console.log(`[usePropertyData] Sales history error:`, error);
    }

    // Remove duplicates based on date and price
    const uniqueSales = allSales.filter((sale, index, self) =>
      index === self.findIndex(s =>
        s.sale_date === sale.sale_date &&
        parseFloat(s.sale_price) === parseFloat(sale.sale_price)
      )
    );

    // Sort by date descending
    uniqueSales.sort((a, b) => new Date(b.sale_date).getTime() - new Date(a.sale_date).getTime());

    console.log(`[usePropertyData] Total unique sales: ${uniqueSales.length}`);
    return uniqueSales;
  };

  // Helper function to fetch NAV assessment data
  const fetchNavData = async (parcelId: string): Promise<any[]> => {
    try {
      const { data: navData, error } = await supabase
        .from('nav_assessments')
        .select('*')
        .eq('parcel_id', parcelId);

      if (error) {
        console.log(`[usePropertyData] NAV data error: ${error.message}`);
        return [];
      }

      return navData || [];
    } catch (error) {
      console.log(`[usePropertyData] NAV data fetch error:`, error);
      return [];
    }
  };

  // Helper function to fetch Sunbiz data
  const fetchSunbizDataForProperty = async (ownerName: string): Promise<any[]> => {
    if (!ownerName || ownerName.length < 3) return [];

    try {
      const { data: sunbizData, error } = await supabase
        .from('sunbiz_corporate')
        .select('*')
        .ilike('entity_name', `%${ownerName}%`)
        .eq('status', 'ACTIVE')
        .limit(5);

      if (error) {
        console.log(`[usePropertyData] Sunbiz data error: ${error.message}`);
        return [];
      }

      return sunbizData || [];
    } catch (error) {
      console.log(`[usePropertyData] Sunbiz data fetch error:`, error);
      return [];
    }
  };

  // Helper function to find last qualified sale
  const findLastQualifiedSale = (salesData: any[]): any => {
    const qualifiedSale = salesData.find(sale => {
      const salePrice = parseFloat(sale.sale_price || '0');
      return salePrice >= 1000 && sale.qualified_sale;
    });

    if (qualifiedSale) {
      return {
        ...qualifiedSale,
        sale_type: qualifiedSale.document_type || 'Warranty Deed',
        is_distressed: qualifiedSale.is_distressed || false,
        is_bank_sale: qualifiedSale.is_bank_sale || false,
        is_cash_sale: qualifiedSale.is_cash_sale || false
      };
    }

    // If no qualified sale, return the most recent sale over $1000
    return salesData.find(sale => parseFloat(sale.sale_price || '0') >= 1000) || null;
  };

  // Helper function to calculate investment score
  const calculateInvestmentScore = (
    property: any, lastSale: any, salesHistory: any[], navData: any[]
  ): number => {
    let score = 50;

    // Value-based scoring
    const justValue = parseFloat(property.just_value || '0');
    if (justValue > 0 && lastSale) {
      const salePrice = parseFloat(lastSale.sale_price || '0');
      if (salePrice > 0) {
        const valueRatio = justValue / salePrice;
        if (valueRatio > 1.2) score += 15; // Property valued higher than sale price
        else if (valueRatio < 0.8) score -= 10; // Property valued lower than sale price
      }
    }

    // Property characteristics
    const yearBuilt = parseInt(property.year_built || '0');
    if (yearBuilt > 2000) score += 10;
    else if (yearBuilt > 0 && yearBuilt < 1980) score -= 5;

    // Sales activity
    if (salesHistory.length > 3) score += 5;
    if (lastSale?.is_distressed) score += 15;
    if (lastSale?.is_bank_sale) score += 10;

    // CDD penalty
    const totalNavAssessment = navData.reduce((sum, nav) =>
      sum + (parseFloat(nav.total_assessment) || 0), 0);
    if (totalNavAssessment > 5000) score -= 15;
    else if (totalNavAssessment > 1000) score -= 5;

    return Math.max(0, Math.min(100, score));
  };

  // Helper function to identify opportunities and risks
  const identifyOpportunitiesAndRisks = (
    property: any, lastSale: any, salesHistory: any[], navData: any[], sunbizData: any[]
  ): { opportunities: string[], riskFactors: string[] } => {
    const opportunities: string[] = [];
    const riskFactors: string[] = [];

    // Opportunities
    if (lastSale?.is_distressed) {
      opportunities.push('🔴 Distressed property - potential below-market opportunity');
    }
    if (lastSale?.is_bank_sale) {
      opportunities.push('🏦 Bank-owned (REO) - motivated seller situation');
    }
    if (sunbizData.length > 0) {
      opportunities.push('🏢 Business owner - potential bulk portfolio opportunity');
    }
    const salePrice = parseFloat(lastSale?.sale_price || '0');
    if (salePrice > 0 && salePrice < 300000) {
      opportunities.push('💰 Below $300K - strong cash flow potential');
    }
    if (salesHistory.length > 5) {
      opportunities.push('📈 Active sales history - established market demand');
    }

    // Risk factors
    const totalNavAssessment = navData.reduce((sum, nav) =>
      sum + (parseFloat(nav.total_assessment) || 0), 0);
    if (totalNavAssessment > 1000) {
      riskFactors.push(`⚠️ Property in CDD - additional assessments $${totalNavAssessment.toFixed(0)}/year`);
    }
    const yearBuilt = parseInt(property.year_built || '0');
    if (yearBuilt > 0 && yearBuilt < 1970) {
      riskFactors.push('⚠️ Built before 1970 - potential structural/code issues');
    }
    if (salesHistory.length === 0) {
      riskFactors.push('⚠️ No recent sales history - difficult to establish market value');
    }
    const lastSaleDate = lastSale?.sale_date;
    if (lastSaleDate) {
      const daysSinceLastSale = (Date.now() - new Date(lastSaleDate).getTime()) / (1000 * 60 * 60 * 24);
      if (daysSinceLastSale > 2555) { // 7 years
        riskFactors.push('📊 No recent sales (7+ years) - market value uncertainty');
      }
    }

    return { opportunities, riskFactors };
  };

  useEffect(() => {
    if (addressOrParcelId) {
      fetchPropertyData()
    }
  }, [addressOrParcelId, city, fetchPropertyData])

  // Set up real-time subscriptions for data updates
  useEffect(() => {
    if (!data?.bcpaData?.parcel_id) return

    const parcelId = data.bcpaData.parcel_id

    // Subscribe to property updates
    const propertySubscription = supabase
      .channel(`property-${parcelId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'florida_parcels',
          filter: `parcel_id=eq.${parcelId}`
        },
        (payload) => {
          console.log('[usePropertyData] Property data updated:', payload)
          fetchPropertyData()
        }
      )
      .subscribe()

    // Subscribe to sales updates
    const salesSubscription = supabase
      .channel(`sales-${parcelId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'comprehensive_sales_data',
          filter: `parcel_id=eq.${parcelId}`
        },
        (payload) => {
          console.log('[usePropertyData] Sales data updated:', payload)
          fetchPropertyData()
        }
      )
      .subscribe()

    // Subscribe to NAV assessment updates
    const navSubscription = supabase
      .channel(`nav-${parcelId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'nav_assessments',
          filter: `parcel_id=eq.${parcelId}`
        },
        (payload) => {
          console.log('[usePropertyData] NAV data updated:', payload)
          fetchPropertyData()
        }
      )
      .subscribe()

    return () => {
      propertySubscription.unsubscribe()
      salesSubscription.unsubscribe()
      navSubscription.unsubscribe()
    }
  }, [data?.bcpaData?.parcel_id, fetchPropertyData])

  return {
    data,
    loading,
    error,
    refetch: fetchPropertyData
  }
}
