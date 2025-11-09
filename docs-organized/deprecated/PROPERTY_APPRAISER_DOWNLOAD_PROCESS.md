# Florida Property Appraiser Data Download Process

## Current Status

After exploring the Florida Revenue website (https://floridarevenue.com/property/Pages/DataPortal.aspx), I found that:

1. **NAL Files Not Directly Accessible**: The NAL (Name, Address, Legal) files are not directly accessible via standard HTTP URLs
2. **Website Structure**: The site uses SharePoint/ASP.NET which may require authentication or special navigation
3. **No Direct FTP Links**: Unlike the Sunbiz database, there are no obvious FTP folder structures exposed

## Attempted Approaches

### 1. Direct URL Patterns (Failed)
- Tried multiple URL patterns for NAL files
- All returned 404 errors
- Patterns tested:
  - `https://floridarevenue.com/property/Documents/DataPortal/NAL/2025/`
  - `https://floridarevenue.com/FTP/NAL/2025/`
  - `https://floridarevenue.com/property/DataPortal/NAL/2025P/`

### 2. Web Scraping (Limited Success)
- Found the main data portal page
- Could not locate specific NAL download links
- Page contains reports and summaries but not raw data files

## Alternative Data Sources

### Option 1: County Property Appraiser Websites
Each Florida county has its own property appraiser website with downloadable data:

#### Major Counties:
- **Broward**: https://web.bcpa.net/
- **Miami-Dade**: https://www.miamidade.gov/pa/
- **Palm Beach**: https://www.pbcgov.com/papa/
- **Orange**: https://www.ocpafl.org/
- **Hillsborough**: https://www.hcpafl.org/

### Option 2: Florida Geographic Data Library (FGDL)
- URL: https://www.fgdl.org/
- Provides GIS and property data for Florida
- May have NAL or similar datasets

### Option 3: Direct County FTP Sites
Some counties provide direct FTP access:
- Example: ftp://sdrftp03.dor.state.fl.us/

## Recommended Next Steps

1. **Contact Florida Department of Revenue**
   - Phone: 850-617-8300
   - Email: Use their contact form
   - Request direct access to NAL data files

2. **Use County-Specific Downloads**
   - Focus on major counties first (Broward, Miami-Dade, Palm Beach)
   - Each county typically provides:
     - Property rolls
     - Sales data
     - Owner information
     - Assessment data

3. **Alternative Data Format**
   - Consider using CAMA (Computer Assisted Mass Appraisal) data
   - Available in different formats (DBF, CSV, TXT)

## Script for County-Level Downloads

I can create scripts to download from individual county property appraiser sites if you prefer this approach. This would give us:
- More current data (updated more frequently)
- Direct access without authentication issues
- County-specific formatting that may be easier to process

## Data Storage Structure

```
C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\
├── BROWARD\
│   ├── property_roll.csv
│   ├── sales_data.csv
│   └── owner_info.csv
├── MIAMI_DADE\
│   └── ...
├── PALM_BEACH\
│   └── ...
└── [Other Counties]\
```

## Conclusion

The Florida Revenue centralized NAL files appear to require special access or authentication. The most practical approach is to:

1. **Download from individual county property appraiser websites** - More reliable and accessible
2. **Use available public datasets** - Many counties provide free downloads
3. **Contact Florida DOR for bulk access** - If you need statewide data

Would you like me to proceed with downloading data from specific county property appraiser websites instead?