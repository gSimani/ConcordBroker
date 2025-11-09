# Production Backup System Deployment Guide

## Overview
This guide explains how to deploy the daily backup system with web-based toggle control to production.

## Current Status
✅ Backup system fully implemented and tested locally
✅ Web interface created with toggle control
✅ Production API configured for Railway deployment
✅ React components updated with production endpoints

## Architecture

### Components
1. **Backup Script** (`daily_supabase_backup.py`) - Core backup functionality
2. **Management API** (`backup_management_api.py`) - REST API for control
3. **React UI** (`BackupManager.tsx`) - Web interface with toggle
4. **Production API** (`production_api.py`) - Combined API service for Railway

### Endpoints
- Production: `https://api.concordbroker.com/backup/*`
- Local: `http://localhost:8006/*`

## Deployment Steps

### 1. Deploy to Railway (Backend)

The Railway configuration has been updated to use the combined `production_api.py` which includes:
- Autocomplete API at `/autocomplete`
- Backup API at `/backup`
- Mortgage API at `/mortgage`

```bash
# Commit and push to trigger Railway deployment
git add .
git commit -m "feat: Add backup management system with web toggle"
git push origin master
```

### 2. Verify API Deployment

After Railway deployment completes:

```bash
# Test health endpoint
curl https://api.concordbroker.com/health

# Test backup config (with API key)
curl -H "x-api-key: concordbroker-backup-key-2025" \
  https://api.concordbroker.com/backup/api/backup/config
```

### 3. Deploy Frontend to Vercel

The frontend will automatically deploy when pushed to master. The backup management UI is available at:
- `/admin/settings` - Admin settings page with backup manager

### 4. Configure Production Backup Server

On your production backup server (Windows machine with access to Supabase):

1. **Install Dependencies**:
```bash
pip install supabase python-dotenv fastapi uvicorn
```

2. **Copy Backup Scripts**:
- `daily_supabase_backup.py`
- `restore_supabase_backup.py`
- `backup_management_api.py`

3. **Set Environment Variables**:
Create `.env` file with:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

4. **Configure Windows Task Scheduler**:
```bash
# Run as Administrator
schtasks /create /tn "Supabase Daily Backup" /tr "python C:\path\to\daily_supabase_backup.py" /sc daily /st 02:00 /f /rl highest
```

## Web Interface Usage

### Accessing the Backup Manager

1. Navigate to: `https://concordbroker.com/admin/settings`
2. Click on "Backup Management" tab
3. Use the toggle switch to enable/disable daily backups

### Features Available

- **Toggle Daily Backups**: Enable/disable with single switch
- **View Statistics**: Total backups, size, last backup date
- **Manual Backup**: Run backup immediately
- **Status Monitoring**: Real-time status updates

### API Authentication

All API calls require the API key header:
```
x-api-key: concordbroker-backup-key-2025
```

## Production Checklist

- [ ] Railway API deployed with backup endpoints
- [ ] Frontend deployed with admin settings page
- [ ] Backup server configured with scripts
- [ ] Windows Task Scheduler configured
- [ ] Environment variables set
- [ ] API endpoints tested
- [ ] Toggle functionality verified
- [ ] First backup run successfully

## Monitoring

### Check Backup Status
```bash
# Via API
curl -H "x-api-key: concordbroker-backup-key-2025" \
  https://api.concordbroker.com/backup/api/backup/stats

# Via Windows Task Scheduler
schtasks /query /tn "Supabase Daily Backup"

# Via logs
type C:\TEMP\SUPABASE_BACKUPS\backup.log
```

### Backup Storage Location
- Path: `C:\TEMP\SUPABASE_BACKUPS\backup_YYYY-MM-DD\`
- Retention: 30 days (automatic cleanup)
- Compression: ~90% reduction with gzip

## Troubleshooting

### Issue: Toggle doesn't work
- Check API key is correct
- Verify Railway deployment is running
- Check CORS settings in production_api.py

### Issue: Backup fails to run
- Verify Supabase credentials
- Check disk space (need ~1GB free)
- Review backup.log for errors
- Ensure Windows Task Scheduler has proper permissions

### Issue: Can't access admin page
- Verify user has admin permissions
- Check route is properly configured in App.tsx
- Ensure AdminSettings component is imported

## Security Notes

1. **API Key**: Keep `concordbroker-backup-key-2025` secure
2. **Service Role Key**: Required for backup operations
3. **Admin Access**: Restrict `/admin/settings` route to authorized users
4. **Backup Files**: Store in secure location with proper access controls

## Future Enhancements

- [ ] Email notifications on backup success/failure
- [ ] Cloud storage integration (S3, Google Cloud)
- [ ] Incremental backups
- [ ] Backup encryption
- [ ] Multiple database support