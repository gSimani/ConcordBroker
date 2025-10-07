import { useState, useEffect, useCallback } from 'react';
import { parcelService } from '@/lib/supabase';

interface PropertyFilters {
  county?: string;
  city?: string;
  address?: string;
  minPrice?: number;
  maxPrice?: number;
  propertyType?: string;
  hasForeclosure?: boolean;
  hasTaxDeed?: boolean;
  hasTaxLien?: boolean;
  limit?: number;
  offset?: number;
}

export function useSupabaseProperties(initialFilters: PropertyFilters = {}) {
  const [properties, setProperties] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState<PropertyFilters>({
    limit: 100,
    offset: 0,
    county: 'BROWARD', // Default to Broward for immediate results
    ...initialFilters
  });

  const fetchProperties = useCallback(async (searchFilters: PropertyFilters) => {
    setLoading(true);
    setError(null);

    try {
      console.log('Fetching properties with filters:', searchFilters);

      const result = await parcelService.getParcels({
        county: searchFilters.county,
        city: searchFilters.city,
        minPrice: searchFilters.minPrice,
        maxPrice: searchFilters.maxPrice,
        propertyType: searchFilters.propertyType,
        hasForeclosure: searchFilters.hasForeclosure,
        hasTaxDeed: searchFilters.hasTaxDeed,
        hasTaxLien: searchFilters.hasTaxLien,
        limit: searchFilters.limit || 100,
        offset: searchFilters.offset || 0
      });

      if (result.error) {
        throw result.error;
      }

      console.log(`Fetched ${result.data?.length || 0} properties, total count: ${result.count}`);

      setProperties(result.data || []);
      setTotal(result.count || 0);
    } catch (err: any) {
      console.error('Error fetching properties:', err);
      setError(err.message || 'Failed to fetch properties');
      setProperties([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const searchByAddress = useCallback(async (address: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await parcelService.searchByAddress(address, filters.county);
      setProperties(result || []);
      setTotal(result?.length || 0);
    } catch (err: any) {
      console.error('Error searching by address:', err);
      setError(err.message || 'Failed to search properties');
      setProperties([]);
    } finally {
      setLoading(false);
    }
  }, [filters.county]);

  const getRecentSales = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await parcelService.getRecentSales(filters.county, 50);
      setProperties(result || []);
      setTotal(result?.length || 0);
    } catch (err: any) {
      console.error('Error fetching recent sales:', err);
      setError(err.message || 'Failed to fetch recent sales');
      setProperties([]);
    } finally {
      setLoading(false);
    }
  }, [filters.county]);

  const getHighValueProperties = useCallback(async (minValue: number = 1000000) => {
    setLoading(true);
    setError(null);

    try {
      const result = await parcelService.getHighValueProperties(filters.county, minValue);
      setProperties(result || []);
      setTotal(result?.length || 0);
    } catch (err: any) {
      console.error('Error fetching high value properties:', err);
      setError(err.message || 'Failed to fetch high value properties');
      setProperties([]);
    } finally {
      setLoading(false);
    }
  }, [filters.county]);

  const updateFilters = useCallback((newFilters: Partial<PropertyFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    fetchProperties(updatedFilters);
  }, [filters, fetchProperties]);

  const loadMore = useCallback(() => {
    const newOffset = (filters.offset || 0) + (filters.limit || 100);
    updateFilters({ offset: newOffset });
  }, [filters, updateFilters]);

  const resetFilters = useCallback(() => {
    const defaultFilters = {
      limit: 100,
      offset: 0,
      county: 'BROWARD'
    };
    setFilters(defaultFilters);
    fetchProperties(defaultFilters);
  }, [fetchProperties]);

  // Load initial data
  useEffect(() => {
    fetchProperties(filters);
  }, []); // Only run once on mount

  return {
    properties,
    loading,
    error,
    total,
    filters,
    updateFilters,
    searchByAddress,
    getRecentSales,
    getHighValueProperties,
    loadMore,
    resetFilters,
    refresh: () => fetchProperties(filters)
  };
}