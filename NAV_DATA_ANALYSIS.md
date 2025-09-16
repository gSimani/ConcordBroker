# Florida Revenue NAV Data Analysis
## Comprehensive Analysis of Non Ad Valorem Assessment Data

Based on the `navlayout.pdf` document analysis, Florida Revenue provides Non Ad Valorem Assessment Roll data through two main file types:

## 📊 **Data Structure Overview**

### **NAV N Files (Parcel Account Table)**
- **Purpose**: Summary of non ad valorem assessments by parcel
- **Record Type**: "N" 
- **File Naming**: `NAVN[CountyNum][Year][SubmissionNum].TXT`
- **Example**: `NAVN110901.TXT` (County 11, Year 09, Submission 01)

### **NAV D Files (Assessment Details Table)**  
- **Purpose**: Detailed breakdown of individual assessments
- **Record Type**: "D"
- **File Naming**: `NAVD[CountyNum][Year][SubmissionNum].TXT`
- **Example**: `NAVD110901.TXT` (County 11, Year 09, Submission 01)

---

## 🏗️ **NAV N (Table N) - Parcel Account Records**

**8 Fields Total** - Summary level data per parcel

| Field | Name | Description | Specifications |
|-------|------|-------------|----------------|
| 1 | Roll Type | Department of Revenue Roll Code ("N") | Alpha, 1 Character |
| 2 | County Number | 2-digit county number (11-77) | Numeric, 2 Characters |
| 3 | PA Parcel Number | Property Appraiser's unique parcel number | Alphanumeric, Up to 26 Characters |
| 4 | TC Account Number | Tax Collector real estate account number | Numeric, Up to 30 Characters |
| 5 | Tax Year | 4-digit year | Numeric, 4 Characters |
| 6 | Total Assessments | Total amount of all non ad valorem assessments | Numeric, Up to 12 Characters |
| 7 | Number of Assessments | Count of total assessments for this parcel | Numeric, Up to 3 Characters |
| 8 | Tax Roll Sequence Number | Sequential order on roll | Numeric, Up to 7 Characters |

---

## 🔍 **NAV D (Table D) - Assessment Detail Records**

**8 Fields Total** - Individual assessment details

| Field | Name | Description | Specifications |
|-------|------|-------------|----------------|
| D1 | Record Type | Department of Revenue record code ("D") | Alpha, 1 Character |
| D2 | County Number | 2-digit county number (11-77) | Numeric, 2 Characters |
| D3 | PA Parcel Number | Property Appraiser's unique parcel number | Alphanumeric, Up to 26 Characters |
| D4 | Levy Identifier | Unique identifier from DR-503NA report | Alphanumeric, Up to 12 Characters |
| D5 | Local Government Code | Type of levy authority from DR-503NA | Numeric, 1 Character |
| D6 | Function Code | Primary intended use (codes 1-10) | Numeric, Up to 2 Characters |
| D7 | Assessment Amount | Dollar amount of assessment | Numeric, Up to 9 Characters |
| D8 | Tax Roll Sequence Number | Sequential number in table | Numeric, Up to 7 Characters |

---

## 🎯 **Key Business Intelligence Opportunities**

### **Non Ad Valorem Assessments Include:**
- **Special Districts**: Fire, Water, Sewer, Lighting Districts
- **Municipal Services**: Stormwater, Solid Waste, Code Enforcement
- **Improvement Districts**: Community Development Districts (CDDs)  
- **Infrastructure**: Road/Bridge Assessments, Utility Connections
- **Environmental**: Environmental remediation, Conservation programs

### **Function Codes (1-10) Track:**
1. General Government
2. Public Safety  
3. Physical Environment
4. Transportation
5. Economic Environment
6. Human Services
7. Culture/Recreation
8. Court Related
9. Debt Service
10. Other

---

## 🏢 **Broward County Analysis (County Code 16)**

Based on the file naming convention, Broward County files would be:
- **NAV N**: `NAVN162401.TXT` (2024 data, submission 01)
- **NAV D**: `NAVD162401.TXT` (2024 data, submission 01)

### **Expected Data Volume:**
- **NAV N Records**: ~600,000+ parcels (summary level)
- **NAV D Records**: ~2,000,000+ assessments (detail level)
- **Relationship**: 1 NAV N record can have multiple NAV D records

---

## 💡 **Strategic Value for ConcordBroker**

### **1. Complete Tax Burden Analysis**
- Combine ad valorem (property tax) + non ad valorem assessments
- True total cost of property ownership
- Hidden costs affecting property investment ROI

### **2. Special District Intelligence**
- Identify properties in CDDs (Community Development Districts)
- Track infrastructure debt obligations  
- Assess municipal service costs

### **3. Investment Risk Assessment**
- Properties with high special assessments
- Pending infrastructure projects requiring assessments
- Municipal bond debt tied to properties

### **4. Market Opportunity Detection**
- Properties with expiring assessment bonds
- Areas with declining special district costs
- Development opportunities based on infrastructure availability

---

## 🔗 **Data Integration Strategy**

### **Primary Keys for Linking:**
- **PA Parcel Number**: Links to existing property data
- **TC Account Number**: Links to tax collector records
- **County Number + Tax Year**: Data versioning

### **Cross-Reference Opportunities:**
1. **TPP Data**: Same parcels with different assessment types
2. **Property Appraiser Data**: Complete property characteristics
3. **Official Records**: Property transfers with assessment obligations
4. **Sunbiz Data**: Business entities responsible for assessments

### **Database Design:**
```sql
-- NAV N Table (Parcel Summaries)
CREATE TABLE nav_parcel_assessments (
    id SERIAL PRIMARY KEY,
    roll_type VARCHAR(1),
    county_number VARCHAR(2),
    pa_parcel_number VARCHAR(26),
    tc_account_number VARCHAR(30),
    tax_year VARCHAR(4),
    total_assessments DECIMAL(12,2),
    number_of_assessments INTEGER,
    tax_roll_sequence_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NAV D Table (Assessment Details)
CREATE TABLE nav_assessment_details (
    id SERIAL PRIMARY KEY,
    record_type VARCHAR(1),
    county_number VARCHAR(2),  
    pa_parcel_number VARCHAR(26),
    levy_identifier VARCHAR(12),
    local_government_code INTEGER,
    function_code INTEGER,
    assessment_amount DECIMAL(9,2),
    tax_roll_sequence_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📈 **Expected Insights**

### **High-Value Analytics:**
1. **Total Cost of Ownership**: Property tax + special assessments
2. **Investment Hotspots**: Areas with low/declining assessment burdens  
3. **Infrastructure Debt**: Properties with CDD or improvement district obligations
4. **Municipal Efficiency**: Cost per service by jurisdiction
5. **Development Patterns**: New assessments indicating growth areas

### **Risk Indicators:**
- Properties with assessment amounts > 5% of property value
- Parcels with multiple overlapping special districts
- Assessment trends indicating fiscal stress in municipalities
- Expiring bonds creating assessment payment spikes

This comprehensive NAV data will provide critical missing pieces for complete property investment analysis in the ConcordBroker system.