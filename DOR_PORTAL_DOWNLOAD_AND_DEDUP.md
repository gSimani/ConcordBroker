# Florida DOR Portal: NAL, NAP, SDF — Download + Dedup Strategy

**Portal:** https://floridarevenue.com/property/dataportal/Pages/default.aspx?path=/property/dataportal/Documents/PTO%20Data%20Portal/~Public%20Records/~20251103-1264400

**Scope:** Historical years 2009–2025 for all 67 counties. This guide documents reliable download patterns for NAL, NAP, SDF and defines strict, idempotent deduplication rules we will enforce to avoid duplicates on re-runs and across P/F versions.

---

## File Types
- NAL — Names and Addresses (parcel-centric; 1 row per parcel per year)
- NAP — Tangible Personal Property (TPP; business equipment; subset of parcels)
- SDF — Sales Data File (transaction history; many rows per parcel across years)

---

## Naming Pattern and Versions
```
{TYPE}{COUNTY_CODE}{P|F}{YYYY}{VV}.csv

Examples (Gilchrist = 31):
- NAL31P202501.csv  → NAL, Preliminary, 2025, v01
- NAL31F202501.csv  → NAL, Final, 2025, v01 (preferred when available)
- SDF31P202401.csv  → SDF, Preliminary, 2024, v01
- NAP31P202401.csv  → NAP, Preliminary, 2024, v01
```
- Release: `P` = Preliminary, `F` = Final. Prefer `F`; fallback to `P` when `F` is not published.
- Version (`VV`): Increments (01, 02, …) when corrections are posted. Always take highest available version per year/county/type.

---

## Portal Structure and Download Strategy
- The SharePoint portal often nests files under “Tax Roll Data Files/{TYPE}/{YEAR}{P|F}/”. Some links may redirect via a web page (HTTP 404 placeholder with a JS redirect). Use our headless crawler utilities to resolve final URLs.
- Existing utilities in repo:
  - `scripts/crawl-dor-sharepoint.mjs` — enumerates directories and resolves redirectors
  - `scripts/download_historical_sdf.py` — SDF-focused downloader
  - `scripts/download_missing_nal_2025.py` — demonstrates pattern for NAL

Recommended approach:
1. Enumerate `{TYPE}` in [`NAL`,`NAP`,`SDF`]
2. For each `YEAR` in 2009..2025, check both `{YEAR}F/` then `{YEAR}P/` folders
3. Within, collect `{TYPE}{COUNTY_CODE}{P|F}{YYYY}{VV}.csv` and keep only the highest `VV` per county
4. Persist checksums and a manifest (CSV or JSON) with: `type, county_code, year, release, version, size, sha256, url`

Manifest fields:
- `type` (NAL/NAP/SDF)
- `county_code` (e.g., "31")
- `county_name` (resolved via mapping in `scripts/integrate_historical_data.py`)
- `year` (int)
- `release` (P/F)
- `version` (e.g., 1)
- `filename`
- `bytes`
- `sha256`
- `source_url`
- `downloaded_at`

---

## Deduplication Rules (No Duplicates)
We enforce idempotency through strong natural-key constraints and upsert behavior. These avoid duplicates across:
- Multiple runs of the same year/county
- Preliminary vs Final re-ingest (Final should overwrite preliminary)
- Higher `VV` versions replacing older versions

### NAL → `florida_parcels`
- Natural key: `(parcel_id, county, year)`
- Behavior: `INSERT ... ON CONFLICT (parcel_id, county, year) DO UPDATE`
- Rationale: NAL is 1:1 per parcel/year. If Final or higher version arrives, it cleanly overwrites previous values.
- Constraint (execute once):
```sql
ALTER TABLE public.florida_parcels
  ADD CONSTRAINT uk_parcel_county_year UNIQUE (parcel_id, county, year);
```

### NAP → `florida_tangible_personal_property` (recommended)
- Create a dedicated TPP table to avoid mixing business accounts with parcels table.
- Natural key: `(county, year, account_id)` where `account_id` = `ACCT_ID`
- Behavior: `INSERT ... ON CONFLICT (county, year, account_id) DO UPDATE`
- Table and constraint:
```sql
CREATE TABLE IF NOT EXISTS public.florida_tangible_personal_property (
  id BIGSERIAL PRIMARY KEY,
  county TEXT NOT NULL,
  year INTEGER NOT NULL,
  account_id TEXT NOT NULL,
  parcel_id TEXT,
  naics_code TEXT,
  just_value_ffe NUMERIC,
  just_value_total NUMERIC,
  assessed_value_total NUMERIC,
  exempt_value NUMERIC,
  taxable_value NUMERIC,
  business_owner_name TEXT,
  business_owner_addr TEXT,
  business_owner_city TEXT,
  business_owner_state TEXT,
  business_owner_zip TEXT,
  business_phy_addr TEXT,
  business_phy_city TEXT,
  business_phy_zip TEXT,
  data_source TEXT DEFAULT 'NAP',
  import_date TIMESTAMP DEFAULT NOW(),
  UNIQUE (county, year, account_id)
);
```

### SDF → `property_sales_history`
Two good strategies depending on your data quality preference.

Option A (simpler; current default in script):
- Natural key: `(parcel_id, county, sale_date)`
- Works if there is ≤1 sale per parcel per month. Rare edge cases could collide.
- Constraint:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uk_sales_parcel_month
  ON public.property_sales_history(parcel_id, county, sale_date);
```

Option B (stronger; recommended):
- Natural key: `(parcel_id, county, sale_date, sale_price, official_record_book, official_record_page, clerk_file_number)`
- Eliminates collisions on same-month multiple transfers; robust to duplicates across re-runs and P→F.
- Constraint:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uk_sales_natural_key
ON public.property_sales_history (
  parcel_id, county, sale_date, sale_price, official_record_book, official_record_page, clerk_file_number
);
```
- Then use `ON CONFLICT` on these columns in your loader.

Additionally (optional document-key uniqueness):
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uk_sales_doc
ON public.property_sales_history (
  county, official_record_book, official_record_page, clerk_file_number, sale_date
);
```

---

## Loader Behavior (Idempotent)
- Always upsert with the defined unique keys.
- Prefer Final releases; if Preliminary already loaded, Final will overwrite.
- If a higher version (VV) appears, it overwrites prior version rows via the same natural key.
- Keep `data_source` formatted as `DOR_{TYPE}_{release}{version}_{year}` for traceability (e.g., `DOR_SDF_F01_2024`).

---

## Implementation Pointers (Repo)
- County codes mapping lives in `scripts/integrate_historical_data.py` (`COUNTY_CODES`).
- NAL mapping used by parser is defined there (`NAL_FIELD_MAPPING`).
- SDF mapping is included (`SDF_FIELD_MAPPING`).
- For NAP, follow the field list in `DOR_FILE_STRUCTURE_MAPPING.md` (NAP section) and map to the recommended TPP table.
- Current SDF upsert uses `(parcel_id,county,sale_date)`. To switch to the stronger key, add the recommended unique index and adjust the conflict target in the uploader.

---

## Operational Checklist
- [ ] Ensure unique constraints exist (see SQL above)
- [ ] Decide on SDF key strategy (A simple vs B stronger) and align script
- [ ] Prefer Final (`F`) over Preliminary (`P`); keep only highest `VV`
- [ ] Maintain a download manifest with checksums
- [ ] Use `--dry-run` and `--limit` to validate before large uploads
- [ ] Monitor ingestion rate; adjust `--batch-size` as needed

---

## Examples
- Re-run SDF for one county/year safely (no duplicates):
```
python scripts/integrate_historical_data.py \
  --county GILCHRIST --year 2024 --mode test --types SDF --batch-size 300
```
- Dry-run NAL+SDF for Broward 2025:
```
python scripts/integrate_historical_data.py \
  --county BROWARD --year 2025 --mode test --types NAL,SDF --dry-run --limit 1000
```

---

## Notes
- SharePoint links sometimes return an HTML page that JS-redirects to the file. Our crawler handles this; avoid direct requests to the visible URL without following redirects.
- For massive backfills, consider staging tables + `INSERT … ON CONFLICT` into final tables, or `COPY` into staging for best performance.

