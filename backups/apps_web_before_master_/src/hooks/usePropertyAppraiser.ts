import { useState, useEffect, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Initialize Supabase client
const supabase = SUPABASE_ANON_KEY 
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;

export interface PropertyAssessment {
  id?: number;
  parcel_id: string;
  county_code?: string;
  county_name?: string;
  owner_name?: string;
  owner_address?: string;
  owner_city?: string;
  owner_state?: string;
  owner_zip?: string;
  property_address?: string;
  property_city?: string;
  property_zip?: string;
  property_use_code?: string;
  tax_district?: string;
  subdivision?: string;
  just_value?: number;
  assessed_value?: number;
  taxable_value?: number;
  land_value?: number;
  building_value?: number;
  total_sq_ft?: number;
  living_area?: number;
  year_built?: number;
  bedrooms?: number;
  bathrooms?: number;
  pool?: boolean;
  tax_year?: number;
  created_at?: string;
  updated_at?: string;
}

export interface PropertySearchParams {
  q?: string;
  county?: string;
  minValue?: number;
  maxValue?: number;
  propertyType?: string;
  limit?: number;
  offset?: number;
}

export const usePropertyAppraiser = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search properties from Property Appraiser data
  const searchProperties = useCallback(async (params: PropertySearchParams) => {
    setLoading(true);
    setError(null);

    try {
      // Try API first
      const queryParams = new URLSearchParams();
      if (params.q) queryParams.append('q', params.q);
      if (params.county) queryParams.append('county', params.county);
      if (params.minValue) queryParams.append('min_value', params.minValue.toString());
      if (params.maxValue) queryParams.append('max_value', params.maxValue.toString());
      if (params.propertyType) queryParams.append('property_type', params.propertyType);
      if (params.limit) queryParams.append('limit', params.limit.toString());
      if (params.offset) queryParams.append('offset', params.offset.toString());

      const response = await fetch(`${API_URL}/api/property-appraiser/search?${queryParams}`);
      
      if (response.ok) {
        const data = await response.json();
        return data.properties || [];
      }

      // Fallback to direct Supabase query if API fails
      if (supabase) {
        let query = supabase
          .from('property_assessments')
          .select('*');

        // Apply search filter
        if (params.q) {
          query = query.or(`owner_name.ilike.%${params.q}%,property_address.ilike.%${params.q}%,parcel_id.eq.${params.q}`);
        }

        // Apply county filter
        if (params.county) {
          if (params.county.length === 2) {
            query = query.eq('county_code', params.county);
          } else {
            query = query.ilike('county_name', `%${params.county}%`);
          }
        }

        // Apply value filters
        if (params.minValue) {
          query = query.gte('taxable_value', params.minValue);
        }
        if (params.maxValue) {
          query = query.lte('taxable_value', params.maxValue);
        }

        // Apply property type filter
        if (params.propertyType) {
          query = query.eq('property_use_code', params.propertyType);
        }

        // Apply pagination
        const limit = params.limit || 100;
        const offset = params.offset || 0;
        query = query.order('taxable_value', { ascending: false })
          .range(offset, offset + limit - 1);

        const { data, error: supabaseError } = await query;
        
        if (supabaseError) throw supabaseError;
        return data || [];
      }

      throw new Error('Failed to fetch property data');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Get property details by parcel ID
  const getPropertyDetails = useCallback(async (parcelId: string, countyCode?: string) => {
    setLoading(true);
    setError(null);

    try {
      // Try API first
      const url = countyCode 
        ? `${API_URL}/api/property-appraiser/property/${parcelId}?county_code=${countyCode}`
        : `${API_URL}/api/property-appraiser/property/${parcelId}`;

      const response = await fetch(url);
      
      if (response.ok) {
        const data = await response.json();
        return data.property;
      }

      // Fallback to direct Supabase query
      if (supabase) {
        let query = supabase
          .from('property_assessments')
          .select('*')
          .eq('parcel_id', parcelId);

        if (countyCode) {
          query = query.eq('county_code', countyCode);
        }

        const { data, error: supabaseError } = await query.single();
        
        if (supabaseError) throw supabaseError;
        return data;
      }

      throw new Error('Property not found');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get top properties by value
  const getTopProperties = useCallback(async (countyCode?: string, limit: number = 10) => {
    setLoading(true);
    setError(null);

    try {
      // Try API first
      const queryParams = new URLSearchParams();
      if (countyCode) queryParams.append('county_code', countyCode);
      queryParams.append('limit', limit.toString());

      const response = await fetch(`${API_URL}/api/property-appraiser/top-properties?${queryParams}`);
      
      if (response.ok) {
        const data = await response.json();
        return data.properties || [];
      }

      // Fallback to direct Supabase query
      if (supabase) {
        let query = supabase
          .from('property_assessments')
          .select('parcel_id, owner_name, property_address, property_city, county_name, taxable_value, total_sq_ft, year_built');

        if (countyCode) {
          query = query.eq('county_code', countyCode);
        }

        query = query
          .order('taxable_value', { ascending: false })
          .limit(limit);

        const { data, error: supabaseError } = await query;
        
        if (supabaseError) throw supabaseError;
        return data || [];
      }

      return [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Get available counties
  const getCounties = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Try API first
      const response = await fetch(`${API_URL}/api/property-appraiser/counties`);
      
      if (response.ok) {
        const data = await response.json();
        return data.counties || [];
      }

      // Fallback to direct Supabase query
      if (supabase) {
        const { data, error: supabaseError } = await supabase
          .from('property_assessments')
          .select('county_code, county_name')
          .order('county_name');

        if (supabaseError) throw supabaseError;

        // Deduplicate counties
        const countyMap = new Map();
        data?.forEach(item => {
          const key = `${item.county_code}_${item.county_name}`;
          if (!countyMap.has(key)) {
            countyMap.set(key, {
              county_code: item.county_code,
              county_name: item.county_name
            });
          }
        });

        return Array.from(countyMap.values());
      }

      return [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Get property statistics
  const getStatistics = useCallback(async (countyCode?: string) => {
    setLoading(true);
    setError(null);

    try {
      const queryParams = countyCode ? `?county_code=${countyCode}` : '';
      const response = await fetch(`${API_URL}/api/property-appraiser/statistics${queryParams}`);
      
      if (response.ok) {
        const data = await response.json();
        return data.statistics;
      }

      return null;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    searchProperties,
    getPropertyDetails,
    getTopProperties,
    getCounties,
    getStatistics
  };
};