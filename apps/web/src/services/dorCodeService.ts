/**
 * DOR Use Code Lookup Service
 *
 * Provides mapping between property_use codes and standardized DOR use codes
 * Supports both Broward County text codes and numeric codes from other counties
 */

import { supabase } from '@/lib/supabase';

export interface DORUseCode {
  id: number;
  main_code: string;
  sub_code: string | null;
  full_code: string;
  description: string;
  category: string;
  created_at: string;
}

export interface DORCodeMapping {
  id: number;
  legacy_code: string;
  standard_full_code: string;
  county: string | null;
  confidence: string;
  created_at: string;
}

export interface PropertyUseInfo {
  code: string;
  full_code: string;
  description: string;
  category: string;
  sub_use: string | null;
  confidence: 'exact' | 'probable' | 'guess';
}

// In-memory cache for DOR codes
let dorCodesCache: DORUseCode[] | null = null;
let dorMappingsCache: DORCodeMapping[] | null = null;
let cacheTimestamp: number = 0;
const CACHE_TTL = 1000 * 60 * 60; // 1 hour

/**
 * Load DOR use codes from database into cache
 */
async function loadDORCodes(): Promise<void> {
  const now = Date.now();

  // Return cached data if still valid
  if (dorCodesCache && dorMappingsCache && (now - cacheTimestamp) < CACHE_TTL) {
    return;
  }

  try {
    // Load use codes
    const { data: codes, error: codesError } = await supabase
      .from('dor_use_codes_std')
      .select('*')
      .order('full_code');

    if (codesError) throw codesError;

    // Load mappings
    const { data: mappings, error: mappingsError } = await supabase
      .from('dor_code_mappings_std')
      .select('*');

    if (mappingsError) throw mappingsError;

    dorCodesCache = codes || [];
    dorMappingsCache = mappings || [];
    cacheTimestamp = now;

  } catch (error) {
    console.error('Failed to load DOR codes:', error);
    // Set empty caches to prevent repeated failed requests
    dorCodesCache = [];
    dorMappingsCache = [];
  }
}

/**
 * Get property use information from code
 */
export async function getPropertyUseInfo(
  propertyUse: string | number | null | undefined,
  county?: string | null
): Promise<PropertyUseInfo | null> {
  if (!propertyUse) return null;

  await loadDORCodes();

  const code = String(propertyUse).trim();

  // Try exact mapping first (for Broward text codes like "SFR", "CONDO")
  const mapping = dorMappingsCache?.find(m =>
    m.legacy_code === code && (!m.county || m.county === county)
  );

  if (mapping) {
    const dorCode = dorCodesCache?.find(c => c.full_code === mapping.standard_full_code);
    if (dorCode) {
      return {
        code,
        full_code: dorCode.full_code,
        description: dorCode.description,
        category: dorCode.category,
        sub_use: dorCode.sub_code,
        confidence: mapping.confidence as any
      };
    }
  }

  // Try to match numeric code with default sub-code (e.g., "1" -> "01-01")
  const paddedCode = code.padStart(2, '0');
  const defaultFullCode = `${paddedCode}-01`; // Assume -01 as default sub-code

  const dorCode = dorCodesCache?.find(c => c.full_code === defaultFullCode);
  if (dorCode) {
    return {
      code,
      full_code: dorCode.full_code,
      description: dorCode.description,
      category: dorCode.category,
      sub_use: dorCode.sub_code,
      confidence: 'probable'
    };
  }

  // Try to match by main_code only (less specific)
  const mainCodeMatch = dorCodesCache?.find(c => c.main_code === paddedCode);
  if (mainCodeMatch) {
    return {
      code,
      full_code: mainCodeMatch.full_code,
      description: mainCodeMatch.description,
      category: mainCodeMatch.category,
      sub_use: mainCodeMatch.sub_code,
      confidence: 'guess'
    };
  }

  // Fallback to category-based guessing
  return getCategoryFromNumericCode(code);
}

/**
 * Fallback: Guess category from numeric code range
 */
function getCategoryFromNumericCode(code: string): PropertyUseInfo | null {
  const num = parseInt(code);
  if (isNaN(num)) return null;

  let category = 'Unknown';
  let description = 'Unknown Property Type';

  if (num >= 0 && num <= 9) {
    category = 'Residential';
    description = 'Residential Property';
    if (num === 0) {
      category = 'Vacant Land';
      description = 'Vacant Residential';
    } else if (num === 1) {
      description = 'Single Family Residential';
    } else if (num === 2) {
      description = 'Manufactured Housing';
    }
  } else if (num >= 10 && num <= 39) {
    category = 'Commercial';
    description = 'Commercial Property';
    if (num >= 17 && num <= 20) {
      description = 'Retail/Office Commercial';
    }
  } else if (num >= 40 && num <= 49) {
    category = 'Industrial';
    description = 'Industrial Property';
  } else if (num >= 50 && num <= 69) {
    category = 'Agricultural';
    description = 'Agricultural Land';
    if (num >= 60 && num <= 61) {
      description = 'Grazing/Cropland';
    }
  } else if (num >= 70 && num <= 89) {
    category = 'Institutional';
    description = 'Institutional/Government Property';
  } else if (num >= 90 && num <= 99) {
    category = 'Vacant Land';
    description = 'Vacant/Improved Land';
    if (num === 99) {
      description = 'Improved Acreage';
    }
  }

  return {
    code,
    full_code: `${String(num).padStart(2, '0')}-00`,
    description,
    category,
    sub_use: null,
    confidence: 'guess'
  };
}

/**
 * Get all DOR codes for a category
 */
export async function getDORCodesByCategory(category: string): Promise<DORUseCode[]> {
  await loadDORCodes();
  return dorCodesCache?.filter(c => c.category === category) || [];
}

/**
 * Get all available categories
 */
export async function getDORCategories(): Promise<string[]> {
  await loadDORCodes();
  const categories = new Set(dorCodesCache?.map(c => c.category) || []);
  return Array.from(categories).sort();
}

/**
 * Search DOR codes by description
 */
export async function searchDORCodes(query: string): Promise<DORUseCode[]> {
  await loadDORCodes();
  const lowerQuery = query.toLowerCase();
  return dorCodesCache?.filter(c =>
    c.description.toLowerCase().includes(lowerQuery) ||
    c.category.toLowerCase().includes(lowerQuery) ||
    c.full_code.includes(query)
  ) || [];
}

/**
 * Clear cache (useful for testing or after updates)
 */
export function clearDORCache(): void {
  dorCodesCache = null;
  dorMappingsCache = null;
  cacheTimestamp = 0;
}

/**
 * Format property use for display
 */
export function formatPropertyUse(info: PropertyUseInfo | null): string {
  if (!info) return 'Unknown';

  return info.description;
}

/**
 * Get badge color for property category
 */
export function getCategoryColor(category: string): string {
  switch (category) {
    case 'Residential':
      return '#3498db'; // Blue
    case 'Commercial':
      return '#e67e22'; // Orange
    case 'Industrial':
      return '#95a5a6'; // Gray
    case 'Agricultural':
      return '#27ae60'; // Green
    case 'Institutional':
      return '#9b59b6'; // Purple
    case 'Vacant Land':
      return '#f39c12'; // Yellow
    default:
      return '#7f8c8d'; // Dark gray
  }
}

export default {
  getPropertyUseInfo,
  getDORCodesByCategory,
  getDORCategories,
  searchDORCodes,
  clearDORCache,
  formatPropertyUse,
  getCategoryColor
};
