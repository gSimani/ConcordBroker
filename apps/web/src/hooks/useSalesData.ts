import { useQuery, useQueryClient } from '@tanstack/react-query';
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

// Helper function to fetch from multiple data sources
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
          // Database stores prices in dollars (not cents)
          sale_price: sale.sale_price ? Math.round(parseFloat(sale.sale_price)) : 0,
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

// Fetch function that will be used by React Query
const fetchSalesData = async (parcelId: string): Promise<PropertySalesData> => {
  // Try multiple sales data sources in order of preference
  const salesRecords = await fetchFromMultipleSources(parcelId);

  if (salesRecords.length === 0) {
    return {
      parcel_id: parcelId,
      most_recent_sale: null,
      previous_sales: [],
      total_sales_count: 0,
      highest_sale_price: 0,
      lowest_sale_price: 0,
      average_sale_price: 0,
      years_on_market: 0,
      last_sale_year: null,
    };
  }

  // Sort by sale date descending
  salesRecords.sort((a, b) => new Date(b.sale_date).getTime() - new Date(a.sale_date).getTime());

  // Calculate statistics
  const prices = salesRecords.map(s => s.sale_price).filter(p => p > 0);
  const years = salesRecords.map(s => s.sale_year).filter(y => y > 0);

  return {
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
};

export function useSalesData(parcelId: string | null) {
  const queryClient = useQueryClient();

  // FIX: Use reactive state instead of stale closure
  // Track batch status reactively so it updates when batch query completes
  const [batchStatus, setBatchStatus] = useState<{
    inProgress: boolean;
    hasData: boolean;
    data?: PropertySalesData;
    timestamp: number; // Track when status was checked
  }>({ inProgress: false, hasData: false, timestamp: Date.now() });

  // NEW: Track on-demand scraping status
  const [scrapingStatus, setScrapingStatus] = useState<{
    triggered: boolean;
    inProgress: boolean;
    completed: boolean;
    error: string | null;
  }>({ triggered: false, inProgress: false, completed: false, error: null });

  // Check if a batch query is currently in progress or has completed
  const checkBatchQueryStatus = (): { inProgress: boolean; hasData: boolean; data?: PropertySalesData; timestamp: number } => {
    if (!parcelId) return { inProgress: false, hasData: false, timestamp: Date.now() };

    // Look through all batch query caches
    const queries = queryClient.getQueryCache().findAll({ queryKey: ['batchSalesData'] });

    for (const query of queries) {
      // Check if batch query is loading or has data
      if (query.state.status === 'pending') {
        return { inProgress: true, hasData: false, timestamp: Date.now() };
      }

      if (query.state.status === 'success') {
        const batchData = query.state.data as Map<string, PropertySalesData> | undefined;
        if (batchData && batchData.has(parcelId)) {
          return { inProgress: false, hasData: true, data: batchData.get(parcelId), timestamp: Date.now() };
        }
      }
    }

    return { inProgress: false, hasData: false, timestamp: Date.now() };
  };

  // FIX: Subscribe to query cache changes and update batch status reactively
  // This ensures individual queries wait for batch completion
  useEffect(() => {
    if (!parcelId) return;

    // Initial check
    const initialStatus = checkBatchQueryStatus();
    setBatchStatus(initialStatus);

    // Subscribe to query cache changes to detect when batch completes
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      // Only react to batch query changes
      if (event?.query?.queryKey?.[0] === 'batchSalesData') {
        const newStatus = checkBatchQueryStatus();
        // Only update if status actually changed
        if (newStatus.inProgress !== batchStatus.inProgress ||
            newStatus.hasData !== batchStatus.hasData) {
          console.log(`🔄 Batch status changed for ${parcelId}:`, newStatus);
          // CRITICAL FIX (2025-10-31): Defer state update to prevent React warning
          // "Cannot update component while rendering a different component"
          // Use queueMicrotask to defer until after current render completes
          queueMicrotask(() => {
            setBatchStatus(newStatus);
          });
        }
      }
    });

    return () => {
      unsubscribe();
    };
  }, [parcelId, queryClient]);

  // Use React Query with aggressive caching and deduplication
  const { data: salesData, isLoading, error, refetch } = useQuery({
    queryKey: ['salesData', parcelId],
    queryFn: () => {
      // If we have batch data, use it
      if (batchStatus.hasData && batchStatus.data) {
        console.log(`✅ Using batch cached data for parcel ${parcelId}`);
        return Promise.resolve(batchStatus.data);
      }
      // Fallback to individual fetch if not in batch cache
      console.log(`🔍 Fetching individual data for parcel ${parcelId}`);
      return fetchSalesData(parcelId!);
    },
    // CRITICAL: Only enable if parcelId exists AND batch query is not in progress
    // This prevents individual queries from firing while batch query is loading
    enabled: !!parcelId && !batchStatus.inProgress,
    staleTime: 10 * 60 * 1000, // 10 minutes - sales data doesn't change often
    gcTime: 30 * 60 * 1000, // 30 minutes in cache
    refetchOnWindowFocus: false,
    refetchOnMount: false, // Critical: prevents refetch on component remount
    retry: 1, // Only retry once for sales data
    // Fix for React Query v5 compatibility - prevent optimistic update issues
    placeholderData: batchStatus.hasData ? batchStatus.data : undefined,
  });

  // NEW: Trigger on-demand scraping when no sales data found
  useEffect(() => {
    // DISABLED: Auto-scraping feature - endpoint /api/scrape-sales does not exist (404 errors)
    // Only trigger if:
    // 1. Data has loaded successfully
    // 2. No sales were found (total_sales_count === 0)
    // 3. Scraping hasn't been triggered yet for this parcel
    // 4. Not currently scraping
    // if (
    //   salesData &&
    //   salesData.total_sales_count === 0 &&
    //   !scrapingStatus.triggered &&
    //   !scrapingStatus.inProgress &&
    //   parcelId
    // ) {
    //   triggerSalesScraping(parcelId);
    // }
  }, [salesData, parcelId, scrapingStatus.triggered, scrapingStatus.inProgress]);

  // Function to trigger background scraping
  const triggerSalesScraping = async (parcelId: string) => {
    try {
      setScrapingStatus({ triggered: true, inProgress: true, completed: false, error: null });
      console.log(`🔄 Triggering sales scraping for ${parcelId}`);

      // Get property info to determine county
      const { data: propertyData } = await supabase
        .from('florida_parcels')
        .select('county')
        .eq('parcel_id', parcelId)
        .single();

      if (!propertyData?.county) {
        throw new Error('Could not determine property county');
      }

      // Call scraping API
      const response = await fetch('/api/scrape-sales', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parcel_id: parcelId, county: propertyData.county })
      });

      if (!response.ok) {
        throw new Error('Scraping request failed');
      }

      const result = await response.json();
      console.log('📡 Scraping response:', result);

      // Poll for completion (every 2 seconds for 30 seconds)
      let attempts = 0;
      const maxAttempts = 15;

      const pollInterval = setInterval(async () => {
        attempts++;

        if (attempts > maxAttempts) {
          clearInterval(pollInterval);
          setScrapingStatus({ triggered: true, inProgress: false, completed: false, error: 'Timeout waiting for scraping' });
          return;
        }

        // Refetch sales data to check if new sales appeared
        const refreshedData = await fetchSalesData(parcelId);

        if (refreshedData.total_sales_count > 0) {
          // Success! New sales found
          clearInterval(pollInterval);
          setScrapingStatus({ triggered: true, inProgress: false, completed: true, error: null });
          // Force refetch to update UI
          refetch();
          console.log('✅ Scraping complete! Found new sales.');
        }
      }, 2000);

    } catch (error) {
      console.error('❌ Scraping error:', error);
      setScrapingStatus({
        triggered: true,
        inProgress: false,
        completed: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  };

  return {
    salesData: salesData || null,
    isLoading: isLoading || scrapingStatus.inProgress,
    isScraping: scrapingStatus.inProgress,
    scrapingComplete: scrapingStatus.completed,
    error: error ? (error instanceof Error ? error.message : 'Failed to fetch sales data') : scrapingStatus.error,
    refetch,
  };
}

// NEW: Batch fetch hook to eliminate N+1 query problem
// Fetches sales data for multiple parcels in one query
export function useBatchSalesData(parcelIds: string[]) {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['batchSalesData', parcelIds.sort().join(',')],
    queryFn: async (): Promise<Map<string, PropertySalesData>> => {
      if (parcelIds.length === 0) {
        return new Map();
      }

      console.log(`🔥 Batch fetching sales data for ${parcelIds.length} parcels`);
      const startTime = Date.now();

      // Fetch all sales records for all parcels in ONE query
      const { data: salesRecords, error: salesError } = await supabase
        .from('property_sales_history')
        .select('*')
        .in('parcel_id', parcelIds)
        .order('sale_date', { ascending: false });

      if (salesError) {
        console.error('Error batch fetching sales:', salesError);
        throw new Error(`Failed to batch fetch sales: ${salesError.message}`);
      }

      const fetchTime = Date.now() - startTime;
      console.log(`✅ Batch fetched ${salesRecords?.length || 0} sales records in ${fetchTime}ms`);

      // Group sales by parcel_id
      const salesByParcel = new Map<string, SalesRecord[]>();
      salesRecords?.forEach(sale => {
        const parcelId = sale.parcel_id;
        if (!salesByParcel.has(parcelId)) {
          salesByParcel.set(parcelId, []);
        }

        // Convert sale record to SalesRecord format
        const record: SalesRecord = {
          parcel_id: sale.parcel_id,
          sale_date: sale.sale_date,
          // Database stores prices in dollars (not cents)
          sale_price: sale.sale_price ? Math.round(parseFloat(sale.sale_price)) : 0,
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
          salesByParcel.get(parcelId)!.push(record);
        }
      });

      // Convert to PropertySalesData format for each parcel
      const result = new Map<string, PropertySalesData>();
      parcelIds.forEach(parcelId => {
        const salesRecords = salesByParcel.get(parcelId) || [];

        if (salesRecords.length === 0) {
          result.set(parcelId, {
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

        // Sort by date descending
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

        result.set(parcelId, propertyData);
      });

      console.log(`📊 Processed sales data for ${result.size} parcels`);
      return result;
    },
    enabled: parcelIds.length > 0,
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    retry: 1,
  });

  return {
    salesDataMap: data || new Map(),
    isLoading,
    error: error ? (error instanceof Error ? error.message : 'Failed to batch fetch sales data') : null,
  };
}

// Helper function to format sales data for components
export function formatSalesForSdfData(salesData: PropertySalesData | null): any[] {
  if (!salesData || salesData.total_sales_count === 0) {
    return [];
  }

  // Safety check: ensure previous_sales is an array
  const previousSales = Array.isArray(salesData.previous_sales) ? salesData.previous_sales : [];
  const allSales = [salesData.most_recent_sale, ...previousSales].filter(Boolean);

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
  // Safety check: ensure previous_sales is an array
  const previousSales = Array.isArray(salesData.previous_sales) ? salesData.previous_sales : [];
  const allSales = [salesData.most_recent_sale, ...previousSales]
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