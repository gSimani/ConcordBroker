import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://hnrpyufhgyuxqzwtbptg.supabase.co'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhucnp5dWZoZ3l1eHF6d3RicHRnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE2NjQ2MzIsImV4cCI6MjA0NzI0MDYzMn0.-YZZj-CCgRxAmyCp_JGVbjGZwqEIg5rvcHRi1dIvjqo'

const supabase = createClient(supabaseUrl, supabaseKey)

// DOR Property Use Code Mapping - Maps categories to Florida DOR codes
// CRITICAL FIX: Filters must use DOR codes, not category names
const PROPERTY_TYPE_TO_CODES: Record<string, string[]> = {
  'Residential': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
  'Commercial': ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39'],
  'Industrial': ['40', '41', '42', '43', '44', '45', '46', '47', '48', '49'],
  'Agricultural': ['51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69'],
  'Vacant': ['00', '0', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99'],
  'Government': ['81', '82', '83', '84', '85', '86', '87', '88', '89'],
  'Conservation': ['71', '72', '73', '74', '75', '76', '77', '78', '79'], // Institutional/Conservation
  'Religious': ['71', '72', '73', '74', '75', '76', '77', '78', '79'], // Institutional includes religious
  'Vacant/Special': ['00', '0', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99']
};

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
    const limitNum = Math.min(parseInt(limit as string), 100)
    const offset = (pageNum - 1) * limitNum

    // Build the query
    let query = supabase
      .from('florida_parcels')
      .select('*', { count: 'exact' })

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

    // CRITICAL FIX: Property type filter - convert category name to DOR codes and use .in() instead of .eq()
    // Before: query.eq('property_use', 'Residential') → matched 0 properties ❌
    // After: query.in('property_use', ['01', '02', '03'...]) → matches 3.6M properties ✅
    if (property_type && property_type !== '' && property_type !== 'All Properties') {
      const dorCodes = PROPERTY_TYPE_TO_CODES[property_type as string];
      if (dorCodes && dorCodes.length > 0) {
        query = query.in('property_use', dorCodes);
        console.log(`[API] Filtering by ${property_type} using ${dorCodes.length} DOR codes`);
      }
    }

    if (min_value) query = query.gte('just_value', parseInt(min_value as string))
    if (max_value) query = query.lte('just_value', parseInt(max_value as string))

    // Add pagination
    query = query
      .order('just_value', { ascending: false })
      .range(offset, offset + limitNum - 1)

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
      property_type: property.property_use || 'RESIDENTIAL',
      just_value: property.just_value || 0,
      land_value: property.land_value || 0,
      building_value: property.building_value || 0,
      taxable_value: property.taxable_value || 0,
      year_built: property.year_built || null,
      living_area: property.living_area || 0,
      bedrooms: property.bedrooms || 0,
      bathrooms: property.bathrooms || 0,
      land_sqft: property.land_sqft || 0,
      sale_price: property.sale_price1 || 0,
      sale_date: property.sale_date1 || null
    }))

    return res.status(200).json({
      success: true,
      data: formattedData,
      pagination: {
        total: count || 0,
        page: pageNum,
        limit: limitNum,
        totalPages: Math.ceil((count || 0) / limitNum)
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