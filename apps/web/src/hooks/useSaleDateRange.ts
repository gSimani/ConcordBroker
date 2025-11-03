import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

interface SaleDateRange {
  minYear: number | null;
  maxYear: number | null;
  minDate: string | null;
  maxDate: string | null;
  loading: boolean;
  error: string | null;
  totalSalesRecords: number;
}

/**
 * Hook to fetch available sale date range from property_sales_history
 * Helps users understand what date ranges have actual data
 */
export function useSaleDateRange(county: string = 'BROWARD') {
  const [dateRange, setDateRange] = useState<SaleDateRange>({
    minYear: null,
    maxYear: null,
    minDate: null,
    maxDate: null,
    loading: true,
    error: null,
    totalSalesRecords: 0
  });

  useEffect(() => {
    let isMounted = true;

    async function fetchDateRange() {
      try {
        // Query to get min and max sale years
        const { data, error, count } = await supabase
          .from('property_sales_history')
          .select('sale_year, sale_date', { count: 'exact' })
          .eq('county', county.toUpperCase())
          .not('sale_year', 'is', null)
          .order('sale_year', { ascending: true })
          .limit(1000); // Sample to get range

        if (error) throw error;

        if (data && data.length > 0 && isMounted) {
          // Extract years
          const years = data
            .map(d => d.sale_year)
            .filter(y => y != null)
            .sort((a, b) => a - b);

          const dates = data
            .map(d => d.sale_date)
            .filter(d => d != null)
            .sort();

          setDateRange({
            minYear: years.length > 0 ? years[0] : null,
            maxYear: years.length > 0 ? years[years.length - 1] : null,
            minDate: dates.length > 0 ? dates[0] : null,
            maxDate: dates.length > 0 ? dates[dates.length - 1] : null,
            loading: false,
            error: null,
            totalSalesRecords: count || 0
          });
        } else if (isMounted) {
          setDateRange({
            minYear: null,
            maxYear: null,
            minDate: null,
            maxDate: null,
            loading: false,
            error: 'No sales data available',
            totalSalesRecords: 0
          });
        }
      } catch (err) {
        if (isMounted) {
          setDateRange(prev => ({
            ...prev,
            loading: false,
            error: err instanceof Error ? err.message : 'Failed to fetch date range'
          }));
        }
      }
    }

    fetchDateRange();

    return () => {
      isMounted = false;
    };
  }, [county]);

  return dateRange;
}
