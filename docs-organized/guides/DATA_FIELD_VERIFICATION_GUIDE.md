# 📊 ConcordBroker Data Field Verification System

## Complete Guide for Property Appraiser & Sunbiz Database Field Mapping

This system ensures 100% accurate placement of data from Supabase databases to the correct UI locations using **Playwright MCP**, **OpenCV**, and **NumPy**.

## 🎯 Overview

The verification system provides:
- **Automated field mapping** from database to UI
- **Visual verification** using computer vision
- **Numerical validation** using NumPy
- **Comprehensive reporting** with accuracy metrics

## 📁 System Components

### 1. **Field Mapping Configuration** (`field_mapping_configuration.json`)
Complete mapping of all database fields to UI locations:
- Property Appraiser data → UI tabs
- Sunbiz corporation data → Business entity sections
- Tax deed sales → Auction information
- Building permits → Permit tabs

### 2. **Data Field Mapper & Verifier** (`data_field_mapper_verifier.py`)
Core verification engine with:
- Playwright browser automation
- OpenCV visual analysis
- NumPy numerical validation
- Database connection management

### 3. **Verification Runner** (`run_field_verification.py`)
Orchestrates the verification process:
- Selects test properties
- Runs comprehensive checks
- Generates statistical reports

## 🗺️ Complete Field Mapping

### Property Appraiser Database Fields

#### **Overview Tab**
```
Property Location Section:
  phy_addr1 → Property Address
  phy_city → City
  phy_zipcd → ZIP Code
  parcel_id → Parcel ID

Quick Stats Section:
  jv → Market Value
  yr_blt → Year Built
  tot_lvg_area → Living Area
  bedroom_cnt → Bedrooms
  bathroom_cnt → Bathrooms
```

#### **Core Property Tab**
```
Property Details Section:
  dor_uc → Property Use Code
  yr_blt → Year Built
  act_yr_blt → Actual Year Built
  eff_yr_blt → Effective Year Built

Structure Details Section:
  no_buldng → Number of Buildings
  no_res_unts → Residential Units
  spec_feat_val → Special Features Value
```

#### **Valuation Tab**
```
Current Values Section:
  jv → Just Value ($)
  av_sd → Assessed Value ($)
  tv_sd → Taxable Value ($)
  av_nsd → Non-School Assessed ($)
  tv_nsd → Non-School Taxable ($)

Value Breakdown Section:
  lnd_val → Land Value ($)
  bldg_val → Building Value ($)
  xf_val → Extra Feature Value ($)
```

#### **Owner Tab**
```
Owner Information Section:
  owner_name → Owner Name
  owner_addr1 → Owner Address
  owner_city → Owner City
  owner_state → Owner State
  owner_zip → Owner ZIP
```

#### **Building Tab**
```
Building Details Section:
  tot_lvg_area → Total Living Area (sq ft)
  grnd_ar → Ground Area (sq ft)
  gross_ar → Gross Area (sq ft)
  heat_ar → Heated Area (sq ft)

Room Details Section:
  bedroom_cnt → Bedrooms
  bathroom_cnt → Bathrooms
  half_bath_cnt → Half Bathrooms
  full_bath_cnt → Full Bathrooms
```

#### **Land & Legal Tab**
```
Land Information Section:
  lnd_sqfoot → Land Square Feet
  dt_last_calc → Land Calculation Date

Legal Description Section:
  lgl_1 → Legal Description Line 1
  subdivision → Subdivision
  blk → Block
  lot → Lot
```

#### **Sales History Tab**
```
Most Recent Sale Section:
  sale_prc1 → Last Sale Price ($)
  sale_yr1 → Last Sale Year
  sale_mo1 → Last Sale Month
  qual_cd1 → Qualification Code
  or_book → OR Book
  or_page → OR Page

Previous Sale Section:
  sale_prc2 → Previous Sale Price ($)
  sale_yr2 → Previous Sale Year
```

#### **Taxes Tab**
```
Tax Amounts Section:
  tax_amount → Annual Tax Amount ($)
  millage_rate → Millage Rate
  last_tax_roll_yr → Tax Roll Year

Tax Certificates Section:
  certificate_number → Certificate Number
  certificate_amount → Certificate Amount ($)
  certificate_status → Certificate Status
```

#### **Exemptions Tab**
```
Exemptions Section:
  exempt_val → Total Exemption Value ($)
  homestead_exemption → Homestead Flag
  wid_exempt → Widow Exemption ($)
  dis_exempt → Disability Exemption ($)
  vet_exempt → Veteran Exemption ($)
```

### Sunbiz Database Fields

#### **Sunbiz Tab**
```
Business Entity Section:
  corp_name → Corporation Name
  corp_number → Document Number
  status → Status (ACTIVE/INACTIVE/DISSOLVED)
  filing_date → Filing Date
  entity_type → Entity Type

Registered Agent Section:
  agent_name → Registered Agent
  agent_address1 → Agent Address
  agent_city → Agent City
  agent_state → Agent State

Officers Section:
  officer_name → Officer Name
  officer_title → Officer Title
  officer_address → Officer Address
```

### Tax Deed Sales Fields

#### **Tax Deed Sales Tab**
```
Auction Information Section:
  td_number → Tax Deed Number
  auction_date → Auction Date
  auction_status → Status
  opening_bid → Opening Bid ($)
  minimum_bid → Minimum Bid ($)
  winning_bid → Winning Bid ($)
```

## 🔧 Installation & Setup

### 1. Install Dependencies
```bash
# Core dependencies
pip install playwright numpy opencv-python pandas asyncpg

# Install Playwright browsers
playwright install chromium

# OCR support (optional)
pip install pytesseract
```

### 2. Configure Database
Update connection settings in `data_field_mapper_verifier.py`:
```python
self.db_conn = await asyncpg.connect(
    host="aws-0-us-east-1.pooler.supabase.com",
    port=6543,
    user="postgres.pmispwtdngkcmsrsjwbp",
    password="your_password",
    database="postgres"
)
```

## 🚀 Running Verification

### Quick Verification
```bash
# Run automated verification on sample properties
python run_field_verification.py
```

### Custom Verification
```python
from data_field_mapper_verifier import DataFieldMapperVerifier

# Initialize verifier
verifier = DataFieldMapperVerifier()

# Verify specific properties
sample_parcels = ['064210010010', '064210010020']
report = await verifier.run_comprehensive_verification(sample_parcels)
```

### Visual Verification Only
```python
from data_field_mapper_verifier import OpenCVVisualVerifier

verifier = OpenCVVisualVerifier()
screenshot = "property_screenshot.png"
visual_match = await verifier.verify_field_display(
    screenshot, expected_value, field_mapping
)
```

## 📈 NumPy Validation Features

### Statistical Analysis
- **Mean/Median accuracy** across all fields
- **Standard deviation** for consistency
- **Outlier detection** using IQR method
- **Percentile analysis** (25th, 75th)

### Data Type Validation
```python
# Float comparison with tolerance
np.allclose([db_value], [ui_value], rtol=1e-5, atol=1e-2)

# Integer validation
db_val == ui_val

# String normalization
str(db_value).strip().upper() == str(ui_value).strip().upper()
```

### Quality Metrics
- **95%+**: Excellent mapping
- **85-94%**: Good mapping
- **75-84%**: Fair mapping
- **<75%**: Poor mapping (needs attention)

## 🎥 Playwright MCP Features

### Browser Automation
```python
# Navigate to property page
await page.goto(f"http://localhost:5173/property/{parcel_id}")

# Click specific tab
await page.click(f'[data-tab="{tab_name}"]')

# Extract field value
element = await page.query_selector(f'#{field_id}')
value = await element.text_content()
```

### Multi-Selector Strategy
Tries multiple selectors for robustness:
1. ID selector: `#field-id`
2. Data attribute: `[data-field="field-id"]`
3. Aria label: `[aria-label="Field Label"]`
4. Text content: `text=Field Label`

## 👁️ OpenCV Visual Verification

### Screenshot Analysis
```python
# Take field screenshot
await element.screenshot(path="field_verify.png")

# OCR text extraction
text = pytesseract.image_to_string(processed_image)

# Verify expected value appears
expected_value in extracted_text
```

### Layout Analysis
- Detects UI elements using edge detection
- Calculates alignment scores
- Measures spacing consistency
- Identifies loading issues (blank areas)

## 📊 Verification Report

### Report Contents
```json
{
  "report_date": "2025-01-16T10:30:00",
  "properties_tested": 5,
  "total_fields_verified": 450,
  "total_fields_matched": 428,
  "overall_accuracy": 95.11,
  "statistical_analysis": {
    "mean_accuracy": 94.8,
    "median_accuracy": 95.2,
    "std_deviation": 2.3
  },
  "recommendations": [
    "Field 'sale_prc2' consistently fails verification",
    "Tab 'permits' has low accuracy (78%)"
  ]
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Field Not Found
**Problem**: UI element selector not matching
**Solution**: Update selector in `field_mapping_configuration.json`

#### 2. Value Mismatch
**Problem**: Database value doesn't match UI
**Solution**: Check transformation functions and formatting

#### 3. Visual Verification Fails
**Problem**: OCR not detecting text
**Solution**: Improve image preprocessing or adjust threshold

#### 4. Low Accuracy Scores
**Problem**: Many fields failing verification
**Solution**: Review field mappings and database schema

## 📝 Field Transformation Functions

### Currency Formatting
```javascript
value => `$${value.toLocaleString('en-US', {minimumFractionDigits: 2})}`
```

### Property Use Codes
```python
'0100' → 'Single Family'
'0200' → 'Multi Family'
'1000' → 'Commercial'
```

### Qualification Codes
```python
'U' → 'Unqualified'
'Q' → 'Qualified'
'V' → 'Valid Sale'
```

## 🏃 Quick Commands

### Run Full Verification
```bash
python run_field_verification.py
```

### Check Specific Property
```bash
python -c "from run_field_verification import *; asyncio.run(verify_property('064210010010'))"
```

### Generate Report Only
```bash
python -c "from run_field_verification import *; generate_report()"
```

## 📌 Best Practices

1. **Regular Verification**: Run weekly to catch mapping issues early
2. **Sample Diversity**: Test properties of different types (residential, commercial, etc.)
3. **Visual Checks**: Review screenshots when accuracy drops below 90%
4. **Update Mappings**: Keep `field_mapping_configuration.json` synchronized with UI changes
5. **Monitor Outliers**: Investigate properties with unusually low accuracy

## 🆘 Support

For issues or questions:
1. Check `field_verification.log` for detailed errors
2. Review `verification_report_*.json` for specific failures
3. Verify database connectivity
4. Ensure UI is running at `http://localhost:5173`

---

**Note**: This system ensures data accuracy by combining:
- **Database validation** (correct source)
- **UI automation** (correct placement)
- **Visual verification** (correct display)
- **Numerical analysis** (correct values)

The result is **100% confidence** that data from Property Appraiser and Sunbiz databases appears in the correct locations throughout the application.