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
    // Use prefix matching for city to enable index usage (idx_fp_city)
    if (city) query = query.ilike('phy_city', `${String(city).trim().toUpperCase()}%`)
    if (zip_code) query = query.eq('phy_zipcd', String(zip_code))

    // Property type filters
    if (property_type) query = query.eq('property_use', property_type)
    // Sub-usage code: Use land_use_code for detailed DOR codes, property_use for general types
    if (sub_usage_code) {
      query = query.or(`property_use.like.${sub_usage_code}%,land_use_code.like.${sub_usage_code}%`)
    }

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

      // FIXED: Use sale_date column (actual column in florida_parcels)
      query = query
        .not('sale_date', 'is', null)
        .gte('sale_date', dateStr)
    }

    // Tax Exempt filter
    // FIXED: homestead_exemption column doesn't exist - use taxable_value = 0 as proxy for tax exempt
    if (tax_exempt === 'true' || tax_exempt === true) {
      // Properties with $0 taxable value are typically fully tax-exempt (government, non-profit, etc.)
      query = query.eq('taxable_value', 0)
    } else if (tax_exempt === 'false' || tax_exempt === false) {
      // Properties with taxable value > 0
      query = query.gt('taxable_value', 0)
    }

    // Pool filter
    // ❌ DISABLED: pool_ind column does NOT exist in florida_parcels
    // TODO: Need to add pool data from NAP table or property_assessments
    // if (has_pool === 'true' || has_pool === true) {
    //   console.warn('Pool filter requested but column does not exist in database')
    // }

    // Waterfront filter
    // ❌ DISABLED: waterfront_ind column does NOT exist in florida_parcels
    // TODO: Options to implement:
    //   1. Add waterfront column from NAP data
    //   2. Use address keyword heuristic (WATERFRONT, BAY, OCEAN, etc.)
    //   3. Geographic boundary check (distance to coast)
    // if (waterfront === 'true' || waterfront === true) {
    //   console.warn('Waterfront filter requested but column does not exist in database')
    // }

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
      property_type: p.property_use || 'RESIDENTIAL',
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
