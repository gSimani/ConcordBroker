# 📊 Database Setup - Final Steps

Your environment is configured correctly! Now you just need to create the tables and load data.

## Current Status
- ✅ **Environment Variables**: Configured
- ✅ **Supabase Connection**: Working
- ✅ **Data Files**: Available (NAP: 18.7MB, SDF: 13.2MB)
- ❌ **Database Tables**: Need to be created

---

## Step 1: Create Database Tables (REQUIRED)

### Option A: Via Supabase Dashboard (Recommended)
1. Open https://supabase.com/dashboard
2. Select your project: `mogulpssjdlx` (based on your URL)
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**
5. Copy ALL content from `apps/api/supabase_schema.sql`
6. Paste into the SQL editor
7. Click **Run** (or press Ctrl+Enter)

You should see "Success. No rows returned" for each CREATE statement.

### Option B: Manual Table Creation
If the schema file is too large, create tables one at a time:

```sql
-- 1. First, enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Create main parcels table
CREATE TABLE IF NOT EXISTS florida_parcels (
    id BIGSERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) NOT NULL,
    county VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    owner_name VARCHAR(255),
    owner_addr1 VARCHAR(255),
    owner_city VARCHAR(100),
    owner_state VARCHAR(2),
    owner_zip VARCHAR(10),
    phy_addr1 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_zipcd VARCHAR(10),
    just_value FLOAT,
    assessed_value FLOAT,
    taxable_value FLOAT,
    land_value FLOAT,
    building_value FLOAT,
    year_built INTEGER,
    total_living_area FLOAT,
    land_sqft FLOAT,
    sale_date TIMESTAMP,
    sale_price FLOAT,
    import_date TIMESTAMP DEFAULT NOW(),
    UNIQUE(parcel_id, county, year)
);

-- 3. Create indexes for performance
CREATE INDEX idx_parcels_county ON florida_parcels(county);
CREATE INDEX idx_parcels_owner ON florida_parcels(owner_name);
CREATE INDEX idx_parcels_address ON florida_parcels(phy_addr1, phy_city);
```

---

## Step 2: Load Data

Once tables are created, run:

```bash
python setup_database.py
```

Choose option **5** for complete setup, or run individually:
- Option 2: Load parcel data (NAP file)
- Option 3: Load sales data (SDF file)
- Option 4: Verify data

### For Testing (Quick - 1000 records)
The script loads only 1000 records by default for quick testing.

### For Production (Full data)
Edit `setup_database.py` line 93 and 146:
```python
# Change from:
nap_df = pd.read_csv(nap_file, low_memory=False, nrows=1000)
# To:
nap_df = pd.read_csv(nap_file, low_memory=False)  # Load all data
```

---

## Step 3: Start Localhost

### Quick Start
```powershell
.\start-localhost.ps1
```

### Manual Start
Terminal 1:
```bash
cd apps/api
python -m uvicorn main:app --reload --port 8000
```

Terminal 2:
```bash
cd apps/web
npm run dev
```

---

## Step 4: Verify Everything Works

### Test Database
```bash
python test_db_ready.py
```

Should show:
- [OK] Environment configured
- [OK] 4 tables exist
- [OK] florida_parcels: X records

### Test API
Open: http://localhost:8000/docs

Try these endpoints:
- `GET /health` - Should return OK
- `GET /api/properties` - Should return property list

### Test Web App
Open: http://localhost:5173

Should see:
- Homepage loads
- No console errors
- Can navigate to Properties page

---

## Troubleshooting

### "relation does not exist"
Tables not created. Go back to Step 1.

### "permission denied"
Check your service role key has full access in Supabase.

### No data showing
1. Check if data loaded: `python test_db_ready.py`
2. Check API logs for errors
3. Verify frontend is calling correct API URL

### CORS errors
Add localhost to allowed origins in `apps/api/config.py`:
```python
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

---

## Quick Commands

```bash
# Check status
python test_db_ready.py

# Load data
python setup_database.py

# Start everything
.\start-localhost.ps1

# Test connection only
cd apps/api && python supabase_client.py
```

---

## Data Sample

After loading, you should have:
- **Parcels**: Property records with owner info, addresses, valuations
- **Sales**: Transaction history with dates and prices
- **Searchable fields**: Owner names, addresses, parcel IDs

---

## Next Actions

1. ✅ Create tables in Supabase (Step 1)
2. ✅ Load sample data (Step 2)
3. ✅ Start localhost (Step 3)
4. ✅ Verify it works (Step 4)

Once working, you can:
- Load full dataset (remove nrows limit)
- Add more data sources
- Implement search features
- Add data visualizations

---

**Ready to start?** Begin with Step 1 - Create tables in Supabase!