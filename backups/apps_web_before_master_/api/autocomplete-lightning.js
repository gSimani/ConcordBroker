// Lightning-fast autocomplete with optimized queries and aggressive caching
// Target: <100ms response time

import { createClient } from '@supabase/supabase-js';

// Initialize Supabase from environment only
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Enhanced in-memory cache with LRU eviction
class LRUCache {
  constructor(maxSize = 500) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  get(key) {
    if (!this.cache.has(key)) return null;

    const item = this.cache.get(key);
    if (Date.now() - item.timestamp > 60000) { // 1 minute TTL
      this.cache.delete(key);
      return null;
    }

    // Move to end (most recently used)
    this.cache.delete(key);
    this.cache.set(key, item);
    return item.data;
  }

  set(key, data) {
    // Remove oldest if at capacity
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  clear() {
    this.cache.clear();
  }
}

const cache = new LRUCache(500);

// Pre-warm cache with common queries
const commonQueries = ['miami', 'fort', 'llc', '123', '456'];
async function warmCache() {
  for (const q of commonQueries) {
    lightningSearch(q, 5).catch(() => {});
  }
}

// Lightning-fast search with optimized queries
async function lightningSearch(query, limit = 10) {
  try {
    const normalizedQuery = query.trim().toUpperCase();

    // Check cache first
    const cacheKey = `${normalizedQuery}_${limit}`;
    const cached = cache.get(cacheKey);
    if (cached) return cached;

    // Determine search type and optimize query accordingly
    const isNumeric = /^\d/.test(normalizedQuery);
    const hasComma = normalizedQuery.includes(',');
    const isShort = normalizedQuery.length <= 3;

    // Build optimized query based on input type
    let searchQuery;

    if (isNumeric) {
      // Address search - most specific, use indexed column
      searchQuery = supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, county, just_value')
        .or(`phy_addr1.ilike.${normalizedQuery}%,parcel_id.ilike.${normalizedQuery}%`)
        .limit(limit);
    } else if (hasComma) {
      // Owner name with comma - use specific owner search
      searchQuery = supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, county, just_value')
        .ilike('owner_name', `%${normalizedQuery}%`)
        .limit(limit);
    } else if (isShort) {
      // Short query - limit to most likely matches
      searchQuery = supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, county, just_value')
        .or(`phy_city.ilike.${normalizedQuery}%,owner_name.ilike.${normalizedQuery}%`)
        .limit(limit);
    } else {
      // General search - use prefix matching for speed
      searchQuery = supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, county, just_value')
        .or(`phy_addr1.ilike.%${normalizedQuery}%,phy_city.ilike.${normalizedQuery}%,owner_name.ilike.${normalizedQuery}%`)
        .limit(limit);
    }

    const { data, error } = await searchQuery;

    if (error) throw error;

    // Minimal data transformation for speed
    const results = (data || []).map(item => ({
      id: item.parcel_id,
      text: item.phy_addr1 || item.owner_name || '',
      sub: `${item.phy_city || ''} ${item.phy_zipcd || ''}`.trim(),
      type: getQuickType(item.property_use),
      value: item.just_value
    }));

    // Cache the results
    cache.set(cacheKey, results);

    return results;
  } catch (error) {
    console.error('Search error:', error);
    return [];
  }
}

function getQuickType(propertyUse) {
  if (!propertyUse) return '🏠';
  const use = propertyUse.toString()[0];
  switch(use) {
    case '0': return '🏞️';
    case '2': return '🏢';
    case '3': return '🏭';
    case '4': return '🌾';
    default: return '🏠';
  }
}

export default async function handler(req, res) {
  // Enable CORS and caching headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Cache-Control', 'public, s-maxage=30, stale-while-revalidate=59');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const startTime = Date.now();
  const { q, limit = 10 } = req.query;

  if (!q || q.length < 2) {
    return res.status(200).json({
      success: true,
      data: [],
      ms: 0
    });
  }

  try {
    const results = await lightningSearch(q, Math.min(parseInt(limit) || 10, 20));

    return res.status(200).json({
      success: true,
      data: results,
      ms: Date.now() - startTime,
      cached: cache.get(`${q.trim().toUpperCase()}_${limit}`) === results
    });

  } catch (error) {
    console.error('API error:', error);
    return res.status(200).json({
      success: false,
      data: [],
      ms: Date.now() - startTime,
      error: error.message
    });
  }
}

// Warm cache on cold start
warmCache();
