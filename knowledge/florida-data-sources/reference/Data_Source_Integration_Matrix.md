# ConcordBroker Data Source Integration Matrix

## Current Integration Status

| Source | Download | Database | RAG | API | Notes |
|--------|----------|----------|-----|-----|-------|
| FL Revenue NAL | YES | florida_parcels | NO | NO | 19M+ records |
| FL Revenue SDF | YES | property_sales_history | NO | NO | 96K+ records |
| FL Revenue NAP | YES | NOT USED | NO | NO | Tangible property |
| Sunbiz Daily | YES | florida_entities | NO | SFTP | 15M+ records |
| Sunbiz Quarterly | NO | - | NO | SFTP | Full snapshots |
| Broward Daily | NO | - | NO | HTTP | County-specific |
| GIS Cadastral | NO | - | NO | REST | 10.8M parcels |
| ArcGIS Parcels | NO | - | NO | REST | Boundaries |

## Database Tables

### florida_parcels
- Source: NAL files
- Records: 19,086,633
- Key: (parcel_id, county, year)
- Updates: Daily via monitor_florida_nal_updates.py

### property_sales_history
- Source: SDF files
- Records: 96,771
- Key: parcel_id + sale date
- Updates: Manual

### florida_entities
- Source: Sunbiz SFTP
- Records: 15,013,088
- Key: entity_id
- Updates: Daily via florida_daily_updater.py

### sunbiz_corporate
- Source: Sunbiz SFTP
- Records: 2,030,912
- Key: filing_number
- Updates: Daily

## Scheduled Updates

### GitHub Actions
- daily-property-update.yml: 2 AM EST daily
- daily-sunbiz-update.yml: Sunbiz data

### Manual Scripts
- scripts/monitor_florida_nal_updates.py
- scripts/upload_nal_to_supabase.py
- apps/agents/florida_daily_updater.py
