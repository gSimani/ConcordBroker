import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/lib/supabase';

interface PropertyCache {
  [key: string]: {
    data: any;
    timestamp: number;
  };
}

const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const propertyCache = new Map<string, { data: any; timestamp: number }>();

export function useOptimizedPropertyData(parcelId: string) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchPropertyData = useCallback(async () => {
    // Check cache first
    const cached = propertyCache.get(parcelId);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      setData(cached.data);
      setLoading(false);
      return;
    }

    // Abort previous request if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    abortControllerRef.current = new AbortController();
    
    try {
      setLoading(true);
      setError(null);

      // Fetch all related data in parallel
      const [propertyResult, salesResult, assessmentResult] = await Promise.all([
        supabase
          .from('properties')
          .select(\`
            *,
            florida_parcels!inner(*)
          \`)
          .eq('parcel_id', parcelId)
          .single(),
        
        supabase
          .from('property_sales_history')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false })
          .limit(10),
        
        supabase
          .from('nav_assessments')
          .select('*')
          .eq('parcel_id', parcelId)
          .single()
      ]);

      if (propertyResult.error && propertyResult.error.code !== 'PGRST116') {
        throw propertyResult.error;
      }

      const combinedData = {
        property: propertyResult.data,
        salesHistory: salesResult.data || [],
        assessment: assessmentResult.data,
        timestamp: Date.now()
      };

      // Cache the result
      propertyCache.set(parcelId, {
        data: combinedData,
        timestamp: Date.now()
      });

      setData(combinedData);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to fetch property data');
      }
    } finally {
      setLoading(false);
    }
  }, [parcelId]);

  useEffect(() => {
    if (parcelId) {
      fetchPropertyData();
    }

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [parcelId, fetchPropertyData]);

  return { data, loading, error, refetch: fetchPropertyData };
}