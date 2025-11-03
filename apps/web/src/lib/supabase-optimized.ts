import { createClient, SupabaseClient } from '@supabase/supabase-js'
import { QueryClient } from '@tanstack/react-query'

// Performance optimized Supabase configuration
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://your-project.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'your-anon-key'

// Create singleton Supabase client with optimized settings
export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  },
  db: {
    schema: 'public'
  }
})

// React Query client for caching
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (renamed from cacheTime in React Query v5)
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
})

// Cache manager for local storage
class CacheManager {
  private cache: Map<string, { data: any; timestamp: number }> = new Map()
  private readonly TTL = 5 * 60 * 1000 // 5 minutes

  set(key: string, data: any) {
    this.cache.set(key, { data, timestamp: Date.now() })
  }

  get(key: string) {
    const cached = this.cache.get(key)
    if (!cached) return null

    const isExpired = Date.now() - cached.timestamp > this.TTL
    if (isExpired) {
      this.cache.delete(key)
      return null
    }

    return cached.data
  }

  clear() {
    this.cache.clear()
  }
}

export const cacheManager = new CacheManager()

// Optimized property service with caching and batching
export const propertyService = {
  // Batch multiple property requests
  batchPropertyRequests: (() => {
    let batch: string[] = []
    let batchTimeout: NodeJS.Timeout | null = null
    let batchResolvers: Map<string, { resolve: Function; reject: Function }[]> = new Map()

    return (parcelId: string): Promise<any> => {
      return new Promise((resolve, reject) => {
        // Add to batch
        batch.push(parcelId)

        // Store resolvers
        if (!batchResolvers.has(parcelId)) {
          batchResolvers.set(parcelId, [])
        }
        batchResolvers.get(parcelId)!.push({ resolve, reject })

        // Clear existing timeout
        if (batchTimeout) {
          clearTimeout(batchTimeout)
        }

        // Set new timeout to execute batch
        batchTimeout = setTimeout(async () => {
          const currentBatch = [...batch]
          const currentResolvers = new Map(batchResolvers)

          // Reset batch
          batch = []
          batchResolvers.clear()
          batchTimeout = null

          try {
            // Execute batch query
            const { data, error } = await supabase
              .from('florida_parcels')
              .select('*')
              .in('parcel_id', currentBatch)

            if (error) throw error

            // Resolve each promise
            for (const property of data || []) {
              const resolvers = currentResolvers.get(property.parcel_id)
              if (resolvers) {
                resolvers.forEach(({ resolve }) => resolve(property))
              }
            }

            // Reject for missing properties
            for (const [parcelId, resolvers] of currentResolvers) {
              if (!data?.find(p => p.parcel_id === parcelId)) {
                resolvers.forEach(({ reject }) =>
                  reject(new Error(`Property ${parcelId} not found`))
                )
              }
            }
          } catch (error) {
            // Reject all promises on error
            for (const resolvers of currentResolvers.values()) {
              resolvers.forEach(({ reject }) => reject(error))
            }
          }
        }, 50) // Wait 50ms to batch requests
      })
    }
  })(),

  // Optimized search with pagination and filtering
  async searchProperties(filters: {
    county?: string
    city?: string
    minPrice?: number
    maxPrice?: number
    propertyType?: string
    hasForeclosure?: boolean
    hasTaxDeed?: boolean
    hasTaxLien?: boolean
    limit?: number
    offset?: number
  }) {
    // Create cache key from filters
    const cacheKey = `search:${JSON.stringify(filters)}`

    // Check cache first
    const cached = cacheManager.get(cacheKey)
    if (cached) return cached

    // Build optimized query
    let query = supabase
      .from('florida_parcels')
      .select('*', { count: 'exact' })
      .eq('is_redacted', false)

    // Apply filters efficiently
    if (filters.county) {
      query = query.eq('county', filters.county.toUpperCase())
    }

    if (filters.city) {
      query = query.ilike('phy_city', `%${filters.city}%`)
    }

    if (filters.minPrice !== undefined) {
      query = query.gte('just_value', filters.minPrice)
    }

    if (filters.maxPrice !== undefined) {
      query = query.lte('just_value', filters.maxPrice)
    }

    // Property type filtering with optimized ranges
    if (filters.propertyType) {
      const typeRanges: Record<string, string[]> = {
        'Residential': ['001', '002', '003', '004', '005', '006', '007', '008', '009'],
        'Commercial': ['010', '011', '012', '013', '014', '015', '016', '017', '018', '019', '020', '021', '022', '023', '024', '025', '026', '027', '028', '029', '030', '031', '032', '033', '034', '035', '036', '037', '038', '039'],
        'Industrial': ['040', '041', '042', '043', '044', '045', '046', '047', '048', '049'],
        'Agricultural': ['050', '051', '052', '053', '054', '055', '056', '057', '058', '059', '060', '061', '062', '063', '064', '065', '066', '067', '068', '069'],
        'Vacant': ['000', '090', '091', '092', '093', '094', '095'],
        'Institutional': ['070', '071', '072', '073', '074', '075', '076', '077', '078', '079', '080', '081', '082', '083', '084', '085', '086', '087', '088', '089']
      }

      if (typeRanges[filters.propertyType]) {
        query = query.in('dor_cd', typeRanges[filters.propertyType])
      }
    }

    // Apply pagination with optimized range
    const limit = Math.min(filters.limit || 20, 100) // Cap at 100
    const offset = filters.offset || 0
    query = query.range(offset, offset + limit - 1)

    // Sort by value for consistent results
    query = query.order('just_value', { ascending: false, nullsFirst: false })

    const { data, error, count } = await query

    if (error) throw error

    const result = { data, total: count, limit, offset }

    // Cache the result
    cacheManager.set(cacheKey, result)

    return result
  },

  // Get single property with related data
  async getPropertyDetails(parcelId: string) {
    const cacheKey = `property:${parcelId}`

    // Check cache
    const cached = cacheManager.get(cacheKey)
    if (cached) return cached

    // Parallel queries for better performance
    const [propertyResult, salesResult, taxDeedResult] = await Promise.all([
      // Main property data
      supabase
        .from('florida_parcels')
        .select('*')
        .eq('parcel_id', parcelId)
        .single(),

      // Sales history
      supabase
        .from('sales_history')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('sale_date', { ascending: false })
        .limit(10),

      // Tax deed info
      supabase
        .from('tax_deed_bidding_items')
        .select('*')
        .eq('parcel_id', parcelId)
        .order('auction_date', { ascending: false })
        .limit(5)
    ])

    if (propertyResult.error) throw propertyResult.error

    const result = {
      ...propertyResult.data,
      sales_history: salesResult.data || [],
      tax_deed_info: taxDeedResult.data || []
    }

    // Cache the result
    cacheManager.set(cacheKey, result)

    return result
  },

  // Get properties by owner with optimization
  async getPropertiesByOwner(ownerName: string, county?: string) {
    const cacheKey = `owner:${ownerName}:${county}`

    // Check cache
    const cached = cacheManager.get(cacheKey)
    if (cached) return cached

    let query = supabase
      .from('florida_parcels')
      .select('parcel_id, county, phy_addr1, phy_city, just_value, land_value, year_built')
      .ilike('owner_name', `%${ownerName}%`)
      .limit(50) // Limit for performance

    if (county) {
      query = query.eq('county', county.toUpperCase())
    }

    const { data, error } = await query

    if (error) throw error

    // Cache the result
    cacheManager.set(cacheKey, data)

    return data
  },

  // Optimized bulk operations
  async getMultipleProperties(parcelIds: string[]) {
    // Use batching for large requests
    if (parcelIds.length > 100) {
      const chunks = []
      for (let i = 0; i < parcelIds.length; i += 100) {
        chunks.push(parcelIds.slice(i, i + 100))
      }

      const results = await Promise.all(
        chunks.map(chunk =>
          supabase
            .from('florida_parcels')
            .select('*')
            .in('parcel_id', chunk)
        )
      )

      return results.flatMap(r => r.data || [])
    }

    const { data, error } = await supabase
      .from('florida_parcels')
      .select('*')
      .in('parcel_id', parcelIds)

    if (error) throw error
    return data
  },

  // Real-time subscriptions with optimization
  subscribeToPropertyUpdates(parcelId: string, callback: (payload: any) => void) {
    return supabase
      .channel(`property:${parcelId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'florida_parcels',
          filter: `parcel_id=eq.${parcelId}`,
        },
        (payload) => {
          // Update cache
          cacheManager.set(`property:${parcelId}`, payload.new)
          callback(payload)
        }
      )
      .subscribe()
  },

  // Analytics queries with caching
  async getMarketAnalytics(county: string, timeRange: 'month' | 'quarter' | 'year' = 'quarter') {
    const cacheKey = `analytics:${county}:${timeRange}`

    // Check cache
    const cached = cacheManager.get(cacheKey)
    if (cached) return cached

    // Use RPC for complex analytics query
    const { data, error } = await supabase
      .rpc('get_market_analytics', {
        p_county: county.toUpperCase(),
        p_time_range: timeRange
      })

    if (error) throw error

    // Cache the result
    cacheManager.set(cacheKey, data)

    return data
  }
}

// Export types
export interface FloridaParcel {
  id: number
  parcel_id: string
  county: string
  year: number
  geometry?: any
  centroid?: any
  area_sqft?: number

  // Owner information
  owner_name?: string
  owner_addr1?: string
  owner_addr2?: string
  owner_city?: string
  owner_state?: string
  owner_zip?: string

  // Physical address
  phy_addr1?: string
  phy_addr2?: string
  phy_city?: string
  phy_state?: string
  phy_zipcd?: string

  // Property characteristics
  dor_cd?: string
  property_use_desc?: string
  just_value?: number
  assessed_value?: number
  taxable_value?: number
  land_value?: number
  building_value?: number

  // Property details
  year_built?: number
  total_living_area?: number
  bedrooms?: number
  bathrooms?: number
  stories?: number
  units?: number
  land_sqft?: number

  // Sales information
  sale_date?: string
  sale_price?: number
  sale_qualification?: string
}

export default supabase