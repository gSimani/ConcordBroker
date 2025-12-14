# Property Profile System Documentation

## 🏠 Complete Property Intelligence Platform

The ConcordBroker Property Profile system aggregates data from **8+ sources** to create comprehensive property profiles accessible via simple URLs like:

**`http://localhost:5175/properties/fort-lauderdale/123-main-street`**

---

## 📊 Data Integration

### What Each Property Profile Contains

| Data Category | Source | Information Provided |
|--------------|--------|---------------------|
| **Property Details** | BCPA | Type, year built, sqft, beds/baths, pool |
| **Valuation** | BCPA/DOR | Market value, assessed value, taxable value |
| **Sales History** | SDF | All transactions, prices, dates, distress flags |
| **Ownership** | BCPA/Sunbiz | Owner name, type (LLC/Corp/Trust), business entity |
| **Tax Information** | NAV/TPP | Property taxes, special assessments, CDD status |
| **Investment Metrics** | Calculated | Cap rate, rental estimate, ROI, flip potential |
| **Opportunities** | Analysis | Distressed, REO, motivated seller indicators |
| **Risk Factors** | Analysis | Title issues, high assessments, structural age |

---

## 🎯 Key Features

### 1. Investment Scoring (0-100)
Each property receives an investment score based on:
- **Positive Factors** (+points)
  - Distressed property (+15)
  - Bank-owned/REO (+10)
  - Flip potential (+10)
  - High cap rate >7% (+10)
  - Low price/sqft <$200 (+5)

- **Negative Factors** (-points)
  - CDD property (-5)
  - High NAV >$5000 (-10)
  - Trust ownership (-5)

### 2. Automatic Opportunity Detection
- 🔴 **Distressed Properties** - Foreclosures, tax deeds
- 🏦 **Bank-Owned (REO)** - Financial institution sales
- 💰 **Flip Opportunities** - Recent price appreciation >30%
- 📈 **High Cap Rate** - Strong rental potential >8%
- 🏢 **Inactive Business Owner** - Potential motivated seller

### 3. Risk Assessment
- ⚠️ CDD with high assessments
- ⚠️ Properties built before 1970
- ⚠️ Tax deed sales (title issues)
- ⚠️ Trust ownership (complex negotiation)
- ⚠️ No recent sales history

---

## 🔗 URL Structure

### Property Profile URLs
```
/properties/{city}/{address}

Examples:
/properties/fort-lauderdale/123-main-street
/properties/miami-beach/456-ocean-drive
/properties/boca-raton/789-palmetto-park-road
```

### API Endpoints
```
GET /api/property/profile/{city}/{address}
GET /api/property/search?q={query}
GET /api/property/investment-opportunities
GET /api/property/market-analysis/{city}
GET /api/property/owner/{owner_name}
GET /api/data/status
```

---

## 💻 Implementation

### Backend Components

#### 1. PropertyProfileService (`property_profile_service.py`)
- Aggregates data from all sources
- Parallel data fetching for performance
- Investment scoring algorithm
- Opportunity/risk detection

#### 2. Property Profile API (`property_profile_api.py`)
- FastAPI endpoints
- CORS enabled for frontend
- Real-time data aggregation
- JSON responses

#### 3. Database Connections
- BCPA Database
- SDF Supabase
- NAV Supabase
- TPP Supabase
- Sunbiz SFTP Database

### Frontend Components

#### PropertyProfile Component (`PropertyProfile.tsx`)
- Tabbed interface (Overview, Ownership, Sales, Taxes, Analysis)
- Investment score display
- Opportunity/risk alerts
- Sales history table
- Data quality indicators

---

## 🚀 Quick Start

### 1. Start the API Server
```bash
cd apps/api
python property_profile_api.py
# API runs on http://localhost:8000
```

### 2. Start the Frontend
```bash
cd apps/web
npm run dev
# Frontend runs on http://localhost:5175
```

### 3. Access Property Profiles
Navigate to:
```
http://localhost:5175/properties/fort-lauderdale/123-main-street
```

---

## 📈 Example Property Profile Response

```json
{
  "address": "123 Main Street",
  "city": "Fort Lauderdale",
  "state": "FL",
  "parcel_id": "494116150190",
  "owner_name": "INVESTMENT PROPERTIES LLC",
  "owner_type": "LLC",
  "property_type": "Single Family",
  "year_built": 1985,
  "living_area": 2500,
  "bedrooms": 4,
  "bathrooms": 3,
  "market_value": 450000,
  "last_sale_price": 380000,
  "last_sale_date": "2024-03-15",
  "is_distressed": false,
  "is_bank_owned": true,
  "investment_score": 85,
  "cap_rate": 7.8,
  "rental_estimate": 3200,
  "opportunities": [
    "Bank-owned (REO) - motivated seller",
    "High cap rate (7.8%) - strong rental potential"
  ],
  "risk_factors": [
    "Property in CDD - additional assessments $2400/year"
  ],
  "confidence_score": 92,
  "data_sources": ["BCPA", "SDF", "NAV", "Sunbiz"]
}
```

---

## 🎨 User Interface

### Property Profile Page Layout

```
┌────────────────────────────────────────┐
│ 📍 123 Main Street                     │
│ Fort Lauderdale, FL 33301              │
│                     Investment Score: 85│
├────────────────────────────────────────┤
│ Market Value  Last Sale  Price/SqFt    │
│ $450,000     $380,000   $180          │
├────────────────────────────────────────┤
│ ✅ Investment Opportunities            │
│ • Bank-owned (REO) property            │
│ • High cap rate potential              │
├────────────────────────────────────────┤
│ [Overview][Ownership][Sales][Taxes]    │
├────────────────────────────────────────┤
│ Property Details        Valuation      │
│ • Type: Single Family   • Market: $450K│
│ • Year: 1985           • Assessed: $420K│
│ • Living: 2,500 sqft   • Taxable: $400K│
│ • Beds: 4              • Last Sale: $380K│
│ • Baths: 3             • Date: Mar 2024│
└────────────────────────────────────────┘
```

---

## 🔄 Data Flow

```
1. User navigates to: /properties/fort-lauderdale/123-main-street
                                    ↓
2. React component calls: /api/property/profile/fort-lauderdale/123-main-street
                                    ↓
3. PropertyProfileService fetches data in parallel:
   ├─→ BCPA (property details)
   ├─→ SDF (sales history)
   ├─→ NAV (assessments)
   ├─→ TPP (tangible property)
   ├─→ Sunbiz (business entity)
   └─→ DOR (tax data)
                                    ↓
4. Service aggregates and scores data
                                    ↓
5. Returns comprehensive property profile
                                    ↓
6. Frontend displays formatted profile with tabs
```

---

## 🛠️ Testing

### Test Property Profiles
```bash
python TEST_PROPERTY_PROFILES.py
```

### Test Specific Address
```python
from property_profile_service import PropertyProfileService

service = PropertyProfileService()
await service.initialize()

profile = await service.get_property_profile(
    address="123 Main Street",
    city="Fort Lauderdale",
    state="FL"
)

print(f"Investment Score: {profile.investment_score}")
print(f"Opportunities: {profile.opportunities}")
```

---

## 📊 Business Value

### For Real Estate Investors
- **Instant property analysis** with investment scoring
- **Distressed property alerts** for below-market opportunities
- **Owner type identification** for negotiation strategy
- **Risk assessment** before making offers

### For Brokers
- **Complete property history** for client presentations
- **Market comparables** from actual sales data
- **Business entity verification** for commercial deals
- **Special assessment warnings** for buyer awareness

### For Property Managers
- **Rental estimates** based on market data
- **Cap rate calculations** for investment analysis
- **Owner portfolio viewing** for bulk management
- **Tax assessment tracking** for budget planning

---

## 🚦 Status Indicators

| Indicator | Meaning |
|-----------|---------|
| 🟢 High Investment Score (80-100) | Excellent opportunity |
| 🟡 Medium Investment Score (60-79) | Good potential with considerations |
| 🔴 Low Investment Score (<60) | Higher risk or limited opportunity |
| 🏦 Bank-Owned | REO property, motivated seller |
| 🔥 Distressed | Foreclosure or tax deed |
| 🏘️ CDD | Community Development District fees |
| 📊 High Confidence | Data from 4+ sources |

---

## 🎯 Next Steps

1. **Add Property Images** - Integrate with image APIs
2. **Neighborhood Stats** - Crime, schools, demographics
3. **Mortgage Calculator** - Payment estimates
4. **Save Searches** - User accounts and alerts
5. **Compare Properties** - Side-by-side analysis
6. **Export Reports** - PDF property reports

---

## 📞 Support

The Property Profile system is the **core of ConcordBroker**, providing comprehensive intelligence on any property through a simple address-based URL. All data sources are integrated and continuously updated to provide the most current information available.