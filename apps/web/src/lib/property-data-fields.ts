// Comprehensive Property Data Fields from Florida DOR, Broward County, and Sunbiz
// Based on NAL (Real Property), SDF (Sales Data File), and NAP (Non-Ad Valorem) data structures

export interface PropertyDataFields {
  // === PARCEL IDENTIFICATION ===
  countyNo: string // County Number (06 = Broward)
  parcelId: string // Unique Parcel ID
  parcelIdNoSpace: string // Parcel ID without spaces
  
  // === OWNER INFORMATION ===
  ownerName1: string // Primary owner name
  ownerName2?: string // Secondary owner name
  ownerMailingAddress1: string // Mailing address line 1
  ownerMailingAddress2?: string // Mailing address line 2
  ownerMailingAddress3?: string // Mailing address line 3
  ownerCity: string
  ownerState: string
  ownerZip: string
  ownerZip4?: string
  ownerCountry?: string
  
  // === PROPERTY LOCATION ===
  situsAddress1: string // Physical address line 1
  situsAddress2?: string // Physical address line 2
  situsAddress3?: string // Physical address line 3
  situsCity: string
  situsState: string
  situsZip: string
  situsZip4?: string
  
  // === LEGAL DESCRIPTION ===
  legalDescription1: string
  legalDescription2?: string
  legalDescription3?: string
  legalDescription4?: string
  subdivision: string
  subDivisionNumber: string
  block: string
  lot: string
  section: string
  township: string
  range: string
  
  // === PROPERTY CLASSIFICATION ===
  dorCode: string // DOR Use Code (00-99)
  dorCodeDescription: string
  appraiserParcelType: string
  propertyUseCode: string
  propertyUseDescription: string
  neighborhoodCode: string
  neighborhoodName: string
  zoningCode: string
  zoningDescription: string
  futureUseCode?: string
  futureUseDescription?: string
  
  // === VALUATIONS ===
  justValue: number // Market value
  assessedValue: number // Assessed value
  taxableValue: number // Taxable value
  landValue: number // Land only value
  buildingValue: number // Building/improvement value
  extraFeatureValue: number // Extra features value
  totalJustValue: number
  totalAssessedValue: number
  totalTaxableValue: number
  previousYearJustValue?: number
  previousYearAssessedValue?: number
  previousYearTaxableValue?: number
  
  // === EXEMPTIONS ===
  homesteadExemption: boolean
  homesteadExemptionValue: number
  seniorExemption: boolean
  veteranExemption: boolean
  widowExemption: boolean
  disabilityExemption: boolean
  agriculturalClassification: boolean
  otherExemptions: string[]
  totalExemptionValue: number
  
  // === BUILDING INFORMATION ===
  numberOfBuildings: number
  totalBuildingArea: number // Total square feet
  totalLivingArea: number // Heated/cooled square feet
  adjustedSquareFeet: number
  grossSquareFeet: number
  effectiveYearBuilt: number // Effective year (adjusted for renovations)
  actualYearBuilt: number // Actual year built
  numberOfStories: number
  structureType: string
  constructionType: string
  foundation: string
  roofStructure: string
  roofCover: string
  exteriorWall: string
  interiorWall: string
  heatingType: string
  coolingType: string
  fireplaces: number
  
  // === RESIDENTIAL SPECIFIC ===
  numberOfResidentialUnits: number
  bedrooms: number
  bathrooms: number
  halfBathrooms: number
  poolType?: string // Pool, Spa, etc.
  poolArea?: number
  garageType?: string
  garageCapacity?: number
  
  // === COMMERCIAL/INDUSTRIAL SPECIFIC ===
  numberOfCommercialUnits?: number
  rentableArea?: number
  commonArea?: number
  grossLeasableArea?: number
  netRentableArea?: number
  parkingSpaces?: number
  parkingType?: string // Surface, Garage, etc.
  loadingDocks?: number
  clearHeight?: number // For warehouses
  officeSpace?: number
  warehouseSpace?: number
  retailSpace?: number
  manufacturingSpace?: number
  
  // === AGRICULTURAL SPECIFIC ===
  agriculturalAcres?: number
  cropType?: string
  irrigationType?: string
  pastureAcres?: number
  woodlandAcres?: number
  wastelandAcres?: number
  
  // === LAND CHARACTERISTICS ===
  totalLandArea: number // Square feet
  totalAcreage: number // Acres
  frontage: number // Street frontage in feet
  depth: number
  landSquareFeet: number
  landUseCode: string
  utilityWater: boolean
  utilitySewer: boolean
  utilityElectric: boolean
  utilityGas: boolean
  utilityStreetLights: boolean
  streetPaved: boolean
  sidewalk: boolean
  
  // === SALES INFORMATION (from SDF) ===
  lastSaleDate?: Date
  lastSalePrice?: number
  lastSaleQualificationCode?: string // Arms-length, etc.
  lastSaleVacantOrImproved?: string
  deedType?: string
  grantor?: string // Seller
  grantee?: string // Buyer
  officialRecordBook?: string
  officialRecordPage?: string
  instrumentNumber?: string
  priorSaleDate?: Date
  priorSalePrice?: number
  priorSaleQualificationCode?: string
  
  // === TAX INFORMATION ===
  taxingDistrictCode: string
  taxingDistrictName: string
  millageRate: number
  nonAdValoremAssessments: number
  totalTaxes: number
  taxBillYear: number
  
  // === GIS/MAPPING ===
  latitude?: number
  longitude?: number
  gisPin?: string
  censusBlock?: string
  censusTract?: string
  floodZone?: string
  floodZoneDate?: Date
  
  // === SPECIAL ASSESSMENTS (NAP) ===
  specialAssessments?: {
    code: string
    description: string
    amount: number
    frequency: string
  }[]
  
  // === OWNERSHIP HISTORY ===
  ownershipHistory?: {
    date: Date
    owner: string
    salePrice: number
    deedType: string
    instrumentNumber: string
  }[]
  
  // === PERMIT HISTORY ===
  permits?: {
    permitNumber: string
    permitType: string
    issueDate: Date
    completionDate?: Date
    value: number
    description: string
  }[]
  
  // === CORPORATE OWNERSHIP (from Sunbiz) ===
  corporateOwner?: {
    entityName: string
    entityType: string // LLC, Corp, etc.
    sunbizNumber: string
    filingDate: Date
    status: string
    principalAddress: string
    registeredAgent: string
    registeredAgentAddress: string
    officers?: {
      name: string
      title: string
      address: string
    }[]
    managers?: {
      name: string
      address: string
    }[]
    members?: {
      name: string
      address: string
    }[]
  }
  
  // === FLAGS & INDICATORS ===
  isHomestead: boolean
  isCommercial: boolean
  isVacant: boolean
  isAgricultural: boolean
  isWaterfront: boolean
  isCornerLot: boolean
  isHistoric: boolean
  isPendingSale: boolean
  isForeclosure: boolean
  isREO: boolean // Real Estate Owned by lender
  
  // === DATES ===
  certifiedDate: Date // County certification date
  lastUpdated: Date
  dataYear: string // e.g., "2024F" for 2024 Final
  
  // === QUALITY INDICATORS ===
  confidenceScore?: number // Data quality score
  verificationStatus?: string
  dataSource: string // NAL, SDF, NAP, etc.
  dataVersion: string // Preliminary, Final, Post-VAB
}

// Mini Profile Fields (for cards/list view)
export interface PropertyMiniProfile {
  parcelId: string
  title: string // Generated from address or owner
  address: string
  city: string
  state: string
  zip: string
  price: number // Just value or asking price
  propertyType: string
  useCode: string
  useDescription: string
  
  // Key metrics based on property type
  // Residential
  bedrooms?: number
  bathrooms?: number
  livingArea?: number
  yearBuilt?: number
  
  // Commercial
  buildingArea?: number
  rentableArea?: number
  occupancyRate?: number
  capRate?: number
  noi?: number // Net Operating Income
  
  // Land
  acres?: number
  zoning?: string
  
  // Common
  landValue: number
  buildingValue: number
  taxableValue: number
  lastSaleDate?: Date
  lastSalePrice?: number
  
  // Visual
  imageUrl?: string
  status: 'active' | 'pending' | 'sold' | 'off-market'
  featured?: boolean
  
  // Meta
  lastUpdated: Date
  dataSource: string
}

// Main Profile Sections
export interface PropertyMainProfile extends PropertyDataFields {
  // Additional computed fields
  pricePerSqFt?: number
  pricePerAcre?: number
  taxRate?: number
  monthlyTaxes?: number
  appreciationRate?: number
  netOperatingIncome?: number
  capRate?: number
  comparableProperties?: PropertyMiniProfile[]
  marketTrends?: {
    date: Date
    medianPrice: number
    inventory: number
    daysOnMarket: number
  }[]
  
  // Documents
  documents?: {
    type: string
    name: string
    date: Date
    url: string
  }[]
  
  // Images
  images?: {
    url: string
    caption?: string
    type: 'exterior' | 'interior' | 'aerial' | 'map' | 'floorplan'
  }[]
}

// Field visibility configuration per property type
export const FIELD_VISIBILITY_CONFIG = {
  RESIDENTIAL: {
    miniProfile: ['bedrooms', 'bathrooms', 'livingArea', 'yearBuilt', 'price', 'taxableValue'],
    mainProfile: {
      overview: ['ownerName1', 'situsAddress1', 'justValue', 'taxableValue', 'yearBuilt', 'livingArea'],
      details: ['bedrooms', 'bathrooms', 'stories', 'poolType', 'garageCapacity', 'constructionType'],
      land: ['totalAcreage', 'frontage', 'depth', 'zoningCode'],
      valuation: ['justValue', 'assessedValue', 'taxableValue', 'landValue', 'buildingValue'],
      tax: ['homesteadExemption', 'totalExemptionValue', 'millageRate', 'totalTaxes'],
      sales: ['lastSaleDate', 'lastSalePrice', 'priorSaleDate', 'priorSalePrice'],
      ownership: ['ownerName1', 'ownerMailingAddress1', 'ownerCity', 'ownerState']
    }
  },
  COMMERCIAL: {
    miniProfile: ['buildingArea', 'rentableArea', 'yearBuilt', 'price', 'capRate', 'noi'],
    mainProfile: {
      overview: ['ownerName1', 'situsAddress1', 'justValue', 'rentableArea', 'capRate', 'noi'],
      details: ['buildingArea', 'grossLeasableArea', 'parkingSpaces', 'loadingDocks', 'clearHeight'],
      tenancy: ['numberOfCommercialUnits', 'occupancyRate', 'rentableArea', 'commonArea'],
      land: ['totalAcreage', 'frontage', 'zoningCode', 'futureUseCode'],
      valuation: ['justValue', 'assessedValue', 'taxableValue', 'landValue', 'buildingValue'],
      income: ['noi', 'capRate', 'monthlyRent', 'annualRent'],
      sales: ['lastSaleDate', 'lastSalePrice', 'pricePerSqFt'],
      ownership: ['corporateOwner', 'ownerName1', 'ownerMailingAddress1']
    }
  },
  INDUSTRIAL: {
    miniProfile: ['buildingArea', 'clearHeight', 'loadingDocks', 'price', 'yearBuilt'],
    mainProfile: {
      overview: ['situsAddress1', 'buildingArea', 'clearHeight', 'loadingDocks', 'justValue'],
      specs: ['warehouseSpace', 'officeSpace', 'manufacturingSpace', 'clearHeight', 'loadingDocks'],
      infrastructure: ['utilityElectric', 'utilitySewer', 'utilityWater', 'streetPaved'],
      land: ['totalAcreage', 'landSquareFeet', 'zoningCode'],
      valuation: ['justValue', 'assessedValue', 'taxableValue', 'pricePerSqFt']
    }
  },
  AGRICULTURAL: {
    miniProfile: ['acres', 'cropType', 'irrigationType', 'price', 'pricePerAcre'],
    mainProfile: {
      overview: ['situsAddress1', 'totalAcreage', 'cropType', 'justValue'],
      land: ['agriculturalAcres', 'pastureAcres', 'woodlandAcres', 'wastelandAcres'],
      production: ['cropType', 'irrigationType', 'agriculturalClassification'],
      improvements: ['numberOfBuildings', 'buildingArea', 'actualYearBuilt'],
      valuation: ['justValue', 'landValue', 'buildingValue', 'pricePerAcre']
    }
  },
  VACANT_LAND: {
    miniProfile: ['acres', 'zoning', 'futureUse', 'price', 'pricePerAcre'],
    mainProfile: {
      overview: ['situsAddress1', 'totalAcreage', 'zoningCode', 'justValue'],
      land: ['totalAcreage', 'landSquareFeet', 'frontage', 'depth'],
      development: ['zoningCode', 'futureUseCode', 'floodZone'],
      utilities: ['utilityWater', 'utilitySewer', 'utilityElectric', 'utilityGas'],
      valuation: ['justValue', 'landValue', 'pricePerAcre', 'pricePerSqFt']
    }
  }
}