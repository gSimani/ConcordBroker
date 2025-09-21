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
      // Try multiple sales data sources in order of preference
      const salesRecords = await fetchFromMultipleSources(parcelId);

      if (salesRecords.length === 0) {
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

      setSalesData(propertyData);
    } catch (err) {
      console.error('Error fetching sales data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch sales data');
      setSalesData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchFromMultipleSources = async (parcelId: string): Promise<SalesRecord[]> => {
    const allSales: SalesRecord[] = [];

    // Source 1: Try comprehensive_sales_data view first
    try {
      const { data: comprehensiveData, error: comprehensiveError } = await supabase
        .from('comprehensive_sales_data')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('sale_date', { ascending: false });

      if (comprehensiveData && comprehensiveData.length > 0) {
        const records = comprehensiveData
          .map(sale => ({
            parcel_id: sale.parcel_id,
            sale_date: sale.sale_date,
            sale_price: parseFloat(sale.sale_price) || 0,
            sale_year: parseInt(sale.sale_year) || 0,
            sale_month: parseInt(sale.sale_month) || 0,
            qualified_sale: sale.sale_qualification?.toLowerCase() === 'qualified' || sale.sale_qualification?.toLowerCase() === 'q',
            document_type: sale.document_type || '',
            grantor_name: sale.grantor_name || '',
            grantee_name: sale.grantee_name || '',
            book: sale.book || '',
            page: sale.page || '',
            sale_reason: sale.sale_reason || '',
            vi_code: sale.vi_code || '',
            is_distressed: sale.is_distressed || false,
            is_bank_sale: sale.is_bank_sale || false,
            is_cash_sale: sale.is_cash_sale || false,
            data_source: sale.data_source || 'comprehensive_view',
          }))
          .filter(record => record.sale_price >= 1000); // Filter out sales under $1000

        allSales.push(...records);
        return allSales; // Return early if comprehensive view works
      }
    } catch (error) {
      console.log('Comprehensive sales view not available, trying individual tables');
    }

    // Source 2: Try SDF sales table
    try {
      const { data: sdfData, error: sdfError } = await supabase
        .from('sdf_sales')
        .select('*')
        .eq('parcel_id', parcelId);

      if (sdfData && sdfData.length > 0) {
        const records = sdfData
          .map(sale => ({
            parcel_id: sale.parcel_id,
            sale_date: sale.sale_date,
            sale_price: parseFloat(sale.sale_price) || 0,
            sale_year: sale.sale_year || parseInt(sale.sale_date?.substring(0, 4)) || 0,
            sale_month: sale.sale_month || parseInt(sale.sale_date?.substring(5, 7)) || 0,
            qualified_sale: sale.qualified_sale === true || sale.qualified_sale === 'true' || sale.qualified_sale === 'Q',
            document_type: sale.document_type || '',
            grantor_name: sale.grantor_name || '',
            grantee_name: sale.grantee_name || '',
            book: sale.book || '',
            page: sale.page || '',
            sale_reason: sale.sale_reason || '',
            vi_code: sale.vi_code || '',
            is_distressed: sale.is_distressed || false,
            is_bank_sale: sale.is_bank_sale || false,
            is_cash_sale: sale.is_cash_sale || false,
            data_source: 'sdf_sales',
          }))
          .filter(record => record.sale_price >= 1000); // Filter out sales under $1000

        allSales.push(...records);
      }
    } catch (error) {
      console.log('SDF sales table not available or error:', error);
    }

    // Source 3: Try sales_history table
    try {
      const { data: historyData, error: historyError } = await supabase
        .from('sales_history')
        .select('*')
        .eq('parcel_id', parcelId);

      if (historyData && historyData.length > 0) {
        const records = historyData
          .map(sale => ({
            parcel_id: sale.parcel_id,
            sale_date: sale.sale_date,
            sale_price: parseFloat(sale.sale_price) || 0,
            sale_year: sale.sale_year || parseInt(sale.sale_date?.substring(0, 4)) || 0,
            sale_month: sale.sale_month || parseInt(sale.sale_date?.substring(5, 7)) || 0,
            qualified_sale: sale.sale_type?.toLowerCase() === 'qualified',
            document_type: sale.document_type || '',
            grantor_name: sale.grantor_name || '',
            grantee_name: sale.grantee_name || '',
            book: sale.book || '',
            page: sale.page || '',
            sale_reason: sale.sale_reason || '',
            vi_code: sale.vi_code || '',
            is_distressed: sale.is_distressed || false,
            is_bank_sale: sale.is_bank_sale || false,
            is_cash_sale: sale.is_cash_sale || false,
            data_source: 'sales_history',
          }))
          .filter(record => record.sale_price >= 1000); // Filter out sales under $1000

        allSales.push(...records);
      }
    } catch (error) {
      console.log('Sales history table not available or error:', error);
    }

    // Source 4: Try florida_parcels table (built-in sales data)
    try {
      const { data: parcelsData, error: parcelsError } = await supabase
        .from('florida_parcels')
        .select('parcel_id, sale_date, sale_price, sale_qualification')
        .eq('parcel_id', parcelId)
        .not('sale_date', 'is', null)
        .not('sale_price', 'is', null);

      if (parcelsData && parcelsData.length > 0) {
        const records = parcelsData.map(sale => ({
          parcel_id: sale.parcel_id,
          sale_date: sale.sale_date,
          sale_price: parseFloat(sale.sale_price) || 0,
          sale_year: parseInt(sale.sale_date?.substring(0, 4)) || 0,
          sale_month: parseInt(sale.sale_date?.substring(5, 7)) || 0,
          qualified_sale: sale.sale_qualification?.toLowerCase() === 'qualified',
          document_type: '',
          grantor_name: '',
          grantee_name: '',
          book: '',
          page: '',
          sale_reason: '',
          vi_code: '',
          is_distressed: false,
          is_bank_sale: false,
          is_cash_sale: false,
          data_source: 'florida_parcels',
        }));

        allSales.push(...records);
      }
    } catch (error) {
      console.log('Florida parcels sales data not available or error:', error);
    }

    // Remove duplicates based on date and price
    const uniqueSales = allSales.filter((sale, index, self) =>
      index === self.findIndex(s =>
        s.sale_date === sale.sale_date &&
        s.sale_price === sale.sale_price
      )
    );

    return uniqueSales;
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