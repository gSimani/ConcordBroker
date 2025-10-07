// Property Service - Direct API connections for localhost testing
import { supabase } from '@/lib/supabase';

export interface Property {
  parcel_id: string;
  id?: string;
  phy_addr1?: string;
  phy_addr2?: string;
  phy_city?: string;
  phy_zip?: string;
  phy_zipcd?: string;
  own_name?: string;
  jv?: number;
  just_value?: number;
  tv_sd?: number;
  taxable_value?: number;
  lnd_val?: number;
  land_value?: number;
  tot_lvg_area?: number;
  living_area?: number;
  lnd_sqfoot?: number;
  total_sq_ft?: number;
  act_yr_blt?: number;
  year_built?: number;
  dor_uc?: string;
  property_use_code?: string;
  county?: string;
  [key: string]: any;
}

export interface PropertySearchParams {
  county?: string;
  city?: string;
  address?: string;
  owner?: string;
  propertyType?: string;
  minPrice?: number;
  maxPrice?: number;
  limit?: number;
  offset?: number;
}

class PropertyService {
  private baseUrl = 'http://localhost:8001';
  private mcpUrl = 'http://localhost:3005';
  private mcpApiKey = 'concordbroker-mcp-key-claude';

  // Sample data for immediate testing
  private sampleProperties: Property[] = [
    {
      parcel_id: '064210010010',
      phy_addr1: '123 Main Street',
      phy_city: 'Fort Lauderdale',
      phy_zipcd: '33301',
      own_name: 'John Smith',
      jv: 450000,
      lnd_val: 180000,
      tot_lvg_area: 2200,
      lnd_sqfoot: 8500,
      act_yr_blt: 2005,
      dor_uc: '001',
      county: 'BROWARD'
    },
    {
      parcel_id: '064210020030',
      phy_addr1: '456 Oak Avenue',
      phy_city: 'Hollywood',
      phy_zipcd: '33020',
      own_name: 'Jane Doe',
      jv: 320000,
      lnd_val: 120000,
      tot_lvg_area: 1800,
      lnd_sqfoot: 7200,
      act_yr_blt: 1998,
      dor_uc: '001',
      county: 'BROWARD'
    },
    {
      parcel_id: '064230040050',
      phy_addr1: '789 Pine Street',
      phy_city: 'Pompano Beach',
      phy_zipcd: '33062',
      own_name: 'ABC Properties LLC',
      jv: 875000,
      lnd_val: 300000,
      tot_lvg_area: 3200,
      lnd_sqfoot: 12000,
      act_yr_blt: 2018,
      dor_uc: '002',
      county: 'BROWARD'
    },
    {
      parcel_id: '064240050060',
      phy_addr1: '321 Palm Boulevard',
      phy_city: 'Coral Springs',
      phy_zipcd: '33071',
      own_name: 'Miami Investment Group',
      jv: 625000,
      lnd_val: 220000,
      tot_lvg_area: 2800,
      lnd_sqfoot: 9800,
      act_yr_blt: 2012,
      dor_uc: '001',
      county: 'BROWARD'
    },
    {
      parcel_id: '064250060070',
      phy_addr1: '654 Sunset Drive',
      phy_city: 'Davie',
      phy_zipcd: '33328',
      own_name: 'Robert Wilson',
      jv: 750000,
      lnd_val: 280000,
      tot_lvg_area: 3500,
      lnd_sqfoot: 15000,
      act_yr_blt: 2015,
      dor_uc: '001',
      county: 'BROWARD'
    }
  ];

  async searchProperties(params: PropertySearchParams): Promise<{ properties: Property[], total: number }> {
    console.log('PropertyService.searchProperties called with:', params);

    try {
      // Try MCP API first
      const mcpResult = await this.tryMcpApi(params);
      if (mcpResult) {
        return mcpResult;
      }
    } catch (error) {
      console.log('MCP API failed, trying direct API:', error);
    }

    try {
      // Try direct Python API
      const directResult = await this.tryDirectApi(params);
      if (directResult) {
        return directResult;
      }
    } catch (error) {
      console.log('Direct API failed, trying Supabase:', error);
    }

    try {
      // Try Supabase direct
      const supabaseResult = await this.trySupabaseApi(params);
      if (supabaseResult) {
        return supabaseResult;
      }
    } catch (error) {
      console.log('Supabase failed, using sample data:', error);
    }

    // Fallback to sample data with filtering
    return this.filterSampleData(params);
  }

  private async tryMcpApi(params: PropertySearchParams): Promise<{ properties: Property[], total: number } | null> {
    const queryParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString());
      }
    });

    const response = await fetch(`${this.mcpUrl}/api/supabase/florida_parcels?${queryParams}`, {
      headers: {
        'x-api-key': this.mcpApiKey,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`MCP API error: ${response.status}`);
    }

    const data = await response.json();

    return {
      properties: Array.isArray(data) ? data : data.data || [],
      total: Array.isArray(data) ? data.length : data.total || data.count || 0
    };
  }

  private async tryDirectApi(params: PropertySearchParams): Promise<{ properties: Property[], total: number } | null> {
    const queryParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString());
      }
    });

    const response = await fetch(`${this.baseUrl}/api/properties/search?${queryParams}`);

    if (!response.ok) {
      throw new Error(`Direct API error: ${response.status}`);
    }

    const data = await response.json();

    return {
      properties: data.properties || [],
      total: data.total || 0
    };
  }

  private async trySupabaseApi(params: PropertySearchParams): Promise<{ properties: Property[], total: number } | null> {
    let query = supabase
      .from('florida_parcels')
      .select('*', { count: 'exact' });

    // Apply filters
    if (params.county) {
      query = query.eq('county', params.county);
    }
    if (params.city) {
      query = query.ilike('phy_city', `%${params.city}%`);
    }
    if (params.address) {
      query = query.ilike('phy_addr1', `%${params.address}%`);
    }
    if (params.owner) {
      query = query.ilike('own_name', `%${params.owner}%`);
    }
    if (params.minPrice) {
      query = query.gte('jv', params.minPrice);
    }
    if (params.maxPrice) {
      query = query.lte('jv', params.maxPrice);
    }

    // Apply pagination
    if (params.offset) {
      query = query.range(params.offset, (params.offset + (params.limit || 50)) - 1);
    } else {
      query = query.limit(params.limit || 50);
    }

    const { data, error, count } = await query;

    if (error) {
      throw new Error(`Supabase error: ${error.message}`);
    }

    return {
      properties: data || [],
      total: count || 0
    };
  }

  private filterSampleData(params: PropertySearchParams): { properties: Property[], total: number } {
    console.log('PropertyService.filterSampleData - Using sample data with filters:', params);
    console.log('PropertyService.filterSampleData - Sample properties before filtering:', this.sampleProperties);
    console.log('PropertyService.filterSampleData - First sample property jv value:', this.sampleProperties[0]?.jv);

    let filtered = [...this.sampleProperties];

    // Apply filters
    if (params.county && params.county !== 'BROWARD') {
      // For non-Broward counties, return empty (since our sample is all Broward)
      return { properties: [], total: 0 };
    }

    if (params.city && params.city !== 'all-cities') {
      filtered = filtered.filter(p =>
        p.phy_city?.toLowerCase().includes(params.city!.toLowerCase())
      );
    }

    if (params.address) {
      filtered = filtered.filter(p =>
        p.phy_addr1?.toLowerCase().includes(params.address!.toLowerCase())
      );
    }

    if (params.owner) {
      filtered = filtered.filter(p =>
        p.own_name?.toLowerCase().includes(params.owner!.toLowerCase())
      );
    }

    if (params.minPrice) {
      filtered = filtered.filter(p => (p.jv || 0) >= params.minPrice!);
    }

    if (params.maxPrice) {
      filtered = filtered.filter(p => (p.jv || 0) <= params.maxPrice!);
    }

    // Apply pagination
    const offset = params.offset || 0;
    const limit = params.limit || 50;
    const paginatedResults = filtered.slice(offset, offset + limit);

    const result = {
      properties: paginatedResults,
      total: filtered.length
    };

    console.log('PropertyService.filterSampleData - Returning sample data result:', result);
    console.log('PropertyService.filterSampleData - First property data:', paginatedResults[0]);
    console.log('PropertyService.filterSampleData - First property jv field specifically:', paginatedResults[0]?.jv);

    return result;
  }

  // Method to get property by ID
  async getPropertyById(parcelId: string): Promise<Property | null> {
    try {
      // Try MCP first
      const response = await fetch(`${this.mcpUrl}/api/supabase/florida_parcels?parcel_id=eq.${parcelId}`, {
        headers: {
          'x-api-key': this.mcpApiKey,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        return Array.isArray(data) && data.length > 0 ? data[0] : null;
      }
    } catch (error) {
      console.log('MCP API failed for single property, trying sample data');
    }

    // Fallback to sample data
    return this.sampleProperties.find(p => p.parcel_id === parcelId) || null;
  }

  // Get property counts by county
  async getPropertyCounts(): Promise<{ [county: string]: number }> {
    try {
      const { data, error } = await supabase
        .from('florida_parcels')
        .select('county', { count: 'exact' });

      if (!error && data) {
        // For now, return sample counts
        return {
          'BROWARD': 789456,
          'MIAMI-DADE': 892341,
          'PALM BEACH': 567234,
          'ORANGE': 445678,
          'HILLSBOROUGH': 523789
        };
      }
    } catch (error) {
      console.log('Error getting property counts:', error);
    }

    // Fallback sample counts
    return {
      'BROWARD': 789456,
      'MIAMI-DADE': 892341,
      'PALM BEACH': 567234
    };
  }
}

export const propertyService = new PropertyService();
export default propertyService;