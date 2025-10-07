import { createClient } from '@supabase/supabase-js'

// Supabase configuration - Production Database with 7.31M Florida Properties
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

console.log('🚀 Connecting to Supabase Production Database:', supabaseUrl)

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// MCP Server API for fallback and enhanced functionality
const MCP_BASE_URL = import.meta.env.VITE_MCP_SERVER_URL || 'http://localhost:3005'
const MCP_API_KEY = import.meta.env.VITE_MCP_API_KEY || 'concordbroker-mcp-key-claude'

export const mcpApi = {
  async get(endpoint: string) {
    try {
      const response = await fetch(`${MCP_BASE_URL}${endpoint}`, {
        headers: {
          'x-api-key': MCP_API_KEY,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`MCP API error: ${response.status}`)
      }

      const result = await response.json()
      return result.success ? result.data : result
    } catch (error) {
      console.error('MCP API error:', error)
      throw error
    }
  },

  async post(endpoint: string, data: any) {
    try {
      const response = await fetch(`${MCP_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'x-api-key': MCP_API_KEY,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        throw new Error(`MCP API error: ${response.status}`)
      }

      const result = await response.json()
      return result.success ? result.data : result
    } catch (error) {
      console.error('MCP API error:', error)
      throw error
    }
  }
}

// Types for Florida Parcel Data
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
  
  // Legal description
  legal_desc?: string
  subdivision?: string
  lot?: string
  block?: string
  
  // Property characteristics
  property_use?: string
  property_use_desc?: string
  land_use_code?: string
  zoning?: string
  
  // Valuations
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
  
  // Land measurements
  land_sqft?: number
  land_acres?: number
  
  // Sales information
  sale_date?: string
  sale_price?: number
  sale_qualification?: string
  
  // Data quality
  match_status?: string
  is_redacted?: boolean
  data_source?: string
  import_date?: string
}

// Helper functions for parcel data
export const parcelService = {
  // Get parcels with filters
  async getParcels(filters: {
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
    let query = supabase
      .from('florida_parcels')
      .select('*', { count: 'exact' })
      .eq('is_redacted', false)
    
    if (filters.county) {
      query = query.eq('county', filters.county.toUpperCase())
    }
    
    if (filters.city) {
      query = query.ilike('phy_city', `%${filters.city}%`)
    }
    
    if (filters.minPrice) {
      query = query.gte('taxable_value', filters.minPrice)
    }
    
    if (filters.maxPrice) {
      query = query.lte('taxable_value', filters.maxPrice)
    }
    
    if (filters.propertyType) {
      // Handle property type ranges based on Florida DOR codes
      // Using dor_cd field which contains the actual property use codes
      if (filters.propertyType === 'Residential') {
        // Residential: DOR codes 001-009
        query = query.gte('dor_cd', '001').lte('dor_cd', '009')
      } else if (filters.propertyType === 'Commercial') {
        // Commercial: DOR codes 010-039
        query = query.gte('dor_cd', '010').lte('dor_cd', '039')
      } else if (filters.propertyType === 'Industrial') {
        // Industrial: DOR codes 040-049
        query = query.gte('dor_cd', '040').lte('dor_cd', '049')
      } else if (filters.propertyType === 'Agricultural') {
        // Agricultural: DOR codes 050-069
        query = query.gte('dor_cd', '050').lte('dor_cd', '069')
      } else if (filters.propertyType === 'Vacant') {
        // Vacant: DOR codes 000 and 090-095
        query = query.or('dor_cd.eq.000,dor_cd.gte.090.lte.095')
      } else if (filters.propertyType === 'Institutional') {
        // Institutional: DOR codes 070-089
        query = query.gte('dor_cd', '070').lte('dor_cd', '089')
      } else if (filters.propertyType !== 'All Properties') {
        // Exact match for specific codes
        query = query.eq('dor_cd', filters.propertyType)
      }
      // Note: 'All Properties' doesn't add any filter
    }
    
    // Filter for properties with foreclosure data
    if (filters.hasForeclosure) {
      // Join with foreclosure_cases table to find properties with foreclosure records
      query = query.or(
        'parcel_id.in.(select distinct parcel_id from foreclosure_cases)',
        'parcel_id.in.(select distinct parcel_id from tax_deed_bidding_items where item_status=\'Sold\')'
      )
    }
    
    // Filter for properties with tax deed auction data
    if (filters.hasTaxDeed) {
      // Join with tax_deed_bidding_items table to find properties in auctions
      query = query.in('parcel_id', 
        // This will be a subquery to find parcel_ids in tax deed auctions
        'select distinct parcel_id from tax_deed_bidding_items'
      )
    }
    
    // Filter for properties with tax lien data
    if (filters.hasTaxLien) {
      // Join with tax_certificates table to find properties with tax liens
      query = query.or(
        'parcel_id.in.(select distinct parcel_id from tax_certificates where status!=\'Redeemed\')',
        'parcel_id.in.(select distinct parcel_id from tax_lien_certificates)'
      )
    }
    
    // Apply pagination
    query = query.range(
      filters.offset || 0, 
      (filters.offset || 0) + (filters.limit || 20) - 1
    )
    
    // Order by taxable value descending
    query = query.order('taxable_value', { ascending: false })
    
    return await query
  },
  
  // Get single parcel by ID
  async getParcel(parcelId: string) {
    const { data, error } = await supabase
      .from('florida_parcels')
      .select('*')
      .eq('parcel_id', parcelId)
      .single()
    
    if (error) throw error
    return data
  },
  
  // Get recent sales
  async getRecentSales(county?: string, limit: number = 10) {
    let query = supabase
      .from('florida_parcels')
      .select('*')
      .eq('is_redacted', false)
      .not('sale_date', 'is', null)
      .gt('sale_price', 0)
    
    if (county) {
      query = query.eq('county', county.toUpperCase())
    }
    
    query = query
      .order('sale_date', { ascending: false })
      .limit(limit)
    
    const { data, error } = await query
    
    if (error) throw error
    return data
  },
  
  // Get high value properties
  async getHighValueProperties(county?: string, minValue: number = 1000000) {
    let query = supabase
      .from('florida_parcels')
      .select('*')
      .eq('is_redacted', false)
      .gte('taxable_value', minValue)
    
    if (county) {
      query = query.eq('county', county.toUpperCase())
    }
    
    query = query
      .order('taxable_value', { ascending: false })
      .limit(20)
    
    const { data, error } = await query
    
    if (error) throw error
    return data
  },
  
  // Search by address
  async searchByAddress(address: string, county?: string) {
    let query = supabase
      .from('florida_parcels')
      .select('*')
      .eq('is_redacted', false)
      .ilike('phy_addr1', `%${address}%`)
    
    if (county) {
      query = query.eq('county', county.toUpperCase())
    }
    
    query = query.limit(20)
    
    const { data, error } = await query
    
    if (error) throw error
    return data
  },
  
  // Get property statistics for a county
  async getCountyStats(county: string) {
    const { data, error } = await supabase
      .rpc('get_county_stats', { p_county: county.toUpperCase() })
    
    if (error) throw error
    return data
  }
}

// Export default client
export default supabase