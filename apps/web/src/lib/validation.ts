/**
 * Zod Validation Schemas for ConcordBroker
 * TypeScript-first schema validation for all property data
 */

import { z } from 'zod';

// ============================================
// PROPERTY SCHEMAS
// ============================================

/**
 * Florida Parcel Schema
 * Validates property data from Florida state sources
 */
export const FloridaParcelSchema = z.object({
  parcel_id: z.string().min(1).max(50),
  county: z.string().min(1).max(50),
  year: z.number().int().min(2000).max(2050),
  
  // Geometry
  geometry: z.any().optional(), // GeoJSON
  centroid: z.any().optional(),
  area_sqft: z.number().positive().optional(),
  perimeter_ft: z.number().positive().optional(),
  
  // Ownership
  owner_name: z.string().max(255).optional(),
  owner_addr1: z.string().max(255).optional(),
  owner_addr2: z.string().max(255).optional(),
  owner_city: z.string().max(100).optional(),
  owner_state: z.string().length(2).optional(),
  owner_zip: z.string().regex(/^\d{5}(-\d{4})?$/).optional(),
  
  // Physical address
  phy_addr1: z.string().max(255).optional(),
  phy_addr2: z.string().max(255).optional(),
  phy_city: z.string().max(100).optional(),
  phy_state: z.string().length(2).default('FL'),
  phy_zipcd: z.string().regex(/^\d{5}(-\d{4})?$/).optional(),
  
  // Legal description
  legal_desc: z.string().optional(),
  subdivision: z.string().max(255).optional(),
  lot: z.string().max(50).optional(),
  block: z.string().max(50).optional(),
  
  // Property characteristics
  property_use: z.string().max(10).optional(),
  property_use_desc: z.string().max(255).optional(),
  land_use_code: z.string().max(10).optional(),
  zoning: z.string().max(50).optional(),
  
  // Valuations (ensure positive numbers)
  just_value: z.number().nonnegative().optional(),
  assessed_value: z.number().nonnegative().optional(),
  taxable_value: z.number().nonnegative().optional(),
  land_value: z.number().nonnegative().optional(),
  building_value: z.number().nonnegative().optional(),
  
  // Property details
  year_built: z.number().int().min(1800).max(2050).optional(),
  total_living_area: z.number().nonnegative().optional(),
  bedrooms: z.number().int().min(0).max(100).optional(),
  bathrooms: z.number().min(0).max(100).optional(),
  stories: z.number().min(0).max(100).optional(),
  units: z.number().int().min(0).optional(),
  
  // Land measurements
  land_sqft: z.number().nonnegative().optional(),
  land_acres: z.number().nonnegative().optional(),
  
  // Sales information
  sale_date: z.coerce.date().optional(),
  sale_price: z.number().nonnegative().optional(),
  sale_qualification: z.string().max(10).optional(),
  
  // Data quality flags
  match_status: z.enum(['matched', 'partial', 'unmatched', 'polygon_only']).optional(),
  discrepancy_reason: z.string().max(100).optional(),
  is_redacted: z.boolean().default(false),
  data_source: z.string().max(20).optional(),
  
  // Metadata
  import_date: z.coerce.date().default(() => new Date()),
  update_date: z.coerce.date().optional(),
  data_hash: z.string().max(64).optional(),
});

export type FloridaParcel = z.infer<typeof FloridaParcelSchema>;

/**
 * Property Sales Data Schema (SDF)
 */
export const PropertySaleSchema = z.object({
  parcel_id: z.string().min(1).max(50),
  county: z.string().min(1).max(50),
  
  // Sale information
  sale_date: z.coerce.date(),
  sale_price: z.number().positive(),
  sale_type: z.string().max(50).optional(),
  qualification_code: z.string().max(10).optional(),
  
  // Parties
  grantor_name: z.string().max(255).optional(),
  grantee_name: z.string().max(255).optional(),
  
  // Property details at sale
  property_address: z.string().max(255).optional(),
  property_use_code: z.string().max(10).optional(),
  
  // Valuations at sale
  just_value_at_sale: z.number().nonnegative().optional(),
  assessed_value_at_sale: z.number().nonnegative().optional(),
  
  // Analysis metrics
  price_per_sqft: z.number().positive().optional(),
  sale_ratio: z.number().min(0).max(10).optional(),
  
  // Flags for special sale types
  is_qualified_sale: z.boolean().default(false),
  is_arms_length: z.boolean().default(false),
  is_foreclosure: z.boolean().default(false),
  is_reo_sale: z.boolean().default(false),
  is_short_sale: z.boolean().default(false),
  
  // Entity flags
  is_corporate_buyer: z.boolean().default(false),
  is_corporate_seller: z.boolean().default(false),
  buyer_entity_type: z.string().max(50).optional(),
  seller_entity_type: z.string().max(50).optional(),
  
  // Recording info
  or_book: z.string().max(20).optional(),
  or_page: z.string().max(20).optional(),
  instrument_number: z.string().max(30).optional(),
  
  import_date: z.coerce.date().default(() => new Date()),
});

export type PropertySale = z.infer<typeof PropertySaleSchema>;

// ============================================
// BUSINESS ENTITY SCHEMAS
// ============================================

/**
 * Sunbiz Corporate Entity Schema
 */
export const SunbizCorporateSchema = z.object({
  doc_number: z.string().max(12),
  entity_name: z.string().max(200).optional(),
  status: z.enum(['ACTIVE', 'INACTIVE', 'DISSOLVED', 'ADMIN_DISSOLVED', 'WITHDRAWN']).optional(),
  filing_date: z.coerce.date().optional(),
  state_country: z.string().max(50).optional(),
  
  // Principal Address
  prin_addr1: z.string().max(100).optional(),
  prin_addr2: z.string().max(100).optional(),
  prin_city: z.string().max(50).optional(),
  prin_state: z.string().length(2).optional(),
  prin_zip: z.string().regex(/^\d{5}(-\d{4})?$/).optional(),
  
  // Mailing Address
  mail_addr1: z.string().max(100).optional(),
  mail_addr2: z.string().max(100).optional(),
  mail_city: z.string().max(50).optional(),
  mail_state: z.string().length(2).optional(),
  mail_zip: z.string().regex(/^\d{5}(-\d{4})?$/).optional(),
  
  // Additional Info
  ein: z.string().regex(/^\d{2}-\d{7}$/).optional(),
  registered_agent: z.string().max(100).optional(),
  
  // Metadata
  file_type: z.string().max(20).optional(),
  subtype: z.string().max(20).optional(),
  source_file: z.string().max(100).optional(),
  import_date: z.coerce.date().default(() => new Date()),
  update_date: z.coerce.date().optional(),
});

export type SunbizCorporate = z.infer<typeof SunbizCorporateSchema>;

// ============================================
// ASSESSMENT SCHEMAS
// ============================================

/**
 * Non-Ad Valorem Assessment Schema
 */
export const NAVAssessmentSchema = z.object({
  parcel_id: z.string().min(1).max(50),
  county: z.string().min(1).max(50),
  tax_year: z.number().int().min(2000).max(2050),
  
  // Property identification
  owner_name: z.string().max(255).optional(),
  property_address: z.string().max(255).optional(),
  
  // Assessment totals (ensure non-negative)
  total_nav_amount: z.number().nonnegative(),
  total_assessments: z.number().int().nonnegative(),
  
  // Common assessment types
  cdd_amount: z.number().nonnegative().optional(),
  hoa_amount: z.number().nonnegative().optional(),
  special_district_amount: z.number().nonnegative().optional(),
  
  // Payment status
  payment_status: z.enum(['PAID', 'UNPAID', 'PARTIAL', 'DELINQUENT']).optional(),
  delinquent_amount: z.number().nonnegative().optional(),
  
  import_date: z.coerce.date().default(() => new Date()),
});

export type NAVAssessment = z.infer<typeof NAVAssessmentSchema>;

// ============================================
// API REQUEST/RESPONSE SCHEMAS
// ============================================

/**
 * Property Search Request Schema
 */
export const PropertySearchRequestSchema = z.object({
  query: z.string().optional(),
  county: z.string().optional(),
  city: z.string().optional(),
  zip: z.string().optional(),
  min_price: z.number().positive().optional(),
  max_price: z.number().positive().optional(),
  min_sqft: z.number().positive().optional(),
  max_sqft: z.number().positive().optional(),
  property_type: z.string().optional(),
  year_built_min: z.number().int().optional(),
  year_built_max: z.number().int().optional(),
  sale_date_from: z.coerce.date().optional(),
  sale_date_to: z.coerce.date().optional(),
  limit: z.number().int().min(1).max(1000).default(100),
  offset: z.number().int().min(0).default(0),
});

export type PropertySearchRequest = z.infer<typeof PropertySearchRequestSchema>;

/**
 * API Response Schema
 */
export const ApiResponseSchema = <T extends z.ZodType>(dataSchema: T) => z.object({
  success: z.boolean(),
  data: dataSchema.optional(),
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.any().optional(),
  }).optional(),
  metadata: z.object({
    total: z.number().int().optional(),
    page: z.number().int().optional(),
    limit: z.number().int().optional(),
    timestamp: z.coerce.date(),
  }).optional(),
});

// ============================================
// VALIDATION UTILITIES
// ============================================

/**
 * Safe parse with error formatting
 */
export function safeParse<T>(schema: z.ZodSchema<T>, data: unknown): {
  success: boolean;
  data?: T;
  errors?: string[];
} {
  const result = schema.safeParse(data);
  
  if (result.success) {
    return { success: true, data: result.data };
  }
  
  const errors = result.error.errors.map(err => 
    `${err.path.join('.')}: ${err.message}`
  );
  
  return { success: false, errors };
}

/**
 * Validate and clean property data
 */
export function validatePropertyData(data: unknown): FloridaParcel | null {
  const result = FloridaParcelSchema.safeParse(data);
  
  if (result.success) {
    return result.data;
  }
  
  console.error('Property validation failed:', result.error.errors);
  return null;
}

/**
 * Batch validation with detailed reporting
 */
export function validateBatch<T>(
  schema: z.ZodSchema<T>,
  items: unknown[]
): {
  valid: T[];
  invalid: { item: unknown; errors: string[] }[];
  stats: {
    total: number;
    valid: number;
    invalid: number;
    successRate: number;
  };
} {
  const valid: T[] = [];
  const invalid: { item: unknown; errors: string[] }[] = [];
  
  for (const item of items) {
    const result = safeParse(schema, item);
    
    if (result.success && result.data) {
      valid.push(result.data);
    } else if (result.errors) {
      invalid.push({ item, errors: result.errors });
    }
  }
  
  const total = items.length;
  const validCount = valid.length;
  const invalidCount = invalid.length;
  
  return {
    valid,
    invalid,
    stats: {
      total,
      valid: validCount,
      invalid: invalidCount,
      successRate: total > 0 ? (validCount / total) * 100 : 0,
    },
  };
}

// ============================================
// CUSTOM VALIDATORS
// ============================================

/**
 * Florida-specific validations
 */
export const FloridaValidators = {
  isValidParcelId: (id: string): boolean => {
    // Florida parcel IDs typically follow county-specific formats
    return /^[0-9A-Z\-\.]+$/.test(id) && id.length >= 10 && id.length <= 30;
  },
  
  isValidFloridaZip: (zip: string): boolean => {
    // Florida ZIP codes range from 32003 to 34997
    const numZip = parseInt(zip.substring(0, 5));
    return numZip >= 32003 && numZip <= 34997;
  },
  
  isValidCounty: (county: string): boolean => {
    const floridaCounties = [
      'BROWARD', 'MIAMI-DADE', 'PALM BEACH', 'MONROE',
      'COLLIER', 'LEE', 'ORANGE', 'HILLSBOROUGH',
      'PINELLAS', 'DUVAL', 'BREVARD', 'VOLUSIA'
    ];
    return floridaCounties.includes(county.toUpperCase());
  },
};

export default {
  // Schemas
  FloridaParcelSchema,
  PropertySaleSchema,
  SunbizCorporateSchema,
  NAVAssessmentSchema,
  PropertySearchRequestSchema,
  ApiResponseSchema,
  
  // Utilities
  safeParse,
  validatePropertyData,
  validateBatch,
  
  // Custom Validators
  FloridaValidators,
};