// Professional Autocomplete API with Sunbiz Integration and Lightning Fast Response
// Includes Redis caching, property icons, and corporation matching

import { createClient } from '@supabase/supabase-js';

// Initialize Supabase from environment only
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '';
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// Enhanced LRU cache for ultra-fast responses
class LRUCache {
  constructor(maxSize = 1000, ttl = 60000) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.ttl = ttl;
  }

  get(key) {
    const entry = this.cache.get(key);
    if (!entry) return null;

    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    // Move to end (most recently used)
    this.cache.delete(key);
    this.cache.set(key, entry);
    return entry.data;
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
}

const cache = new LRUCache(1000, 60000); // 1000 entries, 1 minute TTL

function getCacheKey(query, type) {
  return `${query.toUpperCase().replace(/\s+/g, '_')}_${type}`;
}

function getCachedResult(query, type) {
  return cache.get(getCacheKey(query, type));
}

function setCachedResult(query, type, data) {
  cache.set(getCacheKey(query, type), data);
}

async function searchProperties(query, limit = 20) {
  try {
    // Optimized normalization for speed
    const trimmedQuery = query.trim();
    const normalizedQuery = trimmedQuery.toUpperCase().replace(/\s+/g, ' ');

    // Build focused search query based on input type
    const searchQuery = supabase
      .from('florida_parcels')
      .select('parcel_id, phy_addr1, phy_city, phy_zipcd, owner_name, property_use, county, just_value, sale_price, sale_date')
      .limit(limit);

    // Determine search strategy based on query pattern
    if (/^\d/.test(trimmedQuery)) {
      // Address search - use prefix matching for speed
      const streetNumber = normalizedQuery.split(' ')[0];

      // Handle variations efficiently
      if (normalizedQuery.includes(' ')) {
        // Has space - search with flexible spacing
        const parts = normalizedQuery.split(' ');
        const pattern = parts.join('%'); // Allow flexible spacing
        searchQuery.or(`phy_addr1.ilike.%${pattern}%,phy_addr1.ilike.${streetNumber}%`);
      } else {
        // No space - might be like "3930SW"
        // Add space before common directions
        const withSpace = normalizedQuery.replace(/(\d+)(SW|SE|NW|NE|N|S|E|W)/g, '$1 $2');
        searchQuery.or(`phy_addr1.ilike.${normalizedQuery}%,phy_addr1.ilike.${withSpace}%,phy_addr1.ilike.${streetNumber}%`);
      }
    } else if (normalizedQuery.includes(',')) {
      // Owner name search (Last, First format)
      searchQuery.ilike('owner_name', `%${normalizedQuery}%`);
    } else if (normalizedQuery.length <= 3) {
      // Short query - likely city abbreviation or company suffix
      searchQuery.or(`phy_city.ilike.${normalizedQuery}%,owner_name.ilike.%${normalizedQuery}%`);
    } else {
      // General text search - use targeted fields
      searchQuery.or(`phy_city.ilike.%${normalizedQuery}%,owner_name.ilike.%${normalizedQuery}%,phy_addr1.ilike.%${normalizedQuery}%`);
    }

    const { data, error } = await searchQuery;

    if (error) throw error;

    return data.map(item => ({
      parcel_id: item.parcel_id,
      address: item.phy_addr1,
      city: item.phy_city,
      zip_code: item.phy_zipcd,
      owner_name: item.owner_name,
      property_type: getPropertyType(item.property_use),
      county: item.county,
      just_value: item.just_value,
      sale_price: item.sale_price,
      sale_date: item.sale_date,
      type: 'property',
      icon: getPropertyIcon(item.property_use)
    }));
  } catch (error) {
    console.error('Property search error:', error);
    return [];
  }
}

async function searchSunbizCompanies(query, limit = 10) {
  try {
    // Ultra-flexible normalization for company searches
    const trimmedQuery = query.trim();
    const normalizedQuery = trimmedQuery.toUpperCase().replace(/\s+/g, ' ');

    // Create multiple search variations for companies
    const searchVariations = [
      trimmedQuery,           // Original case
      normalizedQuery,        // Uppercase
      trimmedQuery.toLowerCase(), // Lowercase
    ];

    // Add variations without common suffixes
    const withoutSuffixes = normalizedQuery
      .replace(/\s*(INC\.?|LLC\.?|CORP\.?|CORPORATION|LIMITED|LTD\.?|CO\.?|COMPANY)\s*$/i, '')
      .trim();
    if (withoutSuffixes !== normalizedQuery) {
      searchVariations.push(withoutSuffixes);
    }

    // Add variations with common suffixes if not present
    if (!normalizedQuery.match(/(INC|LLC|CORP|LTD)/i)) {
      searchVariations.push(`${normalizedQuery} LLC`);
      searchVariations.push(`${normalizedQuery} INC`);
      searchVariations.push(`${normalizedQuery} CORP`);
    }

    // Build comprehensive OR conditions for company search
    const orConditions = [];
    searchVariations.forEach(variation => {
      // Company name search
      orConditions.push(`corp_name.ilike.%${variation}%`);

      // Principal address search
      orConditions.push(`principal_addr.ilike.%${variation}%`);

      // Officer search (if we have officer columns)
      orConditions.push(`registered_agent_name.ilike.%${variation}%`);

      // Document number search
      if (/^[A-Z0-9]+$/i.test(variation)) {
        orConditions.push(`corp_number.ilike.%${variation}%`);
      }
    });

    // Search active Florida corporations with ultra-flexible matching
    const { data: companies, error } = await supabase
      .from('sunbiz_companies')
      .select('corp_number, corp_name, status, filing_type, principal_addr, principal_city, principal_state, principal_zip, last_event_date, registered_agent_name')
      .or(orConditions.join(','))
      .limit(limit * 2); // Get more results to filter

    // Filter and prioritize results
    let results = [];

    if (!error && companies && companies.length > 0) {
      // Separate active and inactive
      const activeCompanies = companies.filter(c => c.status === 'ACTIVE');
      const inactiveCompanies = companies.filter(c => c.status !== 'ACTIVE');

      // Prioritize active companies
      results = [...activeCompanies, ...inactiveCompanies].slice(0, limit);
    }

    if (results.length === 0 || error) {
      // Fallback: Try florida_entities table with same flexible approach
      const entityConditions = [];
      searchVariations.forEach(variation => {
        entityConditions.push(`entity_name.ilike.%${variation}%`);
        entityConditions.push(`principal_address.ilike.%${variation}%`);
        entityConditions.push(`registered_agent.ilike.%${variation}%`);
        entityConditions.push(`document_number.ilike.%${variation}%`);
      });

      const { data: entities } = await supabase
        .from('florida_entities')
        .select('*')
        .or(entityConditions.join(','))
        .limit(limit);

      if (entities && entities.length > 0) {
        return entities.map(item => ({
          corp_number: item.document_number,
          corp_name: item.entity_name,
          status: item.status,
          filing_type: item.entity_type,
          address: item.principal_address,
          city: item.principal_city,
          state: item.principal_state,
          zip_code: item.principal_zip,
          officer: item.registered_agent,
          type: 'company',
          icon: '🏢'
        }));
      }
    }

    if (results.length > 0) {
      return results.map(item => ({
        corp_number: item.corp_number,
        corp_name: item.corp_name,
        status: item.status,
        filing_type: item.filing_type,
        address: item.principal_addr,
        city: item.principal_city,
        state: item.principal_state,
        zip_code: item.principal_zip,
        officer: item.registered_agent_name,
        type: 'company',
        icon: getCompanyIcon(item.filing_type)
      }));
    }

    return [];
  } catch (error) {
    console.error('Sunbiz search error:', error);
    return [];
  }
}

async function searchOwners(query, limit = 10) {
  try {
    // Ultra-flexible owner search
    const trimmedQuery = query.trim();
    const normalizedQuery = trimmedQuery.toUpperCase().replace(/\s+/g, ' ');

    // Create search variations for names
    const nameVariations = [];

    // Original and normalized
    nameVariations.push(trimmedQuery);
    nameVariations.push(normalizedQuery);
    nameVariations.push(trimmedQuery.toLowerCase());

    // Handle name formats (Last, First or First Last)
    if (trimmedQuery.includes(',')) {
      // "Smith, John" -> also search "John Smith"
      const [last, first] = trimmedQuery.split(',').map(s => s.trim());
      if (first && last) {
        nameVariations.push(`${first} ${last}`);
        nameVariations.push(`${first.toUpperCase()} ${last.toUpperCase()}`);
      }
    } else if (trimmedQuery.includes(' ')) {
      // "John Smith" -> also search "Smith, John" and "Smith John"
      const parts = trimmedQuery.split(/\s+/);
      if (parts.length === 2) {
        const [first, last] = parts;
        nameVariations.push(`${last}, ${first}`);
        nameVariations.push(`${last.toUpperCase()}, ${first.toUpperCase()}`);
        nameVariations.push(`${last}${first}`);
      }
    }

    // Handle partial names
    const words = normalizedQuery.split(/\s+/);
    words.forEach(word => {
      if (word.length >= 3) {
        nameVariations.push(word);
      }
    });

    // Build comprehensive OR conditions
    const orConditions = [];
    nameVariations.forEach(variation => {
      orConditions.push(`owner_name.ilike.%${variation}%`);
    });

    const { data, error } = await supabase
      .from('florida_parcels')
      .select('owner_name, phy_city, county, phy_addr1, just_value')
      .or(orConditions.join(','))
      .limit(limit * 3); // Get more to deduplicate

    if (error) throw error;

    // Deduplicate and enrich owners
    const uniqueOwners = new Map();
    data.forEach(item => {
      const key = item.owner_name?.toUpperCase();
      if (key && !uniqueOwners.has(key)) {
        uniqueOwners.set(key, {
          owner_name: item.owner_name,
          city: item.phy_city,
          county: item.county,
          property_address: item.phy_addr1,
          property_value: item.just_value,
          type: 'owner',
          icon: '👤'
        });
      }
    });

    // Sort by relevance (exact matches first)
    const results = Array.from(uniqueOwners.values());
    results.sort((a, b) => {
      const aExact = a.owner_name.toUpperCase() === normalizedQuery;
      const bExact = b.owner_name.toUpperCase() === normalizedQuery;
      if (aExact && !bExact) return -1;
      if (!aExact && bExact) return 1;
      return 0;
    });

    return results.slice(0, limit);
  } catch (error) {
    console.error('Owner search error:', error);
    return [];
  }
}

function getPropertyType(propertyUse) {
  if (!propertyUse) return 'Residential';

  const use = propertyUse.toString();
  if (use.startsWith('0')) return 'Vacant Land';
  if (use.startsWith('1')) return 'Residential';
  if (use.startsWith('2')) return 'Commercial';
  if (use.startsWith('3')) return 'Industrial';
  if (use.startsWith('4')) return 'Agricultural';
  if (use.startsWith('5')) return 'Institutional';
  if (use.startsWith('6')) return 'Government';
  if (use.startsWith('7')) return 'Miscellaneous';
  if (use.startsWith('8')) return 'Centrally Assessed';
  if (use.startsWith('9')) return 'Non-Agricultural';

  return 'Residential';
}

function getPropertyIcon(propertyUse) {
  const type = getPropertyType(propertyUse);
  switch (type) {
    case 'Commercial': return '🏢';
    case 'Industrial': return '🏭';
    case 'Agricultural': return '🌾';
    case 'Vacant Land': return '🏞️';
    case 'Government': return '🏛️';
    case 'Institutional': return '🏥';
    default: return '🏠';
  }
}

function getCompanyIcon(filingType) {
  if (!filingType) return '🏢';
  const type = filingType.toUpperCase();
  if (type.includes('CORP')) return '🏢';
  if (type.includes('LLC')) return '🏪';
  if (type.includes('PARTNER')) return '🤝';
  if (type.includes('NONPROFIT')) return '🏛️';
  return '🏢';
}

export default async function handler(req, res) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 's-maxage=10, stale-while-revalidate=59');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const startTime = Date.now();
  const { q, limit = 20, type = 'combined' } = req.query;

  if (!q || q.length < 2) {
    return res.status(200).json({
      success: true,
      data: [],
      count: 0,
      query: q || '',
      response_time_ms: 0,
      cached: false
    });
  }

  try {
    // Check cache first
    const cached = getCachedResult(q, type);
    if (cached) {
      return res.status(200).json({
        success: true,
        data: cached,
        count: cached.length,
        query: q,
        response_time_ms: Date.now() - startTime,
        cached: true
      });
    }

    let results = [];

    if (type === 'combined' || type === 'all') {
      // Parallel search across all data sources
      const [properties, companies, owners] = await Promise.all([
        searchProperties(q, Math.floor(limit * 0.6)),
        searchSunbizCompanies(q, Math.floor(limit * 0.3)),
        searchOwners(q, Math.floor(limit * 0.1))
      ]);

      // Combine and sort by relevance
      results = [
        ...properties,
        ...companies,
        ...owners
      ];

      // Sort by relevance (exact matches first)
      results.sort((a, b) => {
        const aMatch = (
          a.address?.toLowerCase().startsWith(q.toLowerCase()) ||
          a.corp_name?.toLowerCase().startsWith(q.toLowerCase()) ||
          a.owner_name?.toLowerCase().startsWith(q.toLowerCase())
        ) ? 0 : 1;

        const bMatch = (
          b.address?.toLowerCase().startsWith(q.toLowerCase()) ||
          b.corp_name?.toLowerCase().startsWith(q.toLowerCase()) ||
          b.owner_name?.toLowerCase().startsWith(q.toLowerCase())
        ) ? 0 : 1;

        return aMatch - bMatch;
      });

      results = results.slice(0, limit);

    } else if (type === 'property') {
      results = await searchProperties(q, limit);
    } else if (type === 'company') {
      results = await searchSunbizCompanies(q, limit);
    } else if (type === 'owner') {
      results = await searchOwners(q, limit);
    }

    // Cache the results
    setCachedResult(q, type, results);

    const responseTime = Date.now() - startTime;

    return res.status(200).json({
      success: true,
      data: results,
      count: results.length,
      query: q,
      response_time_ms: responseTime,
      cached: false,
      source: 'Supabase + Sunbiz'
    });

  } catch (error) {
    console.error('API error:', error);
    return res.status(500).json({
      success: false,
      error: 'Search failed',
      message: error.message,
      query: q
    });
  }
}
