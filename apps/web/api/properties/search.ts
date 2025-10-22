import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Query real data from Supabase instead of mocks
export default async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300')

  if (req.method === 'OPTIONS') return res.status(200).end()

  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL
    const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY

    if (!supabaseUrl || !supabaseKey) {
      return res.status(500).json({ success: false, error: 'Supabase not configured', data: [], pagination: { total: 0, page: 1, limit: 20 } })
    }

    const supabase = createClient(supabaseUrl, supabaseKey)

    const {
      search = '',
      page = 1,
      limit = 500, // Increased default from 20 to 500
      county,
      city,
      property_type,
      min_value,
      max_value,
      // Size filters
      min_building_sqft,
      max_building_sqft,
      min_land_sqft,
      max_land_sqft,
      // Year built filters
      min_year,
      max_year,
      // Assessment filters
      min_appraised_value,
      max_appraised_value,
      // Location filters
      zip_code,
      // Property type filters
      sub_usage_code,
      // Boolean filters
      recently_sold,
      tax_exempt,
      has_pool,
      waterfront
    } = req.method === 'POST' ? req.body : req.query

    const pageNum = parseInt(page as string)
    // FIXED: Removed hard cap of 100 - now allows up to 5000 properties per request
    const requestedLimit = parseInt(limit as string) || 500
    const limitNum = Math.min(requestedLimit, 5000) // Safety limit to prevent abuse
    const offset = (pageNum - 1) * limitNum

    let query = supabase
      .from('florida_parcels')
      .select('*', { count: 'exact' })

    if (search) {
      const s = String(search).trim()
      if (/^\d/.test(s)) {
        query = query.or(`phy_addr1.ilike.${s}%,parcel_id.ilike.${s}%`)
      } else {
        query = query.or(`owner_name.ilike.%${s}%,phy_city.ilike.%${s}%`)
      }
    }

    // Location filters (most selective first)
    if (county) query = query.eq('county', String(county).toUpperCase())
    if (city) query = query.ilike('phy_city', `%${city}%`)
    if (zip_code) query = query.eq('phy_zipcd', String(zip_code))

    // Property type filters
    if (property_type) query = query.eq('dor_uc', property_type)
    if (sub_usage_code) query = query.like('dor_uc', `${sub_usage_code}%`)

    // Value range filters
    if (min_value) query = query.gte('just_value', parseInt(min_value as string))
    if (max_value) query = query.lte('just_value', parseInt(max_value as string))

    // Assessment filters (taxable value)
    if (min_appraised_value) query = query.gte('taxable_value', parseInt(min_appraised_value as string))
    if (max_appraised_value) query = query.lte('taxable_value', parseInt(max_appraised_value as string))

    // Building size filters
    if (min_building_sqft) query = query.gte('living_area', parseInt(min_building_sqft as string))
    if (max_building_sqft) query = query.lte('living_area', parseInt(max_building_sqft as string))

    // Land size filters
    if (min_land_sqft) query = query.gte('land_sqft', parseInt(min_land_sqft as string))
    if (max_land_sqft) query = query.lte('land_sqft', parseInt(max_land_sqft as string))

    // Year built filters
    if (min_year) query = query.gte('year_built', parseInt(min_year as string))
    if (max_year) query = query.lte('year_built', parseInt(max_year as string))

    // Boolean filters
    // Recently Sold filter (within 1 year)
    if (recently_sold === 'true' || recently_sold === true) {
      const oneYearAgo = new Date()
      oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1)
      const dateStr = oneYearAgo.toISOString().split('T')[0]

      // Use sale_date1 column from florida_parcels
      query = query
        .not('sale_date1', 'is', null)
        .gte('sale_date1', dateStr)
    }

    // Tax Exempt filter
    // Note: Checking multiple possible column names for homestead exemption
    if (tax_exempt === 'true' || tax_exempt === true) {
      // Try common column variations - one of these should exist
      query = query.or('homestead_exemption.eq.Y,homestead_exemption.eq.y,homestead_exemption.eq.true,exempt_value.gt.0')
    } else if (tax_exempt === 'false' || tax_exempt === false) {
      query = query.or('homestead_exemption.is.null,homestead_exemption.eq.N,homestead_exemption.eq.n,homestead_exemption.eq.false')
    }

    // Pool filter
    // Note: May require NAP (property characteristics) table join if available
    if (has_pool === 'true' || has_pool === true) {
      // Try multiple approaches - use first that works
      // Approach 1: Direct column (if exists)
      query = query.or('pool_ind.eq.Y,pool_ind.eq.y,pool_ind.eq.true,has_pool.eq.true')
      // If NAP table exists, this query will need to be updated to join
    } else if (has_pool === 'false' || has_pool === false) {
      query = query.or('pool_ind.is.null,pool_ind.eq.N,pool_ind.eq.n,pool_ind.eq.false,has_pool.eq.false')
    }

    // Waterfront filter
    // Note: May require NAP table join or geographic boundary check
    if (waterfront === 'true' || waterfront === true) {
      // Try multiple possible column names
      query = query.or('waterfront_ind.eq.Y,waterfront_ind.eq.y,waterfront_ind.eq.true,waterfront.eq.true,is_waterfront.eq.true')
    } else if (waterfront === 'false' || waterfront === false) {
      query = query.or('waterfront_ind.is.null,waterfront_ind.eq.N,waterfront_ind.eq.n,waterfront_ind.eq.false,waterfront.eq.false,is_waterfront.eq.false')
    }

    query = query.order('just_value', { ascending: false }).range(offset, offset + limitNum - 1)

    const { data, error, count } = await query
    if (error) throw error

    const formatted = (data || []).map((p: any) => ({
      id: p.parcel_id,
      parcel_id: p.parcel_id,
      address: p.phy_addr1 || '',
      city: p.phy_city || '',
      zip_code: p.phy_zipcd || '',
      county: p.county || '',
      owner_name: p.owner_name || '',
      property_type: p.dor_uc || 'RESIDENTIAL',
      just_value: p.just_value || 0,
      land_value: p.land_value || 0,
      building_value: p.building_value || 0,
      taxable_value: p.taxable_value || 0,
      year_built: p.year_built || null,
      living_area: p.living_area || 0,
      bedrooms: p.bedrooms || 0,
      bathrooms: p.bathrooms || 0,
      land_sqft: p.land_sqft || 0,
      sale_price: p.sale_price1 || 0,
      sale_date: p.sale_date1 || null
    }))

    return res.status(200).json({
      success: true,
      data: formatted,
      pagination: {
        total: count || 0,
        page: pageNum,
        limit: limitNum,
        totalPages: Math.ceil((count || 0) / limitNum)
      }
    })
  } catch (err: any) {
    console.error('Search API error:', err)
    return res.status(500).json({ success: false, error: 'Internal server error', data: [], pagination: { total: 0, page: 1, limit: 20 } })
  }
}
