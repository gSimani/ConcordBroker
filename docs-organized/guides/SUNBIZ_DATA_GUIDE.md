# Sunbiz Data Setup Guide

## Current Status
✅ **Sunbiz tables created** in Supabase (sunbiz_corporations, sunbiz_fictitious_names, etc.)
✅ **Property data loaded**: 789,879 Broward County properties now in database
⚠️ **Sunbiz data pending**: SFTP has limited public access

## Alternative Data Sources

### Option 1: Direct Search API
The Sunbiz website provides a public search API that can be used programmatically:
- URL: https://search.sunbiz.org/Inquiry/CorporationSearch/
- Can search by entity name, document number, registered agent, etc.
- Returns real-time data

### Option 2: Bulk Download Request
Contact Florida Department of State Division of Corporations:
- Email: corphelp@dos.myflorida.com
- Phone: 850-245-6052
- Request bulk data export for Broward County entities

### Option 3: Web Scraping (Rate Limited)
Use the search.sunbiz.org website with careful rate limiting:
- Search for businesses by ZIP code ranges (Broward: 33004-33394)
- Export results programmatically
- Respect rate limits to avoid blocking

## Data Pipeline Status

### Completed:
1. ✅ 789,879 properties loaded from NAL file
2. ✅ Sunbiz database schema created
3. ✅ Property search working with all data
4. ✅ Autocomplete prioritizes addresses over parcel IDs

### Next Steps:
1. Choose Sunbiz data acquisition method
2. Load business entity data
3. Match businesses to properties using:
   - Owner name matching
   - Address matching
   - Registered agent matching

## Matching Algorithm (Ready to Deploy)
Once Sunbiz data is loaded, the matching will work as follows:

```python
# Match by owner name
SELECT * FROM sunbiz_corporations 
WHERE corporation_name ILIKE '%{property_owner}%'

# Match by address
SELECT * FROM sunbiz_corporations
WHERE principal_address ILIKE '%{property_address}%'

# Create matches
INSERT INTO property_business_matches 
(parcel_id, document_number, match_type, confidence_score)
```

## Quick Commands

### Check property count:
```bash
python verify_property_count.py
```

### Load Sunbiz data (when available):
```bash
python load_all_sunbiz_data.py
```

### Test property search:
Visit http://localhost:5174/properties and search for any address or parcel ID

## Summary
The property data is fully loaded (789,879 properties). The Sunbiz infrastructure is ready. Once you obtain the Sunbiz data through one of the methods above, the system will automatically match businesses to properties for comprehensive business intelligence.