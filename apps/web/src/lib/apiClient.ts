/**
 * Unified API Client with Automatic Fallback
 * Implements data flow priority from services.config.ts
 */
import {
  ServiceURLs,
  PropertyEndpoints,
  SupabaseEndpoints,
  MeilisearchEndpoints,
  DataFlowPriority,
  RetryConfig,
  getHeaders,
  getMeilisearchHeaders,
} from '../config/services.config';

interface RetryOptions {
  maxRetries?: number;
  retryDelay?: number;
  backoffMultiplier?: number;
}

/**
 * Retry-enabled fetch with exponential backoff
 */
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retryOptions: RetryOptions = {}
): Promise<Response> {
  const {
    maxRetries = RetryConfig.MAX_RETRIES,
    retryDelay = RetryConfig.RETRY_DELAY,
    backoffMultiplier = RetryConfig.BACKOFF_MULTIPLIER,
  } = retryOptions;

  let lastError: Error | null = null;
  let delay = retryDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), RetryConfig.TIMEOUT);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        return response;
      }

      // Don't retry on 4xx errors (client errors)
      if (response.status >= 400 && response.status < 500) {
        throw new Error(`Client error: ${response.status} ${response.statusText}`);
      }

      lastError = new Error(`HTTP ${response.status}: ${response.statusText}`);
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // Don't retry on abort or network errors
      if (lastError.name === 'AbortError' || lastError.message.includes('network')) {
        break;
      }
    }

    // Wait before retry with exponential backoff
    if (attempt < maxRetries) {
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= backoffMultiplier;
    }
  }

  throw lastError || new Error('Request failed after retries');
}

/**
 * Property Search with Fallback Chain
 * Priority: Meilisearch → Property API → Supabase Direct
 */
export async function searchProperties(query: {
  q?: string;
  filters?: Record<string, any>;
  limit?: number;
  offset?: number;
}): Promise<any> {
  const errors: Array<{ service: string; error: string }> = [];

  // Try Meilisearch first (fastest)
  try {
    const response = await fetchWithRetry(
      MeilisearchEndpoints.SEARCH,
      {
        method: 'POST',
        headers: getMeilisearchHeaders(),
        body: JSON.stringify({
          q: query.q || '',
          filter: query.filters ? buildMeilisearchFilter(query.filters) : undefined,
          limit: query.limit || 20,
          offset: query.offset || 0,
        }),
      }
    );
    const data = await response.json();
    return {
      source: 'Meilisearch',
      data: data.hits || [],
      total: data.estimatedTotalHits || 0,
    };
  } catch (error) {
    errors.push({
      service: 'Meilisearch',
      error: error instanceof Error ? error.message : String(error),
    });
  }

  // Fallback to Property API
  try {
    const url = new URL(PropertyEndpoints.SEARCH);
    if (query.q) url.searchParams.set('q', query.q);
    if (query.limit) url.searchParams.set('limit', String(query.limit));
    if (query.offset) url.searchParams.set('offset', String(query.offset));
    if (query.filters) {
      Object.entries(query.filters).forEach(([key, value]) => {
        url.searchParams.set(key, String(value));
      });
    }

    const response = await fetchWithRetry(url.toString());
    const data = await response.json();
    return {
      source: 'PropertyAPI',
      data: data.properties || data.results || [],
      total: data.total || 0,
    };
  } catch (error) {
    errors.push({
      service: 'PropertyAPI',
      error: error instanceof Error ? error.message : String(error),
    });
  }

  // Last resort: Direct Supabase query
  try {
    const url = new URL(SupabaseEndpoints.FLORIDA_PARCELS);
    url.searchParams.set('select', '*');
    url.searchParams.set('limit', String(query.limit || 20));
    url.searchParams.set('offset', String(query.offset || 0));

    // Apply basic filters
    if (query.filters) {
      Object.entries(query.filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.set(key, `eq.${value}`);
        }
      });
    }

    const response = await fetchWithRetry(
      url.toString(),
      { headers: getHeaders({ includeAuth: true }) }
    );
    const data = await response.json();
    return {
      source: 'Supabase',
      data: data || [],
      total: data.length,
    };
  } catch (error) {
    errors.push({
      service: 'Supabase',
      error: error instanceof Error ? error.message : String(error),
    });
  }

  // All services failed
  throw new Error(
    `All search services failed:\n${errors.map(e => `${e.service}: ${e.error}`).join('\n')}`
  );
}

/**
 * Get Property Details
 */
export async function getProperty(parcelId: string): Promise<any> {
  try {
    const response = await fetchWithRetry(PropertyEndpoints.GET_PROPERTY(parcelId));
    return await response.json();
  } catch (error) {
    // Fallback to Supabase
    const url = `${SupabaseEndpoints.FLORIDA_PARCELS}?parcel_id=eq.${parcelId}`;
    const response = await fetchWithRetry(
      url,
      { headers: getHeaders({ includeAuth: true }) }
    );
    const data = await response.json();
    return data[0] || null;
  }
}

/**
 * Get Sales History with Multi-Source Strategy
 * Priority: comprehensive_sales_data → property_sales_history → sdf_sales → Property API
 */
export async function getSalesHistory(parcelId: string): Promise<any> {
  const errors: Array<{ source: string; error: string }> = [];

  // Try comprehensive_sales_data view first
  try {
    const url = `${SupabaseEndpoints.COMPREHENSIVE_SALES}?parcel_id=eq.${parcelId}&order=sale_date.desc`;
    const response = await fetchWithRetry(
      url,
      { headers: getHeaders({ includeAuth: true }) }
    );
    const data = await response.json();
    if (data && data.length > 0) {
      return { source: 'comprehensive_sales_data', sales: data };
    }
  } catch (error) {
    errors.push({
      source: 'comprehensive_sales_data',
      error: error instanceof Error ? error.message : String(error),
    });
  }

  // Try property_sales_history table
  try {
    const url = `${SupabaseEndpoints.SALES_HISTORY}?parcel_id=eq.${parcelId}&order=sale_date.desc`;
    const response = await fetchWithRetry(
      url,
      { headers: getHeaders({ includeAuth: true }) }
    );
    const data = await response.json();
    if (data && data.length > 0) {
      return { source: 'property_sales_history', sales: data };
    }
  } catch (error) {
    errors.push({
      source: 'property_sales_history',
      error: error instanceof Error ? error.message : String(error),
    });
  }

  // Try sdf_sales table
  try {
    const url = `${SupabaseEndpoints.SDF_SALES}?parcel_id=eq.${parcelId}&order=sale_date.desc`;
    const response = await fetchWithRetry(
      url,
      { headers: getHeaders({ includeAuth: true }) }
    );
    const data = await response.json();
    if (data && data.length > 0) {
      return { source: 'sdf_sales', sales: data };
    }
  } catch (error) {
    errors.push({
      source: 'sdf_sales',
      error: error instanceof Error ? error.message : String(error),
    });
  }

  // Fallback to Property API
  try {
    const response = await fetchWithRetry(PropertyEndpoints.GET_SALES_HISTORY(parcelId));
    const data = await response.json();
    return { source: 'PropertyAPI', sales: data.sales || [] };
  } catch (error) {
    errors.push({
      source: 'PropertyAPI',
      error: error instanceof Error ? error.message : String(error),
    });
  }

  console.warn('All sales history sources failed:', errors);
  return { source: 'none', sales: [] };
}

/**
 * Get Corporate Data (Sunbiz)
 */
export async function getCorporateData(entityName: string): Promise<any> {
  try {
    const url = `${SupabaseEndpoints.SUNBIZ_CORPORATE}?entity_name=ilike.%${encodeURIComponent(entityName)}%`;
    const response = await fetchWithRetry(
      url,
      { headers: getHeaders({ includeAuth: true }) }
    );
    return await response.json();
  } catch (error) {
    // Fallback to florida_entities
    const url = `${SupabaseEndpoints.FLORIDA_ENTITIES}?entity_name=ilike.%${encodeURIComponent(entityName)}%`;
    const response = await fetchWithRetry(
      url,
      { headers: getHeaders({ includeAuth: true }) }
    );
    return await response.json();
  }
}

/**
 * Get Tax Certificates
 */
export async function getTaxCertificates(parcelId: string): Promise<any> {
  const url = `${SupabaseEndpoints.TAX_CERTIFICATES}?parcel_id=eq.${parcelId}`;
  const response = await fetchWithRetry(
    url,
    { headers: getHeaders({ includeAuth: true }) }
  );
  return await response.json();
}

/**
 * Get Property Comparables
 */
export async function getComparables(parcelId: string): Promise<any> {
  const response = await fetchWithRetry(PropertyEndpoints.GET_COMPARABLES(parcelId));
  return await response.json();
}

/**
 * Get Owner Properties
 */
export async function getOwnerProperties(ownerName: string): Promise<any> {
  const response = await fetchWithRetry(PropertyEndpoints.GET_OWNER_PROPERTIES(ownerName));
  return await response.json();
}

/**
 * Autocomplete Search
 */
export async function autocomplete(query: string): Promise<any> {
  const response = await fetchWithRetry(
    `${PropertyEndpoints.AUTOCOMPLETE}?q=${encodeURIComponent(query)}`
  );
  return await response.json();
}

/**
 * Build Meilisearch filter string from filter object
 */
function buildMeilisearchFilter(filters: Record<string, any>): string {
  const conditions: string[] = [];

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null) return;

    if (typeof value === 'object' && 'min' in value && 'max' in value) {
      // Range filter
      conditions.push(`${key} >= ${value.min} AND ${key} <= ${value.max}`);
    } else if (Array.isArray(value)) {
      // Array filter (OR condition)
      const orConditions = value.map(v => `${key} = "${v}"`).join(' OR ');
      conditions.push(`(${orConditions})`);
    } else {
      // Exact match
      conditions.push(`${key} = "${value}"`);
    }
  });

  return conditions.join(' AND ');
}

/**
 * Check service health
 */
export async function checkServiceHealth(): Promise<Record<string, boolean>> {
  const services = {
    Meilisearch: MeilisearchEndpoints.HEALTH,
    PropertyAPI: PropertyEndpoints.HEALTH,
    Supabase: `${SupabaseEndpoints.BASE_URL}/rest/v1/`,
  };

  const results: Record<string, boolean> = {};

  await Promise.all(
    Object.entries(services).map(async ([name, url]) => {
      try {
        const response = await fetch(url, {
          method: 'GET',
          signal: AbortSignal.timeout(5000),
        });
        results[name] = response.ok;
      } catch {
        results[name] = false;
      }
    })
  );

  return results;
}

export default {
  searchProperties,
  getProperty,
  getSalesHistory,
  getCorporateData,
  getTaxCertificates,
  getComparables,
  getOwnerProperties,
  autocomplete,
  checkServiceHealth,
};
