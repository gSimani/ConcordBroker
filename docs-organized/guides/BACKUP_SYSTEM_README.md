# Supabase Daily Backup System

## Overview
Automated daily backup system for Supabase database with compression, verification, and retention management.

## Features
- **Automated Daily Backups** at 2:00 AM via Windows Task Scheduler
- **Compressed Storage** using gzip to minimize disk space
- **Batch Processing** for large tables (10,000 records per batch)
- **Backup Verification** to ensure data integrity
- **30-Day Retention** with automatic cleanup of old backups
- **Complete Restore** capability from any backup

## Files

### Core Scripts
- `daily_supabase_backup.py` - Main backup script
- `restore_supabase_backup.py` - Interactive restore utility
- `setup_daily_backup.bat` - Windows Task Scheduler setup

### Test Scripts
- `test_backup_small.py` - Test backup with limited records
- `verify_nal_import.py` - Verify backup integrity

## Setup Instructions

### 1. Install Dependencies
```bash
pip install supabase python-dotenv
```

### 2. Configure Scheduled Backup
Run as Administrator:
```bash
setup_daily_backup.bat
```

### 3. Manual Backup
```bash
python daily_supabase_backup.py
```

### 4. Restore from Backup
```bash
python restore_supabase_backup.py
```

## Backup Specifications

### Current Configuration
- **Tables Backed Up:** florida_parcels (7.3M+ records)
- **Backup Location:** `C:/TEMP/SUPABASE_BACKUPS/backup_YYYY-MM-DD/`
- **Schedule:** Daily at 2:00 AM
- **Retention:** 30 days
- **Compression:** gzip (approximately 90% size reduction)

### Backup Process
1. Creates timestamped backup directory
2. Backs up florida_parcels table in 10,000-record batches
3. Compresses each batch using gzip
4. Creates metadata and manifest files
5. Verifies backup integrity
6. Cleans up old backups beyond retention period

### File Structure
```
C:/TEMP/SUPABASE_BACKUPS/
├── backup_2025-09-25/
│   ├── backup_manifest.json          # Summary of backup
│   ├── florida_parcels_metadata.json # Table metadata
│   ├── florida_parcels_batch_1.json.gz
│   ├── florida_parcels_batch_2.json.gz
│   └── ... (731+ batch files)
└── backup_2025-09-26/
    └── ... (next day's backup)
```

## Performance Metrics

### Test Results (1,000 records)
- **Backup Time:** 0.9 seconds
- **Original Size:** ~1.2 MB
- **Compressed Size:** 0.07 MB (94% compression)
- **Verification:** PASS

### Full Database Estimates (7.3M records)
- **Estimated Backup Time:** 4-6 hours
- **Estimated Compressed Size:** 500-800 MB
- **Batch Files:** ~731 files
- **Network Requests:** ~1,462 API calls

## Monitoring & Logs

### Log Files
- `backup.log` - Detailed backup operations log
- `restore.log` - Restore operations log

### Windows Task Scheduler
- Task Name: "Supabase Daily Backup"
- View Status: `schtasks /query /tn "Supabase Daily Backup"`
- Run Manually: `schtasks /run /tn "Supabase Daily Backup"`
- Delete Task: `schtasks /delete /tn "Supabase Daily Backup" /f`

## Disaster Recovery

### Complete Database Restore
1. Run `python restore_supabase_backup.py`
2. Select backup date from available options
3. Choose tables to restore (or 'all')
4. Confirm destructive operation if clearing existing data
5. Monitor restore progress in logs

### Partial Data Recovery
- Restore specific tables only
- Option to preserve existing data or replace completely
- Batch verification during restore process

## Security Considerations

### API Keys
- Supabase SERVICE_ROLE_KEY required for backup operations
- Keys are embedded in scripts (secure local storage recommended)
- Backup files contain raw data (secure backup location required)

### Access Control
- Backup requires SERVICE_ROLE permissions
- Restore operations are destructive (requires confirmation)
- Backup files contain sensitive property data

## Maintenance

### Regular Tasks
- Monitor backup.log for errors
- Check disk space in backup directory (estimates 15-25 GB monthly)
- Verify backup integrity weekly using test restore
- Update retention period if needed

### Troubleshooting
- **"No data retrieved"** - Check Supabase connection and API key
- **"Table not found"** - Verify table names in TABLES_TO_BACKUP list
- **Timeout errors** - Increase BATCH_SIZE delay or reduce batch size
- **Disk space** - Reduce RETENTION_DAYS or move backups to external storage

## Future Enhancements
- [ ] Cloud storage integration (AWS S3, Google Cloud)
- [ ] Incremental backups for changed records only
- [ ] Email notifications for backup success/failure
- [ ] Multiple database support
- [ ] Backup encryption
- [ ] Backup integrity checksums