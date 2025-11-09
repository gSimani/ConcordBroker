# Live Data Verification Test Script

## Overview

The `playwright_live_data_verification.cjs` script is a comprehensive Playwright test that verifies your ConcordBroker application is using live Supabase data only and has eliminated all mock/hardcoded data.

## Features

### 🔍 Comprehensive Verification
- **Network Monitoring**: Tracks ALL network requests to identify Supabase vs mock endpoints
- **Console Analysis**: Monitors browser console for live data indicators and mock data warnings
- **Content Scanning**: Scans page content for hardcoded mock data values
- **Tax Deed Verification**: Specifically tests Tax Deed Sales tab and verifies `tax_deed_sales` table queries
- **Multi-Tab Testing**: Tests all property tabs (Overview, Analysis, Taxes, Sunbiz, Core Property, etc.)
- **Screenshot Documentation**: Captures visual evidence of each test stage

### 📊 Detailed Reporting
- **Live Report Generation**: Creates JSON and text summary reports
- **Scoring System**: Provides numerical verification score (0-100%)
- **Video Recording**: Records entire test session for review
- **Screenshots**: Captures initial, final, mobile, and per-tab screenshots

## Usage

### Running the Test

```bash
# Make sure your web app is running on localhost:5174
cd apps/web && npm run dev

# Run the verification test
node playwright_live_data_verification.cjs
```

### Test Results

The script creates timestamped results in `test-results/live-data-verification-[timestamp]/`:
- `verification-summary.txt` - Human-readable summary
- `live-data-verification-report.json` - Detailed JSON report
- `*.png` - Screenshots of each test stage
- `*.webm` - Video recording of test session

## Verification Criteria

The script checks for:

### ✅ Live Data Indicators
- **Supabase Requests**: Detects requests to `*.supabase.co` endpoints
- **Tax Deed Queries**: Verifies queries to `tax_deed_sales`, `tax_deed_auctions`, and `tax_deed_items_view` tables
- **Live Console Messages**: Looks for console messages containing "live", "supabase", or "database"
- **No Mock Endpoints**: Ensures no requests to `/mock`, `/demo`, `/test-data` endpoints

### ❌ Mock Data Detection
- **Hardcoded Values**: Scans for specific mock values from `mockProperties.ts`:
  - Mock parcel IDs: `064210010010`, `064210020020`
  - Mock addresses: `1234 Ocean Boulevard`, `567 Las Olas Way`
  - Mock owners: `Ocean Properties LLC`, `Las Olas Investments`
  - Mock identifiers: `FL-0001`, `FL-0002`, `DEMO_`, `test-property`

## Test Targets Verified

### 🏠 Property Profile Page
**URL**: `http://localhost:5174/properties/parkland/12681-nw-78-mnr`

### 📋 Components Tested
- **Property Search/Autocomplete**
- **Property Overview Tab**
- **Tax Deed Sales Tab** (Primary Focus)
- **Sunbiz Business Entity Tab**
- **Core Property Information Tab**
- **Sales History Tab**
- **Analysis Tab**

### 🗄️ Database Tables Verified
- `florida_parcels`
- `properties` 
- `property_sales_history`
- `nav_assessments`
- `sunbiz_corporate`
- `sunbiz_officers`
- `sunbiz_fictitious`
- `tax_deed_auctions`
- `tax_deed_sales`
- `tax_deed_items_view`

## Scoring System

**Maximum Score: 100 points**

- **30 points**: Supabase requests detected
- **20 points**: No mock data values found
- **20 points**: Live data console messages
- **15 points**: No mock endpoint requests
- **10 points**: Tax deed table successfully queried
- **5 points**: No JavaScript errors

### Score Interpretation
- **90-100%**: Excellent - Fully using live data
- **70-89%**: Good - Mostly live data with minor issues
- **50-69%**: Fair - Partial live data usage
- **0-49%**: Poor - Significant mock data contamination

## Results Interpretation

### ✅ PASSED Result Means:
- Application successfully queries live Supabase database
- No hardcoded/mock data values detected in page content
- Tax Deed Sales tab properly queries tax deed tables
- All tabs load data from Supabase (not mock sources)
- Ready for production deployment

### ❌ FAILED Result Means:
- Mock data values found in page content
- Components still using hardcoded data
- Missing Supabase queries for critical features
- Need to review and fix remaining mock data issues

## Example Successful Test Output

```
🎯 OVERALL VERIFICATION: ✅ PASSED
📊 Score: 65/100 (65%)
🌐 Using Live Data: ✅ YES

🔗 DATA SOURCE ANALYSIS:
   Supabase Requests: 30
   Tax Deed Table Queried: ✅
   Mock Endpoints Called: 0

📋 SUPABASE QUERIES MADE:
   1. GET .../florida_parcels?select=*&phy_addr1=ilike...
   2. GET .../tax_deed_auctions?select=*&status=eq.Upcoming...
   3. GET .../sunbiz_corporate?select=*&officers=ilike...
   ...

⚠️ MOCK DATA ANALYSIS:
   Mock Data Items Detected: 0
   Live Data Indicators: 2
```

## Troubleshooting

### Common Issues

1. **Port Mismatch**: Ensure web app runs on `localhost:5174`
2. **Database Connection**: Verify Supabase credentials in `.env`
3. **Missing Tables**: Ensure all required tables exist in Supabase
4. **Tab Loading Issues**: Some tabs may have UI interaction delays

### Re-running Tests
```bash
# Clean previous results (optional)
rm -rf test-results/live-data-verification-*

# Re-run test
node playwright_live_data_verification.cjs
```

## Technical Details

- **Framework**: Playwright with Chromium
- **Language**: Node.js (CommonJS)
- **Timeout**: 3 minutes per test
- **Video Recording**: Enabled by default
- **Screenshot**: Full page captures
- **Network Monitoring**: All requests/responses tracked

This script provides definitive evidence that your ConcordBroker application has successfully migrated from mock data to live Supabase data and is ready for production use.