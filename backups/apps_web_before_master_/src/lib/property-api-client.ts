/**
 * Optimized Property API Client
 * High-performance client for property detail data
 */

export interface PropertyAddress {
  street: string;
  city: string;
  state: string;
  zip: string;
  full: string;
}

export interface PropertyOwner {
  name: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  is_business: boolean;
}

export interface PropertyValues {
  market_value: number;
  assessed_value: number;
  taxable_value: number;
  land_value: number;
  building_value: number;
  extra_features_value: number;
}

export interface PropertyCharacteristics {
  property_type: string;
  property_use: string;
  year_built: number;
  effective_year_built: number;
  living_area: number;
  total_area: number;
  bedrooms: number;
  bathrooms: number;
  half_bathrooms: number;
  stories: number;
  units: number;
  lot_size: number;
  pool: boolean;
  garage_spaces: number;
}

export interface PropertyLegal {
  description: string;
  subdivision: string;
  plat_book: string;
  plat_page: string;
  block: string;
  lot: string;
  section: string;
  township: string;
  range: string;
}

export interface PropertyExemptions {
  homestead: boolean;
  senior: boolean;
  veteran: boolean;
  widow: boolean;
  disability: boolean;
  agricultural: boolean;
  total_exemption_value: number;
}

export interface SaleRecord {
  sale_date: string;
  sale_price: number;
  sale_type: string;
  qualification_code: string;
  book?: string;
  page?: string;
  instrument_number?: string;
  grantor?: string;
  grantee?: string;
}

export interface TaxRecord {
  year: number;
  amount: number;
  paid: boolean;
}

export interface TaxInfo {
  annual_taxes: number;
  tax_year: number;
  millage_rate: number;
  exemptions: string[];
  tax_history: TaxRecord[];
}

export interface SunbizEntity {
  entity_name: string;
  entity_type: string;
  filing_number: string;
  status: string;
  filing_date: string;
  principal_address: string;
  registered_agent: string;
  officers: any[];
}

export interface BuildingPermit {
  permit_number: string;
  permit_type: string;
  description: string;
  issue_date: string;
  status: string;
  contractor: string;
  estimated_value: number;
}

export interface TaxDeedSale {
  certificate_number: string;
  auction_date: string;
  opening_bid: number;
  sold_amount: number;
  status: string;
  auction_type: string;
  redemption_deadline: string;
}

export interface Comparable {
  parcel_id: string;
  address: string;
  value: number;
  sqft: number;
  bedrooms: number;
  bathrooms: number;
  year_built: number;
}

export interface PropertyDetail {
  parcel_id: string;
  folio: string;
  county: string;
  address: PropertyAddress;
  owner: PropertyOwner;
  values: PropertyValues;
  characteristics: PropertyCharacteristics;
  legal: PropertyLegal;
  exemptions: PropertyExemptions;
  sales_history?: SaleRecord[];
  tax_info?: TaxInfo;
  sunbiz_data?: SunbizEntity[];
  permits?: BuildingPermit[];
  tax_deed_sales?: TaxDeedSale[];
  comparables?: Comparable[];
  _metadata?: {
    source: string;
    last_updated: string;
    response_time_ms: number;
    cache_hit: boolean;
  };
}

export interface QuickPropertyData {
  parcel_id: string;
  address: string;
  owner: string;
  value: number;
  sqft: number;
  bedrooms: number;
  bathrooms: number;
  year_built: number;
  _response_time_ms: number;
}

export interface TabData {
  tab: string;
  parcel_id: string;
  data: any;
  timestamp: string;
}

export class PropertyApiClient {
  private baseUrl: string;
  private cache: Map<string, { data: any; expires: number }> = new Map();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  private getCachedData<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && cached.expires > Date.now()) {
      return cached.data as T;
    }
    this.cache.delete(key);
    return null;
  }

  private setCachedData(key: string, data: any, ttl: number = this.CACHE_TTL) {
    this.cache.set(key, {
      data,
      expires: Date.now() + ttl
    });
  }

  private async makeRequest<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get complete property details with all related data
   */
  async getPropertyDetail(
    parcelId: string,
    options: {
      includeSales?: boolean;
      includeTax?: boolean;
      includeSunbiz?: boolean;
      includePermits?: boolean;
      includeTaxDeeds?: boolean;
      includeComparables?: boolean;
    } = {}
  ): Promise<PropertyDetail> {
    const cacheKey = `property-${parcelId}`;

    // Check cache first
    const cached = this.getCachedData<PropertyDetail>(cacheKey);
    if (cached) {
      return cached;
    }

    const params = new URLSearchParams();
    if (options.includeSales !== undefined) params.set('include_sales', String(options.includeSales));
    if (options.includeTax !== undefined) params.set('include_tax', String(options.includeTax));
    if (options.includeSunbiz !== undefined) params.set('include_sunbiz', String(options.includeSunbiz));
    if (options.includePermits !== undefined) params.set('include_permits', String(options.includePermits));
    if (options.includeTaxDeeds !== undefined) params.set('include_tax_deeds', String(options.includeTaxDeeds));
    if (options.includeComparables !== undefined) params.set('include_comparables', String(options.includeComparables));

    const endpoint = `/api/properties/${encodeURIComponent(parcelId)}?${params.toString()}`;
    const data = await this.makeRequest<PropertyDetail>(endpoint);

    // Cache the response
    this.setCachedData(cacheKey, data);

    return data;
  }

  /**
   * Get minimal property data for ultra-fast loading
   */
  async getPropertyQuick(parcelId: string): Promise<QuickPropertyData> {
    const cacheKey = `quick-${parcelId}`;

    // Check cache first
    const cached = this.getCachedData<QuickPropertyData>(cacheKey);
    if (cached) {
      return cached;
    }

    const endpoint = `/api/properties/${encodeURIComponent(parcelId)}/quick`;
    const data = await this.makeRequest<QuickPropertyData>(endpoint);

    // Cache for longer since it's basic data
    this.setCachedData(cacheKey, data, 10 * 60 * 1000); // 10 minutes

    return data;
  }

  /**
   * Get specific tab data on-demand
   */
  async getPropertyTabData(parcelId: string, tabName: string): Promise<TabData> {
    const cacheKey = `tab-${tabName}-${parcelId}`;

    // Check cache first
    const cached = this.getCachedData<TabData>(cacheKey);
    if (cached) {
      return cached;
    }

    const endpoint = `/api/properties/${encodeURIComponent(parcelId)}/tabs/${tabName}`;
    const data = await this.makeRequest<TabData>(endpoint);

    // Cache tab data
    this.setCachedData(cacheKey, data);

    return data;
  }

  /**
   * Preload property data for faster navigation
   */
  async preloadProperty(parcelId: string): Promise<void> {
    // Start with quick data
    this.getPropertyQuick(parcelId).catch(() => {
      // Ignore errors for preloading
    });

    // Then preload full data in background
    setTimeout(() => {
      this.getPropertyDetail(parcelId, {
        includeSales: true,
        includeTax: true,
        includeSunbiz: true,
        includePermits: false, // Don't preload heavy data
        includeTaxDeeds: false,
        includeComparables: false
      }).catch(() => {
        // Ignore errors for preloading
      });
    }, 100);
  }

  /**
   * Clear cache for a specific property or all cache
   */
  clearCache(parcelId?: string): void {
    if (parcelId) {
      const keysToDelete = Array.from(this.cache.keys()).filter(key =>
        key.includes(parcelId)
      );
      keysToDelete.forEach(key => this.cache.delete(key));
    } else {
      this.cache.clear();
    }
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }

  /**
   * Batch load multiple properties
   */
  async batchLoadProperties(parcelIds: string[]): Promise<Map<string, PropertyDetail>> {
    const results = new Map<string, PropertyDetail>();

    // Load in parallel with concurrency limit
    const BATCH_SIZE = 5;
    for (let i = 0; i < parcelIds.length; i += BATCH_SIZE) {
      const batch = parcelIds.slice(i, i + BATCH_SIZE);
      const promises = batch.map(async (parcelId) => {
        try {
          const data = await this.getPropertyDetail(parcelId);
          results.set(parcelId, data);
        } catch (error) {
          console.error(`Failed to load property ${parcelId}:`, error);
        }
      });

      await Promise.all(promises);
    }

    return results;
  }
}

// Create singleton instance
export const propertyApiClient = new PropertyApiClient();

// Helper function to format currency
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
}

// Helper function to format date
export function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A';

  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch {
    return 'N/A';
  }
}

// Helper function to format number with commas
export function formatNumber(value: number): string {
  return value.toLocaleString('en-US');
}

// Helper function to calculate price per square foot
export function calculatePricePerSqft(value: number, sqft: number): number {
  if (sqft <= 0) return 0;
  return value / sqft;
}