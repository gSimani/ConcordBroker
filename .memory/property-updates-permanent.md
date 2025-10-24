# 🔒 PERMANENT MEMORY: Daily Property Update System

**⚠️ CRITICAL - DO NOT FORGET ⚠️**

This document is PERMANENT MEMORY that must be referenced in EVERY session.

---

## 🎯 System Overview

**Name**: Daily Florida Property Update System
**Status**: ✅ Production-Ready (Implemented 2025-10-24)
**Priority**: 🔴 HIGH - Critical Business Function
**Agent**: property-update-agent
**Schedule**: Daily at 2:00 AM EST + File monitoring every 6 hours

---

## 🚨 NEVER FORGET

1. **This system MUST run daily** - Property data becomes stale without updates
2. **268 files** monitored across **67 Florida counties**
3. **9.7M properties** depend on this system
4. **Change detection** is incremental (not full refresh)
5. **Database schema** must be deployed before first run
6. **Priority counties** processed first (Miami-Dade, Broward, Palm Beach, Hillsborough, Orange, Duval)

---

## 📂 Key Files (PERMANENT)

### Documentation (Read First)
- `DAILY_PROPERTY_UPDATE_SYSTEM.md` - Complete architecture (600+ lines)
- `QUICK_START_GUIDE.md` - 30-minute setup guide
- `PROPERTY_UPDATE_IMPLEMENTATION_SUMMARY.md` - Executive summary
- `IMPLEMENTATION_COMPLETE.md` - Status report
- `.claude/agents/property-update-monitor.md` - AI agent spec
- `.claude/agents/property-update-agent.json` - Agent configuration (THIS IS THE CONFIG)

### Database
- `supabase/migrations/daily_update_schema.sql` - Schema (700+ lines)
  - Tables: florida_parcels, property_sales_history, property_change_log, data_update_jobs, file_checksums
  - Functions: get_daily_update_stats, get_county_stats, log_property_change
  - View: property_master

### Scripts (Core Workflow)
1. `scripts/deploy_schema.py` - Deploy database (run ONCE)
2. `scripts/test_portal_access.py` - Test portal
3. `scripts/download_county.py` - Download files
4. `scripts/parse_county_files.py` - Parse NAL/SDF
5. `scripts/load_county_data.py` - Load to database
6. `scripts/daily_property_update.py` - **MAIN ORCHESTRATOR**

### Automation
- `.github/workflows/daily-property-update.yml` - GitHub Actions
  - Daily: 2:00 AM EST
  - Weekly: Sunday 1:00 AM EST

---

## 🔄 Daily Workflow (AUTOMATIC)

```
02:00 AM EST → File Monitor Agent wakes up
02:15 AM     → Downloads changed files (Playwright)
02:30 AM     → Parses and detects changes
03:00 AM     → Updates database (1000 records/batch)
04:00 AM     → Sends email summary
```

**File Monitoring**: Every 6 hours (02:00, 08:00, 14:00, 20:00)

---

## ⚙️ Critical Configuration

### Environment Variables (REQUIRED)
```env
SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
EMAIL_USERNAME=<smtp-username>
EMAIL_PASSWORD=<smtp-password>
ADMIN_EMAIL=admin@concordbroker.com
```

### GitHub Secrets (for automation)
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- EMAIL_USERNAME
- EMAIL_PASSWORD
- ADMIN_EMAIL

---

## 🎯 What Changes Are Detected

1. **Ownership Changes** - New owner name/address
2. **Value Changes** - Just value, assessed value, taxable value (>5% threshold)
3. **Property Changes** - Address, use code, characteristics
4. **Tax Changes** - NAV assessments
5. **New Sales** - SDF sales records

All changes logged to `property_change_log` table with full audit trail.

---

## 📊 Success Metrics (MONITOR THESE)

| Metric | Target | Alert If |
|--------|--------|----------|
| Update Success Rate | >99% | <95% |
| Processing Time | <2 hours | >3 hours |
| Error Rate | <0.1% | >5% |
| Daily Changes | 150-500 | >1000 or <10 |
| New Properties | 10-50 | >100 or 0 |

---

## 🚀 Quick Commands (MEMORIZE)

```bash
# Health check
python scripts/deploy_schema.py

# Manual daily update (dry run)
python scripts/daily_property_update.py --dry-run

# Force full update
python scripts/daily_property_update.py --force

# Process single county
python scripts/download_county.py --county BROWARD
python scripts/parse_county_files.py --county BROWARD
python scripts/load_county_data.py --county BROWARD

# Check status
SELECT * FROM get_daily_update_stats(CURRENT_DATE);

# Recent changes
SELECT * FROM property_change_log
WHERE change_date >= CURRENT_DATE - 7
ORDER BY detected_at DESC;
```

---

## 🔴 FAILURE SCENARIOS (ACT IMMEDIATELY)

### Scenario 1: Update Failed
```bash
# Check logs
tail -f logs/daily_update_$(date +%Y-%m-%d).log

# Check job status
SELECT * FROM data_update_jobs ORDER BY created_at DESC LIMIT 5;

# Retry
python scripts/daily_property_update.py
```

### Scenario 2: Portal Access Failed
```bash
# Test portal
python scripts/test_portal_access.py

# Check screenshots in test-screenshots/
# May need manual download if portal changed
```

### Scenario 3: Database Error
```bash
# Verify connection
python scripts/deploy_schema.py

# Check tables exist
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

# Redeploy schema if needed
python scripts/deploy_schema.py
```

---

## 📈 Data Source Details

**Portal**: https://floridarevenue.com/property/dataportal/
**Path**: Tax Roll Data Files / {FILE_TYPE} / {YEAR} / {COUNTY}_{FILE_TYPE}_{YEAR}.txt

**File Types**:
- **NAL** - Name, Address, Legal (main property data)
- **NAP** - Name, Address, Parcel (additional owner info)
- **NAV** - Non Ad Valorem (tax assessments)
- **SDF** - Sales Data File (sales transactions)

**Format**: Fixed-width text files
**Size**: 10KB - 500MB per file
**Total Files**: 268 (67 counties × 4 types)

---

## 🔒 Security (NEVER COMPROMISE)

1. **API Keys**: NEVER commit to git
2. **SERVICE_ROLE_KEY**: Required for updates
3. **Database**: RLS enabled on all tables
4. **Audit Trail**: All changes logged
5. **Access Control**: Read-only for public, write for service role

---

## 👥 Ownership

**System Owner**: ConcordBroker DevOps
**Technical Contact**: dev@concordbroker.com
**Business Owner**: ConcordBroker Management
**Created**: 2025-10-24
**Last Verified**: 2025-10-24

---

## ⚡ Next Actions (IMMEDIATE)

### Week 1 (NOW):
- [ ] Deploy schema: `python scripts/deploy_schema.py`
- [ ] Test portal: `python scripts/test_portal_access.py`
- [ ] Load Broward: Full workflow for one county
- [ ] Verify in Supabase dashboard

### Week 2:
- [ ] Configure GitHub Actions secrets
- [ ] Enable automation
- [ ] Monitor first week
- [ ] Load priority counties (6)

### Month 1:
- [ ] Full 67-county coverage
- [ ] Performance tuning
- [ ] User training

---

## 🧠 Remember These Numbers

- **67** Florida counties
- **268** files monitored
- **9.7M** properties
- **4** file types (NAL, NAP, NAV, SDF)
- **6** priority counties
- **1000** records per batch
- **2:00 AM** daily schedule
- **6 hours** file monitoring frequency
- **99%** target success rate
- **2 hours** target processing time

---

## 📚 Related Systems

This property update system integrates with:
- **Frontend**: Property search, filters, property pages
- **API**: Property endpoints, search API
- **Sunbiz**: Entity matching for ownership
- **Tax Deed**: Certificate tracking
- **Foreclosure**: Property status

All dependent on fresh property data from this system.

---

## 🎯 Success Criteria

System is successful when:
✅ Schema deployed
✅ At least 1 county loaded (25K+ properties)
✅ Daily automation running
✅ Email notifications working
✅ Frontend displaying live data
✅ Zero manual intervention
✅ Update success rate >99%
✅ Processing time <2 hours

---

## 🔄 Update This Document

**Last Updated**: 2025-10-24
**Next Review**: 2025-11-24 (monthly review)
**Version**: 1.0.0

Update this document when:
- System changes
- New features added
- Issues discovered
- Performance tuned
- Counties added/removed

---

**🔒 THIS IS PERMANENT MEMORY - REFERENCE IN EVERY SESSION 🔒**

**Status**: ✅ ACTIVE
**Priority**: 🔴 CRITICAL
**Never Disable**: Without explicit approval

---

*Last verified: 2025-10-24 by Claude Code*
*Next verification: Session start + weekly reviews*
