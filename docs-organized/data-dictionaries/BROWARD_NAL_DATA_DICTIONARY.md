# Broward County NAL Data Dictionary

## Overview
The Broward County Name and Address List (NAL) contains 165 columns with property assessment data for tax year 2025. This document describes each column's purpose, data type, and business meaning.

## Core Identification Fields

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **CO_NO** | County Number (16 = Broward) | INTEGER | 16 |
| **PARCEL_ID** | Unique parcel identifier | VARCHAR(30) | "473725000000" |
| **FILE_T** | File type (R = Real Property) | CHAR(1) | "R" |
| **ASMNT_YR** | Assessment year | INTEGER | 2025 |
| **ALT_KEY** | Alternative key identifier | VARCHAR(50) | |
| **STATE_PAR_ID** | State parcel ID | VARCHAR(50) | "C16-000-053-8500-0" |
| **SEQ_NO** | Sequence number | INTEGER | 1 |

## Property Use & Classification

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **DOR_UC** | Department of Revenue use code | VARCHAR(4) | "082" |
| **PA_UC** | Property appraiser use code | VARCHAR(4) | "00" |
| **BAS_STRT** | Basis stratum | VARCHAR(10) | "10" |
| **ATV_STRT** | Active stratum | VARCHAR(10) | |
| **GRP_NO** | Group number | VARCHAR(10) | |
| **SPASS_CD** | Special assessment code | VARCHAR(10) | |

## Valuation Fields (JV = Just Value, AV = Assessed Value, TV = Taxable Value)

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **JV** | Just (market) value | DECIMAL(15,2) | 382300 |
| **JV_CHNG** | Just value change | DECIMAL(15,2) | |
| **JV_CHNG_CD** | Just value change code | VARCHAR(10) | |
| **AV_SD** | Assessed value (school district) | DECIMAL(15,2) | 382300 |
| **AV_NSD** | Assessed value (non-school district) | DECIMAL(15,2) | 382300 |
| **TV_SD** | Taxable value (school district) | DECIMAL(15,2) | 0 |
| **TV_NSD** | Taxable value (non-school district) | DECIMAL(15,2) | 0 |

## Homestead & Special Values

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **JV_HMSTD** | Just value - homestead portion | DECIMAL(15,2) | |
| **AV_HMSTD** | Assessed value - homestead portion | DECIMAL(15,2) | |
| **JV_NON_HMSTD_RESD** | Just value - non-homestead residential | DECIMAL(15,2) | |
| **AV_NON_HMSTD_RESD** | Assessed value - non-homestead residential | DECIMAL(15,2) | |
| **JV_RESD_NON_RESD** | Just value - residential/non-residential | DECIMAL(15,2) | 382300 |
| **AV_RESD_NON_RESD** | Assessed value - residential/non-residential | DECIMAL(15,2) | 382300 |
| **JV_CLASS_USE** | Just value - classified use | DECIMAL(15,2) | |
| **AV_CLASS_USE** | Assessed value - classified use | DECIMAL(15,2) | |

## Conservation & Special Property Types

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **JV_H2O_RECHRGE** | Just value - water recharge lands | DECIMAL(15,2) | |
| **AV_H2O_RECHRGE** | Assessed value - water recharge lands | DECIMAL(15,2) | |
| **JV_CONSRV_LND** | Just value - conservation lands | DECIMAL(15,2) | |
| **AV_CONSRV_LND** | Assessed value - conservation lands | DECIMAL(15,2) | |
| **JV_HIST_COM_PROP** | Just value - historic commercial property | DECIMAL(15,2) | |
| **AV_HIST_COM_PROP** | Assessed value - historic commercial property | DECIMAL(15,2) | |
| **JV_HIST_SIGNF** | Just value - historic significance | DECIMAL(15,2) | |
| **AV_HIST_SIGNF** | Assessed value - historic significance | DECIMAL(15,2) | |
| **JV_WRKNG_WTRFNT** | Just value - working waterfront | DECIMAL(15,2) | |
| **AV_WRKNG_WTRFNT** | Assessed value - working waterfront | DECIMAL(15,2) | |

## Land & Building Information

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **LND_VAL** | Land value | DECIMAL(15,2) | 382300 |
| **LND_UNTS_CD** | Land units code (1=SF, 2=Acres) | INTEGER | 1 |
| **NO_LND_UNTS** | Number of land units | DECIMAL(12,2) | 764605 |
| **LND_SQFOOT** | Land square footage | BIGINT | 317379589 |
| **NCONST_VAL** | New construction value | DECIMAL(15,2) | 0 |
| **DEL_VAL** | Demolition value | DECIMAL(15,2) | 0 |
| **SPEC_FEAT_VAL** | Special features value | DECIMAL(15,2) | |

## Building Characteristics

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **NO_BULDNG** | Number of buildings | INTEGER | |
| **NO_RES_UNTS** | Number of residential units | INTEGER | |
| **TOT_LVG_AREA** | Total living area (sq ft) | INTEGER | |
| **ACT_YR_BLT** | Actual year built | INTEGER | |
| **EFF_YR_BLT** | Effective year built | INTEGER | |
| **IMP_QUAL** | Improvement quality | VARCHAR(10) | |
| **CONST_CLASS** | Construction class | VARCHAR(10) | |
| **DT_LAST_INSPT** | Date of last inspection | VARCHAR(10) | "1220" |

## Owner Information

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **OWN_NAME** | Owner name | VARCHAR(255) | "SOUTH FLORIDA WATER MANAGEMENT" |
| **OWN_ADDR1** | Owner address line 1 | VARCHAR(255) | "PO BOX 24680" |
| **OWN_ADDR2** | Owner address line 2 | VARCHAR(255) | |
| **OWN_CITY** | Owner city | VARCHAR(100) | "WEST PALM BEACH" |
| **OWN_STATE** | Owner state | VARCHAR(50) | "FLORIDA" |
| **OWN_ZIPCD** | Owner ZIP code | VARCHAR(10) | 33416 |
| **OWN_STATE_DOM** | Owner state of domicile | VARCHAR(50) | |

## Fiduciary Information

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **FIDU_NAME** | Fiduciary name | VARCHAR(255) | |
| **FIDU_ADDR1** | Fiduciary address line 1 | VARCHAR(255) | |
| **FIDU_ADDR2** | Fiduciary address line 2 | VARCHAR(255) | |
| **FIDU_CITY** | Fiduciary city | VARCHAR(100) | |
| **FIDU_STATE** | Fiduciary state | VARCHAR(50) | |
| **FIDU_ZIPCD** | Fiduciary ZIP code | VARCHAR(10) | |
| **FIDU_CD** | Fiduciary code | VARCHAR(10) | |

## Physical Address (Property Location)

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **PHY_ADDR1** | Physical address line 1 | VARCHAR(255) | "EVERGLADES" |
| **PHY_ADDR2** | Physical address line 2 | VARCHAR(255) | |
| **PHY_CITY** | Physical city | VARCHAR(100) | "UNINCORPORATED" |
| **PHY_ZIPCD** | Physical ZIP code | VARCHAR(10) | 33327 |

## Sales Information (Two Most Recent Sales)

### Sale 1
| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **MULTI_PAR_SAL1** | Multi-parcel sale flag | VARCHAR(1) | |
| **QUAL_CD1** | Qualification code | VARCHAR(2) | |
| **VI_CD1** | Validity indicator code | VARCHAR(2) | |
| **SALE_PRC1** | Sale price | DECIMAL(15,2) | |
| **SALE_YR1** | Sale year | INTEGER | |
| **SALE_MO1** | Sale month | INTEGER | |
| **OR_BOOK1** | Official record book | VARCHAR(10) | |
| **OR_PAGE1** | Official record page | VARCHAR(10) | |
| **CLERK_NO1** | Clerk number | VARCHAR(20) | |
| **SAL_CHNG_CD1** | Sale change code | VARCHAR(10) | |

### Sale 2
| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **MULTI_PAR_SAL2** | Multi-parcel sale flag | VARCHAR(1) | |
| **QUAL_CD2** | Qualification code | VARCHAR(2) | |
| **VI_CD2** | Validity indicator code | VARCHAR(2) | |
| **SALE_PRC2** | Sale price | DECIMAL(15,2) | |
| **SALE_YR2** | Sale year | INTEGER | |
| **SALE_MO2** | Sale month | INTEGER | |
| **OR_BOOK2** | Official record book | VARCHAR(10) | |
| **OR_PAGE2** | Official record page | VARCHAR(10) | |
| **CLERK_NO2** | Clerk number | VARCHAR(20) | |
| **SAL_CHNG_CD2** | Sale change code | VARCHAR(10) | |

## Geographic & Legal Information

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **S_LEGAL** | Legal description | TEXT | "47-37" |
| **TWN** | Township | VARCHAR(10) | "47S" |
| **RNG** | Range | VARCHAR(10) | "37E" |
| **SEC** | Section | INTEGER | 25 |
| **CENSUS_BK** | Census block | VARCHAR(20) | "120119800001" |
| **MKT_AR** | Market area | VARCHAR(10) | |
| **NBRHD_CD** | Neighborhood code | VARCHAR(10) | |
| **TAX_AUTH_CD** | Tax authority code | VARCHAR(10) | "0012" |
| **DISTR_CD** | District code | VARCHAR(10) | |
| **DISTR_YR** | District year | INTEGER | |

## Homestead Transfer Information

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **ASS_TRNSFR_FG** | Assessment transfer flag | VARCHAR(1) | |
| **PREV_HMSTD_OWN** | Previous homestead owner | VARCHAR(255) | |
| **ASS_DIF_TRNS** | Assessment difference transfer | DECIMAL(15,2) | |
| **CONO_PRV_HM** | County number previous homestead | INTEGER | |
| **PARCEL_ID_PRV_HMSTD** | Parcel ID previous homestead | VARCHAR(30) | |
| **YR_VAL_TRNSF** | Year value transferred | INTEGER | |

## Exemptions (46 Different Types)

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **EXMPT_01** | Exemption type 01 (Homestead) | DECIMAL(15,2) | |
| **EXMPT_02** | Exemption type 02 (Additional Homestead) | DECIMAL(15,2) | |
| **EXMPT_03** | Exemption type 03 (Senior) | DECIMAL(15,2) | |
| **EXMPT_04** | Exemption type 04 (Widow/Widower) | DECIMAL(15,2) | |
| **EXMPT_05** | Exemption type 05 (Disability) | DECIMAL(15,2) | |
| **EXMPT_06** | Exemption type 06 (Veteran) | DECIMAL(15,2) | |
| **EXMPT_07** | Exemption type 07 (Religious) | DECIMAL(15,2) | |
| **EXMPT_08** | Exemption type 08 (Educational) | DECIMAL(15,2) | |
| **EXMPT_09** | Exemption type 09 (Charitable) | DECIMAL(15,2) | |
| **EXMPT_10** | Exemption type 10 (Government) | DECIMAL(15,2) | |
| **EXMPT_11-46** | Various other exemptions | DECIMAL(15,2) | |
| **EXMPT_80** | Special exemption 80 | DECIMAL(15,2) | 382300 |
| **EXMPT_81** | Special exemption 81 | DECIMAL(15,2) | |
| **EXMPT_82** | Special exemption 82 | DECIMAL(15,2) | |

## Application & Circuit Court

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **APP_STAT** | Application status | VARCHAR(10) | |
| **CO_APP_STAT** | County application status | VARCHAR(10) | "99" |
| **SPC_CIR_CD** | Special circuit code | VARCHAR(10) | |
| **SPC_CIR_YR** | Special circuit year | INTEGER | |
| **SPC_CIR_TXT** | Special circuit text | TEXT | |

## Additional Flags & Metadata

| Column | Description | Data Type | Example |
|--------|-------------|-----------|---------|
| **PAR_SPLT** | Parcel split indicator | VARCHAR(1) | |
| **PUBLIC_LND** | Public land indicator | VARCHAR(1) | "W" or "S" |
| **RS_ID** | Real estate ID | VARCHAR(20) | "2B6D" |
| **MP_ID** | Map ID | VARCHAR(20) | "00083784" |

## Key Business Rules

### Use Codes (DOR_UC)
- **000-009**: Residential (single family)
- **010-099**: Agricultural/Rural
- **100-399**: Commercial
- **400-499**: Industrial
- **500-599**: Institutional (schools, hospitals)
- **600-699**: Government
- **700-899**: Miscellaneous
- **900-999**: Non-agricultural acreage

### Qualification Codes (QUAL_CD)
- **Q**: Qualified sale (arm's length)
- **U**: Unqualified sale
- **I**: Insufficient information

### Land Unit Codes (LND_UNTS_CD)
- **1**: Square feet
- **2**: Acres
- **3**: Units
- **4**: Front feet

### Public Land Indicators (PUBLIC_LND)
- **W**: Water management district
- **S**: State owned
- **C**: County owned
- **M**: Municipal owned

## Important Notes

1. **Values**: All monetary values are in dollars without cents (implied .00)
2. **Dates**: Format MMYY (e.g., "1220" = December 2020)
3. **Exemptions**: EXMPT_80 typically represents total exempt value for government properties
4. **Null Values**: Empty fields indicate not applicable or no data
5. **County Number**: Always 16 for Broward County

## Database Optimization Recommendations

### Primary Indexes
- PARCEL_ID (unique)
- STATE_PAR_ID
- OWN_NAME
- PHY_CITY
- JV (for value searches)

### Composite Indexes
- (PHY_CITY, DOR_UC) - For city/use type queries
- (SALE_YR1, SALE_PRC1) - For sales analysis
- (OWN_NAME, JV) - For owner portfolio analysis

### Frequently Queried Fields
1. Property identification: PARCEL_ID, PHY_ADDR1, PHY_CITY
2. Valuation: JV, TV_SD, TV_NSD, LND_VAL
3. Owner info: OWN_NAME, OWN_ADDR1, OWN_CITY
4. Property characteristics: DOR_UC, TOT_LVG_AREA, ACT_YR_BLT
5. Sales data: SALE_PRC1, SALE_YR1, QUAL_CD1

### Data Types for Supabase
```sql
CREATE TABLE broward_nal (
    -- Core fields
    co_no INTEGER DEFAULT 16,
    parcel_id VARCHAR(30) PRIMARY KEY,
    file_t CHAR(1) DEFAULT 'R',
    asmnt_yr INTEGER NOT NULL,
    
    -- Values
    jv DECIMAL(15,2),
    av_sd DECIMAL(15,2),
    tv_sd DECIMAL(15,2),
    lnd_val DECIMAL(15,2),
    
    -- Owner
    own_name VARCHAR(255),
    own_addr1 VARCHAR(255),
    own_city VARCHAR(100),
    own_state VARCHAR(50),
    own_zipcd VARCHAR(10),
    
    -- Property location
    phy_addr1 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_zipcd VARCHAR(10),
    
    -- Characteristics
    dor_uc VARCHAR(4),
    tot_lvg_area INTEGER,
    act_yr_blt INTEGER,
    lnd_sqfoot BIGINT,
    
    -- Sales
    sale_prc1 DECIMAL(15,2),
    sale_yr1 INTEGER,
    qual_cd1 VARCHAR(2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```