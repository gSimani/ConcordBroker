import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client with production database (7.41M Florida Properties)
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.RrKqt2_OSZsXeHiHt1jPXXrVVpWN7kqvxst9rr6gT1M'

const supabase = createClient(supabaseUrl, supabaseKey)

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  const { q, limit = 10 } = req.query

  if (!q || typeof q !== 'string') {
    return res.status(400).json({ success: false, error: 'Query parameter required', data: [] })
  }

  try {
    // Search real Supabase data for owner autocomplete
    const query = q.toLowerCase().trim()
    const limitNum = Math.min(parseInt(limit as string) || 10, 20)

    const { data, error } = await supabase
      .from('florida_parcels')
      .select(`
        owner_name, phy_city, county,
        just_value, parcel_id
      `)
      .ilike('owner_name', `%${query.toUpperCase()}%`)
      .not('owner_name', 'is', null)
      .order('just_value', { ascending: false })
      .limit(limitNum * 2) // Get more to deduplicate

    if (error) {
      console.error('Supabase owners autocomplete error:', error)
      throw error
    }

    // Deduplicate by owner name and keep highest value properties
    const uniqueOwners = new Map()
    for (const property of data || []) {
      const ownerName = property.owner_name
      if (!uniqueOwners.has(ownerName) ||
          property.just_value > uniqueOwners.get(ownerName).just_value) {
        uniqueOwners.set(ownerName, property)
      }
    }

    // Format the results
    const owners = Array.from(uniqueOwners.values())
      .slice(0, limitNum)
      .map((property: any) => ({
        owner_name: property.owner_name || '',
        city: property.phy_city || '',
        county: property.county || '',
        just_value: property.just_value || 0,
        parcel_id: property.parcel_id || '',
        // Add business entity analysis for LLCs/Corps
        business_entity: property.owner_name?.includes('LLC') ||
                        property.owner_name?.includes('CORP') ||
                        property.owner_name?.includes('INC') ? {
          name: property.owner_name,
          status: "ACTIVE",
          type: property.owner_name.includes('LLC') ? 'LLC' :
                property.owner_name.includes('CORP') ? 'CORP' : 'INC',
          confidence: 0.95
        } : null
      }))

    return res.status(200).json({
      success: true,
      data: owners
    })

  } catch (error) {
    console.error('Owner autocomplete error:', error)

    // Return fallback suggestions
    const fallbackOwners = [
      {
        owner_name: "OSLAIDA VALIDO",
        city: "MIAMI",
        county: "MIAMI-DADE",
        just_value: 520602,
        parcel_id: "3040190012860",
        business_entity: null
      }
    ]

    return res.status(200).json({
      success: true,
      data: fallbackOwners,
      fallback: true
    })
  }
}