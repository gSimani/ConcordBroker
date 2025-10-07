/**
 * Unified API Router
 * Consolidates all API endpoints from multiple agents' work
 */

import express from 'express';
import cors from 'cors';

const router = express.Router();

// Enable CORS for all routes
router.use(cors());

// Health check endpoint
router.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {
      properties: 'active',
      sales: 'active',
      investment: 'active',
      taxCertificates: 'active',
      sunbiz: 'active'
    }
  });
});

// ============================================
// PROPERTY ENDPOINTS (Core Data)
// ============================================

router.get('/api/properties/:parcelId', async (req, res) => {
  try {
    const { parcelId } = req.params;
    // Fetch from Supabase with unified field names
    const propertyData = await fetchPropertyData(parcelId);
    res.json(normalizePropertyData(propertyData));
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch property data' });
  }
});

router.get('/api/properties', async (req, res) => {
  try {
    const { county, city, limit = 100 } = req.query;
    // Fetch properties with filters
    const properties = await fetchProperties({ county, city, limit });
    res.json(properties.map(normalizePropertyData));
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch properties' });
  }
});

// ============================================
// SALES HISTORY ENDPOINTS
// ============================================

router.get('/api/sales-history/:parcelId', async (req, res) => {
  try {
    const { parcelId } = req.params;
    const salesData = await fetchSalesHistory(parcelId);
    res.json({
      parcel_id: parcelId,
      sales: salesData,
      most_recent_sale: salesData[0] || null,
      total_sales: salesData.length
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch sales history' });
  }
});

// ============================================
// INVESTMENT ANALYSIS ENDPOINTS
// ============================================

router.get('/api/investment-analysis/:parcelId', async (req, res) => {
  try {
    const { parcelId } = req.params;
    const propertyData = await fetchPropertyData(parcelId);
    const analysis = calculateInvestmentScore(propertyData);

    res.json({
      parcel_id: parcelId,
      score: analysis.score,
      grade: analysis.grade,
      metrics: analysis.metrics,
      opportunities: analysis.opportunities,
      risks: analysis.risks
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to calculate investment analysis' });
  }
});

// ============================================
// TAX CERTIFICATE ENDPOINTS
// ============================================

router.get('/api/tax-certificates/:parcelId', async (req, res) => {
  try {
    const { parcelId } = req.params;
    const certificates = await fetchTaxCertificates(parcelId);

    res.json({
      parcel_id: parcelId,
      has_certificates: certificates.length > 0,
      certificates: certificates,
      total_amount: certificates.reduce((sum, cert) => sum + cert.amount, 0)
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch tax certificates' });
  }
});

// ============================================
// SUNBIZ MATCHING ENDPOINTS
// ============================================

router.get('/api/sunbiz/matches/:parcelId', async (req, res) => {
  try {
    const { parcelId } = req.params;
    const propertyData = await fetchPropertyData(parcelId);
    const ownerName = propertyData.own_name || propertyData.owner_name;

    if (!ownerName) {
      return res.json({ matches: [], has_matches: false });
    }

    const matches = await searchSunbizEntities(ownerName);
    res.json({
      parcel_id: parcelId,
      owner_name: ownerName,
      matches: matches,
      has_matches: matches.length > 0,
      best_match: matches[0] || null
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to search Sunbiz' });
  }
});

// ============================================
// SEARCH ENDPOINTS
// ============================================

router.post('/api/search/properties', async (req, res) => {
  try {
    const { query, filters, limit = 100, offset = 0 } = req.body;
    const results = await searchProperties(query, filters, limit, offset);

    res.json({
      results: results.map(normalizePropertyData),
      total: results.length,
      query: query,
      filters: filters
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to search properties' });
  }
});

// ============================================
// AUTOCOMPLETE ENDPOINTS
// ============================================

router.get('/api/autocomplete', async (req, res) => {
  try {
    const { q: query, limit = 20 } = req.query;

    if (!query || typeof query !== 'string' || query.length < 2) {
      return res.json({ suggestions: [] });
    }

    const suggestions = await getAutocompleteSuggestions(query, parseInt(limit as string));

    res.json({
      suggestions: suggestions,
      success: true,
      data: suggestions
    });
  } catch (error) {
    console.error('Autocomplete error:', error);
    res.status(500).json({
      error: 'Failed to fetch autocomplete suggestions',
      suggestions: []
    });
  }
});

router.get('/api/autocomplete/combined', async (req, res) => {
  try {
    const { q: query, limit = 20 } = req.query;

    if (!query || typeof query !== 'string' || query.length < 2) {
      return res.json({ suggestions: [] });
    }

    const suggestions = await getAutocompleteSuggestions(query, parseInt(limit as string));

    res.json({
      suggestions: suggestions,
      success: true,
      data: suggestions
    });
  } catch (error) {
    console.error('Autocomplete error:', error);
    res.status(500).json({
      error: 'Failed to fetch autocomplete suggestions',
      suggestions: []
    });
  }
});

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Normalize property data to unified format
 */
function normalizePropertyData(data: any) {
  return {
    // Always provide both field name formats for compatibility
    parcel_id: data.parcel_id || data.id,

    // Address fields
    phy_addr1: data.phy_addr1 || data.property_address,
    phy_city: data.phy_city || data.city,
    phy_zipcd: data.phy_zipcd || data.zip_code,

    // Owner fields (both formats)
    own_name: data.own_name || data.owner_name,
    owner_name: data.owner_name || data.own_name,

    // Value fields (all formats)
    jv: data.jv || data.just_value || data.market_value,
    just_value: data.just_value || data.jv || data.market_value,
    market_value: data.market_value || data.jv || data.just_value,

    tv_sd: data.tv_sd || data.taxable_value,
    taxable_value: data.taxable_value || data.tv_sd,

    // Building fields
    tot_lvg_area: data.tot_lvg_area || data.building_sqft,
    building_sqft: data.building_sqft || data.tot_lvg_area,

    // Land fields
    lnd_sqfoot: data.lnd_sqfoot || data.land_sqft,
    land_sqft: data.land_sqft || data.lnd_sqfoot,

    // Year built
    act_yr_blt: data.act_yr_blt || data.year_built,
    year_built: data.year_built || data.act_yr_blt,

    // Property use
    propertyUse: data.propertyUse || data.property_use,
    property_use: data.property_use || data.propertyUse,
    propertyUseDesc: data.propertyUseDesc || data.property_use_desc,
    property_use_desc: data.property_use_desc || data.propertyUseDesc,

    // Keep all other fields
    ...data
  };
}

/**
 * Calculate investment score and grade
 */
function calculateInvestmentScore(property: any) {
  let score = 50; // Base score

  const marketValue = property.jv || property.just_value || 0;
  const yearBuilt = property.act_yr_blt || property.year_built || 1950;
  const propertyAge = new Date().getFullYear() - yearBuilt;

  // Age scoring
  if (propertyAge < 20) score += 15;
  else if (propertyAge < 40) score += 5;
  else if (propertyAge > 60) score -= 10;

  // Value scoring
  if (marketValue > 0 && marketValue < 200000) score += 10;
  else if (marketValue > 500000) score -= 5;

  // Non-homestead bonus
  if (!property.homestead) score += 15;

  // Cap at 0-100
  score = Math.max(0, Math.min(100, score));

  // Calculate grade
  let grade = 'F';
  if (score >= 90) grade = 'A+';
  else if (score >= 80) grade = 'A';
  else if (score >= 70) grade = 'B';
  else if (score >= 60) grade = 'C';
  else if (score >= 50) grade = 'D';

  return {
    score,
    grade,
    metrics: {
      property_age: propertyAge,
      market_value: marketValue,
      value_per_sqft: property.tot_lvg_area ? marketValue / property.tot_lvg_area : 0
    },
    opportunities: [],
    risks: []
  };
}

// Placeholder functions - implement with your database
async function fetchPropertyData(parcelId: string) {
  // TODO: Implement Supabase query
  return {};
}

async function fetchProperties(filters: any) {
  // TODO: Implement Supabase query
  return [];
}

async function fetchSalesHistory(parcelId: string) {
  // TODO: Implement Supabase query
  return [];
}

async function fetchTaxCertificates(parcelId: string) {
  // TODO: Implement Supabase query
  return [];
}

async function searchSunbizEntities(ownerName: string) {
  // TODO: Implement Sunbiz API call
  return [];
}

async function searchProperties(query: string, filters: any, limit: number, offset: number) {
  // TODO: Implement search logic
  return [];
}

async function getAutocompleteSuggestions(query: string, limit: number = 20) {
  const suggestions: any[] = [];

  try {
    // Search for properties by address
    const addressMatches = await searchPropertiesByAddress(query, limit);
    suggestions.push(...addressMatches.map(property => ({
      address: property.phy_addr1,
      city: property.phy_city,
      zip_code: property.phy_zipcd,
      owner_name: property.own_name || property.owner_name,
      property_type: property.propertyUseDesc || property.property_use_desc || 'Property',
      parcel_id: property.parcel_id,
      type: 'property',
      value: property.jv || property.just_value || property.market_value,
      county: property.county,
      priority: property.phy_addr1?.toLowerCase().includes(query.toLowerCase())
    })));

    // Search for properties by owner name
    const ownerMatches = await searchPropertiesByOwner(query, Math.max(5, limit - suggestions.length));
    suggestions.push(...ownerMatches.map(property => ({
      owner_name: property.own_name || property.owner_name,
      address: property.phy_addr1,
      city: property.phy_city,
      zip_code: property.phy_zipcd,
      property_type: 'Owner',
      parcel_id: property.parcel_id,
      type: 'owner',
      county: property.county
    })));

    // Search for properties by city
    const cityMatches = await searchPropertiesByCity(query, Math.max(3, limit - suggestions.length));
    suggestions.push(...cityMatches.map(property => ({
      address: property.phy_addr1,
      city: property.phy_city,
      zip_code: property.phy_zipcd,
      owner_name: property.own_name || property.owner_name,
      property_type: property.propertyUseDesc || property.property_use_desc || 'Property',
      parcel_id: property.parcel_id,
      type: 'property',
      value: property.jv || property.just_value || property.market_value,
      county: property.county
    })));

    // Deduplicate by parcel_id and limit results
    const uniqueSuggestions = suggestions
      .filter((item, index, arr) =>
        arr.findIndex(other => other.parcel_id === item.parcel_id) === index
      )
      .slice(0, limit);

    // Sort by priority (exact matches first), then by value/relevance
    return uniqueSuggestions.sort((a, b) => {
      if (a.priority && !b.priority) return -1;
      if (!a.priority && b.priority) return 1;
      return (b.value || 0) - (a.value || 0);
    });

  } catch (error) {
    console.error('Error getting autocomplete suggestions:', error);
    return [];
  }
}

async function searchPropertiesByAddress(query: string, limit: number = 10) {
  // TODO: Implement Supabase query for address search
  // This would typically search phy_addr1 field with ILIKE
  return [];
}

async function searchPropertiesByOwner(query: string, limit: number = 5) {
  // TODO: Implement Supabase query for owner search
  // This would typically search own_name field with ILIKE
  return [];
}

async function searchPropertiesByCity(query: string, limit: number = 3) {
  // TODO: Implement Supabase query for city search
  // This would typically search phy_city field with ILIKE
  return [];
}

export default router;