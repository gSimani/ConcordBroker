# Property Appraiser Upload - Action Plan

## ✅ Confirmed Working Path
- **REST API with service_role key**: WORKING
- **Current Status**: 3,566,744 of 9,758,470 records uploaded (36.55%)
- **Remaining**: 6,191,726 records

## 🚀 Immediate Actions

### Step 1: Apply Timeout Removal (Run in Supabase SQL Editor)
```sql
-- Run disable_timeouts.sql
ALTER ROLE authenticated IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE authenticated IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';
ALTER ROLE anon IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE anon IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';
ALTER ROLE service_role IN DATABASE postgres SET statement_timeout = '0';
ALTER ROLE service_role IN DATABASE postgres SET idle_in_transaction_session_timeout = '0';
```

### Step 2: Run Optimized Upload Script
```bash
python optimized_property_upload.py
```

**Optimizations Applied:**
- ✅ Batch size: 1000 records (up from 500)
- ✅ Parallel workers: 4 concurrent threads
- ✅ Headers: `Prefer: return=minimal,resolution=merge-duplicates,count=none`
- ✅ Exponential backoff with jitter for rate limiting
- ✅ Progress tracking with resume capability

### Step 3: After Upload - Restore Timeouts
```sql
-- Run restore_timeouts.sql
ALTER ROLE authenticated IN DATABASE postgres RESET statement_timeout;
ALTER ROLE authenticated IN DATABASE postgres RESET idle_in_transaction_session_timeout;
ALTER ROLE anon IN DATABASE postgres RESET statement_timeout;
ALTER ROLE anon IN DATABASE postgres RESET idle_in_transaction_session_timeout;
ALTER ROLE service_role IN DATABASE postgres RESET statement_timeout;
ALTER ROLE service_role IN DATABASE postgres RESET idle_in_transaction_session_timeout;
```

## 📊 Performance Expectations

With optimizations:
- **Batch size**: 1000 records
- **Time per batch**: ~1-2 seconds (improved from 2s)
- **Parallel workers**: 4 threads
- **Effective throughput**: ~2000-4000 records/second
- **Total time estimate**: 1.5-3 hours (down from 3.5 hours)

## 🔄 Alternative: Direct PostgreSQL via IPv6

If you want to try direct COPY (10-100x faster):

### Option A: WSL2 (Recommended)
```bash
# In WSL2/Ubuntu
postgresql://postgres:West@Boca613!@db.pmispwtdngkcmsrsjwbp.supabase.co:5432/postgres?sslmode=require
```

### Option B: Windows IPv6 Connection String
```
postgresql://postgres:West@Boca613!@[2600:1f18:2e13:9d1e:1be4:2e84:a39b:d518]:5432/postgres?sslmode=require&host=db.pmispwtdngkcmsrsjwbp.supabase.co
```

## 📝 For Supabase Support

If REST API still times out after role-level changes, request:

1. **Database-wide timeout removal** (temporary):
```sql
ALTER DATABASE postgres SET statement_timeout = '0';
ALTER DATABASE postgres SET idle_in_transaction_session_timeout = '0';
```

2. **IPv4 endpoint** for direct connection

3. **Confirm pooler credentials**:
   - Username: `postgres.pmispwtdngkcmsrsjwbp`
   - Password: `West@Boca613!`
   - Why "Tenant or user not found" error?

## 🎯 Success Criteria

✅ All 9,758,470 records uploaded
✅ No timeout errors
✅ Completion verification shows 100%

## 📞 Contact Points

- **Supabase Dashboard**: Settings → Database → Connection Info
- **Support Ticket**: Include `SUPABASE_SUPPORT_PROMPT.md`
- **Project ID**: pmispwtdngkcmsrsjwbp

---

**Ready to proceed!** The optimized script with parallel processing and proper headers should complete the upload successfully after applying the timeout removal SQL.