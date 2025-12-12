# Florida NAL (Name-Address-Legal) Column Reference

## Critical Column Mappings (NAL -> florida_parcels table)

### Identifiers
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| CO_NO | county | INT | County code (11-77) |
| PARCEL_ID | parcel_id | TEXT | Primary parcel identifier |
| ASMNT_YR | year | INT | Assessment year |
| ALT_KEY | alt_key | TEXT | Alternative key |
| STATE_PAR_ID | state_par_id | TEXT | State parcel ID |

### Physical Address
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| PHY_ADDR1 | phy_addr1 | TEXT | Street address |
| PHY_ADDR2 | phy_addr2 | TEXT | Unit/Suite |
| PHY_CITY | phy_city | TEXT | City |
| PHY_ZIPCD | phy_zipcd | TEXT | ZIP code |

### Owner Information
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| OWN_NAME | owner_name | TEXT | Owner name |
| OWN_ADDR1 | owner_addr1 | TEXT | Mailing address 1 |
| OWN_ADDR2 | owner_addr2 | TEXT | Mailing address 2 |
| OWN_CITY | owner_city | TEXT | Owner city |
| OWN_STATE | owner_state | TEXT(2) | State (truncate to 2 chars!) |
| OWN_ZIPCD | owner_zip | TEXT | Owner ZIP |

### Property Values
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| JV | just_value | BIGINT | Just/Market value |
| AV_SD | assessed_value | BIGINT | Assessed value |
| TV_SD | taxable_value | BIGINT | Taxable value |
| LND_VAL | land_value | BIGINT | Land value |

### Building Characteristics
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| ACT_YR_BLT | year_built | INT | Actual year built |
| EFF_YR_BLT | eff_year_built | INT | Effective year built |
| TOT_LVG_AREA | total_living_area | INT | Living area sqft |
| LND_SQFOOT | land_sqft | BIGINT | Land square footage |
| DOR_UC | property_use | TEXT | Property use code |

### Sale Information
| NAL Column | DB Column | Type | Description |
|------------|-----------|------|-------------|
| SALE_PRC1 | sale_price | BIGINT | Most recent sale price |
| SALE_YR1 | sale_yr1 | INT | Sale year |
| SALE_MO1 | sale_mo1 | INT | Sale month |
| sale_date | sale_date | DATE | Constructed: YYYY-MM-01 or NULL |

## County Codes (DOR Standard)
11=ALACHUA, 12=BAKER, 13=BAY, 14=BRADFORD, 15=BREVARD,
16=BROWARD, 17=CALHOUN, 18=CHARLOTTE, 19=CITRUS, 20=CLAY,
21=COLLIER, 22=COLUMBIA, 23=MIAMI-DADE, 24=DESOTO, 25=DIXIE,
26=DUVAL, 27=ESCAMBIA, 28=FLAGLER, 29=FRANKLIN, 30=GADSDEN,
31=GILCHRIST, 32=GLADES, 33=GULF, 34=HAMILTON, 35=HARDEE,
36=HENDRY, 37=HERNANDO, 38=HIGHLANDS, 39=HILLSBOROUGH, 40=HOLMES,
41=INDIAN RIVER, 42=JACKSON, 43=JEFFERSON, 44=LAFAYETTE, 45=LAKE,
46=LEE, 47=LEON, 48=LEVY, 49=LIBERTY, 50=MADISON,
51=MANATEE, 52=MARION, 53=MARTIN, 54=MONROE, 55=NASSAU,
56=OKALOOSA, 57=OKEECHOBEE, 58=ORANGE, 59=OSCEOLA, 60=PALM BEACH,
61=PASCO, 62=PINELLAS, 63=POLK, 64=PUTNAM, 65=ST. JOHNS,
66=ST. LUCIE, 67=SANTA ROSA, 68=SARASOTA, 69=SEMINOLE, 70=SUMTER,
71=SUWANNEE, 72=TAYLOR, 73=UNION, 74=VOLUSIA, 75=WAKULLA,
76=WALTON, 77=WASHINGTON

## Common Errors and Fixes
- owner_state too long: Truncate "FLORIDA" -> "FL"
- sale_date empty string: Use NULL instead
- NaN values: Convert to NULL for numeric, empty string for text
