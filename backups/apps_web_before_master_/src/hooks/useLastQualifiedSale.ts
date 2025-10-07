import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

interface LastQualifiedSale {
  sale_date: string;
  sale_price: number;
  or_book?: string;
  or_page?: string;
  book_page?: string;
  quality_code?: string;
  verification_code?: string;
  instrument_type?: string;
}


export function useLastQualifiedSale(parcelId: string) {
  const [sale, setSale] = useState<LastQualifiedSale | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!parcelId) return;

    const fetchLastQualifiedSale = async () => {
      setLoading(true);
      setError(null);

      try {
        console.log(`[useLastQualifiedSale] Fetching sales data for parcel: ${parcelId}`);

        // Source 1: Try florida_parcels table for real sales data
        try {
          console.log(`[useLastQualifiedSale] Trying florida_parcels for ${parcelId}`);
          const { data: parcelData, error: parcelError } = await supabase
            .from('florida_parcels')
            .select('sale_date, sale_price, sale_qualification, parcel_id')
            .eq('parcel_id', parcelId)
            .gte('sale_price', 1000)
            .limit(1);

          if (parcelError) {
            console.log(`[useLastQualifiedSale] Florida parcels error: ${parcelError.message}`);
          } else if (parcelData && parcelData.length > 0 && parcelData[0].sale_price) {
            const property = parcelData[0];
            console.log(`[useLastQualifiedSale] Found real sale data for ${parcelId}:`, property);

            setSale({
              sale_date: property.sale_date || '2024-01-01T00:00:00',
              sale_price: parseFloat(property.sale_price) || 0,
              quality_code: property.sale_qualification?.toLowerCase() === 'qualified' ? 'Q' : 'U',
              instrument_type: 'Deed'
            });
            setLoading(false);
            return;
          }
        } catch (error) {
          console.log(`[useLastQualifiedSale] Florida parcels table error:`, error);
        }

        // Source 2: Try comprehensive_sales_data table
        try {
          console.log(`[useLastQualifiedSale] Trying comprehensive_sales_data for ${parcelId}`);
          const { data: comprehensiveData, error: comprehensiveError } = await supabase
            .from('comprehensive_sales_data')
            .select('sale_date, sale_price, sale_qualification, document_type, book, page, parcel_id')
            .eq('parcel_id', parcelId)
            .gte('sale_price', 1000)
            .not('sale_date', 'is', null)
            .order('sale_date', { ascending: false })
            .limit(1);

          if (!comprehensiveError && comprehensiveData && comprehensiveData.length > 0) {
            const sale = comprehensiveData[0];
            console.log(`[useLastQualifiedSale] Found comprehensive sale data for ${parcelId}:`, sale);

            setSale({
              sale_date: sale.sale_date,
              sale_price: parseFloat(sale.sale_price) || 0,
              quality_code: sale.sale_qualification?.toLowerCase() === 'qualified' ? 'Q' : 'U',
              instrument_type: sale.document_type || 'Deed',
              book_page: sale.book && sale.page ? `${sale.book}/${sale.page}` : undefined
            });
            setLoading(false);
            return;
          }
        } catch (error) {
          console.log(`[useLastQualifiedSale] Comprehensive sales data error:`, error);
        }

        // Source 3: Try sdf_sales table
        try {
          console.log(`[useLastQualifiedSale] Trying sdf_sales for ${parcelId}`);
          const { data: sdfData, error: sdfError } = await supabase
            .from('sdf_sales')
            .select('sale_date, sale_price, qualified_sale, document_type, book, page, parcel_id')
            .eq('parcel_id', parcelId)
            .gte('sale_price', 1000)
            .not('sale_date', 'is', null)
            .order('sale_date', { ascending: false })
            .limit(1);

          if (!sdfError && sdfData && sdfData.length > 0) {
            const sale = sdfData[0];
            console.log(`[useLastQualifiedSale] Found SDF sale data for ${parcelId}:`, sale);

            setSale({
              sale_date: sale.sale_date,
              sale_price: parseFloat(sale.sale_price) || 0,
              quality_code: sale.qualified_sale ? 'Q' : 'U',
              instrument_type: sale.document_type || 'Deed',
              book_page: sale.book && sale.page ? `${sale.book}/${sale.page}` : undefined
            });
            setLoading(false);
            return;
          }
        } catch (error) {
          console.log(`[useLastQualifiedSale] SDF sales data error:`, error);
        }

        // Source 4: Try sales_history table
        try {
          console.log(`[useLastQualifiedSale] Trying sales_history for ${parcelId}`);
          const { data: historyData, error: historyError } = await supabase
            .from('sales_history')
            .select('sale_date, sale_price, sale_type, document_type, book, page, parcel_id')
            .eq('parcel_id', parcelId)
            .gte('sale_price', 1000)
            .not('sale_date', 'is', null)
            .order('sale_date', { ascending: false })
            .limit(1);

          if (!historyError && historyData && historyData.length > 0) {
            const sale = historyData[0];
            console.log(`[useLastQualifiedSale] Found history sale data for ${parcelId}:`, sale);

            setSale({
              sale_date: sale.sale_date,
              sale_price: parseFloat(sale.sale_price) || 0,
              quality_code: sale.sale_type?.toLowerCase() === 'qualified' ? 'Q' : 'U',
              instrument_type: sale.document_type || 'Deed',
              book_page: sale.book && sale.page ? `${sale.book}/${sale.page}` : undefined
            });
            setLoading(false);
            return;
          }
        } catch (error) {
          console.log(`[useLastQualifiedSale] Sales history error:`, error);
        }

        // Source 5: Try property_sales_history table (actual populated table)
        try {
          console.log(`[useLastQualifiedSale] Trying property_sales_history for ${parcelId}`);
          const { data: propHistData, error: propHistError } = await supabase
            .from('property_sales_history')
            .select('sale_date, sale_price, verification_code, or_book, or_page, parcel_id')
            .eq('parcel_id', parcelId)
            .gte('sale_price', 1000)
            .not('sale_date', 'is', null)
            .order('sale_date', { ascending: false })
            .limit(1);

          if (!propHistError && propHistData && propHistData.length > 0) {
            const sale = propHistData[0];
            console.log(`[useLastQualifiedSale] Found property_sales_history data for ${parcelId}:`, sale);

            setSale({
              sale_date: sale.sale_date,
              sale_price: parseFloat(sale.sale_price as any) || 0,
              quality_code: (sale.verification_code || '').toUpperCase() === 'Q' ? 'Q' : 'U',
              instrument_type: sale.verification_code || 'Deed',
              book_page: sale.or_book && sale.or_page ? `${sale.or_book}/${sale.or_page}` : undefined
            });
            setLoading(false);
            return;
          }
        } catch (error) {
          console.log(`[useLastQualifiedSale] property_sales_history error:`, error);
        }

        // No real sales data found - return null
        console.log(`[useLastQualifiedSale] No real sales data found for ${parcelId}`);
        setSale(null);
      } catch (err) {
        console.error('Error in useLastQualifiedSale:', err);
        setError('Failed to fetch sales data');
        setSale(null);
      } finally {
        setLoading(false);
      }
    };

    fetchLastQualifiedSale();
  }, [parcelId]);

  return { sale, loading, error };
}
