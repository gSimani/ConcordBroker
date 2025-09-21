// API Response Types

export interface AuthResponse {
  success: boolean;
  access_token?: string;
  refresh_token?: string;
  user_id?: string;
  email?: string;
  message?: string;
  demo_mode?: boolean;
  token?: string;
}

export interface User {
  id: string;
  email: string;
  full_name?: string;
  company?: string;
  metadata?: Record<string, any>;
}

export interface PropertySearchParams {
  search?: string;
  county?: string;
  city?: string;
  property_use?: string;
  min_value?: number;
  max_value?: number;
  min_sqft?: number;
  max_sqft?: number;
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PropertyData {
  parcel_id: string;
  county: string;
  phy_addr1?: string;
  phy_addr2?: string;
  phy_city?: string;
  phy_zipcode?: string;
  owner_name?: string;
  owner_addr1?: string;
  owner_addr2?: string;
  owner_city?: string;
  owner_state?: string;
  owner_zipcode?: string;
  just_value?: number;
  land_value?: number;
  building_value?: number;
  assessed_value?: number;
  market_value?: number;
  taxable_value?: number;
  land_sqft?: number;
  building_sqft?: number;
  year_built?: number;
  property_use?: string;
  property_use_code?: string;
  bedrooms?: number;
  bathrooms?: number;
  half_baths?: number;
  homestead?: string;
  tax_amount?: number;
  sale_date?: string;
  sale_price?: number;
  year?: number;
  // Navigation Assessment data
  navData?: NavAssessmentData;
  // Total navigation assessment
  totalNavAssessment?: number;
  // CDD indicator
  isInCDD?: boolean;
  // BCPA data for Broward County
  bcpaData?: BcpaData;
  // Sales history
  sdfData?: PropertySalesData;
  // TPP data
  tppData?: any;
  // Sunbiz data
  sunbizData?: any;
  // Last sale information
  lastSale?: any;
  // Additional calculated fields
  calculated_value?: number;
  investment_score?: number;
  roi_potential?: number;
  market_appreciation?: number;
}

export interface NavAssessmentData {
  parcel_id: string;
  county: string;
  assessed_value?: number;
  market_value?: number;
  land_value?: number;
  building_value?: number;
  year?: number;
}

export interface BcpaData {
  parcel_id: string;
  market_value?: number;
  assessed_value?: number;
  taxable_value?: number;
  land_value?: number;
  building_value: number;
  tax_amount?: number;
  homestead_exemption?: string;
  owner_name?: string;
}

export interface PropertySalesData {
  length?: number;
  sales?: SaleRecord[];
}

export interface SaleRecord {
  sale_date: string;
  sale_price: number;
  sale_year?: number;
  deed_type?: string;
  grantor?: string;
  grantee?: string;
  legal_description?: string;
}

export interface EntityMatch {
  entity_name: string;
  document_number: string;
  entity_doc_number?: string;
  entity_type: string;
  status: string;
  filing_date: string;
  principal_address: string;
  registered_agent: string;
  match_confidence: number;
  confidence_score?: number;
  search_term_used: string;
  match_type?: string;
  verified?: boolean;
}

export interface OfficerProperty {
  officer_name: string;
  company_name: string;
  parcel_id: string;
  phy_addr1: string;
  phy_city: string;
  market_value?: number;
  just_value?: number;
  property_use: string;
  year_built?: number;
  owner_name: string;
}

export interface TaxDeedProperty {
  id: string;
  tax_deed_number: string;
  parcel_number: string;
  composite_key: string;
  tax_certificate_number: string;
  legal_description: string;
  situs_address: string;
  homestead?: boolean;
  is_homestead?: boolean;
  assessed_value: number;
  auction_date?: string;
  winner_name?: string;
  winning_bid?: number;
  applicant?: string;
  applicant_name?: string;
  sunbiz_matched?: boolean;
  sunbiz_entities?: any[];
  sunbiz_entity_ids?: string[];
  property_appraiser_link?: string;
}

export interface TaxCertificate {
  certificate_number: string;
  parcel_id: string;
  tax_year: number;
  face_value: number;
  interest_rate: number;
  sale_date: string;
  redemption_date?: string;
  buyer_name: string;
  property_address?: string;
  legal_description?: string;
  county: string;
  status: 'active' | 'redeemed' | 'foreclosed';
  buyer_entity?: {
    entity_name: string;
    document_number: string;
    entity_type: string;
    status: string;
    filing_date: string;
    filing_type?: string;
    principal_address: string;
    registered_agent: string;
    officers?: any;
    match_confidence?: number;
    search_term_used?: string;
    is_live_data?: boolean;
  };
}

// Speech Recognition Types
export interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
}

export interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
}

export interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

// Global Window Types
declare global {
  interface Window {
    SpeechRecognition?: typeof SpeechRecognition;
    webkitSpeechRecognition?: typeof SpeechRecognition;
    selectProperty?: (parcelId: string) => void;
  }

  interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start(): void;
    stop(): void;
    abort(): void;
    onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
    onend: ((this: SpeechRecognition, ev: Event) => any) | null;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
    onerror: ((this: SpeechRecognition, ev: any) => any) | null;
  }

  interface SpeechRecognitionConstructor {
    new (): SpeechRecognition;
  }
}

// Animation Types for Framer Motion
export interface MotionVariants {
  expanded: {
    width: number;
    transition: {
      type: 'spring';
      damping: number;
      stiffness: number;
    };
  };
  collapsed: {
    width: number;
    transition: {
      type: 'spring';
      damping: number;
      stiffness: number;
    };
  };
}