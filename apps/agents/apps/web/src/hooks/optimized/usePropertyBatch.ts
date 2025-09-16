import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/lib/supabase';

interface BatchOptions {
  pageSize?: number;
  filters?: Record<string, any>;
  orderBy?: string;
  ascending?: boolean;
}

export function usePropertyBatch(options: BatchOptions = {}) {
  const { 
    pageSize = 20, 
    filters = {}, 
    orderBy = 'assessed_value', 
    ascending = false 
  } = options;
  
  const [properties, setProperties] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(0);

  const fetchBatch = useCallback(async (pageNum: number) => {
    setLoading(true);
    
    try {
      let query = supabase
        .from('properties')
        .select('*', { count: 'exact' });

      // Apply filters
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          if (typeof value === 'string' && value.includes('%')) {
            query = query.ilike(key, value);
          } else {
            query = query.eq(key, value);
          }
        }
      });

      // Apply ordering
      query = query.order(orderBy, { ascending });

      // Apply pagination
      const from = pageNum * pageSize;
      const to = from + pageSize - 1;
      query = query.range(from, to);

      const { data, error, count } = await query;

      if (error) throw error;

      if (pageNum === 0) {
        setProperties(data || []);
      } else {
        setProperties(prev => [...prev, ...(data || [])]);
      }

      setTotalCount(count || 0);
      setHasMore((data?.length || 0) === pageSize);
      setPage(pageNum);
    } catch (error) {
      console.error('Error fetching properties:', error);
    } finally {
      setLoading(false);
    }
  }, [pageSize, filters, orderBy, ascending]);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      fetchBatch(page + 1);
    }
  }, [loading, hasMore, page, fetchBatch]);

  const reset = useCallback(() => {
    setProperties([]);
    setPage(0);
    setHasMore(true);
    fetchBatch(0);
  }, [fetchBatch]);

  useEffect(() => {
    fetchBatch(0);
  }, [filters, orderBy, ascending]);

  return {
    properties,
    loading,
    hasMore,
    totalCount,
    loadMore,
    reset
  };
}