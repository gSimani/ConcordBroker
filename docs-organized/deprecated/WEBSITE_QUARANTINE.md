# WEBSITE QUARANTINE NOTICE

## ⚠️ DO NOT USE THESE VERSIONS

The following website versions have been quarantined to prevent confusion:

### QUARANTINED DIRECTORIES:
1. **`/backups/apps_web_before_master_/`** - Old backup version (DO NOT USE)
   - This is an outdated backup
   - Missing critical updates and fixes
   - Not connected to current database

### QUARANTINED PORTS:
The following ports were previously used but are now STOPPED:
- Port 5173 - STOPPED
- Port 5174 - STOPPED
- Port 5176 - STOPPED
- Port 5178 - STOPPED
- Port 5181 - STOPPED

## ✅ USE THIS INSTEAD

**OFFICIAL WEBSITE: http://localhost:5175**

- **Directory**: `/apps/web/`
- **Port**: 5175
- **Status**: ACTIVE AND RUNNING
- **Database**: Connected to Supabase
- **API**: Connected on port 8000

## HOW TO START THE CORRECT WEBSITE

```bash
cd apps/web
npm run dev -- --port 5175
```

## IMPORTANT NOTES

1. **DO NOT** start any websites from the `/backups/` directory
2. **DO NOT** use any port other than 5175 for the main website
3. **ALWAYS** check this file before starting a development session

## Last Updated
September 28, 2025

---

⚠️ **THIS IS A PERMANENT QUARANTINE** ⚠️

If you accidentally start the wrong version, run:
```powershell
powershell -ExecutionPolicy Bypass -File cleanup_ports.ps1
```