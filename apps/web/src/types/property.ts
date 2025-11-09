/**
 * Comprehensive Property Data Types for ConcordBroker
 *
 * This file contains all TypeScript interfaces for Florida property data,
 * replacing all `any` types with proper type definitions.
 */

// ============================================
// FLORIDA PARCELS DATA (BCPA - Property Appraiser)
// ============================================

export interface FloridaParcelData {
  // Primary identifiers
  parcel_id: string;
  county: string;
  year?: number;

  // Property address
  phy_addr1: string | null;
  phy_addr2?: string | null;
  phy_city: string | null;
  phy_zipcd: string | null;
  phy_state?: string;

  // Owner information
  owner_name: string | null;
  owner_addr1: string | null;
  owner_addr2?: string | null;
  owner_city: string | null;
  owner_state: string | null;
  owner_zip: string | null;
  owner_zipcd?: string | null;

  // Property values
  just_value: number;
  assessed_value: number;
  taxable_value: number;
  land_value: number;
  building_value?: number;
  market_value?: number;

  // Property characteristics
  year_built: string | number | null;
  total_living_area: string | number | null;
  bedrooms: string | number | null;
  bathrooms: string | number | null;
  half_baths?: string | number | null;
  land_sqft: string | number | null;
  building_sqft?: string | number | null;

  // Property classification
  property_use_code: string | null;
  property_use_desc: string | null;
  property_use?: string;
  dor_uc?: string; // DOR Use Code
  property_type_desc?: string;
  land_use_desc?: string;

  // Sales information
  sale_date: string | null;
  sale_price: string | number | null;
  sale_year: string | number | null;
  sale_month: string | number | null;
  sale_qualification?: string;

  // Tax information
  tax_amount?: number;
  homestead?: string;
  homestead_exemption?: string;

  // Additional fields
  legal_description?: string;
  subdivision?: string;
  lot_number?: string;
  block?: string;

  // Metadata
  import_date?: string;
  source?: string;
}

// ============================================
// NAV ASSESSMENT DATA (Special Assessments/CDD)
// ============================================

export interface NavAssessmentData {
  id?: string;
  parcel_id: string;
  county: string;
  year?: number;

  // Assessment details
  total_assessment: string | number;
  assessment_type?: string;
  district_name?: string;
  district_id?: string;

  // Values
  assessed_value?: number;
  market_value?: number;
  land_value?: number;
  building_value?: number;

  // Dates
  effective_date?: string;
  created_at?: string;
}

// ============================================
// SALES HISTORY DATA
// ============================================

export interface SalesHistoryRecord {
  id?: string;
  parcel_id: string;

  // Sale details
  sale_date: string;
  sale_price: number | string;
  sale_year: number;
  sale_month: number;

  // Quality indicators
  qualified_sale: boolean;
  quality_code?: string; // 'Q' for qualified
  sale_qualification?: string;

  // Document information
  clerk_no?: string;
  document_type?: string;
  or_book?: string; // Official Records book
  or_page?: string; // Official Records page
  book?: string;
  page?: string;

  // Parties
  grantor_name?: string;
  grantee_name?: string;
  grantor?: string;
  grantee?: string;

  // Transaction details
  sale_reason?: string;
  vi_code?: string; // Validity Indicator
  deed_type?: string;
  legal_description?: string;

  // Flags
  is_distressed?: boolean;
  is_bank_sale?: boolean;
  is_cash_sale?: boolean;
  is_arms_length?: boolean;

  // Metadata
  data_source: string;
  import_date?: string;
}

// ============================================
// SUNBIZ CORPORATE DATA (Business Entities)
// ============================================

export interface SunbizCorporateData {
  // Entity identification
  document_number: string; // Primary key
  entity_name: string;
  entity_type: string; // Corporation, LLC, etc.

  // Status
  status: string; // ACTIVE, INACTIVE, etc.
  filing_date: string;
  filing_type?: string;
  last_event_date?: string;
  event_description?: string;

  // Address information
  principal_address: string | null;
  principal_city?: string;
  principal_state?: string;
  principal_zip?: string;
  principal_country?: string;

  mailing_address?: string | null;
  mailing_city?: string;
  mailing_state?: string;
  mailing_zip?: string;
  mailing_country?: string;

  // Registered agent
  registered_agent: string | null;
  registered_agent_name?: string;
  registered_agent_address?: string;
  registered_agent_city?: string;
  registered_agent_state?: string;
  registered_agent_zip?: string;

  // Officers and directors
  officers?: SunbizOfficerData[];

  // Business details
  fei_number?: string; // Federal Employer ID
  naics_code?: string;
  business_type?: string;

  // Match information (for property matching)
  match_confidence?: number;
  confidence_score?: number;
  search_term_used?: string;
  match_type?: string;
  verified?: boolean;
  is_live_data?: boolean;

  // Metadata
  created_at?: string;
  updated_at?: string;
}

export interface SunbizOfficerData {
  id?: string;
  document_number: string; // Foreign key to entity

  // Officer information
  officer_name: string;
  officer_title: string; // President, Director, etc.
  officer_address?: string;
  officer_city?: string;
  officer_state?: string;
  officer_zip?: string;
  officer_country?: string;

  // Contact information
  email?: string;
  phone?: string;

  // Dates
  date_appointed?: string;
  date_resigned?: string;

  // Metadata
  created_at?: string;
  updated_at?: string;
}

// ============================================
// TPP DATA (Tangible Personal Property)
// ============================================

export interface TppData {
  id?: string;
  parcel_id: string;
  county: string;
  year?: number;

  // Business information
  business_name?: string;
  dba_name?: string; // Doing Business As
  owner_name?: string;

  // Property details
  total_value: number;
  assessed_value?: number;
  just_value?: number;

  // Assets
  furniture_fixtures?: number;
  machinery_equipment?: number;
  computer_equipment?: number;
  vehicles?: number;
  inventory?: number;
  signs?: number;
  other_assets?: number;

  // Classification
  business_type?: string;
  naics_code?: string;
  sic_code?: string;

  // Location
  business_address?: string;
  business_city?: string;
  business_zip?: string;

  // Metadata
  filing_date?: string;
  created_at?: string;
}

// ============================================
// TAX DEED / TAX CERTIFICATE DATA
// ============================================

export interface TaxDeedData {
  id: string;

  // Identifiers
  tax_deed_number: string;
  tax_certificate_number: string;
  parcel_id: string;
  parcel_number?: string;
  composite_key: string;

  // Property information
  legal_description: string;
  situs_address: string;
  homestead: boolean;
  is_homestead?: boolean;
  assessed_value: number;

  // Auction information
  auction_date: string | null;
  sale_date?: string;
  opening_bid?: number;
  winning_bid: number | null;
  minimum_bid?: number;

  // Winner/Buyer information
  winner_name: string | null;
  applicant: string | null;
  applicant_name?: string;
  buyer_name?: string;
  buyer_entity?: SunbizCorporateData;

  // Sunbiz matching
  sunbiz_matched: boolean;
  sunbiz_entities?: SunbizCorporateData[];
  sunbiz_entity_ids?: string[];

  // Links
  property_appraiser_link: string | null;

  // Status
  status?: 'pending' | 'sold' | 'cancelled';

  // Metadata
  county?: string;
  tax_year?: number;
  created_at?: string;
  updated_at?: string;
}

export interface TaxCertificateData {
  id?: string;

  // Identifiers
  certificate_number: string;
  parcel_id: string;
  county: string;

  // Tax information
  tax_year: number;
  face_value: number;
  interest_rate: number;

  // Dates
  sale_date: string;
  redemption_date: string | null;
  maturity_date?: string;

  // Buyer information
  buyer_name: string;
  buyer_address?: string;
  buyer_city?: string;
  buyer_state?: string;
  buyer_zip?: string;
  buyer_entity?: SunbizCorporateData;

  // Property information
  property_address: string | null;
  legal_description: string | null;

  // Status
  status: 'active' | 'redeemed' | 'foreclosed' | 'cancelled';

  // Amounts
  amount_due?: number;
  interest_earned?: number;
  penalties?: number;

  // Metadata
  created_at?: string;
  updated_at?: string;
}

// ============================================
// PERMIT DATA
// ============================================

export interface PermitData {
  id?: string;
  parcel_id: string;

  // Permit details
  permit_number: string;
  permit_type: string; // Building, Electrical, Plumbing, etc.
  permit_description?: string;

  // Status
  status: string; // Issued, Pending, Completed, etc.
  issue_date: string | null;
  completion_date?: string | null;
  expiration_date?: string | null;

  // Values
  estimated_cost: number | null;
  permit_fee?: number;

  // Location
  address: string | null;
  city?: string;
  zip?: string;

  // Contractor
  contractor_name?: string;
  contractor_license?: string;

  // Work details
  work_description?: string;
  square_footage?: number;
  stories?: number;

  // Metadata
  county?: string;
  created_at?: string;
  updated_at?: string;
}

// ============================================
// AGGREGATE PROPERTY DATA (Used by usePropertyData hook)
// ============================================

export interface PropertyData {
  // Core property data from Property Appraiser
  bcpaData: FloridaParcelData | null;

  // Sales history
  sdfData: SalesHistoryRecord[];

  // Special assessments (CDD, etc.)
  navData: NavAssessmentData[];

  // Tangible personal property
  tppData: TppData[];

  // Business entities
  sunbizData: SunbizCorporateData[];

  // Last qualified sale
  lastSale: SalesHistoryRecord | null;

  // Calculated fields
  totalNavAssessment: number;
  isInCDD: boolean;
  investmentScore: number;
  opportunities: string[];
  riskFactors: string[];

  // Data quality indicators
  dataQuality: {
    bcpa: boolean;
    sdf: boolean;
    nav: boolean;
    tpp: boolean;
    sunbiz: boolean;
  };
}

// ============================================
// SEARCH & FILTERING TYPES
// ============================================

export interface PropertySearchFilters {
  // Text search
  search?: string;
  address?: string;
  owner?: string;
  parcel_id?: string;

  // Location filters
  county?: string;
  city?: string;
  zip?: string;

  // Property type filters
  property_use?: string;
  property_use_code?: string;
  property_type?: 'residential' | 'commercial' | 'industrial' | 'vacant' | 'agricultural';

  // Value filters
  min_value?: number;
  max_value?: number;
  min_land_value?: number;
  max_land_value?: number;
  min_building_value?: number;
  max_building_value?: number;

  // Size filters
  min_sqft?: number;
  max_sqft?: number;
  min_land_sqft?: number;
  max_land_sqft?: number;

  // Characteristics
  min_bedrooms?: number;
  max_bedrooms?: number;
  min_bathrooms?: number;
  max_bathrooms?: number;
  min_year_built?: number;
  max_year_built?: number;

  // Special filters
  has_homestead?: boolean;
  in_cdd?: boolean;
  has_recent_sale?: boolean;
  has_sunbiz_entity?: boolean;
  is_distressed?: boolean;

  // Pagination
  page?: number;
  limit?: number;
  offset?: number;

  // Sorting
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PropertySearchResult {
  properties: FloridaParcelData[];
  total_count: number;
  page: number;
  limit: number;
  total_pages: number;
  has_more: boolean;
}

// ============================================
// INVESTMENT ANALYSIS TYPES
// ============================================

export interface InvestmentAnalysis {
  property: FloridaParcelData;

  // Valuation
  current_value: number;
  purchase_price: number | null;
  estimated_value: number;
  value_appreciation: number;

  // Returns
  investment_score: number; // 0-100
  roi_potential: number; // Percentage
  cash_on_cash_return: number;
  cap_rate: number;

  // Opportunities
  opportunities: string[];
  strengths: string[];

  // Risks
  riskFactors: string[];
  concerns: string[];

  // Market data
  comparable_sales: SalesHistoryRecord[];
  market_trends: {
    average_price: number;
    median_price: number;
    price_trend: 'up' | 'down' | 'stable';
    sales_velocity: number;
  };

  // Special assessments
  cdd_assessment: number;
  special_assessments: NavAssessmentData[];

  // Owner insights
  owner_entities: SunbizCorporateData[];
  is_corporate_owner: boolean;
  is_institutional_owner: boolean;
}

// ============================================
// UTILITY TYPES
// ============================================

export interface DataQuality {
  source: string;
  last_updated: string;
  completeness: number; // 0-100
  accuracy_score: number; // 0-100
  has_errors: boolean;
  error_messages: string[];
}

export interface GeoLocation {
  latitude: number;
  longitude: number;
  accuracy?: number;
  geocoded_address?: string;
  geocoding_method?: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
  offset: number;
}

export interface SortParams {
  sort_by: string;
  sort_order: 'asc' | 'desc';
}

// ============================================
// API RESPONSE TYPES
// ============================================

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
  metadata?: {
    timestamp: string;
    request_id?: string;
    duration_ms?: number;
  };
}

export interface PaginatedApiResponse<T> extends ApiResponse<T> {
  pagination: {
    page: number;
    limit: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}
