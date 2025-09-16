# Ultimate Database Architecture for ConcordBroker

## 🏗️ Complete Data Architecture

### Core Data Sources Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    MASTER PROPERTY VIEW                      │
├─────────────────────────────────────────────────────────────┤
│  Combines all data sources into single authoritative view    │
└─────────────────────────────────────────────────────────────┘
                              ▲
        ┌─────────────────────┴─────────────────────┐
        │                                           │
┌───────▼────────┐  ┌────────────────┐  ┌─────────▼────────┐
│ PROPERTY DATA  │  │  OWNERSHIP     │  │ CORPORATE DATA   │
├────────────────┤  ├────────────────┤  ├──────────────────┤
│ • NAL (Values) │  │ • NAP (Owners) │  │ • Sunbiz Corps   │
│ • SDF (Sales)  │  │ • Title Chain  │  │ • Officers       │
│ • NAV (Assess) │  │ • Liens        │  │ • Agents         │
│ • TPP (Tangbl) │  │ • Mortgages    │  │ • Entity Links   │
└────────────────┘  └────────────────┘  └──────────────────┘
```

## 📊 Master Tables Structure

### 1. **properties_master** (Unified Property View)
```sql
CREATE TABLE properties_master (
    -- Primary Identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    folio_number VARCHAR(30),
    county_code VARCHAR(5),
    county_name VARCHAR(50),
    
    -- Location Data
    property_address VARCHAR(255),
    property_city VARCHAR(100),
    property_state VARCHAR(2) DEFAULT 'FL',
    property_zip VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Owner Information (Latest from NAP)
    owner_name VARCHAR(255),
    owner_type VARCHAR(50), -- Individual, LLC, Corp, Trust
    owner_address VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    
    -- Valuation (Latest from NAL)
    just_value DECIMAL(12,2),
    assessed_value DECIMAL(12,2),
    taxable_value DECIMAL(12,2),
    land_value DECIMAL(12,2),
    building_value DECIMAL(12,2),
    
    -- Property Characteristics
    property_use_code VARCHAR(20),
    property_type VARCHAR(50), -- Residential, Commercial, etc
    total_sq_ft INTEGER,
    living_area INTEGER,
    lot_size DECIMAL(10,2),
    year_built INTEGER,
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    pool BOOLEAN DEFAULT FALSE,
    
    -- Financial Metrics
    tax_amount DECIMAL(10,2),
    nav_total DECIMAL(10,2),
    homestead_exemption BOOLEAN DEFAULT FALSE,
    
    -- Investment Metrics
    cap_rate DECIMAL(5,2),
    price_per_sqft DECIMAL(10,2),
    rental_estimate DECIMAL(10,2),
    investment_score INTEGER,
    
    -- Sales Information (Latest)
    last_sale_date DATE,
    last_sale_price DECIMAL(12,2),
    days_on_market INTEGER,
    
    -- Corporate Connections
    has_corporate_owner BOOLEAN DEFAULT FALSE,
    sunbiz_entity_id VARCHAR(50),
    
    -- Metadata
    data_quality_score INTEGER, -- 0-100
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. **property_sales_enriched** (Enhanced Sales History)
```sql
CREATE TABLE property_sales_enriched (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_id VARCHAR(50) REFERENCES properties_master(parcel_id),
    
    -- Transaction Details
    sale_date DATE NOT NULL,
    sale_price DECIMAL(12,2),
    price_per_sqft DECIMAL(10,2),
    
    -- Parties
    seller_name VARCHAR(255),
    seller_type VARCHAR(50),
    buyer_name VARCHAR(255),
    buyer_type VARCHAR(50),
    
    -- Sale Characteristics
    sale_type VARCHAR(50),
    deed_type VARCHAR(50),
    qualified_sale BOOLEAN,
    arms_length BOOLEAN,
    foreclosure BOOLEAN,
    
    -- Financing
    mortgage_amount DECIMAL(12,2),
    cash_sale BOOLEAN,
    lender_name VARCHAR(255),
    
    -- Market Context
    market_value_at_sale DECIMAL(12,2),
    sale_to_value_ratio DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3. **property_corporate_links** (Property-Business Connections)
```sql
CREATE TABLE property_corporate_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_id VARCHAR(50) REFERENCES properties_master(parcel_id),
    sunbiz_entity_id VARCHAR(50),
    
    -- Relationship Details
    relationship_type VARCHAR(50), -- Owner, Lessee, Manager
    ownership_percentage DECIMAL(5,2),
    
    -- Corporate Details (Denormalized for speed)
    entity_name VARCHAR(255),
    entity_type VARCHAR(50),
    entity_status VARCHAR(50),
    
    -- Key People
    registered_agent VARCHAR(255),
    principal_address VARCHAR(255),
    
    -- Dates
    relationship_start DATE,
    relationship_end DATE,
    is_current BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4. **investment_opportunities** (AI-Generated Insights)
```sql
CREATE TABLE investment_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_id VARCHAR(50) REFERENCES properties_master(parcel_id),
    
    -- Opportunity Details
    opportunity_type VARCHAR(50), -- Undervalued, Flip, Rental, Development
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    potential_roi DECIMAL(5,2),
    
    -- Analysis
    reasoning TEXT,
    risk_factors JSONB,
    comparable_properties JSONB,
    
    -- Recommendations
    recommended_action VARCHAR(100),
    estimated_investment DECIMAL(12,2),
    estimated_return DECIMAL(12,2),
    time_horizon_months INTEGER,
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, expired, realized
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);
```

## 🔄 Data Flow Architecture

### Real-Time Data Pipeline
```yaml
1. Data Ingestion Layer:
   - Florida Revenue Downloads (NAL, NAP, SDF, NAV)
   - Sunbiz SFTP Downloads
   - Public Records APIs
   - MLS Feeds (when available)

2. Processing Layer:
   - Data Validation & Cleaning
   - Entity Resolution (matching owners to businesses)
   - Geocoding & Address Standardization
   - Value Calculations & Metrics

3. Storage Layer:
   - Raw Data Tables (as downloaded)
   - Processed Tables (cleaned & standardized)
   - Master Views (unified data)
   - Cache Tables (for performance)

4. API Layer:
   - REST Endpoints for Website
   - GraphQL for Complex Queries
   - WebSocket for Real-Time Updates
   - Webhooks for External Integrations

5. Application Layer:
   - Website (React/TypeScript)
   - Mobile Apps
   - Admin Dashboard
   - Analytics Platform
```

## 🚀 Optimized Website Integration

### API Endpoints Structure
```typescript
// Main Property Endpoint
GET /api/property/:parcelId
Returns: {
  property: MasterPropertyData,
  sales: SalesHistory[],
  assessments: AssessmentHistory[],
  navDetails: NavAssessment[],
  corporateLinks: CorporateConnection[],
  opportunities: InvestmentOpportunity[],
  comparables: ComparableProperty[]
}

// Search Endpoint
POST /api/properties/search
Body: {
  filters: {
    priceRange: [min, max],
    location: { city, zip, radius },
    propertyType: string[],
    ownerType: string[],
    hasOpportunity: boolean
  },
  sort: { field, direction },
  pagination: { page, limit }
}

// Analytics Endpoint
GET /api/analytics/market/:county
Returns: {
  medianPrice: number,
  priceChange: number,
  inventory: number,
  daysOnMarket: number,
  trends: TrendData[]
}
```

## 📈 Performance Optimization

### Materialized Views for Speed
```sql
-- Fast Property Search View
CREATE MATERIALIZED VIEW property_search_view AS
SELECT 
    p.parcel_id,
    p.property_address,
    p.owner_name,
    p.taxable_value,
    p.last_sale_price,
    p.investment_score,
    COUNT(o.id) as opportunity_count,
    MAX(o.potential_roi) as max_roi
FROM properties_master p
LEFT JOIN investment_opportunities o ON p.parcel_id = o.parcel_id
GROUP BY p.parcel_id;

-- Refresh every hour
CREATE OR REPLACE FUNCTION refresh_search_view()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY property_search_view;
END;
$$ LANGUAGE plpgsql;
```

### Indexes for Common Queries
```sql
-- Location-based searches
CREATE INDEX idx_property_location ON properties_master 
    USING GIST (ll_to_earth(latitude, longitude));

-- Owner searches
CREATE INDEX idx_owner_name_trgm ON properties_master 
    USING GIN (owner_name gin_trgm_ops);

-- Value range searches
CREATE INDEX idx_taxable_value ON properties_master(taxable_value);
CREATE INDEX idx_sale_price ON property_sales_enriched(sale_price);

-- Corporate connections
CREATE INDEX idx_sunbiz_entity ON property_corporate_links(sunbiz_entity_id);
```

## 🔐 Row Level Security

```sql
-- Public read access
ALTER TABLE properties_master ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access" ON properties_master
    FOR SELECT USING (true);

-- Authenticated write access
CREATE POLICY "Authenticated write" ON properties_master
    FOR ALL USING (auth.role() = 'authenticated');

-- Premium user access to opportunities
CREATE POLICY "Premium opportunities" ON investment_opportunities
    FOR SELECT USING (
        auth.jwt() ->> 'subscription_level' IN ('premium', 'enterprise')
        OR parcel_id IN (
            SELECT parcel_id FROM user_watchlist 
            WHERE user_id = auth.uid()
        )
    );
```

## 🎯 Website Hook Integration

### React Hook Update
```typescript
// usePropertyData.ts
import { useQuery } from '@tanstack/react-query'
import { supabase } from '@/lib/supabase'

export const usePropertyData = (parcelId: string) => {
  return useQuery({
    queryKey: ['property', parcelId],
    queryFn: async () => {
      // Get master property data
      const { data: property } = await supabase
        .from('properties_master')
        .select('*')
        .eq('parcel_id', parcelId)
        .single()
      
      // Get related data in parallel
      const [sales, nav, corporate, opportunities] = await Promise.all([
        supabase.from('property_sales_enriched')
          .select('*')
          .eq('parcel_id', parcelId)
          .order('sale_date', { ascending: false }),
        
        supabase.from('nav_details')
          .select('*')
          .eq('parcel_id', parcelId),
        
        supabase.from('property_corporate_links')
          .select('*')
          .eq('parcel_id', parcelId),
        
        supabase.from('investment_opportunities')
          .select('*')
          .eq('parcel_id', parcelId)
          .eq('status', 'active')
      ])
      
      return {
        property: property.data,
        salesHistory: sales.data,
        navAssessments: nav.data,
        corporateLinks: corporate.data,
        opportunities: opportunities.data
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
```

## 📋 Data Quality Monitoring

```sql
-- Monitor data completeness
CREATE OR REPLACE FUNCTION check_data_quality()
RETURNS TABLE (
    table_name TEXT,
    total_records BIGINT,
    records_with_nulls BIGINT,
    completeness_percentage NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'properties_master'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE owner_name IS NULL)::BIGINT,
        ROUND((COUNT(*) FILTER (WHERE owner_name IS NOT NULL)::NUMERIC / COUNT(*)) * 100, 2)
    FROM properties_master
    
    UNION ALL
    
    SELECT 
        'property_sales_enriched'::TEXT,
        COUNT(*)::BIGINT,
        COUNT(*) FILTER (WHERE sale_price IS NULL)::BIGINT,
        ROUND((COUNT(*) FILTER (WHERE sale_price IS NOT NULL)::NUMERIC / COUNT(*)) * 100, 2)
    FROM property_sales_enriched;
END;
$$ LANGUAGE plpgsql;
```

## 🔄 Sync Schedule

```yaml
Daily Updates (Midnight):
  - New sales from SDF files
  - Sunbiz entity changes
  - Market value adjustments

Weekly Updates (Sunday):
  - Full NAL assessment refresh
  - NAV assessment updates
  - Investment opportunity recalculation

Monthly Updates (1st):
  - Complete data reconciliation
  - Historical data archival
  - Performance optimization

Real-Time:
  - User watchlist properties
  - High-value transactions (>$1M)
  - Corporate ownership changes
```

This architecture ensures all data flows seamlessly from collection through to the website, with optimal performance and real-time updates where needed.