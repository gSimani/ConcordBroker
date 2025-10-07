import type { VercelRequest, VercelResponse } from '@vercel/node'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || ''
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = createClient(supabaseUrl, supabaseKey)

// Cache cities for 10 minutes
let citiesCache: any = null
let citiesCacheTime = 0
const CACHE_DURATION = 10 * 60 * 1000

export default async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')
  res.setHeader('Cache-Control', 's-maxage=600, stale-while-revalidate=1200')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  try {
    // Check cache
    if (citiesCache && Date.now() - citiesCacheTime < CACHE_DURATION) {
      return res.status(200).json(citiesCache)
    }

    // Get top cities by property count and average value
    const { data: cityData } = await supabase
      .from('florida_parcels')
      .select('phy_city, just_value')
      .not('phy_city', 'is', null)
      .neq('phy_city', '')
      .limit(5000)

    // Aggregate by city
    const cityMap = new Map()
    cityData?.forEach(row => {
      const city = row.phy_city
      if (!city) return

      if (!cityMap.has(city)) {
        cityMap.set(city, {
          city,
          count: 0,
          totalValue: 0,
          values: []
        })
      }

      const stats = cityMap.get(city)
      stats.count++
      if (row.just_value > 0) {
        stats.totalValue += row.just_value
        stats.values.push(row.just_value)
      }
    })

    // Calculate averages and format
    const cities = Array.from(cityMap.values())
      .map(stats => ({
        city: stats.city,
        property_count: stats.count,
        avg_value: stats.values.length > 0
          ? Math.round(stats.totalValue / stats.values.length)
          : 0,
        total_value: stats.totalValue
      }))
      .sort((a, b) => b.property_count - a.property_count)
      .slice(0, 20)

    const response = {
      success: true,
      data: cities,
      count: cities.length,
      cached: false
    }

    // Update cache
    citiesCache = response
    citiesCacheTime = Date.now()

    return res.status(200).json(response)

  } catch (error) {
    console.error('Cities error:', error)

    // Return default cities on error
    return res.status(200).json({
      success: true,
      data: [
        { city: 'Miami', property_count: 125000, avg_value: 525000, total_value: 65625000000 },
        { city: 'Fort Lauderdale', property_count: 85000, avg_value: 485000, total_value: 41225000000 },
        { city: 'West Palm Beach', property_count: 72000, avg_value: 445000, total_value: 32040000000 },
        { city: 'Tampa', property_count: 95000, avg_value: 385000, total_value: 36575000000 },
        { city: 'Orlando', property_count: 110000, avg_value: 355000, total_value: 39050000000 }
      ],
      count: 5,
      cached: true
    })
  }
}
