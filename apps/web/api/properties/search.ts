import type { VercelRequest, VercelResponse } from '@vercel/node'

// Simple proxy to our AI-enhanced API for production
export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  try {
    // Return mock data for now to show properties
    const mockProperties = [
      {
        id: "123456789",
        parcel_id: "123456789",
        address: "123 MAIN ST",
        city: "MIAMI",
        zip_code: "33101",
        owner_name: "FLORIDA HOLDINGS LLC",
        county: "DADE",
        property_type: "RESIDENTIAL",
        just_value: 750000,
        land_value: 250000,
        building_value: 500000
      },
      {
        id: "987654321",
        parcel_id: "987654321",
        address: "456 OCEAN BLVD",
        city: "MIAMI BEACH",
        zip_code: "33139",
        owner_name: "BEACHFRONT PROPERTIES LLC",
        county: "DADE",
        property_type: "COMMERCIAL",
        just_value: 2500000,
        land_value: 1500000,
        building_value: 1000000
      },
      {
        id: "555777999",
        parcel_id: "555777999",
        address: "789 BISCAYNE BLVD",
        city: "MIAMI",
        zip_code: "33132",
        owner_name: "MIAMI TOWER LLC",
        county: "DADE",
        property_type: "COMMERCIAL",
        just_value: 5000000,
        land_value: 2000000,
        building_value: 3000000
      },
      {
        id: "111222333",
        parcel_id: "111222333",
        address: "3930 SW 53RD AVE",
        city: "DAVIE",
        zip_code: "33314",
        owner_name: "RESIDENTIAL TRUST LLC",
        county: "BROWARD",
        property_type: "RESIDENTIAL",
        just_value: 450000,
        land_value: 180000,
        building_value: 270000
      },
      {
        id: "444555666",
        parcel_id: "444555666",
        address: "1000 CORPORATE BLVD",
        city: "FORT LAUDERDALE",
        zip_code: "33334",
        owner_name: "CORPORATE CENTER LLC",
        county: "BROWARD",
        property_type: "COMMERCIAL",
        just_value: 8500000,
        land_value: 3500000,
        building_value: 5000000
      }
    ]

    return res.status(200).json({
      success: true,
      data: mockProperties,
      pagination: {
        total: mockProperties.length,
        page: 1,
        limit: 20
      }
    })

  } catch (error) {
    console.error('API Error:', error)
    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      data: [],
      pagination: { total: 0, page: 1, limit: 20 }
    })
  }
}