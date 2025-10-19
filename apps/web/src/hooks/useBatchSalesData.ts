import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { SalesRecord, PropertySalesData } from './useSalesData';

// Batch fetch sales data for multiple parcel IDs
const fetchBatchSalesData = async (parcelIds: string[]): Promise<Map<string, PropertySalesData>> => {
  const salesMap = new Map<string, PropertySalesData>();

  if (!parcelIds || parcelIds.length === 0) {
    return salesMap;
  }

  try {
    // Fetch all sales data in a single query using .in()
    const { data: historyData, error: historyError } = await supabase
      .from('property_sales_history')
      .select('*')
      .in('parcel_id', parcelIds)
      .order('sale_date', { ascending: false });

    if (historyError) {
      console.error('Error batch querying property_sales_history:', historyError);
      return salesMap;
    }

    if (!historyData || historyData.length === 0) {
      // Initialize empty data for all parcel IDs
      parcelIds.forEach(parcelId => {
        salesMap.set(parcelId, {
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
      });
      return salesMap;
    }

    // Group sales by parcel_id
    const salesByParcel = new Map<string, SalesRecord[]>();

    historyData.forEach(sale => {
      const record: SalesRecord = {
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
        book: sale.or_book || '',
        page: sale.or_page || '',
        sale_reason: '',
        vi_code: sale.clerk_no || '',
        is_distressed: false,
        is_bank_sale: false,
        is_cash_sale: false,
        data_source: 'property_sales_history',
      };

      // Filter out sales under $1,000
      if (record.sale_price >= 1000) {
        if (!salesByParcel.has(sale.parcel_id)) {
          salesByParcel.set(sale.parcel_id, []);
        }
        salesByParcel.get(sale.parcel_id)!.push(record);
      }
    });

    // Process each parcel's sales data
    parcelIds.forEach(parcelId => {
      const salesRecords = salesByParcel.get(parcelId) || [];

      if (salesRecords.length === 0) {
        salesMap.set(parcelId, {
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

      // Sort by sale date descending (most recent first)
      salesRecords.sort((a, b) => new Date(b.sale_date).getTime() - new Date(a.sale_date).getTime());

      // Calculate statistics
      const prices = salesRecords.map(s => s.sale_price).filter(p => p > 0);
      const years = salesRecords.map(s => s.sale_year).filter(y => y > 0);

      salesMap.set(parcelId, {
        parcel_id: parcelId,
        most_recent_sale: salesRecords[0] || null,
        previous_sales: salesRecords.slice(1),
        total_sales_count: salesRecords.length,
        highest_sale_price: prices.length > 0 ? Math.max(...prices) : 0,
        lowest_sale_price: prices.length > 0 ? Math.min(...prices) : 0,
        average_sale_price: prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0,
        years_on_market: years.length > 1 ? Math.max(...years) - Math.min(...years) : 0,
        last_sale_year: years.length > 0 ? Math.max(...years) : null,
      });
    });

    return salesMap;
  } catch (error) {
    console.error('Error batch fetching sales data:', error);
    return salesMap;
  }
};

/**
 * Hook to batch prefetch sales data for multiple properties
 * This dramatically reduces API calls by fetching all sales data in a single request
 *
 * @param parcelIds - Array of parcel IDs to fetch sales data for
 * @returns Query result containing a Map of parcelId -> PropertySalesData
 */
export function useBatchSalesData(parcelIds: string[]) {
  // Sort and deduplicate parcel IDs for consistent cache keys
  const uniqueSortedIds = [...new Set(parcelIds)].sort();

  return useQuery({
    queryKey: ['batchSalesData', uniqueSortedIds],
    queryFn: () => fetchBatchSalesData(uniqueSortedIds),
    enabled: uniqueSortedIds.length > 0,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    retry: 1,
  });
}
