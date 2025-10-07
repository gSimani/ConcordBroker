// Vercel Serverless Function for Autocomplete
// This runs directly on Vercel without needing Railway

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { q, limit = 20 } = req.query;

  if (!q || q.length < 2) {
    return res.status(200).json({
      success: true,
      data: [],
      count: 0,
      query: q || '',
    });
  }

  try {
    // Direct Supabase connection with proper keys
    const SUPABASE_URL = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://pmispwtdngkcmsrsjwbp.supabase.co';
    const SUPABASE_ANON_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0';

    if (!SUPABASE_ANON_KEY) {
      console.error('Supabase key not configured');
      return res.status(500).json({ error: 'Database configuration error' });
    }

    // Query Supabase directly
    const response = await fetch(
      `${SUPABASE_URL}/rest/v1/florida_parcels?` +
      `or=(phy_addr1.ilike.%25${encodeURIComponent(q)}%25,owner_name.ilike.%25${encodeURIComponent(q)}%25,phy_city.ilike.%25${encodeURIComponent(q)}%25)` +
      `&limit=${limit}` +
      `&select=phy_addr1,phy_city,phy_zipcd,owner_name,property_use,county`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      console.error('Supabase error:', response.status, await response.text());
      return res.status(500).json({ error: 'Database query failed' });
    }

    const data = await response.json();

    // Transform data to match frontend expectations
    const transformed = data.map(item => ({
      address: item.phy_addr1,
      city: item.phy_city,
      zip_code: item.phy_zipcd,
      owner_name: item.owner_name,
      property_type: item.property_use || 'Residential',
      county: item.county,
      type: 'property',
    }));

    return res.status(200).json({
      success: true,
      data: transformed,
      count: transformed.length,
      query: q,
    });

  } catch (error) {
    console.error('Autocomplete error:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
}