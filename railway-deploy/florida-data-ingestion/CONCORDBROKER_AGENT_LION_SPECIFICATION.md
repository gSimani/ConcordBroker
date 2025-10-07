# ConcordBroker Agent Lion - Complete Specification

**Purpose**: AI-powered Florida property intelligence platform with corporate ownership analysis and investment assessment

**Core Mission**:
1. Search and aggregate Florida property data (9.7M+ parcels)
2. Match property owners to Sunbiz corporate entities
3. Handle multi-corporation ownership structures
4. Provide AI-powered investment analysis via Agent Lion
5. Explain valuations, formulas, financials, and investment strategies

---

## System Architecture for ConcordBroker

### Data Sources (Already Integrated)

**Property Data**:
- ✅ `florida_parcels` (9.1M records) - Property details, owners, values
- ✅ `property_sales_history` (96K records) - Sale transactions
- ✅ Tax certificates, exemptions, assessments

**Corporate Data**:
- ✅ `florida_entities` (15M records) - All Sunbiz entities
- ✅ `sunbiz_corporate` (2M records) - Corporate filings
- ⚠️ Need: Owner → Corporation matching table

**Missing Links**:
- Property owner name → Sunbiz entity name matching
- Multi-corporation ownership tracking
- Principal officer → Multiple entities mapping

---

## Agent Lion for ConcordBroker

### Primary Role: Investment Intelligence Assistant

**Agent Lion Capabilities**:

1. **Property Analysis**
   - "Explain why this property is valued at $450K when similar properties sell for $380K"
   - "What's the tax assessment methodology for this commercial property?"
   - "Calculate NOI (Net Operating Income) based on rental comps"

2. **Corporate Ownership Intelligence**
   - "This owner has 47 LLCs. Show me all properties across all entities"
   - "Identify shell corporations vs. active operating companies"
   - "Find common principals across multiple entities"

3. **Investment Strategy**
   - "Is this a good investment given current cap rates?"
   - "Calculate cash-on-cash return with 25% down at 7% interest"
   - "Compare this to similar properties in the same neighborhood"

4. **Valuation Formulas**
   - "Explain the formula used to calculate just value vs. assessed value"
   - "What exemptions is this property eligible for?"
   - "How does the county calculate building value vs. land value?"

5. **Financial Proforma**
   - "Generate a 10-year financial projection for this property"
   - "What's the break-even occupancy rate?"
   - "Calculate IRR (Internal Rate of Return) with different exit scenarios"

---

## RAG System Configuration for ConcordBroker

### Documents to Embed (Property Investment Focus)

**DOR Documentation** (Tax Assessment Rules):
- 2025 NAL/SDF/NAP Users Guide - Field definitions
- DOR Property Tax Overview - Assessment methodologies
- Florida Statute 193 - Property tax valuation
- Florida Statute 197 - Tax deed sales

**Real Estate Investment**:
- Real Estate Financial Modeling book (PDF)
- Cap rate methodology guides
- NOI calculation standards
- Commercial real estate valuation methods

**Florida Corporate Law**:
- Florida LLC Act (Chapter 605)
- Corporate filing requirements
- Sunbiz entity types and structures
- Beneficial ownership rules

**ConcordBroker Internal**:
- Property scoring algorithms
- Investment criteria templates
- Market analysis methodologies
- Due diligence checklists

### RAG Schema for ConcordBroker

```sql
-- Documentation embeddings (pgvector)
CREATE TABLE concordbroker_docs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    category text NOT NULL, -- 'tax_law', 'investment', 'corporate', 'internal'
    document_name text NOT NULL,
    section_title text,
    content text NOT NULL,
    embedding vector(1536),
    metadata jsonb, -- {page, formula_name, statute_section, etc}
    created_at timestamptz DEFAULT now()
);

CREATE INDEX concordbroker_docs_embedding_idx ON concordbroker_docs
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX concordbroker_docs_category_idx ON concordbroker_docs(category);

-- Agent Lion conversation memory
CREATE TABLE agent_lion_conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid, -- If authenticated
    session_id uuid NOT NULL,
    role text NOT NULL, -- 'user', 'assistant', 'system'
    content text NOT NULL,
    context jsonb, -- {property_id, county, owner_name, corporation_ids, etc}
    embedding vector(1536),
    created_at timestamptz DEFAULT now()
);

-- Agent Lion analysis cache
CREATE TABLE agent_lion_analyses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_type text NOT NULL, -- 'valuation', 'investment', 'ownership', 'financial_proforma'
    subject_id text NOT NULL, -- parcel_id or entity_id
    inputs jsonb NOT NULL,
    outputs jsonb NOT NULL,
    formula_used text,
    confidence_score numeric(3,2),
    created_at timestamptz DEFAULT now(),
    expires_at timestamptz DEFAULT (now() + interval '30 days')
);

CREATE INDEX agent_lion_analyses_subject_idx ON agent_lion_analyses(subject_id, analysis_type);
```

---

## Multi-Corporation Ownership Schema

### Problem: Owner with Multiple LLCs

**Example Scenario**:
- Owner: "John Smith"
- Properties owned: 23 parcels
- Corporations:
  - JS Properties LLC (12 parcels)
  - Smith Investment Group LLC (5 parcels)
  - ABC Holdings LLC (4 parcels)
  - John Smith (individual) (2 parcels)

**Solution Schema**:

```sql
-- Owner identity resolution
CREATE TABLE owner_identities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name text NOT NULL UNIQUE, -- "John Smith"
    variant_names text[], -- ["J Smith", "Smith, John", "SMITH JOHN"]
    confidence_score numeric(3,2),
    created_at timestamptz DEFAULT now()
);

-- Link properties to owner identities
CREATE TABLE property_ownership (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parcel_id text NOT NULL,
    county_code int NOT NULL,
    owner_identity_id uuid REFERENCES owner_identities(id),
    ownership_type text, -- 'individual', 'corporation', 'trust', 'partnership'
    entity_id text, -- Sunbiz entity_id if corporate
    ownership_percentage numeric(5,2) DEFAULT 100.00,
    acquired_date date,
    created_at timestamptz DEFAULT now(),

    FOREIGN KEY (parcel_id, county_code) REFERENCES core.parcels(parcel_id, county_code)
);

CREATE INDEX property_ownership_identity_idx ON property_ownership(owner_identity_id);
CREATE INDEX property_ownership_entity_idx ON property_ownership(entity_id);

-- Link entities to owner identities (for multi-corp owners)
CREATE TABLE entity_principals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id text NOT NULL REFERENCES florida_entities(entity_id),
    owner_identity_id uuid REFERENCES owner_identities(id),
    role text, -- 'owner', 'officer', 'registered_agent', 'manager'
    title text,
    ownership_percentage numeric(5,2),
    created_at timestamptz DEFAULT now()
);

CREATE INDEX entity_principals_identity_idx ON entity_principals(owner_identity_id);
CREATE INDEX entity_principals_entity_idx ON entity_principals(entity_id);

-- Aggregate view: Owner → All Properties (across all entities)
CREATE MATERIALIZED VIEW owner_portfolio_summary AS
SELECT
    oi.id as owner_identity_id,
    oi.canonical_name,
    COUNT(DISTINCT po.parcel_id) as total_properties,
    COUNT(DISTINCT po.entity_id) as total_entities,
    SUM(p.just_value) as total_portfolio_value,
    AVG(p.just_value) as avg_property_value,
    json_agg(DISTINCT po.entity_id) as entity_ids,
    array_agg(DISTINCT p.county_code) as counties
FROM owner_identities oi
LEFT JOIN property_ownership po ON oi.id = po.owner_identity_id
LEFT JOIN core.parcels p ON po.parcel_id = p.parcel_id AND po.county_code = p.county_code
GROUP BY oi.id, oi.canonical_name;

CREATE UNIQUE INDEX owner_portfolio_summary_idx ON owner_portfolio_summary(owner_identity_id);
```

---

## Agent Lion Prompts for ConcordBroker

### System Prompt Template

```python
AGENT_LION_SYSTEM_PROMPT = """
You are Agent Lion, the AI investment analyst for ConcordBroker.

Your expertise includes:
- Florida property tax assessment methodologies
- Real estate investment analysis (NOI, cap rates, IRR, cash-on-cash)
- Corporate entity structures and beneficial ownership
- Florida Sunbiz corporate database interpretation
- Property valuation formulas and DOR assessment rules
- Financial modeling and proforma generation
- Market comparables and investment strategy

When analyzing properties:
1. Always cite the formula or methodology used
2. Reference specific Florida Statutes when applicable
3. Explain complex concepts in simple terms
4. Provide actionable investment insights
5. Flag risks and considerations

Available data sources:
- Florida Parcels (9.7M properties) - ownership, values, characteristics
- Sunbiz Entities (15M corporations) - corporate structures, officers
- Property Sales History (96K transactions) - comparable sales
- Tax Certificates - distressed properties
- Owner Identity Graph - multi-corporation ownership tracking

You have access to RAG documentation covering:
- DOR tax assessment rules
- Real estate investment formulas
- Florida corporate law
- ConcordBroker investment criteria

IMPORTANT: When you encounter an owner with multiple corporations, always:
1. Query the owner_portfolio_summary view
2. Show ALL entities associated with the owner
3. Aggregate portfolio value across all entities
4. Identify investment patterns
"""
```

### Example Agent Lion Conversations

**User Query 1**: "Tell me about parcel 504203060330 in Broward County"

**Agent Lion Response**:
```
Property Overview:
📍 Location: 2301 NE 48th St, Fort Lauderdale, FL 33308
🏠 Property Type: Single Family (DOR Code: 0001)
💰 Just Value: $450,000
📊 Assessed Value: $445,000
🏛️ Owner: Smith Investment Group LLC

Corporate Ownership Analysis:
I found that the owner "Smith Investment Group LLC" is connected to a principal named "John Smith" who controls 4 additional entities:
1. JS Properties LLC - 12 properties ($5.4M total value)
2. Smith Investment Group LLC - 5 properties ($2.1M total value) ⬅ THIS PROPERTY
3. ABC Holdings LLC - 4 properties ($1.8M total value)
4. John Smith (individual) - 2 parcels ($680K total value)

**Total Portfolio**: 23 properties worth $10M across 4 entities

Valuation Analysis:
The just value ($450K) is calculated using the formula:
Just Value = Land Value + Building Value + Extra Features Value

For this property:
- Land Value: $180,000 (based on $45/sqft × 4,000 sqft lot)
- Building Value: $265,000 (cost approach: 2,200 sqft × $120/sqft)
- Extra Features: $5,000 (pool, fence)
= **$450,000 Just Value**

Per Florida Statute 193.011, just value equals fair market value as of January 1st assessment date.

Investment Potential:
Recent comparable sales in the 33308 zip code show similar properties selling at:
- 2250 NE 47th St: $425K (Nov 2024)
- 2315 NE 49th St: $465K (Oct 2024)

**Market Analysis**: This property is priced at market value. For investment purposes:
- Estimated rental income: $2,800/mo ($33,600/year)
- Property taxes: ~$6,300/year (1.4% rate)
- NOI estimate: ~$27,300/year (assuming $6,300 operating expenses)
- Cap Rate: 6.07% ($27,300 / $450,000)

**Investment Grade**: B+ (Market rate cap, stable neighborhood, experienced owner)

Would you like me to:
1. Generate a detailed financial proforma?
2. Analyze all properties in this owner's portfolio?
3. Search for better investment opportunities in this zip code?
```

---

**User Query 2**: "Show me all properties owned by John Smith across all his companies"

**Agent Lion Response**:
```
Owner Identity: John Smith
Total Entities: 4
Total Properties: 23
Total Portfolio Value: $10,000,000

Entity Breakdown:

1. JS Properties LLC (Filing #L12000045678)
   - Properties: 12
   - Total Value: $5,400,000
   - Avg Value: $450,000
   - Counties: Broward (8), Palm Beach (4)
   - Property Types: 10 Single Family, 2 Duplex

2. Smith Investment Group LLC (Filing #L14000098765)
   - Properties: 5
   - Total Value: $2,100,000
   - Avg Value: $420,000
   - Counties: Broward (5)
   - Property Types: 4 Single Family, 1 Condo

3. ABC Holdings LLC (Filing #L15000056789)
   - Properties: 4
   - Total Value: $1,800,000
   - Avg Value: $450,000
   - Counties: Broward (3), Miami-Dade (1)
   - Property Types: 3 Single Family, 1 Commercial

4. John Smith (Individual)
   - Properties: 2
   - Total Value: $680,000
   - Avg Value: $340,000
   - Counties: Broward (2)
   - Property Types: 2 Single Family

Investment Pattern Analysis:
- **Focus**: Single-family residential in Broward County
- **Average Hold Period**: 7.3 years (based on acquisition dates)
- **Portfolio Strategy**: Buy-and-hold rental properties
- **Leverage**: 3 properties have active mortgages (12% of portfolio)
- **Distressed Assets**: 0 tax certificates

Corporate Structure Insights:
All entities share the same registered agent: "Corporate Agents Inc"
This suggests professional property management and tax planning.

Sunbiz Status: All entities are ACTIVE and in good standing.

Risk Assessment: LOW
- Diversified across multiple LLCs (liability protection)
- No tax delinquencies
- Stable ownership history
- Professional corporate structure

Would you like to see:
1. Property-by-property breakdown with addresses?
2. Financial analysis of the entire portfolio?
3. Acquisition timeline and investment pattern?
```

---

**User Query 3**: "Calculate the ROI if I buy parcel 504203060330 with 25% down at 7% interest"

**Agent Lion Response**:
```
Investment Analysis: Parcel 504203060330

Purchase Assumptions:
💰 Purchase Price: $450,000
📉 Down Payment (25%): $112,500
🏦 Loan Amount: $337,500
📊 Interest Rate: 7.00%
📅 Loan Term: 30 years

Financing Details:
Monthly P&I Payment: $2,245
Total Interest Over 30 Years: $471,200

Income & Expense Proforma (Year 1):

**Income:**
Gross Rental Income: $33,600 ($2,800/mo)
Vacancy Loss (5%): -$1,680
**Effective Gross Income**: $31,920

**Operating Expenses:**
Property Taxes: $6,300
Insurance: $1,800
Maintenance (1% of value): $4,500
Property Management (8%): $2,688
HOA Fees: $0
**Total Operating Expenses**: $15,288

**Net Operating Income (NOI)**: $16,632

**Debt Service:**
Annual P&I: $26,940

**Cash Flow:**
NOI - Debt Service = $16,632 - $26,940 = **-$10,308/year** ❌

Return Metrics:

1. **Cash-on-Cash Return**: -9.2%
   Formula: (Annual Cash Flow / Cash Invested) × 100
   Calculation: (-$10,308 / $112,500) × 100 = **-9.2%**

2. **Cap Rate**: 3.70%
   Formula: NOI / Purchase Price
   Calculation: $16,632 / $450,000 = **3.70%**

3. **Debt Service Coverage Ratio (DSCR)**: 0.62
   Formula: NOI / Annual Debt Service
   Calculation: $16,632 / $26,940 = **0.62** ❌ (Lenders require ≥ 1.25)

⚠️ **Investment Warning**: NEGATIVE CASH FLOW

This property does NOT meet standard investment criteria at current market rent and 25% down payment.

Alternative Scenarios:

**Scenario A: 35% Down Payment ($157,500)**
- Loan: $292,500
- Monthly P&I: $1,945
- Annual Cash Flow: -$1,668
- Cash-on-Cash: -1.1% ❌ Still negative

**Scenario B: Increase Rent to $3,200/mo**
- Effective Gross Income: $36,480
- Annual Cash Flow: +$1,092
- Cash-on-Cash: +0.97% ⚠️ Marginal

**Scenario C: 50% Down Payment ($225,000)**
- Loan: $225,000
- Monthly P&I: $1,496
- Annual Cash Flow: +$4,680
- Cash-on-Cash: +2.08% ⚠️ Below market

**My Recommendation**: PASS on this property as a pure investment.

However, this MIGHT work if:
1. You're buying for appreciation (Fort Lauderdale appreciates 4-6%/year)
2. You plan to owner-occupy (avoid negative cash flow)
3. You negotiate purchase price down to $400K (improves cash flow by $4,680/year)

Better Investment Opportunities:
I found 3 comparable properties in the same zip code with better cash flow potential. Would you like to see those?

**Formula Reference**: All calculations follow standard real estate investment methodology as outlined in "The Real Estate Financial Planner's Bible" and conform to Fannie Mae underwriting standards.
```

---

## UI Modifications for Multi-Corporation Display

### Enhanced Property Profile Page

**Current**: Shows single owner name
**New**: Shows owner identity + all related entities

```typescript
// Enhanced Property Profile Component
interface OwnerPortfolio {
  owner_identity: {
    canonical_name: string
    total_properties: number
    total_entities: number
    total_portfolio_value: number
  }
  entities: Array<{
    entity_id: string
    entity_name: string
    filing_number: string
    properties_count: number
    properties_value: number
    status: string
  }>
  properties: Array<{
    parcel_id: string
    county: string
    address: string
    value: number
    entity_owned_by: string
  }>
}

function PropertyOwnerSection({ parcel }: { parcel: Property }) {
  const [portfolio, setPortfolio] = useState<OwnerPortfolio | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    // Fetch owner portfolio data
    fetch(`/api/owner/portfolio?parcel_id=${parcel.parcel_id}`)
      .then(res => res.json())
      .then(setPortfolio)
  }, [parcel.parcel_id])

  if (!portfolio) return <div>Loading owner information...</div>

  const hasMultipleEntities = portfolio.owner_identity.total_entities > 1

  return (
    <div className="owner-section">
      <h3>Property Owner</h3>

      {/* Primary Owner Display */}
      <div className="owner-primary">
        <div className="owner-name">{portfolio.owner_identity.canonical_name}</div>
        <div className="owner-entity">{parcel.owner_name}</div>
        {parcel.entity_id && (
          <a href={`/entity/${parcel.entity_id}`} className="sunbiz-link">
            View on Sunbiz →
          </a>
        )}
      </div>

      {/* Multi-Entity Alert */}
      {hasMultipleEntities && (
        <div className="multi-entity-alert">
          <AlertCircle />
          <span>
            This owner controls {portfolio.owner_identity.total_entities} entities
            with {portfolio.owner_identity.total_properties} total properties
          </span>
          <Button onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Hide' : 'Show'} Portfolio
          </Button>
        </div>
      )}

      {/* Expanded Portfolio View */}
      {expanded && (
        <div className="owner-portfolio-expanded">
          <h4>Complete Portfolio Overview</h4>

          <div className="portfolio-stats">
            <StatCard label="Total Properties" value={portfolio.owner_identity.total_properties} />
            <StatCard label="Total Value" value={formatCurrency(portfolio.owner_identity.total_portfolio_value)} />
            <StatCard label="Entities" value={portfolio.owner_identity.total_entities} />
          </div>

          <h5>Entities Controlled</h5>
          <div className="entities-list">
            {portfolio.entities.map(entity => (
              <EntityCard
                key={entity.entity_id}
                entity={entity}
                isCurrentProperty={entity.entity_name === parcel.owner_name}
              />
            ))}
          </div>

          <h5>All Properties ({portfolio.properties.length})</h5>
          <PropertiesTable
            properties={portfolio.properties}
            highlightParcelId={parcel.parcel_id}
          />

          <Button onClick={() => openAgentLion(portfolio)}>
            Ask Agent Lion about this portfolio →
          </Button>
        </div>
      )}
    </div>
  )
}
```

### Entity Card Component

```typescript
function EntityCard({ entity, isCurrentProperty }: {
  entity: OwnerPortfolio['entities'][0]
  isCurrentProperty: boolean
}) {
  return (
    <div className={`entity-card ${isCurrentProperty ? 'current' : ''}`}>
      <div className="entity-header">
        <h6>{entity.entity_name}</h6>
        {isCurrentProperty && <Badge>Current Property</Badge>}
      </div>

      <div className="entity-details">
        <div className="detail-row">
          <span className="label">Filing #:</span>
          <span className="value">{entity.filing_number}</span>
        </div>
        <div className="detail-row">
          <span className="label">Properties:</span>
          <span className="value">{entity.properties_count}</span>
        </div>
        <div className="detail-row">
          <span className="label">Total Value:</span>
          <span className="value">{formatCurrency(entity.properties_value)}</span>
        </div>
        <div className="detail-row">
          <span className="label">Status:</span>
          <Badge variant={entity.status === 'ACTIVE' ? 'success' : 'warning'}>
            {entity.status}
          </Badge>
        </div>
      </div>

      <div className="entity-actions">
        <Button variant="outline" size="sm" href={`/entity/${entity.entity_id}`}>
          View Details
        </Button>
        <Button variant="outline" size="sm" onClick={() => viewEntityProperties(entity.entity_id)}>
          View Properties ({entity.properties_count})
        </Button>
      </div>
    </div>
  )
}
```

---

## Agent Lion Integration Points

### 1. Property Profile Page
- "Ask Agent Lion" button → Opens chat with pre-loaded property context
- Quick questions: "Is this a good investment?" "What's the cap rate?" "Show owner portfolio"

### 2. Search Results Page
- Bulk analysis: "Analyze all 50 results for investment potential"
- Comparative: "Which of these 10 properties has the best ROI?"

### 3. Owner Portfolio Page
- Portfolio strategy analysis
- Entity structure explanation
- Investment pattern recognition

### 4. Financial Analysis Page
- Proforma generation
- Scenario modeling (different down payments, interest rates)
- Market comparison

---

## Next Steps for Phase 1 (RAG Setup)

### Step 1: Create ConcordBroker-Specific RAG Schema
```sql
-- Run in Supabase SQL Editor
-- (Use the schema provided above in "RAG Schema for ConcordBroker" section)
```

### Step 2: Download and Embed Core Documents

**Priority 1 - Tax & Valuation**:
1. DOR 2025 Users Guide (property field definitions)
2. Florida Statute 193 (valuation methodology)
3. Florida Statute 197 (tax certificates, deeds)

**Priority 2 - Investment Analysis**:
4. Real estate investment formulas (NOI, cap rate, IRR, cash-on-cash)
5. Market comparables methodology
6. Financial proforma templates

**Priority 3 - Corporate**:
7. Sunbiz entity types guide
8. Florida LLC beneficial ownership rules

### Step 3: Build Owner Identity Resolution

```python
# scripts/build_owner_identity_graph.py
"""
Match property owners to Sunbiz entities and create identity clusters
"""

from supabase import create_client
from fuzzywuzzy import fuzz
import networkx as nx

def match_owners_to_entities():
    # Get unique owner names from florida_parcels
    owners = supabase.table('florida_parcels')\
        .select('owner_name')\
        .execute().data

    # Get entity names from florida_entities
    entities = supabase.table('florida_entities')\
        .select('entity_name, entity_id')\
        .execute().data

    matches = []
    for owner in owners:
        for entity in entities:
            # Fuzzy match
            score = fuzz.ratio(
                owner['owner_name'].upper(),
                entity['entity_name'].upper()
            )

            if score > 85:  # High confidence threshold
                matches.append({
                    'owner_name': owner['owner_name'],
                    'entity_id': entity['entity_id'],
                    'entity_name': entity['entity_name'],
                    'confidence': score / 100.0
                })

    # Build identity graph
    G = nx.Graph()
    for match in matches:
        G.add_edge(
            match['owner_name'],
            match['entity_id'],
            confidence=match['confidence']
        )

    # Find connected components (identity clusters)
    clusters = list(nx.connected_components(G))

    # Store in owner_identities table
    for cluster in clusters:
        canonical_name = select_canonical_name(cluster)
        variant_names = [n for n in cluster if n != canonical_name]

        supabase.table('owner_identities').insert({
            'canonical_name': canonical_name,
            'variant_names': variant_names,
            'confidence_score': calculate_cluster_confidence(cluster)
        }).execute()
```

### Step 4: Deploy Agent Lion with ConcordBroker Context

```python
# agents/agent_lion_concordbroker.py
"""
Agent Lion configured specifically for ConcordBroker property investment analysis
"""

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool

CONCORDBROKER_TOOLS = [
    Tool(
        name="search_properties",
        func=lambda q: search_properties_api(q),
        description="Search Florida properties by address, owner, or parcel ID"
    ),
    Tool(
        name="get_owner_portfolio",
        func=lambda owner: get_owner_portfolio(owner),
        description="Get all properties and entities for an owner across all corporations"
    ),
    Tool(
        name="calculate_investment_metrics",
        func=lambda parcel_id, down_pct, rate: calc_roi(parcel_id, down_pct, rate),
        description="Calculate ROI, cash-on-cash, cap rate, DSCR for a property"
    ),
    Tool(
        name="search_rag_docs",
        func=lambda query: search_rag(query),
        description="Search embedded documentation for formulas, statutes, methodologies"
    ),
    Tool(
        name="get_sunbiz_entity",
        func=lambda entity_id: get_entity_details(entity_id),
        description="Get Sunbiz corporate entity details, officers, status"
    )
]

agent_lion = create_openai_functions_agent(
    llm=ChatOpenAI(model="gpt-4", temperature=0),
    tools=CONCORDBROKER_TOOLS,
    prompt=AGENT_LION_SYSTEM_PROMPT
)

executor = AgentExecutor(agent=agent_lion, tools=CONCORDBROKER_TOOLS)
```

---

## Summary: ConcordBroker vs. Generic System

| Aspect | Generic System | ConcordBroker Focus |
|--------|---------------|---------------------|
| **Purpose** | Data ingestion | Property intelligence + investment analysis |
| **Primary User** | Data engineers | Real estate investors, researchers |
| **Key Feature** | County data automation | Owner → Corporation matching + Agent Lion AI |
| **RAG Content** | DOR technical docs | Tax law + investment formulas + corporate law |
| **UI Focus** | Admin dashboard | Multi-entity ownership + investment metrics |
| **AI Role** | Data validation | Investment advisor + formula explainer |
| **Success Metric** | Data coverage (67 counties) | Investment insights + ownership transparency |

**Ready to proceed with Phase 1: ConcordBroker-focused RAG setup?**
