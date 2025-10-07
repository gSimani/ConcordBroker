# MAIN WEBSITE REFERENCE

## 🎯 IMPORTANT: DEFAULT WEBSITE TO USE

**THE MAIN PRODUCTION WEBSITE IS: `/apps/web/`**

This is WEBSITE 1A - the primary version that matches production (concordbroker.com).

## ⚠️ CRITICAL UPDATE - September 28, 2025

**ONLY USE PORT 5175 FOR LOCAL DEVELOPMENT**

## Directory Structure

```
ConcordBroker/
├── apps/
│   └── web/           ← ✅ THIS IS THE MAIN WEBSITE (USE THIS)
│       ├── src/
│       ├── package.json
│       └── vite.config.ts
├── backups/
│   └── apps_web_before_master_/  ← ❌ QUARANTINED - DO NOT USE
```

## Running the Main Website

Always use the main website from `/apps/web/` on PORT 5175:

```bash
cd apps/web
npm run dev -- --port 5175
```

**REQUIRED PORT: 5175**
**URL: http://localhost:5175**

## Key Features of Main Website

1. **Property Search**: http://localhost:5175/properties
2. **Property Details**: http://localhost:5175/property/{parcelId}
3. **Enhanced Property Profile**: Now fixed and working
4. **MiniPropertyCard Component**: Fully integrated
5. **All Tab Components**: Working correctly

## DO NOT USE

- `/backups/apps_web_before_master_/` - This is the backup version (WEBSITE 2A)
- Any test HTML files in the root directory

## Current Status

- Main website has been fixed to include:
  - EnhancedPropertyProfile component
  - Proper tab imports (TaxesTab instead of PropertyTaxInfoTab)
  - Property detail navigation working
  - All imports corrected

## Remember

**ALWAYS USE `/apps/web/` AS THE DEFAULT WEBSITE**

Last updated: September 28, 2025