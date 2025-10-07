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

    // Source 1: property_sales_history table (MAIN SOURCE - 96,771 records)
    // This is the correct table with or_book and or_page fields
    try {
      const { data: historyData, error: historyError } = await supabase
        .from('property_sales_history')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('sale_date', { ascending: false });

      if (historyError) {
        console.error('Error querying property_sales_history:', historyError);
      }

      if (historyData && historyData.length > 0) {

        const records = historyData
          .map(sale => ({
            parcel_id: sale.parcel_id,
            sale_date: sale.sale_date,
            // Convert from cents to dollars (database stores in cents)
            sale_price: sale.sale_price ? Math.round(parseFloat(sale.sale_price) / 100) : 0,
            sale_year: sale.sale_year || 0,
            sale_month: sale.sale_month || 0,
            qualified_sale: sale.quality_code === 'Q' || sale.quality_code === 'q',
            document_type: sale.clerk_no || '',
            grantor_name: '',
            grantee_name: '',
            // Use or_book and or_page fields from property_sales_history
            book: sale.or_book || '',
            page: sale.or_page || '',
            sale_reason: '',
            vi_code: sale.clerk_no || '',
            is_distressed: false,
            is_bank_sale: false,
            is_cash_sale: false,
            data_source: 'property_sales_history',
          }))
          .filter(record => record.sale_price >= 1000); // Filter out sales under $1,000

        allSales.push(...records);
        return allSales; // Return early since this is our main source
      } else {
      }
    } catch (error) {
      console.error('Error fetching from property_sales_history:', error);
    }

    // Source 2: florida_parcels table (9.1M records - fallback with sale_date, sale_price, sale_qualification)
    try {
      const { data: parcelsData, error: parcelsError } = await supabase
        .from('florida_parcels')
        .select('parcel_id, sale_date, sale_price, sale_qualification')
        .eq('parcel_id', parcelId)
        .not('sale_price', 'is', null)
        .not('sale_date', 'is', null)
        .limit(1);

      if (parcelsError) {
        console.error('Error querying florida_parcels:', parcelsError);
      }

      if (parcelsData && parcelsData.length > 0) {
        const parcel = parcelsData[0];
        const price = parcel.sale_price;
        const saleDate = parcel.sale_date;
        const qualification = parcel.sale_qualification;

        if (price && price > 1000 && saleDate) {
          // Extract year and month from date
          const date = new Date(saleDate);
          const year = date.getFullYear();
          const month = date.getMonth() + 1;

          allSales.push({
            parcel_id: parcel.parcel_id,
            sale_date: saleDate,
            sale_price: parseFloat(price) || 0,
            sale_year: year,
            sale_month: month,
            qualified_sale: qualification?.toLowerCase() === 'qualified',
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
          });

        }
      }
    } catch (error) {
      console.error('Error fetching from florida_parcels:', error);
    }

    // Remove duplicates based on date and price
    const uniqueSales = allSales.filter((sale, index, self) =>
      index === self.findIndex(s =>
        s.sale_date === sale.sale_date &&
        Math.abs(s.sale_price - sale.sale_price) < 1 // Allow for small floating point differences
      )
    );

    // Sort by date descending
    uniqueSales.sort((a, b) => new Date(b.sale_date).getTime() - new Date(a.sale_date).getTime());

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