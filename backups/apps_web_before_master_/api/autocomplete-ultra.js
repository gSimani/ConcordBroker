// Ultra-fast autocomplete - target: <50ms response time
// Extreme optimizations: minimal queries, aggressive caching, indexed-only searches

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Ultra-aggressive in-memory cache
class UltraCache {
  constructor() {
    this.cache = new Map();
    this.maxSize = 2000; // Larger cache
    this.ttl = 300000; // 5 minutes TTL
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item || Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    return item.data;
  }

  set(key, data) {
    if (this.cache.size >= this.maxSize) {
      // Remove 20% of oldest entries
      const entries = [...this.cache.entries()];
      const toRemove = Math.floor(this.maxSize * 0.2);
      entries.slice(0, toRemove).forEach(([k]) => this.cache.delete(k));
    }
    this.cache.set(key, { data, timestamp: Date.now() });
  }
}

const ultraCache = new UltraCache();

// Ultra-fast search with minimal database load
async function ultraSearch(query, limit = 10) {
  const startTime = Date.now();

  try {
    const normalizedQuery = query.trim().toUpperCase();
    const cacheKey = `${normalizedQuery}_${limit}`;

    // Check cache first
    const cached = ultraCache.get(cacheKey);
    if (cached) {
      return {
        results: cached,
        ms: Date.now() - startTime,
        cached: true
      };
    }

    // Determine optimal query strategy
    let results = [];

    if (/^\d{1,4}$/.test(normalizedQuery)) {
      // Pure numeric - address number only - fastest query
      const { data } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value')
        .ilike('phy_addr1', `${normalizedQuery}%`)
        .limit(limit);
      results = data || [];

    } else if (/^\d{1,4}\s*[NSEW]/.test(normalizedQuery)) {
      // Address with direction - specific indexed search
      const parts = normalizedQuery.split(/\s+/);
      const number = parts[0];
      const direction = parts[1];
      const { data } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value')
        .ilike('phy_addr1', `${number}%${direction}%`)
        .limit(limit);
      results = data || [];

    } else if (normalizedQuery.includes(',')) {
      // Owner name with comma - indexed owner search
      const { data } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value')
        .ilike('owner_name', `%${normalizedQuery}%`)
        .limit(limit);
      results = data || [];

    } else if (normalizedQuery.length <= 5) {
      // Short query - city or owner prefix
      const { data } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value')
        .or(`phy_city.ilike.${normalizedQuery}%,owner_name.ilike.${normalizedQuery}%`)
        .limit(limit);
      results = data || [];

    } else {
      // General search - use most selective condition first
      const { data } = await supabase
        .from('florida_parcels')
        .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, just_value')
        .ilike('owner_name', `%${normalizedQuery}%`)
        .limit(limit);
      results = data || [];
    }

    // Minimal data transformation for speed
    const processed = results.map(item => {
      const isAddress = item.phy_addr1 && /^\d/.test(item.phy_addr1);
      const display = isAddress ? item.phy_addr1 : (item.owner_name || 'Unknown');

      return {
        address: isAddress ? item.phy_addr1 : null,
        owner_name: !isAddress ? item.owner_name : null,
        city: item.phy_city,
        zip_code: item.phy_zipcd,
        property_type: getSimplePropertyType(item.property_use),
        parcel_id: item.parcel_id,
        just_value: item.just_value,
        type: isAddress ? 'property' : 'owner',
        icon: getQuickIcon(item.property_use, isAddress)
      };
    });

    // Cache results
    ultraCache.set(cacheKey, processed);

    return {
      results: processed,
      ms: Date.now() - startTime,
      cached: false
    };

  } catch (error) {
    console.error('Ultra search error:', error);
    return {
      results: [],
      ms: Date.now() - startTime,
      cached: false,
      error: error.message
    };
  }
}

function getSimplePropertyType(use) {
  if (!use) return 'Residential';
  const code = use.toString()[0];
  switch(code) {
    case '0': return 'Vacant Land';
    case '2': return 'Commercial';
    case '3': return 'Industrial';
    case '4': return 'Agricultural';
    default: return 'Residential';
  }
}

function getQuickIcon(use, isAddress) {
  if (!isAddress) return '👤'; // Owner
  if (!use) return '🏠';
  const code = use.toString()[0];
  switch(code) {
    case '0': return '🏞️';
    case '2': return '🏢';
    case '3': return '🏭';
    case '4': return '🌾';
    default: return '🏠';
  }
}

export default async function handler(req, res) {
  // Ultra-fast response headers
  res.setHeader('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=300');
  res.setHeader('Access-Control-Allow-Origin', '*');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { q, limit = 10 } = req.query;

  if (!q || q.length < 1) {
    return res.status(200).json({
      success: true,
      data: [],
      ms: 0,
      cached: false
    });
  }

  try {
    const searchResult = await ultraSearch(q, Math.min(parseInt(limit) || 10, 15));

    return res.status(200).json({
      success: true,
      data: searchResult.results,
      ms: searchResult.ms,
      cached: searchResult.cached,
      count: searchResult.results.length
    });

  } catch (error) {
    console.error('API error:', error);
    return res.status(200).json({
      success: false,
      data: [],
      ms: 0,
      error: error.message
    });
  }
}
