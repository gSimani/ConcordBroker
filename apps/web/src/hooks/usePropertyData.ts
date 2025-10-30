import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'

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

export const usePropertyData = (addressOrParcelId: string, city: string = '', county: string = 'BROWARD') => {
  const [data, setData] = useState<PropertyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPropertyData = useCallback(async () => {
    console.log(`[usePropertyData] Starting fetch with:`, { addressOrParcelId, city, county });

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

      // Optional: Resolve alternate identifiers (tax deed/certificate) to a parcel_id first
      // Examples: C00007600055 (certificate), TD-XXXX (tax deed number), etc.
      const maybeResolveParcelFromAlternateId = async (rawId: string): Promise<string | null> => {
        const id = (rawId || '').trim();
        if (!id) return null;

        // Heuristics: Starts with 'C' followed by digits OR contains non-digit markers like 'TD'
        const looksLikeCertificate = /^C\d{5,}$/i.test(id);
        const looksLikeDeed = /^(TD|TDM|TDS|DEED)[-\d]/i.test(id) || /-TD\b/i.test(id);

        if (!looksLikeCertificate && !looksLikeDeed) return null;

        try {
          // Try tax_deed_bidding_items first
          const { data: itemsByCert } = await supabase
            .from('tax_deed_bidding_items')
            .select('parcel_id')
            .or(
              `tax_certificate_number.eq.${id},tax_deed_number.eq.${id}`
            )
            .limit(1);

          if (itemsByCert && itemsByCert.length > 0 && itemsByCert[0]?.parcel_id) {
            console.log('[usePropertyData] Resolved parcel_id from tax_deed_bidding_items:', itemsByCert[0].parcel_id);
            return itemsByCert[0].parcel_id as string;
          }

          // Fallback: materialized/combined view if available
          const { data: viewByCert } = await supabase
            .from('tax_deed_items_view')
            .select('parcel_id')
            .or(
              `tax_certificate_number.eq.${id},tax_deed_number.eq.${id}`
            )
            .limit(1);

          if (viewByCert && viewByCert.length > 0 && viewByCert[0]?.parcel_id) {
            console.log('[usePropertyData] Resolved parcel_id from tax_deed_items_view:', viewByCert[0].parcel_id);
            return viewByCert[0].parcel_id as string;
          }
        } catch (e) {
          console.log('[usePropertyData] Alternate ID resolution error:', e);
        }

        return null;
      };

      // Step 1: Get primary property data
      if (isParcelId) {
        console.log(`[usePropertyData] Fetching by parcel ID: ${addressOrParcelId}`);
        try {
          // Try maybeSingle first to avoid errors on duplicates
          let query = supabase
            .from('florida_parcels')
            .select('*')
            .eq('parcel_id', addressOrParcelId);

          let { data: floridaData, error: floridaError } = await query.maybeSingle();

          // If no result or duplicate, fallback to deterministic pick (latest by year/import_date)
          if ((!floridaData || floridaError) && !bcpaData) {
            console.log('[usePropertyData] maybeSingle fallback due to', { floridaError, floridaDataNull: !floridaData });
            const { data: rowsLimited, error: rowsErr } = await supabase
              .from('florida_parcels')
              .select('*')
              .eq('parcel_id', addressOrParcelId)
              .order('year', { ascending: false })
              .limit(1);

            if (!rowsErr && rowsLimited && rowsLimited.length > 0) {
              floridaData = rowsLimited[0];
              floridaError = null as any;
            }
          }

          // If still not found, try alternate formatting for Broward folio (12 digits -> 4-2-2-4 pattern)
          if (!floridaData && /^\d{12}$/.test(addressOrParcelId)) {
            const raw = addressOrParcelId;
            const dashed = `${raw.slice(0,4)}-${raw.slice(4,6)}-${raw.slice(6,8)}-${raw.slice(8)}`;
            const spaced = `${raw.slice(0,4)} ${raw.slice(4,6)} ${raw.slice(6,8)} ${raw.slice(8)}`;
            console.log('[usePropertyData] Trying alternate folio formats', { dashed, spaced });

            const { data: altRows, error: altErr } = await supabase
              .from('florida_parcels')
              .select('*')
              .or(`parcel_id.eq.${dashed},parcel_id.eq.${spaced}`)
              .order('year', { ascending: false })
              .limit(1);

            if (!altErr && altRows && altRows.length > 0) {
              floridaData = altRows[0];
            }
          }

          if (!floridaError && floridaData) {
            bcpaData = floridaData;
            parcelId = floridaData.parcel_id;
            console.log(`[usePropertyData] Found property in florida_parcels:`, floridaData);
          }
        } catch (error) {
          console.log(`[usePropertyData] Florida parcels error:`, error);
        }

        // If not found and the identifier might be a tax deed/certificate, try to resolve to a parcel_id
        if (!bcpaData) {
          const resolvedParcel = await maybeResolveParcelFromAlternateId(addressOrParcelId);
          if (resolvedParcel) {
            try {
              const { data: floridaDataByResolved, error: floridaResolvedErr } = await supabase
                .from('florida_parcels')
                .select('*')
                .eq('parcel_id', resolvedParcel)
                .single();

              if (!floridaResolvedErr && floridaDataByResolved) {
                bcpaData = floridaDataByResolved;
                parcelId = floridaDataByResolved.parcel_id;
                console.log('[usePropertyData] Loaded property via resolved parcel_id:', parcelId);
              } else {
                console.log('[usePropertyData] Resolved parcel_id not found in florida_parcels:', resolvedParcel);
              }
            } catch (e) {
              console.log('[usePropertyData] Error loading resolved parcel_id:', e);
            }
          }
        }
      } else {
        // Address-based lookup with optimized prefix matching
        console.log(`[usePropertyData] Searching by address: ${addressOrParcelId}, ${city}, county: ${county}`);
        try {
          const searchAddress = addressOrParcelId.replace(/-/g, ' ').trim().toUpperCase();
          const searchCity = city.trim().toUpperCase();

          // Use prefix matching for better index utilization (uses idx_fp_autocomplete_covering)
          let query = supabase
            .from('florida_parcels')
            .select('*')
            .eq('county', county.toUpperCase()) // Filter by county first for index usage
            .ilike('phy_addr1', `${searchAddress}%`); // Prefix match instead of wildcard

          if (searchCity) {
            query = query.ilike('phy_city', `${searchCity}%`); // Prefix match instead of wildcard
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

      // Normalize field names so UI has consistent keys regardless of county/source
      const normalizeBcpaData = (row: any) => {
        if (!row) return row;
        const normalized: any = { ...row };

        normalized.owner_name = row.owner_name || row.own_name || row.own1 || row.owner || null;
        normalized.owner_addr1 = row.owner_addr1 || row.owner_address || row.own_addr1 || null;
        normalized.owner_city = row.owner_city || row.own_city || row.city_owner || null;
        normalized.owner_state = row.owner_state || row.own_state || 'FL';
        normalized.owner_zip = row.owner_zip || row.owner_zipcd || row.own_zip || row.zip_owner || null;

        normalized.phy_addr1 = row.phy_addr1 || row.property_address_full || row.property_address || row.situs_addr || row.situs_address || null;
        normalized.phy_city = row.phy_city || row.city || row.situs_city || null;
        normalized.phy_zipcd = row.phy_zipcd || row.zip || row.zip_cd || row.situs_zip || null;

        normalized.just_value = parseFloat(row.just_value ?? row.jv ?? 0) || 0;
        normalized.assessed_value = parseFloat(row.assessed_value ?? row.av_sd ?? 0) || 0;
        normalized.taxable_value = parseFloat(row.taxable_value ?? row.tv_sd ?? 0) || 0;
        normalized.land_value = parseFloat(row.land_value ?? row.lnd_val ?? row.land_val ?? 0) || 0;
        // Compute building value if not set but just/land present
        if (!normalized.building_value && normalized.just_value && normalized.land_value >= 0 && normalized.just_value > normalized.land_value) {
          normalized.building_value = normalized.just_value - normalized.land_value;
        }

        normalized.year_built = row.year_built || row.act_yr_blt || row.yr_blt || null;
        normalized.total_living_area = row.total_living_area || row.tot_lvg_area || row.living_area || null;
        normalized.bedrooms = row.bedrooms || row.bedroom_cnt || null;
        normalized.bathrooms = row.bathrooms || row.bathroom_cnt || null;
        normalized.land_sqft = row.land_sqft || row.lnd_sqfoot || row.lot_size_sqft || null;

        normalized.property_use_code = row.property_use_code || row.dor_uc || row.property_use || null;
        normalized.property_use_desc = row.property_use_desc || row.property_type_desc || row.land_use_desc || null;

        // Sales fallbacks commonly present in county exports
        const salePrice = row.sale_price ?? row.sale_prc1 ?? row.sale_amt1;
        const saleDate = row.sale_date ?? row.sale_dt1;
        const saleYear = row.sale_year ?? row.sale_yr1;
        const saleMonth = row.sale_month ?? row.sale_mo1;
        if (!row.sale_date && saleYear && saleMonth) {
          try {
            const dt = new Date(Number(saleYear), Number(saleMonth) - 1, 1);
            normalized.sale_date = dt.toISOString();
          } catch {}
        } else if (saleDate) {
          normalized.sale_date = saleDate;
        }
        if (salePrice) normalized.sale_price = parseFloat(salePrice) || 0;

        return normalized;
      };

      bcpaData = normalizeBcpaData(bcpaData);

      // Step 2: Get comprehensive sales data
      console.log(`[usePropertyData] Fetching sales data for parcel: ${parcelId}`);
      const salesDataResults = await fetchSalesDataFromMultipleSources(parcelId, bcpaData);
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

  // Helper function to fetch sales data from multiple sources
  const fetchSalesDataFromMultipleSources = async (parcelId: string, baseRecord?: any): Promise<any[]> => {
    const allSales: any[] = [];
    console.log(`[usePropertyData] Fetching sales from multiple sources for: ${parcelId}`);

    // Source 1: property_sales_history (main source - 96,771 records)
    try {
      const { data: salesHistory, error } = await supabase
        .from('property_sales_history')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('sale_date', { ascending: false });

      if (!error && salesHistory && salesHistory.length > 0) {
        const sales = salesHistory.map(sale => ({
          parcel_id: sale.parcel_id,
          sale_date: sale.sale_date,
          sale_price: sale.sale_price ? Math.round(parseFloat(sale.sale_price)) : 0,
          sale_year: sale.sale_year || 0,
          sale_month: sale.sale_month || 0,
          qualified_sale: sale.quality_code === 'Q' || sale.quality_code === 'q',
          document_type: sale.clerk_no || '',
          book: sale.or_book || '',
          page: sale.or_page || '',
          data_source: 'property_sales_history'
        })).filter(record => record.sale_price >= 1000);

        allSales.push(...sales);
        console.log(`[usePropertyData] Found ${sales.length} property_sales_history records`);
        return allSales; // Return early since this is our main source
      }
    } catch (error) {
      console.log(`[usePropertyData] Property sales history error:`, error);
    }

    // Source 2: florida_parcels (fallback)
    try {
      const { data: parcelsData, error } = await supabase
        .from('florida_parcels')
        .select('parcel_id, sale_date, sale_price, sale_qualification')
        .eq('parcel_id', parcelId)
        .not('sale_price', 'is', null)
        .not('sale_date', 'is', null)
        .limit(1);

      if (!error && parcelsData && parcelsData.length > 0) {
        const parcel = parcelsData[0];
        const price = parcel.sale_price;
        const saleDate = parcel.sale_date;

        if (price && price > 1000 && saleDate) {
          const date = new Date(saleDate);
          allSales.push({
            parcel_id: parcel.parcel_id,
            sale_date: saleDate,
            sale_price: parseFloat(price) || 0,
            sale_year: date.getFullYear(),
            sale_month: date.getMonth() + 1,
            qualified_sale: parcel.sale_qualification?.toLowerCase() === 'qualified',
            data_source: 'florida_parcels'
          });
        }
      }
    } catch (error) {
      console.log(`[usePropertyData] Florida parcels sales error:`, error);
    }

    // Source 3: bcpa-style columns on base record (sale_prc1, sale_yr1, sale_mo1)
    if (allSales.length === 0 && baseRecord) {
      const prop = baseRecord as any;
      const price = prop.sale_price ?? prop.sale_prc1 ?? prop.sale_amt1;
      const saleYear = prop.sale_year ?? prop.sale_yr1;
      const saleMonth = prop.sale_month ?? prop.sale_mo1;
      if (price && (saleYear || saleMonth)) {
        const y = Number(saleYear) || new Date().getFullYear();
        const m = Number(saleMonth) || 1;
        const dt = new Date(y, m - 1, 1).toISOString();
        allSales.push({
          parcel_id: parcelId,
          sale_date: dt,
          sale_price: parseFloat(price) || 0,
          sale_year: y,
          sale_month: m,
          qualified_sale: undefined,
          data_source: 'bcpa_fields'
        });
      }
    }

    // Remove duplicates and sort
    const uniqueSales = allSales.filter((sale, index, self) =>
      index === self.findIndex(s =>
        s.sale_date === sale.sale_date &&
        Math.abs(s.sale_price - sale.sale_price) < 1
      )
    );

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
        // Silence permission errors in client; return empty without noisy logs
        const msg = (error as any)?.message || '';
        if (!/permission denied|401|unauthorized/i.test(msg)) {
          console.log(`[usePropertyData] NAV data error: ${msg}`);
        }
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

    if (qualifiedSale) return qualifiedSale;

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
        if (valueRatio > 1.2) score += 15;
        else if (valueRatio < 0.8) score -= 10;
      }
    }

    // Property characteristics
    const yearBuilt = parseInt(property.year_built || '0');
    if (yearBuilt > 2000) score += 10;
    else if (yearBuilt > 0 && yearBuilt < 1980) score -= 5;

    // Sales activity
    if (salesHistory.length > 3) score += 5;

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

    return { opportunities, riskFactors };
  };

  useEffect(() => {
    if (addressOrParcelId) {
      fetchPropertyData()
    }
  }, [addressOrParcelId, city, fetchPropertyData])

  return {
    data,
    loading,
    error,
    refetch: fetchPropertyData
  }
}
