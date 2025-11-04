# Comprehensive Supabase Database Audit Report

**Generated:** 2025-10-31 13:16:34
**Database:** aws-1-us-east-1.pooler.supabase.com
**Schema:** public

---

## 🎯 Executive Summary


### Database Overview
- **Total Tables:** 115
- **Total Records:** 29,104,742
- **Database Size:** 45 GB

### Critical Data Status
- **Florida Properties:** 10,304,043 / 9,700,000 expected
- **Counties Covered:** 73 / 67 expected
- **Sales History Records:** 637,890
- **Sunbiz Corporate Records:** 2,030,912
- **Sunbiz Entity Records:** 15,013,088

### Health Score: 104.9%


### ✅ Do we have the full Florida property database? **YES**


### Major Findings

- ⚠️ **agent_activity_logs**: Empty table (0 records)
- ⚠️ **agent_config**: Empty table (0 records)
- ⚠️ **agent_lion_analyses**: Empty table (0 records)
- ⚠️ **agent_lion_conversations**: Empty table (0 records)
- ⚠️ **agent_notifications**: Empty table (0 records)
- ⚠️ **concordbroker_docs**: Empty table (0 records)
- ⚠️ **data_source_jobs**: Empty table (0 records)
- ⚠️ **data_source_monitor**: Empty table (0 records)
- ⚠️ **document_search_sessions**: Empty table (0 records)
- ⚠️ **entity_relationships**: Empty table (0 records)
- ⚠️ **entity_search_cache**: Empty table (0 records)
- ⚠️ **file_registry**: Empty table (0 records)
- ⚠️ **fl_nav_assessment_detail**: Empty table (0 records)
- ⚠️ **fl_nav_parcel_summary**: Empty table (0 records)
- ⚠️ **fl_sdf_sales**: Empty table (0 records)
- ⚠️ **fl_tpp_accounts**: Empty table (0 records)
- ⚠️ **florida_business_activities**: Empty table (0 records)
- ⚠️ **florida_entities_staging**: Empty table (0 records)
- ⚠️ **florida_raw_records**: Empty table (0 records)
- ⚠️ **florida_registered_agents**: Empty table (0 records)
- ⚠️ **match_audit_log**: Empty table (0 records)
- ⚠️ **ml_model_metrics**: Empty table (0 records)
- ⚠️ **nal_staging**: Empty table (0 records)
- ⚠️ **nap_staging**: Empty table (0 records)
- ⚠️ **nav_assessment_details**: Empty table (0 records)
- ⚠️ **nav_details**: Empty table (0 records)
- ⚠️ **nav_jobs**: Empty table (0 records)
- ⚠️ **nav_summaries**: Empty table (0 records)
- ⚠️ **owner_entity_links**: Empty table (0 records)
- ⚠️ **parcel_update_history**: Empty table (0 records)
- ⚠️ **properties_master**: Empty table (0 records)
- ⚠️ **property_entity_matches**: Empty table (0 records)
- ⚠️ **property_owners**: Empty table (0 records)
- ⚠️ **property_ownership_history**: Empty table (0 records)
- ⚠️ **property_sales**: Empty table (0 records)
- ⚠️ **sdf_import_errors**: Empty table (0 records)
- ⚠️ **sdf_import_progress**: Empty table (0 records)
- ⚠️ **sdf_jobs**: Empty table (0 records)
- ⚠️ **sdf_staging**: Empty table (0 records)
- ⚠️ **sunbiz_change_log**: Empty table (0 records)
- ⚠️ **sunbiz_corporate_events**: Empty table (0 records)
- ⚠️ **sunbiz_corporate_staging**: Empty table (0 records)
- ⚠️ **sunbiz_download_jobs**: Empty table (0 records)
- ⚠️ **sunbiz_entity_search**: Empty table (0 records)
- ⚠️ **sunbiz_events_staging**: Empty table (0 records)
- ⚠️ **sunbiz_fictitious_events**: Empty table (0 records)
- ⚠️ **sunbiz_fictitious_staging**: Empty table (0 records)
- ⚠️ **sunbiz_import_log**: Empty table (0 records)
- ⚠️ **sunbiz_lien_debtors**: Empty table (0 records)
- ⚠️ **sunbiz_lien_secured_parties**: Empty table (0 records)
- ⚠️ **sunbiz_liens**: Empty table (0 records)
- ⚠️ **sunbiz_marks**: Empty table (0 records)
- ⚠️ **sunbiz_partnership_events**: Empty table (0 records)
- ⚠️ **sunbiz_partnerships**: Empty table (0 records)
- ⚠️ **sunbiz_principal_data**: Empty table (0 records)
- ⚠️ **sunbiz_processed_files**: Empty table (0 records)
- ⚠️ **sunbiz_sftp_downloads**: Empty table (0 records)
- ⚠️ **tpp_jobs**: Empty table (0 records)
- ⚠️ **validation_errors**: Empty table (0 records)
- ⚠️ **validation_results**: Empty table (0 records)
- ⚠️ **watchlist_alerts**: Empty table (0 records)

---

## 📊 Table-by-Table Analysis


### florida_entities

- **Records:** 15,013,088
- **Size:** 7834 MB
- **Columns:** 25
- **Indexes:** 9
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `entity_id` (character varying)
- `entity_type` (character)
- `business_name` (character varying)
- `dba_name` (character varying) (nullable)
- `entity_status` (character varying) (nullable)
- `business_address_line1` (character varying) (nullable)
- `business_address_line2` (character varying) (nullable)
- `business_city` (character varying) (nullable)
- `business_state` (character) (nullable)
- ... and 15 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "entity_id": "1FLR0000010",
  "entity_type": "G",
  "business_name": "010620210000100001AF081020200000000009092030 0000000001000010000100001",
  "dba_name": null,
  "entity_status": "ACTIVE",
  "business_address_line1": "",
  "business_address_line2": null,
  "business_city": "",
  "business_state": "FL",
  "business_zip": "",
  "business_county": "",
  "mailing_address_line1": null,
  "mailing_address_line2": null,
  "mailing_city": null,
  "mailing_state": null,
  "mailing_zip": null,
  "formation_date": null,
  "registration_date": null,
  "last_update_date": null,
  "source_file": "20210106flrf.txt",
  "source_record_line": null,
  "processed_at": "2025-09-11 21:58:07.629084",
  "created_at": "2025-09-11 17:58:07.058769",
  "updated_at": "2025-09-11 21:58:07.629084"
}
```

### florida_parcels

- **Records:** 10,304,043
- **Size:** 30 GB
- **Columns:** 57
- **Indexes:** 92
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `parcel_id` (character varying)
- `county` (character varying)
- `year` (integer)
- `geometry` (jsonb) (nullable) - 100.0% NULL
- `centroid` (jsonb) (nullable) - 100.0% NULL
- `area_sqft` (double precision) (nullable) - 100.0% NULL
- `perimeter_ft` (double precision) (nullable) - 100.0% NULL
- `owner_name` (character varying) (nullable)
- `owner_addr1` (character varying) (nullable)
- ... and 47 more columns

**Sample Record (first):**
```json
{
  "id": 11560419,
  "parcel_id": "20270821R000004000090U",
  "county": "HILLSBOROUGH",
  "year": 2025,
  "geometry": null,
  "centroid": null,
  "area_sqft": null,
  "perimeter_ft": null,
  "owner_name": "PHAN HUONG MANH",
  "owner_addr1": "18521 OTTERWOOD AVE",
  "owner_addr2": null,
  "owner_city": "TAMPA",
  "owner_state": "FL",
  "owner_zip": "33647.0",
  "phy_addr1": "18521 OTTERWOOD AVE",
  "phy_addr2": null,
  "phy_city": "TAMPA",
  "phy_state": "FL",
  "phy_zipcd": "33647.0",
  "legal_desc": null,
  "subdivision": null,
  "lot": null,
  "block": null,
  "property_use": "1",
  "property_use_desc": null,
  "land_use_code": null,
  "zoning": null,
  "just_value": 268311.0,
  "assessed_value": 268311.0,
  "taxable_value": 268311.0,
  "land_value": 80080.0,
  "building_value": 188231.0,
  "year_built": 1992,
  "total_living_area": 1843.0,
  "bedrooms": null,
  "bathrooms": null,
  "stories": null,
  "units": null,
  "land_sqft": 6919.0,
  "land_acres": null,
  "sale_date": null,
  "sale_price": null,
  "sale_qualification": null,
  "match_status": null,
  "discrepancy_reason": null,
  "is_redacted": false,
  "data_source": null,
  "import_date": "2025-09-16 05:25:21.291005",
  "update_date": null,
  "data_hash": null,
  "market_value": null,
  "data_quality_score": 100,
  "last_validated_at": null,
  "source_type": "DOR",
  "ingestion_run_id": null,
  "county_normalized": null,
  "standardized_property_use": "Single Family Residential"
}
```

### sunbiz_corporate

- **Records:** 2,030,912
- **Size:** 6318 MB
- **Columns:** 24
- **Indexes:** 29
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `entity_name` (character varying) (nullable)
- `status` (character varying) (nullable)
- `filing_date` (date) (nullable) - 100.0% NULL
- `state_country` (character varying) (nullable)
- `prin_addr1` (character varying) (nullable)
- `prin_addr2` (character varying) (nullable)
- `prin_city` (character varying) (nullable)
- `prin_state` (character varying) (nullable)
- ... and 14 more columns

**Sample Record (first):**
```json
{
  "id": 1539122,
  "doc_number": "M23000011936",
  "entity_name": "WATERMAN BROADCASTING LLC",
  "status": "",
  "filing_date": null,
  "state_country": "NE",
  "prin_addr1": "SANIBEL                       3395",
  "prin_addr2": "",
  "prin_city": "7       1300 SEASPRAY LANE",
  "prin_state": "",
  "prin_zip": "",
  "mail_addr1": "SANIBEL                     FL33957     US09182023              N",
  "mail_addr2": "",
  "mail_city": "DE                                       CAPITO",
  "mail_state": "L",
  "mail_zip": "CORPORATE",
  "ein": "",
  "registered_agent": "SERVICES, INC.          C515 EAST PARK AVENUE, 2ND FLOOR           TALLAHASSEE                 FL323",
  "file_type": "1300 SEA",
  "subtype": "AFORL",
  "source_file": null,
  "import_date": "2025-09-11 01:55:41.817787",
  "update_date": null,
  "updated_at": "2025-10-27 15:35:00.015976"
}
```

### florida_parcels_staging

- **Records:** 654,537
- **Size:** 196 MB
- **Columns:** 32
- **Indexes:** 0
- **Foreign Keys:** 0

**Columns:**
- `parcel_id` (text) (nullable)
- `county` (text) (nullable)
- `year` (integer) (nullable)
- `owner_name` (text) (nullable)
- `owner_addr1` (text) (nullable)
- `owner_addr2` (text) (nullable) - 98.4% NULL
- `owner_city` (text) (nullable)
- `owner_state` (text) (nullable)
- `owner_zip` (text) (nullable)
- `phy_addr1` (text) (nullable)
- ... and 22 more columns

**Sample Record (first):**
```json
{
  "parcel_id": "00354031000009000",
  "county": "PALM BEACH",
  "year": 2025,
  "owner_name": "TIITF",
  "owner_addr1": "3900 COMMONWEALTH BLVD MS 108",
  "owner_addr2": null,
  "owner_city": "TALLAHASSEE",
  "owner_state": "Fl",
  "owner_zip": "32399",
  "phy_addr1": "39990 LAKEVIEW DR",
  "phy_addr2": null,
  "phy_city": "PAHOKEE",
  "phy_state": "FL",
  "phy_zipcd": "33476",
  "property_use": "087",
  "land_use_code": "087",
  "just_value": 47048146,
  "assessed_value": 47048146,
  "taxable_value": 0,
  "land_value": 46937383,
  "building_value": 110763,
  "market_value": 47048146,
  "year_built": null,
  "total_living_area": null,
  "land_sqft": 6815307975.0,
  "sale_date": null,
  "sale_price": null,
  "data_source": "Florida DOR NAL",
  "source_type": "NAL",
  "import_date": "2025-10-25T23:04:29.502310",
  "data_quality_score": 85,
  "is_redacted": false
}
```

### property_sales_history

- **Records:** 637,890
- **Size:** 861 MB
- **Columns:** 31
- **Indexes:** 39
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `county_no` (character varying)
- `parcel_id` (character varying)
- `state_parcel_id` (character varying) (nullable) - 81.9% NULL
- `assessment_year` (integer) (nullable) - 43.5% NULL
- `atv_start` (integer) (nullable) - 83.2% NULL
- `group_no` (character varying) (nullable) - 83.2% NULL
- `dor_use_code` (character varying) (nullable) - 83.2% NULL
- `neighborhood_code` (character varying) (nullable) - 83.6% NULL
- `market_area` (character varying) (nullable) - 83.2% NULL
- ... and 21 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "county_no": "16",
  "parcel_id": "474119030010",
  "state_parcel_id": "C16-001-192-0124-2",
  "assessment_year": 2025,
  "atv_start": 8,
  "group_no": "1",
  "dor_use_code": "000",
  "neighborhood_code": "665550",
  "market_area": "7",
  "census_block": null,
  "sale_id_code": "99000120039267",
  "sale_change_code": null,
  "verification_code": "V",
  "or_book": null,
  "or_page": null,
  "clerk_no": "120039267",
  "quality_code": "11",
  "sale_year": 2025,
  "sale_month": 2,
  "sale_price": 100,
  "multi_parcel_sale": "C",
  "rs_id": "2B6D",
  "mp_id": "00B5E2FC",
  "sale_date": "2025-02-01",
  "created_at": "2025-09-09 19:25:36.153999+00:00",
  "updated_at": "2025-09-09 19:25:36.153999+00:00",
  "county": null,
  "data_quality_score": 100,
  "source_type": "DOR",
  "ingestion_run_id": null
}
```

### dor_code_audit

- **Records:** 294,325
- **Size:** 62 MB
- **Columns:** 13
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `audit_id` (bigint)
- `property_id` (bigint)
- `parcel_id` (character varying) (nullable)
- `county` (character varying) (nullable)
- `change_timestamp` (timestamp without time zone) (nullable)
- `old_land_use_code` (character varying) (nullable) - 51.0% NULL
- `old_property_use` (character varying) (nullable)
- `new_land_use_code` (character varying) (nullable)
- `new_property_use` (character varying) (nullable)
- `change_reason` (character varying) (nullable)
- ... and 3 more columns

**Sample Record (first):**
```json
{
  "audit_id": 1,
  "property_id": 1182123,
  "parcel_id": "1078130000340",
  "county": "DADE",
  "change_timestamp": "2025-09-30 12:10:53.842577",
  "old_land_use_code": "0",
  "old_property_use": "0",
  "new_land_use_code": "10",
  "new_property_use": "Vacant Re",
  "change_reason": "Fix 0/0 placeholder to Vacant Residential",
  "building_value": "0",
  "land_value": "299754",
  "just_value": "299754"
}
```

### property_assessments

- **Records:** 121,477
- **Size:** 81 MB
- **Columns:** 29
- **Indexes:** 11
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `county_code` (text) (nullable)
- `county_name` (text) (nullable)
- `owner_name` (text) (nullable)
- `owner_address` (text) (nullable)
- `owner_city` (text) (nullable)
- `owner_state` (text) (nullable)
- `owner_zip` (text) (nullable)
- `property_address` (text) (nullable)
- ... and 19 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "parcel_id": "00002-000-000",
  "county_code": "11",
  "county_name": "ALACHUA",
  "owner_name": "STATE OF FLA IIF  DNR",
  "owner_address": "3900 COMMONWEALTH BLVD",
  "owner_city": "TALLAHASSEE",
  "owner_state": "FL",
  "owner_zip": "32399",
  "property_address": "UNASSIGNED LOCATION RE",
  "property_city": null,
  "property_zip": null,
  "property_use_code": "087",
  "tax_district": null,
  "subdivision": null,
  "just_value": "60000.0",
  "assessed_value": "60000.0",
  "taxable_value": "0.0",
  "land_value": "42543.0",
  "building_value": "0",
  "total_sq_ft": 1306800,
  "living_area": 784,
  "year_built": 1989,
  "bedrooms": 1,
  "bathrooms": "0.0",
  "pool": false,
  "tax_year": 2025,
  "created_at": "2025-09-12 22:57:11.174128+00:00",
  "updated_at": "2025-09-12 22:57:11.174128+00:00"
}
```

### nav_parcel_assessments

- **Records:** 31,000
- **Size:** 10176 kB
- **Columns:** 13
- **Indexes:** 6
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `roll_type` (character varying) (nullable)
- `county_number` (character varying) (nullable)
- `pa_parcel_number` (character varying) (nullable)
- `tc_account_number` (character varying) (nullable)
- `tax_year` (character varying) (nullable)
- `total_assessments` (numeric) (nullable)
- `number_of_assessments` (integer) (nullable)
- `tax_roll_sequence_number` (integer) (nullable)
- `county_name` (character varying) (nullable)
- ... and 3 more columns

**Sample Record (first):**
```json
{
  "id": 10955,
  "roll_type": "N",
  "county_number": "16",
  "pa_parcel_number": "10827",
  "tc_account_number": "474236-05-0120",
  "tax_year": "2024",
  "total_assessments": "373.92",
  "number_of_assessments": 2,
  "tax_roll_sequence_number": 12414,
  "county_name": "Broward",
  "data_source": "florida_revenue_nav",
  "created_at": "2025-09-05 14:01:03.963814",
  "updated_at": "2025-09-05 14:01:03.963814"
}
```

### spatial_ref_sys

- **Records:** 8,500
- **Size:** 7144 kB
- **Columns:** 5
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `srid` (integer)
- `auth_name` (character varying) (nullable)
- `auth_srid` (integer) (nullable)
- `srtext` (character varying) (nullable)
- `proj4text` (character varying) (nullable)

**Sample Record (first):**
```json
{
  "srid": 2000,
  "auth_name": "EPSG",
  "auth_srid": 2000,
  "srtext": "PROJCS[\"Anguilla 1957 / British West Indies Grid\",GEOGCS[\"Anguilla 1957\",DATUM[\"Anguilla_1957\",SPHEROID[\"Clarke 1880 (RGS)\",6378249.145,293.465,AUTHORITY[\"EPSG\",\"7012\"]],AUTHORITY[\"EPSG\",\"6600\"]],PRIMEM[\"Greenwich\",0,AUTHORITY[\"EPSG\",\"8901\"]],UNIT[\"degree\",0.0174532925199433,AUTHORITY[\"EPSG\",\"9122\"]],AUTHORITY[\"EPSG\",\"4600\"]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"latitude_of_origin\",0],PARAMETER[\"central_meridian\",-62],PARAMETER[\"scale_factor\",0.9995],PARAMETER[\"false_easting\",400000],PARAMETER[\"false_northing\",0],UNIT[\"metre\",1,AUTHORITY[\"EPSG\",\"9001\"]],AXIS[\"Easting\",EAST],AXIS[\"Northing\",NORTH],AUTHORITY[\"EPSG\",\"2000\"]]",
  "proj4text": "+proj=tmerc +lat_0=0 +lon_0=-62 +k=0.9995000000000001 +x_0=400000 +y_0=0 +ellps=clrk80 +units=m +no_defs "
}
```

### data_flow_metrics

- **Records:** 3,253
- **Size:** 1240 kB
- **Columns:** 8
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `table_name` (character varying)
- `metric_type` (character varying)
- `metric_value` (double precision)
- `metric_unit` (character varying) (nullable)
- `county_filter` (character varying) (nullable) - 100.0% NULL
- `additional_context` (jsonb) (nullable)
- `timestamp` (timestamp without time zone)

**Sample Record (first):**
```json
{
  "id": 1,
  "table_name": "agent_propertydataagent",
  "metric_type": "health_check",
  "metric_value": 1.0,
  "metric_unit": "success",
  "county_filter": null,
  "additional_context": "{'alerts': 0, 'status': 'ACTIVE'}",
  "timestamp": "2025-10-30 22:28:00.089947"
}
```

### normalization_progress

- **Records:** 2,343
- **Size:** 280 kB
- **Columns:** 5
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `county` (text) (nullable)
- `code` (text) (nullable)
- `rows_updated` (bigint) (nullable)
- `completed_at` (timestamp with time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1283,
  "county": "JACKSON",
  "code": "0",
  "rows_updated": 14057,
  "completed_at": "2025-10-28 04:21:31.018876+00:00"
}
```

### fact_property_score

- **Records:** 1,201
- **Size:** 1360 kB
- **Columns:** 13
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `county` (text)
- `year` (integer)
- `score_v1` (numeric)
- `reasons` (jsonb)
- `inputs_checksum` (text)
- `ownership_score` (numeric) (nullable)
- `hold_period_score` (numeric) (nullable)
- `tax_status_score` (numeric) (nullable)
- ... and 3 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "parcel_id": "00-00-00-0190-0000-0050",
  "county": "JEFFERSON",
  "year": 2025,
  "score_v1": "40.00",
  "reasons": "{'ownership': {'type': 'individual', 'score': 15, 'explanation': 'Owner classified as individual'}, 'tax_status': {'score': 5, 'status': 'delinquent', 'explanation': 'Tax status: delinquent'}, 'hold_period': {'score': 8, 'category': 'unknown', 'explanation': 'Hold period: unknown years'}, 'total_score': 40, 'equity_proxy': {'score': 12, 'category': 'no_sale_data', 'explanation': 'Value appreciation: no_sale_data'}, 'component_scores': {'ownership': 15, 'tax_status': 5, 'hold_period': 8, 'equity_proxy': 12}}",
  "inputs_checksum": "34afea28a263fceb0934740811cc072a",
  "ownership_score": "15.00",
  "hold_period_score": "8.00",
  "tax_status_score": "5.00",
  "equity_proxy_score": "12.00",
  "scored_at": "2025-09-21 04:56:57.182192+00:00",
  "scoring_version": "1.0"
}
```

### sunbiz_officer_corporation_matches

- **Records:** 1,182
- **Size:** 1200 kB
- **Columns:** 15
- **Indexes:** 9
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `doc_number` (character varying) (nullable)
- `officer_name` (character varying) (nullable)
- `officer_address` (character varying) (nullable)
- `officer_city` (character varying) (nullable)
- `officer_state` (character varying) (nullable)
- `officer_zip` (character varying) (nullable)
- `officer_email` (character varying) (nullable) - 100.0% NULL
- `officer_phone` (character varying) (nullable) - 100.0% NULL
- `corp_name` (character varying) (nullable)
- ... and 5 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "doc_number": "N17000007799",
  "officer_name": "Majed B PTarabay G",
  "officer_address": "P.O.Box: 302",
  "officer_city": "Oak Lawn",
  "officer_state": "",
  "officer_zip": "IL60454",
  "officer_email": null,
  "officer_phone": null,
  "corp_name": "PEL- ZOUHAIRI        ANDIRA        Esq.    P.O.Box: 302",
  "corp_address": "Oak Lawn                    IL60454",
  "corp_city": "",
  "corp_state": "",
  "corp_zip": "",
  "created_at": "2025-09-11 12:20:36.867322"
}
```

### dor_use_codes_std

- **Records:** 186
- **Size:** 152 kB
- **Columns:** 7
- **Indexes:** 6
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `main_code` (character varying)
- `sub_code` (character varying) (nullable)
- `full_code` (character varying)
- `description` (text)
- `category` (character varying)
- `created_at` (timestamp without time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "main_code": "00",
  "sub_code": "01",
  "full_code": "00-01",
  "description": "Vacant Residential",
  "category": "Vacant Land",
  "created_at": "2025-10-06 00:13:44.366230"
}
```

### dor_code_mappings_std

- **Records:** 134
- **Size:** 160 kB
- **Columns:** 6
- **Indexes:** 7
- **Foreign Keys:** 1

**Columns:**
- `id` (integer)
- `legacy_code` (character varying)
- `standard_full_code` (character varying)
- `county` (character varying) (nullable)
- `confidence` (character varying) (nullable)
- `created_at` (timestamp without time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 127,
  "legacy_code": "Condo",
  "standard_full_code": "04-01",
  "county": "MIAMI-DADE",
  "confidence": "exact",
  "created_at": "2025-10-09 19:45:03.870255"
}
```

### sunbiz_officers

- **Records:** 110
- **Size:** 208 kB
- **Columns:** 12
- **Indexes:** 8
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `doc_number` (character varying) (nullable)
- `officer_name` (character varying) (nullable)
- `officer_title` (character varying) (nullable)
- `officer_address` (character varying) (nullable)
- `officer_city` (character varying) (nullable)
- `officer_state` (character varying) (nullable)
- `officer_zip` (character varying) (nullable)
- `officer_email` (character varying) (nullable)
- `officer_phone` (character varying) (nullable)
- ... and 2 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "doc_number": "P00000000001",
  "officer_name": "SMITH, JOHN A",
  "officer_title": "PRESIDENT",
  "officer_address": "123 MAIN ST",
  "officer_city": "MIAMI",
  "officer_state": "FL",
  "officer_zip": "33101",
  "officer_email": "jsmith@example.com",
  "officer_phone": "305-555-0001",
  "source_file": "SAMPLE_OFFICERS.txt",
  "import_date": "2025-09-10 22:26:30.568526"
}
```

### florida_processing_log

- **Records:** 105
- **Size:** 128 kB
- **Columns:** 11
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `file_path` (character varying)
- `file_size` (bigint) (nullable)
- `records_processed` (integer) (nullable)
- `records_successful` (integer) (nullable)
- `records_failed` (integer) (nullable)
- `processing_status` (character varying) (nullable)
- `error_details` (text) (nullable) - 100.0% NULL
- `started_at` (timestamp without time zone) (nullable)
- `completed_at` (timestamp without time zone) (nullable)
- ... and 1 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "file_path": "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\TEMP\\DATABASE\\doc\\FLR\\FILINGS\\20210106flrf.txt",
  "file_size": 4648,
  "records_processed": 56,
  "records_successful": 56,
  "records_failed": 0,
  "processing_status": "COMPLETED",
  "error_details": null,
  "started_at": "2025-09-11 17:58:07.032094",
  "completed_at": "2025-09-11 17:58:07.179962",
  "created_at": "2025-09-11 17:58:07.032094"
}
```

### property_use_mapping

- **Records:** 105
- **Size:** 80 kB
- **Columns:** 6
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `raw_code` (text)
- `standardized_name` (text)
- `dor_code` (text) (nullable)
- `category` (text) (nullable)
- `description` (text) (nullable)
- `created_at` (timestamp with time zone) (nullable)

**Sample Record (first):**
```json
{
  "raw_code": "0001",
  "standardized_name": "Single Family Residential",
  "dor_code": "001",
  "category": "Residential",
  "description": "Single family home",
  "created_at": "2025-10-26 04:37:21.506511+00:00"
}
```

### dor_use_codes

- **Records:** 100
- **Size:** 112 kB
- **Columns:** 18
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `code` (text)
- `description` (text)
- `category` (text)
- `subcategory` (text) (nullable)
- `is_residential` (boolean) (nullable)
- `is_commercial` (boolean) (nullable)
- `is_industrial` (boolean) (nullable)
- `is_agricultural` (boolean) (nullable)
- `is_institutional` (boolean) (nullable)
- ... and 8 more columns

**Sample Record (first):**
```json
{
  "id": "a7276a0a-efc5-4dfb-ab70-f2111bf7a842",
  "code": "000",
  "description": "Vacant",
  "category": "Vacant",
  "subcategory": "Residential",
  "is_residential": true,
  "is_commercial": false,
  "is_industrial": false,
  "is_agricultural": false,
  "is_institutional": false,
  "is_governmental": false,
  "is_miscellaneous": false,
  "is_vacant": true,
  "color_class": "text-gray-600",
  "bg_color_class": "bg-gray-50",
  "border_color_class": "border-gray-200",
  "created_at": "2025-09-26 04:10:56.269345+00:00",
  "updated_at": "2025-09-26 04:10:56.269345+00:00"
}
```

### county_codes

- **Records:** 66
- **Size:** 96 kB
- **Columns:** 3
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `county_name` (text)
- `county_no` (text)
- `dor_code` (text) (nullable) - 21.2% NULL

**Sample Record (first):**
```json
{
  "county_name": "ALACHUA",
  "county_no": "01",
  "dor_code": null
}
```

### county_name_mappings

- **Records:** 20
- **Size:** 32 kB
- **Columns:** 2
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `variant` (text)
- `canonical` (text)

**Sample Record (first):**
```json
{
  "variant": "DADE",
  "canonical": "MIAMI-DADE"
}
```

### tax_deed_bidding_items

- **Records:** 19
- **Size:** 64 kB
- **Columns:** 25
- **Indexes:** 2
- **Foreign Keys:** 1

**Columns:**
- `id` (integer)
- `auction_id` (integer) (nullable)
- `parcel_id` (character varying)
- `tax_deed_number` (character varying) (nullable)
- `tax_certificate_number` (character varying) (nullable) - 100.0% NULL
- `legal_situs_address` (text) (nullable)
- `homestead_exemption` (boolean) (nullable)
- `assessed_value` (numeric) (nullable)
- `soh_value` (numeric) (nullable) - 100.0% NULL
- `opening_bid` (numeric) (nullable)
- ... and 15 more columns

**Sample Record (first):**
```json
{
  "id": 281,
  "auction_id": 110,
  "parcel_id": "514114-10-6250",
  "tax_deed_number": "TD-51640",
  "tax_certificate_number": null,
  "legal_situs_address": "6418 SW 7 ST",
  "homestead_exemption": false,
  "assessed_value": "302260.82",
  "soh_value": null,
  "opening_bid": "151130.41",
  "current_bid": null,
  "reserve_met": false,
  "close_time": "2025-09-17 11:00:00",
  "item_status": "Upcoming",
  "total_bids": 0,
  "unique_bidders": 0,
  "applicant_name": "TAX CERTIFICATE HOLDER",
  "tax_years_included": null,
  "total_taxes_owed": null,
  "winning_bid": null,
  "winning_bidder": null,
  "gis_parcel_map_url": null,
  "property_appraisal_url": null,
  "created_at": "2025-09-10 21:21:03.542122",
  "updated_at": "2025-09-10 21:21:03.542122"
}
```

### ml_property_scores_xgb

- **Records:** 12
- **Size:** 96 kB
- **Columns:** 10
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `county` (text) (nullable)
- `score_v1` (numeric) (nullable)
- `ml_score` (numeric) (nullable)
- `score_final` (numeric) (nullable)
- `ml_confidence` (numeric) (nullable)
- `feature_importance` (jsonb) (nullable)
- `model_version` (text) (nullable)
- `computed_at` (timestamp with time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "parcel_id": "TEST123",
  "county": "BROWARD",
  "score_v1": "90.00",
  "ml_score": "99.59",
  "score_final": "95.75",
  "ml_confidence": "0.9959",
  "feature_importance": "{'just_value': 0.05371033400297165, 'land_value': 2.6187264919281006, 'property_age': 0.2270614057779312, 'is_top_county': -0.02051575854420662, 'building_value': 0.29909053444862366, 'land_value_pct': 0.07049926370382309, 'value_per_sqft': 0.5615702867507935, 'building_value_pct': 0.8660616278648376, 'land_building_ratio': 0.7562964558601379}",
  "model_version": "xgboost_v1",
  "computed_at": "2025-09-21 13:36:11.493660+00:00"
}
```

### document_categories

- **Records:** 10
- **Size:** 80 kB
- **Columns:** 10
- **Indexes:** 4
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `category_name` (text)
- `category_code` (text)
- `description` (text) (nullable)
- `parent_category_id` (bigint) (nullable) - 100.0% NULL
- `requires_ocr` (boolean) (nullable)
- `auto_classification` (boolean) (nullable)
- `retention_years` (integer) (nullable)
- `created_at` (timestamp with time zone) (nullable)
- `updated_at` (timestamp with time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "category_name": "Tax Certificates",
  "category_code": "TAX_CERT",
  "description": "Property tax certificates and liens",
  "parent_category_id": null,
  "requires_ocr": true,
  "auto_classification": true,
  "retention_years": 10,
  "created_at": "2025-09-21 05:55:07.586112+00:00",
  "updated_at": "2025-09-21 05:55:07.586112+00:00"
}
```

### fl_data_updates

- **Records:** 10
- **Size:** 48 kB
- **Columns:** 16
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `source_type` (character varying) (nullable)
- `source_name` (character varying) (nullable)
- `update_date` (timestamp without time zone) (nullable)
- `records_processed` (integer) (nullable) - 100.0% NULL
- `records_added` (integer) (nullable) - 100.0% NULL
- `records_updated` (integer) (nullable) - 100.0% NULL
- `records_failed` (integer) (nullable) - 100.0% NULL
- `source_file` (character varying) (nullable) - 100.0% NULL
- `file_size` (bigint) (nullable) - 100.0% NULL
- ... and 6 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "source_type": "SDF",
  "source_name": "sdf_agent",
  "update_date": "2025-09-05 13:50:38.577283",
  "records_processed": null,
  "records_added": null,
  "records_updated": null,
  "records_failed": null,
  "source_file": null,
  "file_size": null,
  "file_hash": null,
  "processing_time_seconds": null,
  "status": "failed",
  "error_message": null,
  "agent_name": "sdf_agent",
  "agent_version": null
}
```

### ml_property_scores

- **Records:** 10
- **Size:** 112 kB
- **Columns:** 10
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `score_v1` (numeric) (nullable)
- `ml_score` (numeric) (nullable)
- `score_final` (numeric) (nullable)
- `feature_importance` (jsonb) (nullable)
- `shap_values` (jsonb) (nullable)
- `top_features` (jsonb) (nullable)
- `model_version` (text) (nullable)
- `computed_at` (timestamp with time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "parcel_id": "102000601120",
  "score_v1": "85.00",
  "ml_score": "0.00",
  "score_final": "51.00",
  "feature_importance": "{'bedrooms': 0.0, 'lot_size': 0.0, 'bathrooms': 0.0, 'land_value': 0.5556035137881619, 'year_built': 4.681140288982689, 'living_area': 0.0, 'property_age': 5.066388764863172, 'assessed_value': 6.305431177803256, 'building_value': 0.940818056295485, 'value_per_sqft': 0.0, 'land_building_ratio': 0.10761819826721919}",
  "shap_values": "{'bedrooms': 0.0, 'lot_size': 0.0, 'bathrooms': 0.0, 'land_value': 0.5556035137881619, 'year_built': 4.681140288982689, 'living_area': 0.0, 'property_age': 5.066388764863172, 'assessed_value': 6.305431177803256, 'building_value': 0.940818056295485, 'value_per_sqft': 0.0, 'land_building_ratio': 0.10761819826721919}",
  "top_features": "[{'feature': 'assessed_value', 'importance': 6.305431177803256, 'contribution': 6.305431177803256}, {'feature': 'property_age', 'importance': 5.066388764863172, 'contribution': 5.066388764863172}, {'feature': 'year_built', 'importance': 4.681140288982689, 'contribution': 4.681140288982689}]",
  "model_version": "v1_20250921",
  "computed_at": "2025-09-21 06:34:47.063549+00:00"
}
```

### tax_certificates

- **Records:** 10
- **Size:** 208 kB
- **Columns:** 22
- **Indexes:** 12
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `parcel_id` (character varying) (nullable)
- `real_estate_account` (character varying) (nullable)
- `certificate_number` (character varying)
- `tax_year` (integer) (nullable)
- `buyer_name` (character varying) (nullable)
- `certificate_buyer` (character varying) (nullable)
- `advertised_number` (character varying) (nullable)
- `face_amount` (numeric) (nullable)
- `tax_amount` (numeric) (nullable)
- ... and 12 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "parcel_id": "504234-08-00-20",
  "real_estate_account": "504234-08-00-20",
  "certificate_number": "2023-08745",
  "tax_year": 2023,
  "buyer_name": "CAPITAL ONE, NATIONAL ASSOCIATION (USA)",
  "certificate_buyer": "CAPITAL ONE, NATIONAL ASSOCIATION",
  "advertised_number": "AD-2023-08745",
  "face_amount": "8574.32",
  "tax_amount": "8574.32",
  "issued_date": "2023-06-01",
  "sale_date": "2023-06-01",
  "expiration_date": "2025-06-01",
  "interest_rate": "18.00",
  "bid_percentage": "18.00",
  "winning_bid_percentage": "18.00",
  "status": "active",
  "redemption_amount": "10117.70",
  "redemption_date": null,
  "buyer_entity": "{'status': 'Active', 'entity_name': 'CAPITAL ONE, NATIONAL ASSOCIATION', 'filing_type': 'Corporation', 'document_number': 'F96000004500', 'registered_agent': 'Corporate Services Company', 'principal_address': '1680 Capital One Drive, McLean, VA 22102'}",
  "created_at": "2025-09-08 22:54:48.017946",
  "updated_at": "2025-09-08 22:54:48.017946"
}
```

### watchlist_items

- **Records:** 9
- **Size:** 96 kB
- **Columns:** 13
- **Indexes:** 5
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `watchlist_id` (bigint) (nullable)
- `parcel_id` (text)
- `alert_on_price_change` (boolean) (nullable)
- `alert_on_status_change` (boolean) (nullable)
- `alert_on_new_listing` (boolean) (nullable)
- `alert_threshold_pct` (numeric) (nullable)
- `last_known_price` (numeric) (nullable) - 100.0% NULL
- `last_known_score` (numeric) (nullable) - 100.0% NULL
- `last_known_status` (text) (nullable) - 100.0% NULL
- ... and 3 more columns

**Sample Record (first):**
```json
{
  "id": 4,
  "watchlist_id": 2,
  "parcel_id": "00424240020270",
  "alert_on_price_change": true,
  "alert_on_status_change": true,
  "alert_on_new_listing": true,
  "alert_threshold_pct": "5.00",
  "last_known_price": null,
  "last_known_score": null,
  "last_known_status": null,
  "notes": "Test property 00424240020270",
  "added_at": "2025-09-21 13:44:51.134929+00:00",
  "last_checked": "2025-09-21 13:44:51.134929+00:00"
}
```

### documents

- **Records:** 8
- **Size:** 256 kB
- **Columns:** 32
- **Indexes:** 11
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `document_hash` (text)
- `original_filename` (text)
- `display_name` (text) (nullable)
- `category_id` (bigint) (nullable) - 25.0% NULL
- `document_type` (text) (nullable) - 87.5% NULL
- `confidence_score` (numeric) (nullable) - 37.5% NULL
- `file_size_bytes` (bigint) (nullable) - 37.5% NULL
- `mime_type` (text) (nullable) - 37.5% NULL
- `storage_path` (text)
- ... and 22 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "document_hash": "b40479d6e34636f27c71142a957dc776450f630c1f8fc55b06718ecd8433d33f",
  "original_filename": "assessment_notice_2025.pdf",
  "display_name": "assessment_notice_2025.pdf",
  "category_id": 5,
  "document_type": null,
  "confidence_score": "0.1667",
  "file_size_bytes": 46,
  "mime_type": "application/pdf",
  "storage_path": "C:\\Users\\gsima\\AppData\\Local\\Temp\\concordbroker_docs_nkv8r0d1\\assessment_notice_2025.pdf",
  "storage_bucket": "property-documents",
  "ocr_text": "\n            PROPERTY DOCUMENT\n            Date: 09/21/2025\n            Property: 123 MAIN ST\n            County: Jefferson\n            Document processed by automated system\n            ",
  "ocr_confidence": "0.7500",
  "processed_at": "2025-09-21 01:57:12.567217+00:00",
  "processing_status": "completed",
  "document_date": "2025-09-21",
  "effective_date": null,
  "expiration_date": null,
  "issuing_authority": null,
  "document_number": null,
  "parcel_ids": "[]",
  "counties": "[]",
  "addresses": "['123 MAIN ST\\n            County', '123 MAIN ST']",
  "search_vector": "'09/21/2025':5 '123':7 'assess':20 'assessment_notice_2025.pdf':1 'autom':15 'counti':10 'date':4 'document':3,12,18 'jefferson':11 'main':8,19 'process':13 'properti':2,6,17 'st':9 'system':16",
  "tags": "['assessment']",
  "keywords": "['PROPERTY', 'DOCUMENT', 'MAIN']",
  "access_level": "private",
  "created_by": "system",
  "created_at": "2025-09-21 05:57:12.770634+00:00",
  "updated_at": "2025-09-21 05:57:12.770634+00:00",
  "last_accessed_at": null,
  "access_count": 0
}
```

### entity_principals

- **Records:** 7
- **Size:** 112 kB
- **Columns:** 13
- **Indexes:** 6
- **Foreign Keys:** 1

**Columns:**
- `id` (uuid)
- `entity_id` (text)
- `entity_name` (text) (nullable)
- `owner_identity_id` (uuid) (nullable)
- `principal_name` (text)
- `role` (text) (nullable)
- `title` (text) (nullable) - 100.0% NULL
- `ownership_percentage` (numeric) (nullable) - 100.0% NULL
- `start_date` (date) (nullable) - 100.0% NULL
- `end_date` (date) (nullable) - 100.0% NULL
- ... and 3 more columns

**Sample Record (first):**
```json
{
  "id": "86ffb142-afb0-4714-a66d-b711f17e2a2c",
  "entity_id": "L25000344178",
  "entity_name": "MCV INVESTMENT PROPERTIES LLC                                                                                                                                                                   AFLAL",
  "owner_identity_id": "d56c0feb-5d4a-4d15-a74f-8be602192d46",
  "principal_name": "MCV INVESTMENT PROPERTIES LLC                                                                                                                                                                   AFLAL",
  "role": "owner",
  "title": null,
  "ownership_percentage": null,
  "start_date": null,
  "end_date": null,
  "source": "sunbiz",
  "created_at": "2025-10-05 21:21:26.542620+00:00",
  "updated_at": "2025-10-05 21:21:26.542620+00:00"
}
```

### fl_agent_status

- **Records:** 7
- **Size:** 112 kB
- **Columns:** 18
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `agent_name` (character varying)
- `agent_type` (character varying) (nullable)
- `is_enabled` (boolean) (nullable)
- `is_running` (boolean) (nullable)
- `current_status` (character varying) (nullable) - 42.9% NULL
- `schedule_type` (character varying) (nullable)
- `schedule_time` (time without time zone) (nullable)
- `schedule_day` (integer) (nullable) - 100.0% NULL
- `last_run_start` (timestamp without time zone) (nullable) - 42.9% NULL
- ... and 8 more columns

**Sample Record (first):**
```json
{
  "id": 5,
  "agent_name": "bcpa_agent",
  "agent_type": "property",
  "is_enabled": true,
  "is_running": false,
  "current_status": null,
  "schedule_type": "daily",
  "schedule_time": "03:00:00",
  "schedule_day": null,
  "last_run_start": null,
  "last_run_end": null,
  "last_run_status": null,
  "last_run_records": null,
  "last_error": null,
  "next_scheduled_run": null,
  "config": null,
  "created_at": "2025-09-05 13:44:48.629674",
  "updated_at": null
}
```

### florida_contacts

- **Records:** 7
- **Size:** 88 kB
- **Columns:** 21
- **Indexes:** 5
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `entity_id` (character varying)
- `contact_type` (character varying)
- `contact_role` (character varying) (nullable) - 100.0% NULL
- `first_name` (character varying) (nullable) - 100.0% NULL
- `middle_name` (character varying) (nullable) - 100.0% NULL
- `last_name` (character varying) (nullable) - 100.0% NULL
- `title` (character varying) (nullable) - 100.0% NULL
- `organization_name` (character varying) (nullable) - 100.0% NULL
- `phone` (character varying) (nullable) - 100.0% NULL
- ... and 11 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "entity_id": "23000284192",
  "contact_type": "EMAIL",
  "contact_role": null,
  "first_name": null,
  "middle_name": null,
  "last_name": null,
  "title": null,
  "organization_name": null,
  "phone": null,
  "email": "l23000284192manacjafafahotsandcateringllc@yahoo.com",
  "address_line1": null,
  "address_line2": null,
  "city": null,
  "state": null,
  "zip_code": null,
  "country": "US",
  "is_primary_contact": false,
  "source_file": "extracted_emails.txt",
  "created_at": "2025-09-11 17:58:07.258865",
  "updated_at": "2025-09-11 21:58:07.818012"
}
```

### property_ownership

- **Records:** 7
- **Size:** 128 kB
- **Columns:** 13
- **Indexes:** 7
- **Foreign Keys:** 1

**Columns:**
- `id` (uuid)
- `parcel_id` (text)
- `county_code` (integer)
- `owner_identity_id` (uuid) (nullable)
- `ownership_type` (text) (nullable)
- `entity_id` (text) (nullable)
- `entity_name` (text) (nullable)
- `ownership_percentage` (numeric) (nullable)
- `acquired_date` (date) (nullable) - 100.0% NULL
- `disposed_date` (date) (nullable) - 100.0% NULL
- ... and 3 more columns

**Sample Record (first):**
```json
{
  "id": "71244110-4adc-498a-b1ef-9b95ce06048e",
  "parcel_id": "01462311000044020",
  "county_code": 36,
  "owner_identity_id": "d56c0feb-5d4a-4d15-a74f-8be602192d46",
  "ownership_type": "corporation",
  "entity_id": "L25000344178",
  "entity_name": "MCV INVESTMENT PROPERTIES LLC                                                                                                                                                                   AFLAL",
  "ownership_percentage": "100.00",
  "acquired_date": null,
  "disposed_date": null,
  "source": "florida_parcels",
  "created_at": "2025-10-05 21:21:26.119649+00:00",
  "updated_at": "2025-10-05 21:21:26.119649+00:00"
}
```

### document_access_log

- **Records:** 5
- **Size:** 96 kB
- **Columns:** 12
- **Indexes:** 5
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `document_id` (bigint)
- `user_id` (text)
- `access_type` (text)
- `ip_address` (inet) (nullable) - 100.0% NULL
- `user_agent` (text) (nullable) - 100.0% NULL
- `referrer` (text) (nullable) - 100.0% NULL
- `search_query` (text) (nullable) - 100.0% NULL
- `access_granted` (boolean) (nullable)
- `denial_reason` (text) (nullable) - 100.0% NULL
- ... and 2 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "document_id": 1,
  "user_id": "system",
  "access_type": "view",
  "ip_address": null,
  "user_agent": null,
  "referrer": null,
  "search_query": null,
  "access_granted": true,
  "denial_reason": null,
  "accessed_at": "2025-09-21 06:07:36.477810+00:00",
  "session_id": null
}
```

### document_property_links

- **Records:** 4
- **Size:** 96 kB
- **Columns:** 12
- **Indexes:** 5
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `document_id` (bigint)
- `parcel_id` (text)
- `county` (text)
- `link_type` (text)
- `confidence` (numeric) (nullable)
- `extraction_method` (text) (nullable)
- `verified` (boolean) (nullable)
- `verified_by` (text) (nullable) - 75.0% NULL
- `verified_at` (timestamp with time zone) (nullable) - 75.0% NULL
- ... and 2 more columns

**Sample Record (first):**
```json
{
  "id": 2,
  "document_id": 6,
  "parcel_id": "232330555880",
  "county": "DADE",
  "link_type": "reference",
  "confidence": "0.5714",
  "extraction_method": "ai_classification",
  "verified": false,
  "verified_by": null,
  "verified_at": null,
  "created_at": "2025-09-21 06:16:11.096245+00:00",
  "updated_at": "2025-09-21 06:16:11.096245+00:00"
}
```

### owner_identities

- **Records:** 4
- **Size:** 104 kB
- **Columns:** 12
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `canonical_name` (text)
- `variant_names` (ARRAY) (nullable)
- `identity_type` (text) (nullable)
- `confidence_score` (numeric) (nullable)
- `primary_address` (jsonb) (nullable) - 100.0% NULL
- `phone` (text) (nullable) - 100.0% NULL
- `email` (text) (nullable) - 100.0% NULL
- `total_properties` (integer) (nullable)
- `total_value` (numeric) (nullable)
- ... and 2 more columns

**Sample Record (first):**
```json
{
  "id": "d56c0feb-5d4a-4d15-a74f-8be602192d46",
  "canonical_name": "C&O INVESTMENT LLC",
  "variant_names": "[]",
  "identity_type": "company",
  "confidence_score": "0.86",
  "primary_address": null,
  "phone": null,
  "email": null,
  "total_properties": 1,
  "total_value": "132592.00",
  "created_at": "2025-10-05 21:21:25.943073+00:00",
  "updated_at": "2025-10-05 21:26:43.754304+00:00"
}
```

### tax_deed_auctions

- **Records:** 4
- **Size:** 64 kB
- **Columns:** 19
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `auction_date` (date)
- `auction_time` (time without time zone) (nullable) - 25.0% NULL
- `description` (text) (nullable)
- `auction_type` (character varying) (nullable) - 25.0% NULL
- `status` (character varying) (nullable)
- `total_items` (integer) (nullable)
- `items_sold` (integer) (nullable)
- `total_revenue` (numeric) (nullable) - 100.0% NULL
- `location` (character varying) (nullable) - 100.0% NULL
- ... and 9 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "auction_date": "2025-01-15",
  "auction_time": "10:00:00",
  "description": "Broward County Tax Deed Sale - January 2025",
  "auction_type": "Online",
  "status": "Upcoming",
  "total_items": 245,
  "items_sold": 0,
  "total_revenue": null,
  "location": null,
  "auctioneer": null,
  "online_platform": "DeedAuction.net",
  "platform_url": "https://broward.deedauction.net/",
  "registration_deadline": null,
  "deposit_required": "5000.00",
  "bid_increment": "25.00",
  "created_at": "2025-09-09 13:48:07.791771",
  "updated_at": "2025-09-09 13:48:07.791771",
  "data_source": "County Records"
}
```

### monitoring_agents

- **Records:** 3
- **Size:** 48 kB
- **Columns:** 10
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `agent_name` (character varying)
- `agent_type` (character varying) (nullable)
- `monitoring_urls` (jsonb) (nullable) - 100.0% NULL
- `check_frequency_hours` (integer) (nullable)
- `last_run` (timestamp without time zone) (nullable) - 100.0% NULL
- `next_run` (timestamp without time zone) (nullable) - 100.0% NULL
- `enabled` (boolean) (nullable)
- `notification_settings` (jsonb) (nullable)
- `created_at` (timestamp without time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "agent_name": "Florida_PTO_Monitor",
  "agent_type": "data_source",
  "monitoring_urls": null,
  "check_frequency_hours": 24,
  "last_run": null,
  "next_run": null,
  "enabled": true,
  "notification_settings": "{'email': 'admin@westbocaexecutiveoffice.com', 'on_error': True, 'on_change': True}",
  "created_at": "2025-09-05 13:38:47.416737"
}
```

### properties

- **Records:** 3
- **Size:** 240 kB
- **Columns:** 19
- **Indexes:** 14
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (character varying)
- `owner_name` (character varying) (nullable)
- `property_address` (character varying) (nullable)
- `city` (character varying) (nullable)
- `state` (character varying) (nullable)
- `zip_code` (character varying) (nullable)
- `property_type` (character varying) (nullable)
- `year_built` (integer) (nullable)
- `total_sqft` (double precision) (nullable)
- ... and 9 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "parcel_id": "504231242720",
  "owner_name": "RODRIGUEZ MARIA",
  "property_address": "3920 SW 53 CT",
  "city": "Hollywood",
  "state": "FL",
  "zip_code": "33021",
  "property_type": "Single Family",
  "year_built": 1978,
  "total_sqft": 2150.0,
  "lot_size_sqft": 8500.0,
  "bedrooms": 3,
  "bathrooms": 2.0,
  "assessed_value": "285000.00",
  "market_value": "425000.00",
  "last_sale_date": "2019-06-15",
  "last_sale_price": "320000.00",
  "created_at": "2025-09-07 15:33:35.551767",
  "updated_at": "2025-09-07 15:33:35.551767"
}
```

### user_preferences

- **Records:** 3
- **Size:** 96 kB
- **Columns:** 13
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `user_id` (text)
- `email` (text) (nullable)
- `phone` (text) (nullable)
- `email_notifications` (boolean) (nullable)
- `sms_notifications` (boolean) (nullable)
- `notification_frequency` (text) (nullable)
- `quiet_hours_start` (time without time zone) (nullable)
- `quiet_hours_end` (time without time zone) (nullable)
- `timezone` (text) (nullable)
- `opted_out` (boolean) (nullable)
- ... and 3 more columns

**Sample Record (first):**
```json
{
  "user_id": "test-user-1",
  "email": "test@example.com",
  "phone": "+1234567890",
  "email_notifications": true,
  "sms_notifications": true,
  "notification_frequency": "immediate",
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00",
  "timezone": "America/New_York",
  "opted_out": false,
  "opted_out_at": null,
  "created_at": "2025-09-21 05:25:02.771394+00:00",
  "updated_at": "2025-09-21 05:25:02.771394+00:00"
}
```

### user_watchlists

- **Records:** 3
- **Size:** 32 kB
- **Columns:** 7
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `user_id` (text)
- `name` (text) (nullable)
- `description` (text) (nullable)
- `is_active` (boolean) (nullable)
- `created_at` (timestamp with time zone) (nullable)
- `updated_at` (timestamp with time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 2,
  "user_id": "test_user_api_001",
  "name": "Investment Opportunities",
  "description": "High-potential properties in South Florida",
  "is_active": false,
  "created_at": "2025-09-21 13:44:46.519662+00:00",
  "updated_at": "2025-09-21 13:45:05.095299+00:00"
}
```

### watchlist

- **Records:** 3
- **Size:** 96 kB
- **Columns:** 12
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `user_id` (text)
- `parcel_id` (text)
- `county` (text)
- `notify_score_change` (boolean) (nullable)
- `notify_ownership_change` (boolean) (nullable)
- `notify_value_change` (boolean) (nullable)
- `min_score_change` (numeric) (nullable)
- `min_value_change_percent` (numeric) (nullable)
- `created_at` (timestamp with time zone) (nullable)
- ... and 2 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "user_id": "test-user-1",
  "parcel_id": "12345678",
  "county": "COLUMBIA",
  "notify_score_change": true,
  "notify_ownership_change": true,
  "notify_value_change": true,
  "min_score_change": "5.00",
  "min_value_change_percent": "20.00",
  "created_at": "2025-09-21 05:25:02.771394+00:00",
  "updated_at": "2025-09-21 05:25:02.771394+00:00",
  "last_notified_at": null
}
```

### document_processing_queue

- **Records:** 2
- **Size:** 80 kB
- **Columns:** 14
- **Indexes:** 4
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `document_id` (bigint)
- `operation_type` (text)
- `priority` (integer) (nullable)
- `status` (text) (nullable)
- `started_at` (timestamp with time zone) (nullable)
- `completed_at` (timestamp with time zone) (nullable)
- `error_message` (text) (nullable) - 50.0% NULL
- `retry_count` (integer) (nullable)
- `max_retries` (integer) (nullable)
- ... and 4 more columns

**Sample Record (first):**
```json
{
  "id": 3,
  "document_id": 8,
  "operation_type": "classification",
  "priority": 3,
  "status": "failed",
  "started_at": "2025-09-21 06:23:15.002724+00:00",
  "completed_at": "2025-09-21 06:23:15.112398+00:00",
  "error_message": "the JSON object must be str, bytes or bytearray, not dict",
  "retry_count": 0,
  "max_retries": 3,
  "processing_results": "{'auto_classify': True, 'file_patterns': ['*.pdf'], 'source_directory': 'C:\\\\Users\\\\gsima\\\\AppData\\\\Local\\\\Temp\\\\bulk_test_docs_gmkw3rlu', 'notification_email': None, 'auto_link_properties': True}",
  "scheduled_for": "2025-09-21 06:23:14.890216+00:00",
  "created_at": "2025-09-21 06:23:14.890216+00:00",
  "updated_at": "2025-09-21 06:23:14.890216+00:00"
}
```

### ingestion_runs

- **Records:** 2
- **Size:** 80 kB
- **Columns:** 16
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `run_timestamp` (timestamp with time zone) (nullable)
- `source_type` (text)
- `county_code` (integer) (nullable) - 100.0% NULL
- `file_name` (text) (nullable) - 100.0% NULL
- `file_size` (bigint) (nullable) - 100.0% NULL
- `file_hash` (text) (nullable) - 100.0% NULL
- `rows_inserted` (integer) (nullable)
- `rows_updated` (integer) (nullable)
- `rows_failed` (integer) (nullable)
- ... and 6 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "run_timestamp": "2025-10-05 18:43:54.518402+00:00",
  "source_type": "ORCHESTRATOR",
  "county_code": null,
  "file_name": null,
  "file_size": null,
  "file_hash": null,
  "rows_inserted": 0,
  "rows_updated": 0,
  "rows_failed": 0,
  "duration_seconds": null,
  "ai_quality_score": 100,
  "status": "SUCCESS",
  "error_message": null,
  "completed_at": null,
  "started_at": "2025-10-16 21:04:41.079370+00:00"
}
```

### notification_history

- **Records:** 2
- **Size:** 80 kB
- **Columns:** 16
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `user_id` (text)
- `parcel_id` (text)
- `county` (text)
- `notification_type` (text)
- `delivery_method` (text)
- `old_value` (jsonb) (nullable) - 100.0% NULL
- `new_value` (jsonb) (nullable) - 100.0% NULL
- `change_summary` (text) (nullable)
- `sent_at` (timestamp with time zone) (nullable)
- ... and 6 more columns

**Sample Record (first):**
```json
{
  "id": 3,
  "user_id": "test-user-notifications",
  "parcel_id": "TEST123",
  "county": "JEFFERSON",
  "notification_type": "score_change",
  "delivery_method": "email",
  "old_value": null,
  "new_value": null,
  "change_summary": "Score increased by 25 points",
  "sent_at": "2025-09-21 05:39:33.624032+00:00",
  "delivered_at": null,
  "status": "delivered",
  "error_message": null,
  "subject": "Property Alert: Score change",
  "body": "Test email body",
  "created_at": "2025-09-21 05:39:33.624032+00:00"
}
```

### property_change_log

- **Records:** 2
- **Size:** 64 kB
- **Columns:** 15
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `county` (text)
- `change_type` (text)
- `field_name` (text)
- `old_value` (text) (nullable)
- `new_value` (text) (nullable)
- `change_magnitude` (numeric) (nullable)
- `old_score` (numeric) (nullable)
- `new_score` (numeric) (nullable)
- ... and 5 more columns

**Sample Record (first):**
```json
{
  "id": 5,
  "parcel_id": "TEST123",
  "county": "JEFFERSON",
  "change_type": "score_change",
  "field_name": "score_v1",
  "old_value": "75",
  "new_value": "100",
  "change_magnitude": "25.00",
  "old_score": "75.00",
  "new_score": "100.00",
  "score_diff": "25.00",
  "detected_at": "2025-09-21 05:39:32.828649+00:00",
  "processed_at": null,
  "notifications_sent": 0,
  "scoring_run_id": "synthetic_test_20250921_013931"
}
```

### sunbiz_monitoring_agents

- **Records:** 2
- **Size:** 48 kB
- **Columns:** 10
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `agent_name` (character varying)
- `agent_type` (character varying) (nullable)
- `last_check` (timestamp without time zone) (nullable) - 100.0% NULL
- `next_check` (timestamp without time zone) (nullable) - 100.0% NULL
- `files_found` (integer) (nullable)
- `files_processed` (integer) (nullable)
- `last_error` (text) (nullable) - 100.0% NULL
- `enabled` (boolean) (nullable)
- `created_at` (timestamp without time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "agent_name": "Sunbiz_Daily_Monitor",
  "agent_type": "daily_check",
  "last_check": null,
  "next_check": null,
  "files_found": 0,
  "files_processed": 0,
  "last_error": null,
  "enabled": true,
  "created_at": "2025-09-05 13:38:49.716633"
}
```

### ab_validation_results

- **Records:** 1
- **Size:** 48 kB
- **Columns:** 7
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `validation_id` (text) (nullable)
- `properties_tested` (integer) (nullable)
- `gate_passed` (boolean) (nullable)
- `avg_improvement` (numeric) (nullable)
- `results_json` (jsonb) (nullable)
- `created_at` (timestamp with time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "validation_id": "ab_test_20250921_024508",
  "properties_tested": 500,
  "gate_passed": false,
  "avg_improvement": "-77.99",
  "results_json": "{'overall': {'avg_score_ml': 8.2, 'avg_score_v1': 75.73, 'std_score_v1': 14.27, 'avg_score_final': 48.72, 'std_score_final': 5.18}, 'thresholds': {'50': {'hit_rate_v1': 1.0, 'hit_rate_final': 0.88, 'improvement_pct': -11.94, 'passes_10pct_improvement': False}, '60': {'hit_rate_v1': 1.22, 'hit_rate_final': 0.0, 'improvement_pct': -100.0, 'passes_10pct_improvement': False}, '70': {'hit_rate_v1': 1.39, 'hit_rate_final': 0.0, 'improvement_pct': -100.0, 'passes_10pct_improvement': False}, '80': {'hit_rate_v1': 0.99, 'hit_rate_final': 0.0, 'improvement_pct': -100.0, 'passes_10pct_improvement': False}}, 'gate_passed': False, 'properties_tested': 500, 'properties_with_recent_sales': 5}",
  "created_at": "2025-09-21 06:45:08.493585+00:00"
}
```

### document_alerts

- **Records:** 1
- **Size:** 80 kB
- **Columns:** 17
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `user_id` (text)
- `alert_name` (text)
- `document_categories` (ARRAY) (nullable)
- `counties` (ARRAY) (nullable)
- `keywords` (ARRAY) (nullable)
- `parcel_ids` (ARRAY) (nullable)
- `document_date_from` (date) (nullable) - 100.0% NULL
- `document_date_to` (date) (nullable) - 100.0% NULL
- `enabled` (boolean) (nullable)
- ... and 7 more columns

**Sample Record (first):**
```json
{
  "id": 1,
  "user_id": "test-alert-user",
  "alert_name": "Tax Certificate Alerts for Broward",
  "document_categories": "['TAX_CERT']",
  "counties": "['BROWARD']",
  "keywords": "['certificate', 'tax']",
  "parcel_ids": "[]",
  "document_date_from": null,
  "document_date_to": null,
  "enabled": true,
  "notification_method": "email",
  "frequency": "immediate",
  "last_checked_at": "2025-09-21 06:19:18.206315+00:00",
  "last_triggered_at": null,
  "trigger_count": 0,
  "created_at": "2025-09-21 06:19:18.105556+00:00",
  "updated_at": "2025-09-21 06:19:18.105556+00:00"
}
```

### edge_functions

- **Records:** 1
- **Size:** 48 kB
- **Columns:** 4
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `name` (character varying)
- `code` (text) (nullable)
- `created_at` (timestamp without time zone) (nullable)
- `updated_at` (timestamp without time zone) (nullable)

**Sample Record (first):**
```json
{
  "name": "fetch-sunbiz",
  "code": "aW1wb3J0IHsgc2VydmUgfSBmcm9tICJodHRwczovL2Rlbm8ubGFuZC9zdGRAMC4xNjguMC9odHRwL3NlcnZlci50cyIKaW1wb3J0IHsgY3JlYXRlQ2xpZW50IH0gZnJvbSAnaHR0cHM6Ly9lc20uc2gvQHN1cGFiYXNlL3N1cGFiYXNlLWpzQDIuMzkuMycKCmNvbnN0IGNvcnNIZWFkZXJzID0gewogICdBY2Nlc3MtQ29udHJvbC1BbGxvdy1PcmlnaW4nOiAnKicsCiAgJ0FjY2Vzcy1Db250cm9sLUFsbG93LUhlYWRlcnMnOiAnYXV0aG9yaXphdGlvbiwgeC1jbGllbnQtaW5mbywgYXBpa2V5LCBjb250ZW50LXR5cGUnLAp9CgpzZXJ2ZShhc3luYyAocmVxKSA9PiB7CiAgLy8gSGFuZGxlIENPUlMKICBpZiAocmVxLm1ldGhvZCA9PT0gJ09QVElPTlMnKSB7CiAgICByZXR1cm4gbmV3IFJlc3BvbnNlKCdvaycsIHsgaGVhZGVyczogY29yc0hlYWRlcnMgfSkKICB9CgogIHRyeSB7CiAgICBjb25zdCB7IGRhdGFfdHlwZSwgZmlsZW5hbWUsIGFjdGlvbiB9ID0gYXdhaXQgcmVxLmpzb24oKQogICAgCiAgICAvLyBJbml0aWFsaXplIFN1cGFiYXNlIGNsaWVudAogICAgY29uc3Qgc3VwYWJhc2VVcmwgPSBEZW5vLmVudi5nZXQoJ1NVUEFCQVNFX1VSTCcpIQogICAgY29uc3Qgc3VwYWJhc2VTZXJ2aWNlS2V5ID0gRGVuby5lbnYuZ2V0KCdTVVBBQkFTRV9TRVJWSUNFX1JPTEVfS0VZJykhCiAgICBjb25zdCBzdXBhYmFzZSA9IGNyZWF0ZUNsaWVudChzdXBhYmFzZVVybCwgc3VwYWJhc2VTZXJ2aWNlS2V5KQoKICAgIGlmIChhY3Rpb24gPT09ICdsaXN0JykgewogICAgICAvLyBMaXN0IGF2YWlsYWJsZSBmaWxlcyBpbiBGVFAgZGlyZWN0b3J5CiAgICAgIGNvbnN0IGZ0cFVybCA9IGBmdHA6Ly9mdHAuZG9zLnN0YXRlLmZsLnVzL3B1YmxpYy9kb2MvJHtkYXRhX3R5cGV9L2AKICAgICAgCiAgICAgIC8vIFRyeSBIVFRQIG1pcnJvciBmaXJzdCAobW9yZSByZWxpYWJsZSkKICAgICAgY29uc3QgaHR0cFVybCA9IGZ0cFVybC5yZXBsYWNlKCdmdHA6Ly8nLCAnaHR0cDovLycpCiAgICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goaHR0cFVybCwgeyAKICAgICAgICBtZXRob2Q6ICdHRVQnLAogICAgICAgIGhlYWRlcnM6IHsgJ1VzZXItQWdlbnQnOiAnTW96aWxsYS81LjAnIH0KICAgICAgfSkKICAgICAgCiAgICAgIGlmIChyZXNwb25zZS5vaykgewogICAgICAgIGNvbnN0IGh0bWwgPSBhd2FpdCByZXNwb25zZS50ZXh0KCkKICAgICAgICAKICAgICAgICAvLyBQYXJzZSBkaXJlY3RvcnkgbGlzdGluZwogICAgICAgIGNvbnN0IGZpbGVzID0gW10KICAgICAgICBjb25zdCBsaW5rUmVnZXggPSAvPGEgaHJlZj0iKFteIl0rXC4odHh0fHppcCkpIj4oW148XSspPFwvYT4vZ2kKICAgICAgICBsZXQgbWF0Y2gKICAgICAgICAKICAgICAgICB3aGlsZSAoKG1hdGNoID0gbGlua1JlZ2V4LmV4ZWMoaHRtbCkpICE9PSBudWxsKSB7CiAgICAgICAgICBmaWxlcy5wdXNoKHsKICAgICAgICAgICAgZmlsZW5hbWU6IG1hdGNoWzFdLAogICAgICAgICAgICBkaXNwbGF5OiBtYXRjaFszXSwKICAgICAgICAgICAgdHlwZTogbWF0Y2hbMl0KICAgICAgICAgIH0pCiAgICAgICAgfQogICAgICAgIAogICAgICAgIC8vIFN0b3JlIGxpc3RpbmcgaW4gZGF0YWJhc2UKICAgICAgICBhd2FpdCBzdXBhYmFzZS5mcm9tKCdzdW5iaXpfZG93bmxvYWRfam9icycpLmluc2VydCh7CiAgICAgICAgICBkYXRhX3R5cGUsCiAgICAgICAgICBzdGF0dXM6ICdsaXN0aW5nX2ZvdW5kJywKICAgICAgICAgIGZpbGVfY291bnQ6IGZpbGVzLmxlbmd0aCwKICAgICAgICAgIGVycm9yX21lc3NhZ2U6IEpTT04uc3RyaW5naWZ5KGZpbGVzLnNsaWNlKDAsIDEwKSkgLy8gU2FtcGxlCiAgICAgICAgfSkKICAgICAgICAKICAgICAgICByZXR1cm4gbmV3IFJlc3BvbnNlKEpTT04uc3RyaW5naWZ5KHsKICAgICAgICAgIHN1Y2Nlc3M6IHRydWUsCiAgICAgICAgICBkYXRhX3R5cGUsCiAgICAgICAgICBmaWxlX2NvdW50OiBmaWxlcy5sZW5ndGgsCiAgICAgICAgICBmaWxlczogZmlsZXMuc2xpY2UoMCwgMTAwKSwgLy8gUmV0dXJuIGZpcnN0IDEwMCBmaWxlcwogICAgICAgICAgbWVzc2FnZTogJ0RpcmVjdG9yeSBsaXN0aW5nIHJldHJpZXZlZCcKICAgICAgICB9KSwgeyBoZWFkZXJzOiB7IC4uLmNvcnNIZWFkZXJzLCAnQ29udGVudC1UeXBlJzogJ2FwcGxpY2F0aW9uL2pzb24nIH0gfSkKICAgICAgfQogICAgfQogICAgCiAgICBpZiAoYWN0aW9uID09PSAnZG93bmxvYWQnKSB7CiAgICAgIC8vIERvd25sb2FkIHNwZWNpZmljIGZpbGUgdG8gU3VwYWJhc2UgU3RvcmFnZQogICAgICBjb25zdCBmdHBVcmwgPSBgZnRwOi8vZnRwLmRvcy5zdGF0ZS5mbC51cy9wdWJsaWMvZG9jLyR7ZGF0YV90eXBlfS8ke2ZpbGVuYW1lfWAKICAgICAgY29uc3QgaHR0cFVybCA9IGZ0cFVybC5yZXBsYWNlKCdmdHA6Ly8nLCAnaHR0cDovLycpCiAgICAgIAogICAgICBjb25zb2xlLmxvZyhgRG93bmxvYWRpbmc6ICR7aHR0cFVybH1gKQogICAgICAKICAgICAgLy8gU3RyZWFtIGRvd25sb2FkCiAgICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goaHR0cFVybCwgewogICAgICAgIG1ldGhvZDogJ0dFVCcsCiAgICAgICAgaGVhZGVyczogeyAnVXNlci1BZ2VudCc6ICdNb3ppbGxhLzUuMCcgfQogICAgICB9KQogICAgICAKICAgICAgaWYgKHJlc3BvbnNlLm9rKSB7CiAgICAgICAgY29uc3QgYXJyYXlCdWZmZXIgPSBhd2FpdCByZXNwb25zZS5hcnJheUJ1ZmZlcigpCiAgICAgICAgY29uc3QgdWludDhBcnJheSA9IG5ldyBVaW50OEFycmF5KGFycmF5QnVmZmVyKQogICAgICAgIAogICAgICAgIC8vIFVwbG9hZCB0byBTdXBhYmFzZSBTdG9yYWdlCiAgICAgICAgY29uc3Qgc3RvcmFnZVBhdGggPSBgJHtkYXRhX3R5cGV9LyR7ZmlsZW5hbWV9YAogICAgICAgIGNvbnN0IHsgZGF0YTogdXBsb2FkRGF0YSwgZXJyb3I6IHVwbG9hZEVycm9yIH0gPSBhd2FpdCBzdXBhYmFzZQogICAgICAgICAgLnN0b3JhZ2UKICAgICAgICAgIC5mcm9tKCdzdW5iaXotZGF0YScpCiAgICAgICAgICAudXBsb2FkKHN0b3JhZ2VQYXRoLCB1aW50OEFycmF5LCB7CiAgICAgICAgICAgIGNvbnRlbnRUeXBlOiBmaWxlbmFtZS5lbmRzV2l0aCgnLnppcCcpID8gJ2FwcGxpY2F0aW9uL3ppcCcgOiAndGV4dC9wbGFpbicsCiAgICAgICAgICAgIHVwc2VydDogdHJ1ZQogICAgICAgICAgfSkKICAgICAgICAKICAgICAgICBpZiAodXBsb2FkRXJyb3IpIHRocm93IHVwbG9hZEVycm9yCiAgICAgICAgCiAgICAgICAgLy8gQ2hlY2sgZm9yIGVtYWlscyBpbiB0ZXh0IGZpbGVzCiAgICAgICAgbGV0IGVtYWlsQ291bnQgPSAwCiAgICAgICAgbGV0IHBob25lQ291bnQgPSAwCiAgICAgICAgCiAgICAgICAgaWYgKGZpbGVuYW1lLmVuZHNXaXRoKCcudHh0JykpIHsKICAgICAgICAgIGNvbnN0IHRleHQgPSBuZXcgVGV4dERlY29kZXIoKS5kZWNvZGUodWludDhBcnJheSkKICAgICAgICAgIGVtYWlsQ291bnQgPSAodGV4dC5tYXRjaCgvW2EtekEtWjAtOS5fJSstXStAW2EtekEtWjAtOS4tXStcLlthLXpBLVpdezIsfS9nKSB8fCBbXSkubGVuZ3RoCiAgICAgICAgICBwaG9uZUNvdW50ID0gKHRleHQubWF0Y2goL1xiXGR7M31bLS5dP1xkezN9Wy0uXT9cZHs0fVxiL2cpIHx8IFtdKS5sZW5ndGgKICAgICAgICB9CiAgICAgICAgCiAgICAgICAgLy8gVXBkYXRlIGRhdGFiYXNlCiAgICAgICAgYXdhaXQgc3VwYWJhc2UuZnJvbSgnc3VuYml6X2Rvd25sb2FkX2pvYnMnKS5pbnNlcnQoewogICAgICAgICAgZGF0YV90eXBlLAogICAgICAgICAgc3RhdHVzOiAnZG93bmxvYWRlZCcsCiAgICAgICAgICBmaWxlX2NvdW50OiAxLAogICAgICAgICAgdG90YWxfc2l6ZV9ieXRlczogYXJyYXlCdWZmZXIuYnl0ZUxlbmd0aCwKICAgICAgICAgIGVycm9yX21lc3NhZ2U6IEpTT04uc3RyaW5naWZ5KHsKICAgICAgICAgICAgZmlsZW5hbWUsCiAgICAgICAgICAgIHNpemU6IGFycmF5QnVmZmVyLmJ5dGVMZW5ndGgsCiAgICAgICAgICAgIGVtYWlsQ291bnQsCiAgICAgICAgICAgIHBob25lQ291bnQsCiAgICAgICAgICAgIHN0b3JhZ2VQYXRoCiAgICAgICAgICB9KSwKICAgICAgICAgIGNvbXBsZXRlZF9hdDogbmV3IERhdGUoKS50b0lTT1N0cmluZygpCiAgICAgICAgfSkKICAgICAgICAKICAgICAgICByZXR1cm4gbmV3IFJlc3BvbnNlKEpTT04uc3RyaW5naWZ5KHsKICAgICAgICAgIHN1Y2Nlc3M6IHRydWUsCiAgICAgICAgICBmaWxlbmFtZSwKICAgICAgICAgIHNpemU6IGFycmF5QnVmZmVyLmJ5dGVMZW5ndGgsCiAgICAgICAgICBlbWFpbENvdW50LAogICAgICAgICAgcGhvbmVDb3VudCwKICAgICAgICAgIHN0b3JhZ2VQYXRoLAogICAgICAgICAgbWVzc2FnZTogYEZpbGUgdXBsb2FkZWQgdG8gU3VwYWJhc2UgU3RvcmFnZWAKICAgICAgICB9KSwgeyBoZWFkZXJzOiB7IC4uLmNvcnNIZWFkZXJzLCAnQ29udGVudC1UeXBlJzogJ2FwcGxpY2F0aW9uL2pzb24nIH0gfSkKICAgICAgfQogICAgfQogICAgCiAgICBpZiAoYWN0aW9uID09PSAnc3RyZWFtJykgewogICAgICAvLyBTdHJlYW0gZGlyZWN0bHkgZm9yIG1lbXZpZCBwcm9jZXNzaW5nCiAgICAgIGNvbnN0IGZ0cFVybCA9IGBmdHA6Ly9mdHAuZG9zLnN0YXRlLmZsLnVzL3B1YmxpYy9kb2MvJHtkYXRhX3R5cGV9LyR7ZmlsZW5hbWV9YAogICAgICBjb25zdCBodHRwVXJsID0gZnRwVXJsLnJlcGxhY2UoJ2Z0cDovLycsICdodHRwOi8vJykKICAgICAgCiAgICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goaHR0cFVybCwgewogICAgICAgIG1ldGhvZDogJ0dFVCcsCiAgICAgICAgaGVhZGVyczogeyAnVXNlci1BZ2VudCc6ICdNb3ppbGxhLzUuMCcgfQogICAgICB9KQogICAgICAKICAgICAgaWYgKHJlc3BvbnNlLm9rKSB7CiAgICAgICAgLy8gUmV0dXJuIHN0cmVhbWluZyByZXNwb25zZSBmb3IgZGlyZWN0IHBpcGVsaW5lIHByb2Nlc3NpbmcKICAgICAgICByZXR1cm4gbmV3IFJlc3BvbnNlKHJlc3BvbnNlLmJvZHksIHsKICAgICAgICAgIGhlYWRlcnM6IHsKICAgICAgICAgICAgLi4uY29yc0hlYWRlcnMsCiAgICAgICAgICAgICdDb250ZW50LVR5cGUnOiBmaWxlbmFtZS5lbmRzV2l0aCgnLnppcCcpID8gJ2FwcGxpY2F0aW9uL3ppcCcgOiAndGV4dC9wbGFpbicsCiAgICAgICAgICAgICdYLUVtYWlsLUNvdW50JzogJzAnLCAvLyBXaWxsIGJlIHVwZGF0ZWQgYnkgcGlwZWxpbmUKICAgICAgICAgICAgJ1gtRGF0YS1UeXBlJzogZGF0YV90eXBlLAogICAgICAgICAgICAnWC1GaWxlbmFtZSc6IGZpbGVuYW1lCiAgICAgICAgICB9CiAgICAgICAgfSkKICAgICAgfQogICAgfQogICAgCiAgICByZXR1cm4gbmV3IFJlc3BvbnNlKEpTT04uc3RyaW5naWZ5KHsKICAgICAgZXJyb3I6ICdJbnZhbGlkIGFjdGlvbiBvciByZXF1ZXN0IGZhaWxlZCcsCiAgICAgIHZhbGlkQWN0aW9uczogWydsaXN0JywgJ2Rvd25sb2FkJywgJ3N0cmVhbSddCiAgICB9KSwgeyAKICAgICAgc3RhdHVzOiA0MDAsCiAgICAgIGhlYWRlcnM6IHsgLi4uY29yc0hlYWRlcnMsICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicgfSAKICAgIH0pCiAgICAKICB9IGNhdGNoIChlcnJvcikgewogICAgY29uc29sZS5lcnJvcignRWRnZSBmdW5jdGlvbiBlcnJvcjonLCBlcnJvcikKICAgIHJldHVybiBuZXcgUmVzcG9uc2UoSlNPTi5zdHJpbmdpZnkoewogICAgICBlcnJvcjogZXJyb3IubWVzc2FnZQogICAgfSksIHsgCiAgICAgIHN0YXR1czogNTAwLAogICAgICBoZWFkZXJzOiB7IC4uLmNvcnNIZWFkZXJzLCAnQ29udGVudC1UeXBlJzogJ2FwcGxpY2F0aW9uL2pzb24nIH0gCiAgICB9KQogIH0KfSk=",
  "created_at": "2025-09-11 02:22:11.228651",
  "updated_at": "2025-09-11 02:22:11.228651"
}
```

### florida_permits

- **Records:** 1
- **Size:** 32 kB
- **Columns:** 8
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `permit_number` (character varying)
- `parcel_id` (character varying) (nullable)
- `property_address` (character varying) (nullable)
- `permit_type` (character varying) (nullable)
- `description` (text) (nullable)
- `status` (character varying) (nullable)
- `created_at` (timestamp without time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "permit_number": "B24-001234",
  "parcel_id": "504231242720",
  "property_address": "3920 SW 53 CT",
  "permit_type": "Building",
  "description": "Roof Replacement",
  "status": "Active",
  "created_at": "2025-09-07 21:22:32.056307"
}
```

### nav_assessments

- **Records:** 1
- **Size:** 56 kB
- **Columns:** 9
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (character varying)
- `tax_year` (integer)
- `just_value` (numeric) (nullable) - 100.0% NULL
- `assessed_value` (numeric) (nullable)
- `taxable_value` (numeric) (nullable)
- `land_value` (numeric) (nullable) - 100.0% NULL
- `building_value` (numeric) (nullable) - 100.0% NULL
- `created_at` (timestamp without time zone) (nullable)

**Sample Record (first):**
```json
{
  "id": 1,
  "parcel_id": "504231242720",
  "tax_year": 2024,
  "just_value": null,
  "assessed_value": "285000.00",
  "taxable_value": "260000.00",
  "land_value": null,
  "building_value": null,
  "created_at": "2025-09-07 21:22:32.056307"
}
```

### notification_queue

- **Records:** 1
- **Size:** 64 kB
- **Columns:** 14
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `user_id` (text)
- `parcel_id` (text)
- `county` (text)
- `change_types` (ARRAY)
- `aggregated_changes` (jsonb)
- `first_change_at` (timestamp with time zone)
- `last_change_at` (timestamp with time zone) (nullable)
- `scheduled_send_at` (timestamp with time zone)
- `status` (text) (nullable)
- ... and 4 more columns

**Sample Record (first):**
```json
{
  "id": 3,
  "user_id": "test-user-notifications",
  "parcel_id": "TEST123",
  "county": "JEFFERSON",
  "change_types": "['score_change', 'ownership_change']",
  "aggregated_changes": "{'changes': [{'county': 'JEFFERSON', 'new_score': 100.0, 'new_value': '100', 'old_score': 75.0, 'old_value': '75', 'parcel_id': 'TEST123', 'field_name': 'score_v1', 'score_diff': 25.0, 'change_type': 'score_change', 'change_magnitude': 25.0}, {'county': 'JEFFERSON', 'new_value': 'TEST HOLDINGS CORP', 'old_value': 'TEST PROPERTY LLC', 'parcel_id': 'TEST123', 'field_name': 'owner_name', 'change_type': 'ownership_change', 'change_magnitude': 100.0}], 'summary': '2 changes detected', 'change_types': ['score_change', 'ownership_change']}",
  "first_change_at": "2025-09-21 01:39:33.195672+00:00",
  "last_change_at": "2025-09-21 01:39:33.195672+00:00",
  "scheduled_send_at": "2025-09-21 01:39:33.195672+00:00",
  "status": "sent",
  "attempts": 0,
  "max_attempts": 3,
  "created_at": "2025-09-21 05:39:33.509119+00:00",
  "updated_at": "2025-09-21 05:39:33.509119+00:00"
}
```

### sunbiz_fictitious

- **Records:** 1
- **Size:** 240 kB
- **Columns:** 17
- **Indexes:** 14
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `name` (character varying) (nullable) - 100.0% NULL
- `owner_name` (character varying) (nullable) - 100.0% NULL
- `owner_addr1` (character varying) (nullable) - 100.0% NULL
- `owner_addr2` (character varying) (nullable) - 100.0% NULL
- `owner_city` (character varying) (nullable) - 100.0% NULL
- `owner_state` (character varying) (nullable) - 100.0% NULL
- `owner_zip` (character varying) (nullable) - 100.0% NULL
- `filed_date` (date) (nullable) - 100.0% NULL
- ... and 7 more columns

**Sample Record (first):**
```json
{
  "id": 6,
  "doc_number": "L24000123456",
  "name": null,
  "owner_name": null,
  "owner_addr1": null,
  "owner_addr2": null,
  "owner_city": null,
  "owner_state": null,
  "owner_zip": null,
  "filed_date": null,
  "expires_date": null,
  "county": null,
  "file_type": null,
  "subtype": null,
  "source_file": null,
  "import_date": "2025-09-19 21:26:16.917625",
  "updated_at": null
}
```

### agent_activity_logs

- **Records:** 0
- **Size:** 16 kB
- **Columns:** 6
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `agent_name` (character varying) (nullable)
- `activity_type` (character varying) (nullable)
- `status` (character varying) (nullable)
- `details` (jsonb) (nullable)
- `created_at` (timestamp without time zone) (nullable)

### agent_config

- **Records:** 0
- **Size:** 24 kB
- **Columns:** 5
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `agent_name` (character varying) (nullable)
- `config_key` (character varying) (nullable)
- `config_value` (text) (nullable)
- `updated_at` (timestamp without time zone) (nullable)

### agent_lion_analyses

- **Records:** 0
- **Size:** 40 kB
- **Columns:** 10
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `analysis_type` (text)
- `subject_id` (text)
- `inputs` (jsonb)
- `outputs` (jsonb)
- `formula_used` (text) (nullable)
- `assumptions` (jsonb) (nullable)
- `confidence_score` (numeric) (nullable)
- `expires_at` (timestamp with time zone) (nullable)
- `created_at` (timestamp with time zone) (nullable)

### agent_lion_conversations

- **Records:** 0
- **Size:** 840 kB
- **Columns:** 10
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `session_id` (uuid)
- `user_id` (uuid) (nullable)
- `role` (text)
- `content` (text)
- `context` (jsonb) (nullable)
- `embedding` (USER-DEFINED) (nullable)
- `tokens_used` (integer) (nullable)
- `model` (text) (nullable)
- `created_at` (timestamp with time zone) (nullable)

### agent_notifications

- **Records:** 0
- **Size:** 16 kB
- **Columns:** 5
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `agent_name` (character varying) (nullable)
- `message` (text) (nullable)
- `is_error` (boolean) (nullable)
- `timestamp` (timestamp without time zone) (nullable)

### concordbroker_docs

- **Records:** 0
- **Size:** 1656 kB
- **Columns:** 9
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `category` (text)
- `document_name` (text)
- `section_title` (text) (nullable)
- `content` (text)
- `embedding` (USER-DEFINED) (nullable)
- `metadata` (jsonb) (nullable)
- `created_at` (timestamp with time zone) (nullable)
- `updated_at` (timestamp with time zone) (nullable)

### data_source_jobs

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 16
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `job_name` (text)
- `job_type` (text)
- `status` (text)
- `schedule_enabled` (boolean) (nullable)
- `schedule_cron` (text) (nullable)
- `last_run_at` (timestamp without time zone) (nullable)
- `next_run_at` (timestamp without time zone) (nullable)
- `created_at` (timestamp without time zone) (nullable)
- `updated_at` (timestamp without time zone) (nullable)
- ... and 6 more columns

### data_source_monitor

- **Records:** 0
- **Size:** 24 kB
- **Columns:** 14
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `source_url` (text)
- `source_type` (character varying) (nullable)
- `county` (character varying) (nullable)
- `year` (integer) (nullable)
- `file_name` (character varying) (nullable)
- `file_size` (bigint) (nullable)
- `file_hash` (character varying) (nullable)
- `last_modified` (timestamp without time zone) (nullable)
- `last_checked` (timestamp without time zone) (nullable)
- ... and 4 more columns

### document_search_sessions

- **Records:** 0
- **Size:** 40 kB
- **Columns:** 14
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `session_id` (text)
- `user_id` (text) (nullable)
- `search_query` (text) (nullable)
- `filters_applied` (jsonb) (nullable)
- `results_count` (integer) (nullable)
- `documents_viewed` (ARRAY) (nullable)
- `documents_downloaded` (ARRAY) (nullable)
- `search_duration_seconds` (integer) (nullable)
- `found_relevant_documents` (boolean) (nullable)
- ... and 4 more columns

### entity_relationships

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 9
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `entity1_doc_number` (character varying)
- `entity1_name` (character varying) (nullable)
- `entity2_doc_number` (character varying)
- `entity2_name` (character varying) (nullable)
- `relationship_type` (character varying) (nullable)
- `relationship_metadata` (jsonb) (nullable)
- `confidence_score` (double precision) (nullable)
- `discovered_date` (timestamp without time zone) (nullable)

### entity_search_cache

- **Records:** 0
- **Size:** 40 kB
- **Columns:** 7
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `normalized_name` (character varying) (nullable)
- `original_name` (character varying) (nullable)
- `entity_doc_number` (character varying) (nullable)
- `entity_type` (character varying) (nullable)
- `is_active` (boolean) (nullable)
- `last_updated` (timestamp without time zone) (nullable)

### file_registry

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 11
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `source_url` (text)
- `file_name` (text)
- `file_hash` (text)
- `file_size` (bigint) (nullable)
- `file_type` (text) (nullable)
- `county_code` (integer) (nullable)
- `year` (integer) (nullable)
- `last_modified` (timestamp with time zone) (nullable)
- `first_seen` (timestamp with time zone) (nullable)
- ... and 1 more columns

### fl_nav_assessment_detail

- **Records:** 0
- **Size:** 16 kB
- **Columns:** 14
- **Indexes:** 1
- **Foreign Keys:** 9

**Columns:**
- `id` (bigint)
- `parcel_id` (character varying)
- `county` (character varying) (nullable)
- `tax_year` (integer) (nullable)
- `assessment_type` (character varying) (nullable)
- `assessment_description` (text) (nullable)
- `levying_authority` (character varying) (nullable)
- `assessment_amount` (numeric) (nullable)
- `paid_amount` (numeric) (nullable)
- `balance_due` (numeric) (nullable)
- ... and 4 more columns

### fl_nav_parcel_summary

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 15
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (character varying)
- `county` (character varying) (nullable)
- `tax_year` (integer) (nullable)
- `owner_name` (character varying) (nullable)
- `property_address` (character varying) (nullable)
- `total_nav_amount` (numeric) (nullable)
- `total_assessments` (integer) (nullable)
- `cdd_amount` (numeric) (nullable)
- `hoa_amount` (numeric) (nullable)
- ... and 5 more columns

### fl_sdf_sales

- **Records:** 0
- **Size:** 64 kB
- **Columns:** 29
- **Indexes:** 7
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (character varying)
- `county` (character varying) (nullable)
- `sale_date` (date) (nullable)
- `sale_price` (numeric) (nullable)
- `sale_type` (character varying) (nullable)
- `qualification_code` (character varying) (nullable)
- `grantor_name` (character varying) (nullable)
- `grantee_name` (character varying) (nullable)
- `property_address` (character varying) (nullable)
- ... and 19 more columns

### fl_tpp_accounts

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 28
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `account_number` (character varying)
- `owner_name` (character varying) (nullable)
- `business_name` (character varying) (nullable)
- `mailing_addr1` (character varying) (nullable)
- `mailing_addr2` (character varying) (nullable)
- `mailing_city` (character varying) (nullable)
- `mailing_state` (character varying) (nullable)
- `mailing_zip` (character varying) (nullable)
- `physical_addr1` (character varying) (nullable)
- ... and 18 more columns

### florida_business_activities

- **Records:** 0
- **Size:** 16 kB
- **Columns:** 7
- **Indexes:** 1
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `entity_id` (character varying)
- `activity_description` (text) (nullable)
- `naics_code` (character varying) (nullable)
- `sic_code` (character varying) (nullable)
- `industry_category` (character varying) (nullable)
- `created_at` (timestamp without time zone) (nullable)

### florida_entities_staging

- **Records:** 0
- **Size:** 152 kB
- **Columns:** 21
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `entity_id` (character varying)
- `entity_type` (character) (nullable)
- `business_name` (character varying) (nullable)
- `dba_name` (character varying) (nullable)
- `entity_status` (character varying) (nullable)
- `business_address_line1` (character varying) (nullable)
- `business_address_line2` (character varying) (nullable)
- `business_city` (character varying) (nullable)
- `business_state` (character) (nullable)
- `business_zip` (character varying) (nullable)
- ... and 11 more columns

### florida_raw_records

- **Records:** 0
- **Size:** 1640 kB
- **Columns:** 7
- **Indexes:** 3
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `entity_id` (character varying)
- `raw_content` (text)
- `record_type` (character varying) (nullable)
- `file_source` (character varying) (nullable)
- `embedding` (USER-DEFINED) (nullable)
- `created_at` (timestamp without time zone) (nullable)

### florida_registered_agents

- **Records:** 0
- **Size:** 40 kB
- **Columns:** 15
- **Indexes:** 3
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `entity_id` (character varying)
- `agent_name` (character varying)
- `agent_type` (character varying) (nullable)
- `address_line1` (character varying) (nullable)
- `address_line2` (character varying) (nullable)
- `city` (character varying) (nullable)
- `state` (character) (nullable)
- `zip_code` (character varying) (nullable)
- `agent_phone` (character varying) (nullable)
- ... and 5 more columns

### match_audit_log

- **Records:** 0
- **Size:** 16 kB
- **Columns:** 11
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `action` (character varying) (nullable)
- `parcel_id` (character varying) (nullable)
- `entity_doc_number` (character varying) (nullable)
- `old_confidence` (double precision) (nullable)
- `new_confidence` (double precision) (nullable)
- `old_match_type` (character varying) (nullable)
- `new_match_type` (character varying) (nullable)
- `user_id` (character varying) (nullable)
- `notes` (text) (nullable)
- ... and 1 more columns

### ml_model_metrics

- **Records:** 0
- **Size:** 24 kB
- **Columns:** 6
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `model_version` (text) (nullable)
- `metric_type` (text) (nullable)
- `metric_value` (numeric) (nullable)
- `properties_evaluated` (integer) (nullable)
- `recorded_at` (timestamp with time zone) (nullable)

### nal_staging

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 21
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `county_code` (integer)
- `parcel_id` (text) (nullable)
- `rs_id` (text) (nullable)
- `owner_name` (text) (nullable)
- `owner_addr1` (text) (nullable)
- `owner_addr2` (text) (nullable)
- `owner_city` (text) (nullable)
- `owner_state` (text) (nullable)
- `owner_zip` (text) (nullable)
- ... and 11 more columns

### nap_staging

- **Records:** 0
- **Size:** 24 kB
- **Columns:** 14
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `county_code` (integer)
- `parcel_id` (text) (nullable)
- `bedrooms` (integer) (nullable)
- `bathrooms` (integer) (nullable)
- `units` (integer) (nullable)
- `stories` (integer) (nullable)
- `year_built` (integer) (nullable)
- `total_living_area` (numeric) (nullable)
- `lot_size_sqft` (numeric) (nullable)
- ... and 4 more columns

### nav_assessment_details

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 15
- **Indexes:** 6
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `record_type` (character varying) (nullable)
- `county_number` (character varying) (nullable)
- `pa_parcel_number` (character varying) (nullable)
- `levy_identifier` (character varying) (nullable)
- `local_government_code` (integer) (nullable)
- `function_code` (integer) (nullable)
- `assessment_amount` (numeric) (nullable)
- `tax_roll_sequence_number` (integer) (nullable)
- `county_name` (character varying) (nullable)
- ... and 5 more columns

### nav_details

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 12
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `county_code` (text) (nullable)
- `county_name` (text) (nullable)
- `levy_id` (text) (nullable)
- `levy_name` (text) (nullable)
- `local_gov_code` (text) (nullable)
- `function_code` (text) (nullable)
- `assessment_amount` (numeric) (nullable)
- `tax_roll_sequence` (integer) (nullable)
- ... and 2 more columns

### nav_jobs

- **Records:** 0
- **Size:** 16 kB
- **Columns:** 14
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `job_type` (character varying) (nullable)
- `table_type` (character varying) (nullable)
- `county_number` (character varying) (nullable)
- `tax_year` (character varying) (nullable)
- `started_at` (timestamp without time zone) (nullable)
- `finished_at` (timestamp without time zone) (nullable)
- `success` (boolean) (nullable)
- `records_processed` (integer) (nullable)
- `records_created` (integer) (nullable)
- ... and 4 more columns

### nav_summaries

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 11
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `county_code` (text) (nullable)
- `county_name` (text) (nullable)
- `tax_account_number` (text) (nullable)
- `roll_type` (text) (nullable)
- `tax_year` (integer) (nullable)
- `total_assessments` (numeric) (nullable)
- `num_assessments` (integer) (nullable)
- `tax_roll_sequence` (integer) (nullable)
- ... and 1 more columns

### owner_entity_links

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 10
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `county` (text) (nullable)
- `owner_name` (text) (nullable)
- `norm_owner` (text) (nullable)
- `sunbiz_id` (bigint) (nullable)
- `corporate_name` (text) (nullable)
- `norm_corp` (text) (nullable)
- `match_type` (text) (nullable)
- `confidence` (numeric) (nullable)
- `created_at` (timestamp with time zone) (nullable)

### parcel_update_history

- **Records:** 0
- **Size:** 16 kB
- **Columns:** 10
- **Indexes:** 1
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `county` (character varying) (nullable)
- `update_type` (character varying) (nullable)
- `records_added` (integer) (nullable)
- `records_updated` (integer) (nullable)
- `records_deleted` (integer) (nullable)
- `processing_time_seconds` (double precision) (nullable)
- `success` (boolean) (nullable)
- `error_message` (text) (nullable)
- `update_date` (timestamp without time zone) (nullable)

### properties_master

- **Records:** 0
- **Size:** 80 kB
- **Columns:** 46
- **Indexes:** 8
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `folio_number` (text) (nullable)
- `county_code` (text) (nullable)
- `county_name` (text) (nullable)
- `property_address` (text) (nullable)
- `property_city` (text) (nullable)
- `property_state` (text) (nullable)
- `property_zip` (text) (nullable)
- `latitude` (numeric) (nullable)
- ... and 36 more columns

### property_entity_matches

- **Records:** 0
- **Size:** 64 kB
- **Columns:** 15
- **Indexes:** 7
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (character varying)
- `owner_name` (character varying) (nullable)
- `entity_doc_number` (character varying)
- `entity_name` (character varying) (nullable)
- `entity_type` (character varying) (nullable)
- `confidence_score` (double precision) (nullable)
- `match_type` (character varying) (nullable)
- `match_metadata` (jsonb) (nullable)
- `verified` (boolean) (nullable)
- ... and 5 more columns

### property_owners

- **Records:** 0
- **Size:** 56 kB
- **Columns:** 16
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `county_code` (text) (nullable)
- `county_name` (text) (nullable)
- `owner_sequence` (integer) (nullable)
- `owner_name` (text) (nullable)
- `owner_type` (text) (nullable)
- `mailing_address_1` (text) (nullable)
- `mailing_address_2` (text) (nullable)
- `mailing_city` (text) (nullable)
- ... and 6 more columns

### property_ownership_history

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 11
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (character varying)
- `prev_owner_name` (character varying) (nullable)
- `prev_entity_doc_number` (character varying) (nullable)
- `new_owner_name` (character varying) (nullable)
- `new_entity_doc_number` (character varying) (nullable)
- `change_date` (date) (nullable)
- `sale_price` (numeric) (nullable)
- `deed_type` (character varying) (nullable)
- `data_source` (character varying) (nullable)
- ... and 1 more columns

### property_sales

- **Records:** 0
- **Size:** 96 kB
- **Columns:** 18
- **Indexes:** 9
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `parcel_id` (text)
- `county_code` (text) (nullable)
- `county_name` (text) (nullable)
- `sale_date` (date) (nullable)
- `sale_price` (numeric) (nullable)
- `sale_type` (text) (nullable)
- `deed_type` (text) (nullable)
- `grantor_name` (text) (nullable)
- `grantee_name` (text) (nullable)
- ... and 8 more columns

### sdf_import_errors

- **Records:** 0
- **Size:** 40 kB
- **Columns:** 9
- **Indexes:** 4
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `county` (text)
- `chunk_id` (integer)
- `parcel_id` (text) (nullable)
- `error_type` (text)
- `error_category` (text) (nullable)
- `error_message` (text) (nullable)
- `raw_data` (jsonb) (nullable)
- `created_at` (timestamp without time zone) (nullable)

### sdf_import_progress

- **Records:** 0
- **Size:** 64 kB
- **Columns:** 16
- **Indexes:** 7
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `county` (text)
- `total_chunks` (integer) (nullable)
- `completed_chunks` (integer) (nullable)
- `total_records` (bigint) (nullable)
- `loaded_records` (bigint) (nullable)
- `error_records` (bigint) (nullable)
- `skipped_records` (bigint) (nullable)
- `status` (text) (nullable)
- `current_chunk` (integer) (nullable)
- ... and 6 more columns

### sdf_jobs

- **Records:** 0
- **Size:** 24 kB
- **Columns:** 11
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `job_id` (character varying) (nullable)
- `county` (character varying) (nullable)
- `year` (integer) (nullable)
- `status` (character varying) (nullable)
- `file_path` (text) (nullable)
- `records_processed` (integer) (nullable)
- `started_at` (timestamp without time zone) (nullable)
- `completed_at` (timestamp without time zone) (nullable)
- `error_message` (text) (nullable)
- ... and 1 more columns

### sdf_staging

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 13
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `county_code` (integer)
- `parcel_id` (text) (nullable)
- `sale_date` (date) (nullable)
- `sale_price` (numeric) (nullable)
- `sale_type` (text) (nullable)
- `qualified_sale` (boolean) (nullable)
- `or_book` (text) (nullable)
- `or_page` (text) (nullable)
- `clerk_instrument_number` (text) (nullable)
- ... and 3 more columns

### sunbiz_change_log

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 9
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `entity_id` (text)
- `change_type` (text)
- `old_value` (jsonb) (nullable)
- `new_value` (jsonb) (nullable)
- `source_file` (text) (nullable)
- `occurred_at` (timestamp without time zone) (nullable)
- `processed` (boolean) (nullable)
- `processed_at` (timestamp without time zone) (nullable)

### sunbiz_corporate_events

- **Records:** 0
- **Size:** 88 kB
- **Columns:** 7
- **Indexes:** 7
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `event_date` (date) (nullable)
- `event_type` (character varying) (nullable)
- `detail` (character varying) (nullable)
- `source_file` (character varying) (nullable)
- `import_date` (timestamp without time zone) (nullable)

### sunbiz_corporate_staging

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 28
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `source_file` (text)
- `load_batch_id` (uuid)
- `loaded_at` (timestamp without time zone) (nullable)
- `filing_number` (text) (nullable)
- `doc_number` (text) (nullable)
- `entity_name` (text) (nullable)
- `status` (text) (nullable)
- `filing_date` (text) (nullable)
- `subtype` (text) (nullable)
- ... and 18 more columns

### sunbiz_download_jobs

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 13
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `data_type` (character varying)
- `status` (character varying) (nullable)
- `file_count` (integer) (nullable)
- `total_size_bytes` (bigint) (nullable)
- `started_at` (timestamp without time zone) (nullable)
- `completed_at` (timestamp without time zone) (nullable)
- `error_message` (text) (nullable)
- `created_at` (timestamp without time zone) (nullable)
- `notes` (text) (nullable)
- ... and 3 more columns

### sunbiz_entity_search

- **Records:** 0
- **Size:** 96 kB
- **Columns:** 14
- **Indexes:** 7
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `entity_id` (text)
- `entity_type` (text) (nullable)
- `entity_name` (text) (nullable)
- `dba_name` (text) (nullable)
- `status` (text) (nullable)
- `address` (text) (nullable)
- `city` (text) (nullable)
- `state` (text) (nullable)
- `zip` (text) (nullable)
- ... and 4 more columns

### sunbiz_events_staging

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 9
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `source_file` (text)
- `load_batch_id` (uuid)
- `loaded_at` (timestamp without time zone) (nullable)
- `filing_number` (text) (nullable)
- `event_date` (text) (nullable)
- `event_type` (text) (nullable)
- `description` (text) (nullable)
- `raw_line` (text) (nullable)

### sunbiz_fictitious_events

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 6
- **Indexes:** 4
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `event_date` (date) (nullable)
- `event_type` (character varying) (nullable)
- `source_file` (character varying) (nullable)
- `import_date` (timestamp without time zone) (nullable)

### sunbiz_fictitious_staging

- **Records:** 0
- **Size:** 32 kB
- **Columns:** 16
- **Indexes:** 3
- **Foreign Keys:** 0

**Columns:**
- `id` (uuid)
- `source_file` (text)
- `load_batch_id` (uuid)
- `loaded_at` (timestamp without time zone) (nullable)
- `filing_number` (text) (nullable)
- `business_name` (text) (nullable)
- `owner_name` (text) (nullable)
- `filed_date` (text) (nullable)
- `expiration_date` (text) (nullable)
- `status` (text) (nullable)
- ... and 6 more columns

### sunbiz_import_log

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 7
- **Indexes:** 5
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `file_type` (character varying) (nullable)
- `source_file` (character varying) (nullable)
- `records_imported` (integer) (nullable)
- `import_date` (timestamp without time zone) (nullable)
- `success` (boolean) (nullable)
- `error_message` (text) (nullable)

### sunbiz_lien_debtors

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 6
- **Indexes:** 4
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `debtor_name` (character varying) (nullable)
- `debtor_addr` (character varying) (nullable)
- `source_file` (character varying) (nullable)
- `import_date` (timestamp without time zone) (nullable)

### sunbiz_lien_secured_parties

- **Records:** 0
- **Size:** 40 kB
- **Columns:** 6
- **Indexes:** 3
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `party_name` (character varying) (nullable)
- `party_addr` (character varying) (nullable)
- `source_file` (character varying) (nullable)
- `import_date` (timestamp without time zone) (nullable)

### sunbiz_liens

- **Records:** 0
- **Size:** 56 kB
- **Columns:** 10
- **Indexes:** 7
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `lien_type` (character varying) (nullable)
- `filed_date` (date) (nullable)
- `lapse_date` (date) (nullable)
- `amount` (numeric) (nullable)
- `file_type` (character varying) (nullable)
- `subtype` (character varying) (nullable)
- `source_file` (character varying) (nullable)
- `import_date` (timestamp without time zone) (nullable)

### sunbiz_marks

- **Records:** 0
- **Size:** 88 kB
- **Columns:** 13
- **Indexes:** 8
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `mark_text` (character varying) (nullable)
- `mark_type` (character varying) (nullable)
- `status` (character varying) (nullable)
- `filed_date` (date) (nullable)
- `registration_date` (date) (nullable)
- `expiration_date` (date) (nullable)
- `owner_name` (character varying) (nullable)
- `owner_addr` (character varying) (nullable)
- ... and 3 more columns

### sunbiz_partnership_events

- **Records:** 0
- **Size:** 24 kB
- **Columns:** 6
- **Indexes:** 3
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `event_date` (date) (nullable)
- `event_type` (character varying) (nullable)
- `source_file` (character varying) (nullable)
- `import_date` (timestamp without time zone) (nullable)

### sunbiz_partnerships

- **Records:** 0
- **Size:** 64 kB
- **Columns:** 13
- **Indexes:** 6
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `doc_number` (character varying)
- `name` (character varying) (nullable)
- `status` (character varying) (nullable)
- `filed_date` (date) (nullable)
- `prin_addr1` (character varying) (nullable)
- `prin_city` (character varying) (nullable)
- `prin_state` (character varying) (nullable)
- `prin_zip` (character varying) (nullable)
- `file_type` (character varying) (nullable)
- ... and 3 more columns

### sunbiz_principal_data

- **Records:** 0
- **Size:** 80 kB
- **Columns:** 10
- **Indexes:** 8
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `doc_number` (character varying) (nullable)
- `entity_name` (character varying) (nullable)
- `principal_name` (character varying) (nullable)
- `principal_title` (character varying) (nullable)
- `principal_address` (character varying) (nullable)
- `principal_email` (character varying) (nullable)
- `principal_phone` (character varying) (nullable)
- `source_file` (character varying) (nullable)
- `import_date` (timestamp without time zone) (nullable)

### sunbiz_processed_files

- **Records:** 0
- **Size:** 16 kB
- **Columns:** 7
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `filename` (character varying) (nullable)
- `file_hash` (character varying) (nullable)
- `file_size` (bigint) (nullable)
- `processed_date` (timestamp without time zone) (nullable)
- `records_count` (integer) (nullable)
- `processing_time_seconds` (double precision) (nullable)

### sunbiz_sftp_downloads

- **Records:** 0
- **Size:** 24 kB
- **Columns:** 10
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `file_name` (character varying) (nullable)
- `file_type` (character varying) (nullable)
- `file_size` (bigint) (nullable)
- `download_date` (timestamp without time zone) (nullable)
- `process_date` (timestamp without time zone) (nullable)
- `status` (character varying) (nullable)
- `records_processed` (integer) (nullable)
- `error_message` (text) (nullable)
- `created_at` (timestamp without time zone) (nullable)

### tpp_jobs

- **Records:** 0
- **Size:** 24 kB
- **Columns:** 11
- **Indexes:** 2
- **Foreign Keys:** 0

**Columns:**
- `id` (bigint)
- `job_id` (character varying) (nullable)
- `county` (character varying) (nullable)
- `year` (integer) (nullable)
- `status` (character varying) (nullable)
- `file_path` (text) (nullable)
- `records_processed` (integer) (nullable)
- `started_at` (timestamp without time zone) (nullable)
- `completed_at` (timestamp without time zone) (nullable)
- `error_message` (text) (nullable)
- ... and 1 more columns

### validation_errors

- **Records:** 0
- **Size:** 40 kB
- **Columns:** 9
- **Indexes:** 4
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `run_id` (bigint) (nullable)
- `county_code` (integer) (nullable)
- `parcel_id` (text) (nullable)
- `error_type` (text)
- `error_message` (text) (nullable)
- `raw_data` (jsonb) (nullable)
- `severity` (text) (nullable)
- `detected_at` (timestamp with time zone) (nullable)

### validation_results

- **Records:** 0
- **Size:** 56 kB
- **Columns:** 7
- **Indexes:** 6
- **Foreign Keys:** 0

**Columns:**
- `id` (integer)
- `table_name` (character varying)
- `validation_type` (character varying)
- `passed` (boolean)
- `message` (text) (nullable)
- `details` (jsonb) (nullable)
- `timestamp` (timestamp without time zone)

### watchlist_alerts

- **Records:** 0
- **Size:** 48 kB
- **Columns:** 12
- **Indexes:** 5
- **Foreign Keys:** 1

**Columns:**
- `id` (bigint)
- `watchlist_item_id` (bigint) (nullable)
- `alert_type` (text)
- `severity` (text) (nullable)
- `change_description` (text) (nullable)
- `old_value` (text) (nullable)
- `new_value` (text) (nullable)
- `change_percentage` (numeric) (nullable)
- `created_at` (timestamp with time zone) (nullable)
- `sent_at` (timestamp with time zone) (nullable)
- ... and 2 more columns

---

## 🏠 Florida Parcels Deep Dive

- **Total Properties:** 10,304,043
- **Counties:** 73 of 67
- **Years:** 2025
- **Completeness Score:** 104.9%

### Critical Field Coverage

- **parcel_id:** 100.0% (0 missing)
- **county:** 100.0% (0 missing)
- **year:** 100.0% (0 missing)
- **owner_name:** 100.0% (1,049 missing)
- **just_value:** 100.0% (64 missing)
- **phy_addr1:** 97.5% (259,437 missing)

### County Distribution (Top 20)

- DADE: 1,249,796 properties
- BROWARD: 824,854 properties
- PALM BEACH: 622,285 properties
- LEE: 599,163 properties
- HILLSBOROUGH: 566,674 properties
- ORANGE: 553,956 properties
- MIAMI-DADE: 487,000 properties
- DUVAL: 430,919 properties
- BREVARD: 399,511 properties
- COLLIER: 349,836 properties
- PASCO: 332,226 properties
- MARION: 299,075 properties
- CHARLOTTE: 248,316 properties
- LAKE: 241,263 properties
- ST. JOHNS: 191,641 properties
- ESCAMBIA: 188,919 properties
- BAY: 173,617 properties
- ST. LUCIE: 167,779 properties
- CITRUS: 157,808 properties
- HIGHLANDS: 131,399 properties

---

## 📈 Sales History Analysis

- **Total Sales:** 637,890
- **Properties with Sales History:** 539,395
- **Date Range:** 1963-08-01 to 2025-10-01

### Data Quality Issues

- **MEDIUM:** Invalid or NULL sale prices (4,772 instances)

---

## 🏢 Sunbiz Business Entity Analysis

- **Corporate Records:** 2,030,912
- **Entity Records:** 15,013,088

### Entity Types (Top 20)

-  : 7,326,507
- 1: 2,211,473
- 2: 1,090,072
- 3: 790,824
- 4: 638,911
- 5: 568,178
- 7: 543,370
- 6: 470,197
- 8: 422,321
- 9: 351,005
- 0: 178,454
- O: 50,120
- C: 37,626
- E: 31,511
- G: 26,671
- A: 26,451
- B: 24,790
- S: 24,604
- I: 23,403
- R: 22,344

### Status Distribution

- Unknown: 2,030,890
- F: 6
- 6: 2
- 18: 2
- 16: 1
- 22: 1
- 231: 1
- 29: 1
- 41: 1
- BRAN: 1
- FL: 1
- L34741: 1
- RIVE: 1
- 0 W HO: 1
- 111 EN: 1
- 1245: 1

---

## 🚀 Optimization Recommendations

### Missing Indexes (HIGH PRIORITY)

- **dor_code_audit.parcel_id**
  ```sql
  CREATE INDEX idx_dor_code_audit_parcel_id ON dor_code_audit(parcel_id);
  ```
- **fl_nav_assessment_detail.parcel_id**
  ```sql
  CREATE INDEX idx_fl_nav_assessment_detail_parcel_id ON fl_nav_assessment_detail(parcel_id);
  ```
- **florida_business_activities.entity_id**
  ```sql
  CREATE INDEX idx_florida_business_activities_entity_id ON florida_business_activities(entity_id);
  ```
- **florida_parcels_staging.parcel_id**
  ```sql
  CREATE INDEX idx_florida_parcels_staging_parcel_id ON florida_parcels_staging(parcel_id);
  ```
- **florida_permits.parcel_id**
  ```sql
  CREATE INDEX idx_florida_permits_parcel_id ON florida_permits(parcel_id);
  ```
- **florida_raw_records.entity_id**
  ```sql
  CREATE INDEX idx_florida_raw_records_entity_id ON florida_raw_records(entity_id);
  ```
- **match_audit_log.parcel_id**
  ```sql
  CREATE INDEX idx_match_audit_log_parcel_id ON match_audit_log(parcel_id);
  ```
- **notification_queue.parcel_id**
  ```sql
  CREATE INDEX idx_notification_queue_parcel_id ON notification_queue(parcel_id);
  ```
- **tax_deed_bidding_items.parcel_id**
  ```sql
  CREATE INDEX idx_tax_deed_bidding_items_parcel_id ON tax_deed_bidding_items(parcel_id);
  ```
- **validation_errors.parcel_id**
  ```sql
  CREATE INDEX idx_validation_errors_parcel_id ON validation_errors(parcel_id);
  ```

### Missing Indexes (MEDIUM PRIORITY)

- **data_source_monitor.county**
  ```sql
  CREATE INDEX idx_data_source_monitor_county ON data_source_monitor(county);
  ```
- **fl_nav_assessment_detail.county**
  ```sql
  CREATE INDEX idx_fl_nav_assessment_detail_county ON fl_nav_assessment_detail(county);
  ```
- **fl_sdf_sales.county**
  ```sql
  CREATE INDEX idx_fl_sdf_sales_county ON fl_sdf_sales(county);
  ```
- **florida_parcels_staging.county**
  ```sql
  CREATE INDEX idx_florida_parcels_staging_county ON florida_parcels_staging(county);
  ```
- **florida_parcels_staging.sale_date**
  ```sql
  CREATE INDEX idx_florida_parcels_staging_sale_date ON florida_parcels_staging(sale_date);
  ```

### Underutilized Tables

- **ab_validation_results**: 1 records (verify if needed)
- **agent_activity_logs**: 0 records (verify if needed)
- **agent_config**: 0 records (verify if needed)
- **agent_lion_analyses**: 0 records (verify if needed)
- **agent_lion_conversations**: 0 records (verify if needed)
- **agent_notifications**: 0 records (verify if needed)
- **concordbroker_docs**: 0 records (verify if needed)
- **county_codes**: 66 records (verify if needed)
- **county_name_mappings**: 20 records (verify if needed)
- **data_source_jobs**: 0 records (verify if needed)

---

## ✅ Action Items (Prioritized)

### Immediate (P0)
3. **Create 10 high-priority indexes**

### High Priority (P1)
1. Review and fix data quality issues identified above
2. Verify all foreign key relationships are valid
3. Implement automated data quality monitoring

### Medium Priority (P2)
1. Create medium-priority indexes for performance optimization
2. Review and archive/drop underutilized tables
3. Document table purposes and data lineage

---

## 📝 Conclusion

✅ **SUCCESS:** The database contains the full Florida property dataset with excellent coverage.

The system is production-ready with minor optimization opportunities identified above.

**Overall Assessment:** 104.9% complete
