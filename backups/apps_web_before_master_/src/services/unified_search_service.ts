/**
 * Unified Search Service - Production Supabase Data Only
 * Ensures ALL components use the same real data source
 */

export interface DatasetSummary {
  supabase_url: string;
  project_ref: string;
  table_used: string;
  total_properties: number;
  sample_counties: string[];
  last_updated: string | null;
  is_production_dataset: boolean;
  samples_ok: boolean;
  status: 'production' | 'limited' | 'error';
  response_time_ms: number;
  timestamp: string;
}

export interface PropertyCard {
  parcel_id: string;
  address: string;
  city: string;
  zip: string;
  full_address: string;
  owner_name: string;
  use_category: string;
  county: string;
  market_value: number;
  assessed_value: number;
  year_built: number;
  living_area: number;
  bedrooms: number;
  bathrooms: number;
  lot_size: number;
}

export interface SearchParams {
  query?: string;
  county?: string;
  use_categories?: string[];
  limit?: number;
  offset?: number;
}

export interface SearchResponse {
  properties: PropertyCard[];
  total_found: number;
  search_params: SearchParams;
  metadata: {
    source: string;
    table_used: string;
    is_production: boolean;
    response_time_ms: number;
    timestamp: string;
  };
}

export interface AutocompleteSuggestion {
  parcel_id: string;
  display_text: string;
  address: string;
  city: string;
  zip: string;
  owner: string;
  county: string;
  type: string;
}

export interface AutocompleteResponse {
  suggestions: AutocompleteSuggestion[];
  total: number;
  search_query: string;
  county_filter?: string;
  metadata: {
    source: string;
    response_time_ms: number;
    timestamp: string;
  };
}

class UnifiedSearchService {
  private readonly API_BASE: string;
  private datasetCache: DatasetSummary | null = null;
  private cacheExpiry: number = 0;

  constructor() {
    // Use production API base - NO fallbacks to mock/optimized APIs
    this.API_BASE = (import.meta.env.VITE_API_BASE ?? '').trim();

    // Log which API we're using for debugging
    console.log('🏭 UnifiedSearchService initialized with API:', this.API_BASE);
  }

  /**
   * Get dataset summary to verify production data
   * Cached for 5 minutes to avoid repeated calls
   */
  async getDatasetSummary(forceRefresh = false): Promise<DatasetSummary> {
    const now = Date.now();

    if (!forceRefresh && this.datasetCache && now < this.cacheExpiry) {
      return this.datasetCache;
    }

    try {
      const response = await fetch(`${this.API_BASE}/api/dataset/summary`);

      if (!response.ok) {
        throw new Error(`Dataset summary failed: ${response.status}`);
      }

      const summary: DatasetSummary = await response.json();

      // Cache for 5 minutes
      this.datasetCache = summary;
      this.cacheExpiry = now + (5 * 60 * 1000);

      // Log production status
      if (summary.is_production_dataset) {
        console.log(`✅ Production dataset verified: ${summary.total_properties.toLocaleString()} properties`);
      } else {
        console.warn(`⚠️ Limited dataset detected: ${summary.total_properties.toLocaleString()} properties`);
      }

      return summary;
    } catch (error) {
      console.error('Failed to get dataset summary:', error);

      // Return error state
      return {
        supabase_url: 'unknown',
        project_ref: 'error',
        table_used: 'error',
        total_properties: 0,
        sample_counties: [],
        last_updated: null,
        is_production_dataset: false,
        samples_ok: false,
        status: 'error',
        response_time_ms: 0,
        timestamp: new Date().toISOString()
      };
    }
  }

  /**
   * Search properties using canonical search function
   * Used by both grid and autocomplete components
   */
  async searchProperties(params: SearchParams): Promise<SearchResponse> {
    try {
      const searchParams = new URLSearchParams();

      if (params.query) searchParams.set('q', params.query);
      if (params.county && params.county !== 'ALL') searchParams.set('county', params.county);
      if (params.use_categories && params.use_categories.length > 0) {
        searchParams.set('use', params.use_categories[0]);
      }
      if (typeof (params as any).minValue === 'number') searchParams.set('minValue', String((params as any).minValue));
      if (typeof (params as any).maxValue === 'number') searchParams.set('maxValue', String((params as any).maxValue));
      if (typeof (params as any).minBeds === 'number') searchParams.set('minBeds', String((params as any).minBeds));
      if (typeof (params as any).minBaths === 'number') searchParams.set('minBaths', String((params as any).minBaths));
      if (params.limit) searchParams.set('limit', params.limit.toString());
      if (params.offset) searchParams.set('offset', params.offset.toString());

      const url = `${this.API_BASE}/api/properties/search?${searchParams.toString()}`;

      console.log('🔍 Searching properties:', { params, url });

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Property search failed: ${response.status}`);
      }

      const raw = await response.json();

      if (raw && typeof raw === 'object' && 'success' in raw && 'data' in raw) {
        const properties: PropertyCard[] = (raw.data || []).map((p: any) => ({
          parcel_id: p.parcel_id,
          address: p.address,
          city: p.city,
          zip: p.zipCode,
          full_address: `${p.address || ''}, ${p.city || ''}, FL ${p.zipCode || ''}`.trim(),
          owner_name: p.owner,
          use_category: p.propertyType,
          county: p.county,
          market_value: p.marketValue,
          assessed_value: p.assessedValue,
          year_built: p.yearBuilt,
          living_area: p.buildingSqFt,
          bedrooms: p.bedrooms,
          bathrooms: p.bathrooms,
          lot_size: p.landSqFt,
        }));

        const transformed: SearchResponse = {
          properties,
          total_found: raw.pagination?.total ?? properties.length,
          search_params: params,
          metadata: {
            source: 'ultra_fast_api',
            table_used: 'florida_parcels',
            is_production: true,
            response_time_ms: raw.performance?.query_time_ms ?? 0,
            timestamp: raw.timestamp || new Date().toISOString(),
          },
        };

        return transformed;
      }

      const result: SearchResponse = raw;
      return result;
    } catch (error) {
      console.error('Property search failed:', error);
      throw error;
    }
  }

  /**
   * Get autocomplete suggestions
   * Uses same canonical search but with minimal data
   */
  async getAutocompleteSuggestions(
    query: string,
    county?: string,
    limit = 10
  ): Promise<AutocompleteResponse> {
    try {
      if (!query || query.length < 2) {
        return {
          suggestions: [],
          total: 0,
          search_query: query,
          county_filter: county,
          metadata: {
            source: 'florida_parcels',
            response_time_ms: 0,
            timestamp: new Date().toISOString()
          }
        };
      }

      const searchParams = new URLSearchParams();
      searchParams.set('q', query);
      if (county && county !== 'ALL') searchParams.set('county', county);
      searchParams.set('limit', limit.toString());

      const base = this.API_BASE || '';
      const url = `${base}/api/autocomplete-ultra?${searchParams.toString()}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Autocomplete failed: ${response.status}`);
      }

      const result: AutocompleteResponse = await response.json();

      return result;
    } catch (error) {
      console.error('Autocomplete failed:', error);

      // Return empty results on error
      return {
        suggestions: [],
        total: 0,
        search_query: query,
        county_filter: county,
        metadata: {
          source: 'error',
          response_time_ms: 0,
          timestamp: new Date().toISOString()
        }
      };
    }
  }

  /**
   * Get property details by parcel ID
   */
  async getPropertyDetail(parcelId: string) {
    try {
      const response = await fetch(`${this.API_BASE}/api/properties/${encodeURIComponent(parcelId)}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`Property not found: ${parcelId}`);
        }
        throw new Error(`Property detail failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Property detail failed:', error);
      throw error;
    }
  }

  /**
   * Verify the service is using production data
   */
  async verifyProductionData(): Promise<boolean> {
    try {
      const summary = await this.getDatasetSummary();
      return summary.is_production_dataset && summary.total_properties > 1000000;
    } catch {
      return false;
    }
  }

  /**
   * Get service health status
   */
  async getHealthStatus() {
    try {
      const response = await fetch(`${this.API_BASE}/health`);

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      return {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Get list of available counties
   */
  async getCounties(): Promise<string[]> {
    try {
      const summary = await this.getDatasetSummary();
      return summary.sample_counties || [];
    } catch {
      return [];
    }
  }

  /**
   * Format currency values
   */
  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }

  /**
   * Format numbers with commas
   */
  formatNumber(value: number): string {
    return value.toLocaleString('en-US');
  }
}

// Export singleton instance
export const unifiedSearchService = new UnifiedSearchService();

// Export service class for testing
export { UnifiedSearchService };



