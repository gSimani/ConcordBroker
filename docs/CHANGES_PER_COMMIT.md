# Per-Commit Change Summary (last 15 commits)
Generated: 2025-11-05T15:11:45

## 5bbf6b8 — docs: Add 48-county RealAuction scraper system architecture (2025-11-05)
Author: gSimani

``
A	48_COUNTY_SCRAPER_ARCHITECTURE.md
``

## dc73bef — feat: Add Tooltip UI component for auction site links (2025-11-05)
Author: gSimani

``
M	apps/web/package-lock.json M	apps/web/package.json A	apps/web/src/components/ui/tooltip.tsx
``

## c35051b — fix: Correct metadata to reflect 48 Florida counties (not 47) (2025-11-05)
Author: gSimani

``
M	florida_realauction_sites.json M	supabase/migrations/20250105_florida_auction_sites.sql
``

## 659aca5 — feat: Integrate RealAuction site links into Property tabs (2025-11-05)
Author: gSimani

``
M	apps/web/src/components/property/tabs/ForeclosureTab.tsx M	apps/web/src/components/property/tabs/OverviewTab.tsx M	apps/web/src/components/property/tabs/TaxDeedSalesTab.tsx
``

## 4d31656 — feat: Add RealAuction site links UI components (2025-11-05)
Author: gSimani

``
A	apps/web/src/components/auction/AuctionSiteLinks.tsx A	apps/web/src/hooks/useAuctionSites.ts
``

## 5469a0c — feat: Add Florida RealAuction sites database implementation (2025-11-05)
Author: gSimani

``
A	SUPABASE_REQUEST_AUCTION_SITES.md A	florida_realauction_sites.json A	supabase/migrations/20250105_florida_auction_sites.sql
``

## 4415728 — feat: Add BROWARD direct property appraiser links with fnumber parameter (2025-11-05)
Author: gSimani

``
M	apps/web/src/utils/property-appraiser-links.ts
``

## 1617323 — fix: Update MIAMI-DADE Property Appraiser links to use direct folio search (2025-11-04)
Author: gSimani

``
M	apps/web/src/utils/property-appraiser-links.ts
``

## 681f23f — feat: Complete RealAuction Florida counties analysis - 47 counties mapped (2025-11-04)
Author: gSimani

``
A	FLORIDA_REALAUCTION_COMPLETE_MAPPING.md A	florida_counties_complete_20251104_190138.json A	scripts/analyze_realauction_clients.py A	scripts/analyze_realauction_florida_interactive.py A	scripts/extract_florida_counties_from_page.py A	scripts/extract_florida_with_chrome_devtools.py
``

## 5c83235 — feat: Enhanced Tax Deed scraping with complete data capture and SUNBIZ linking (2025-11-04)
Author: gSimani

``
A	TAX_DEED_ENHANCED_FIELDS_SUPABASE_REQUEST.md A	TAX_DEED_ENHANCED_SCRAPING_PROGRESS.md M	apps/web/src/components/property/tabs/TaxDeedSalesTab.tsx A	apps/web/src/utils/sunbiz-link.ts A	scripts/scrape_broward_complete_enhanced.py A	supabase/migrations/20251104_add_tax_deed_enhanced_fields.sql
``

## 4e3a188 — fix: Tax Deed Sales - Property Appraiser links and filter fixes (2025-11-04)
Author: gSimani

``
A	PROPERTY_APPRAISER_LINKS_FIX_COMPLETE.md A	TAX_DEED_SALES_FIXES_VERIFIED_COMPLETE.md A	TAX_DEED_SALES_TAB_FIX_COMPLETE.md M	apps/web/src/components/property/tabs/TaxDeedSalesTab.tsx A	apps/web/src/utils/property-appraiser-links.ts A	test-property-appraiser-links-fixed.cjs A	test-results/autocomplete-screenshots/02-address-autocomplete-dropdown.png A	test-results/autocomplete-screenshots/03-owner-autocomplete-dropdown.png A	test-results/autocomplete-screenshots/05-after-search-execution.png A	test-results/autocomplete-screenshots/test-report.json A	test-results/broward-links-working.png A	test-results/icon-fix-verification.json A	test-results/industrial-complete-fix-verification.json A	test-results/property-appraiser-links-fixed.png A	test-results/search-api-fix-verification.json A	test-results/tax-deed-sales-filter-complete.png A	test-tax-deed-sales-filter-complete.cjs
``

## 46730aa — docs: Add Supabase migration and instructions for parcel_id nullable (2025-11-04)
Author: gSimani

``
A	EXECUTE_THIS_IN_SUPABASE.md A	TAX_DEED_UI_ENHANCEMENTS_COMPLETE.md A	scripts/execute_parcel_nullable_migration.py A	scripts/make_parcel_id_nullable.py A	supabase/migrations/20251104_make_parcel_id_nullable.sql
``

## 3ea9a22 — fix: Improve synopsis banner readability with icons and spacing (2025-11-04)
Author: gSimani

``
M	apps/web/src/components/property/tabs/TaxDeedSalesTab.tsx
``

## a91eb44 — feat: Add searchable county dropdown with all 67 Florida counties (2025-11-04)
Author: gSimani

``
M	apps/web/src/components/property/tabs/TaxDeedSalesTab.tsx
``

## 392ecba — feat: Enhance Tax Deed Sales UI with bigger text and comprehensive statistics (2025-11-04)
Author: gSimani

``
M	apps/web/src/components/property/tabs/TaxDeedSalesTab.tsx A	scripts/scrape_broward_tax_deeds.py A	scripts/upload_tax_deed_fixed_env.py
``

