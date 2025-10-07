import { supabase } from '@/lib/supabase';

export interface DORUseCodeDB {
  code: string;
  category: string;
  subcategory: string | null;
  description: string;
  color_class: string;
  bg_color_class: string;
  border_color_class: string;
  is_residential: boolean;
  is_commercial: boolean;
  is_industrial: boolean;
  is_agricultural: boolean;
  is_institutional: boolean;
  is_governmental: boolean;
  is_vacant: boolean;
  typical_use: string | null;
  created_at: string;
  updated_at: string;
}

export interface PropertyWithDOR {
  parcel_id: string;
  county: string;
  owner_name: string;
  property_address: string;
  dor_uc: string;
  dor_category: string;
  dor_subcategory: string | null;
  dor_description: string;
  is_residential: boolean;
  is_commercial: boolean;
  is_vacant: boolean;
  just_value: number;
  assessed_value: number;
}

export interface PropertyStatsByCategory {
  category: string;
  property_count: number;
  total_just_value: number;
  avg_just_value: number;
  total_assessed_value: number;
  avg_assessed_value: number;
}

class DORUseCodeService {
  /**
   * Get a single DOR use code by code
   */
  async getDORUseCode(code: string | number): Promise<DORUseCodeDB | null> {
    try {
      // Pad the code with zeros if needed
      const paddedCode = String(code).padStart(3, '0');

      const { data, error } = await supabase
        .from('dor_use_codes')
        .select('*')
        .eq('code', paddedCode)
        .single();

      if (error) {
        console.error('Error fetching DOR use code:', error);
        return null;
      }

      return data;
    } catch (error) {
      console.error('Error in getDORUseCode:', error);
      return null;
    }
  }

  /**
   * Get all DOR use codes
   */
  async getAllDORUseCodes(): Promise<DORUseCodeDB[]> {
    try {
      const { data, error } = await supabase
        .from('dor_use_codes')
        .select('*')
        .order('code');

      if (error) {
        console.error('Error fetching all DOR use codes:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in getAllDORUseCodes:', error);
      return [];
    }
  }

  /**
   * Get DOR use codes by category
   */
  async getDORUseCodesByCategory(category: string): Promise<DORUseCodeDB[]> {
    try {
      const { data, error } = await supabase
        .from('dor_use_codes')
        .select('*')
        .eq('category', category)
        .order('code');

      if (error) {
        console.error('Error fetching DOR use codes by category:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in getDORUseCodesByCategory:', error);
      return [];
    }
  }

  /**
   * Get all residential DOR use codes
   */
  async getResidentialCodes(): Promise<DORUseCodeDB[]> {
    try {
      const { data, error } = await supabase
        .from('v_dor_residential_codes')
        .select('*')
        .order('code');

      if (error) {
        console.error('Error fetching residential codes:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in getResidentialCodes:', error);
      return [];
    }
  }

  /**
   * Get all commercial DOR use codes
   */
  async getCommercialCodes(): Promise<DORUseCodeDB[]> {
    try {
      const { data, error } = await supabase
        .from('v_dor_commercial_codes')
        .select('*')
        .order('code');

      if (error) {
        console.error('Error fetching commercial codes:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in getCommercialCodes:', error);
      return [];
    }
  }

  /**
   * Get all vacant property codes
   */
  async getVacantCodes(): Promise<DORUseCodeDB[]> {
    try {
      const { data, error } = await supabase
        .from('v_dor_vacant_codes')
        .select('*')
        .order('code');

      if (error) {
        console.error('Error fetching vacant codes:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in getVacantCodes:', error);
      return [];
    }
  }

  /**
   * Get property with DOR details by parcel ID
   */
  async getPropertyWithDORDetails(parcelId: string): Promise<PropertyWithDOR | null> {
    try {
      const { data, error } = await supabase
        .rpc('get_property_with_dor_details', { p_parcel_id: parcelId });

      if (error) {
        console.error('Error fetching property with DOR details:', error);
        return null;
      }

      return data?.[0] || null;
    } catch (error) {
      console.error('Error in getPropertyWithDORDetails:', error);
      return null;
    }
  }

  /**
   * Get property statistics by DOR category
   */
  async getPropertyStatsByCategory(county?: string): Promise<PropertyStatsByCategory[]> {
    try {
      const { data, error } = await supabase
        .rpc('get_property_stats_by_dor_category', {
          p_county: county || null
        });

      if (error) {
        console.error('Error fetching property stats by category:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in getPropertyStatsByCategory:', error);
      return [];
    }
  }

  /**
   * Get category summary from materialized view
   */
  async getCategorySummary(): Promise<{ category: string; code_count: number; codes: string[] }[]> {
    try {
      const { data, error } = await supabase
        .from('mv_dor_category_summary')
        .select('*')
        .order('category');

      if (error) {
        console.error('Error fetching category summary:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in getCategorySummary:', error);
      return [];
    }
  }

  /**
   * Search properties with DOR categorization
   */
  async searchPropertiesWithDOR(
    filters: {
      county?: string;
      dor_category?: string;
      dor_subcategory?: string;
      is_vacant?: boolean;
      is_residential?: boolean;
      is_commercial?: boolean;
      min_value?: number;
      max_value?: number;
    },
    limit: number = 100
  ) {
    try {
      let query = supabase
        .from('v_properties_with_dor')
        .select('*');

      // Apply filters
      if (filters.county) {
        query = query.eq('county', filters.county);
      }
      if (filters.dor_category) {
        query = query.eq('dor_category', filters.dor_category);
      }
      if (filters.dor_subcategory) {
        query = query.eq('dor_subcategory', filters.dor_subcategory);
      }
      if (filters.is_vacant !== undefined) {
        query = query.eq('is_vacant', filters.is_vacant);
      }
      if (filters.is_residential !== undefined) {
        query = query.eq('is_residential', filters.is_residential);
      }
      if (filters.is_commercial !== undefined) {
        query = query.eq('is_commercial', filters.is_commercial);
      }
      if (filters.min_value) {
        query = query.gte('just_value', filters.min_value);
      }
      if (filters.max_value) {
        query = query.lte('just_value', filters.max_value);
      }

      // Apply limit and ordering
      query = query.limit(limit).order('just_value', { ascending: false });

      const { data, error } = await query;

      if (error) {
        console.error('Error searching properties with DOR:', error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error('Error in searchPropertiesWithDOR:', error);
      return [];
    }
  }

  /**
   * Refresh the materialized view for category summary
   */
  async refreshCategorySummary(): Promise<boolean> {
    try {
      const { error } = await supabase
        .rpc('refresh_dor_category_summary');

      if (error) {
        console.error('Error refreshing category summary:', error);
        return false;
      }

      return true;
    } catch (error) {
      console.error('Error in refreshCategorySummary:', error);
      return false;
    }
  }
}

// Export singleton instance
export const dorUseCodeService = new DORUseCodeService();