import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';

interface SalesRecord {
  parcel_id: string;
  sale_date: string | null;
  sale_price: number | null;
  sale_yr1: number | null;
  sale_mo1: number | null;
}

type BatchSalesData = Record<string, SalesRecord[]>;

/**
 * Fetch sales data for multiple properties in a single batch query
 * This replaces individual useSalesData calls to eliminate N+1 query problem
 *
 * @param parcelIds - Array of parcel IDs to fetch sales data for
 * @returns Map of parcel_id -> sales records
 */
export const useBatchSalesData = (parcelIds: string[]) => {
  return useQuery<BatchSalesData>({
    queryKey: ['sales-batch', parcelIds.sort().join(',')],
    queryFn: async () => {
      if (!parcelIds || parcelIds.length === 0) {
        return {};
      }

      // Single API call for ALL parcel IDs using .in() filter
      // Query property_sales_history table (same as individual hook)
      const { data, error } = await supabase
        .from('property_sales_history')
        .select('*')
        .in('parcel_id', parcelIds)
        .order('sale_date', { ascending: false });

      if (error) {
        console.error('Batch sales data fetch error:', error);
        throw error;
      }

      // Return as map for O(1) lookup by parcel_id
      // Group sales by parcel_id
      return (data || []).reduce<BatchSalesData>((acc, sale) => {
        if (!acc[sale.parcel_id]) {
          acc[sale.parcel_id] = [];
        }
        acc[sale.parcel_id].push(sale);
        return acc;
      }, {});
    },
    enabled: parcelIds.length > 0,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    cacheTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
  });
};
