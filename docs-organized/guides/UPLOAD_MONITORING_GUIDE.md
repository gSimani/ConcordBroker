# 2023 NAL Upload Monitoring Guide

**Status**: ✅ ACTIVE - Upload running successfully
**Started**: 2025-11-09 ~15:02:00
**Script**: `scripts/upload_2023_nal_resume.py`

---

## 🎯 Quick Status Check

### Progress Dashboard (Best Option)
```
http://localhost:5555/
```
**Live Updates**: Auto-refreshes every 5 seconds

### API Check (Detailed JSON)
```bash
curl -s http://localhost:5555/api/progress | python -m json.tool
```

### Total Record Count
```bash
python check_2023_count.py
```

---

## 📊 Current Status (as of 15:08)

- **Total Records**: 6,425,912 (increasing)
- **Current County**: DUVAL
- **Counties Completed**: 39 (skipped by resume script)
- **Counties Remaining**: ~28
- **ETA**: 5-6 hours

---

## 🔍 Detailed Progress Tracking

### Check Upload Process
```bash
# See if script is still running
tasklist | findstr python

# Check progress database entries
python check_ingestion_history.py
```

### Monitor Specific County
```bash
curl -s http://localhost:5555/api/progress | grep county
```

### Check for Errors
Look for these patterns in output:
- `[ERROR]` - Upload errors
- `[RETRY X/5]` - Automatic retries (normal)
- `[WARNING]` - Non-critical issues

---

## ⚠️ If Upload Stops

### 1. Check if process is hung
```bash
tasklist /FI "IMAGENAME eq python.exe" /FO LIST /V
```
Look for process with high memory but low CPU time.

### 2. Kill hung process
```bash
taskkill /F /PID <process_id>
```

### 3. Restart upload (auto-resumes)
```bash
python scripts/upload_2023_nal_resume.py
```
The script **automatically skips completed counties**, so it's safe to restart!

---

## 🎓 Understanding the Progress

### Progress Server Shows:
- **Total Rows**: Actual count from database (updates as data is uploaded)
- **Current County**: County being processed right now
- **Percent**: Progress for CURRENT COUNTY (not overall)
- **Files Processed**: Files completed for current county

### Overall Progress Calculation:
```
Overall Progress = (Completed Counties / 67 Total Counties)
Currently: 39/67 = 58% complete
```

---

## 🔧 Improvements in Resume Script

1. **Smart Resume**: Skips 39 already completed counties
2. **Adaptive Batching**:
   - Large counties (ORANGE, BROWARD, etc.): 750 rows/batch
   - Normal counties: 1500 rows/batch
3. **Retry Logic**: Max 5 retries with exponential backoff
4. **Better Error Handling**: Logs errors but continues processing
5. **Same Run ID**: Maintains '2023-full-load-v3' continuity

---

## 📈 Expected County Processing Order

**Next 10 Counties to Upload**:
1. ✅ DUVAL (in progress)
2. FLAGLER
3. HERNANDO
4. HILLSBOROUGH ⚠️ Large
5. INDIAN RIVER
6. LAKE
7. LEE ⚠️ Large
8. MADISON
9. MANATEE
10. MARION

**Large Counties** (may take 15-30 min each):
- HILLSBOROUGH
- LEE
- ORANGE
- PALM BEACH
- PASCO
- PINELLAS
- POLK

---

## 🚨 Common Issues & Solutions

### Issue: Row count not changing
**Check**: Is upload script still running?
```bash
tasklist | findstr python
```

### Issue: Dashboard stuck at 100%
**Reason**: Dashboard shows per-county progress, not overall
**Solution**: Look at "Current County" to see which is processing

### Issue: Script seems slow
**Normal**: Large counties (ORANGE, PALM BEACH) take longer
**Check**: Progress is still incrementing in database

### Issue: Errors in upload
**Normal**: Script has retry logic for timeouts/rate limits
**Concern**: If same county fails 5 times, it will skip and continue

---

## 📝 Files Created During This Session

1. **2023_NAL_UPLOAD_STATUS_REPORT.md** - Detailed analysis of upload status
2. **upload_2023_nal_resume.py** - Improved upload script with resume capability
3. **check_2023_count.py** - Quick database count checker
4. **check_ingestion_history.py** - Progress history analyzer
5. **check_uploaded_counties.py** - County breakdown script

---

## ✅ Success Criteria

Upload is complete when:
- ✅ All 67 counties show "ingested:" status
- ✅ Total record count reaches ~9.7M rows
- ✅ No counties in "start:" status (incomplete)
- ✅ Script exits with "UPLOAD COMPLETE" message

---

**Last Updated**: 2025-11-09 15:10:00
**Monitoring**: http://localhost:5555/
