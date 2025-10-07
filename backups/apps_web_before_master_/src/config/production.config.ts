/**
 * Production Configuration for ConcordBroker
 * This file manages API endpoints for both localhost and production environments
 */

export const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost'
export const isProduction = typeof window !== 'undefined' && (
  window.location.hostname.includes('concordbroker.com') ||
  window.location.hostname.includes('vercel.app')
)

// API Endpoint Configuration
export const API_CONFIG = {
  // Base URLs
  BASE_URL: isLocalhost ? 'http://localhost:8000' : '',

  // Autocomplete endpoints
  AUTOCOMPLETE: {
    ADDRESSES: isLocalhost ? 'http://localhost:8000/api/autocomplete/addresses' : '/api/autocomplete/addresses',
    OWNERS: isLocalhost ? 'http://localhost:8000/api/autocomplete/owners' : '/api/autocomplete/owners',
    CITIES: isLocalhost ? 'http://localhost:8000/api/autocomplete/cities' : '/api/autocomplete/cities',
  },

  // Property endpoints
  PROPERTIES: {
    SEARCH: isLocalhost ? 'http://localhost:8000/api/properties/search' : '/api/properties/search',
    DETAIL: (id: string) => isLocalhost ? `http://localhost:8000/api/properties/${id}` : `/api/properties/${id}`,
    STATS: isLocalhost ? 'http://localhost:8000/api/fast/stats' : '/api/properties/stats',
    CITIES: isLocalhost ? 'http://localhost:8000/api/fast/cities' : '/api/properties/cities',
    BY_TYPE: isLocalhost ? 'http://localhost:8000/api/properties/stats/by-type' : '/api/properties/stats/by-type',
    RECENT_SALES: isLocalhost ? 'http://localhost:8000/api/properties/recent-sales' : '/api/properties/recent-sales',
    ENHANCED: (id: string) => isLocalhost ? `http://localhost:8005/api/enhanced/property/${id}` : `/api/properties/enhanced/${id}`,
    CORE_INFO: (id: string) => isLocalhost ? `http://localhost:8000/api/properties/${id}` : `/api/properties/enhanced/${id}`,
    TAX_INFO: (id: string) => isLocalhost ? `http://localhost:8000/api/properties/tax-info/${id}` : `/api/properties/tax-info/${id}`,
  },

  // Sales history
  SALES: {
    HISTORY: (id: string) => isLocalhost ? `http://localhost:8000/api/sales-history/${id}` : `/api/properties/${id}/sales`,
  },

  // Cache status
  CACHE: {
    STATUS: isLocalhost ? 'http://localhost:8000/api/cache/status' : '/api/cache/status',
  },
}

// Performance configuration
export const PERFORMANCE_CONFIG = {
  // Cache TTL in seconds
  CACHE_TTL: {
    SEARCH: 60,
    AUTOCOMPLETE: 30,
    PROPERTY_DETAIL: 300,
    STATS: 600,
    CITIES: 600,
  },

  // Request timeouts in milliseconds
  TIMEOUTS: {
    AUTOCOMPLETE: 2000,
    SEARCH: 5000,
    DETAIL: 3000,
    STATS: 5000,
  },

  // Batch sizes
  BATCH_SIZES: {
    SEARCH: 20,
    AUTOCOMPLETE: 15,
    EXPORT: 100,
  },
}

// Database configuration
export const DATABASE_CONFIG = {
  SUPABASE_URL: 'https://pmispwtdngkcmsrsjwbp.supabase.co',
  TOTAL_PROPERTIES: 7312041,
  TOTAL_COUNTIES: 67,
  INDEXES: [
    'idx_florida_parcels_parcel_id',
    'idx_florida_parcels_county',
    'idx_florida_parcels_owner_name',
    'idx_florida_parcels_phy_addr1',
    'idx_florida_parcels_phy_city',
  ],
}

// Feature flags
export const FEATURES = {
  ENABLE_REDIS_CACHE: !isLocalhost, // Redis only in production
  ENABLE_ANALYTICS: isProduction,
  ENABLE_ERROR_REPORTING: isProduction,
  ENABLE_PERFORMANCE_MONITORING: isProduction,
  ENABLE_AI_SEARCH: true,
  ENABLE_SALES_HISTORY: true,
  ENABLE_PROPERTY_PROFILES: true,
  ENABLE_EXPORT: true,
}

// Helper function to get API endpoint
export function getApiEndpoint(endpoint: string): string {
  if (isLocalhost) {
    // In localhost, use the specific service ports
    if (endpoint.includes('stats') || endpoint.includes('cities')) {
      return endpoint.replace('http://localhost:8000', 'http://localhost:8000')
    }
    if (endpoint.includes('enhanced')) {
      return endpoint.replace('http://localhost:8000', 'http://localhost:8005')
    }
    return endpoint
  }

  // In production, all endpoints go through Vercel serverless functions
  return endpoint
}

// Helper function to add caching headers
export function getCacheHeaders(ttl: number = 60): HeadersInit {
  return {
    'Cache-Control': `public, s-maxage=${ttl}, stale-while-revalidate=${ttl * 2}`,
  }
}

// Export production-ready fetch wrapper
export async function productionFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const endpoint = getApiEndpoint(url)

  // Add default headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  // Add caching for GET requests in production
  if (isProduction && (!options.method || options.method === 'GET')) {
    Object.assign(headers, getCacheHeaders(60))
  }

  try {
    const response = await fetch(endpoint, {
      ...options,
      headers,
    })

    if (!response.ok && response.status !== 404) {
      console.error(`API Error: ${response.status} ${response.statusText} for ${endpoint}`)
    }

    return response
  } catch (error) {
    console.error(`Network Error for ${endpoint}:`, error)
    throw error
  }
}

export default API_CONFIG