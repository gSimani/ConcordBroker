# Florida DOR Code to USE/SUBUSE Mappings

## Overview
This document maps Florida Department of Revenue (DOR) property use codes (00-99) to the standardized USE/SUBUSE taxonomy used in ConcordBroker.

## Mapping Strategy

### Main Categories (Level 1)
- **RESIDENTIAL** - Residential properties (00-09)
- **COMMERCIAL** - Commercial properties (10-39)
- **INDUSTRIAL** - Industrial properties (40-49)
- **AGRICULTURAL** - Agricultural properties (50-69)
- **INSTITUTIONAL** - Institutional properties (70-79)
- **GOVERNMENT** - Government-owned properties (80-89)
- **MISC** - Miscellaneous properties (90-97)
- **CENTRAL** - Centrally assessed properties (98)
- **NONAG** - Non-agricultural acreage (99)

### Confidence Scoring
- **0.95** - High confidence (specific, well-defined codes)
- **0.90** - Good confidence (clear category)
- **0.85** - Medium confidence (general category)
- **0.80** - Fair confidence (broad category)
- **0.70** - Low confidence (vacant/unclear)

## Detailed Mappings

### RESIDENTIAL (00-09) - Confidence: 0.80-0.95

| DOR Code | DOR Label | Main Code | Subuse Code | Confidence | Notes |
|----------|-----------|-----------|-------------|------------|-------|
| 00 | Vacant residential | RESIDENTIAL | NULL | 0.85 | May have improvements |
| 01 | Single family | RESIDENTIAL | NULL | 0.95 | Most common residential |
| 02 | Mobile homes | RESIDENTIAL | NULL | 0.90 | Manufactured housing |
| 03 | Multifamily (10+) | RESIDENTIAL | NULL | 0.90 | 10+ units |
| 04 | Condominium | RESIDENTIAL | CONDOMINIUM | 0.95 | Specific subuse |
| 05 | Cooperative | RESIDENTIAL | NULL | 0.85 | Less common |
| 06 | Retirement homes (non-exempt) | RESIDENTIAL | NULL | 0.85 | Specialized |
| 07 | Misc. residential | RESIDENTIAL | NULL | 0.80 | Catch-all category |
| 08 | Multifamily (<10) | RESIDENTIAL | NULL | 0.90 | 2-9 units |
| 09 | Residential common areas | RESIDENTIAL | NULL | 0.85 | HOA/Condo common |

**Text Code Mappings:**
- `SFR`, `SINGLE FAMILY`, `RESIDENTIAL` → Code 01
- `CONDO`, `CONDOMINIUM` → Code 04
- `MOBILE HOME`, `MOBILE` → Code 02
- `MULTI-FAMILY`, `MULTIFAMILY`, `APARTMENT` → Code 03
- `VACANT RESIDENTIAL` → Code 00

### COMMERCIAL (10-39) - Confidence: 0.70-0.95

| DOR Code | DOR Label | Main Code | Subuse Code | Confidence | Notes |
|----------|-----------|-----------|-------------|------------|-------|
| 10 | Vacant commercial | COMMERCIAL | NULL | 0.70 | Undeveloped |
| 11 | Stores, one story | COMMERCIAL | RETAIL_STORE | 0.95 | Common retail |
| 12 | Mixed-use (store+office/residential) | COMMERCIAL | RETAIL_STORE | 0.85 | Multi-purpose |
| 13 | Department stores | COMMERCIAL | RETAIL_STORE | 0.95 | Large retail |
| 14 | Supermarkets | COMMERCIAL | RETAIL_STORE | 0.95 | Grocery stores |
| 15 | Regional shopping center | COMMERCIAL | SHOPPING_CENTER | 0.95 | Malls |
| 16 | Community shopping center | COMMERCIAL | SHOPPING_CENTER | 0.95 | Strip centers |
| 17 | Office, one story | COMMERCIAL | OFFICE | 0.95 | Single-story |
| 18 | Office, multi-story | COMMERCIAL | OFFICE | 0.95 | Multi-story |
| 19 | Professional service bldg | COMMERCIAL | OFFICE | 0.95 | Professional |
| 20 | Airports/terminals/marinas | COMMERCIAL | NULL | 0.85 | Transportation |
| 21 | Restaurants | COMMERCIAL | RESTAURANT | 0.95 | Food service |
| 22 | Drive-in restaurants | COMMERCIAL | RESTAURANT | 0.95 | Fast food |
| 23 | Financial institutions | COMMERCIAL | NULL | 0.85 | Banks |
| 24 | Insurance offices | COMMERCIAL | OFFICE | 0.85 | Insurance |
| 25 | Repair service shops | COMMERCIAL | NULL | 0.85 | Service |
| 26 | Service stations | COMMERCIAL | NULL | 0.85 | Gas stations |
| 27 | Auto sales/repair/storage | COMMERCIAL | AUTO_SALES_SERVICE | 0.90 | Automotive |
| 28 | Parking lots & mobile home parks | COMMERCIAL | NULL | 0.85 | Parking/storage |
| 29 | Wholesale outlets | COMMERCIAL | NULL | 0.85 | Wholesale |
| 30 | Florist/greenhouses | COMMERCIAL | NULL | 0.85 | Horticultural |
| 31 | Drive-in theaters/open stadiums | COMMERCIAL | NULL | 0.85 | Entertainment |
| 32 | Enclosed theaters/auditoriums | COMMERCIAL | NULL | 0.85 | Entertainment |
| 33 | Bars/nightclubs | COMMERCIAL | NULL | 0.85 | Nightlife |
| 34 | Bowling/skating/arenas | COMMERCIAL | NULL | 0.85 | Recreation |
| 35 | Tourist attractions/fairs | COMMERCIAL | NULL | 0.85 | Tourism |
| 36 | Camps | COMMERCIAL | CAMP | 0.85 | Recreational camps |
| 37 | Race tracks | COMMERCIAL | RACETRACK | 0.90 | Auto/horse racing |
| 38 | Golf/driving ranges | COMMERCIAL | GOLF | 0.90 | Golf facilities |
| 39 | Hotels/motels | COMMERCIAL | HOTEL | 0.95 | Lodging |

**Text Code Mappings:**
- `COM`, `COMMERCIAL`, `RETAIL` → Code 11
- `OFFICE` → Code 17
- `HOTEL`, `MOTEL` → Code 39
- `RESTAURANT` → Code 21
- `VAC`, `VACANT` → Code 10

### INDUSTRIAL (40-49) - Confidence: 0.70-0.90

| DOR Code | DOR Label | Main Code | Subuse Code | Confidence | Notes |
|----------|-----------|-----------|-------------|------------|-------|
| 40 | Vacant industrial | INDUSTRIAL | NULL | 0.70 | Undeveloped |
| 41 | Light manufacturing/printing | INDUSTRIAL | LIGHT_MANUFACTURING | 0.90 | Light industry |
| 42 | Heavy industrial/plants | INDUSTRIAL | HEAVY_INDUSTRY | 0.90 | Heavy industry |
| 43 | Lumber/sawmills | INDUSTRIAL | LUMBER | 0.90 | Wood processing |
| 44 | Packing plants | INDUSTRIAL | PACKING_PLANT | 0.90 | Food packing |
| 45 | Canneries/brewers/bottlers | INDUSTRIAL | NULL | 0.90 | Food/beverage |
| 46 | Other food processing | INDUSTRIAL | NULL | 0.90 | Food processing |
| 47 | Mineral/refining/cement | INDUSTRIAL | NULL | 0.90 | Heavy processing |
| 48 | Warehousing/distribution/terminals | INDUSTRIAL | WAREHOUSE | 0.90 | Distribution |
| 49 | Open storage/junk/fuel yards | INDUSTRIAL | NULL | 0.90 | Storage |

**Text Code Mappings:**
- `IND`, `INDUSTRIAL` → Code 41
- `WAREHOUSE` → Code 48

### AGRICULTURAL (50-69) - Confidence: 0.90

| DOR Code | DOR Label | Main Code | Subuse Code | Confidence | Notes |
|----------|-----------|-----------|-------------|------------|-------|
| 50 | Improved agricultural | AGRICULTURAL | NULL | 0.90 | General ag |
| 51 | Cropland Class I | AGRICULTURAL | AG_CROPLAND | 0.90 | Best cropland |
| 52 | Cropland Class II | AGRICULTURAL | AG_CROPLAND | 0.90 | Good cropland |
| 53 | Cropland Class III | AGRICULTURAL | AG_CROPLAND | 0.90 | Fair cropland |
| 54 | Timberland SI ≥90 | AGRICULTURAL | AG_TIMBER | 0.90 | Best timberland |
| 55 | Timberland SI 80–89 | AGRICULTURAL | AG_TIMBER | 0.90 | Good timberland |
| 56 | Timberland SI 70–79 | AGRICULTURAL | AG_TIMBER | 0.90 | Fair timberland |
| 57 | Timberland SI 60–69 | AGRICULTURAL | AG_TIMBER | 0.90 | Fair timberland |
| 58 | Timberland SI 50–59 | AGRICULTURAL | AG_TIMBER | 0.90 | Poor timberland |
| 59 | Timberland (other) | AGRICULTURAL | AG_TIMBER | 0.90 | Other timberland |
| 60 | Grazing Class I | AGRICULTURAL | AG_GRAZING | 0.90 | Best grazing |
| 61 | Grazing Class II | AGRICULTURAL | AG_GRAZING | 0.90 | Good grazing |
| 62 | Grazing Class III | AGRICULTURAL | AG_GRAZING | 0.90 | Fair grazing |
| 63 | Grazing Class IV | AGRICULTURAL | AG_GRAZING | 0.90 | Fair grazing |
| 64 | Grazing Class V | AGRICULTURAL | AG_GRAZING | 0.90 | Poor grazing |
| 65 | Grazing Class VI | AGRICULTURAL | AG_GRAZING | 0.90 | Poor grazing |
| 66 | Orchards/Groves/Citrus | AGRICULTURAL | NULL | 0.90 | Fruit production |
| 67 | Poultry/bees/fish/rabbits | AGRICULTURAL | NULL | 0.90 | Livestock |
| 68 | Dairies/feed lots | AGRICULTURAL | NULL | 0.90 | Dairy/cattle |
| 69 | Ornamentals/misc ag | AGRICULTURAL | NULL | 0.90 | Other agriculture |

**Text Code Mappings:**
- `AGR`, `AGRICULTURAL`, `FARM` → Code 50

### INSTITUTIONAL (70-79) - Confidence: 0.70-0.90

| DOR Code | DOR Label | Main Code | Subuse Code | Confidence | Notes |
|----------|-----------|-----------|-------------|------------|-------|
| 70 | Vacant institutional | INSTITUTIONAL | NULL | 0.70 | Undeveloped |
| 71 | Churches | INSTITUTIONAL | RELIGIOUS | 0.90 | Religious facilities |
| 72 | Private schools/colleges | INSTITUTIONAL | SCHOOL_PRIVATE | 0.90 | Private education |
| 73 | Private hospitals | INSTITUTIONAL | PRIVATE_HOSPITAL | 0.90 | Private healthcare |
| 74 | Homes for the aged | INSTITUTIONAL | NULL | 0.90 | Senior care |
| 75 | Orphanages/charitable | INSTITUTIONAL | NULL | 0.90 | Charitable |
| 76 | Mortuaries/cemeteries | INSTITUTIONAL | NULL | 0.90 | Funeral services |
| 77 | Clubs/lodges | INSTITUTIONAL | NULL | 0.90 | Private clubs |
| 78 | Sanitariums/rest homes | INSTITUTIONAL | NULL | 0.90 | Healthcare |
| 79 | Cultural facilities | INSTITUTIONAL | NULL | 0.90 | Museums/libraries |

### GOVERNMENT (80-89) - Confidence: 0.95

| DOR Code | DOR Label | Main Code | Subuse Code | Confidence | Notes |
|----------|-----------|-----------|-------------|------------|-------|
| 80 | Vacant governmental | GOVERNMENT | NULL | 0.95 | Gov-owned vacant |
| 81 | Military | GOVERNMENT | NULL | 0.95 | Military facilities |
| 82 | Forests/parks/recreation | GOVERNMENT | NULL | 0.95 | Public recreation |
| 83 | Public county schools | GOVERNMENT | PUBLIC_SCHOOL | 0.95 | K-12 schools |
| 84 | Public colleges | GOVERNMENT | PUBLIC_COLLEGE | 0.95 | Higher education |
| 85 | Public hospitals | GOVERNMENT | PUBLIC_HOSPITAL | 0.95 | Public healthcare |
| 86 | County properties (other) | GOVERNMENT | NULL | 0.95 | County facilities |
| 87 | State properties (other) | GOVERNMENT | NULL | 0.95 | State facilities |
| 88 | Federal properties (other) | GOVERNMENT | NULL | 0.95 | Federal facilities |
| 89 | Municipal properties (other) | GOVERNMENT | NULL | 0.95 | City facilities |

### MISCELLANEOUS (90-99) - Confidence: 0.85

| DOR Code | DOR Label | Main Code | Subuse Code | Confidence | Notes |
|----------|-----------|-----------|-------------|------------|-------|
| 90 | Government leasehold interest | MISC | NULL | 0.85 | Leased from gov |
| 91 | Utilities/rail/water/sewer | MISC | NULL | 0.85 | Infrastructure |
| 92 | Mining/petroleum/gas lands | MISC | NULL | 0.85 | Extractive |
| 93 | Subsurface rights | MISC | NULL | 0.85 | Mineral rights |
| 94 | Right-of-way | MISC | NULL | 0.85 | Easements |
| 95 | Rivers/lakes/submerged | MISC | NULL | 0.85 | Water bodies |
| 96 | Waste/disposal/drainage/marsh | MISC | NULL | 0.85 | Environmental |
| 97 | Outdoor recreation/high-water recharge | MISC | NULL | 0.85 | Conservation |
| 98 | Centrally assessed | CENTRAL | NULL | 0.85 | Railroad/utilities |
| 99 | Non-agricultural acreage | NONAG | NULL | 0.85 | Vacant acreage |

**Text Code Mappings:**
- `VACANT LAND` → Code 10 (or 99 for large acreage)

## Special Cases

### Code Normalization
The migration handles various code formats:
- **1-digit:** `'1'` → `01`
- **2-digit:** `'01'` → `01`
- **3-digit:** `'001'` → `01`
- **Text:** `'SFR'` → `01`

### NULL Handling
- `property_use IS NULL` → No assignment created
- `property_use = ''` → No assignment created
- Invalid codes → No assignment created (needs manual review)

### SUBUSE Assignment Rules
1. **Explicit mapping:** DOR code directly maps to SUBUSE (e.g., 04 → CONDOMINIUM)
2. **NULL SUBUSE:** When no specific subuse is applicable
3. **Future expansion:** Additional SUBUSE categories can be added to taxonomy

## Coverage Expectations

### By Category
| Category | Expected % | Estimated Count |
|----------|-----------|-----------------|
| RESIDENTIAL | 65-70% | 900K-1M |
| COMMERCIAL | 15-20% | 210K-280K |
| INDUSTRIAL | 2-3% | 30K-40K |
| AGRICULTURAL | 5-7% | 70K-100K |
| INSTITUTIONAL | 1-2% | 15K-30K |
| GOVERNMENT | 1-2% | 15K-30K |
| MISC/CENTRAL/NONAG | 2-3% | 30K-40K |

### By Confidence
| Confidence | Expected % | Quality |
|-----------|-----------|---------|
| 0.95 | ~40% | Excellent - High certainty |
| 0.90 | ~30% | Good - Clear category |
| 0.85 | ~25% | Medium - General category |
| 0.80 | ~4% | Fair - Broad category |
| 0.70 | ~1% | Low - Vacant/unclear |

## Data Quality

### High Quality Indicators
- ✅ Confidence ≥ 0.90
- ✅ Specific SUBUSE assigned
- ✅ Matches building characteristics (if available)
- ✅ Standard DOR code format

### Review Recommended
- ⚠️ Confidence < 0.70
- ⚠️ NULL SUBUSE for detailed categories
- ⚠️ Conflicts with building data
- ⚠️ Unusual code patterns

## References

### Source Documents
- **PDR:** FL-USETAX-PDR-001 v1.0.0
- **DOR Manual:** Florida Department of Revenue Land Use Codes
- **Taxonomy:** ConcordBroker USE/SUBUSE hierarchy

### Related Files
- `20251101_m0_seed_dor_uses.sql` - Full DOR code reference
- `20251101_m0_schema_adapted.sql` - Taxonomy schema
- `20251103_standardize_null_property_use.sql` - Migration implementation

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-03
**Maintained By:** ConcordBroker Data Team
