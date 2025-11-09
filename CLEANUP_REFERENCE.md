# Root Directory Cleanup Progress

## Summary
- **Starting files**: 617 Python scripts at root
- **Archived so far**: ~269 scripts
- **Remaining**: 348 scripts (still need consolidation)

## Scripts Archived
✅ 72 check_* scripts
✅ 43 verify_* scripts
✅ 17 analyze_* scripts
✅ 7 audit_* scripts
✅ 6 TEST_* scripts
✅ 40 load_* scripts
✅ 7 upload_* scripts
✅ 11 create_* scripts
✅ ~20 debug_* scripts
✅ ~25 comprehensive_* scripts
✅ ~21 deploy_* scripts

## Scripts Requiring Review (Duplicates Found)

### FLORIDA Data Scripts (15 at root)
Which ONE do you use in production?
- `florida_comprehensive_downloader.py`
- `florida_data_uploader.py`
- `florida_ftp_downloader.py`
- `florida_property_appraiser_downloader.py`
- `florida_revenue_downloader.py`
- `florida_revenue_daily_sync_system.py`
- Others...

### SUNBIZ Scripts (10 at root + 23 in apps/workers/)
Which ONE do you use in production?
- `sunbiz_downloader_final.py`
- `sunbiz_final_working.py`
- `sunbiz_working_downloader.py`
- `sunbiz_integration_system.py`
- `sunbiz_sftp_downloader.py`
- Others...

### TAX DEED Scripts (4 at root + 11 in apps/workers/)
Which ONE do you use?
- `tax_deed_auction_scraper.py`
- `final_tax_deed_scraper.py`
- In apps/workers/:
  - `tax_deed_scraper.py`
  - `tax_deed_api_scraper.py`
  - `tax_deed_auction_scraper.py`
  - Others...

### BROWARD Scripts (4 at root)
- `broward_comprehensive_property_loader.py`
- `broward_full_production_loader.py`
- `broward_property_downloader.py`
- `broward_tax_deed_final_scraper.py`

### Download Scripts (20+ duplicates)
- `download_florida_data.py`
- `download_florida_data_direct.py`
- `download-florida-data.py` (dash vs underscore!)
- `download_sunbiz_data.py`
- `download_sunbiz_direct.py`
- `download_sunbiz_sftp_new.py`
- Many more...

### Import Scripts (15+ duplicates)
NAP Import variants (7 versions!):
- `nap_batch_importer.py`
- `nap_broward_import.py`
- `nap_dedicated_importer.py`
- `nap_import_existing_columns.py`
- `nap_import_fixed.py`
- `nap_import_strategy.py`
- `nap_simple_insert.py`

Other imports:
- `import_all_sdf_files.py`
- `import_florida_parcels.py`
- `import_nal_property_data.py`
- `import_nav_assessments.py`
- `import_nav_simple.py`
- `import_sdf_sales.py`

### Database Setup Scripts (30+ duplicates)
- `setup_database.py`
- `setup_database_tables.py`
- `setup_real_database.py`
- `setup_tax_deed_table.py`
- `discover_tables_supabase.py`
- `discover_real_tables.py`
- `list_tables.py`
- `list_all_tables.py`
- Many execute_* variants

## Next Steps
1. **NEED YOUR INPUT**: Which scripts are actually used in production?
2. Move obsolete scripts to archive
3. Keep ONLY production scripts
4. Move production scripts to proper `scripts/` directory
5. Update documentation

## Archive Location
All archived scripts are in: `archive-cleanup-2025/root-scripts/`

Subdirectories:
- `check/` - 72 files
- `verify/` - 43 files
- `analyze/` - 17 files
- `audit/` - 7 files
- `test/` - 6 files
- `load/` - 40 files
- `upload/` - 7 files
- `create/` - 11 files
- `debug/` - ~20 files
- `comprehensive/` - ~25 files
- `deploy/` - ~21 files
- `utility/` - ~10 files
