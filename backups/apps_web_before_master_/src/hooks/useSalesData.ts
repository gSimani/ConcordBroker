import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

export interface SalesRecord {
  parcel_id: string;
  sale_date: string;
  sale_price: number;
  sale_year: number;
  sale_month: number;
  qualified_sale: boolean;
  document_type?: string;
  grantor_name?: string;
  grantee_name?: string;
  book?: string;
  page?: string;
  sale_reason?: string;
  vi_code?: string;
  is_distressed?: boolean;
  is_bank_sale?: boolean;
  is_cash_sale?: boolean;
  data_source: string;
}

export interface PropertySalesData {
  parcel_id: string;
  most_recent_sale: SalesRecord | null;
  previous_sales: SalesRecord[];
  total_sales_count: number;
  highest_sale_price: number;
  lowest_sale_price: number;
  average_sale_price: number;
  years_on_market: number;
  last_sale_year: number | null;
}

export function useSalesData(parcelId: string | null) {
  const [salesData, setSalesData] = useState<PropertySalesData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId) {
      setSalesData(null);
      return;
    }

    fetchSalesData(parcelId);
  }, [parcelId]);

  const fetchSalesData = async (parcelId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log(`[useSalesData] Starting comprehensive sales fetch for parcel: ${parcelId}`);

      // Try multiple sales data sources in order matching useLastQualifiedSale
      const salesRecords = await fetchFromMultipleSources(parcelId);

      if (salesRecords.length === 0) {
        console.log(`[useSalesData] No real sales data found for ${parcelId} - returning empty data`);
        setSalesData({
          parcel_id: parcelId,
          most_recent_sale: null,
          previous_sales: [],
          total_sales_count: 0,
          highest_sale_price: 0,
          lowest_sale_price: 0,
          average_sale_price: 0,
          years_on_market: 0,
          last_sale_year: null,
        });
        return;
      }

      // Sort by sale date descending
      salesRecords.sort((a, b) => new Date(b.sale_date).getTime() - new Date(a.sale_date).getTime());

      // Calculate statistics
      const prices = salesRecords.map(s => s.sale_price).filter(p => p > 0);
      const years = salesRecords.map(s => s.sale_year).filter(y => y > 0);

      const propertyData: PropertySalesData = {
        parcel_id: parcelId,
        most_recent_sale: salesRecords[0] || null,
        previous_sales: salesRecords.slice(1),
        total_sales_count: salesRecords.length,
        highest_sale_price: prices.length > 0 ? Math.max(...prices) : 0,
        lowest_sale_price: prices.length > 0 ? Math.min(...prices) : 0,
        average_sale_price: prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0,
        years_on_market: years.length > 1 ? Math.max(...years) - Math.min(...years) : 0,
        last_sale_year: years.length > 0 ? Math.max(...years) : null,
      };

      console.log(`[useSalesData] Successfully processed ${salesRecords.length} sales for ${parcelId}:`, {
        mostRecentPrice: propertyData.most_recent_sale?.sale_price,
        mostRecentDate: propertyData.most_recent_sale?.sale_date,
        totalSales: propertyData.total_sales_count,
        priceRange: `$${propertyData.lowest_sale_price} - $${propertyData.highest_sale_price}`
      });

      setSalesData(propertyData);
    } catch (err) {
      console.error('[useSalesData] Error in fetchSalesData:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch comprehensive sales data');
      setSalesData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchFromMultipleSources = async (parcelId: string): Promise<SalesRecord[]> => {
    console.log(`[useSalesData] Fetching sales data from API for parcel: ${parcelId}`);

    try {
      // Use our fixed sales history API endpoint
      const apiUrl = window.location.hostname === 'localhost'
        ? 'http://localhost:8002'
        : 'https://api.concordbroker.com';

      const response = await fetch(`${apiUrl}/api/properties/${parcelId}/sales`);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const apiData = await response.json();
      console.log(`[useSalesData] API response for ${parcelId}:`, apiData);

      if (!apiData.success || !apiData.sales || apiData.sales.length === 0) {
        console.log(`[useSalesData] No sales data from API for ${parcelId}`);
        return [];
      }

      // Convert API response to our format
      const salesRecords = apiData.sales.map((sale: any) => ({
        parcel_id: apiData.parcel_id,
        sale_date: sale.sale_date,
        sale_price: sale.sale_price,
        sale_year: sale.sale_year || (sale.sale_date ? parseInt(sale.sale_date.substring(0, 4)) : 0),
        sale_month: sale.sale_month || (sale.sale_date ? parseInt(sale.sale_date.substring(5, 7)) : 0),
        qualified_sale: sale.qualified_sale,
        document_type: sale.document_type || 'Deed',
        grantor_name: sale.grantor_name || '',
        grantee_name: sale.grantee_name || '',
        book: sale.book || '',
        page: sale.page || '',
        sale_reason: '',
        vi_code: sale.vi_code || '',
        is_distressed: false,
        is_bank_sale: false,
        is_cash_sale: false,
        data_source: sale.data_source || 'api',
      }));

      console.log(`[useSalesData] Converted ${salesRecords.length} sales records from API`);
      return salesRecords;

    } catch (error) {
      console.error(`[useSalesData] API error for ${parcelId}:`, error);

      // Fallback to direct Supabase query if API fails
      console.log(`[useSalesData] Falling back to direct Supabase query for ${parcelId}`);
      return await fetchFromSupabaseFallback(parcelId);
    }
  };

  const fetchFromSupabaseFallback = async (parcelId: string): Promise<SalesRecord[]> => {
    const allSales: SalesRecord[] = [];

    console.log(`[useSalesData] Using Supabase fallback for parcel: ${parcelId}`);

    // Only try the main florida_parcels table as fallback
    try {
      console.log(`[useSalesData] Trying florida_parcels fallback for ${parcelId}`);
      const { data: parcelData, error: parcelError } = await supabase
        .from('florida_parcels')
        .select('sale_date, sale_price, sale_qualification, parcel_id')
        .eq('parcel_id', parcelId)
        .gte('sale_price', 1000)
        .not('sale_price', 'is', null);

      if (parcelError) {
        console.log(`[useSalesData] Florida parcels fallback error: ${parcelError.message}`);
      } else if (parcelData && parcelData.length > 0) {
        console.log(`[useSalesData] Found ${parcelData.length} florida_parcels fallback records for ${parcelId}`);
        const records = parcelData.map(sale => ({
          parcel_id: sale.parcel_id,
          sale_date: sale.sale_date || '2024-01-01T00:00:00',
          sale_price: parseFloat(sale.sale_price) || 0,
          sale_year: sale.sale_date ? parseInt(sale.sale_date.substring(0, 4)) : 2024,
          sale_month: sale.sale_date ? parseInt(sale.sale_date.substring(5, 7)) : 1,
          qualified_sale: sale.sale_qualification?.toLowerCase() === 'qualified' || sale.sale_qualification === 'Q',
          document_type: 'Deed',
          grantor_name: '',
          grantee_name: '',
          book: '',
          page: '',
          sale_reason: '',
          vi_code: sale.sale_qualification || '',
          is_distressed: false,
          is_bank_sale: false,
          is_cash_sale: false,
          data_source: 'florida_parcels',
        }));
        allSales.push(...records);
      }
    } catch (error) {
      console.log(`[useSalesData] Florida parcels fallback error:`, error);
    }

    console.log(`[useSalesData] Fallback found ${allSales.length} sales for ${parcelId}`);
    return allSales;
  };

  return {
    salesData,
    isLoading,
    error,
    refetch: () => parcelId && fetchSalesData(parcelId),
  };
}

// Helper function to format sales data for components
export function formatSalesForSdfData(salesData: PropertySalesData | null): any[] {
  if (!salesData || salesData.total_sales_count === 0) {
    return [];
  }

  const allSales = [salesData.most_recent_sale, ...salesData.previous_sales].filter(Boolean);

  return allSales.map(sale => ({
    sale_date: sale!.sale_date,
    sale_price: sale!.sale_price.toString(),
    qualified_sale: sale!.qualified_sale,
    document_type: sale!.document_type,
    grantor_name: sale!.grantor_name,
    grantee_name: sale!.grantee_name,
    book: sale!.book,
    page: sale!.page,
    sale_reason: sale!.sale_reason,
    vi_code: sale!.vi_code,
    is_distressed: sale!.is_distressed,
    is_bank_sale: sale!.is_bank_sale,
    is_cash_sale: sale!.is_cash_sale,
  }));
}

// Helper function to get latest sale info for mini cards
// NOTE: Filters out sales ≤ $1,000 to skip quick claim deeds and nominal transfers
export function getLatestSaleInfo(salesData: PropertySalesData | null): {
  sale_prc1?: number;
  sale_yr1?: number;
  sale_date?: string;
} {
  if (!salesData) {
    return {};
  }

  // Get all sales (most recent + previous) and filter for actual sales > $1,000
  const allSales = [salesData.most_recent_sale, ...salesData.previous_sales]
    .filter(Boolean)
    .filter(sale => sale!.sale_price > 1000); // Skip quick claim deeds and nominal transfers

  if (allSales.length === 0) {
    return {};
  }

  // Sort by date descending to get the most recent qualifying sale
  allSales.sort((a, b) => new Date(b!.sale_date).getTime() - new Date(a!.sale_date).getTime());

  const latestQualifyingSale = allSales[0]!;

  return {
    sale_prc1: latestQualifyingSale.sale_price,
    sale_yr1: latestQualifyingSale.sale_year,
    sale_date: latestQualifyingSale.sale_date,
  };
}
