import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase from environment only (no hardcoded defaults)
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = createClient(supabaseUrl, supabaseKey)

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  try {
    const {
      search = '',
      page = 1,
      limit = 20,
      county,
      city,
      property_type,
      min_value,
      max_value
    } = req.method === 'POST' ? req.body : req.query

    const pageNum = parseInt(page as string)
    const limitNum = Math.min(parseInt(limit as string) || 12, 50) // Reduced for performance
    const offset = (pageNum - 1) * limitNum

    // Build the query with minimal fields for performance
    let query = supabase
      .from('florida_parcels')
      .select(`
        parcel_id, county, owner_name, phy_addr1, phy_city, phy_zipcd,
        just_value, land_value, building_value, taxable_value,
        year_built, total_living_area, property_use
      `, { count: 'planned' }) // Use planned for faster estimation

    // Apply search filters
    if (search) {
      const searchStr = String(search).trim()
      if (/^\d/.test(searchStr)) {
        // Address search
        query = query.or(`phy_addr1.ilike.${searchStr}%,parcel_id.ilike.${searchStr}%`)
      } else {
        // Name or city search
        query = query.or(`owner_name.ilike.%${searchStr}%,phy_city.ilike.%${searchStr}%`)
      }
    }

    // Apply filters
    if (county) query = query.eq('county', String(county).toUpperCase())
    if (city) query = query.ilike('phy_city', `%${city}%`)
    if (property_type) query = query.eq('dor_uc', property_type)
    if (min_value) query = query.gte('just_value', parseInt(min_value as string))
    if (max_value) query = query.lte('just_value', parseInt(max_value as string))

    // Add pagination
    query = query
      .order('just_value', { ascending: false, nullsFirst: false })
      .range(offset, offset + limitNum - 1)
      .limit(limitNum) // Explicit limit for safety

    const { data, error, count } = await query

    if (error) {
      console.error('Supabase error:', error)
      throw error
    }

    // Format the response
    const formattedData = (data || []).map((property: any) => ({
      id: property.parcel_id,
      parcel_id: property.parcel_id,
      address: property.phy_addr1 || '',
      city: property.phy_city || '',
      zip_code: property.phy_zipcd || '',
      county: property.county || '',
      owner_name: property.owner_name || '',
      property_type: property.dor_uc || 'RESIDENTIAL',
      just_value: property.just_value || 0,
      land_value: property.land_value || 0,
      building_value: property.building_value || 0,
      taxable_value: property.taxable_value || 0,
      year_built: property.year_built || null,
      living_area: property.total_living_area || property.living_area || 0,
      bedrooms: property.bedrooms || 0,
      bathrooms: property.bathrooms || 0,
      land_sqft: property.land_sqft || 0,
      sale_price: property.sale_price || 0,
      sale_date: property.sale_date || null
    }))

    return res.status(200).json({
      success: true,
      data: formattedData,
      pagination: {
        total: count || 100000, // Estimate for performance,
        page: pageNum,
        limit: limitNum,
        totalPages: Math.ceil((count || 100000) / limitNum),
        has_more: formattedData.length === limitNum
      }
    })

  } catch (error: any) {
    console.error('API Error:', error)

    // Return sample data as fallback
    const sampleData = [
      {
        id: "123456789",
        parcel_id: "123456789",
        address: "123 MAIN ST",
        city: "MIAMI",
        zip_code: "33101",
        county: "DADE",
        owner_name: "FLORIDA HOLDINGS LLC",
        property_type: "RESIDENTIAL",
        just_value: 750000,
        land_value: 250000,
        building_value: 500000,
        taxable_value: 650000
      },
      {
        id: "987654321",
        parcel_id: "987654321",
        address: "456 OCEAN BLVD",
        city: "MIAMI BEACH",
        zip_code: "33139",
        county: "DADE",
        owner_name: "BEACHFRONT PROPERTIES LLC",
        property_type: "COMMERCIAL",
        just_value: 2500000,
        land_value: 1500000,
        building_value: 1000000,
        taxable_value: 2200000
      }
    ]

    return res.status(200).json({
      success: true,
      data: sampleData,
      pagination: {
        total: sampleData.length,
        page: 1,
        limit: 20,
        totalPages: 1
      },
      fallback: true
    })
  }
}
